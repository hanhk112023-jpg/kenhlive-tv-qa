#!/usr/bin/env python3
"""Offline unit tests for KenhLive QA upgrades:
1. SessionHistory (1M-context episodic memory + multi-turn text retention + zero old image retention + persistence).
2. VisionClient (reasoning_effort='high', max_tokens >= 8192, HTTP 400 fallback host caching,
   balanced JSON extraction with reasoning braces, anti-mistake guards).
3. RealtimeDevice (unified data.db WAL-mode sidecar reading, kenhlive_cinema.db fallback,
   compressed dump, refreshed TAB_KEYWORDS).
4. ScreenWatcher & RealtimeRunner (mark_action, faster cadence, SessionHistory wiring in qa_report.json).
5. Legacy AIBrain (autonomous_ai_qa.py) & ai_judge.py (QA_REASONING_EFFORT='high', 1M window > 30 msgs,
   balanced JSON extractor).
"""
import base64
import io
import json
import os
import shutil
import sqlite3
import sys
import tempfile
import unittest
import urllib.error
from unittest.mock import patch

RT_DIR = os.path.dirname(os.path.abspath(__file__))
HARNESS_DIR = os.path.dirname(RT_DIR)
sys.path.insert(0, RT_DIR)
sys.path.insert(0, HARNESS_DIR)

import history as history_mod
import vision as vision_mod
import perception as perception_mod
import detectors as detectors_mod
import device as device_mod
import runner as runner_mod
import ai_judge as ai_judge_mod
import autonomous_ai_qa as auto_qa_mod
import driver as driver_mod
from missions import get_missions


class FakeHTTPResponse:
    def __init__(self, body_dict):
        self._raw = json.dumps(body_dict).encode("utf-8")

    def read(self):
        return self._raw

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


class UpgradeTests(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="kl_qa_upg_")
        vision_mod._NO_REASONING_EFFORT_HOSTS.clear()
        ai_judge_mod._NO_REASONING_EFFORT_HOSTS.clear()
        auto_qa_mod._NO_REASONING_EFFORT_HOSTS.clear()

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    # 1. SessionHistory 1M-Context Space tests
    def test_session_history_1m_memory_and_no_old_images(self):
        h = history_mod.SessionHistory(session_id="RT-TEST")
        specs = {s.name: s for s in get_missions()}
        h.start_mission(specs["MISSION_COLD_START"], t_offset=0.0)
        obs1 = {
            "t_offset": 1.2,
            "activity": "com.kenhlive.tv/.MainActivity",
            "frame_hash": "hash_1",
            "frame_ref": "step_001.jpg",
            "loading_screen": False,
            "motion": False,
            "motion_delta": 0.1,
            "ui_state": {
                "focused_sig": "nav_home#[0,0][100,100]",
                "focused_text": "Trang chủ",
                "has_dialog": False,
                "dialog_ids": [],
                "osd_visible": False,
                "all_visible_texts": [("nav_home", "Trang chủ"), ("row1", "Đang Trực Tiếp Ngay")],
            },
            "findings": [],
        }
        h.record_step(1, "MISSION_COLD_START", obs1, tab=0)
        h.record_action(1, {"type": "KEY", "param": "DPAD_DOWN", "rule": "explore:down", "thought": "Move"})
        # Repeat same state -> UNCHANGED + triggers stuck hint
        h.record_step(2, "MISSION_COLD_START", dict(obs1, t_offset=2.4), tab=0)
        h.record_action(2, {"type": "KEY", "param": "DPAD_DOWN", "rule": "explore:down", "thought": "Move"})
        h.record_step(3, "MISSION_COLD_START", dict(obs1, t_offset=3.5), tab=0)
        h.record_finding({
            "severity": "HIGH",
            "area": "Home",
            "issue": "Sample issue",
            "detail": "Details",
            "evidence": {"frame": "step_001.jpg", "video_t": 1.2},
        }, "MISSION_COLD_START")
        # Duplicate finding should not double count
        h.record_finding({
            "severity": "HIGH",
            "area": "Home",
            "issue": "Sample issue",
            "detail": "Details",
            "evidence": {"frame": "step_001.jpg", "video_t": 1.2},
        }, "MISSION_COLD_START")

        # Add 3 vision turns
        for i in range(1, 4):
            h.record_vision_turn(
                "confirm_target",
                f"Check step {i}",
                json.dumps({"confirmed": i == 3, "quote": f"Text {i}"}),
                parsed={"confirmed": i == 3, "quote": f"Text {i}"},
                meta={"mission": "MISSION_COLD_START", "step_id": i, "frame_ref": f"step_00{i}.jpg"},
            )

        msgs = h.build_messages(
            "Final question",
            b64_image=base64.b64encode(b"CURRENT_FAKE_IMAGE").decode(),
            context={"mission": "MISSION_COLD_START", "step_id": 4, "activity": "MainActivity"},
        )
        self.assertEqual(msgs[0]["role"], "system")
        # 1 system + 3*2 historical turns + 1 current user = 8 messages
        self.assertEqual(len(msgs), 8)
        # Historical turns MUST be pure text strings (no old image_url!)
        for m in msgs[1:-1]:
            self.assertIsInstance(m["content"], str)
            self.assertNotIn("data:image/jpeg", m["content"])
        # Current user turn MUST include episodic memory + image_url
        cur = msgs[-1]
        self.assertEqual(cur["role"], "user")
        self.assertIsInstance(cur["content"], list)
        self.assertIn("ĐÃ PHÁT HIỆN", cur["content"][0]["text"])
        self.assertIn("CẢNH BÁO KẸT", cur["content"][0]["text"])
        self.assertEqual(cur["content"][1]["type"], "image_url")

        h.end_mission({"name": "MISSION_COLD_START", "outcome": "PASS", "reason": "ok", "steps": 3}, t_offset=4.0)
        jpath, mpath = h.save(self.tmpdir)
        self.assertTrue(os.path.exists(jpath))
        self.assertTrue(os.path.exists(mpath))
        with open(jpath, encoding="utf-8") as jf:
            saved = json.load(jf)
        self.assertEqual(saved["stats"]["findings_recorded"], 1)
        self.assertEqual(saved["stats"]["context_window_tokens"], 1000000)

    # 2. JSON extraction & Reasoning high + HTTP 400 fallback tests
    def test_extract_json_handles_reasoning_braces_and_fences(self):
        raw = (
            "Thinking process: I see {some: invalid} braces and a draft {\"confirmed\": false} "
            "Wait, actually looking closely at the frame I see LIVE and score.\n"
            "```json\n{\"confirmed\": true, \"confidence\": \"high\", \"quote\": \"LIVE 2 : 1\",}\n```"
        )
        parsed = vision_mod._extract_json(raw)
        self.assertEqual(parsed, {"confirmed": True, "confidence": "high", "quote": "LIVE 2 : 1"})

    def test_vision_high_reasoning_and_400_fallback_host_cache(self):
        sent_payloads = []

        def fake_urlopen(req, timeout=60):
            body = json.loads(req.data.decode("utf-8"))
            sent_payloads.append(body)
            if "reasoning_effort" in body:
                raise urllib.error.HTTPError(
                    req.full_url, 400, "Bad Request", {},
                    io.BytesIO(b'{"error": {"message": "Unknown parameter: reasoning_effort"}}')
                )
            return FakeHTTPResponse({
                "choices": [{"message": {
                    "reasoning_content": "internal thought {not final}",
                    "content": '{"confirmed": true, "confidence": "high", "quote": "Trang chu"}'
                }}]
            })

        old_base, old_key, old_model = vision_mod.OPENAI_BASE, vision_mod.OPENAI_KEY, vision_mod.OPENAI_MODEL
        old_ds, old_ag, old_kl = vision_mod.DEEPSEEK_BASE, vision_mod.ANTIGRAVITY_KEY, vision_mod.KILO_KEY
        try:
            vision_mod.DEEPSEEK_BASE = ""
            vision_mod.ANTIGRAVITY_KEY = ""
            vision_mod.KILO_KEY = ""
            vision_mod.OPENAI_BASE = "https://mock-gateway.example.com/v1"
            vision_mod.OPENAI_KEY = "sk-test"
            vision_mod.OPENAI_MODEL = "gemini-3-flash"

            vc = vision_mod.VisionClient(budget=10, reasoning_effort="high")
            self.assertEqual(vc.provider, "OPENAI")
            self.assertEqual(vc.reasoning_effort, "high")

            with patch("urllib.request.urlopen", side_effect=fake_urlopen):
                res1, err1 = vc.confirm_target(b"FAKEPNG", "nav Trang chu", context={"step_id": 1})
                res2, err2 = vc.confirm_target(b"FAKEPNG", "nav Kho phim", context={"step_id": 2})

            self.assertIsNone(err1)
            self.assertTrue(res1["confirmed"])
            self.assertIsNone(err2)
            # Call 1 tried reasoning_effort="high" + max_tokens >= 8192, got 400 -> retried without reasoning_effort
            self.assertEqual(sent_payloads[0].get("reasoning_effort"), "high")
            self.assertGreaterEqual(sent_payloads[0]["max_tokens"], 8192)
            self.assertNotIn("reasoning_effort", sent_payloads[1])
            # Call 2 hit host cache -> never even tried reasoning_effort
            self.assertNotIn("reasoning_effort", sent_payloads[2])
            self.assertEqual(len(sent_payloads), 3)
            # SessionHistory retained turn 1 -> turn 2 messages has prior user + assistant turn
            self.assertEqual(len(sent_payloads[2]["messages"]), 4)
        finally:
            vision_mod.OPENAI_BASE, vision_mod.OPENAI_KEY, vision_mod.OPENAI_MODEL = old_base, old_key, old_model
            vision_mod.DEEPSEEK_BASE, vision_mod.ANTIGRAVITY_KEY, vision_mod.KILO_KEY = old_ds, old_ag, old_kl

    def test_vision_guards_low_conf_and_player_switch_tab(self):
        vc = vision_mod.VisionClient(budget=5)
        vc.provider = "OPENAI"
        vc.endpoint_host = "mock.local"
        # Low-confidence confirm without quote must be downgraded to False
        with patch.object(vc, "_attempt", return_value=('{"confirmed": true, "confidence": "low", "quote": ""}', None)):
            res, err = vc.confirm_target(b"FAKE", "target")
            self.assertIsNone(err)
            self.assertFalse(res["confirmed"])
        # stuck_assist inside PlayerActivity must never emit SWITCH_TAB
        with patch.object(vc, "_attempt", return_value=('{"action": "SWITCH_TAB", "param": "2"}', None)):
            res2, err2 = vc.stuck_assist(
                b"FAKE", "target", "DPAD_DOWN",
                context={"activity": "com.kenhlive.tv/.PlayerActivity"}
            )
            self.assertIsNone(err2)
            self.assertEqual(res2["action"], "KEY")
            self.assertEqual(res2["param"], "BACK")

    # 3. Unified data.db WAL mode & TAB_KEYWORDS tests
    def test_device_reads_unified_data_db_with_wal_sidecars(self):
        db_path = os.path.join(self.tmpdir, "data.db")
        con = sqlite3.connect(db_path)
        con.execute("PRAGMA journal_mode = WAL;")
        con.execute(
            "CREATE TABLE watch_history (slug TEXT, episode_slug TEXT, position_ms INTEGER, duration_ms INTEGER, last_watched_at INTEGER)"
        )
        con.execute("INSERT INTO watch_history VALUES ('phim-a', 'tap-1', 12000, 100000, 100)")
        con.commit()
        # Keep uncheckpointed data in -wal sidecar
        con.execute("INSERT INTO watch_history VALUES ('phim-a', 'tap-2', 48500, 100000, 999)")
        con.commit()

        def _read_bytes(p):
            with open(p, "rb") as f:
                return f.read()

        files = {
            "data.db": _read_bytes(db_path),
            "data.db-wal": _read_bytes(db_path + "-wal") if os.path.exists(db_path + "-wal") else b"",
            "data.db-shm": _read_bytes(db_path + "-shm") if os.path.exists(db_path + "-shm") else b"",
        }
        dev = device_mod.RealtimeDevice()
        with patch.object(dev, "_pull_app_db_file", side_effect=lambda name: files.get(name, b"")):
            probe = dev.webplayer_progress_probe()
        con.close()
        self.assertIsNotNone(probe)
        self.assertEqual(probe["slug"], "phim-a")
        self.assertEqual(probe["episode_slug"], "tap-2")
        self.assertEqual(probe["pos_ms"], 48500)

    def test_device_fallback_to_legacy_kenhlive_cinema_db(self):
        legacy_path = os.path.join(self.tmpdir, "kenhlive_cinema.db")
        con = sqlite3.connect(legacy_path)
        con.execute(
            "CREATE TABLE watch_history (slug TEXT, episode_slug TEXT, position_ms INTEGER, duration_ms INTEGER, last_watched_at INTEGER)"
        )
        con.execute("INSERT INTO watch_history VALUES ('legacy-film', 'tap-3', 30000, 90000, 500)")
        con.commit()
        con.close()
        with open(legacy_path, "rb") as lf:
            raw = lf.read()

        dev = device_mod.RealtimeDevice()
        with patch.object(dev, "_pull_app_db_file", side_effect=lambda name: raw if name == "kenhlive_cinema.db" else b""):
            probe = dev.webplayer_progress_probe()
        self.assertIsNotNone(probe)
        self.assertEqual(probe["slug"], "legacy-film")
        self.assertEqual(probe["pos_ms"], 30000)

    def test_tab_keywords_sync(self):
        dev = device_mod.RealtimeDevice()
        self.assertEqual(dev.detect_tab_index({"all_visible_texts": [("btnPhimQuickSearch", "Kho Phim")], "selected_ids": []}), 5)
        self.assertEqual(dev.detect_tab_index({"all_visible_texts": [("rowHdr", "Truyền Hình · Xem được")], "selected_ids": []}), 2)
        self.assertEqual(dev.detect_tab_index({"all_visible_texts": [("rowHdr", "🔴 Đang Trực Tiếp Ngay")], "selected_ids": []}), 0)

    # 4. Perception cadence & Runner integration tests
    def test_watcher_mark_action_and_runner_history_report(self):
        self.assertLessEqual(perception_mod.SAMPLE_PERIOD_S, 0.5)
        dev = device_mod.RealtimeDevice()
        w = perception_mod.ScreenWatcher(dev)
        w._stable_streak = 4
        w.mark_action()
        self.assertEqual(w._stable_streak, 0)

        # Verify RealtimeRunner wires SessionHistory cleanly on fake device
        class MockDev(device_mod.RealtimeDevice):
            def screencap_bytes(self):
                return b"PNGFAKE" * 900
            def dump_ui_state(self):
                return {
                    "focused_sig": "nav_home#[362,0][563,112]",
                    "focused_text": "Trang chủ",
                    "focused_bounds": "[362,0][563,112]",
                    "focusable_count": 4,
                    "all_visible_texts": [("nav_home", "Trang chủ"), ("liveHdr", "Đang Trực Tiếp Ngay")],
                    "all_visible_nodes": [{"id": "nav_home", "text": "Trang chủ", "bounds": "[362,0][563,112]"}],
                    "has_dialog": False, "dialog_ids": [], "selected_ids": ["nav_live"],
                    "ui_summary": "[FOCUSED] nav_home ('Trang chủ')", "osd_visible": False,
                }
            def current_activity(self):
                return "com.kenhlive.tv/.MainActivity"
            def launch_app(self):
                return 250
            def checkpoint_logcat(self):
                return None
            def get_pss_memory_mb(self):
                return 0.0
            def detect_focus_ring(self, *a):
                return True, "ORANGE", 0.5
            def switch_tab(self, tab_index):
                self._note("SWITCH_TAB(%d)" % tab_index)
                return True
            def send_key(self, k):
                self._note(k)

        old_dev, old_rec = runner_mod.RealtimeDevice, runner_mod.VideoRecorder
        try:
            runner_mod.RealtimeDevice = MockDev
            runner_mod.VideoRecorder = None
            r = runner_mod.RealtimeRunner(out_dir=self.tmpdir, no_vision=True, vision_budget=0)
            specs = get_missions(only=["MISSION_COLD_START"])
            report = r.run(specs)
            self.assertIn("session_history", report)
            self.assertGreaterEqual(report["session_history"]["steps_recorded"], 1)
            self.assertEqual(report["reasoning_effort"], vision_mod.REASONING_EFFORT)
            self.assertTrue(os.path.exists(os.path.join(self.tmpdir, "session_history.json")))
            self.assertTrue(os.path.exists(os.path.join(self.tmpdir, "session_history.md")))
        finally:
            runner_mod.RealtimeDevice, runner_mod.VideoRecorder = old_dev, old_rec

    # 5. Legacy AIBrain & ai_judge upgrades
    def test_autonomous_ai_brain_1m_history_and_reasoning_high(self):
        self.assertEqual(auto_qa_mod.QA_REASONING_EFFORT, "high")
        self.assertGreaterEqual(auto_qa_mod.MAX_SESSION_MESSAGES, 400)
        self.assertGreaterEqual(auto_qa_mod.MAX_SESSION_CHARS, 500000)
        self.assertEqual(ai_judge_mod.REASONING_EFFORT, "high")
        self.assertGreaterEqual(ai_judge_mod._max_tokens_for("gpt-4o", 1500), 8192)

        # Ensure balanced JSON extractor works cleanly with reasoning traces
        parsed = auto_qa_mod._extract_balanced_json(
            "Reasoning {skip} ```json\n{\"thought\": \"ok\", \"action_type\": \"KEY\", \"action_param\": \"DPAD_DOWN\"}\n```"
        )
        self.assertEqual(parsed["action_type"], "KEY")
        self.assertEqual(parsed["action_param"], "DPAD_DOWN")

        # Verify AIBrain preserves > 40 messages without sliding-window truncation at 30
        brain = auto_qa_mod.AIBrain()
        brain.provider_active = "OPENAI"
        brain.init_session("TEST-1M")
        for idx in range(25):
            brain.session_messages.append({"role": "user", "content": [{"type": "text", "text": f"Step {idx}"}]})
            brain.session_messages.append({"role": "assistant", "content": json.dumps({"action_type": "KEY", "action_param": "DPAD_DOWN"})})

        class DummyMission:
            name = "M1"
            title = "Mission 1"
            description = "desc"
            success_criteria = "crit"
            steps_executed = 1
            max_steps = 10

        with patch.object(brain, "chat_turn", return_value=('{"thought": "next", "action_type": "KEY", "action_param": "OK", "defect_detected": null}', "OPENAI")):
            dec = brain.decide_mission_action(DummyMission(), {
                "activity": "MainActivity",
                "focused_sig": "card#1",
                "focused_text": "Card",
                "has_focus_ring": True,
                "focus_ring_color": "ORANGE",
                "video_motion_playing": False,
                "recent_keys": ["DPAD_DOWN"],
                "logcat_alerts": [],
                "ui_summary": "card#1",
            })
        self.assertEqual(dec["action_param"], "OK")
        # 1 sys + 25*2 + 2 new = 53 messages retained (> 30!)
        self.assertEqual(len(brain.session_messages), 53)
        self.assertEqual(len(brain.action_ledger), 1)

    # 6. Regression fixes from video analysis (Gboard TV qqq spam, Phone Search stall, Upcoming 00:45 card)
    def test_driver_keyboard_guards_and_upcoming_kickoff_detection(self):
        from gate import EvidenceGate
        specs = {s.name: s for s in get_missions()}
        dev = device_mod.RealtimeDevice()

        # Stray Gboard in non-keyboard mission -> dismiss via BACK (never spam OK)
        m_cold = specs["MISSION_COLD_START"]
        drv_stray = driver_mod.Driver(dev, EvidenceGate(m_cold), m_cold)
        act_stray = drv_stray.next_action({
            "focused_sig": "searchPhimInput#[0,0][200,80]",
            "focused_text": "Tìm phim",
            "has_dialog": False,
            "keyboard_open": True,
            "all_visible_texts": [("searchPhimInput", "Tìm phim")],
        }, "com.kenhlive.tv/.MainActivity", None, 0.0)
        self.assertEqual(act_stray.type, "KEY")
        self.assertEqual(act_stray.param, "BACK")
        self.assertEqual(act_stray.rule, "keyboard:dismiss_stray")

        # Repeated 'qqqqq' in search box -> anti_repeat BACK
        m_search = specs["MISSION_SEARCH_AND_SETTINGS_FEEDBACK"]
        drv_rep = driver_mod.Driver(dev, EvidenceGate(m_search), m_search)
        act_rep = drv_rep.next_action({
            "focused_sig": "searchInput#[0,0][200,80]",
            "focused_text": "qqqqqqqqq",
            "has_dialog": False,
            "keyboard_open": True,
            "all_visible_texts": [("searchInput", "qqqqqqqqq")],
        }, "com.kenhlive.tv/.MainActivity", None, 0.0)
        self.assertEqual(act_rep.rule, "keyboard:anti_repeat")
        self.assertEqual(act_rep.param, "BACK")

        # Card with 'Lên sóng lúc 00:45' (Gà Vàng 33) without LIVE badge -> skipped as upcoming
        m_stream = specs["MISSION_PLAYER_STREAMING_AND_CONTROLS"]
        drv_up = driver_mod.Driver(dev, EvidenceGate(m_stream), m_stream)
        status_up = drv_up._focused_card_status({
            "focused_sig": "cardRoot#[100,200][500,500]",
            "focused_text": "FK Bodo/Glimt vs LASK Linz",
            "focused_bounds": "[100,200][500,500]",
            "all_visible_texts": [("cardRoot", "FK Bodo/Glimt"), ("cardTimeBadge", "00:45"), ("cardBlv", "Lên sóng lúc 00:45")],
            "all_visible_nodes": [
                {"id": "cardRoot", "text": "FK Bodo/Glimt", "bounds": "[100,200][500,500]"},
                {"id": "cardBlv", "text": "Lên sóng lúc 00:45", "bounds": "[110,450][450,480]"},
            ],
        })
        self.assertEqual(status_up, "upcoming")

        # is_ime_shown() parses dumpsys input_method mInputShown=true
        with patch.object(device_mod, "sh", return_value="  mInputShown=true mIsInputViewShown=true\n"):
            self.assertTrue(dev.is_ime_shown())
        with patch.object(device_mod, "sh", return_value="  mInputShown=false\n"):
            self.assertFalse(dev.is_ime_shown())

    # 7. QA v5 Harness upgrades: landscape bounds, sheet* dialog, dialog clipping detector, live sport gate, rank 3 OSD
    def test_landscape_bounds_and_sheet_dialog_recognition(self):
        dev = device_mod.RealtimeDevice()
        dev._viewport = (1080, 2400)  # wm size stays portrait during landscape rotation
        xml_landscape = (
            '<hierarchy rotation="1">'
            '<node bounds="[0,0][2400,1080]" text="">'
            '<node resource-id="com.kenhlive.tv:id/qualityBtn" text="Cài đặt" bounds="[1650,40][1820,120]" focusable="true" focused="true" />'
            '<node resource-id="com.kenhlive.tv:id/sheetFilmTitle" text="Mật Án Vigil" bounds="[80,180][980,260]" focusable="false" />'
            '</node>'
            '</hierarchy>'
        )
        with patch.object(device_mod, "sh", return_value=xml_landscape):
            st = dev.dump_ui_state()
        texts = [t for _, t in st["all_visible_texts"]]
        self.assertIn("Cài đặt", texts)
        self.assertTrue(st["has_dialog"])
        self.assertIn("sheetFilmTitle", st["dialog_ids"])

    def test_dialog_clipped_controls_detector(self):
        # Clipped Phone landscape dialog: "Tốc độ phát" shown, "Tắt" missing, "Phụ đề" sliced to 9px height at bottom
        ui_clipped = {
            "has_dialog": True,
            "dialog_ids": ["dialogPlayerSettingsRoot"],
            "dialog_bounds": "[100,100][2100,900]",
            "focused_sig": "chip#[200,200][350,260]",
            "all_visible_texts": [
                ("dialogTitle", "Chất lượng hình & âm"),
                ("lbl", "Tốc độ phát"),
                ("lbl2", "Phụ đề"),
            ],
            "all_visible_nodes": [
                {"id": "dialogTitle", "text": "Chất lượng hình & âm", "bounds": "[140,130][800,180]"},
                {"id": "lbl", "text": "Tốc độ phát", "bounds": "[140,700][500,740]"},
                {"id": "lbl2", "text": "Phụ đề", "bounds": "[140,880][300,889]"},
            ],
        }
        ctx = {"reported": set()}
        findings = detectors_mod.detect_dialog_clipped_controls(
            ui_clipped, "com.kenhlive.tv/.PlayerActivity", ctx, "step_053.jpg", 10.0
        )
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["severity"], "HIGH")

        # Clean dialog with "Tắt" visible and full height -> no finding
        ui_clean = {
            "has_dialog": True,
            "dialog_ids": ["dialogPlayerSettingsRoot"],
            "dialog_bounds": "[100,60][2100,960]",
            "focused_sig": "chip#[200,200][350,260]",
            "all_visible_texts": [
                ("dialogTitle", "Chất lượng hình & âm"),
                ("lbl", "Tốc độ phát"),
                ("lbl2", "Phụ đề"),
                ("chipSub", "Tắt"),
            ],
            "all_visible_nodes": [
                {"id": "lbl2", "text": "Phụ đề", "bounds": "[140,760][300,800]"},
                {"id": "chipSub", "text": "Tắt", "bounds": "[140,810][260,880]"},
            ],
        }
        self.assertEqual(
            detectors_mod.detect_dialog_clipped_controls(
                ui_clean, "com.kenhlive.tv/.PlayerActivity", {"reported": set()}, "step_053.jpg", 10.0
            ),
            [],
        )

    def test_live_sport_cards_and_player_title_rank(self):
        # detect_live_sport_cards sets flags on scored live cards on tab 0, ignores nav_live & SAP DA
        ctx_live = {"reported": set()}
        ui_sport = {
            "selected_ids": ["nav_live"],
            "all_visible_nodes": [
                {"id": "nav_live", "text": "TRỰC TIẾP", "bounds": "[100,20][300,100]"},
                {"id": "heroBadge", "text": "TRỰC TIẾP", "bounds": "[60,200][220,240]"},
                {"id": "heroScore", "text": "0 : 1", "bounds": "[460,280][560,340]"},
            ],
            "all_visible_texts": [("nav_live", "TRỰC TIẾP"), ("heroBadge", "TRỰC TIẾP"), ("heroScore", "0 : 1")],
        }
        detectors_mod.detect_live_sport_cards(ui_sport, "com.kenhlive.tv/.MainActivity", ctx_live)
        self.assertTrue(ctx_live.get("live_sport_seen"))
        self.assertTrue(ctx_live.get("live_sport_with_score"))

        ctx_upcoming = {"reported": set()}
        ui_up = {
            "selected_ids": ["nav_home"],
            "all_visible_nodes": [
                {"id": "nav_live", "text": "TRỰC TIẾP", "bounds": "[700,0][900,112]"},
                {"id": "cardBadge", "text": "SẮP ĐÁ", "bounds": "[120,410][200,440]"},
            ],
            "all_visible_texts": [("nav_live", "TRỰC TIẾP"), ("cardBadge", "SẮP ĐÁ")],
        }
        detectors_mod.detect_live_sport_cards(ui_up, "com.kenhlive.tv/.MainActivity", ctx_upcoming)
        self.assertFalse(ctx_upcoming.get("live_sport_seen", False))

        # _player_title_rank: OSD visible (3) > OSD hidden (2) > fallback motion None (2) > no motion (1) > error (0)
        rank = runner_mod.RealtimeRunner._player_title_rank
        self.assertEqual(rank({"motion": True, "ui_state": {"osd_visible": True, "all_visible_texts": []}}), 3)
        self.assertEqual(rank({"motion": True, "ui_state": {"osd_visible": False, "all_visible_texts": []}}), 2)
        self.assertEqual(rank({"motion": True, "ui_state": {"all_visible_texts": []}}), 2)
        self.assertEqual(rank({"motion": False, "ui_state": {"all_visible_texts": []}}), 1)
        self.assertEqual(rank({"motion": True, "ui_state": {"all_visible_texts": [("e", "video_error")]}}), 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)

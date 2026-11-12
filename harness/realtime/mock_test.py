#!/usr/bin/env python3
"""Smoke test offline cho runner realtime (vòng CI-T3): mock RealtimeDevice
bằng ảnh PIL giả + dump UI giả, chạy thật vòng mission (watcher -> observe ->
gate -> driver -> judge) + kiểm chứng các fix CI-T2 bằng frame THẬT của run
42979726992 (OSD gate). Không cần emulator, không gọi vision.

BẢN GỐC nằm ở /tmp/mock_qa_test.py nhưng /tmp bị xóa sau restart VM
2026-11-11 — bản này được khôi phục nguyên văn + các test CI-T5, lưu bền ở
~/workspace/kenhlive-plan/mock_qa_test.py; cuối vòng CI-T5 sẽ commit một
bản copy vào qa/kenhlive_qa/realtime/mock_test.py trong repo.
"""
import io
import json
import os
import sys
import time

sys.path.insert(0, os.path.expanduser("~/workspace/kenhlive-tv/qa/kenhlive_qa/realtime"))
sys.path.insert(0, os.path.expanduser("~/workspace/kenhlive-tv/qa/kenhlive_qa"))

import runner as runner_mod
from device import RealtimeDevice


def _fake_png(seed=0):
    from PIL import Image, ImageDraw
    im = Image.new("RGB", (960, 540), (30, 32, 40))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, 960, 120], fill=(200, 30, 30))
    # seed đổi màu 1 hình chữ nhật lớn để 2 frame khác seed có pixel_diff rõ
    # (dùng cho test fallback motion CI-T5); seed=0 giữ nguyên ảnh gốc.
    d.rectangle([40, 160, 300, 400], fill=(60 + (seed * 53) % 180, 120, 200))
    d.rectangle([340, 160, 600, 400], fill=(40, 180, 90))
    d.rectangle([640, 160, 900, 400], fill=(220, 200, 60))
    d.rectangle([40, 440, 900, 500], fill=(240, 240, 240))
    buf = io.BytesIO()
    im.save(buf, format="PNG")
    return buf.getvalue()


class FakeDevice(RealtimeDevice):
    HOME_DUMP = {
        "focused_sig": "nav_home#[362,0][563,112]",
        "focused_text": "Trang chủ",
        "focused_bounds": "[362,0][563,112]",
        "focusable_count": 8,
        "all_visible_texts": [("nav_home", "Trang chủ"), ("nav_live", "Trực tiếp"),
                              ("row1", "ĐANG PHÁT"), ("row2", "Mới cập nhật")],
        "has_dialog": False,
        "dialog_ids": [],
        "selected_ids": ["nav_home"],
        "ui_summary": "[FOCUSED] nav_home ('Trang chủ') [362,0][563,112]",
        "osd_visible": False,
    }
    WELCOME_DUMP = {
        "focused_sig": "btnCloseFeedback#[564,920][900,1032]",
        "focused_text": "ĐÃ HIỂU / ĐÓNG",
        "focused_bounds": "[564,920][900,1032]",
        "focusable_count": 2,
        "all_visible_texts": [("dialogTitle", "THÔNG BÁO"),
                              ("btnCloseFeedback", "ĐÃ HIỂU / ĐÓNG"),
                              ("btnOpenTelegram", "VÀO NHÓM TELEGRAM")],
        "has_dialog": True,
        "dialog_ids": ["dialogTitle", "btnCloseFeedback"],
        "selected_ids": [],
        "ui_summary": "[FOCUSED] btnCloseFeedback ('ĐÃ HIỂU / ĐÓNG') [564,920][900,1032]",
        "osd_visible": False,
    }

    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self._n = 0
        self.keys = []
        self._dump = dict(self.HOME_DUMP)
        self._activity = "com.kenhlive.tv/.MainActivity"
        self._tab = 6

    def screencap_bytes(self):
        self._n += 1
        return _fake_png(self._n)

    def dump_ui_state(self):
        return dict(self._dump)

    def current_activity(self):
        return self._activity

    def launch_app(self):
        self._activity = "com.kenhlive.tv/.MainActivity"
        return 500

    def checkpoint_logcat(self):
        return None

    def get_pss_memory_mb(self):
        return 0.0

    def detect_focus_ring(self, png_bytes, focused_bounds_str):
        return True, "white", 1.0

    def detect_tab_index(self, ui_state):
        return self._tab

    def send_key(self, key_name):
        self.keys.append(key_name)
        self._note(key_name)
        # giả lập hành vi thật: BACK trong player về MainActivity
        if key_name == "BACK" and "PlayerActivity" in self._activity:
            self._activity = "com.kenhlive.tv/.MainActivity"

    def switch_tab(self, tab_index):
        self._tab = int(tab_index)
        self.keys.append("SWITCH_TAB(%d)" % tab_index)
        self._note("SWITCH_TAB(%d)" % tab_index)


def main():
    runner_mod.VideoRecorder = None
    runner_mod.RealtimeDevice = FakeDevice
    from missions import get_missions
    from driver import Driver
    from gate import EvidenceGate
    specs = {s.name: s for s in get_missions()}

    # --- Test A: dialog chào mừng phải được đóng bằng OK, không kẹt ---
    dev = FakeDevice()
    dev._dump = dict(FakeDevice.WELCOME_DUMP)
    drv = Driver(dev, EvidenceGate(specs["MISSION_COLD_START"]), specs["MISSION_COLD_START"])
    act = drv.next_action(dev._dump, "com.kenhlive.tv/.MainActivity", None, 0.0)
    print("dialog-dismiss action:", act.type, act.param, "| rule:", act.rule)
    assert act.type == "KEY" and act.param == "OK" and act.rule == "dismiss_dialog_ok"
    dev._dump = dict(FakeDevice.HOME_DUMP)
    act2 = drv.next_action(dev._dump, "com.kenhlive.tv/.MainActivity", None, 0.0)
    assert act2.rule != "dismiss_dialog_ok"
    print("DIALOG_DISMISS_OK")

    # --- Test B: video phát trong player -> reset streak (không kẹt) ---
    dev2 = FakeDevice()
    drv2 = Driver(dev2, EvidenceGate(specs["MISSION_WEBPLAYER_DIRECTED_REAL_FILM"]),
                  specs["MISSION_WEBPLAYER_DIRECTED_REAL_FILM"])
    sig = dict(FakeDevice.HOME_DUMP)
    for _ in range(7):
        drv2.note_state(sig, "com.kenhlive.tv/.phim.WebPlayerActivity", motion_playing=True)
    assert not drv2.stuck(), "video đang phát trong player mà vẫn tính kẹt"
    drv3 = Driver(dev2, EvidenceGate(specs["MISSION_WEBPLAYER_DIRECTED_REAL_FILM"]),
                  specs["MISSION_WEBPLAYER_DIRECTED_REAL_FILM"])
    for _ in range(4):
        drv3.note_state(sig, "com.kenhlive.tv/.phim.WebPlayerActivity", motion_playing=False)
    assert drv3.stuck(), "video đứng yên phải tính kẹt ở 3 bước không đổi"
    print("MOTION_STUCK_OK")

    # --- Test B2: motion UNKNOWN trong player không nổ stuck + fallback pixel_diff (CI-T5 mục 2) ---
    # CI-T4 VOD FAIL oan: phim phát thật nhưng watcher đói mẫu -> motion None
    # cả 9 bước -> streak kẹt nổ. Giờ None trong player không tính streak.
    drv_u = Driver(FakeDevice(), EvidenceGate(specs["MISSION_VOD_PLAYER_SEEK_AND_RESUME"]),
                   specs["MISSION_VOD_PLAYER_SEEK_AND_RESUME"])
    for _ in range(7):
        drv_u.note_state(sig, "com.kenhlive.tv/.phim.WebPlayerActivity", motion_playing=None)
    print("motion None x7 trong player stuck:", drv_u.stuck())
    assert not drv_u.stuck(), "motion UNKNOWN trong player không được nổ stuck (FN CI-T4)"
    # Ngoài player, None vẫn xử như False (hành vi cũ): đứng yên 3 bước -> kẹt.
    drv_u2 = Driver(FakeDevice(), EvidenceGate(specs["MISSION_COLD_START"]),
                    specs["MISSION_COLD_START"])
    for _ in range(4):
        drv_u2.note_state(sig, "com.kenhlive.tv/.MainActivity", motion_playing=None)
    assert drv_u2.stuck(), "ngoài player, motion None vẫn tính kẹt như trước"
    # Fallback: 2 frame khác nhau rõ -> pixel_diff > ngưỡng phát (0.35);
    # 2 frame giống hệt -> ~0; thiếu frame -> -1 (UNKNOWN).
    from perception import ScreenWatcher
    d_diff = ScreenWatcher.fallback_pixel_diff(_fake_png(0), _fake_png(5))
    d_same = ScreenWatcher.fallback_pixel_diff(_fake_png(0), _fake_png(0))
    d_none = ScreenWatcher.fallback_pixel_diff(None, _fake_png(0))
    print("fallback pixel_diff khác/giống/thiếu:", round(d_diff, 2), round(d_same, 2), d_none)
    assert d_diff > 0.35, "2 frame khác nhau rõ phải đo được motion qua pixel_diff"
    assert d_same < 0.35, "2 frame giống hệt không được báo motion"
    assert d_none == -1.0, "thiếu frame thì fallback vẫn UNKNOWN (-1)"
    # Tích hợp _observe: watcher đói mẫu (history rỗng) + frame trước khác
    # frame hiện tại -> motion True qua fallback, motion_state True.
    r_obs = runner_mod.RealtimeRunner(out_dir="/tmp/qa_mock_obs", serial=None,
                                      vision_budget=0, no_vision=True)
    r_obs.device._activity = "com.kenhlive.tv/.phim.WebPlayerActivity"
    png_a, png_b = _fake_png(0), _fake_png(5)
    r_obs.watcher._latest_png = png_b
    r_obs.watcher._stable_streak = 5
    r_obs._prev_obs_png = png_a
    obs_fb = r_obs._observe("MISSION_VOD_PLAYER_SEEK_AND_RESUME")
    print("_observe fallback: motion", obs_fb["motion"], "| state", obs_fb["motion_state"],
          "| source", obs_fb["motion_source"], "| delta", round(obs_fb["motion_delta"], 2))
    assert obs_fb["motion"] is True and obs_fb["motion_state"] is True, \
        "watcher đói mẫu nhưng pixel_diff thay đổi rõ -> motion_seen true"
    assert obs_fb["motion_source"] == "fallback_pixel_diff"
    # Frame trước giống hệt -> motion False, state False (đứng yên thật).
    r_obs.watcher._latest_png = png_b
    r_obs.watcher._stable_streak = 5
    r_obs._prev_obs_png = png_b
    obs_st = r_obs._observe("MISSION_VOD_PLAYER_SEEK_AND_RESUME")
    assert obs_st["motion"] is False and obs_st["motion_state"] is False
    # Chưa có frame trước nào -> motion_state None (UNKNOWN, không bịa False).
    r_obs2 = runner_mod.RealtimeRunner(out_dir="/tmp/qa_mock_obs2", serial=None,
                                       vision_budget=0, no_vision=True)
    r_obs2.device._activity = "com.kenhlive.tv/.phim.WebPlayerActivity"
    r_obs2.watcher._latest_png = png_b
    r_obs2.watcher._stable_streak = 5
    obs_un = r_obs2._observe("MISSION_VOD_PLAYER_SEEK_AND_RESUME")
    print("_observe no-prev: motion_state", obs_un["motion_state"], "| source", obs_un["motion_source"])
    assert obs_un["motion_state"] is None, "chưa có frame trước -> motion UNKNOWN (None)"
    print("MOTION_UNKNOWN_NO_STUCK_OK")

    # --- Test B3: driver chỉ mở thẻ LIVE, WebPlayer chưa phát thì bấm Play (CI-T5 mục 3) ---
    # CI-T4 PLAYER_STREAMING FAIL A-B-A-B: mở thẻ [SẮP ĐÁ] ĐTQ 19:00 chưa đá
    # -> loading vô hạn -> player tự thoát -> dao động.
    dev3 = FakeDevice()
    dev3._tab = 0  # mission player cần tab Trực tiếp (0)
    drv6 = Driver(dev3, EvidenceGate(specs["MISSION_PLAYER_STREAMING_AND_CONTROLS"]),
                  specs["MISSION_PLAYER_STREAMING_AND_CONTROLS"])
    ui_upcoming = {
        "focused_sig": "cardRoot#[100,200][500,600]",
        "focused_text": "ĐTQ Việt Nam",
        "focused_bounds": "[100,200][500,600]",
        "all_visible_texts": [("cardRoot", "ĐTQ Việt Nam"), ("cardBadge", "SẮP ĐÁ"),
                              ("cardTime", "19:00")],
        "all_visible_nodes": [
            {"id": "cardRoot", "text": "ĐTQ Việt Nam", "bounds": "[100,200][500,600]"},
            {"id": "cardBadge", "text": "SẮP ĐÁ", "bounds": "[120,210][200,240]"},
            {"id": "cardTime", "text": "19:00", "bounds": "[120,300][200,330]"}],
        "has_dialog": False, "dialog_ids": [],
    }
    a_up = drv6.next_action(ui_upcoming, "com.kenhlive.tv/.MainActivity", None, 0.0)
    print("thẻ [SẮP ĐÁ] ->", a_up.type, a_up.param, "| rule:", a_up.rule)
    assert a_up.type == "KEY" and a_up.param == "DPAD_DOWN" and a_up.rule == "skip_upcoming_card", \
        "thẻ [SẮP ĐÁ] phải bị loại khỏi target, không được mở player"
    # Thẻ LIVE thì mở bình thường.
    ui_live = dict(ui_upcoming,
                   all_visible_texts=[("cardRoot", "South East Melbourne"),
                                      ("cardBadge", "LIVE"), ("cardScoreHome", "54 : 71")],
                   all_visible_nodes=[
                       {"id": "cardRoot", "text": "South East Melbourne", "bounds": "[100,200][500,600]"},
                       {"id": "cardBadge", "text": "LIVE", "bounds": "[120,210][200,240]"}])
    a_live = drv6.next_action(ui_live, "com.kenhlive.tv/.MainActivity", None, 0.0)
    print("thẻ LIVE ->", a_live.type, a_live.param, "| rule:", a_live.rule)
    assert a_live.type == "KEY" and a_live.param == "OK" and a_live.rule == "open_player", \
        "thẻ LIVE phải được mở bằng OK"
    # 'socolive' là tên đài, không phải badge LIVE — không được nhận nhầm.
    assert drv6._focused_card_status(
        {"focused_sig": "cardRoot#[100,200][500,600]", "focused_bounds": "[100,200][500,600]",
         "all_visible_texts": [("rowTitle", "Socolive"), ("cardRoot", "Trận A")],
         "all_visible_nodes": [
             {"id": "rowTitle", "text": "Socolive", "bounds": "[120,210][300,240]"}]}) is None
    # Fallback khi dump không có bounds: cửa sổ ±6 node quanh node focus.
    ui_fb = {"focused_sig": "cardRoot#[100,200][500,600]",
             "focused_text": "ĐTQ Việt Nam",
             "all_visible_texts": [("cardRoot", "ĐTQ Việt Nam"), ("cardBadge", "SẮP ĐÁ")],
             "has_dialog": False, "dialog_ids": []}
    a_fb = drv6.next_action(ui_fb, "com.kenhlive.tv/.MainActivity", None, 0.0)
    assert a_fb.rule == "skip_upcoming_card", "fallback adjacency cũng phải loại thẻ [SẮP ĐÁ]"
    # WebPlayer đã mở mà video chưa phát: WAIT 1 lần rồi bấm Play (OK),
    # sau đó lại WAIT (không bấm Play liên tục kẻo toggle thành Pause).
    drv7 = Driver(FakeDevice(), EvidenceGate(specs["MISSION_VOD_PLAYER_SEEK_AND_RESUME"]),
                  specs["MISSION_VOD_PLAYER_SEEK_AND_RESUME"])
    ui_wp = dict(FakeDevice.HOME_DUMP, focused_sig="btnPlay#[800,900][1000,1000]",
                 focused_text="Phát")
    a_w1 = drv7.next_action(ui_wp, "com.kenhlive.tv/.phim.WebPlayerActivity", None, 0.0)
    a_w2 = drv7.next_action(ui_wp, "com.kenhlive.tv/.phim.WebPlayerActivity", None, 0.0)
    a_w3 = drv7.next_action(ui_wp, "com.kenhlive.tv/.phim.WebPlayerActivity", None, 0.0)
    print("WebPlayer chưa phát:", [(a.type, a.param, a.rule) for a in (a_w1, a_w2, a_w3)])
    assert (a_w1.type, a_w1.param, a_w1.rule) == ("WAIT", "2.0", "wait_stream")
    assert (a_w2.type, a_w2.param, a_w2.rule) == ("KEY", "OK", "play_webplayer"), \
        "WebPlayer chưa phát sau 1 lần chờ thì phải bấm Play thay vì chỉ WAIT"
    assert a_w3.rule == "wait_stream", "đã bấm Play 1 lần rồi thì quay lại WAIT"
    print("LIVE_TARGET_ONLY_OK")

    # --- Test N4: skip-upcoming phổ quát + goto thẻ LIVE (CI-T6 mục 5+6) ---
    # Mục 5 — hình CI-T5 ROOM_PICKER step_013/014: focus blvCardRoot, badge
    # [SẮP ĐÁ] có trong dump nhưng id node text KHÔNG khớp id view đang
    # focus (fid lookup thất bại) và KHÔNG có bounds -> luật cũ bỏ qua,
    # driver mở thẻ INTERF 19:00 vào player loading vô hạn. Fallback mới
    # theo focused_text phải bắt được. Và luật giờ phổ quát: mission KHÔNG
    # cần player/dialog (vd SCHEDULE_EPG) cũng phải tránh thẻ [SẮP ĐÁ].
    _ui_no_bounds = {
        "focused_sig": "blvCardRoot#[180,408][666,664]",
        "focused_text": "INTERF 19:00",
        # id node text trong dump là cardMain, KHÁC id view đang focus
        # (blvCardRoot) -> lookup theo fid thất bại, chỉ còn fallback theo
        # focused_text; badge SẮP ĐÁ nằm ±10 node quanh cardMain.
        "all_visible_texts": [
            ("nav0", "Trực tiếp"), ("rowTitle", "Bóng đá"), ("cardA", "VIE - CHI"),
            ("cardMain", "INTERF 19:00"), ("cardBadge", "SẮP ĐÁ"),
            ("cardTime", "19:00")],
        "has_dialog": False, "dialog_ids": []}
    _dev8 = FakeDevice()
    _dev8._tab = 0  # ROOM_PICKER ở tab Trực tiếp (0)
    drv8 = Driver(_dev8, EvidenceGate(specs["MISSION_SPORTS_ROOM_PICKER"]),
                  specs["MISSION_SPORTS_ROOM_PICKER"])
    a_5 = drv8.next_action(_ui_no_bounds, "com.kenhlive.tv/.MainActivity", None, 0.0)
    print("ROOM_PICKER thẻ [SẮP ĐÁ] (không bounds, fid lệch) ->", a_5.param, "| rule:", a_5.rule)
    assert a_5.rule == "skip_upcoming_card", \
        "fallback focused_text phải loại thẻ [SẮP ĐÁ] của ROOM_PICKER"
    _dev9 = FakeDevice()
    _dev9._tab = 1  # SCHEDULE_EPG ở tab Lịch thi đấu (1)
    drv9 = Driver(_dev9, EvidenceGate(specs["MISSION_SCHEDULE_EPG_AND_FIXTURE_TAP"]),
                  specs["MISSION_SCHEDULE_EPG_AND_FIXTURE_TAP"])
    a_5b = drv9.next_action(_ui_no_bounds, "com.kenhlive.tv/.MainActivity", None, 0.0)
    assert a_5b.rule == "skip_upcoming_card", \
        "luật skip-upcoming phải áp cho MỌI mission, không chỉ mission mở player"
    print("SKIP_UPCOMING_UNIVERSAL_OK")
    # Mục 6 — PLAYER_STREAMING: focus ở nav, thẻ LIVE ở dưới -> đi tới thẻ
    # LIVE (goto_live_card) thay vì bấm OK mù; đã đứng trên thẻ LIVE thì
    # bấm OK như thường; không có thẻ LIVE thì hành vi cũ (OK).
    dev_live = FakeDevice()
    dev_live._tab = 0
    drv10 = Driver(dev_live, EvidenceGate(specs["MISSION_PLAYER_STREAMING_AND_CONTROLS"]),
                   specs["MISSION_PLAYER_STREAMING_AND_CONTROLS"])
    _ui_goto = {
        "focused_sig": "nav_home#[362,0][563,112]",
        "focused_text": "Trang chủ",
        "focused_bounds": "[362,0][563,112]",
        "all_visible_texts": [("nav_home", "Trang chủ"), ("cardRoot", "South East Melbourne"),
                              ("cardBadge", "LIVE"), ("cardScore", "54 : 71")],
        "all_visible_nodes": [
            {"id": "nav_home", "text": "Trang chủ", "bounds": "[362,0][563,112]"},
            {"id": "cardRoot", "text": "South East Melbourne", "bounds": "[100,400][500,700]"},
            {"id": "cardBadge", "text": "LIVE", "bounds": "[120,410][200,440]"}],
        "has_dialog": False, "dialog_ids": []}
    a_6 = drv10.next_action(_ui_goto, "com.kenhlive.tv/.MainActivity", None, 0.0)
    print("focus nav, thẻ LIVE dưới ->", a_6.type, a_6.param, "| rule:", a_6.rule)
    assert a_6.rule == "goto_live_card" and a_6.param == "DPAD_DOWN", \
        "đang ở nav thì phải đi tới thẻ LIVE trước khi mở player"
    _ui_on_live = dict(_ui_goto,
                       focused_sig="cardRoot#[100,400][500,700]",
                       focused_text="South East Melbourne",
                       focused_bounds="[100,400][500,700]")
    a_6b = drv10.next_action(_ui_on_live, "com.kenhlive.tv/.MainActivity", None, 0.0)
    print("đã đứng trên thẻ LIVE ->", a_6b.type, a_6b.param, "| rule:", a_6b.rule)
    assert a_6b.type == "KEY" and a_6b.param == "OK" and a_6b.rule == "open_player", \
        "đã đứng trên thẻ LIVE thì bấm OK mở player"
    _ui_no_live = dict(_ui_goto,
                       all_visible_texts=[("nav_home", "Trang chủ"), ("cardRoot", "Trận A"),
                                          ("cardBadge", "SẮP ĐÁ")],
                       all_visible_nodes=[
                           {"id": "nav_home", "text": "Trang chủ", "bounds": "[362,0][563,112]"},
                           {"id": "cardRoot", "text": "Trận A", "bounds": "[100,400][500,700]"},
                           {"id": "cardBadge", "text": "SẮP ĐÁ", "bounds": "[120,410][200,440]"}])
    a_6c = drv10.next_action(_ui_no_live, "com.kenhlive.tv/.MainActivity", None, 0.0)
    assert a_6c.rule == "scan_live_card", \
        ("CI-T9 nhóm B mục (3) — Thử 3: không có thẻ LIVE thì hành vi cũ "
         "(OK mù) mở nhầm KUW–SYR đá ngày mai vì focus không text; giờ "
         "phải quét xuống tìm thẻ LIVE, không được bấm OK mù")
    print("GOTO_LIVE_CARD_OK")

    # --- Test N5: focus-trap chỉ tính quan sát khác nhau + bỏ shot trùng (CI-T6 mục 7) ---
    # CI-T5: 011=012, 055=056, 075=076 là cùng 1 frame chụp lại — hist nhận
    # 2 entry giống hệt từ 1 trạng thái thật -> tố kẹt oan (step_075).
    import hashlib as _hl
    from detectors import detect_focus_trap as _dft

    def _ui_trap(kb=False):
        texts = [("cardA", "Trận A")]
        if kb:
            texts += [("k%d" % i, chr(97 + i)) for i in range(10)]
        return {"focused_sig": "cardA#[100,200][500,600]",
                "focused_bounds": "[100,200][500,600]",
                "focusable_count": 8, "has_dialog": False,
                "all_visible_texts": texts, "keyboard_open": kb}

    # (a) cùng frame 3 lần + DPAD_DOWN -> không tố, hist chỉ 1 entry
    # (quan sát đầu vẫn tính, 2 lần chụp trùng sau không thêm).
    _ctx = {"last_key": "DPAD_DOWN"}
    _h = _hl.sha256(b"FAKEPNG-BYTES-1").hexdigest()
    _ctx["frame_hash"], _ctx["frame_hash_prev"] = _h, None
    _f1 = _dft(_ui_trap(), "MainActivity", _ctx, "step_001.jpg", 1.0)
    _ctx["frame_hash_prev"] = _h
    _f2 = _dft(_ui_trap(), "MainActivity", _ctx, "step_002.jpg", 2.0)
    _f3 = _dft(_ui_trap(), "MainActivity", _ctx, "step_003.jpg", 3.0)
    print("focus-trap cùng frame 3x ->", _f1, _f2, _f3, "| hist:", len(_ctx.get("focus_hist", [])))
    assert not _f1 and not _f2 and not _f3 and len(_ctx.get("focus_hist", [])) == 1
    # (b) 3 frame KHÁC NHAU, cùng sig + cùng hướng -> tố 1 finding MEDIUM.
    _ctx2 = {"last_key": "DPAD_DOWN"}
    for _i in range(3):
        _hh = _hl.sha256(("PNG-%d" % _i).encode()).hexdigest()
        _ctx2["frame_hash"] = _hh
        _out = _dft(_ui_trap(), "MainActivity", _ctx2, "step_%03d.jpg" % _i, float(_i))
        _ctx2["frame_hash_prev"] = _hh
    assert len(_out) == 1 and _out[0]["severity"] == "MEDIUM", \
        "3 quan sát khác nhau, focus đứng yên -> phải tố kẹt"
    # (c) bàn phím mở, 3 frame khác nhau -> không tố (đang gõ, đứng yên là đúng).
    _ctx3 = {"last_key": "DPAD_DOWN"}
    for _i in range(3):
        _hh = _hl.sha256(("KB-%d" % _i).encode()).hexdigest()
        _ctx3["frame_hash"] = _hh
        _out3 = _dft(_ui_trap(kb=True), "MainActivity", _ctx3, "step_%03d.jpg" % _i, float(_i))
        _ctx3["frame_hash_prev"] = _hh
    assert not _out3, "bàn phím đang mở thì focus đứng yên không phải kẹt"
    # (d) tích hợp _observe: cùng PNG 2 lần -> lần 2 duplicate_frame True
    # và không lưu shot; PNG khác -> duplicate False, lưu shot bình thường.
    r_dup = runner_mod.RealtimeRunner(out_dir="/tmp/qa_mock_obs_dup", serial=None,
                                      vision_budget=0, no_vision=True)
    r_dup.device._activity = "com.kenhlive.tv/.MainActivity"
    _png_dup = _fake_png(0)
    r_dup.watcher._latest_png = _png_dup
    r_dup.watcher._stable_streak = 5
    _o1 = r_dup._observe("MISSION_COLD_START")
    r_dup.watcher._latest_png = _png_dup
    r_dup.watcher._stable_streak = 5
    _o2 = r_dup._observe("MISSION_COLD_START")
    r_dup.watcher._latest_png = _fake_png(5)
    r_dup.watcher._stable_streak = 5
    _o3 = r_dup._observe("MISSION_COLD_START")
    print("duplicate frame: o1", _o1["duplicate_frame"], _o1["frame_file"],
          "| o2", _o2["duplicate_frame"], _o2["frame_file"],
          "| o3", _o3["duplicate_frame"], bool(_o3["frame_file"]))
    assert _o1["duplicate_frame"] is False and _o1["frame_file"], "quan sát đầu lưu shot"
    assert _o2["duplicate_frame"] is True and _o2["frame_file"] is None, \
        "frame trùng quan sát trước và không có defect -> không lưu shot"
    assert _o3["duplicate_frame"] is False and _o3["frame_file"], "frame khác thì lưu shot"
    print("FOCUS_TRAP_DEDUP_OK")

    # --- Test N11: focus-trap + bàn phím theo ẢNH, không theo dump (CI-T7 mục 3) ---
    # CI-T6 tố oan focus-trap MEDIUM ở step_066/067: bàn phím QWERTY in-app
    # đang mở (phím focus đổi ⇧ -> 'z' -> 'q') nhưng dump KHÔNG có node phím
    # nào (ui_state chỉ có 5 trường focused) nên guard đếm ký tự trong dump
    # không thấy gì; mock N5(c) cũ truyền keyboard_open=True bằng tay nên
    # không chứng minh được hành vi live. Mock mới: dump KHÔNG có node bàn
    # phím, chỉ có ẢNH bàn phím -> vẫn phải nhận ra đang gõ, không tố kẹt.
    from detectors import detect_keyboard_from_image as _kb_img
    assert _kb_img(None) is False
    assert _kb_img(_fake_png(0)) is False, "ảnh thường không có bàn phím"
    # (a) ảnh bàn phím tổng hợp (lưới QWERTY: 4 hàng phím xám trên nền tối).
    from PIL import Image as _Image11, ImageDraw as _Draw11
    _im11 = _Image11.new("RGB", (960, 540), (5, 5, 8))
    _d11 = _Draw11.Draw(_im11)
    _d11.rectangle([290, 290, 720, 530], fill=(32, 32, 32))
    for _cy in (377, 420, 463, 506):
        for _i in range(10):
            _x0 = 310 + _i * 43
            _d11.rectangle([_x0, _cy - 18, _x0 + 38, _cy + 18], fill=(55, 55, 55))
    _buf11 = io.BytesIO()
    _im11.save(_buf11, format="PNG")
    _png_kb = _buf11.getvalue()
    assert _kb_img(_png_kb) is True, "ảnh lưới phím QWERTY phải nhận là bàn phím mở"
    # (b) frame THẬT CI-T6: 066/067/071 có bàn phím -> True; 011/026/051/055 không -> False.
    _shots11 = os.path.expanduser("~/workspace/kenhlive-plan/qa-run-43027661716/qa-report-realtime/shots")
    for _f, _want in (("step_066_search_a.jpg", True), ("step_067_search_a.jpg", True),
                      ("step_071_dpad_cha.jpg", True), ("step_011_sports_r.jpg", False),
                      ("step_026_home_bil.jpg", False), ("step_051_phim_epi.jpg", False),
                      ("step_055_vod_play.jpg", False)):
        _got = _kb_img(open(os.path.join(_shots11, _f), "rb").read())
        print("keyboard ảnh %s -> %s (muốn %s)" % (_f, _got, _want))
        assert _got is _want, "frame thật %s: keyboard=%s, muốn %s" % (_f, _got, _want)
    # (c) tích hợp focus-trap: dump KHÔNG có node phím (keyboard_open False),
    # 3 quan sát khác nhau cùng sig + DPAD_DOWN, ảnh là bàn phím -> KHÔNG tố.
    _ctx11 = {"last_key": "DPAD_DOWN"}
    for _i in range(3):
        _hh = _hl.sha256(("KBIMG-%d" % _i).encode()).hexdigest()
        _ctx11["frame_hash"] = _hh
        _out11 = _dft(_ui_trap(), "MainActivity", _ctx11, "step_%03d.jpg" % _i,
                      float(_i), _png_kb)
        _ctx11["frame_hash_prev"] = _hh
    print("focus-trap + ảnh bàn phím ->", _out11,
          "| keyboard_open_image:", _ctx11.get("keyboard_open_image"))
    assert not _out11, "dump không có node phím nhưng ẢNH có bàn phím thì không được tố kẹt"
    assert _ctx11.get("keyboard_open_image") is True
    # (d) cùng dump đó, ảnh thường (không bàn phím) -> vẫn tố kẹt như cũ.
    _ctx11b = {"last_key": "DPAD_DOWN"}
    for _i in range(3):
        _hh = _hl.sha256(("PLAIN-%d" % _i).encode()).hexdigest()
        _ctx11b["frame_hash"] = _hh
        _out11b = _dft(_ui_trap(), "MainActivity", _ctx11b, "step_%03d.jpg" % _i,
                       float(_i), _fake_png(_i))
        _ctx11b["frame_hash_prev"] = _hh
    assert len(_out11b) == 1 and _out11b[0]["severity"] == "MEDIUM", \
        "ảnh không có bàn phím thì kẹt thật vẫn phải tố"
    assert _ctx11b.get("keyboard_open_image") is False
    print("KEYBOARD_FROM_IMAGE_OK")

    # --- Test N14: dedup shot trùng ở _finish_mission + giữa mission (CI-T7 mục 6) ---
    # CI-T6: 046=047, 026=037 là cùng 1 ảnh nhưng lưu 2 file — _observe có
    # check duplicate_frame, _finish_mission là đường bypass (luôn lưu frame
    # cuối mission nếu file chưa tồn tại, không so nội dung). Sửa: _save_frame
    # dedup theo sha256 PNG (trả lại path đã lưu), _finish_mission ghi rõ
    # shot nào được dùng lại (evidence_frame_duplicate_of).
    # Dọn thư mục out trước: file sót từ lần chạy mock trước sẽ làm mission 1
    # bỏ qua lưu (file đã tồn tại) khiến hash không được ghi, dedup sai lệch.
    import shutil as _shutil14
    _shutil14.rmtree("/tmp/qa_mock_dedup", ignore_errors=True)
    _shutil14.rmtree("/tmp/qa_mock_dedup2", ignore_errors=True)
    _png_dup14 = _fake_png(0)
    r14 = runner_mod.RealtimeRunner(out_dir="/tmp/qa_mock_dedup", serial=None,
                                    vision_budget=0, no_vision=True)
    _s14a = r14._save_frame(_png_dup14, "step_001_x")
    _s14b = r14._save_frame(_png_dup14, "step_002_x")
    print("save cùng PNG 2 lần ->", _s14a, "|", _s14b)
    assert _s14a == _s14b and _s14a is not None, \
        "cùng 1 ảnh thì _save_frame phải trả lại cùng 1 path, không ghi trùng"
    assert _s14a != r14._save_frame(_fake_png(5), "step_003_x"), \
        "ảnh khác thì vẫn lưu file riêng"

    class _DupDevice14(FakeDevice):
        def screencap_bytes(self):
            return _fake_png(0)  # device trả cùng 1 frame mọi lần

    _orig_dev14 = runner_mod.RealtimeDevice
    runner_mod.RealtimeDevice = _DupDevice14
    try:
        r14b = runner_mod.RealtimeRunner(out_dir="/tmp/qa_mock_dedup2", serial=None,
                                         vision_budget=0, no_vision=True)
        _rep14 = r14b.run([specs["MISSION_COLD_START"], specs["MISSION_COLD_START"]])
    finally:
        runner_mod.RealtimeDevice = _orig_dev14
    _shots14 = sorted(os.listdir(os.path.join("/tmp/qa_mock_dedup2", "shots")))
    print("2 mission cùng frame: shots:", _shots14, "| outcomes:",
          [(m["name"], m["outcome"]) for m in r14b.mission_results])
    assert len(_shots14) == 1, \
        "2 mission cùng 1 frame cuối thì chỉ được lưu 1 shot, được %s" % _shots14
    assert r14b.mission_results[1].get("evidence_frame_duplicate_of") == "shots/" + _shots14[0], \
        "mission 2 phải ghi rõ dùng lại shot của mission 1"
    assert all(m["outcome"] == "PASS" for m in r14b.mission_results), \
        "dedup không được làm đổi outcome mission"
    print("DEDUP_FINISH_MISSION_OK")

    # --- Test N15: đồng bộ screenshot/dump (CI-T7 mục 7) ---
    # CI-T6 EPISODE_PICKER: frame step_051 không thấy dialog dù dump ghi
    # 'Tập 1' — chụp trước, dump sau, dialog mở giữa hai lần lấy mẫu.
    # Sửa: dump -> chụp -> dump kiểm chứng; lệch thì chụp lại + dump lại.
    _DUMP_A15 = dict(FakeDevice.HOME_DUMP)
    _DUMP_B15 = {
        "focused_sig": "episodeList#[100,300][800,900]",
        "focused_text": "Tập 1",
        "focused_bounds": "[100,300][800,900]",
        "focusable_count": 5,
        "all_visible_texts": [("episodeList", "Tập 1"), ("episodeList", "Tập 2")],
        "all_visible_nodes": [{"id": "episodeList", "text": "Tập 1",
                               "bounds": "[100,300][800,900]"}],
        "has_dialog": True,
        "dialog_ids": ["episodeList"],
        "selected_ids": [],
        "ui_summary": "[FOCUSED] episodeList ('Tập 1') [100,300][800,900]",
        "osd_visible": False,
    }

    class _ScriptedDevice15(FakeDevice):
        # dump lần 1: màn thường (chưa dialog); dump 2+ : dialog đã mở.
        def __init__(self, *a, **k):
            super().__init__(*a, **k)
            self._dumps = 0

        def dump_ui_state(self):
            self._dumps += 1
            return dict(_DUMP_B15 if self._dumps >= 2 else _DUMP_A15)

    _orig_dev15 = runner_mod.RealtimeDevice
    runner_mod.RealtimeDevice = _ScriptedDevice15
    try:
        r15 = runner_mod.RealtimeRunner(out_dir="/tmp/qa_mock_sync", serial=None,
                                        vision_budget=0, no_vision=True)
        r15.device._activity = "com.kenhlive.tv/.MainActivity"
        r15.watcher._latest_png = _fake_png(0)
        r15.watcher._stable_streak = 5
        _o15 = r15._observe("MISSION_PHIM_EPISODE_PICKER_AND_FAVORITE")
    finally:
        runner_mod.RealtimeDevice = _orig_dev15
    print("observe lệch dump/chụp -> has_dialog:", _o15["ui_state"]["has_dialog"],
          "| focused:", _o15["ui_state"]["focused_text"],
          "| sync_retries:", getattr(r15, "_sync_retries", 0),
          "| dump calls:", r15.device._dumps)
    assert _o15["ui_state"]["has_dialog"] is True, \
        "dialog mở giữa dump đầu và lúc chụp thì observation phải ghi dialog (bộ sau)"
    assert _o15["ui_state"]["focused_text"] == "Tập 1"
    assert getattr(r15, "_sync_retries", 0) == 1, "lệch 1 lần thì retry đúng 1 lần"
    assert r15.device._dumps == 3, "dump đầu + kiểm chứng + dump lại = 3 lần"
    # Không lệch thì không retry (dump tĩnh như cũ).
    r15b = runner_mod.RealtimeRunner(out_dir="/tmp/qa_mock_sync2", serial=None,
                                     vision_budget=0, no_vision=True)
    r15b.device._activity = "com.kenhlive.tv/.MainActivity"
    r15b.watcher._latest_png = _fake_png(0)
    r15b.watcher._stable_streak = 5
    _o15b = r15b._observe("MISSION_COLD_START")
    assert getattr(r15b, "_sync_retries", 0) == 0, "dump ổn định thì không chụp lại"
    assert _o15b["ui_state"]["has_dialog"] is False
    print("SYNC_SHOT_DUMP_OK")

    # --- Test N16: IPTV_EPG cần vision_confirm tên kênh đang phát (CI-T7 mục 8,
    # H4 trial 5) ---
    # CI-T6 PASS mềm: frame chỉ thấy list kênh, không thấy EPG text mà vẫn
    # PASS cứng. Giờ mission bắt buộc vision (xác nhận tên kênh + kênh đang
    # phát trong frame): đủ tín hiệu rẻ mà chưa có vision thì VISION_PENDING,
    # không PASS.
    # H4 (trial 5 run 43183031119): target cũ đòi EPG TRONG PLAYER là sai với
    # app thật — OSD player chỉ hiện tên kênh, EPG chỉ có ở thẻ lưới
    # (step_041: 'Khám phá Việt Nam…' dưới tên kênh). Target mới chỉ đòi tên
    # kênh + đang phát; EPG lấy từ thẻ lưới qua required_texts=['kênh']
    # (lưới đã thấy trong mission). Vision xác nhận tên kênh đang phát (không
    # cần EPG trong khung player) thì PASS.
    from gate import EvidenceGate as _EG16
    _spec16 = specs["MISSION_IPTV_EPG_AND_ZAPPING_PLAYER"]
    assert _spec16.needs_vision is True, "IPTV_EPG phải cần vision_confirm"
    assert "tên kênh" in _spec16.target_desc, \
        "target_desc phải yêu cầu thấy tên kênh đang phát trong frame"
    assert "EPG" not in _spec16.target_desc, \
        "H4: target không được đòi EPG trong player — OSD player không hiện EPG, EPG chỉ có ở thẻ lưới"
    assert "kênh" in _spec16.required_texts, \
        "H4: EPG lấy từ thẻ lưới — mission phải yêu cầu text 'kênh' (lưới đã thấy)"
    _g16 = _EG16(_spec16)
    # Bước lưới (tab IPTV): thấy header đếm kênh -> bank text 'kênh'.
    _g16.observe("com.kenhlive.tv/.MainActivity", ["Địa Phương — 66 kênh"],
                 [], False, False, 10.0)
    for _t in (20.0, 30.0, 40.0):
        _g16.observe("com.kenhlive.tv/.PlayerActivity", [], [], False, True, _t)
    _v16, _r16, _ = _g16.evaluate("step_004.jpg")
    print("IPTV_EPG đủ tín hiệu rẻ, chưa vision ->", _v16, "|", _r16)
    assert _v16 == "VISION_PENDING", "chỉ thấy lưới/player mà chưa vision thì không được PASS"
    _g16.record_vision(True, "step_004.jpg", 40.0,
                       "đang phát VTV Cần Thơ, tên kênh hiện trên OSD")
    _v16b, _r16b, _ = _g16.evaluate("step_004.jpg")
    assert _v16b == "PASS", "vision xác nhận tên kênh đang phát thì PASS (không cần EPG trong player)"
    print("IPTV_EPG_VISION_OK")

    # --- Test N17: detector điểm số trực tiếp ở Schedule (CI-T7 mục 9) ---
    # Lỗi thật từ CI-T3, mắt thấy ở CI-T6: hàng LIVE hiện giờ kickoff
    # '18:30'/'18:35' thay vì tỉ số. Detector gom node theo hàng (bounds):
    # hàng LIVE + token giờ kickoff 'HH:MM' mà không có token tỉ số 'X : Y'
    # -> tố (cần thấy 2 lần quan sát). Hàng SẮP ĐÁ hiện giờ là đúng, hàng
    # LIVE đã có tỉ số là đúng, màn không phải lịch thì không chạy.
    from detectors import detect_schedule_live_no_score as _d_sched

    def _ui_sched():
        _nodes = [
            # Hàng 1: LIVE, chỉ có giờ kickoff 18:30 -> PHẢI TỐ.
            {"id": "schedCard", "text": "Vietnam vs Thailand", "bounds": "[100,400][900,560]"},
            {"id": "cardBadge", "text": "LIVE", "bounds": "[820,420][880,450]"},
            {"id": "schedTime", "text": "18:30", "bounds": "[820,470][880,500]"},
            # Hàng 2: LIVE, đã có tỉ số 2 : 1 -> đúng, không tố.
            {"id": "schedCard", "text": "Japan vs Korea", "bounds": "[100,600][900,760]"},
            {"id": "cardBadge", "text": "LIVE", "bounds": "[820,620][880,650]"},
            {"id": "cardScore", "text": "2 : 1", "bounds": "[820,670][880,700]"},
            # Hàng 3: SẮP ĐÁ, giờ kickoff 19:00 -> đúng, không tố.
            {"id": "schedCard", "text": "Inter vs Milan", "bounds": "[100,800][900,960]"},
            {"id": "cardBadge", "text": "SẮP ĐÁ", "bounds": "[820,820][880,850]"},
            {"id": "schedTime", "text": "19:00", "bounds": "[820,870][880,900]"},
        ]
        return {"focused_sig": "schedCard#[100,400][900,560]",
                "focused_text": "Vietnam vs Thailand",
                "focused_bounds": "[100,400][900,560]",
                "focusable_count": 8, "has_dialog": False,
                "all_visible_texts": [(n["id"], n["text"]) for n in _nodes],
                "all_visible_nodes": _nodes}

    _ui17 = _ui_sched()
    _ctx17 = {"reported": set()}
    _f17a = _d_sched(_ui17, "com.kenhlive.tv/.MainActivity", _ctx17, "step_001.jpg", 1.0)
    print("Schedule LIVE 18:30 lần 1 ->", _f17a)
    assert _f17a == [], "lần đầu thấy chỉ ghi nhận, chưa tố (cần ổn định 2 lần)"
    _f17b = _d_sched(_ui17, "com.kenhlive.tv/.MainActivity", _ctx17, "step_002.jpg", 2.0)
    print("Schedule LIVE 18:30 lần 2 ->", [f["issue"] for f in _f17b])
    assert len(_f17b) == 1 and _f17b[0]["severity"] == "HIGH", \
        "hàng LIVE chỉ hiện giờ kickoff phải tố HIGH ở lần thấy thứ 2"
    assert "18:30" in _f17b[0]["issue"] and "19:00" not in _f17b[0]["issue"], \
        "chỉ tố hàng LIVE 18:30, không tố hàng SẮP ĐÁ 19:00 hay hàng đã có tỉ số"
    assert "2 : 1" not in (_f17b[0]["detail"] or ""), "hàng đã có tỉ số không được tố"
    # Lần 3: không tố trùng (reported).
    assert _d_sched(_ui17, "com.kenhlive.tv/.MainActivity", _ctx17, "step_003.jpg", 3.0) == []
    # Màn không phải lịch (không có id 'sched') -> không chạy.
    _ui17b = _ui_sched()
    for _n in _ui17b["all_visible_nodes"]:
        _n["id"] = _n["id"].replace("sched", "live")
    _ui17b["all_visible_texts"] = [(n["id"], n["text"]) for n in _ui17b["all_visible_nodes"]]
    assert _d_sched(_ui17b, "com.kenhlive.tv/.MainActivity", {"reported": set()},
                    "step_001.jpg", 1.0) == [], "không có ngữ cảnh lịch thì không tố"
    print("SCHEDULE_LIVE_SCORE_OK")

    # --- Test N6: bằng chứng thời gian phát tăng (CI-T6 mục 8) ---
    # CI-T5 WebPlayer đóng băng 00:20 qua 3 quan sát mà vẫn PASS — giờ phải
    # FAIL (hoặc UNVERIFIED nếu không đọc được đồng hồ). Chỉ 2 mission VOD
    # có needs_playback_progress; live stream không có elapsed clock nên
    # không ép (xem DESIGN §15.8 mục 8).
    from gate import EvidenceGate as _EG6
    assert specs["MISSION_PLAYER_STREAMING_AND_CONTROLS"].needs_playback_progress is False, \
        "live stream không có elapsed clock — không được ép playback progress"
    assert specs["MISSION_VOD_PLAYER_SEEK_AND_RESUME"].needs_playback_progress is True
    assert specs["MISSION_WEBPLAYER_DIRECTED_REAL_FILM"].needs_playback_progress is True

    def _gate_pb(seq, vision=True):
        g = _EG6(specs["MISSION_VOD_PLAYER_SEEK_AND_RESUME"])
        for t, pb in seq:
            g.observe("com.kenhlive.tv/.phim.WebPlayerActivity", [], [], False, True, t)
            g.observe_playback(pb, t)
        if vision:
            g.record_vision(True, "step_010.jpg", seq[-1][0], "phim đang phát")
        return g

    # Đóng băng 00:20 qua 10 quan sát -> FAIL, lý do nêu playback.
    _seq_frozen = [(float(i * 10), 20) for i in range(1, 11)]
    _gf = _gate_pb(_seq_frozen)
    assert _gf.playback_status() == "frozen"
    assert any(m.startswith("playback:") for m in _gf.missing_summary())
    _vf, _rf, _ = _gf.evaluate("step_010.jpg")
    print("playback đóng băng 00:20 x10 ->", _vf, "|", _rf)
    assert _vf == "FAIL" and "playback" in _rf
    # Tăng 20 -> 25 -> 31 ... -> PASS.
    _seq_ok = [(float(i * 10), 20 + 5 * (i - 1)) for i in range(1, 11)]
    _go = _gate_pb(_seq_ok)
    assert _go.playback_status() == "increasing"
    assert not any(m.startswith("playback:") for m in _go.missing_summary())
    _vo, _ro, _ = _go.evaluate("step_010.jpg")
    print("playback tăng 20->65 ->", _vo, "|", _ro)
    assert _vo == "PASS"
    # Không đọc được đồng hồ (unknown) sau >= 2 quan sát -> KHÔNG PASS tự
    # do nữa (CI-T7 mục 4; luật CI-T6 cũ cho unknown PASS là lỗ false-pass
    # — CI-T6 readings [] + unknown ở mọi mission player mà vẫn PASS).
    # Live: FAIL ở max_steps; replay downgrade thành UNVERIFIED.
    _seq_un = [(float(i * 10), None) for i in range(1, 11)]
    _gu = _gate_pb(_seq_un)
    assert _gu.playback_status() == "unknown"
    assert any(m.startswith("playback:") for m in _gu.missing_summary())
    _vu, _ru, _ = _gu.evaluate("step_010.jpg")
    print("playback unknown x10 ->", _vu, "|", _ru)
    assert _vu == "FAIL" and "playback" in _ru
    # Đơn điệu (CI-T7 mục 4): dãy mắt đọc CI-T6 00:20->00:00->00:30->00:20
    # có max-min=30s nên playback_status() cũ vẫn 'increasing' -> PASS oan
    # dù frame đóng băng 60,3s (step_055 = step_059 pixel-identical).
    _seq_nm = [(float(i * 10), v) for i, v in
               enumerate([20, 0, 30, 20, 25, 30, 20, 25, 30, 35], start=1)]
    _gnm = _gate_pb(_seq_nm)
    assert _gnm.playback_status() == "increasing", \
        "max-min=35s nên status cũ vẫn increasing — đó chính là lỗ hổng"
    _mono_nm, _det_nm = _gnm.playback_monotonic()
    print("playback không đơn điệu 20->0->30->20 -> mono:", _mono_nm, _det_nm)
    assert _mono_nm is False, "lùi 30->20 không sau tua ngược phải tố"
    assert any(m.startswith("playback:") for m in _gnm.missing_summary())
    _vnm, _rnm, _ = _gnm.evaluate("step_010.jpg")
    print("playback không đơn điệu ->", _vnm, "|", _rnm)
    assert _vnm == "FAIL" and "playback" in _rnm
    # Tăng đơn điệu thật (20->25->31...) vẫn PASS như cũ.
    _go2 = _gate_pb([(float(i * 10), 20 + 5 * (i - 1)) for i in range(1, 11)])
    assert _go2.playback_monotonic()[0] is True
    # Lùi ngay sau tua NGƯỢC thì được miễn (đồng hồ lùi là đúng).
    _gsk = _EG6(specs["MISSION_VOD_PLAYER_SEEK_AND_RESUME"])
    for _t, _pb in [(10.0, 20), (20.0, 0), (30.0, 30)]:
        if _pb == 0:
            _gsk.note_seek()
        _gsk.observe("com.kenhlive.tv/.phim.WebPlayerActivity", [], [], False, True, _t)
        _gsk.observe_playback(_pb, _t)
    assert _gsk.playback_monotonic()[0] is True, \
        "lùi 20->0 ngay sau tua ngược phải được miễn"
    # Nhiễu OCR nhỏ (lùi <= 2s) không tính là không đơn điệu.
    _gno = _EG6(specs["MISSION_VOD_PLAYER_SEEK_AND_RESUME"])
    for _t, _pb in [(10.0, 20), (20.0, 19), (30.0, 25)]:
        _gno.observe("com.kenhlive.tv/.phim.WebPlayerActivity", [], [], False, True, _t)
        _gno.observe_playback(_pb, _t)
    assert _gno.playback_monotonic()[0] is True, "lùi 1s là nhiễu OCR, không tố"
    # Trích xuất đồng hồ: dump '00:20 / 01:05:24' -> 20 (lấy số nhỏ hơn).
    r_pb = runner_mod.RealtimeRunner(out_dir="/tmp/qa_mock_pb", serial=None,
                                     vision_budget=0, no_vision=True)
    assert r_pb._extract_playback_s(
        {"all_visible_texts": [("tvTime", "00:20 / 01:05:24")]}, "step_001.jpg") == 20
    assert r_pb._extract_playback_s(
        {"all_visible_texts": [("tvTime", "Tập 01")]}, "step_001.jpg") is None
    # Fallback OCR band dưới: 2 token -> min; 1 token lẻ -> None (không đoán).
    from detectors import BOTTOM_BAR_BAND as _BBB
    r_pb.detector_ctx["_ocr_cache"] = {
        ("step_001.jpg", _BBB): [{"text": "00:20"}, {"text": "24:14"}]}
    assert r_pb._extract_playback_s({"all_visible_texts": []}, "step_001.jpg") == 20
    r_pb.detector_ctx["_ocr_cache"] = {
        ("step_001.jpg", _BBB): [{"text": "24:14"}]}
    assert r_pb._extract_playback_s({"all_visible_texts": []}, "step_001.jpg") is None
    print("PLAYBACK_PROGRESS_OK")

    # --- Test N12: playback_readings từ ẢNH — OCR ép band dưới (CI-T7 mục 4) ---
    # Gốc rễ CI-T6: dump WebView không có text -> osd_visible=False ->
    # detector band dưới skip -> cache OCR trống -> _extract_playback_s
    # luôn None -> readings [] ở mọi mission player. Sửa: cache trống thì
    # OCR ÉP band dưới trực tiếp từ ảnh, không dựa osd_visible từ dump.
    from PIL import Image as _Image12, ImageDraw as _Draw12, ImageFont as _Font12
    _im12 = _Image12.new("RGB", (960, 540), (10, 10, 15))
    _d12 = _Draw12.Draw(_im12)
    _f12 = _Font12.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 44)
    _d12.text((80, 450), "00:20", fill=(255, 255, 255), font=_f12)
    _d12.text((700, 450), "24:14", fill=(255, 255, 255), font=_f12)
    _buf12 = io.BytesIO()
    _im12.save(_buf12, format="PNG")
    _png12 = _buf12.getvalue()
    r_img = runner_mod.RealtimeRunner(out_dir="/tmp/qa_mock_pb_img", serial=None,
                                      vision_budget=0, no_vision=True)
    r_img.detector_ctx["_ocr_cache"] = {}
    _v12 = r_img._extract_playback_s(
        {"all_visible_texts": [], "osd_visible": False}, "step_001.jpg", _png12)
    print("playback từ ảnh (dump rỗng, osd False) ->", _v12)
    assert _v12 == 20, "OCR ép band dưới phải đọc được 00:20 từ ảnh dù osd False"
    assert ("step_001.jpg", _BBB) in r_img.detector_ctx["_ocr_cache"], \
        "lần OCR ép phải ghi vào cache để detector sau dùng chung, không OCR lại"
    # Ảnh đen không có chữ giờ -> None, không bịa số.
    _im12b = _Image12.new("RGB", (960, 540), (0, 0, 0))
    _buf12b = io.BytesIO()
    _im12b.save(_buf12b, format="PNG")
    r_img.detector_ctx["_ocr_cache"] = {}
    assert r_img._extract_playback_s(
        {"all_visible_texts": []}, "step_002.jpg", _buf12b.getvalue()) is None
    # Parse quote vision 'elapsed / total' (nguồn thứ hai, CI-T2 đã cứu
    # WebPlayer directed bằng quote '00:20 / 24:14').
    from runner import _playback_seconds_from_text as _pb_txt
    assert _pb_txt("phim đang phát 00:20 / 01:05:24") == 20
    assert _pb_txt("00:00 / 24:14") == 0
    assert _pb_txt("không thấy đồng hồ") is None
    assert _pb_txt("chỉ có 24:14 lẻ") is None
    print("PLAYBACK_FROM_IMAGE_OK")


    # --- Test B4: cuộn lên đầu đầu mission list (CI-T5 mục 4) ---
    # CI-T4 DATA_ACCURACY/SCHEDULE/IPTV_CATEGORIES FAIL trung thực vì header
    # ('Hôm nay', 'tv360') đã cuộn mất trước observation đầu tiên.
    r4 = runner_mod.RealtimeRunner(out_dir="/tmp/qa_mock_scroll", serial=None,
                                   vision_budget=0, no_vision=True)
    r4.run([specs["MISSION_SPORTS_DATA_ACCURACY"]])
    print("DATA_ACCURACY keys đầu:", r4.device.keys[:10])
    assert r4.device.keys[0] == "SWITCH_TAB(1)", "reset phải chuyển về tab 1 trước"
    assert r4.device.keys[1:9] == ["UP"] * 8, \
        "sau reset phải có UP x8 để header 'Hôm nay' hiện trước khi gate đọc"
    # Mission không gắn cờ thì không cuộn (không tốn thời gian).
    r4b = runner_mod.RealtimeRunner(out_dir="/tmp/qa_mock_scroll2", serial=None,
                                    vision_budget=0, no_vision=True)
    r4b.run([specs["MISSION_COLD_START"]])
    assert "UP" not in r4b.device.keys, "mission không cần header thì không gửi UP"
    print("SCROLL_TOP_HEADER_OK")

    # --- Test B5: gate chỉ tính motion khi ở đúng activity đích (CI-T5 mục 5) ---
    # CI-T4 IPTV_EPG PASS mềm: motion đo ở MainActivity sau khi player tự
    # thoát, không phải trong player.
    g5 = EvidenceGate(specs["MISSION_IPTV_EPG_AND_ZAPPING_PLAYER"])  # cần PlayerActivity + motion
    g5.observe("com.kenhlive.tv/.MainActivity", [], [], False, True, 1.0)
    print("motion ở MainActivity -> motion_seen:", g5.motion_seen)
    assert g5.motion_seen is False, "motion đo ở activity khác không được set motion_seen"
    g5.observe("com.kenhlive.tv/.PlayerActivity", [], [], False, True, 2.0)
    assert g5.motion_seen is True, "motion ở đúng activity đích phải set motion_seen"
    # Player khác loại cũng không tính: VOD cần WebPlayerActivity, motion ở
    # PlayerActivity (native) không được tính.
    g5b = EvidenceGate(specs["MISSION_VOD_PLAYER_SEEK_AND_RESUME"])
    g5b.observe("com.kenhlive.tv/.PlayerActivity", [], [], False, True, 1.0)
    assert g5b.motion_seen is False, "motion ở PlayerActivity không tính cho mission WebPlayer"
    g5b.observe("com.kenhlive.tv/.phim.WebPlayerActivity", [], [], False, True, 2.0)
    assert g5b.motion_seen is True, "motion ở WebPlayerActivity (dạng đầy đủ .phim.) phải tính"
    print("MOTION_ACTIVITY_BOUND_OK")

    # --- Test B6: hero band OCR thưa hơn — mỗi 2 lần OCR-due mới soi 1 lần (CI-T5 mục 6) ---
    # Đo local trên frame thật CI-T4 (960x540): hero 1.1–2.0s trong tổng
    # 2.5–3.4s cho 3 band (~45–60%); nav + band dưới giữ nguyên mỗi lần due.
    import detectors as det6
    from detectors import NAV_BAND as _NB, HERO_BAND as _HB, BOTTOM_BAR_BAND as _BB

    class CountingOCR:
        def __init__(self):
            self.calls = []
        def available(self):
            return True
        def read_boxes(self, png_bytes, region=None, lang="vie", min_conf=30):
            self.calls.append(tuple(region) if region else None)
            return []

    cocc = CountingOCR()
    ctx6 = {"reported": set(), "steps_since_ocr": 99, "focus_hist": [],
            "force_ocr": False, "_ocr_cache": {}}
    ui6 = {"focused_sig": "nav_home#[0,0][100,100]", "all_visible_texts": [],
           "osd_visible": False}
    det6.run_all_detectors(_fake_png(0), ui6, "com.kenhlive.tv/.MainActivity",
                           ctx6, "h1.jpg", 1.0, cocc)
    ctx6["steps_since_ocr"] = 99  # ép due lần 2
    det6.run_all_detectors(_fake_png(0), ui6, "com.kenhlive.tv/.MainActivity",
                           ctx6, "h2.jpg", 2.0, cocc)
    n_hero = sum(1 for c in cocc.calls if c == tuple(_HB))
    n_nav = sum(1 for c in cocc.calls if c == tuple(_NB))
    n_bot = sum(1 for c in cocc.calls if c == tuple(_BB))
    print("OCR calls sau 2 lần due: hero", n_hero, "| nav", n_nav, "| bottom", n_bot)
    assert n_hero == 1, "hero band chỉ được OCR 1 lần sau 2 lần OCR-due"
    assert n_nav == 2 and n_bot == 2, "nav + band dưới vẫn OCR đủ mỗi lần due"
    print("HERO_OCR_THROTTLE_OK")

    # --- Test B7: vision check hero + title player, tối đa 2 call/run (CI-T5 mục 7) ---
    # OCR không tách được 2 lớp chữ chồng (hero giờ đè phụ đề step_006/016;
    # WebPlayer tiêu đề đè đôi step_071/082) — chỉ vision mới bắt.
    class FakeVision:
        def __init__(self, hero_found=True, title_found=False):
            self.hero_found = hero_found
            self.title_found = title_found
            self.calls = []
        def available(self):
            return True
        def remaining(self):
            return 10
        def check_visual(self, image_bytes, question, timeout=30, crop=None, max_side=None):
            self.calls.append(crop)
            if crop == (0, 140, 1920, 850):
                return {"found": self.hero_found, "severity": "HIGH",
                        "detail": "giờ 16:17 đè lên dòng phụ đề hero"}, None
            return {"found": self.title_found, "severity": "HIGH",
                    "detail": "tên phim đè lên Tập 01"}, None

    def _vision_runner(hero_found, title_found):
        rr = runner_mod.RealtimeRunner(out_dir="/tmp/qa_mock_vision", serial=None,
                                       vision_budget=40, no_vision=False)
        rr.start_time = time.time()
        rr._hero_frame = {"png": _fake_png(0), "frame": "step_006_sports_m.jpg", "t": 12.0}
        rr._player_title_frame = {"png": _fake_png(1), "frame": "step_071_vod_play.jpg",
                                  "t": 300.0, "activity": "com.kenhlive.tv/.phim.WebPlayerActivity"}
        fv = FakeVision(hero_found, title_found)
        rr.vision = fv
        rr._vision_overlap_checks()
        return rr, fv

    r7, fv7 = _vision_runner(True, False)
    print("vision hero/title calls:", len(fv7.calls), fv7.calls)
    print("findings:", [(f["issue"], f["evidence"]["frame"]) for f in r7.findings])
    assert len(fv7.calls) == 2, "hero + title mỗi vùng đúng 1 vision call/run"
    assert fv7.calls[0] == (0, 140, 1920, 850), "hero crop đúng vùng hero"
    assert fv7.calls[1] == (0, 0, 1920, 280), "title crop đúng vùng tiêu đề player"
    assert len(r7.findings) == 1 and r7.findings[0]["issue"] == "Giờ đè lên phụ đề hero", \
        "vision báo hero overlap thì phải tạo finding HIGH"
    assert r7.findings[0]["severity"] == "HIGH"
    assert r7.findings[0]["evidence"]["frame"] == "step_006_sports_m.jpg"
    r7b, fv7b = _vision_runner(False, True)
    assert len(r7b.findings) == 1 and r7b.findings[0]["issue"] == "Tiêu đề player đè đôi", \
        "vision báo title overlap thì phải tạo finding title"
    assert len(fv7b.calls) == 2
    # Không có frame ứng cử thì không gọi vision lần nào.
    r7c = runner_mod.RealtimeRunner(out_dir="/tmp/qa_mock_vision2", serial=None,
                                    vision_budget=40, no_vision=False)
    fv7c = FakeVision(True, True)
    r7c.vision = fv7c
    r7c._vision_overlap_checks()
    assert fv7c.calls == [] and r7c.findings == [], "không có frame thì 0 vision call"
    print("VISION_HERO_TITLE_OK")

    # --- Test N2: vision check title phải tố được đè đôi step_063 (CI-T6 mục 2) ---
    # CI-T5: 2 call check_visual không sinh finding nào dù tiêu đề WebPlayer
    # đè đôi hiện rõ ở step_063/066/067. Debug live (nemotron):
    #   - prompt CŨ trên frame step_063 -> found=True HIGH (13.7s)
    #   - prompt MỚI (hỏi rõ "2 DÒNG TIÊU ĐỀ CHỒNG LÊN NHAU" + ép đọc nguyên
    #     văn vào quote) -> found=True HIGH (19.3s), quote đủ cả 2 dòng.
    # Vậy prompt/crop (0,0,1920,280) không sai; nghi vấn còn lại là frame
    # được soi là frame WebPlayer ĐẦU TIÊN (lúc loading, chưa hiện lỗi).
    # Sửa: (a) giữ frame title CUỐI thay vì đầu, (b) prompt hỏi rõ đè đôi,
    # (c) log rõ mỗi call đã soi frame nào (frame path + timestamp + crop).
    class FakeVision2:
        def __init__(self):
            self.calls = []  # (crop, question, image_bytes)
        def available(self):
            return True
        def remaining(self):
            return 10
        def check_visual(self, image_bytes, question, timeout=30, crop=None, max_side=None):
            self.calls.append((crop, question, image_bytes))
            return {"found": True, "severity": "HIGH",
                    "detail": "Tiêu đề đè đôi", "quote": "Dòng 1 | Dòng 2"}, None

    png63 = open(os.path.join(
        os.path.expanduser("~/workspace/kenhlive-plan/qa-run-43010818257/qa-report-realtime/shots"),
        "step_063_vod_play.jpg"), "rb").read()
    r_n2 = runner_mod.RealtimeRunner(out_dir="/tmp/qa_mock_vision_n2", serial=None,
                                     vision_budget=40, no_vision=False)
    r_n2.start_time = time.time()
    r_n2._hero_frame = {"png": _fake_png(0), "frame": "step_006_sports_m.jpg", "t": 12.0}
    r_n2._player_title_frame = {"png": png63, "frame": "step_063_vod_play.jpg",
                                "t": 300.0, "activity": "com.kenhlive.tv/.phim.WebPlayerActivity"}
    fv2 = FakeVision2()
    r_n2.vision = fv2
    r_n2._vision_overlap_checks()
    _title_q = [q for c, q, _ in fv2.calls if c == (0, 0, 1920, 280)][0]
    print("title question:", _title_q[:120])
    assert "2 DÒNG TIÊU ĐỀ" in _title_q and "CHỒNG LÊN NHAU" in _title_q, \
        "prompt title phải hỏi rõ 'có 2 dòng tiêu đề chồng nhau không'"
    assert fv2.calls[1][2] == png63, "check title phải soi đúng frame step_063 (bytes thật)"
    _title_find = [f for f in r_n2.findings if f["issue"] == "Tiêu đề player đè đôi"]
    assert len(_title_find) == 1 and _title_find[0]["evidence"]["frame"] == "step_063_vod_play.jpg", \
        "vision báo đè đôi trên step_063 thì phải tạo finding HIGH kèm frame đó"
    print("vision_check_log:", r_n2.vision_check_log)
    assert len(r_n2.vision_check_log) == 2, "mỗi call check_visual phải được log"
    _log_title = [e for e in r_n2.vision_check_log if e["kind"] == "player_title"][0]
    assert _log_title["frame"] == "step_063_vod_play.jpg" and _log_title["t"] == 300.0, \
        "log phải ghi rõ frame path + timestamp đã soi"
    assert _log_title["crop"] == [0, 0, 1920, 280] and _log_title["result"] == "found"
    # Frame CUỐI thắng frame đầu (loading): note 2 lần, lần sau thắng.
    r_n2b = runner_mod.RealtimeRunner(out_dir="/tmp/qa_mock_vision_n2b", serial=None,
                                      vision_budget=40, no_vision=True)
    _spec_vod = specs["MISSION_VOD_PLAYER_SEEK_AND_RESUME"]
    r_n2b._note_vision_frames(_spec_vod,
                              {"png": _fake_png(0), "t_offset": 100.0},
                              "step_061_vod_play.jpg")
    r_n2b._note_vision_frames(_spec_vod,
                              {"png": _fake_png(1), "t_offset": 200.0},
                              "step_063_vod_play.jpg")
    # obs thiếu 'activity' -> _note_vision_frames không set title (cần activity)
    assert r_n2b._player_title_frame is None
    r_n2b._note_vision_frames(_spec_vod,
                              {"png": _fake_png(0), "t_offset": 100.0,
                               "activity": "com.kenhlive.tv/.phim.WebPlayerActivity"},
                              "step_061_vod_play.jpg")
    r_n2b._note_vision_frames(_spec_vod,
                              {"png": _fake_png(1), "t_offset": 200.0,
                               "activity": "com.kenhlive.tv/.phim.WebPlayerActivity"},
                              "step_063_vod_play.jpg")
    print("title frame cuối:", r_n2b._player_title_frame["frame"])
    assert r_n2b._player_title_frame["frame"] == "step_063_vod_play.jpg", \
        "phải giữ frame title CUỐI (step_063, lỗi đã hiện), không phải frame đầu lúc loading"
    print("VISION_TITLE_DOUBLE_OK")

    # --- Test B8: video giữ chunk cuối đang quay dở (CI-T5 mục 8) ---
    # CI-T4: chunk_08 (~160s cuối) 'moov atom not found' ở bước chuẩn hóa
    # -> video chỉ 1225/1534s. Giả lập adb: chunk cuối chỉ xuất hiện trong
    # ls + pidof hết sau 1.5s (đang finalize); lần pull đầu của nó bị cắt
    # ngắn -> phải pull lại. Dùng ffmpeg thật để tạo chunk + ghép.
    import shutil as _shutil
    import subprocess as _sp
    if not _shutil.which("ffmpeg"):
        print("VIDEO_LAST_CHUNK_SKIP (không có ffmpeg local)")
    else:
        import video_recorder as _vr
        from video_recorder import VideoRecorder as _VR
        td = "/tmp/qa_mock_video"
        devdir = os.path.join(td, "device")
        _shutil.rmtree(td, ignore_errors=True)
        os.makedirs(devdir)
        for _name, _dur in (("qa_rec_01.mp4", 5), ("qa_rec_02.mp4", 4)):
            _sp.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i",
                     "testsrc=duration=%d:size=320x180:rate=10" % _dur,
                     "-c:v", "libx264", "-pix_fmt", "yuv420p",
                     os.path.join(devdir, _name)], check=True, timeout=60)
        _real_run = _sp.run  # subprocess thật cho ffmpeg/ffprobe

        class _FakeCompleted:
            def __init__(self, stdout="", returncode=0):
                self.stdout, self.stderr, self.returncode = stdout, "", returncode

        def _make_fake_adb(finalize_delay, pull_truncate=True, devdir=devdir):
            t0 = time.time()
            fin_at = t0 + finalize_delay
            pull_count = {}

            def fake_run(cmd, *a, **k):
                if isinstance(cmd, str) and "adb" in cmd:
                    if "pidof screenrecord" in cmd:
                        return _FakeCompleted("1234\n" if time.time() < fin_at else "")
                    if "ls /sdcard/qa_rec_" in cmd:
                        files = ["/sdcard/qa_rec_01.mp4"]
                        if time.time() >= fin_at:
                            files.append("/sdcard/qa_rec_02.mp4")
                        return _FakeCompleted("\n".join(files) + "\n")
                    if "stat -c %s" in cmd:
                        remote = cmd.rsplit(None, 1)[-1]
                        p = os.path.join(devdir, os.path.basename(remote))
                        if time.time() < fin_at or not os.path.exists(p):
                            return _FakeCompleted("")
                        return _FakeCompleted("%d\n" % os.path.getsize(p))
                    if " pull " in cmd:
                        parts = cmd.split()
                        remote, local = parts[parts.index("pull") + 1: parts.index("pull") + 3]
                        src = os.path.join(devdir, os.path.basename(remote))
                        pull_count[remote] = pull_count.get(remote, 0) + 1
                        if pull_truncate and remote.endswith("qa_rec_02.mp4") \
                                and pull_count[remote] == 1:
                            with open(src, "rb") as f, open(local, "wb") as g:
                                g.write(f.read(1000))  # pull đầu bị cắt ngắn
                        else:
                            _shutil.copy(src, local)
                        return _FakeCompleted("")
                    return _FakeCompleted("")
                return _real_run(cmd, *a, **k)

            return fake_run, pull_count

        # A: chunk cuối finalize sau 1.5s + pull đầu cắt ngắn -> vẫn đủ ~9s, 2 chunk.
        _fake_a, _pull_a = _make_fake_adb(1.5)
        _vr.subprocess.run = _fake_a
        try:
            rec_a = _VR(out_dir=os.path.join(td, "out_a"))
            rec_a.is_recording = True
            rec_a.remote_chunks = ["/sdcard/qa_rec_01.mp4", "/sdcard/qa_rec_02.mp4"]
            rec_a._current_remote = "/sdcard/qa_rec_02.mp4"
            res_a = rec_a.stop_and_save()
        finally:
            _vr.subprocess.run = _real_run
        print("video last-chunk A: recorded", res_a and res_a.get("recorded_seconds"),
              "| chunks:", res_a and res_a.get("chunks"),
              "| pull chunk_02:", _pull_a.get("/sdcard/qa_rec_02.mp4"))
        assert res_a is not None and 8.0 <= res_a["recorded_seconds"] <= 10.5, \
            "chunk cuối đang quay dở phải được kéo về và ghép (kỳ vọng ~9s, được %s)" \
            % (res_a and res_a.get("recorded_seconds"))
        assert res_a["chunks"] == 2, "phải có 2 chunk chuẩn hóa"
        assert _pull_a.get("/sdcard/qa_rec_02.mp4", 0) >= 2, "pull thiếu phải pull lại"
        # B: chunk cuối KHÔNG bao giờ finalize -> vẫn xong, giữ chunk đầu, không treo.
        # Mô phỏng đúng CI-T4: file chunk cuối trên máy là H.264 thô không có
        # moov atom (screenrecord chết không finalize) -> pull về vẫn bị loại
        # ở bước chuẩn hóa, nhưng run không treo và chunk đầu còn nguyên.
        devdir_b = os.path.join(td, "device_b")
        os.makedirs(devdir_b)
        _shutil.copy(os.path.join(devdir, "qa_rec_01.mp4"),
                     os.path.join(devdir_b, "qa_rec_01.mp4"))
        _sp.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i",
                 "testsrc=duration=4:size=320x180:rate=10",
                 "-c:v", "libx264", "-f", "h264",
                 os.path.join(devdir_b, "qa_rec_02.mp4")], check=True, timeout=60)
        # Cắt file còn 30% (mô phỏng pull đúng lúc screenrecord đang ghi dở:
        # không moov + mdat đứt giữa chừng -> ffmpeg không decode được, như
        # chunk_08 CI-T4). File H.264 nguyên vẹn thì ffmpeg vẫn decode được
        # (test vòng trước) nên không dùng để mô phỏng chunk hỏng.
        _p_b = os.path.join(devdir_b, "qa_rec_02.mp4")
        with open(_p_b, "r+b") as _f:
            _f.truncate(os.path.getsize(_p_b) * 3 // 10)
        _fake_b, _pull_b = _make_fake_adb(3600.0, pull_truncate=False, devdir=devdir_b)
        _vr.subprocess.run = _fake_b
        t_b0 = time.time()
        try:
            rec_b = _VR(out_dir=os.path.join(td, "out_b"))
            rec_b.is_recording = True
            rec_b.remote_chunks = ["/sdcard/qa_rec_01.mp4", "/sdcard/qa_rec_02.mp4"]
            rec_b._current_remote = "/sdcard/qa_rec_02.mp4"
            rec_b._finalize_timeout_s = 4.0
            res_b = rec_b.stop_and_save()
        finally:
            _vr.subprocess.run = _real_run
        dt_b = time.time() - t_b0
        print("video last-chunk B: recorded", res_b and res_b.get("recorded_seconds"),
              "| chunks:", res_b and res_b.get("chunks"), "| elapsed %.1fs" % dt_b)
        assert res_b is not None and 4.0 <= res_b["recorded_seconds"] <= 6.5, \
            "chunk cuối không finalize được thì vẫn giữ chunk đầu (~5s)"
        # Chunk hỏng có thể chuẩn hóa thành clip vụn ~0.2s (vẫn tính là 1
        # chunk chuẩn hóa) — điều quan trọng là video cuối vẫn ~5s, không
        # phải ~9s, và run không treo ở bước chờ finalize.
        assert dt_b < 20, "timeout finalize không được treo run"
        print("VIDEO_LAST_CHUNK_OK")

    # --- Test N3: chờ moov khi finalize chunk cuối (CI-T6 mục 3) ---
    # CI-T5: chunk cuối mất ở normalize vì 'moov atom not found' (video
    # 83%) dù mục 8 đã chờ size ổn định 2 lần đọc — size ổn định KHÔNG
    # chứng minh moov đã ghi. _wait_chunk_finalized_moov phải pull thử +
    # ffprobe: lần 1 chưa thấy moov -> pull lại; lần 2 thấy moov -> True.
    # Chưa bao giờ thấy moov -> False (caller vẫn pull thử như cũ).
    import subprocess as _sp3
    import video_recorder as _vr3
    from video_recorder import VideoRecorder as _VR3

    class _FakeCompleted3:
        def __init__(self, stdout="", returncode=0):
            self.stdout, self.stderr, self.returncode = stdout, "", returncode

    def _fake_run_pull_only(cmd, *a, **k):
        if isinstance(cmd, str) and " pull " in cmd:
            return _FakeCompleted3("")
        return _sp3.run(cmd, *a, **k)

    td3 = "/tmp/qa_mock_moov"
    _shutil.rmtree(td3, ignore_errors=True)
    os.makedirs(td3, exist_ok=True)
    _probe_calls = {"n": 0}

    def _fake_probe(path):
        _probe_calls["n"] += 1
        if _probe_calls["n"] == 1:
            return (0.0, False, 0)  # lần 1: chưa có moov
        return (4.0, True, 120)      # lần 2: có moov

    _rec3 = _VR3(out_dir=os.path.join(td3, "out"))
    _rec3._screenrecord_running = lambda: False
    _rec3._device_file_size = lambda remote: 5000000
    _rec3._probe_video = _fake_probe
    _orig_run3 = _vr3.subprocess.run
    _vr3.subprocess.run = _fake_run_pull_only
    try:
        ok_moov = _rec3._wait_chunk_finalized_moov("/sdcard/qa_rec_02.mp4", timeout=10.0)
    finally:
        _vr3.subprocess.run = _orig_run3
    print("moov wait: ok", ok_moov, "| probe calls:", _probe_calls["n"])
    assert ok_moov is True and _probe_calls["n"] == 2, \
        "lần 1 chưa moov phải pull lại, lần 2 có moov thì xong"
    # Không bao giờ có moov -> False sau tối đa 5 lần thử (~10s), không treo.
    _probe_calls["n"] = 0
    _rec3b = _VR3(out_dir=os.path.join(td3, "out_b"))
    _rec3b._screenrecord_running = lambda: False
    _rec3b._device_file_size = lambda remote: 5000000
    _rec3b._probe_video = lambda path: (0.0, False, 0)
    _vr3.subprocess.run = _fake_run_pull_only
    _t3 = time.time()
    try:
        ok_moov_b = _rec3b._wait_chunk_finalized_moov("/sdcard/qa_rec_02.mp4", timeout=10.0)
    finally:
        _vr3.subprocess.run = _orig_run3
    print("moov wait (không moov): ok", ok_moov_b, "| elapsed %.1fs" % (time.time() - _t3))
    assert ok_moov_b is False and time.time() - _t3 < 20, \
        "không có moov thì trả False, không treo run"
    print("VIDEO_MOOV_WAIT_OK")

    # --- Test N13: video chunk cuối — dừng mềm + xác minh pidof (CI-T7 mục 5) ---
    # CI-T6: video chỉ 79% — moov-wait 60s chạy mà vẫn thất bại vì
    # _wait_for_screenrecord_exit() trả về bị bỏ qua (screenrecord chưa chết
    # hẳn thì moov không được ghi). Sửa: (a) request_graceful_stop() để chunk
    # cuối hết hạn 175s tự nhiên (không SIGINT); (b) xác minh pidof trước
    # khi chờ moov, log + ghi vào dict trả về (screenrecord_exited).
    import threading as _th13
    import subprocess as _sp13
    import video_recorder as _vr13
    from video_recorder import VideoRecorder as _VR13
    # LƯU HÀM THẬT TRƯỚC KHI PATCH: _vr13.subprocess CHÍNH LÀ module
    # subprocess toàn cục — gán _vr13.subprocess.run = fake sẽ đổi cả
    # _sp13.run, nên fake phải gọi bản đã lưu, không gọi _sp13.run.
    _real_run13 = _sp13.run

    class _FakeCompleted13:
        def __init__(self, stdout="", returncode=0):
            self.stdout, self.stderr, self.returncode = stdout, "", returncode

    def _make_fake_adb13(devdir, pidof_pid=None):
        pull_count = {}

        def fake_run(cmd, *a, **k):
            if isinstance(cmd, str) and "adb" in cmd:
                if "pidof screenrecord" in cmd:
                    return _FakeCompleted13((pidof_pid + "\n") if pidof_pid else "")
                if "ls /sdcard/qa_rec_" in cmd:
                    return _FakeCompleted13(
                        "".join("/sdcard/%s\n" % f for f in sorted(os.listdir(devdir))
                                if f.endswith(".mp4")))
                if "stat -c %s" in cmd:
                    remote = cmd.rsplit(None, 1)[-1]
                    p = os.path.join(devdir, os.path.basename(remote))
                    return _FakeCompleted13("%d\n" % os.path.getsize(p)
                                            if os.path.exists(p) else "")
                if " pull " in cmd:
                    parts = cmd.split()
                    remote, local = parts[parts.index("pull") + 1: parts.index("pull") + 3]
                    src = os.path.join(devdir, os.path.basename(remote))
                    pull_count[remote] = pull_count.get(remote, 0) + 1
                    _shutil.copy(src, local)
                    return _FakeCompleted13("")
                return _FakeCompleted13("")
            return _real_run13(cmd, *a, **k)

        return fake_run, pull_count

    # (a) worker dừng mềm: chunk tự thoát (poll -> 0) thì KHÔNG SIGINT.
    _adb_cmds13 = []

    def _fake_run13a(cmd, *a, **k):
        if isinstance(cmd, str) and "adb" in cmd:
            _adb_cmds13.append(cmd)
            if "pidof screenrecord" in cmd:
                return _FakeCompleted13("")
            return _FakeCompleted13("")
        return _real_run13(cmd, *a, **k)

    class _FakeProc13:
        def __init__(self):
            self._polls = 0

        def poll(self):
            self._polls += 1
            return None if self._polls <= 10 else 0  # tự thoát sau ~5s

        def wait(self, timeout=None):
            return 0

    _orig_run13 = _vr13.subprocess.run
    _orig_popen13 = _vr13.subprocess.Popen
    _vr13.subprocess.run = _fake_run13a
    _vr13.subprocess.Popen = lambda cmd, *a, **k: _FakeProc13()
    try:
        rec13 = _VR13(out_dir="/tmp/qa_mock_video_grace/out")
        rec13.start()
        time.sleep(0.5)
        rec13.request_graceful_stop()
        assert rec13._graceful_stop is True and rec13.stop_event.is_set()
        rec13.worker_thread.join(timeout=8)
        assert not rec13.worker_thread.is_alive(), \
            "worker dừng mềm phải thoát khi chunk hết hạn tự nhiên"
        assert not any("pkill" in c or "kill -2" in c for c in _adb_cmds13), \
            "dừng mềm không được SIGINT chunk (phải để hết hạn tự nhiên)"
        assert rec13._screenrecord_exited is True, \
            "chunk hết hạn tự nhiên thì screenrecord đã chết (pidof)"
    finally:
        _vr13.subprocess.run = _orig_run13
        _vr13.subprocess.Popen = _orig_popen13
    print("VIDEO_GRACEFUL_STOP_OK")
    # (b)+(c) cần ffmpeg để tạo chunk thật (như B8).
    if not _shutil.which("ffmpeg"):
        print("VIDEO_GRACEFUL_SAVE_SKIP (không có ffmpeg local)")
    else:
        td13 = "/tmp/qa_mock_video_grace"
        devdir13 = os.path.join(td13, "device")
        os.makedirs(devdir13, exist_ok=True)
        _sp13.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i",
                 "testsrc=duration=5:size=320x180:rate=10",
                 "-c:v", "libx264", "-pix_fmt", "yuv420p",
                 os.path.join(devdir13, "qa_rec_01.mp4")], check=True, timeout=60)
        # (b) stop_and_save dừng mềm: join worker xong, pidof hết, chunk về đủ.
        _fake13b, _pull13b = _make_fake_adb13(devdir13, pidof_pid=None)
        _vr13.subprocess.run = _fake13b
        try:
            rec13b = _VR13(out_dir=os.path.join(td13, "out_b"))
            rec13b.is_recording = True
            rec13b.remote_chunks = ["/sdcard/qa_rec_01.mp4"]
            rec13b._current_remote = "/sdcard/qa_rec_01.mp4"
            rec13b._current_started_at = time.time() - 170.0  # chunk sắp hết hạn
            rec13b.worker_thread = _th13.Thread(target=lambda: time.sleep(0.5))
            rec13b.worker_thread.start()
            rec13b.request_graceful_stop()
            res13b = rec13b.stop_and_save()
        finally:
            _vr13.subprocess.run = _orig_run13
        print("video graceful save: recorded", res13b and res13b.get("recorded_seconds"),
              "| screenrecord_exited:", res13b and res13b.get("screenrecord_exited"),
              "| graceful:", res13b and res13b.get("graceful_stop"))
        assert res13b is not None and 4.0 <= res13b["recorded_seconds"] <= 6.5
        assert res13b["screenrecord_exited"] is True, "pidof hết thì phải ghi True"
        assert res13b["graceful_stop"] is True
        # (c) pidof vẫn thấy screenrecord chạy -> ghi False, không chờ thêm
        # quá lâu (mock B8: không có worker thread thì chỉ log, moov-wait xử lý).
        _fake13c, _pull13c = _make_fake_adb13(devdir13, pidof_pid="1234")
        _vr13.subprocess.run = _fake13c
        _t13c = time.time()
        try:
            rec13c = _VR13(out_dir=os.path.join(td13, "out_c"))
            rec13c.is_recording = True
            rec13c.remote_chunks = ["/sdcard/qa_rec_01.mp4"]
            rec13c._current_remote = "/sdcard/qa_rec_01.mp4"
            rec13c._finalize_timeout_s = 4.0
            res13c = rec13c.stop_and_save()
        finally:
            _vr13.subprocess.run = _orig_run13
        _dt13c = time.time() - _t13c
        print("video pidof còn chạy: recorded", res13c and res13c.get("recorded_seconds"),
              "| screenrecord_exited:", res13c and res13c.get("screenrecord_exited"),
              "| elapsed %.1fs" % _dt13c)
        assert res13c is not None and res13c["screenrecord_exited"] is False, \
            "pidof còn thấy process thì phải ghi False (chunk cuối có nguy cơ mất moov)"
        assert _dt13c < 20, "xác minh pidof không được treo run"
        print("VIDEO_GRACEFUL_SAVE_OK")

    # --- Test B9: driver đi tới view đích theo id + phân biệt dialog/player (CI-T5 mục 9) ---
    # CI-T4 EPISODE_PICKER đi lạc về Home trong khi nút CHỌN TẬP hiện ngay
    # trên màn hình; ROOM_PICKER OK mở PLAYER thay vì dialog (step_018).
    from gate import MissionSpec as _MS
    spec_goto = _MS("MISSION_TEST_GOTO", "Test goto", "test", max_steps=6,
                    required_activity="MainActivity", required_views=["roomList"])
    dev_g = FakeDevice()
    drv_g = Driver(dev_g, EvidenceGate(spec_goto), spec_goto)
    base_g = {
        "focused_sig": "heroPlay#[100,100][300,200]",
        "focused_text": "",
        "focused_bounds": "[100,100][300,200]",
        "all_visible_texts": [("heroPlay", ""), ("roomList", "Phòng")],
        "has_dialog": False, "dialog_ids": [],
    }
    def _ui_g(room_bounds):
        return dict(base_g, all_visible_nodes=[
            {"id": "heroPlay", "text": "", "bounds": "[100,100][300,200]"},
            {"id": "roomList", "text": "Phòng BLV", "bounds": room_bounds}])
    a_down = drv_g.next_action(_ui_g("[100,500][400,900]"), "com.kenhlive.tv/.MainActivity", None, 0.0)
    a_up = drv_g.next_action(_ui_g("[100,0][400,80]"), "com.kenhlive.tv/.MainActivity", None, 0.0)
    a_right = drv_g.next_action(_ui_g("[800,100][1100,200]"), "com.kenhlive.tv/.MainActivity", None, 0.0)
    a_missing = drv_g.next_action(dict(base_g, all_visible_nodes=[
        {"id": "heroPlay", "text": "", "bounds": "[100,100][300,200]"}]),
        "com.kenhlive.tv/.MainActivity", None, 0.0)
    print("goto roomList dưới/trên/phải/vắng:",
          [(a.type, a.param, a.rule) for a in (a_down, a_up, a_right, a_missing)])
    assert (a_down.type, a_down.param, a_down.rule) == ("KEY", "DPAD_DOWN", "goto_view")
    assert (a_up.type, a_up.param, a_up.rule) == ("KEY", "DPAD_UP", "goto_view")
    assert (a_right.type, a_right.param, a_right.rule) == ("KEY", "DPAD_RIGHT", "goto_view")
    assert (a_missing.type, a_missing.param, a_missing.rule) == ("KEY", "DPAD_DOWN", "seek_view"), \
        "view đích chưa thấy thì explore DOWN như trước"
    # Đi tới nút CHỌN TẬP theo text rồi mới bấm OK mở dialog.
    dev_ep = FakeDevice()
    dev_ep._tab = 5  # EPISODE_PICKER cần tab Kho Phim (5)
    drv_ep = Driver(dev_ep, EvidenceGate(specs["MISSION_PHIM_EPISODE_PICKER_AND_FAVORITE"]),
                    specs["MISSION_PHIM_EPISODE_PICKER_AND_FAVORITE"])
    ui_ep = {"focused_sig": "btnHeroBackHome#[45,45][155,155]",
             "focused_text": "Về trang chủ",
             "focused_bounds": "[45,45][155,155]",
             "all_visible_texts": [("btnHeroBackHome", "Về trang chủ"),
                                   ("btnEpisode", "CHỌN TẬP")],
             "all_visible_nodes": [
                 {"id": "btnHeroBackHome", "text": "Về trang chủ", "bounds": "[45,45][155,155]"},
                 {"id": "btnEpisode", "text": "CHỌN TẬP", "bounds": "[100,500][400,600]"}],
             "has_dialog": False, "dialog_ids": []}
    a_ep = drv_ep.next_action(ui_ep, "com.kenhlive.tv/.MainActivity", None, 0.0)
    print("EPISODE_PICKER focus lạc ->", a_ep.type, a_ep.param, "| rule:", a_ep.rule)
    assert a_ep.rule == "goto_view_text" and a_ep.param == "DPAD_DOWN", \
        "focus đang lạc thì phải đi tới nút CHỌN TẬP, không bấm OK mù"
    ui_ep_on = dict(ui_ep,
                    focused_sig="btnEpisode#[100,500][400,600]",
                    focused_text="CHỌN TẬP",
                    focused_bounds="[100,500][400,600]")
    a_ep2 = drv_ep.next_action(ui_ep_on, "com.kenhlive.tv/.MainActivity", None, 0.0)
    assert (a_ep2.type, a_ep2.param, a_ep2.rule) == ("KEY", "OK", "open_dialog"), \
        "đã đứng trên nút CHỌN TẬP thì bấm OK mở dialog"
    # OK mở PLAYER thay vì dialog -> FAIL với lý do đúng (không PASS oan).
    class PlayerOpeningDevice(FakeDevice):
        def send_key(self, key_name):
            super().send_key(key_name)
            if key_name == "OK":
                self._activity = "com.kenhlive.tv/.PlayerActivity"
    runner_mod.RealtimeDevice = PlayerOpeningDevice
    try:
        r9 = runner_mod.RealtimeRunner(out_dir="/tmp/qa_mock_room", serial=None,
                                       vision_budget=0, no_vision=True)
        r9.run([specs["MISSION_SPORTS_ROOM_PICKER"]])
    finally:
        runner_mod.RealtimeDevice = FakeDevice
    res9 = r9.mission_results[0]
    print("ROOM_PICKER OK mở player:", res9["outcome"], "|", res9["reason"])
    assert res9["outcome"] == "FAIL" and "PLAYER thay vì dialog" in res9["reason"], \
        "OK mở player thay vì dialog phải FAIL với lý do đúng, không PASS oan"
    # --- Test N7: timeline không được thiếu step_id (CI-T6 mục 9) ---
    # CI-T5: qa_session.json 79 entry, step_id 1-80 thiếu đúng số 14 — bước
    # mở PlayerActivity thay vì dialog bị break TRƯỚC khi timeline.append
    # (trong khi _global_step đã tăng). Giờ append đứng trước check FAIL.
    _ids9 = [e["step_id"] for e in r9.timeline]
    print("ROOM_PICKER timeline step_ids:", _ids9, "| _global_step:", r9._global_step)
    assert _ids9 == list(range(1, len(_ids9) + 1)), \
        "timeline phải liên tục 1..N — không được mất step như CI-T5 (thiếu 14)"
    assert _ids9[-1] == r9._global_step, \
        "bước FAIL cuối phải có mặt trong timeline (step_id == step cuối)"
    assert "PlayerActivity" in r9.timeline[-1]["activity"], \
        "bước cuối (FAIL) phải ghi đúng PlayerActivity đã mở thay vì dialog"
    print("TIMELINE_STEP_IDS_OK")

    # --- Test N8: nhãn provider thật, không ghi 'NIM' khi provider là OPENAI (CI-T6 mục 10) ---
    # CI-T5 report: nim_usage.provider='OPENAI' đúng, nhưng dòng in + HTML ghi
    # 'NIM requests' — sai nhãn. VisionClient có _detect_endpoint_host():
    # provider OPENAI qua URL NIM-compatible -> host integrate.api.nvidia.com
    # (limiter đếm request gửi tới host đó); nim_stats() phải có endpoint_host;
    # report có vision_provider ở cấp cao nhất; HTML ghi 'Vision: OPENAI qua ...'.
    import vision as _vis10
    _saved10 = (_vis10.DEEPSEEK_BASE, _vis10.ANTIGRAVITY_BASE, _vis10.ANTIGRAVITY_KEY,
                _vis10.KILO_BASE, _vis10.KILO_KEY, _vis10.OPENAI_BASE, _vis10.OPENAI_KEY)
    _vis10.DEEPSEEK_BASE = ""
    _vis10.ANTIGRAVITY_BASE = ""; _vis10.ANTIGRAVITY_KEY = ""
    _vis10.KILO_BASE = ""; _vis10.KILO_KEY = ""
    _vis10.OPENAI_BASE = "https://integrate.api.nvidia.com/v1/chat/completions"
    _vis10.OPENAI_KEY = "fake-key-chi-de-test-nhan"
    try:
        _vc10 = _vis10.VisionClient()
        print("provider:", _vc10.provider, "| endpoint_host:", _vc10.endpoint_host,
              "| nim_stats provider/host:", _vc10.nim_stats().get("provider"),
              _vc10.nim_stats().get("endpoint_host"))
        assert _vc10.provider == "OPENAI"
        assert _vc10.endpoint_host == "integrate.api.nvidia.com", \
            "provider OPENAI qua URL NIM-compatible -> host là integrate.api.nvidia.com"
        assert _vc10.nim_stats()["endpoint_host"] == "integrate.api.nvidia.com"
        assert _vc10.nim_stats()["provider"] == "OPENAI"
    finally:
        (_vis10.DEEPSEEK_BASE, _vis10.ANTIGRAVITY_BASE, _vis10.ANTIGRAVITY_KEY,
         _vis10.KILO_BASE, _vis10.KILO_KEY, _vis10.OPENAI_BASE, _vis10.OPENAI_KEY) = _saved10
    _html10 = "/tmp/qa_mock_provider_label.html"
    from judge import HonestJudge as _HJ10
    _rep10 = {"score": 0, "engine": "KenhLive Realtime Vision QA",
              "missions_passed": "0/17", "vision_calls": {"total": 8},
              "duration_sec": 843, "timings": {}, "verdict": "NEEDS_FIX",
              "vision_provider": "OPENAI",
              "vision_endpoint_host": "integrate.api.nvidia.com",
              "nim_usage": {"requests_used": 8, "limit_per_min": 30, "hit_429": False,
                            "provider": "OPENAI",
                            "endpoint_host": "integrate.api.nvidia.com"},
              "defect_reel_coverage": {"text": "3/3 finding"},
              "checks": [], "findings": [], "unverified": []}
    _HJ10("/tmp").render_html(_rep10, _html10)
    _html_txt = open(_html10, encoding="utf-8").read()
    assert "Vision: OPENAI qua integrate.api.nvidia.com" in _html_txt, \
        "HTML phải ghi provider thật + endpoint, không ghi 'NIM requests'"
    assert "NIM requests:" not in _html_txt
    print("VISION_PROVIDER_LABEL_OK")
    print("GOTO_VIEW_BY_ID_OK")

    # --- Test N9: nhận diện MatchDetailPanel là dialog (CI-T7 mục 1) ---
    # CI-T6 ROOM_PICKER FAIL: bấm thẻ trận mở match-detail PANEL
    # (LiveFragment.openGroupPicker -> dialog_match_detail.xml) nhưng
    # has_dialog=False suốt lúc panel mở vì không id panel nào có trong
    # dialog_id_set -> driver tưởng dialog chưa mở, bấm OK tiếp -> player.
    # Sửa: 13 id panel* trong set + mọi id bắt đầu "panel" / "blvCardRoot"
    # đều tính là dialog. Kiểm chứng bằng XML dump THẬT (parse như live).
    import device as _devmod9

    def _fake_xml9(nodes):
        parts = ['<hierarchy rotation="0">']
        for _id, _txt, _foc in nodes:
            parts.append(
                '<node index="0" text="%s" resource-id="com.kenhlive.tv:id/%s" '
                'class="android.widget.Button" package="com.kenhlive.tv" '
                'content-desc="" checkable="false" checked="false" clickable="true" '
                'enabled="true" focusable="true" focused="%s" scrollable="false" '
                'long-clickable="false" password="false" selected="false" '
                'bounds="[100,200][500,600]" />' % (_txt, _id, "true" if _foc else "false"))
        parts.append('</hierarchy>')
        return "".join(parts)

    _orig_sh9 = _devmod9.sh
    try:
        # (a) panel mở: panelBlvList + blvCardRoot đang focus -> dialog.
        _devmod9.sh = lambda cmd, timeout=30: _fake_xml9([
            ("panelScore", "5 : 3", False),
            ("panelBlvList", "", False),
            ("blvCardRoot", "Phòng 1", True),
            ("panelPlay", "Xem ngay", False)])
        _st9a = _devmod9.RealtimeDevice().dump_ui_state()
        print("panel mở -> has_dialog:", _st9a["has_dialog"],
              "| dialog_ids:", _st9a["dialog_ids"],
              "| focused:", _st9a["focused_sig"])
        assert _st9a["has_dialog"] is True, \
            "panelBlvList/blvCardRoot hiện thì has_dialog phải True"
        assert "panelBlvList" in _st9a["dialog_ids"] and "panelPlay" in _st9a["dialog_ids"]
        assert _st9a["focused_sig"].startswith("blvCardRoot#")
        # (b) chỉ 1 id panel lẻ (panelScore) cũng đủ nhận dialog.
        _devmod9.sh = lambda cmd, timeout=30: _fake_xml9([("panelScore", "5 : 3", True)])
        assert _devmod9.RealtimeDevice().dump_ui_state()["has_dialog"] is True, \
            "panelScore đơn độc cũng phải nhận là dialog"
        # (c) dialog cũ (dialogTitle/btnCloseFeedback) vẫn nhận như trước.
        _devmod9.sh = lambda cmd, timeout=30: _fake_xml9([
            ("dialogTitle", "THÔNG BÁO", False),
            ("btnCloseFeedback", "ĐÃ HIỂU", True)])
        _st9c = _devmod9.RealtimeDevice().dump_ui_state()
        assert _st9c["has_dialog"] is True and "btnCloseFeedback" in _st9c["dialog_ids"]
        # (d) màn thường KHÔNG có dialog: channelCarouselPanel kết thúc bằng
        # "Panel" (không bắt đầu bằng "panel") -> không được nhận nhầm.
        _devmod9.sh = lambda cmd, timeout=30: _fake_xml9([
            ("nav_home", "Trang chủ", True),
            ("channelCarouselPanel", "", False),
            ("sportOptionsPanel", "", False)])
        _st9d = _devmod9.RealtimeDevice().dump_ui_state()
        print("màn thường (channelCarouselPanel) -> has_dialog:", _st9d["has_dialog"])
        assert _st9d["has_dialog"] is False, \
            "id kết thúc bằng 'Panel' không được tính là dialog"
    finally:
        _devmod9.sh = _orig_sh9
    print("DIALOG_PANEL_IDS_OK")

    # --- Test N10: driver không đuổi badge LIVE sau overlay (CI-T7 mục 2) ---
    # CI-T6 PLAYER_STREAMING: rule 0c2 (_goto_live_card_action) chạy 4 lần
    # nhưng sai trạng thái — panel đã mở (không được nhận là dialog) nên
    # luật đuổi theo badge LIVE ở list NỀN sau overlay thay vì bấm OK trên
    # phòng đang focus -> dao động dialog<->list (A-B-A-B) cả 8 bước.
    # Sửa: gate 0c2 bằng `not has_dialog` (+ guard trong chính
    # _goto_live_card_action) và panel không còn bị dismiss bằng BACK khi
    # mission cần player (đường vào player là OK trên phòng đang focus).
    _ui_panel_open = {
        "focused_sig": "blvCardRoot#[180,408][666,664]",
        "focused_text": "Phòng 1",
        "focused_bounds": "[180,408][666,664]",
        "all_visible_texts": [("panelBlvTitle", "Phòng BLV"),
                              ("blvCardRoot", "Phòng 1"),
                              ("cardRoot", "Singapore U17 vs India U"),
                              ("cardBadge", "LIVE")],
        "all_visible_nodes": [
            {"id": "panelBlvList", "text": "", "bounds": "[180,408][666,664]"},
            {"id": "blvCardRoot", "text": "Phòng 1", "bounds": "[180,408][666,664]"},
            {"id": "cardRoot", "text": "Singapore U17 vs India U", "bounds": "[100,700][500,900]"},
            {"id": "cardBadge", "text": "LIVE", "bounds": "[120,710][200,740]"}],
        "has_dialog": True, "dialog_ids": ["panelBlvList", "blvCardRoot"],
    }
    _dev10 = FakeDevice()
    _dev10._tab = 0  # PLAYER_STREAMING cần tab Trực tiếp (0)
    drv10b = Driver(_dev10, EvidenceGate(specs["MISSION_PLAYER_STREAMING_AND_CONTROLS"]),
                    specs["MISSION_PLAYER_STREAMING_AND_CONTROLS"])
    a_10 = drv10b.next_action(_ui_panel_open, "com.kenhlive.tv/.MainActivity", None, 0.0)
    print("panel mở + badge LIVE sau overlay ->", a_10.type, a_10.param, "| rule:", a_10.rule)
    assert (a_10.type, a_10.param, a_10.rule) == ("KEY", "OK", "open_player"), \
        "panel đang mở thì phải bấm OK trên phòng đang focus, không goto_live_card"
    # _goto_live_card_action trực tiếp cũng phải từ chối khi dialog mở.
    assert drv10b._goto_live_card_action(_ui_panel_open) is None, \
        "goto_live_card phải trả None khi has_dialog (guard trong hàm)"
    # Panel đóng -> hành vi cũ: focus ở nav, thẻ LIVE ở dưới -> goto_live_card.
    _ui_panel_closed = dict(_ui_panel_open,
                            focused_sig="nav_home#[362,0][563,112]",
                            focused_text="Trang chủ",
                            focused_bounds="[362,0][563,112]",
                            has_dialog=False, dialog_ids=[])
    _ui_panel_closed["all_visible_nodes"] = [
        {"id": "nav_home", "text": "Trang chủ", "bounds": "[362,0][563,112]"},
        {"id": "cardRoot", "text": "Singapore U17 vs India U", "bounds": "[100,400][500,700]"},
        {"id": "cardBadge", "text": "LIVE", "bounds": "[120,410][200,440]"}]
    _ui_panel_closed["all_visible_texts"] = [
        ("nav_home", "Trang chủ"), ("cardRoot", "Singapore U17 vs India U"),
        ("cardBadge", "LIVE")]
    a_10b = drv10b.next_action(_ui_panel_closed, "com.kenhlive.tv/.MainActivity", None, 0.0)
    print("panel đóng, thẻ LIVE dưới ->", a_10b.type, a_10b.param, "| rule:", a_10b.rule)
    assert a_10b.rule == "goto_live_card" and a_10b.param == "DPAD_DOWN", \
        "không có dialog thì luật goto_live_card cũ vẫn chạy"
    # Luật driver chọn ở mỗi bước phải ghi vào timeline (CI-T6: luật chạy
    # 4 lần mà không thấy được trong log — chỉ có print console).
    r10 = runner_mod.RealtimeRunner(out_dir="/tmp/qa_mock_actionlog", serial=None,
                                    vision_budget=0, no_vision=True)
    r10.run([specs["MISSION_COLD_START"]])
    _acts10 = [(e["step_id"], (e.get("action") or {}).get("rule")) for e in r10.timeline]
    print("timeline actions:", _acts10)
    assert len(_acts10) >= 3, "COLD_START phải có >= 3 bước timeline"
    assert _acts10[0][1] == "explore:down" and _acts10[1][1] == "explore:down", \
        "2 bước đầu phải ghi đúng rule explore:down vào timeline"
    assert all((e.get("action") or {}).get("rule") for e in r10.timeline[:-1]), \
        "mọi bước có hành động đều phải ghi rule vào timeline"
    print("DRIVER_NO_GOTO_BEHIND_DIALOG_OK")

    # --- Test B10: LONG_PRESS thật cho IPTV favorites (CI-T5 mục 10, nợ cũ) ---
    # Driver trước giờ không bao giờ phát LONG_PRESS (execute có sẵn nhưng
    # không rule nào dùng) nên favorites chưa từng kiểm tra thật.
    dev_lp = FakeDevice()
    dev_lp._tab = 2  # IPTV_CATEGORIES cần tab IPTV (2)
    drv_lp = Driver(dev_lp, EvidenceGate(specs["MISSION_IPTV_CATEGORIES_AND_FAVORITES"]),
                    specs["MISSION_IPTV_CATEGORIES_AND_FAVORITES"])
    ui_lp = {"focused_sig": "channelCard#[100,300][400,600]",
             "focused_text": "VTV1",
             "focused_bounds": "[100,300][400,600]",
             "all_visible_texts": [("channelCard", "VTV1")],
             "all_visible_nodes": [
                 {"id": "channelCard", "text": "VTV1", "bounds": "[100,300][400,600]"}],
             "has_dialog": False, "dialog_ids": []}
    a_lp = drv_lp.next_action(ui_lp, "com.kenhlive.tv/.MainActivity", None, 0.0)
    print("IPTV focus thẻ kênh ->", a_lp.type, a_lp.param, "| rule:", a_lp.rule)
    assert (a_lp.type, a_lp.param, a_lp.rule) == ("LONG_PRESS", "OK", "favorite_long_press"), \
        "mission IPTV favorites phải phát LONG_PRESS trên thẻ kênh"
    ok_lp, _settle = drv_lp.execute(a_lp)
    assert ok_lp and "LONG_PRESS(OK)" in dev_lp.action_history, \
        "execute LONG_PRESS phải gọi device.send_long_press thật"
    a_lp2 = drv_lp.next_action(ui_lp, "com.kenhlive.tv/.MainActivity", None, 0.0)
    assert a_lp2.rule != "favorite_long_press", "long-press chỉ phát 1 lần/mission"
    # Focus đang ở nav thì không long-press (để lần sau thử lại trên thẻ kênh).
    drv_lp2 = Driver(dev_lp, EvidenceGate(specs["MISSION_IPTV_CATEGORIES_AND_FAVORITES"]),
                     specs["MISSION_IPTV_CATEGORIES_AND_FAVORITES"])
    ui_nav = dict(FakeDevice.HOME_DUMP)  # focus nav_home
    a_nav = drv_lp2.next_action(ui_nav, "com.kenhlive.tv/.MainActivity", None, 0.0)
    assert a_nav.rule != "favorite_long_press", "không long-press trên nav"
    assert drv_lp2._long_press_tried is False, "chưa phát thì không đánh dấu đã thử"
    print("LONG_PRESS_FAVORITES_OK")

    # --- Test B11: vision retry lỗi transport hạ tầng (bắt buộc cho replay R6) ---
    # Replay R6 rớt P0-3 hai lần liên tiếp: 'Remote end closed connection
    # without response' — gọi lại ngay sau đó thì thành công 2/3 lần.
    # CI-T8 mục 5: retry ĐÚNG 1 lần (tổng 2 lần gửi) rồi mới ghi
    # UNVERIFIED — thử 3 lần cũ tốn tới 102s/call lỗi, không đáng.
    import vision as _vis
    import urllib.request as _urlreq
    import http.client as _httpc

    class _FakeResp:
        def read(self):
            return json.dumps({"choices": [{"message": {"content": "{\"found\": true}"}}]}).encode()

    _orig_urlopen = _urlreq.urlopen
    _orig_backoff = _vis._TRANSPORT_BACKOFF_S
    _calls = {"n": 0}

    def _flaky_urlopen(req, timeout=None):
        _calls["n"] += 1
        if _calls["n"] <= 1:
            raise _httpc.RemoteDisconnected("Remote end closed connection without response")
        return _FakeResp()

    assert _vis._is_transport_error(_httpc.RemoteDisconnected("Remote end closed connection without response"))
    assert not _vis._is_transport_error(ValueError("boom"))
    # _post lên URL NIM sẽ acquire() slot của LIMITER toàn cục — snapshot và
    # khôi phục sau test để không làm bẩn số đếm của test F (no-vision).
    from ratelimit import LIMITER as _LIM
    _lim_req, _lim_stamps = _LIM.requests, list(_LIM._stamps)
    _vis._TRANSPORT_BACKOFF_S = (0.05,)
    _urlreq.urlopen = _flaky_urlopen
    try:
        out11 = _vis._post(_vis.NVIDIA_NIM_BASE, "",
                           {"model": "x", "messages": []}, timeout=5)
    finally:
        _urlreq.urlopen = _orig_urlopen
        _vis._TRANSPORT_BACKOFF_S = _orig_backoff
    print("vision transport retry: urlopen calls", _calls["n"], "->", out11)
    assert _calls["n"] == 2, "lỗi transport retry đúng 1 lần (tổng 2 lần gửi)"
    assert out11 == '{"found": true}', "lần thứ 2 thành công thì phải trả nội dung"
    # Lỗi transport 2 lần liên tiếp -> raise sau 2 lần gửi (hết retry).
    def _flaky2_urlopen(req, timeout=None):
        _calls["n"] += 1
        raise _httpc.RemoteDisconnected("Remote end closed connection without response")
    _calls["n"] = 0
    _urlreq.urlopen = _flaky2_urlopen
    try:
        _vis._post(_vis.NVIDIA_NIM_BASE, "", {"model": "x", "messages": []}, timeout=5)
        _raised11 = False
    except _httpc.RemoteDisconnected:
        _raised11 = True
    finally:
        _urlreq.urlopen = _orig_urlopen
    assert _raised11 and _calls["n"] == 2, \
        "lỗi transport 2 lần liên tiếp phải raise sau 2 lần gửi (1 retry)"
    # Lỗi không phải transport thì vẫn chỉ thử 2 lần rồi raise.

    def _boom_urlopen(req, timeout=None):
        _calls["n"] += 1
        raise ValueError("boom")

    _calls["n"] = 0
    _urlreq.urlopen = _boom_urlopen
    try:
        _vis._post(_vis.NVIDIA_NIM_BASE, "", {"model": "x", "messages": []}, timeout=5)
        _raised = False
    except ValueError:
        _raised = True
    finally:
        _urlreq.urlopen = _orig_urlopen
        _LIM.requests = _lim_req
        _LIM._stamps = _lim_stamps
    assert _raised and _calls["n"] == 2, "lỗi thường chỉ thử 2 lần rồi raise"
    print("VISION_TRANSPORT_RETRY_OK")

    # --- Test C: verdict không PASS khi tỉ lệ pass thấp ---
    from judge import HonestJudge
    j = HonestJudge("/tmp/qa_mock_out")
    fake_missions = [{"name": "m%d" % i, "title": "m%d" % i,
                      "outcome": "PASS" if i == 0 else "FAIL", "reason": "x",
                      "evidence": {}, "steps": 4} for i in range(17)]
    rep = j.judge(fake_missions, [], [])
    print("verdict 1/17 pass, score", rep["score"], "->", rep["verdict"])
    assert rep["verdict"] == "NEEDS_FIX"
    print("VERDICT_OK")

    # --- Test D: reset đầu mission — đang ở PlayerActivity phải BACK về Home ---
    r = runner_mod.RealtimeRunner(out_dir="/tmp/qa_mock_out", serial=None,
                                  vision_budget=0, no_vision=True)
    assert isinstance(r.device, FakeDevice)
    r.device._activity = "com.kenhlive.tv/.PlayerActivity"
    r.device._tab = 0  # đang ở tab Sports, mission cần tab 6
    report = r.run([specs["MISSION_COLD_START"]])
    print("reset keys:", [k for k in r.device.keys if "BACK" in k or "SWITCH" in k],
          "| activity sau reset:", r.device._activity, "| tab:", r.device._tab)
    assert r.device._activity == "com.kenhlive.tv/.MainActivity", "reset không về MainActivity"
    assert r.device._tab == 6, "reset không chuyển về tab 6"
    assert r.mission_results[0]["outcome"] == "PASS"
    print("RESET_OK")

    # --- Test E: OSD gate trên frame THẬT CI-T2 ---
    # step_091: OSD ẩn (chỉ có phụ đề video) -> OCR detectors phải trả [].
    # step_094: OSD hiện, phụ đề đè seekbar THẬT -> subtitle detector vẫn bắt.
    import detectors as det
    import ocr as ocr_mod
    shots = os.path.expanduser("~/workspace/kenhlive-plan/qa-run-42979726992/shots")
    png91 = open(os.path.join(shots, "step_091_mission_.jpg"), "rb").read()
    png94 = open(os.path.join(shots, "step_094_mission_.jpg"), "rb").read()
    ui_hidden = {"focused_sig": "NONE", "osd_visible": False}
    ui_shown = {"focused_sig": "NONE", "osd_visible": True}
    act_w = "com.kenhlive.tv/.phim.WebPlayerActivity"
    ctx = {"reported": set(), "steps_since_ocr": 99}
    f91 = (det.detect_text_overlap(png91, ui_hidden, act_w, dict(ctx), "step_091.jpg", 0, ocr_mod)
           + det.detect_clipped_text(png91, ui_hidden, act_w, dict(ctx), "step_091.jpg", 0, ocr_mod)
           + det.detect_subtitle_seekbar_overlap(png91, ui_hidden, act_w, dict(ctx), "step_091.jpg", 0, ocr_mod))
    print("step_091 (OSD ẩn) findings:", len(f91), [f["issue"] for f in f91])
    assert f91 == [], "OSD ẩn mà detector vẫn báo lỗi (false positive CI-T2 #7-10)"
    ctx2 = {"reported": set(), "steps_since_ocr": 99}
    f94 = det.detect_subtitle_seekbar_overlap(png94, ui_shown, act_w, dict(ctx2), "step_094.jpg", 0, ocr_mod)
    print("step_094 (OSD hiện) subtitle findings:", len(f94), [f["issue"] for f in f94])
    assert len(f94) == 1 and "seekbar" in f94[0]["issue"], "finding 11 thật bị mất sau khi thêm guard"
    print("OSD_GATE_OK")

    # --- Test G: defect reel CHIA video_t cho speed_factor (CI-T4) ---
    # Tour 12s thật -> tăng tốc 4x còn 3s. Reel phải cắt video_t/4.
    import shutil
    import subprocess as sp
    if shutil.which("ffmpeg"):
        td = "/tmp/qa_mock_reel"
        os.makedirs(td, exist_ok=True)
        sp.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i",
                "testsrc=duration=12:size=320x180:rate=10",
                "-c:v", "libx264", "-pix_fmt", "yuv420p", os.path.join(td, "raw12.mp4")],
               check=True, timeout=60)
        sp.run(["ffmpeg", "-y", "-v", "error", "-i", os.path.join(td, "raw12.mp4"),
                "-filter:v", "setpts=0.25*PTS", "-c:v", "libx264", "-pix_fmt", "yuv420p",
                os.path.join(td, "tour4x.mp4")], check=True, timeout=60)
        dur = float(sp.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                            "-of", "default=noprint_wrappers=1:nokey=1",
                            os.path.join(td, "tour4x.mp4")], capture_output=True,
                           text=True, timeout=30).stdout.strip())
        print("tour 4x duration:", dur)
        assert 2.5 < dur < 3.5, "video test 4x phải ~3s"
        j2 = HonestJudge(td)
        fakes = [{"severity": "HIGH", "area": "X", "issue": "defect A",
                  "evidence": {"frame": "a.jpg", "video_t": 5.0}},
                 {"severity": "HIGH", "area": "X", "issue": "defect B",
                  "evidence": {"frame": "b.jpg", "video_t": 10.0}},
                 # CI-T6 mục 3: defect C ở 20.0s thật -> 5.0s trong tour 3s
                 # (vượt tour như entry 3 video_t 177.6s vượt tour 175.2s ở CI-T5).
                 {"severity": "MEDIUM", "area": "X", "issue": "defect C",
                  "evidence": {"frame": "c.jpg", "video_t": 20.0}}]
        rp, entries = j2.build_defect_reel(os.path.join(td, "tour4x.mp4"), fakes,
                                           speed_factor=4.0)
        print("reel entries video_t:", [e["video_t"] for e in entries])
        assert entries[0]["video_t"] == 1.2 and entries[1]["video_t"] == 2.5
        print("reel entries covered/clamped:",
              [(e["video_t"], e["covered"], e["clamped"], e["seg_start"]) for e in entries])
        assert entries[0]["covered"] is True and entries[1]["covered"] is True, \
            "defect trong tour phải covered"
        assert entries[2]["video_t"] == 5.0 and entries[2]["covered"] is False \
            and entries[2]["clamped"] is True, \
            "defect vượt tour phải bị kẹp (clamped) và không tính là covered"
        assert entries[2]["seg_start"] == 0.0 and abs(entries[2]["seg_s"] - dur) < 0.15, \
            "đoạn kẹp phải nằm trong tour (6s cuối tour %.1fs -> bắt đầu 0.0s)" % dur
        rdur = float(sp.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                             "-of", "default=noprint_wrappers=1:nokey=1", rp],
                            capture_output=True, text=True, timeout=30).stdout.strip())
        print("reel duration (speed 4x):", rdur, "| reel path:", rp)
        # Hai đoạn cắt ở 0-3s trong file 3s -> reel ~6s. Không chia hệ số thì
        # đoạn 2 cắt ở 7s (vượt file) -> reel chỉ ~3s.
        assert rdur >= 5.0, "reel phải đủ 2 đoạn (~6s), không được rỗng 1 đoạn"
        print("REEL_4X_OK")
    else:
        print("REEL_4X_SKIP (không có ffmpeg local)")

    # --- Test H: fake-score chỉ tố khi ổn định 2 lần (đồng hồ đổi thì không) ---
    import detectors as det2
    ctxh = {"reported": set(), "_score_seen": {}}
    ui_clock = {"all_visible_texts": [("cardScoreHome", "15 : 11")]}
    f1 = det2.detect_fake_score(ui_clock, "com.kenhlive.tv/.MainActivity", ctxh, "s1.jpg", 1)
    assert f1 == [], "lần đầu thấy đồng hồ không được tố"
    ui_clock2 = {"all_visible_texts": [("cardScoreHome", "17 : 23")]}
    f2 = det2.detect_fake_score(ui_clock2, "com.kenhlive.tv/.MainActivity", ctxh, "s2.jpg", 2)
    assert f2 == [], "đồng hồ đổi giá trị (15:11->17:23) không được tố"
    f3 = det2.detect_fake_score(ui_clock2, "com.kenhlive.tv/.MainActivity", ctxh, "s3.jpg", 3)
    print("clock stable 17:23 x2 findings:", len(f3), [f["issue"] for f in f3])
    assert len(f3) == 1 and "17 : 23" in f3[0]["issue"], "giá trị ổn định 2 lần phải bị tố"
    # frame trích dẫn phải chứa đúng giá trị tố (CI-T3 tố 17:23 trên frame 15:11)
    assert f3[0]["evidence"]["frame"] == "s3.jpg"
    ctxh2 = {"reported": set(), "_score_seen": {}}
    ui_ok = {"all_visible_texts": [("cardScoreHome", "0 : 0")]}
    assert det2.detect_fake_score(ui_ok, "com.kenhlive.tv/.MainActivity", ctxh2, "s4.jpg", 4) == []
    assert det2.detect_fake_score(ui_ok, "com.kenhlive.tv/.MainActivity", ctxh2, "s5.jpg", 5) == []
    print("FAKE_SCORE_CLOCK_OK")

    # --- Test H2: fake-score theo môn (CI-T5 mục 1) ---
    # Bóng rổ 54:71 thật (NBL, CI-T4 FP) không bị tố; bóng đá 12:3 vẫn bị tố;
    # giờ đội lốt tỉ số 15:00 vẫn bị tố dù ở context bóng rổ.
    ctxb = {"reported": set(), "_score_seen": {}}
    ui_bb = {"all_visible_texts": [("heroSub", "Liên đoàn Bóng rổ Quốc gia Úc"),
                                   ("cardScoreHome", "54 : 71")]}
    assert det2.detect_fake_score(ui_bb, "com.kenhlive.tv/.MainActivity", ctxb, "b1.jpg", 1) == []
    fb = det2.detect_fake_score(ui_bb, "com.kenhlive.tv/.MainActivity", ctxb, "b2.jpg", 2)
    print("basketball 54:71 x2 findings:", len(fb))
    assert fb == [], "tỉ số bóng rổ thật 54:71 không được tố (FP CI-T4)"
    ctxf = {"reported": set(), "_score_seen": {}}
    ui_fb = {"all_visible_texts": [("heroSub", "Bóng đá Ngoại hạng Anh"),
                                   ("cardScoreHome", "12 : 3")]}
    assert det2.detect_fake_score(ui_fb, "com.kenhlive.tv/.MainActivity", ctxf, "f1.jpg", 1) == []
    ff = det2.detect_fake_score(ui_fb, "com.kenhlive.tv/.MainActivity", ctxf, "f2.jpg", 2)
    print("football 12:3 x2 findings:", len(ff), [x["issue"] for x in ff])
    assert len(ff) == 1 and "12 : 3" in ff[0]["issue"], "bóng đá 12:3 vẫn phải bị tố"
    ctxt = {"reported": set(), "_score_seen": {}}
    ui_tm = {"all_visible_texts": [("heroSub", "Liên đoàn Bóng rổ Quốc gia Úc"),
                                   ("cardScoreHome", "15 : 00")]}
    assert det2.detect_fake_score(ui_tm, "com.kenhlive.tv/.MainActivity", ctxt, "t1.jpg", 1) == []
    ft = det2.detect_fake_score(ui_tm, "com.kenhlive.tv/.MainActivity", ctxt, "t2.jpg", 2)
    print("basketball ctx 15:00 x2 findings:", len(ft), [x["issue"] for x in ft])
    assert len(ft) == 1 and "15 : 00" in ft[0]["issue"], \
        "nhánh giờ đội lốt tỉ số (15:00) phải tố dù ở context bóng rổ"
    print("FAKE_SCORE_BASKETBALL_OK")

    # --- Test I: kẹt A-B-A-B (luân phiên, focused_sig đổi mỗi bước) ---
    drv4 = Driver(FakeDevice(), EvidenceGate(specs["MISSION_PHIM_EPISODE_PICKER_AND_FAVORITE"]),
                  specs["MISSION_PHIM_EPISODE_PICKER_AND_FAVORITE"])
    sigA = dict(FakeDevice.HOME_DUMP, focused_sig="btnHeroBackHome#[0,0][100,100]")
    sigB = dict(FakeDevice.HOME_DUMP, focused_sig="heroPlay#[200,0][300,100]")
    for s in (sigA, sigB, sigA, sigB):
        drv4.note_state(s, "com.kenhlive.tv/.MainActivity", motion_playing=False)
    print("A-B-A-B stuck:", drv4.stuck(), "| revisit_streak:", drv4._revisit_streak)
    assert drv4.stuck(), "luân phiên A-B-A-B phải tính kẹt (CI-T3 EPISODE_PICKER)"
    drv5 = Driver(FakeDevice(), EvidenceGate(specs["MISSION_PHIM_EPISODE_PICKER_AND_FAVORITE"]),
                  specs["MISSION_PHIM_EPISODE_PICKER_AND_FAVORITE"])
    for i in range(4):
        drv5.note_state(dict(FakeDevice.HOME_DUMP, focused_sig="item%d#[0,0][100,100]" % i),
                        "com.kenhlive.tv/.MainActivity", motion_playing=False)
    assert not drv5.stuck(), "đi qua 4 focus khác nhau không phải kẹt"
    print("STUCK_ABAB_OK")

    # --- Test J: stress gate FAIL khi app văng khỏi foreground ---
    from gate import EvidenceGate as EG
    sg = EG(specs["MISSION_DPAD_CHAOS_STRESS_AND_RECOVERY"])
    for _ in range(6):
        sg.observe("com.kenhlive.tv/.MainActivity", [], [], False, False, 1.0)
    v, r_, _ = sg.evaluate("s6.jpg")
    assert v == "PASS", "stress đủ bước + app foreground phải PASS"
    sg2 = EG(specs["MISSION_DPAD_CHAOS_STRESS_AND_RECOVERY"])
    for i in range(6):
        act = ("com.kenhlive.tv/.MainActivity" if i < 5
               else "com.google.android.tvlauncher/.MainActivity")
        sg2.observe(act, [], [], False, False, 1.0)
    v2, r2_, _ = sg2.evaluate("s6.jpg")
    print("stress văng launcher:", v2, "|", r2_)
    assert v2 == "FAIL", "stress mà activity cuối là launcher phải FAIL (lỗ false-pass CI-T4)"
    print("STRESS_GATE_OK")

    # --- Test K: guard chuỗi OCR rác (vowel + token dài) ---
    assert not det2._plausible_text("LPđPfUHPBIHUALI"), "chuỗi rác 15 ký tự phải rớt"
    assert det2._plausible_text("VTV4 HD"), "VTV4 HD là chữ thật"
    assert det2._plausible_text("TRANG CHỦ"), "TRANG CHỦ là chữ thật"
    assert det2._plausible_text("TRỰC…"), "TRỰC… là chữ thật"
    assert not det2._plausible_text("‹©"), "ký tự lạ phải rớt"
    print("PLAUSIBLE_GARBAGE_OK")

    # --- Test L: frame evidence của mission FAIL phải tồn tại trên đĩa ---
    r3 = runner_mod.RealtimeRunner(out_dir="/tmp/qa_mock_out_fail", serial=None,
                                   vision_budget=0, no_vision=True)
    r3.run([specs["MISSION_SPORTS_MULTI_SOURCE"]])  # cần text 'cola' (CI-T6 mục 4; trước đó 'socolive'): mock không có -> FAIL
    res3 = r3.mission_results[0]
    print("FAIL mission:", res3["name"], res3["outcome"], "| evidence frame:",
          (res3["evidence"] or {}).get("frame"))
    assert res3["outcome"] == "FAIL"
    cited = (res3["evidence"] or {}).get("frame")
    assert cited, "mission FAIL phải có frame trong evidence"
    assert os.path.exists(os.path.join("/tmp/qa_mock_out_fail", "shots",
                                       os.path.basename(cited))), \
        "frame evidence FAIL %s thiếu trên đĩa (CI-T3: 6/7 frame FAIL thiếu)" % cited
    print("FAIL_FRAME_OK")

    # --- Test N1: text-overlap không tố "Xem ngay" (CI-T6 mục 1) ---
    # FP HIGH CI-T5: pill "Xem ngay" sạch trên step_010 nhưng detector tố
    # "Chữ 'Xem' đè lên 'ngay' (chồng 93%)". Box THẬT trong report CI-T5:
    #   Xem (432, 927, 482, 986) vs ngay (400, 929, 590, 984)
    # (tọa độ ảnh 960x540 — "Xem" nằm gần gọn trong "ngay", cùng baseline).
    # Guard chuỗi con là SAI ("Xem" in "ngay" == False): đây là 2 box OCR
    # trùng nhau của cùng 1 dòng (PSM 11 không khử trùng), không phải 2 text
    # đè nhau. Sửa: (a) gộp box cùng dòng thành 1 cụm trước khi so chồng,
    # (b) bỏ qua cặp trùng (box nhỏ >=90% nằm trong box lớn + cùng baseline).
    import ocr as ocr_n1
    _boxes_fp = [
        {"text": "Xem", "x0": 432, "y0": 927, "x1": 482, "y1": 986, "conf": 90},
        {"text": "ngay", "x0": 400, "y0": 929, "x1": 590, "y1": 984, "conf": 88},
    ]
    _pairs_fp = det2._ocr_boxes_pairwise_overlap(_boxes_fp)
    print("cặp 'Xem'/'ngay' 93% sau guard trùng:", _pairs_fp)
    assert _pairs_fp == [], "box nhỏ 93% nằm trong box lớn + cùng baseline là trùng OCR, không được tố"
    _cl = ocr_n1.cluster_same_line_boxes(_boxes_fp)
    print("cụm cùng dòng 'Xem'+'ngay' ->", len(_cl), _cl[0]["text"] if _cl else None)
    assert len(_cl) == 1 and set(_cl[0]["text"].split()) == {"Xem", "ngay"}, \
        "2 box cùng dòng phải gộp thành 1 cụm trước khi so chồng"
    # Chữ đè THẬT (2 dòng khác baseline, chồng 36%) vẫn phải tố.
    _boxes_real = [
        {"text": "Dòng 1", "x0": 100, "y0": 100, "x1": 400, "y1": 140, "conf": 90},
        {"text": "Dòng 2", "x0": 110, "y0": 125, "x1": 410, "y1": 165, "conf": 90},
    ]
    assert len(ocr_n1.cluster_same_line_boxes(_boxes_real)) == 2, \
        "2 dòng khác baseline không được gộp (lỗi đè đôi tiêu đề phải còn tố được)"
    assert len(det2._ocr_boxes_pairwise_overlap(_boxes_real)) == 1, \
        "chữ đè thật khác baseline vẫn phải tố"
    # Regression trên frame THẬT step_010 CI-T5 (cần tesseract như Test E):
    # detector text_overlap trên toàn frame phải trả 0 finding chứa "Xem".
    shots10 = os.path.expanduser("~/workspace/kenhlive-plan/qa-run-43010818257/qa-report-realtime/shots")
    png10 = open(os.path.join(shots10, "step_010_sports_m.jpg"), "rb").read()
    ui10 = {"focused_sig": "cardRoot#[109,653][787,1035]", "osd_visible": False,
            "all_visible_texts": []}
    ctx10 = {"reported": set(), "steps_since_ocr": 99}
    f10 = det2.detect_text_overlap(png10, ui10, "com.kenhlive.tv/.MainActivity",
                                   dict(ctx10), "step_010_sports_m.jpg", 73.1, ocr_n1)
    print("step_010 (pill 'Xem ngay' sạch) text_overlap findings:",
          len(f10), [f["issue"] for f in f10])
    assert not any("Xem" in (f.get("issue") or "") for f in f10), \
        "pill 'Xem ngay' sạch trên step_010 không được tố (FP HIGH CI-T5)"
    print("OVERLAP_XEM_NGAY_OK")

    # --- Test M: wait_backoff không đếm request ---
    from ratelimit import RateLimiter
    import time as _time
    lim = RateLimiter()
    lim.backoff_until = _time.monotonic() + 0.2
    lim.wait_backoff()
    assert lim.requests == 0, "chờ backoff không được đếm thành request"
    lim.acquire()
    assert lim.requests == 1, "chỉ lần gửi thật mới đếm"
    print("RATELIMIT_WAIT_OK")

    # --- Test N18: vòng focus trên ẢNH trong WebPlayer (CI-T8 mục 1) ---
    # CI-T7 finding #1 giả: dump NONE trong WebPlayer nhưng mắt thấy viền
    # vàng quanh nút OSD — detector cũ tin dump nên tố mất focus oan.
    # Ảnh giả 960x540: nút OSD viền VÀNG ở band dưới + khối vàng ĐẶC (phải
    # loại bằng guard tỉ lệ lấp) + khối trắng đặc (phải loại).
    def _ring_png():
        from PIL import Image as _Im, ImageDraw as _Dr
        _im = _Im.new("RGB", (960, 540), (25, 25, 30))
        _d = _Dr.Draw(_im)
        _d.rectangle([100, 450, 300, 500], outline=(255, 200, 0), width=3)
        _d.rectangle([600, 450, 700, 500], fill=(255, 200, 0))
        _d.rectangle([760, 450, 900, 500], fill=(240, 240, 240))
        _buf = io.BytesIO()
        _im.save(_buf, format="PNG")
        return _buf.getvalue()
    _dev18 = RealtimeDevice()
    _found18, _col18, _cov18, _box18 = _dev18.detect_focus_ring_anywhere(_ring_png())
    print("vòng vàng OSD trên ảnh ->", _found18, _col18, _cov18, _box18)
    assert _found18 is True and _col18 == "YELLOW", \
        "viền vàng quanh nút OSD phải được nhận là vòng focus (CI-T7 #1 giả)"
    assert _box18 and 180 <= _box18[0] <= 220 and 880 <= _box18[1] <= 920, \
        "box vòng phải gần nút đã vẽ (100,450)-(300,500) ở 960x540, được %s" % (_box18,)
    # Khung thường (khối đặc, không có vòng) -> False.
    _found18b, _, _, _ = _dev18.detect_focus_ring_anywhere(_fake_png(0))
    print("khung thường (khối đặc) ->", _found18b)
    assert _found18b is False, "khối vàng/trắng đặc không phải vòng focus"
    # Tích hợp detector: dump NONE + OSD hiện + ảnh có vòng -> KHÔNG tố;
    # ảnh không có vòng -> tố như cũ (P0-6 thật vẫn bắt).
    _ui18 = {"focused_sig": "NONE", "osd_visible": True, "image_focus_ring": True,
             "all_visible_texts": []}
    _f18 = det2.detect_player_focus_loss(_ui18, "com.kenhlive.tv/.phim.WebPlayerActivity",
                                         {"reported": set()}, "step_056_web.jpg", 1181.7)
    print("WebPlayer dump NONE + ảnh có vòng -> findings:", len(_f18))
    assert _f18 == [], "ảnh có viền vàng thì không được tố mất focus (HIGH giả CI-T7)"
    _ui18b = dict(_ui18)
    _ui18b["image_focus_ring"] = False
    _f18b = det2.detect_player_focus_loss(_ui18b, "com.kenhlive.tv/.phim.WebPlayerActivity",
                                          {"reported": set()}, "step_056_web.jpg", 1181.7)
    assert len(_f18b) == 1 and _f18b[0]["severity"] == "HIGH", \
        "ảnh cũng không có vòng thì mất focus thật vẫn phải tố"
    print("IMAGE_FOCUS_RING_OK")

    # --- Test N19: timebase tour theo chunk + verify nội dung reel (CI-T8 mục 2) ---
    # CI-T7: video_t = QA_t / 4,7 đều bị lệch ~10-17 tour-giây (reel mỗi
    # đoạn chỉ ~25% đúng cảnh) vì giữa các chunk có khoảng trống. Sửa:
    # (a) map QA_t -> tour_t theo chunk_map (nội suy trong chunk, kẹp ở
    # khoảng trống); (b) verify nội dung đoạn reel bằng frame-match với
    # shot trích dẫn, dời tâm cắt về vị trí khớp nhất (±6s).
    import video_recorder as _vr19
    _cm19 = [{"qa_start_s": 0, "qa_end_s": 175, "raw_start_s": 0, "raw_end_s": 170, "dur_s": 170},
             {"qa_start_s": 180, "qa_end_s": 355, "raw_start_s": 170, "raw_end_s": 345, "dur_s": 175}]
    _t19a, _g19a = _vr19.qa_to_tour_t(87.5, _cm19, 4.7)
    print("QA 87.5s trong chunk 1 -> tour", _t19a, "in_gap:", _g19a)
    assert abs(_t19a - 85.0 / 4.7) < 0.2 and _g19a is False, "nội suy trong chunk phải đúng"
    _t19b, _g19b = _vr19.qa_to_tour_t(177, _cm19, 4.7)
    assert _g19b is True and abs(_t19b - 170.0 / 4.7) < 0.3, \
        "QA rơi vào khoảng trống giữa 2 chunk phải kẹp về cuối chunk trước + cờ in_gap"
    _t19c, _g19c = _vr19.qa_to_tour_t(267.5, _cm19, 4.7)
    assert abs(_t19c - 257.5 / 4.7) < 0.2 and _g19c is False, "nội suy trong chunk 2 phải đúng"
    _t19d, _g19d = _vr19.qa_to_tour_t(94, None, 4.7)
    assert abs(_t19d - 20.0) < 0.1 and _g19d is False, \
        "không có chunk_map thì fallback chia đều như cũ"
    print("CHUNK_MAP_OK")
    # (b) verify nội dung reel: tour 12s (đỏ 0-6s, xanh 6-12s), shot đỏ,
    # finding ở video_t=9.0 (vùng xanh — lệch do drift) -> phải dời tâm cắt
    # về ~3s (vùng đỏ khớp shot) và gắn content_verified=True; shot xanh lá
    # (không có trong tour) -> content_verified=False.
    import shutil as _sh19
    import subprocess as _sp19
    if _sh19.which("ffmpeg") is None:
        print("REEL_CONTENT_SKIP (thiếu ffmpeg)")
    else:
        _out19 = "/tmp/qa_mock_reel2"
        _sh19.rmtree(_out19, ignore_errors=True)
        os.makedirs(os.path.join(_out19, "shots"), exist_ok=True)
        _tour19 = os.path.join(_out19, "tour.mp4")
        _r19 = _sp19.run(
            ["ffmpeg", "-y", "-v", "error",
             "-f", "lavfi", "-i", "color=c=red:s=320x180:r=10:d=6",
             "-f", "lavfi", "-i", "color=c=blue:s=320x180:r=10:d=6",
             "-filter_complex", "[0:v][1:v]concat=n=2:v=1:a=0",
             "-c:v", "libx264", "-pix_fmt", "yuv420p", _tour19],
            capture_output=True, timeout=120)
        assert os.path.exists(_tour19) and os.path.getsize(_tour19) > 1000, \
            "không dựng được tour giả bằng ffmpeg"
        from PIL import Image as _Im19
        _Im19.new("RGB", (960, 540), (255, 0, 0)).save(
            os.path.join(_out19, "shots", "step_001_test.jpg"), "JPEG", quality=85)
        _Im19.new("RGB", (960, 540), (0, 255, 0)).save(
            os.path.join(_out19, "shots", "step_002_test.jpg"), "JPEG", quality=85)
        from judge import HonestJudge as _HJ19
        _j19 = _HJ19(_out19)
        _f19 = [{"severity": "HIGH", "area": "Test", "issue": "defect đỏ",
                 "detail": "d", "suggestion": "s",
                 "evidence": {"frame": "step_001_test.jpg", "video_t": 9.0, "ui_state": ""}},
                {"severity": "HIGH", "area": "Test", "issue": "defect xanh lá",
                 "detail": "d", "suggestion": "s",
                 "evidence": {"frame": "step_002_test.jpg", "video_t": 9.0, "ui_state": ""}}]
        _rp19, _en19 = _j19.build_defect_reel(_tour19, _f19, speed_factor=1.0)
        print("reel entries:", [(e["video_t"], e.get("content_verified"), e.get("content_diff"),
                                 e.get("seg_start")) for e in _en19])
        assert len(_en19) == 2, "2 finding phải ra 2 entry"
        assert _en19[0]["content_verified"] is True, \
            "đoạn đỏ phải khớp shot đỏ (content_verified True)"
        assert abs(_en19[0]["video_t"] - 3.0) < 1.0, \
            "tâm cắt phải dời về vùng đỏ khớp shot (~3s), được %s" % _en19[0]["video_t"]
        assert _en19[1]["content_verified"] is False, \
            "shot xanh lá không có trong tour thì không được ghi khớp"
        assert os.path.exists(_rp19) and os.path.getsize(_rp19) > 1000, \
            "reel phải được ghi ra file"
        print("REEL_CONTENT_OK")

    # --- Test N20: đồng bộ frame bằng chứng + FAIL ồn ào khi thiếu (CI-T8 mục 3) ---
    # CI-T7: step_035/step_042 trích dẫn trong evidence nhưng file không có
    # trong shots/ (dedup trả path cũ mà evidence vẫn giữ tên mới);
    # step_051: dialog mở thật nhưng khung cuối mission không thấy dialog.
    from gate import EvidenceGate as _EG20
    # (a) frame bằng chứng thiếu trên đĩa -> FAIL ồn ào, không PASS lặng lẽ.
    _r20a = runner_mod.RealtimeRunner(out_dir="/tmp/qa_mock_ev3a", serial=None,
                                      vision_budget=0, no_vision=True)
    _g20a = _EG20(specs["MISSION_COLD_START"])
    _g20a.outcome = "PASS"
    _g20a.outcome_reason = "đủ mọi tín hiệu áp dụng"
    _g20a.evidence = {"frame": "step_999_ghost.jpg", "activities_seen": [],
                      "texts_seen": [], "views_seen": [], "dialog_seen": False,
                      "motion_seen": False, "vision_confirmations": [],
                      "vision_denials": 0, "playback_status": "unknown",
                      "playback_readings": [], "playback_monotonic": True,
                      "steps": 3}
    _res20a = _r20a._finish_mission(specs["MISSION_COLD_START"], _g20a, [])
    print("evidence ghost -> outcome:", _res20a["outcome"], "| reason:", _res20a["reason"])
    assert _res20a["outcome"] == "FAIL", "frame bằng chứng thiếu phải FAIL ồn ào"
    assert _res20a.get("evidence_frame_missing") is True
    assert "BẰNG CHỨNG THIẾU" in _res20a["reason"]
    # (b) mission cần dialog -> evidence frame phải là khung dialog đã thấy.
    _r20b = runner_mod.RealtimeRunner(out_dir="/tmp/qa_mock_ev3b", serial=None,
                                      vision_budget=0, no_vision=True)
    _g20b = _EG20(specs["MISSION_PHIM_EPISODE_PICKER_AND_FAVORITE"])
    _g20b.outcome = "PASS"
    _g20b.outcome_reason = "đủ mọi tín hiệu áp dụng"
    _g20b.evidence = {"frame": "step_005_phim_epi.jpg", "activities_seen": [],
                      "texts_seen": [], "views_seen": [], "dialog_seen": True,
                      "motion_seen": False, "vision_confirmations": [],
                      "vision_denials": 0, "playback_status": "unknown",
                      "playback_readings": [], "playback_monotonic": True,
                      "steps": 5}
    _dlg20 = {"png": _fake_png(7), "frame_ref": "step_002_phim_epi.jpg", "t_offset": 5.0}
    _last20 = {"png": _fake_png(8), "frame_ref": "step_005_phim_epi.jpg", "t_offset": 12.0}
    _res20b = _r20b._finish_mission(specs["MISSION_PHIM_EPISODE_PICKER_AND_FAVORITE"],
                                    _g20b, [_last20], dialog_obs=_dlg20)
    _ev20b = (_res20b.get("evidence") or {}).get("frame")
    print("dialog evidence frame:", _ev20b, "| duplicate_of:",
          _res20b.get("evidence_frame_duplicate_of"))
    assert _ev20b and "step_002" in _ev20b, \
        "evidence frame phải là khung dialog (step_002), không phải khung cuối, được %s" % _ev20b
    assert os.path.exists(os.path.join("/tmp/qa_mock_ev3b", "shots",
                                       os.path.basename(_ev20b))), \
        "frame dialog trích dẫn phải tồn tại trên đĩa"
    assert _res20b["outcome"] == "PASS", "dialog frame có đủ thì không được FAIL oan"
    # (c) dedup: 2 mission cùng 1 frame cuối -> evidence frame của mission 2
    # phải trỏ file TỒN TẠI (shot dùng lại), không trỏ tên mới không có file.
    import shutil as _sh20c
    _sh20c.rmtree("/tmp/qa_mock_ev3c", ignore_errors=True)

    class _DupDevice20(FakeDevice):
        def screencap_bytes(self):
            return _fake_png(0)

    _orig_dev20 = runner_mod.RealtimeDevice
    runner_mod.RealtimeDevice = _DupDevice20
    try:
        _r20c = runner_mod.RealtimeRunner(out_dir="/tmp/qa_mock_ev3c", serial=None,
                                          vision_budget=0, no_vision=True)
        _r20c.run([specs["MISSION_COLD_START"], specs["MISSION_COLD_START"]])
    finally:
        runner_mod.RealtimeDevice = _orig_dev20
    _ev20c = (_r20c.mission_results[1].get("evidence") or {}).get("frame")
    print("mission 2 evidence frame (dedup):", _ev20c)
    assert _ev20c and os.path.exists(os.path.join("/tmp/qa_mock_ev3c", "shots",
                                                  os.path.basename(_ev20c))), \
        "evidence frame sau dedup phải trỏ file tồn tại, được %s" % _ev20c
    print("EVIDENCE_SYNC_OK")

    # --- Test N21: kẹt lần 1 thoát cục bộ trước khi tốn vision (CI-T8 mục 4) ---
    # Vision latency trung bình 57,9s/call là nút thắt (CI-T7: 11 call =
    # 637,2s) — kẹt lần 1 thử DPAD_DOWN cục bộ (~9s); vẫn kẹt mới gọi vision.
    _spec21 = specs["MISSION_COLD_START"]
    _dev21 = FakeDevice()
    _drv21 = Driver(_dev21, EvidenceGate(_spec21), _spec21, vision=None)
    for _i in range(4):
        _drv21.note_state(_dev21._dump, "com.kenhlive.tv/.MainActivity",
                          motion_playing=False)
    assert _drv21.stuck(), "3 quan sát không đổi phải báo kẹt"
    _a21 = _drv21.next_action(_dev21._dump, "com.kenhlive.tv/.MainActivity",
                              _fake_png(0), 0.0)
    print("kẹt lần 1 -> action:", _a21.type, _a21.param, "| rule:", _a21.rule)
    assert _a21.type == "KEY" and _a21.param == "DPAD_DOWN" \
        and _a21.rule == "stuck:local_unstick", \
        "kẹt lần 1 phải thử thoát cục bộ, không tốn vision"
    assert _drv21._vision_assist_used is False, "chưa được gọi vision"
    # Vẫn kẹt sau thoát cục bộ, không có vision -> FAIL level 2 (không treo).
    for _i in range(4):
        _drv21.note_state(_dev21._dump, "com.kenhlive.tv/.MainActivity",
                          motion_playing=False)
    assert _drv21.stuck(), "kẹt lần 2 phải vẫn báo kẹt"
    _a21b = _drv21.next_action(_dev21._dump, "com.kenhlive.tv/.MainActivity",
                               _fake_png(0), 0.0)
    print("kẹt lần 2 (không vision) -> action:", _a21b.type, "| rule:", _a21b.rule)
    assert _a21b.type == "FAIL" and _a21b.rule == "stuck:level2", \
        "kẹt lần 2 không vision phải FAIL level 2"
    # Kẹt lần 2 có vision -> vision-assist (không lặp lại local unstick).
    class _Vision21:
        def available(self):
            return True
        def remaining(self):
            return 5
        def stuck_assist(self, *a, **k):
            return ({"action": "KEY", "param": "DPAD_UP"}, None)
    _drv21v = Driver(FakeDevice(), EvidenceGate(_spec21), _spec21, vision=_Vision21())
    for _i in range(4):
        _drv21v.note_state(_drv21v.device._dump, "com.kenhlive.tv/.MainActivity",
                           motion_playing=False)
    _av1 = _drv21v.next_action(_drv21v.device._dump, "com.kenhlive.tv/.MainActivity",
                               _fake_png(0), 0.0)
    assert _av1.rule == "stuck:local_unstick", "lần 1 vẫn phải local unstick"
    for _i in range(4):
        _drv21v.note_state(_drv21v.device._dump, "com.kenhlive.tv/.MainActivity",
                           motion_playing=False)
    _av2 = _drv21v.next_action(_drv21v.device._dump, "com.kenhlive.tv/.MainActivity",
                               _fake_png(0), 0.0)
    print("kẹt lần 2 (có vision) -> action:", _av2.type, _av2.param, "| rule:", _av2.rule)
    assert _av2.rule == "stuck:vision_assist" and _av2.param == "DPAD_UP", \
        "kẹt lần 2 có vision phải dùng vision-assist"
    print("LOCAL_UNSTICK_OK")
    # --- Test N21b: vision timeout 60s + retry đúng 1 lần (CI-T8 mục 4/5) ---
    import inspect as _ins21
    from vision import VisionClient as _VC21
    for _m21 in ("confirm_target", "check_visual", "stuck_assist"):
        _t21 = _ins21.signature(getattr(_VC21, _m21)).parameters["timeout"].default
        assert _t21 == 60, "%s timeout phải là 60s (nemotron cần ~45-55s), được %s" % (_m21, _t21)
    import vision as _vis21
    import urllib.request as _urlreq21
    import urllib.error as _urlerr21
    _calls21 = {"n": 0}
    _orig_urlopen21 = _urlreq21.urlopen

    def _fake_urlopen21(*a, **k):
        _calls21["n"] += 1
        raise _urlerr21.HTTPError("https://x", 503, "Service Unavailable", {}, None)
    _urlreq21.urlopen = _fake_urlopen21
    try:
        _vis21._post("https://example.invalid/v1/chat", "Bearer x",
                     {"model": "m", "messages": []}, timeout=5)
        _raised21 = False
    except Exception:
        _raised21 = True
    finally:
        _urlreq21.urlopen = _orig_urlopen21
    print("503 -> urlopen calls:", _calls21["n"], "| raised:", _raised21)
    assert _raised21 and _calls21["n"] == 2, \
        "503 chỉ retry đúng 1 lần (tổng 2 lần gửi), được %d" % _calls21["n"]
    print("VISION_RETRY_ONCE_OK")

    # --- Test N22: fallback provider khi primary lỗi 503 (CI-T8 mục 5) ---
    # Primary lỗi -> thử đúng 1 provider dự phòng KHÁC HOST rồi mới ghi
    # UNVERIFIED. Ở CI chỉ có 1 provider (OPENAI qua integrate.api.nvidia.
    # com) nên fallback là no-op — kiểm chứng bằng stub _post ở đây.
    # Thứ tự ưu tiên: KILO > OPENAI nên test dùng KILO làm primary,
    # OPENAI làm fallback (host khác nhau).
    import vision as _vis22
    import urllib.error as _urlerr22
    _orig22 = {k: getattr(_vis22, k) for k in ("OPENAI_BASE", "OPENAI_KEY", "OPENAI_MODEL",
                                               "KILO_BASE", "KILO_KEY", "KILO_MODEL",
                                               "DEEPSEEK_BASE")}
    _vis22.OPENAI_BASE = "https://primary.example/v1"
    _vis22.OPENAI_KEY = "k1"
    _vis22.OPENAI_MODEL = "m1"
    _vis22.KILO_BASE = "https://api.kilo.ai/api/gateway/v1/chat/completions"
    _vis22.KILO_KEY = "k2"
    _vis22.KILO_MODEL = "kilo-auto/free"
    _vis22.DEEPSEEK_BASE = ""
    _orig_post22 = _vis22._post
    _calls22 = {"primary": 0, "fallback": 0}

    def _fake_post22(url, key, payload, timeout, user=None, surrogate=None,
                     surrogate_host=None):
        # _post thật trả CONTENT string (đã parse body) — stub giữ đúng mức.
        if "kilo" in (url or ""):
            _calls22["primary"] += 1
            raise _urlerr22.HTTPError(url, 503, "Service Unavailable", {}, None)
        _calls22["fallback"] += 1
        return '{"found": true}'

    _vis22._post = _fake_post22
    try:
        _vc22 = _vis22.VisionClient(budget=40)
        assert _vc22.provider == "KILO", "primary phải là KILO, được %s" % _vc22.provider
        _res22, _err22 = _vc22.check_visual(_fake_png(0), "có lỗi gì không?")
        print("fallback -> res:", _res22, "| err:", _err22,
              "| fallback_provider:", _vc22.fallback_provider, "| used:", _vc22.fallback_used)
        assert _res22 is not None and _res22.get("found") is True, \
            "fallback OPENAI phải trả kết quả khi primary 503"
        assert _vc22.fallback_used == 1 and _vc22.fallback_provider == "OPENAI", \
            "phải ghi nhận 1 lần dùng fallback OPENAI"
        assert _vc22.calls_total == 2, "primary + fallback = 2 call thật, được %d" % _vc22.calls_total
        # Cùng host thì không làm fallback cho nhau (OPENAI qua
        # integrate.api.nvidia.com vs NVIDIA_NIM): tắt mọi provider khác
        # -> _pick_fallback phải trả None.
        _vis22.KILO_KEY = ""
        _orig_pc22 = _vis22.VisionClient._provider_configured
        _vis22.VisionClient._provider_configured = staticmethod(lambda name: False)

        def _fake_post22_raise(url, key, payload, timeout, user=None, surrogate=None,
                               surrogate_host=None):
            raise _urlerr22.HTTPError(url, 503, "Service Unavailable", {}, None)
        _vis22._post = _fake_post22_raise
        try:
            _vc22b = _vis22.VisionClient(budget=40)
            assert _vc22b._pick_fallback() is None, \
                "không có provider dự phòng thì _pick_fallback phải trả None"
            _res22b, _err22b = _vc22b.check_visual(_fake_png(0), "có lỗi gì không?")
            assert _res22b is None and _err22b and "error" in _err22b, \
                "không fallback thì trả (None, error) như cũ, được res=%s err=%s" % (_res22b, _err22b)
            assert _vc22b.fallback_used == 0 and _vc22b.calls_total == 1, \
                "không fallback thì chỉ 1 call, được %d" % _vc22b.calls_total
        finally:
            _vis22.VisionClient._provider_configured = _orig_pc22
            _vis22._post = _fake_post22
    finally:
        _vis22._post = _orig_post22
        for _k22, _v22 in _orig22.items():
            setattr(_vis22, _k22, _v22)
    print("VISION_FALLBACK_OK")

    # --- Test N23: bàn phím mở = trạng thái đổi, không tính kẹt (CI-T8 mục 6) ---
    # CI-T7 STRESS FAIL oan: gõ phím mà dump không đổi (bàn phím in-app mù
    # với uiautomator) nên detector "kẹt" nổ dù highlight di chuyển a->z->▶.
    _spec23 = specs["MISSION_DPAD_CHAOS_STRESS_AND_RECOVERY"]
    _drv23 = Driver(FakeDevice(), EvidenceGate(_spec23), _spec23, vision=None)
    _kb23 = dict(FakeDevice.HOME_DUMP)
    _kb23["keyboard_open"] = True
    for _i in range(4):
        _drv23.note_state(_kb23, "com.kenhlive.tv/.MainActivity", motion_playing=False)
    print("bàn phím mở (dump) x4 -> stuck:", _drv23.stuck(),
          "| streak:", _drv23._no_change_streak)
    assert not _drv23.stuck(), "đang gõ bàn phím thì dump không đổi cũng không được tính kẹt"
    # Cùng dump nhưng bàn phím đóng -> kẹt sau 3 bước không đổi.
    _drv23b = Driver(FakeDevice(), EvidenceGate(_spec23), _spec23, vision=None)
    for _i in range(4):
        _drv23b.note_state(dict(FakeDevice.HOME_DUMP), "com.kenhlive.tv/.MainActivity",
                           motion_playing=False)
    assert _drv23b.stuck(), "bàn phím đóng + dump không đổi 3 bước thì phải kẹt"
    # Bàn phím chỉ thấy trên ẢNH (dump mù, như bàn phím in-app KenhLive).
    _drv23c = Driver(FakeDevice(), EvidenceGate(_spec23), _spec23, vision=None)
    _kb23c = dict(FakeDevice.HOME_DUMP)
    _kb23c["keyboard_open_image"] = True
    for _i in range(4):
        _drv23c.note_state(_kb23c, "com.kenhlive.tv/.MainActivity", motion_playing=False)
    assert not _drv23c.stuck(), "bàn phím thấy trên ảnh cũng phải reset streak kẹt"
    # detect_focus_trap: ctx đã có keyboard_open_image=True thì không tố.
    import detectors as _det23
    _ctx23 = {"reported": set(), "frame_hash": "h1", "frame_hash_prev": "h0",
              "keyboard_open_image": True, "last_key": "DPAD_DOWN",
              "focus_hist": [("com.kenhlive.tv/.MainActivity", "nav_home", "DPAD_DOWN")] * 3}
    _ui23 = {"focused_sig": "nav_home", "focused_bounds": "[500,500][700,600]",
             "has_dialog": False, "focusable_count": 10, "keyboard_open": False}
    _f23 = _det23.detect_focus_trap(_ui23, "com.kenhlive.tv/.MainActivity",
                                    _ctx23, "step_001.jpg", 0.0)
    print("focus_trap với bàn phím trên ảnh -> findings:", len(_f23))
    assert _f23 == [], "bàn phím mở (ảnh) thì focus đứng yên là đúng, không tố trap"
    print("KEYBOARD_STUCK_OK")

    # --- Test N24: Schedule LIVE — detector ghi nhận + mission UNVERIFIED (CI-T8 mục 7) ---
    # CI-T7: run không có hàng LIVE nào mà detector (e) im lặng — không biết
    # là đã kiểm hay chưa kiểm. Giờ: (a) detector thấy hàng LIVE thì ghi
    # ctx['schedule_live_seen']; (b) mission directed không thấy hàng LIVE
    # thì UNVERIFIED (không FAIL, không tính pass rate); (c) finish() ghi
    # UNTESTED vào unverified khi cả run không có hàng LIVE.
    import detectors as _det24
    _nodes24 = [
        {"id": "schedHeader", "text": "Hôm nay", "bounds": "[0,100][1920,200]"},
        {"id": "schedMatch", "text": "LIVE", "bounds": "[100,300][300,400]"},
        {"id": "schedMatch", "text": "18:30", "bounds": "[400,300][600,400]"},
        {"id": "schedMatch", "text": "Đội A", "bounds": "[700,300][900,400]"},
    ]
    _ui24 = {"all_visible_nodes": _nodes24}
    _ctx24 = {"reported": set()}
    _f24 = _det24.detect_schedule_live_no_score(
        _ui24, "com.kenhlive.tv/.MainActivity", _ctx24, "step_001.jpg", 0.0)
    print("hàng LIVE có giờ kickoff, không tỉ số -> findings:", len(_f24),
          "| schedule_live_seen:", _ctx24.get("schedule_live_seen"),
          "| rows:", _ctx24.get("schedule_live_rows"))
    assert _ctx24.get("schedule_live_seen") is True, \
        "detector phải ghi nhận đã thấy hàng LIVE"
    assert _ctx24.get("schedule_live_rows", 0) >= 1
    # Hàng LIVE đã có tỉ số '2 : 1' -> không tố, nhưng vẫn ghi nhận đã thấy.
    _nodes24b = [
        {"id": "schedHeader", "text": "Hôm nay", "bounds": "[0,100][1920,200]"},
        {"id": "schedMatch", "text": "LIVE", "bounds": "[100,300][300,400]"},
        {"id": "schedMatch", "text": "2 : 1", "bounds": "[400,300][600,400]"},
    ]
    _ctx24b = {"reported": set()}
    _f24b = _det24.detect_schedule_live_no_score(
        {"all_visible_nodes": _nodes24b}, "com.kenhlive.tv/.MainActivity",
        _ctx24b, "step_002.jpg", 0.0)
    assert _f24b == [], "hàng LIVE đã có tỉ số thì không tố"
    assert _ctx24b.get("schedule_live_seen") is True, \
        "hàng LIVE có tỉ số cũng phải ghi nhận đã thấy"
    # (b)+(c): chạy mission directed trên FakeDevice (không có hàng LIVE) ->
    # UNVERIFIED + finish ghi UNTESTED.
    import shutil as _sh24
    _sh24.rmtree("/tmp/qa_mock_live24", ignore_errors=True)
    _orig_dev24 = runner_mod.RealtimeDevice
    runner_mod.RealtimeDevice = FakeDevice
    try:
        _r24 = runner_mod.RealtimeRunner(out_dir="/tmp/qa_mock_live24", serial=None,
                                         vision_budget=0, no_vision=True)
        _rep24 = _r24.run([specs["MISSION_SCHEDULE_LIVE_DIRECTED"]])
    finally:
        runner_mod.RealtimeDevice = _orig_dev24
    print("directed live mission -> outcome:", _r24.mission_results[0]["outcome"],
          "| schedule_live_seen:", _rep24.get("schedule_live_seen"),
          "| unverified:", [u.get("reason") for u in _rep24.get("unverified", [])])
    assert _r24.mission_results[0]["outcome"] == "UNVERIFIED", \
        "không có hàng LIVE thì mission directed phải UNVERIFIED, không FAIL"
    assert _rep24.get("schedule_live_seen") is False
    assert any(u.get("reason") == "schedule_live_no_score"
               for u in _rep24.get("unverified", [])), \
        "finish() phải ghi UNTESTED schedule_live_no_score khi run không có hàng LIVE"
    print("SCHEDULE_LIVE_OK")

    # --- Test N25: định nghĩa per-step rõ ràng + observe percentiles (CI-T8 mục 9) ---
    # CI-T7: reviewer tính lại p95/mean từ timeline observe_s ra 20.01/8.91
    # trong khi report ghi 21.95/9.61 — khác định nghĩa đo (per_step_* là
    # wall time cả bước, observe_s chỉ là observe), không phải lỗi tính.
    import shutil as _sh25
    _sh25.rmtree("/tmp/qa_mock_tim25", ignore_errors=True)
    _orig_dev25 = runner_mod.RealtimeDevice
    runner_mod.RealtimeDevice = FakeDevice
    try:
        _r25 = runner_mod.RealtimeRunner(out_dir="/tmp/qa_mock_tim25", serial=None,
                                         vision_budget=0, no_vision=True)
        _rep25 = _r25.run([specs["MISSION_COLD_START"]])
    finally:
        runner_mod.RealtimeDevice = _orig_dev25
    _tim25 = _rep25.get("timings", {})
    print("per_step_definition:", _tim25.get("per_step_definition"))
    print("observe percentiles:", _tim25.get("observe_p50_s"),
          _tim25.get("observe_p95_s"), _tim25.get("observe_mean_s"))
    assert _tim25.get("per_step_definition"), "report phải ghi rõ định nghĩa per-step"
    # observe_* phải khớp tính lại từ timeline observe_s của chính report.
    _sess25 = json.load(open("/tmp/qa_mock_tim25/qa_session.json", encoding="utf-8"))
    _obs25 = sorted(e["observe_s"] for e in _sess25["timeline"]
                    if isinstance(e.get("observe_s"), (int, float)))
    assert _obs25, "timeline phải có observe_s"
    assert _tim25.get("observe_p50_s") == _obs25[len(_obs25) // 2], \
        "observe_p50 phải khớp tính lại từ timeline"
    assert _tim25.get("observe_mean_s") == round(sum(_obs25) / len(_obs25), 2), \
        "observe_mean phải khớp tính lại từ timeline"
    print("TIMINGS_DEFINITION_OK")

    # --- Test N26: chunk_map trim khi ghép hỏng (reviewer CI-T8) ---
    # Khi _concat_norm thất bại và chỉ giữ chunk chuẩn hóa DÀI NHẤT làm
    # tour, chunk_map cộng dồn tất cả chunk sẽ làm raw_end_s vượt độ dài
    # tour thật -> reel cắt/verify lệch âm thầm. Phải trim về đúng chunk
    # được giữ (raw 0..dur, qa theo chunk đó).
    import video_recorder as _vr26
    _rec26 = _vr26.VideoRecorder(serial=None, out_dir="/tmp/qa_mock_chunkmap26")
    _rec26._start_wall = 1000.0
    _rec26._chunk_times = [
        {"index": 1, "remote": "x", "wall_start": 1000.0, "wall_end": 1175.0},
        {"index": 2, "remote": "x", "wall_start": 1180.0, "wall_end": 1355.0}]
    _rec26._norm_chunks = ["/tmp/qa_mock_chunkmap26/norm_01.mp4",
                           "/tmp/qa_mock_chunkmap26/norm_02.mp4"]
    _rec26._norm_valid = [("c1", 170.0, 1), ("c2", 175.0, 2)]
    # Ghép thành công: map đủ 2 chunk, raw cộng dồn 0-170, 170-345.
    _rec26._keep_chunks_on_failure = False
    _cm26 = _rec26._build_chunk_map("/tmp/qa_mock_chunkmap26/final.mp4")
    print("chunk_map đủ:", _cm26)
    assert _cm26 and len(_cm26) == 2 and _cm26[-1]["raw_end_s"] == 345.0, \
        "ghép đủ thì map phải có 2 chunk cộng dồn"
    # Ghép hỏng, chỉ giữ chunk dài nhất (norm_02): map trim về 1 entry,
    # raw 0..175, qa theo chunk 2 (180..355).
    _rec26._keep_chunks_on_failure = True
    _cm26b = _rec26._build_chunk_map("/tmp/qa_mock_chunkmap26/norm_02.mp4")
    print("chunk_map trim:", _cm26b)
    assert _cm26b and len(_cm26b) == 1, "ghép hỏng thì map chỉ còn chunk được giữ"
    assert _cm26b[0]["raw_start_s"] == 0.0 and _cm26b[0]["raw_end_s"] == 175.0, \
        "map trim phải bắt đầu từ 0 và kết thúc ở độ dài chunk giữ lại"
    assert _cm26b[0]["qa_start_s"] == 180.0, "qa_start phải là của chunk được giữ"
    print("CHUNK_MAP_TRIM_OK")

    # --- CI-T9 mục 2: fake-score giữ ngữ cảnh môn khi nhãn bị cắt ---
    test_ci_t9_fake_score_context()
    # --- CI-T9 mục 3 (hàm test_ci_t9_* ở cuối file) ---
    test_ci_t9_nav_excluded_from_live_rows()
    # --- CI-T9 mục 4 ---
    test_ci_t9_gate_requires_scored_live_row(specs)
    # --- CI-T9 mục 5 ---
    test_ci_t9_video_coverage_action_time()

    # --- CI-T9 nhóm B mục (3): ExoPlayer chỉ mở trận đang đá ---
    test_ci_t9_exoplayer_live_only()
    test_ci_t9_exoplayer_no_live_unverified()
    # --- CI-T9 mục 1: focus-ring nhận vòng tròn/ellipse ---
    test_ci_t9_focus_ring_circle()
    # --- CI-T9 mục 6 + 7, nhóm B (1)(2) (hàm test_ci_t9_* ở cuối file) ---
    test_ci_t9_playback_merged_clock_token()
    test_ci_t9_playback_trial_frames()
    test_ci_t9_player_title_frame_skips_error_dialog()
    test_ci_t9_player_title_question_asks_duplicate()
    test_ci_t9_keyboard_open_type_unverified()
    # --- H3/H4 (vòng sửa sau trial 5, run 43183031119) ---
    test_h3_sports_multi_source_seek_cola()
    test_h4_iptv_hold_and_no_tab_switch_in_player()
    # --- H1 (vòng sửa sau trial 5, run 43183031119) ---
    test_h1_total_only_reading_dropped()
    # --- H4-runner (1): vision-confirm chỉ trên observation hiện tại ---
    test_h4_runner_vision_confirm_current_frame()
    # --- H4-runner (2): màn đang tải không tính là đang phát ---
    test_h4_runner_loading_screen_not_playing()
    # --- H2 (vòng sửa sau trial 5, run 43183031119) ---
    test_h2_episode_dialog_detected()
    test_h2_episode_picker_player_is_not_fail()
    # --- Test F: chạy thật 1 mission (mock runner đầy đủ) ---
    r2 = runner_mod.RealtimeRunner(out_dir="/tmp/qa_mock_out", serial=None,
                                   vision_budget=0, no_vision=True)
    report2 = r2.run([specs["MISSION_COLD_START"]])
    print("watcher samples:", r2.watcher.sample_count())
    print("steps:", r2.timings["steps"], "| observe_s total:", round(r2.timings["observe_s"], 1))
    print("missions:", [(m["name"], m["outcome"]) for m in r2.mission_results])
    print("score:", report2["score"], "| nim:", report2["nim_usage"]["requests_used"])
    ok = (r2.watcher.sample_count() > 0
          and r2.timings["steps"] >= 3
          and r2.mission_results[0]["outcome"] == "PASS"
          and report2["nim_usage"]["requests_used"] == 0)
    print("MOCK_RUNNER_OK" if ok else "MOCK_RUNNER_FAIL")
    return 0 if ok else 1


def test_ci_t9_fake_score_context():
    """CI-T9 (2): fake-score giữ ngữ cảnh môn khi nhãn giải bị cắt —
    finding #3 GIẢ ở CI-T8 (Knicks 23–33 Cavaliers thật bị tố phi lý).
    (a) Tiền tố cắt: "Hiệp hội Bóng r..." -> basketball; "National
    Basketb..." -> basketball.
    (b) Tên đội NBA: Knicks/Cavaliers/Lakers -> basketball (khớp theo từ:
    "Heather"/"sunscreen" không bắt nhầm).
    (c) Tỉ số đang tick: 13:21 -> 23:33 (2 lần quan sát, đổi giá trị)
    không tố; chuỗi CI-T8 đầy đủ (step 9: 13:21 + tiêu đề NBA, step 27/29:
    23:33 + nhãn cắt + tên đội) không tố.
    Hồi quy: bóng đá 12:3 phi lý thật vẫn tố; không ngữ cảnh + đứng yên
    qua 2 lần quan sát vẫn tố (Test H: đồng hồ 15:11->17:23->17:23).
    RANH GIỚI (ghi rõ, không giấu): KHÔNG áp miễn trừ tick blanket cho
    nhánh phi lý — nó mâu thuẫn Test H (đồng hồ tick rồi đứng yên vẫn phải
    tố; chuỗi tick không ngữ cảnh 13:21->23:33->23:33 có cấu trúc giống hệt
    đồng hồ). Case CI-T8 được sửa bằng (a)+(b) — ngữ cảnh bóng rổ có mặt
    ở observation tố — cộng gate ổn định sẵn có. Nếu muốn miễn trừ tick
    không ngữ cảnh thì phải sửa lại Test H, chưa làm ở vòng này.
    """
    import detectors as _det
    _A = "com.kenhlive.tv/.MainActivity"
    assert _det._sport_context([("league", "Hiệp hội Bóng r...")]) == "basketball", \
        "nhãn cắt 'Bóng r...' phải nhận ra bóng rổ"
    assert _det._sport_context([("title", "National Basketb...")]) == "basketball"
    assert _det._sport_context([("title", "Bóng đá Ngoại hạng Anh")]) == "football"
    assert _det._sport_context([("home", "New York Knicks"),
                                ("away", "Cleveland Cavaliers")]) == "basketball", \
        "tên đội NBA phải nhận ra bóng rổ"
    assert _det._sport_context([("home", "Los Angeles Lakers")]) == "basketball"
    assert _det._sport_context([("note", "Heather")]) is None, \
        "'Heather' chứa 'heat' nhưng không phải tên đội"
    assert _det._sport_context([("note", "sunscreen")]) is None
    # (a)+(b): nhãn cắt + tên đội, tỉ số NBA 23:33 ổn định 2 lần -> KHÔNG tố.
    _ctx = {"reported": set(), "_score_seen": {}}
    _ui = {"all_visible_texts": [("leagueLabel", "Hiệp hội Bóng r..."),
                                 ("teamHome", "New York Knicks"),
                                 ("teamAway", "Cleveland Cavaliers"),
                                 ("cardScoreHome", "23 : 33")]}
    assert _det.detect_fake_score(_ui, _A, _ctx, "s1.jpg", 1) == []
    assert _det.detect_fake_score(_ui, _A, _ctx, "s2.jpg", 2) == [], \
        "Knicks 23-33 Cavaliers (nhãn cắt + tên đội) không được tố"
    # (c): chuỗi CI-T8 đầy đủ — tick 13:21 -> 23:33 rồi đứng yên, có ngữ cảnh.
    _ctx = {"reported": set(), "_score_seen": {}}
    _o1 = {"all_visible_texts": [("heroTitle", "National Basketball Association"),
                                 ("cardScoreHome", "13 : 21")]}
    _o2 = {"all_visible_texts": [("leagueLabel", "Hiệp hội Bóng r..."),
                                 ("teamHome", "New York Knicks"),
                                 ("teamAway", "Cleveland Cavaliers"),
                                 ("cardScoreHome", "23 : 33")]}
    assert _det.detect_fake_score(_o1, _A, _ctx, "t1.jpg", 1) == []
    assert _det.detect_fake_score(_o2, _A, _ctx, "t2.jpg", 2) == []
    _f3 = _det.detect_fake_score(_o2, _A, _ctx, "t3.jpg", 3)
    print("NBA tick 13:21->23:33 findings:", len(_f3))
    assert _f3 == [], "tỉ số NBA thật đang tick không được tố (finding #3 GIẢ CI-T8)"
    # (c): tick 2 lần quan sát (đổi giá trị) -> chưa tố (gate ổn định).
    _ctx2 = {"reported": set(), "_score_seen": {}}
    _u1 = {"all_visible_texts": [("cardScoreHome", "13 : 21")]}
    _u2 = {"all_visible_texts": [("cardScoreHome", "23 : 33")]}
    assert _det.detect_fake_score(_u1, _A, _ctx2, "u1.jpg", 1) == []
    assert _det.detect_fake_score(_u2, _A, _ctx2, "u2.jpg", 2) == [], \
        "giá trị đổi (13:21->23:33) thì chưa tố"
    # Hồi quy: bóng đá phi lý thật vẫn tố.
    _ctx3 = {"reported": set(), "_score_seen": {}}
    _uf = {"all_visible_texts": [("heroSub", "Bóng đá Ngoại hạng Anh"),
                                 ("cardScoreHome", "12 : 3")]}
    assert _det.detect_fake_score(_uf, _A, _ctx3, "f1.jpg", 1) == []
    _ff = _det.detect_fake_score(_uf, _A, _ctx3, "f2.jpg", 2)
    assert len(_ff) == 1 and "12 : 3" in _ff[0]["issue"], \
        "bóng đá 12:3 phi lý thật vẫn phải bị tố"
    print("CI_T9_FAKE_SCORE_CONTEXT_OK")


def test_ci_t9_playback_merged_clock_token():
    """CI-T9 B(1)(a): box OCR gộp 'elapsed/total' phải đọc được.
    Gốc rễ: tesseract PSM 11 trả đồng hồ thành 1 box duy nhất ('0020/1353',
    '00:20/13:53') — _parse_time_token fullmatch cũ trượt nên playback_s
    null suốt 2 trial. Cặp gộp tính đủ 2 giá trị (đủ điều kiện >=2);
    token lẻ vẫn None (không đoán elapsed/total)."""
    import re as _re
    from runner import _playback_seconds_from_text as _pb_txt, \
        _times_in_text as _times
    from runner import RealtimeRunner as _RR
    assert _times("00:20 / 13:53") == [20, 833]
    assert _times("0020/1353") == [20, 833]
    assert _times("00:20/13:53") == [20, 833]
    assert _times("01/00/13:53") == [60, 833], \
        "OCR đọc nhầm ':' thành '/' ('01/00/13:53') vẫn phải đọc được"
    assert _times("00:20") == [20] and _times("24:14") == [1454]
    assert _times("Tập 01") == [] and _times("10/20") == [] \
        and _times("12/11") == []
    assert _pb_txt("phim đang phát 00:20 / 01:05:24") == 20
    assert _pb_txt("00:00 / 24:14") == 0
    assert _pb_txt("0020/1353") == 20, "quote vision gộp cũng đọc được"
    assert _pb_txt("không thấy đồng hồ") is None
    assert _pb_txt("chỉ có 24:14 lẻ") is None
    # fullmatch cũ trượt trên chính token gộp, parser mới đọc được.
    assert _re.fullmatch(r"(\d{1,2}):(\d{2})(?::(\d{2}))?", "0020/1353") is None
    assert _RR._parse_time_token("0020/1353") == 20
    assert _RR._parse_time_token("00:20") == 20
    assert _RR._parse_time_token("Tập 01") is None
    # _extract: 1 box gộp -> 20; 1 box lẻ -> None; 2 box lẻ -> min.
    from detectors import BOTTOM_BAR_BAND as _BBB
    _r = _RR(out_dir="/tmp/qa_mock_pb_t9", serial=None,
             vision_budget=0, no_vision=True)
    _r.detector_ctx["_ocr_cache"] = {
        ("step_001.jpg", _BBB): [{"text": "0020/1353"}]}
    assert _r._extract_playback_s({"all_visible_texts": []}, "step_001.jpg") == 20
    _r.detector_ctx["_ocr_cache"] = {
        ("step_001.jpg", _BBB): [{"text": "24:14"}]}
    assert _r._extract_playback_s({"all_visible_texts": []}, "step_001.jpg") is None
    _r.detector_ctx["_ocr_cache"] = {
        ("step_001.jpg", _BBB): [{"text": "00:20"}, {"text": "13:53"}]}
    assert _r._extract_playback_s({"all_visible_texts": []}, "step_001.jpg") == 20
    print("CI_T9_PLAYBACK_MERGED_TOKEN_OK")


def test_ci_t9_playback_trial_frames():
    """CI-T9 B(1): replay trên khung THẬT T3/T4 — trước: null hết; sau: đọc
    đúng giá trị mắt đọc. Khung OSD ẩn (không đồng hồ) vẫn None, không bịa.
    Đồng hồ tăng đơn điệu qua các khung -> gate increasing."""
    import os as _os
    from gate import EvidenceGate
    from missions import get_missions
    import runner as _rm
    _base = _os.path.expanduser("~/workspace/kenhlive-plan")
    _frames = [
        ("qa-run-43168594823", "step_056_vod_play.jpg", 20),   # 00:20
        ("qa-run-43168594823", "step_061_vod_play.jpg", 60),   # 01:00
        ("qa-run-43164647966", "step_061_vod_play.jpg", 79),   # 01:19
        ("qa-run-43164647966", "step_064_vod_play.jpg", 119),  # 01:59
    ]
    _vals = []
    for _run, _shot, _want in _frames:
        _p = _os.path.join(_base, _run, "artifact", "shots", _shot)
        _png = open(_p, "rb").read()
        _r = _rm.RealtimeRunner(out_dir="/tmp/qa_mock_pb_t9f", serial=None,
                                vision_budget=0, no_vision=True)
        _r.detector_ctx["_ocr_cache"] = {}
        _v = _r._extract_playback_s({"all_visible_texts": []}, _shot, _png)
        print("playback khung thật %s/%s -> %s (mắt đọc %s)" % (_run[-5:], _shot, _v, _want))
        assert _v is not None and abs(_v - _want) <= 2, \
            "khung %s: đọc được %s, mắt đọc %s" % (_shot, _v, _want)
        _vals.append(_v)
    assert _vals == sorted(_vals) and len(set(_vals)) == len(_vals), \
        "đồng hồ phải tăng đơn điệu qua các khung: %s" % _vals
    # Khung OSD ẩn (066/071, video fullscreen, không đồng hồ) -> None.
    for _run, _shot in (("qa-run-43168594823", "step_066_webplaye.jpg"),
                        ("qa-run-43168594823", "step_071_webplaye.jpg")):
        _p = _os.path.join(_base, _run, "artifact", "shots", _shot)
        _r = _rm.RealtimeRunner(out_dir="/tmp/qa_mock_pb_t9f", serial=None,
                                vision_budget=0, no_vision=True)
        _r.detector_ctx["_ocr_cache"] = {}
        assert _r._extract_playback_s(
            {"all_visible_texts": []}, _shot, open(_p, "rb").read()) is None, \
            "khung OSD ẩn %s không có đồng hồ thì phải None, không bịa" % _shot
    _specs = {s.name: s for s in get_missions()}
    _g = EvidenceGate(_specs["MISSION_VOD_PLAYER_SEEK_AND_RESUME"])
    for _i, _v in enumerate(_vals):
        _g.observe_playback(_v, float(_i * 30))
    assert _g.playback_status() == "increasing", \
        "đọc 20->60->79->119 thì gate phải increasing, được %s" % _g.playback_status()
    assert _g.playback_monotonic()[0] is True
    print("CI_T9_PLAYBACK_TRIAL_FRAMES_OK", _vals)


def test_ci_t9_player_title_frame_skips_error_dialog():
    """CI-T9 B(2): run kết thúc bằng dialog lỗi video_error vẫn chọn được
    khung đang phát. Rank: phát=2, không-lỗi-không-rõ=1, dialog lỗi=0;
    cùng rank thì frame CUỐI thắng (giữ luật CI-T6). Chỉ toàn khung lỗi
    thì fallback khung lỗi (vẫn có cái để soi)."""
    from missions import get_missions
    import runner as _rm
    _specs = {s.name: s for s in get_missions()}
    _spec = _specs["MISSION_VOD_PLAYER_SEEK_AND_RESUME"]
    _WP = "com.kenhlive.tv/.phim.WebPlayerActivity"

    def _obs(frame, t, motion, texts):
        return {"png": _fake_png(abs(hash(frame)) % 5 + 1), "t_offset": t,
                "activity": _WP, "motion": motion,
                "ui_state": {"all_visible_texts": [("x", tx) for tx in texts]}}

    assert _rm.RealtimeRunner._player_title_rank(
        _obs("e", 0, False, ["Không phát được video", "Error code: video_error"])) == 0
    assert _rm.RealtimeRunner._player_title_rank(
        _obs("p", 0, True, ["Tuyệt Thế Chiến Hồn"])) == 2
    assert _rm.RealtimeRunner._player_title_rank(
        _obs("u", 0, False, ["Tuyệt Thế Chiến Hồn"])) == 1
    _r = _rm.RealtimeRunner(out_dir="/tmp/qa_mock_title_t9", serial=None,
                            vision_budget=0, no_vision=True)
    _r._note_vision_frames(_spec, _obs("step_056_vod_play.jpg", 100.0, True,
                                       ["Tuyệt Thế Chiến Hồn"]), "step_056_vod_play.jpg")
    assert _r._player_title_frame["frame"] == "step_056_vod_play.jpg"
    _r._note_vision_frames(_spec, _obs("step_061_vod_play.jpg", 200.0, False,
                                       ["Tuyệt Thế Chiến Hồn"]), "step_061_vod_play.jpg")
    assert _r._player_title_frame["frame"] == "step_056_vod_play.jpg", \
        "khung không-rõ (rank 1) không được thay khung đang phát (rank 2)"
    _r._note_vision_frames(_spec, _obs("step_066_webplaye.jpg", 300.0, True,
                                       ["Tuyệt Thế Chiến Hồn"]), "step_066_webplaye.jpg")
    assert _r._player_title_frame["frame"] == "step_066_webplaye.jpg", \
        "cùng rank phát thì frame CUỐI thắng"
    _r._note_vision_frames(_spec, _obs("step_075_webplaye.jpg", 400.0, False,
                                       ["Không phát được video",
                                        "Error code: video_error"]), "step_075_webplaye.jpg")
    assert _r._player_title_frame["frame"] == "step_066_webplaye.jpg", \
        "khung dialog lỗi cuối run (như T4 step_075) không được thay khung đang phát"
    # Chỉ toàn khung lỗi -> fallback khung lỗi cuối (vẫn có cái để soi).
    _r2 = _rm.RealtimeRunner(out_dir="/tmp/qa_mock_title_t9b", serial=None,
                             vision_budget=0, no_vision=True)
    _r2._note_vision_frames(_spec, _obs("step_075_webplaye.jpg", 100.0, False,
                                        ["Không phát được video",
                                         "Error code: video_error"]), "step_075_webplaye.jpg")
    _r2._note_vision_frames(_spec, _obs("step_076_webplaye.jpg", 200.0, False,
                                        ["Không phát được video",
                                         "Error code: video_error"]), "step_076_webplaye.jpg")
    assert _r2._player_title_frame["frame"] == "step_076_webplaye.jpg", \
        "không có khung phát nào thì fallback khung lỗi cuối"
    print("CI_T9_TITLE_FRAME_SKIPS_ERROR_OK")


def test_ci_t9_player_title_question_asks_duplicate():
    """CI-T9 mục 6: câu hỏi player_title phải hỏi TRÙNG tiêu đề (2 dòng khác
    nhau cùng tên phim/tập, kể cả khi nằm riêng không đè nhau), không chỉ
    hỏi chồng chữ. Giữ 2 cụm '2 DÒNG TIÊU ĐỀ' + 'CHỒNG LÊN NHAU' để test
    N2 vẫn đúng (câu hỏi bao cả 2 dạng)."""
    import runner as _rm

    class _FV:
        def __init__(self):
            self.calls = []
        def available(self):
            return True
        def remaining(self):
            return 10
        def check_visual(self, image_bytes, question, timeout=30, crop=None, max_side=None):
            self.calls.append((crop, question))
            return {"found": True, "severity": "HIGH",
                    "detail": "2 dòng tiêu đề trùng nhau", "quote": "Dòng 1 | Dòng 2"}, None

    _r = _rm.RealtimeRunner(out_dir="/tmp/qa_mock_title_q_t9", serial=None,
                            vision_budget=40, no_vision=False)
    _r._player_title_frame = {"png": _fake_png(1), "frame": "step_061_vod_play.jpg",
                              "t": 300.0, "activity": "com.kenhlive.tv/.phim.WebPlayerActivity"}
    _fv = _FV()
    _r.vision = _fv
    _r._vision_overlap_checks()
    _q = [q for c, q in _fv.calls if c == (0, 0, 1920, 280)][0]
    print("title question (T9):", _q[:160])
    assert "2 DÒNG TIÊU ĐỀ" in _q and "CHỒNG LÊN NHAU" in _q, \
        "câu hỏi vẫn phải nhắc 2 dòng tiêu đề chồng nhau (test N2)"
    assert "TRÙNG" in _q, "câu hỏi phải hỏi trùng lặp tiêu đề, không chỉ chồng chữ"
    assert "nằm riêng" in _q or "riêng" in _q, \
        "câu hỏi phải bao cả dạng 2 dòng nằm riêng không đè nhau"
    assert "vị trí" in _q, "câu hỏi phải ép đọc vị trí từng dòng"
    _find = [f for f in _r.findings if f["issue"] == "Tiêu đề player đè đôi"]
    assert len(_find) == 1 and _find[0]["evidence"]["frame"] == "step_061_vod_play.jpg"
    print("CI_T9_TITLE_QUESTION_DUPLICATE_OK")


_SEARCH_DUMP_T9 = {
    "focused_sig": "searchInput#[128,136][1688,228]",
    "focused_text": "Tìm trận đấu, kênh, phim, BLV…",
    "focused_bounds": "[128,136][1688,228]",
    "focusable_count": 8,
    "all_visible_texts": [("searchInput", "Tìm trận đấu, kênh, phim, BLV…"),
                          ("nav_search", "Tìm kiếm"),
                          ("row1", "INTERF"), ("row2", "WNZT")],
    "has_dialog": False,
    "dialog_ids": [],
    "selected_ids": ["nav_search"],
    "ui_summary": "[FOCUSED] searchInput ('Tìm trận đấu, kênh, phim, BLV…')",
    "osd_visible": False,
}


def test_ci_t9_keyboard_open_type_unverified():
    """CI-T9 mục 7: (a) driver: focus ở ô tìm kiếm -> OK mở bàn phím (tối đa
    2 lần); bàn phím đã mở -> gõ 'uefa' qua adb input; (b) runner: mission
    SEARCH mà bàn phím không mở lần nào thì PASS bị lật UNVERIFIED (không
    PASS lặng như CI-T8); (c) bàn phím mở thật sau OK thì mission PASS và
    đã gõ từ khóa."""
    from driver import Driver
    from gate import EvidenceGate
    from missions import get_missions
    import runner as _rm
    _specs = {s.name: s for s in get_missions()}
    # Mock tự gắn cờ needs_keyboard trên bản sao của spec SEARCH: dây
    # production (missions.py) do worker ExoPlayer commit riêng (file đó
    # đang có thay đổi song song, không commit ở đây); test này kiểm
    # driver/runner độc lập với file đó.
    import copy as _copy
    _spec = _copy.copy(_specs["MISSION_SEARCH_AND_SETTINGS_FEEDBACK"])
    _spec.needs_keyboard = True
    # (a) driver, unit.
    _dev = FakeDevice()
    _dev._tab = 3
    _dev._dump = dict(_SEARCH_DUMP_T9)
    _drv = Driver(_dev, EvidenceGate(_spec), _spec)
    _a1 = _drv.next_action(_dev._dump, "com.kenhlive.tv/.MainActivity", None, 0.0)
    print("keyboard open action:", _a1.type, _a1.param, _a1.rule)
    assert _a1.type == "KEY" and _a1.param == "OK" and _a1.rule == "keyboard:open", \
        "focus ở ô tìm kiếm thì driver phải bấm OK mở bàn phím, được %s %s [%s]" % (
            _a1.type, _a1.param, _a1.rule)
    _dump_kb = dict(_SEARCH_DUMP_T9)
    _dump_kb["keyboard_open"] = True
    _dump_kb["keyboard_open_image"] = True
    _a2 = _drv.next_action(_dump_kb, "com.kenhlive.tv/.MainActivity", None, 0.0)
    print("keyboard type action:", _a2.type, _a2.param, _a2.rule)
    assert _a2.type == "TEXT" and _a2.param == "uefa" and _a2.rule == "keyboard:type", \
        "bàn phím đã mở thì driver phải gõ từ khóa qua TEXT"
    _a3 = _drv.next_action(_dump_kb, "com.kenhlive.tv/.MainActivity", None, 0.0)
    assert _a3.rule != "keyboard:type", "chỉ gõ từ khóa 1 lần/mission"

    # (b) runner: bàn phím không mở lần nào -> UNVERIFIED (dù đủ tín hiệu PASS).
    class _NoKbDevice(FakeDevice):
        def __init__(self, *a, **k):
            super().__init__(*a, **k)
            self._dump = dict(_SEARCH_DUMP_T9)
            self._tab = 3

    _orig_dev = _rm.RealtimeDevice
    _rm.RealtimeDevice = _NoKbDevice
    try:
        _r = _rm.RealtimeRunner(out_dir="/tmp/qa_mock_kb_t9", serial=None,
                                vision_budget=0, no_vision=True)
        _rep = _r.run([_spec])
    finally:
        _rm.RealtimeDevice = _orig_dev
    _res = _r.mission_results[0]
    print("SEARCH không mở bàn phím ->", _res["outcome"], "|", _res["reason"][:120],
          "| keys:", _r.device.keys)
    assert "OK" in _r.device.keys, "driver phải thử bấm OK mở bàn phím (keys: %s)" % _r.device.keys
    assert _res["outcome"] == "UNVERIFIED", \
        "bàn phím không mở lần nào thì mission SEARCH phải UNVERIFIED, không PASS lặng (được %s)" % _res["outcome"]
    assert "Bàn phím" in _res["reason"]
    assert _rep.get("keyboard_seen") is False

    # (c) runner: OK mở được bàn phím thật -> PASS + đã gõ từ khóa.
    class _KbDevice(FakeDevice):
        def __init__(self, *a, **k):
            super().__init__(*a, **k)
            self._dump = dict(_SEARCH_DUMP_T9)
            self._tab = 3
            self.typed = []
        def send_key(self, key_name):
            super().send_key(key_name)
            if key_name == "OK" and "searchInput" in self._dump.get("focused_sig", ""):
                _d = dict(self._dump)
                _d["all_visible_texts"] = list(_d["all_visible_texts"]) + [
                    ("kb%d" % i, ch) for i, ch in enumerate("qwertyui")]
                self._dump = _d
        def input_text(self, text):
            self.typed.append(text)
            self._note("TEXT(%s)" % text)

    _rm.RealtimeDevice = _KbDevice
    try:
        _r2 = _rm.RealtimeRunner(out_dir="/tmp/qa_mock_kb_t9b", serial=None,
                                 vision_budget=0, no_vision=True)
        _rep2 = _r2.run([_spec])
    finally:
        _rm.RealtimeDevice = _orig_dev
    _res2 = _r2.mission_results[0]
    print("SEARCH mở bàn phím ->", _res2["outcome"], "| typed:", _r2.device.typed)
    assert _res2["outcome"] == "PASS", \
        "bàn phím mở thật + đủ tín hiệu thì mission SEARCH phải PASS (được %s: %s)" % (
            _res2["outcome"], _res2["reason"][:120])
    assert _r2.device.typed == ["uefa"], \
        "phải gõ đúng 1 lần từ khóa 'uefa' khi bàn phím mở (được %s)" % _r2.device.typed
    assert _rep2.get("keyboard_seen") is True
    print("CI_T9_KEYBOARD_OPEN_TYPE_UNVERIFIED_OK")


def test_ci_t9_video_coverage_action_time():
    """CI-T9 mục 5: độ phủ video = giây video đã ghi / thời gian hành động
    (t bước cuối cùng), không theo duration_sec (gồm ~325s finalize sau
    bước cuối — headline CI-T8 chỉ 78,5% dù phủ thật ~99%). Số thô cũ
    (theo duration_sec) vẫn giữ để đối chiếu.
    Số kiểu CI-T8: ghi 99s, bước cuối t=100, duration 130 -> coverage
    0.99, thô 99/130 = 0.7615. Không có bước/video -> coverage None."""
    import shutil as _sh
    _sh.rmtree("/tmp/qa_mock_cov5", ignore_errors=True)
    _r = runner_mod.RealtimeRunner(out_dir="/tmp/qa_mock_cov5", serial=None,
                                   vision_budget=0, no_vision=True)
    _r.start_time = time.time()
    _r.timeline = [{"time_offset_sec": 10.0, "observe_s": 1.0},
                   {"time_offset_sec": 55.5, "observe_s": 1.0},
                   {"time_offset_sec": 100.0, "observe_s": 1.0}]
    _rep = _r.finish(130, {"recorded_seconds": 99.0})
    _vc = _rep.get("video_coverage", {})
    print("coverage:", _vc)
    assert _vc.get("coverage") == 0.99, \
        "coverage phải = 99/100 thời gian hành động, được %s" % _vc.get("coverage")
    assert _vc.get("coverage_vs_duration_sec") == round(99.0 / 130, 4), \
        "số thô cũ (theo duration_sec) phải giữ để đối chiếu"
    assert _vc.get("action_seconds") == 100.0, "action_seconds = t bước cuối"
    assert _vc.get("recorded_seconds") == 99.0
    assert _vc.get("duration_sec") == 130
    assert "99.0%" in _vc.get("text", ""), "text headline phải ghi 99.0%"
    # Không có bước nào / không có video -> coverage None, không bịa số.
    _sh.rmtree("/tmp/qa_mock_cov5b", ignore_errors=True)
    _r2 = runner_mod.RealtimeRunner(out_dir="/tmp/qa_mock_cov5b", serial=None,
                                    vision_budget=0, no_vision=True)
    _r2.start_time = time.time()
    _rep2 = _r2.finish(50, None)
    assert _rep2.get("video_coverage", {}).get("coverage") is None, \
        "không có bước/video thì coverage phải None"
    assert _rep2.get("video_coverage", {}).get("action_seconds") == 0.0
    print("CI_T9_COVERAGE_ACTION_OK")


def test_ci_t9_gate_requires_scored_live_row(specs):
    """CI-T9 mục 4: mission SCHEDULE_LIVE_DIRECTED chỉ giữ PASS khi đã thấy
    hàng LIVE CÓ tỉ số (cờ schedule_live_with_score).
    - Detector: hàng LIVE có '2 : 1' -> with_score đặt; hàng LIVE chỉ có
      giờ kickoff -> live_seen đặt, with_score KHÔNG đặt.
    - Runner: (a) dump có hàng LIVE có tỉ số -> mission PASS giữ + report
      schedule_live_with_score True; (b) dump chỉ có hàng LIVE không tỉ số
      -> mission UNVERIFIED (không PASS mềm) + with_score False.
      Hành vi UNVERIFIED khi run KHÔNG có hàng LIVE nào giữ nguyên (N24)."""
    import detectors as _det
    import shutil as _sh
    _nodes_scored = [
        {"id": "schedHeader", "text": "Hôm nay", "bounds": "[0,150][1920,260]"},
        {"id": "nav_schedule", "text": "TRỰC TIẾP", "bounds": "[362,0][563,112]"},
        {"id": "schedMatch", "text": "Vietnam vs Thailand", "bounds": "[100,300][900,460]"},
        {"id": "cardBadge", "text": "LIVE", "bounds": "[820,320][880,350]"},
        {"id": "schedScore", "text": "2 : 1", "bounds": "[820,370][880,400]"},
    ]
    _nodes_noscore = [dict(n) for n in _nodes_scored]
    _nodes_noscore[-1] = {"id": "schedScore", "text": "18:30", "bounds": "[820,370][880,400]"}
    _ctx_s = {"reported": set()}
    _det.detect_schedule_live_no_score(
        {"all_visible_nodes": _nodes_scored}, "com.kenhlive.tv/.MainActivity",
        _ctx_s, "step_001.jpg", 0.0)
    print("LIVE + tỉ số -> live_seen:", _ctx_s.get("schedule_live_seen"),
          "| with_score:", _ctx_s.get("schedule_live_with_score"))
    assert _ctx_s.get("schedule_live_with_score") is True, \
        "hàng LIVE có tỉ số phải đặt cờ schedule_live_with_score"
    assert _ctx_s.get("schedule_live_with_score_rows", 0) == 1
    _ctx_n = {"reported": set()}
    _det.detect_schedule_live_no_score(
        {"all_visible_nodes": _nodes_noscore}, "com.kenhlive.tv/.MainActivity",
        _ctx_n, "step_001.jpg", 0.0)
    print("LIVE + giờ kickoff -> live_seen:", _ctx_n.get("schedule_live_seen"),
          "| with_score:", _ctx_n.get("schedule_live_with_score"))
    assert _ctx_n.get("schedule_live_seen") is True, \
        "hàng LIVE không tỉ số vẫn phải đặt cờ live_seen"
    assert _ctx_n.get("schedule_live_with_score") is not True, \
        "hàng LIVE không tỉ số không được đặt cờ with_score"

    def _sched_device(nodes):
        class _SchedDevice(FakeDevice):
            def dump_ui_state(self):
                _d = dict(FakeDevice.HOME_DUMP)
                _d["all_visible_nodes"] = nodes
                _d["all_visible_texts"] = [(n["id"], n["text"]) for n in nodes]
                return _d
        return _SchedDevice

    def _run_directed(nodes, out_dir):
        _sh.rmtree(out_dir, ignore_errors=True)
        _orig = runner_mod.RealtimeDevice
        runner_mod.RealtimeDevice = _sched_device(nodes)
        try:
            _r = runner_mod.RealtimeRunner(out_dir=out_dir, serial=None,
                                           vision_budget=0, no_vision=True)
            _rep = _r.run([specs["MISSION_SCHEDULE_LIVE_DIRECTED"]])
        finally:
            runner_mod.RealtimeDevice = _orig
        return _r, _rep

    # (a) hàng LIVE có tỉ số -> PASS giữ.
    _r_a, _rep_a = _run_directed(_nodes_scored, "/tmp/qa_mock_live_scored")
    print("directed + hàng LIVE có tỉ số -> outcome:",
          _r_a.mission_results[0]["outcome"],
          "| with_score:", _rep_a.get("schedule_live_with_score"))
    assert _r_a.mission_results[0]["outcome"] == "PASS", \
        "đã thấy hàng LIVE có tỉ số thì mission directed phải giữ PASS"
    assert _rep_a.get("schedule_live_with_score") is True
    assert _rep_a.get("schedule_live_seen") is True
    # (b) hàng LIVE không tỉ số -> UNVERIFIED, không PASS mềm.
    _r_b, _rep_b = _run_directed(_nodes_noscore, "/tmp/qa_mock_live_noscore")
    print("directed + hàng LIVE không tỉ số -> outcome:",
          _r_b.mission_results[0]["outcome"],
          "| live_seen:", _rep_b.get("schedule_live_seen"),
          "| with_score:", _rep_b.get("schedule_live_with_score"))
    assert _r_b.mission_results[0]["outcome"] == "UNVERIFIED", \
        "chỉ thấy hàng LIVE không tỉ số thì mission không được PASS mềm"
    assert _rep_b.get("schedule_live_seen") is True
    assert _rep_b.get("schedule_live_with_score") is False
    print("CI_T9_GATE_SCORED_OK")


def test_ci_t9_nav_excluded_from_live_rows():
    """CI-T9 mục 3: hàng nav 'TRỰC TIẾP' (band y 0–112) không được đặt cờ
    schedule_live_seen, không được đếm là hàng trận. Bằng chứng CI-T8:
    cờ bị đặt oan bởi nav nên mission SCHEDULE_LIVE_DIRECTED PASS mềm."""
    import detectors as _det
    # Chỉ có hàng nav + ngữ cảnh lịch (id 'sched'): không cờ nào được đặt.
    _nodes_nav = [
        {"id": "schedHeader", "text": "Hôm nay", "bounds": "[0,150][1920,260]"},
        {"id": "nav_schedule", "text": "TRỰC TIẾP", "bounds": "[362,0][563,112]"},
    ]
    _ctx = {"reported": set()}
    assert _det.detect_schedule_live_no_score(
        {"all_visible_nodes": _nodes_nav}, "com.kenhlive.tv/.MainActivity",
        _ctx, "step_001.jpg", 0.0) == [], "chỉ có nav thì detector không tố"
    print("chỉ nav TRỰC TIẾP -> live_seen:", _ctx.get("schedule_live_seen"),
          "| rows:", _ctx.get("schedule_live_rows"))
    assert _ctx.get("schedule_live_seen") is not True, \
        "hàng nav TRỰC TIẾP không được đặt cờ schedule_live_seen"
    assert _ctx.get("schedule_live_rows", 0) == 0, \
        "hàng nav không được đếm là hàng trận"
    # Nav + 1 hàng trận LIVE thật (giờ kickoff, y 300–400): chỉ hàng trận
    # được đếm (rows == 1), nav vẫn không tính.
    _nodes_mix = _nodes_nav + [
        {"id": "schedMatch", "text": "LIVE", "bounds": "[100,300][300,400]"},
        {"id": "schedMatch", "text": "18:30", "bounds": "[400,300][600,400]"},
        {"id": "schedMatch", "text": "Đội A", "bounds": "[700,300][900,400]"},
    ]
    _ctx2 = {"reported": set()}
    _det.detect_schedule_live_no_score(
        {"all_visible_nodes": _nodes_mix}, "com.kenhlive.tv/.MainActivity",
        _ctx2, "step_001.jpg", 0.0)
    print("nav + 1 hàng LIVE thật -> live_seen:", _ctx2.get("schedule_live_seen"),
          "| rows:", _ctx2.get("schedule_live_rows"))
    assert _ctx2.get("schedule_live_seen") is True, \
        "hàng trận LIVE thật vẫn phải đặt cờ"
    assert _ctx2.get("schedule_live_rows", 0) == 1, \
        "chỉ đếm 1 hàng trận thật, nav không được đếm thêm"
    print("CI_T9_NAV_EXCLUDED_OK")


def test_ci_t9_exoplayer_live_only():
    """CI-T9 nhóm B mục (3): ExoPlayer chỉ mở trận ĐANG ĐÁ.
    Thử 3 (run 43164647966): driver bấm OK mù trên focus không text ''
    (step_016/018, sau khi player thoát) rồi mở PlayerActivity cho KUW–SYR
    đá NGÀY MAI 21:00 ('SẮP ĐÁ') — trận chưa đá thì không có luồng, mission
    FAIL oan. Giờ: (a) dump có cả trận tương lai + trận LIVE -> đi tới thẻ
    LIVE (không mở trận tương lai); (b) focus đã đứng trên thẻ LIVE -> mở
    bằng OK; (c) hồi quy Thử 3 — focus '' + badge SẮP ĐÁ không gắn được
    + không có thẻ LIVE -> KHÔNG bấm OK mù, quét xuống tìm LIVE, quét hết
    6 lượt -> FAIL no_live_target; (d) không có badge nhưng giờ kickoff
    hôm nay đã qua -> coi là đang đá (mở OK); trận ngày mai / trận hôm nay
    chưa tới giờ -> không mở; (e) nav 'TRỰC TIẾP' không được tính là thẻ
    LIVE; (f) mission mở player khác (IPTV_EPG, mở kênh) không bị chặn."""
    from datetime import datetime, timezone, timedelta
    from driver import Driver
    from gate import EvidenceGate
    from missions import get_missions
    _specs = {s.name: s for s in get_missions()}
    _exo = _specs["MISSION_PLAYER_STREAMING_AND_CONTROLS"]
    assert _exo.requires_live_row is True, \
        "spec ExoPlayer phải có requires_live_row để runner đổi FAIL thành UNVERIFIED khi run không có trận đang đá"

    def _drv(spec=None, **kw):
        _dev = FakeDevice()
        _sp = spec or _exo
        _dev._tab = _sp.tab if _sp.tab is not None else 0
        return Driver(_dev, EvidenceGate(_sp), _sp, **kw)

    def _act(drv, ui):
        return drv.next_action(ui, "com.kenhlive.tv/.MainActivity", None, 0.0)

    # (a) focus ở nav, dưới có cả thẻ SẮP ĐÁ và thẻ LIVE -> đi tới thẻ LIVE
    # (không mở trận tương lai); nhãn nav 'TRỰC TIẾP' không được đuổi theo.
    _ui_mix = {
        "focused_sig": "nav_home#[362,0][563,112]", "focused_text": "Trang chủ",
        "focused_bounds": "[362,0][563,112]",
        "all_visible_texts": [("nav_home", "Trang chủ"), ("nav_live", "TRỰC TIẾP"),
                              ("cardRoot", "Kuwait vs Syria"), ("cardBadge", "SẮP ĐÁ"),
                              ("cardRoot2", "South East Melbourne"), ("cardBadge2", "LIVE")],
        "all_visible_nodes": [
            {"id": "nav_home", "text": "Trang chủ", "bounds": "[362,0][563,112]"},
            {"id": "nav_live", "text": "TRỰC TIẾP", "bounds": "[700,0][900,112]"},
            {"id": "cardRoot", "text": "Kuwait vs Syria", "bounds": "[100,200][500,400]"},
            {"id": "cardBadge", "text": "SẮP ĐÁ", "bounds": "[120,210][200,240]"},
            {"id": "cardRoot2", "text": "South East Melbourne", "bounds": "[100,500][500,800]"},
            {"id": "cardBadge2", "text": "LIVE", "bounds": "[120,510][200,540]"}],
        "has_dialog": False, "dialog_ids": []}
    _a = _act(_drv(), _ui_mix)
    print("dump có SẮP ĐÁ + LIVE, focus nav ->", _a.type, _a.param, "| rule:", _a.rule)
    assert _a.rule == "goto_live_card" and _a.param == "DPAD_DOWN", \
        "dump có cả trận tương lai và trận LIVE thì phải đi tới thẻ LIVE, không mở trận tương lai"
    # (b) đã đứng trên thẻ LIVE -> mở bằng OK.
    _ui_on_live = dict(_ui_mix,
                       focused_sig="cardRoot2#[100,500][500,800]",
                       focused_text="South East Melbourne",
                       focused_bounds="[100,500][500,800]")
    _a = _act(_drv(), _ui_on_live)
    print("đã đứng trên thẻ LIVE ->", _a.type, _a.param, "| rule:", _a.rule)
    assert _a.type == "KEY" and _a.param == "OK" and _a.rule == "open_player", \
        "đã đứng trên thẻ LIVE thì bấm OK mở player"
    # (c) hồi quy Thử 3: focus không text, badge SẮP ĐÁ có trong dump nhưng
    # không gắn được với focus (bounds xa), không có thẻ LIVE nào.
    _ui_t3 = {
        "focused_sig": "cardRoot#[180,408][666,664]", "focused_text": "",
        "focused_bounds": "[180,408][666,664]",
        "all_visible_texts": [("nav_home", "Trang chủ"), ("cardRoot", "Kuwait vs Syria"),
                              ("cardBadge", "SẮP ĐÁ"), ("cardTime", "21:00")],
        "all_visible_nodes": [
            {"id": "nav_home", "text": "Trang chủ", "bounds": "[362,0][563,112]"},
            {"id": "cardRoot", "text": "Kuwait vs Syria", "bounds": "[180,408][666,664]"},
            {"id": "cardBadge", "text": "SẮP ĐÁ", "bounds": "[200,900][300,930]"},
            {"id": "cardTime", "text": "21:00", "bounds": "[200,940][300,970]"}],
        "has_dialog": False, "dialog_ids": []}
    _drv_t3 = _drv()
    assert _drv_t3._focused_card_status(_ui_t3) is None, \
        "badge SẮP ĐÁ không gắn được với focus thì trạng thái là None như Thử 3"
    assert _drv_t3._is_confirmed_live_target(_ui_t3) is False
    for _i in range(6):
        _a = _act(_drv_t3, _ui_t3)
        assert _a.rule == "scan_live_card", \
            "focus chưa xác nhận + không có thẻ LIVE thì phải quét tìm LIVE, không được bấm OK mù (lần %d: %s)" % (_i + 1, _a.rule)
    _a = _act(_drv_t3, _ui_t3)
    print("quét hết 6 lượt không thấy LIVE ->", _a.type, "| rule:", _a.rule)
    assert _a.type == "FAIL" and _a.rule == "no_live_target", \
        "quét hết lượt mà không thấy thẻ LIVE thì FAIL no_live_target (runner đổi thành UNVERIFIED)"
    # (d) giờ kickoff: 'Hôm nay 13:00' lúc 14:00 (GMT+7), không badge -> mở;
    # 'Ngày mai 10:00' lúc 14:00 -> không mở; 'Hôm nay 21:00' lúc 14:00 -> không mở.
    _gmt7 = timezone(timedelta(hours=7))
    _now14 = datetime(2026, 11, 12, 14, 0, tzinfo=_gmt7)

    def _ui_kickoff(date_txt, time_txt):
        return {
            "focused_sig": "cardRoot#[100,400][500,700]", "focused_text": "Đội A vs Đội B",
            "focused_bounds": "[100,400][500,700]",
            "all_visible_texts": [("nav_home", "Trang chủ"), ("cardRoot", "Đội A vs Đội B"),
                                  ("cardDate", date_txt), ("cardTime", time_txt)],
            "all_visible_nodes": [
                {"id": "nav_home", "text": "Trang chủ", "bounds": "[362,0][563,112]"},
                {"id": "cardRoot", "text": "Đội A vs Đội B", "bounds": "[100,400][500,700]"},
                {"id": "cardDate", "text": date_txt, "bounds": "[120,410][220,440]"},
                {"id": "cardTime", "text": time_txt, "bounds": "[120,450][220,480]"}],
            "has_dialog": False, "dialog_ids": []}
    _a = _act(_drv(now_fn=lambda: _now14), _ui_kickoff("Hôm nay", "13:00"))
    print("'Hôm nay 13:00' lúc 14:00 ->", _a.type, _a.param, "| rule:", _a.rule)
    assert _a.rule == "open_player", "giờ kickoff hôm nay đã qua thì trận đã bắt đầu, được mở"
    _a = _act(_drv(now_fn=lambda: _now14), _ui_kickoff("Ngày mai", "10:00"))
    print("'Ngày mai 10:00' lúc 14:00 ->", _a.type, _a.param, "| rule:", _a.rule)
    assert _a.rule == "scan_live_card", "trận ngày mai thì giờ đã qua cũng chưa đá, không được mở"
    _a = _act(_drv(now_fn=lambda: _now14), _ui_kickoff("Hôm nay", "21:00"))
    assert _a.rule == "scan_live_card", "trận hôm nay chưa tới giờ đá thì không được mở"
    # (e) chỉ có nav 'TRỰC TIẾP' + thẻ SẮP ĐÁ (không có thẻ LIVE thật) ->
    # nav không được tính là thẻ LIVE: không mở, quét xuống.
    _ui_nav_only = {
        "focused_sig": "nav_home#[362,0][563,112]", "focused_text": "Trang chủ",
        "focused_bounds": "[362,0][563,112]",
        "all_visible_texts": [("nav_home", "Trang chủ"), ("nav_live", "TRỰC TIẾP"),
                              ("cardRoot", "Trận A"), ("cardBadge", "SẮP ĐÁ")],
        "all_visible_nodes": [
            {"id": "nav_home", "text": "Trang chủ", "bounds": "[362,0][563,112]"},
            {"id": "nav_live", "text": "TRỰC TIẾP", "bounds": "[700,0][900,112]"},
            {"id": "cardRoot", "text": "Trận A", "bounds": "[100,400][500,700]"},
            {"id": "cardBadge", "text": "SẮP ĐÁ", "bounds": "[120,410][200,440]"}],
        "has_dialog": False, "dialog_ids": []}
    _a = _act(_drv(), _ui_nav_only)
    print("chỉ nav TRỰC TIẾP + thẻ SẮP ĐÁ ->", _a.type, _a.param, "| rule:", _a.rule)
    assert _a.rule == "scan_live_card", \
        "nhãn nav 'TRỰC TIẾP' không phải thẻ trận LIVE — không được mở"
    # (f) mission mở player KHÁC (IPTV_EPG: mở kênh, không phải trận) không
    # bị chặn bởi luật trận đang đá: không có thẻ LIVE vẫn OK như cũ.
    _iptv = _specs["MISSION_IPTV_EPG_AND_ZAPPING_PLAYER"]
    _ui_chan = {
        "focused_sig": "channelCard#[100,400][500,700]", "focused_text": "VTV1 HD",
        "focused_bounds": "[100,400][500,700]",
        "all_visible_texts": [("nav_home", "Trang chủ"), ("nav_live", "TRỰC TIẾP"),
                              ("channelCard", "VTV1 HD"), ("channelCard2", "VTV3 HD")],
        "all_visible_nodes": [
            {"id": "nav_home", "text": "Trang chủ", "bounds": "[362,0][563,112]"},
            {"id": "nav_live", "text": "TRỰC TIẾP", "bounds": "[700,0][900,112]"},
            {"id": "channelCard", "text": "VTV1 HD", "bounds": "[100,400][500,700]"},
            {"id": "channelCard2", "text": "VTV3 HD", "bounds": "[100,750][500,1050]"}],
        "has_dialog": False, "dialog_ids": []}
    _a = _act(_drv(spec=_iptv), _ui_chan)
    print("IPTV_EPG không có thẻ LIVE ->", _a.type, _a.param, "| rule:", _a.rule)
    assert _a.rule == "open_player", \
        "luật chỉ-chọn-trận-đang-đá chỉ áp mission ExoPlayer, mission IPTV mở kênh không bị chặn"
    print("CI_T9_EXOPLAYER_LIVE_ONLY_OK")


def test_ci_t9_exoplayer_no_live_unverified():
    """CI-T9 nhóm B mục (3): dump chỉ có trận tương lai (SẮP ĐÁ) -> mission
    ExoPlayer phải UNVERIFIED (chưa kiểm được), KHÔNG mở player (không bấm
    OK lần nào), KHÔNG FAIL oan. Chạy mission thật bằng runner trên
    FakeDevice chỉ có trận tương lai; cờ schedule_live_seen False nên
    runner đổi outcome thành UNVERIFIED (cơ chế CI-T8 mục 7)."""
    import shutil as _sh
    _sh.rmtree("/tmp/qa_mock_exo_nolive", ignore_errors=True)
    _no_live_dump = {
        "focused_sig": "nav_home#[362,0][563,112]",
        "focused_text": "Trang chủ",
        "focused_bounds": "[362,0][563,112]",
        "focusable_count": 8,
        "all_visible_texts": [("nav_home", "Trang chủ"), ("nav_live", "TRỰC TIẾP"),
                              ("cardRoot", "Kuwait vs Syria"), ("cardBadge", "SẮP ĐÁ"),
                              ("cardTime", "21:00")],
        "all_visible_nodes": [
            {"id": "nav_home", "text": "Trang chủ", "bounds": "[362,0][563,112]"},
            {"id": "nav_live", "text": "TRỰC TIẾP", "bounds": "[700,0][900,112]"},
            {"id": "cardRoot", "text": "Kuwait vs Syria", "bounds": "[100,400][500,700]"},
            {"id": "cardBadge", "text": "SẮP ĐÁ", "bounds": "[120,410][200,440]"},
            {"id": "cardTime", "text": "21:00", "bounds": "[120,450][220,480]"}],
        "has_dialog": False,
        "dialog_ids": [],
        "selected_ids": ["nav_home"],
        "ui_summary": "[FOCUSED] nav_home ('Trang chủ') [362,0][563,112]",
        "osd_visible": False,
    }

    class _NoLiveDevice(FakeDevice):
        def __init__(self, *a, **k):
            super().__init__(*a, **k)
            self._dump = dict(_no_live_dump)
            self._tab = 0

    from missions import get_missions
    _specs = {s.name: s for s in get_missions()}
    _orig_dev = runner_mod.RealtimeDevice
    runner_mod.RealtimeDevice = _NoLiveDevice
    try:
        _r = runner_mod.RealtimeRunner(out_dir="/tmp/qa_mock_exo_nolive", serial=None,
                                       vision_budget=0, no_vision=True)
        _rep = _r.run([_specs["MISSION_PLAYER_STREAMING_AND_CONTROLS"]])
    finally:
        runner_mod.RealtimeDevice = _orig_dev
    _res = _r.mission_results[0]
    print("ExoPlayer chỉ có trận tương lai -> outcome:", _res["outcome"],
          "| reason:", _res["reason"][:160],
          "| keys:", _r.device.keys)
    assert _res["outcome"] == "UNVERIFIED", \
        "chỉ có trận tương lai thì mission ExoPlayer phải UNVERIFIED, không FAIL (được %s)" % _res["outcome"]
    assert "OK" not in _r.device.keys, \
        "không có trận đang đá thì driver không được bấm OK mở player lần nào (keys: %s)" % _r.device.keys
    assert _rep.get("schedule_live_seen") is False
    print("CI_T9_EXOPLAYER_NO_LIVE_UNVERIFIED_OK")


def test_ci_t9_focus_ring_circle():
    """CI-T9 (1): focus-ring phải nhận vòng tròn/ellipse — test chu vi cũ
    (>= 45% pixel sát 4 cạnh bbox) loại hình tròn nội tiếp (chỉ chạm cạnh
    ở 4 điểm). Bằng chứng CI-T8: step_066/076 có vòng trắng rõ quanh nút
    pause nhưng image_focus_ring=False ở cả 95/95 bước.
    - Vòng tròn r=40 vẽ bằng PIL: rect-coverage cũ 0.438 (< 0.45, đo trực
      tiếp từ ảnh — code cũ loại) nhưng code mới phải nhận (đường ellipse).
    - Ellipse dẹt 200x60: rect-coverage cũ 0.446 -> cũ loại, mới nhận.
    - Viền chữ nhật cũ (N18) vẫn pass; khối đặc vẫn loại (hồi quy).
    - Replay khung thật CI-T8 (bỏ qua nếu không có artifact local):
      step_066/076 (vòng pause) True, step_081 (nút list focus) True,
      step_060 (nút "ÂM THANH & PHỤ ĐỀ" focus) True, step_062 (không
      viền — finding #1 THẬT) False.
    Lưu ý cơ chế thật (đo trên khung 066): vòng còn vỡ thành mảnh dưới
    ngưỡng trắng 215 + nối +-1px nên code cũ không thấy component nào
    (rect-coverage của vòng gộp là 0.64 — test chu vi không phải thủ phạm
    duy nhất); sửa gồm ngưỡng 190 + nối +-2px + 2 đường ellipse/circle.
    """
    from PIL import Image as _Im, ImageDraw as _Dr
    _dev = RealtimeDevice()

    def _png(_draw):
        _im = _Im.new("RGB", (960, 540), (25, 25, 30))
        _draw(_Dr.Draw(_im))
        _buf = io.BytesIO()
        _im.save(_buf, format="PNG")
        return _buf.getvalue()

    def _rect_cov(_png_bytes):
        """Tỉ lệ pixel trắng nằm sát 4 cạnh bbox — đúng luật test chu vi
        cũ, đo độc lập với detect_focus_ring_anywhere."""
        _im = _Im.open(io.BytesIO(_png_bytes)).convert("RGB")
        _px = _im.load()
        _pts = []
        for _y in range(425, 540):
            for _x in range(0, 960, 2):
                _r, _g, _b = _px[_x, _y]
                if _r >= 190 and _g >= 190 and _b >= 190:
                    _pts.append((_x, _y))
        _xs = [p[0] for p in _pts]
        _ys = [p[1] for p in _pts]
        _x0, _x1, _y0, _y1 = min(_xs), max(_xs), min(_ys), max(_ys)
        return sum(1 for (a, b) in _pts
                   if b - _y0 <= 3 or _y1 - b <= 3
                   or a - _x0 <= 3 or _x1 - a <= 3) / len(_pts)

    _circ = _png(lambda d: d.ellipse([390, 442, 470, 522],
                                     outline=(255, 255, 255), width=3))
    _cc = _rect_cov(_circ)
    print("vòng tròn r=40 rect-coverage cũ:", round(_cc, 3))
    assert _cc < 0.45, "vòng tròn r=40 phải rớt test chu vi cũ (được %.3f)" % _cc
    _f, _col, _cov, _box = _dev.detect_focus_ring_anywhere(_circ)
    print("vòng tròn r=40 ->", _f, _col, _cov, _box)
    assert _f is True and _col == "WHITE" and _cov >= 0.55, \
        "vòng tròn trắng thật phải được nhận là vòng focus"
    assert _box and 760 <= _box[0] <= 800 and 860 <= _box[1] <= 900, \
        "box vòng phải gần (390,442)-(470,522) ở 960x540, được %s" % (_box,)
    _el = _png(lambda d: d.ellipse([600, 455, 800, 515],
                                   outline=(255, 255, 255), width=3))
    _ec = _rect_cov(_el)
    print("ellipse 200x60 rect-coverage cũ:", round(_ec, 3))
    assert _ec < 0.45, "ellipse dẹt phải rớt test chu vi cũ (được %.3f)" % _ec
    _f2, _col2, _cov2, _box2 = _dev.detect_focus_ring_anywhere(_el)
    print("ellipse 200x60 ->", _f2, _col2, _cov2, _box2)
    assert _f2 is True and _cov2 >= 0.55, "ellipse trắng thật phải được nhận"
    assert _box2 and 1180 <= _box2[0] <= 1220 and 900 <= _box2[1] <= 925, \
        "box ellipse phải gần (600,455)-(800,515) ở 960x540, được %s" % (_box2,)
    # Hồi quy: viền chữ nhật cũ vẫn pass, khối đặc vẫn loại.
    _rect = _png(lambda d: d.rectangle([100, 450, 300, 500],
                                       outline=(255, 200, 0), width=3))
    assert _dev.detect_focus_ring_anywhere(_rect)[0] is True, \
        "viền chữ nhật cũ vẫn phải pass"
    _solid = _png(lambda d: d.rectangle([600, 450, 700, 500],
                                        fill=(240, 240, 240)))
    assert _dev.detect_focus_ring_anywhere(_solid)[0] is False, \
        "khối trắng đặc không phải vòng focus"
    # Replay khung thật CI-T8.
    _shots = os.path.expanduser(
        "~/workspace/kenhlive-plan/qa-run-43127423731/shots")
    if not os.path.isdir(_shots):
        print("CI_T9_FOCUS_RING_CIRCLE_SKIP (không có artifact CI-T8 local)")
        return
    for _fn in ("step_066_vod_play.jpg", "step_076_webplaye.jpg"):
        _r66 = _dev.detect_focus_ring_anywhere(
            open(os.path.join(_shots, _fn), "rb").read())
        print(_fn, "->", _r66)
        assert _r66[0] is True and _r66[1] == "WHITE", \
            "vòng pause trắng ở %s phải được nhận" % _fn
        assert _r66[3] and 770 <= _r66[3][0] <= 810 and 900 <= _r66[3][1] <= 940, \
            "box vòng pause phải gần nút pause (788,920)-(896,1032), được %s" % (_r66[3],)
    _r62 = _dev.detect_focus_ring_anywhere(
        open(os.path.join(_shots, "step_062_vod_play.jpg"), "rb").read())
    print("step_062 (không viền) ->", _r62)
    assert _r62[0] is False, "step_062 không có viền thì finding #1 thật, không được nhận oan"
    _r60 = _dev.detect_focus_ring_anywhere(
        open(os.path.join(_shots, "step_060_phim_epi.jpg"), "rb").read())
    print("step_060 (nút ÂM THANH & PHỤ ĐỀ focus) ->", _r60)
    assert _r60[0] is True, "step_060 có nút focus viền trắng thì phải nhận"
    _r81 = _dev.detect_focus_ring_anywhere(
        open(os.path.join(_shots, "step_081_webplaye.jpg"), "rb").read())
    assert _r81[0] is True, "step_081 có nút list focus thì phải nhận"
    print("CI_T9_FOCUS_RING_CIRCLE_OK")


def test_h3_sports_multi_source_seek_cola():
    """H3 (trial 5 run 43183031119): mission SPORTS_MULTI_SOURCE tìm 'cola'
    sai chỗ — driver explore DOWN/RIGHT dao động A-B-A-B giữa 2 thẻ NBL/JLC
    (chỉ có badge 'SOCO') suốt 8 bước, trong khi app CÓ hiện 'COLA' ở thẻ
    khác cùng tab (step_036 'Aus Champ COLA'). Giờ spec khai goto_texts
    ['cola'] + max_steps 10, driver quét chéo DOWN/RIGHT xen kẽ cho tới khi
    text xuất hiện trong dump; đã thấy text thì dừng quét (explore thường).
    Hồi quy: dump chỉ toàn SOCO, focus dao động 2 thẻ -> các action phải
    xen kẽ DOWN, RIGHT, DOWN, RIGHT (không được DOWN, DOWN, RIGHT như
    explore cũ, và không được kẹt ở 1 hướng)."""
    from driver import Driver
    from gate import EvidenceGate
    from missions import get_missions
    _specs = {s.name: s for s in get_missions()}
    _sp = _specs["MISSION_SPORTS_MULTI_SOURCE"]
    assert _sp.goto_texts == ["cola"], \
        "spec SPORTS_MULTI phải khai goto_texts ['cola'] để driver quét tìm"
    assert _sp.max_steps == 10, \
        "quét chéo cần chỗ: max_steps 8 -> 10 (thử 5 hết 8 bước vẫn chưa tới hàng COLA)"

    def _ui_soco(focus_text, focus_sig):
        return {
            "focused_sig": focus_sig, "focused_text": focus_text,
            "focused_bounds": "[100,400][500,700]",
            "all_visible_texts": [("nav_live", "TRỰC TIẾP"),
                                  ("cardRoot", "Adelaide vs Melbourne United"),
                                  ("cardBadge", "SOCO"),
                                  ("cardRoot2", "Kawasaki Frontale vs Kashiwa Reysol"),
                                  ("cardBadge2", "SOCO")],
            "all_visible_nodes": [
                {"id": "cardRoot", "text": "Adelaide vs Melbourne United",
                 "bounds": "[100,400][500,700]"},
                {"id": "cardRoot2", "text": "Kawasaki Frontale vs Kashiwa Reysol",
                 "bounds": "[100,750][500,1050]"}],
            "has_dialog": False, "dialog_ids": []}
    _dev = FakeDevice()
    _dev._tab = 0
    _gate = EvidenceGate(_sp)
    _drv = Driver(_dev, _gate, _sp)
    # Mô phỏng bẫy A-B-A-B thử 5: DOWN từ thẻ A rơi về thẻ B và ngược lại.
    _seq = []
    _focus = [("Adelaide vs Melbourne United", "cardRoot#[100,400][500,700]"),
              ("Kawasaki Frontale vs Kashiwa Reysol", "cardRoot2#[100,750][500,1050]")]
    for _i in range(4):
        _ft, _fs = _focus[_i % 2]
        _a = _drv.next_action(_ui_soco(_ft, _fs),
                              "com.kenhlive.tv/.MainActivity", None, 0.0)
        _seq.append((_a.param, _a.rule))
    print("quét tìm 'cola' giữa 2 thẻ SOCO ->", _seq)
    assert [p for p, _ in _seq] == ["DPAD_DOWN", "DPAD_RIGHT",
                                    "DPAD_DOWN", "DPAD_RIGHT"], \
        "chưa thấy 'cola' thì phải quét chéo DOWN/RIGHT xen kẽ, được %s" % (_seq,)
    assert all(r == "seek_target_text" for _, r in _seq), \
        "các bước quét phải mang rule seek_target_text, không phải explore"
    # Đã thấy 'cola' trong dump (gate bank) thì dừng quét, về explore thường.
    _gate.texts_seen.add("cola")
    _a = _drv.next_action(_ui_soco(*_focus[0]),
                          "com.kenhlive.tv/.MainActivity", None, 0.0)
    print("đã thấy 'cola' ->", _a.type, _a.param, "| rule:", _a.rule)
    assert _a.rule != "seek_target_text", \
        "đã thấy text mục tiêu thì không được quét nữa (rule: %s)" % _a.rule
    print("H3_SPORTS_MULTI_SEEK_COLA_OK")


def test_h4_iptv_hold_and_no_tab_switch_in_player():
    """H4 (trial 5 run 43183031119): mission IPTV_EPG FAIL oan 2× vision deny.
    (a) Driver SWITCH_TAB giết player đang phát: ở PlayerActivity, dump có
    nút OSD 'VỀ TRỰC TIẾP' nên detect_tab trả 0 ≠ tab 2 -> luật goto_tab nổ
    -> `am start MainActivity` -> player thoát về lưới (log run: SWITCH_TAB 2
    [goto_tab] giữa lúc kênh đang phát, motion 10.37) -> vision chạy trên
    khung lưới rồi khung tải luồng. Giờ goto_tab CẤM trong player.
    (b) Kênh đã phát (motion_seen) thì driver GIỮ NGUYÊN (WAIT) thay vì probe
    DPAD_RIGHT, để observation kế tiếp — lúc runner gọi vision-confirm —
    vẫn là khung kênh đang phát, không phải màn 'Đang tải luồng...'.
    (c) Hồi quy: ExoPlayer không bị luật giữ kênh IPTV chạm tới; ngoài player
    thì goto_tab vẫn chạy như cũ."""
    from driver import Driver
    from gate import EvidenceGate
    from missions import get_missions
    _specs = {s.name: s for s in get_missions()}
    _iptv = _specs["MISSION_IPTV_EPG_AND_ZAPPING_PLAYER"]
    _exo = _specs["MISSION_PLAYER_STREAMING_AND_CONTROLS"]

    def _drv(spec, tab, motion_seen=False):
        _dev = FakeDevice()
        _dev._tab = tab
        _g = EvidenceGate(spec)
        if motion_seen:
            _g.observe("com.kenhlive.tv/.PlayerActivity", [], [], False, True, 10.0)
        return Driver(_dev, _g, spec)

    # Dump player IPTV kiểu thử 5: OSD có 'VỀ TRỰC TIẾP', focus 'QUAY LẠI'.
    _ui_player = {
        "focused_sig": "btnBack#[100,900][300,1000]",
        "focused_text": "◀ QUAY LẠI",
        "focused_bounds": "[100,900][300,1000]",
        "all_visible_texts": [("btnBack", "◀ QUAY LẠI"),
                              ("btnLive", "VỀ TRỰC TIẾP"),
                              ("channelName", "VTV Cần Thơ")],
        "all_visible_nodes": [
            {"id": "btnBack", "text": "◀ QUAY LẠI", "bounds": "[100,900][300,1000]"},
            {"id": "btnLive", "text": "VỀ TRỰC TIẾP", "bounds": "[400,900][700,1000]"}],
        "has_dialog": False, "dialog_ids": []}

    # (a) trong player + tab detect lệch (0 ≠ 2) + kênh đang phát -> WAIT giữ
    # kênh, TUYỆT ĐỐI không SWITCH_TAB.
    _a = _drv(_iptv, 0, motion_seen=True).next_action(
        _ui_player, "com.kenhlive.tv/.PlayerActivity", None, 0.0)
    print("IPTV trong player, tab lệch, đang phát ->", _a.type, _a.param, "| rule:", _a.rule)
    assert _a.type != "SWITCH_TAB", \
        "SWITCH_TAB trong player giết playback (thử 5) — không được chạy khi đang ở PlayerActivity"
    assert _a.rule == "hold_playing_channel" and _a.type == "WAIT", \
        "kênh đang phát thì phải WAIT giữ khung phát (được %s %s)" % (_a.type, _a.rule)
    # (a2) trong player + tab lệch + kênh CHƯA phát xong motion -> WAIT chờ
    # stream, cũng không SWITCH_TAB.
    _a = _drv(_iptv, 0, motion_seen=False).next_action(
        _ui_player, "com.kenhlive.tv/.PlayerActivity", None, 0.0)
    print("IPTV trong player, tab lệch, chưa có motion ->", _a.type, _a.param, "| rule:", _a.rule)
    assert _a.type != "SWITCH_TAB" and _a.rule == "wait_stream", \
        "chưa có motion thì WAIT chờ stream, không SWITCH_TAB (được %s %s)" % (_a.type, _a.rule)
    # (b) kênh đã phát, focus có text -> trước đây probe DPAD_RIGHT, giờ WAIT.
    _a = _drv(_iptv, 2, motion_seen=True).next_action(
        _ui_player, "com.kenhlive.tv/.PlayerActivity", None, 0.0)
    assert _a.rule == "hold_playing_channel", \
        "IPTV đã phát thì giữ kênh, không probe DPAD_RIGHT (được %s)" % _a.rule
    # (c1) hồi quy ExoPlayer: đang phát thì vẫn probe như cũ, không giữ kênh.
    _a = _drv(_exo, 0, motion_seen=True).next_action(
        _ui_player, "com.kenhlive.tv/.PlayerActivity", None, 0.0)
    print("ExoPlayer trong player, đang phát ->", _a.type, _a.param, "| rule:", _a.rule)
    assert _a.rule == "probe_player", \
        "luật giữ kênh chỉ áp mission IPTV, ExoPlayer vẫn probe như cũ (được %s)" % _a.rule
    # (c2) ngoài player thì goto_tab vẫn chạy: lưới IPTV nhưng detect tab 0.
    _ui_grid = dict(_ui_player, focused_sig="channelCard#[100,400][500,700]",
                    focused_text="VTV Cần Thơ",
                    focused_bounds="[100,400][500,700]")
    _a = _drv(_iptv, 0).next_action(
        _ui_grid, "com.kenhlive.tv/.MainActivity", None, 0.0)
    print("IPTV ở MainActivity, tab lệch ->", _a.type, _a.param, "| rule:", _a.rule)
    assert _a.type == "SWITCH_TAB" and _a.param == "2" and _a.rule == "goto_tab", \
        "ngoài player thì sai tab vẫn phải SWITCH_TAB về tab đích (được %s %s)" % (_a.type, _a.rule)
    print("H4_IPTV_HOLD_NO_TAB_SWITCH_IN_PLAYER_OK")


def test_h1_total_only_reading_dropped():
    """H1 (vòng sửa sau trial 5, run 43183031119): lần đọc đồng hồ bằng
    đúng giờ tổng (13:53 = 833s) phải bị bỏ qua — đó là lúc cả 2 lượt OCR
    đều mất chữ giờ phát mà chỉ đọc được giờ tổng (vals=[833,833]).
    Dãy đọc trial 5: 114, 833, 134, 144, 144, 833, 833, 174, 174, 194,
    204 — bỏ 833 thì còn 114->204 tăng đơn điệu, mission không FAIL oan.
    Quy tắc: cặp elapsed/total phải có 2 giá trị KHÁC nhau; mọi giá trị
    đọc được đều bằng nhau thì lần đọc mơ hồ -> None (không đoán)."""
    from runner import _playback_seconds_from_text as _pb_txt
    from runner import RealtimeRunner as _RR
    from detectors import BOTTOM_BAR_BAND as _BBB
    from gate import EvidenceGate
    from missions import get_missions
    # Cặp bằng nhau (elapsed == tổng) thì mơ hồ -> None, không lấy min.
    assert _pb_txt("13:53 / 13:53") is None, \
        "cặp elapsed/total bằng nhau thì không phân biệt được, phải None"
    assert _pb_txt("03:24 / 13:53") == 204
    assert _pb_txt("00:59 / 13:53") == 59
    assert _RR._parse_time_token("13:53/13:53") is None
    assert _RR._parse_time_token("0224/1353") == 144
    assert _RR._parse_time_token("02:24") == 144, "token lẻ giữ nguyên"
    _r = _RR(out_dir="/tmp/qa_mock_h1", serial=None,
             vision_budget=0, no_vision=True)

    def _extract(boxes):
        _r.detector_ctx["_ocr_cache"] = {("step_001.jpg", _BBB): boxes}
        return _r._extract_playback_s({"all_visible_texts": []}, "step_001.jpg")

    # Cả 2 lượt OCR chỉ đọc được giờ tổng -> bỏ qua (trial 5: 833 oan).
    assert _extract([{"text": "13:53"}, {"text": "13:53"}]) is None, \
        "2 lượt OCR đều chỉ đọc được giờ tổng thì lần đọc phải bị bỏ qua"
    # 1 box gộp toàn giờ tổng cũng vậy.
    assert _extract([{"text": "13:53/13:53"}]) is None
    # Cặp đủ -> elapsed; box lẻ elapsed + box lẻ tổng -> elapsed.
    assert _extract([{"text": "02:24/13:53"}]) == 144
    assert _extract([{"text": "02:24"}, {"text": "13:53"}]) == 144
    # Dãy trial 5 qua _extract + gate: 833 bị bỏ, còn lại tăng đơn điệu.
    _specs = {s.name: s for s in get_missions()}
    _g = EvidenceGate(_specs["MISSION_WEBPLAYER_DIRECTED_REAL_FILM"])
    _trial5 = [114, 833, 134, 144, 144, 833, 833, 174, 174, 194, 204]
    _kept = []
    for _i, _v in enumerate(_trial5):
        _m, _s = divmod(_v, 60)
        if _v == 833:
            _got = _extract([{"text": "13:53"}, {"text": "13:53"}])
        else:
            _got = _extract([{"text": "%02d:%02d/13:53" % (_m, _s)}])
        _want = None if _v == 833 else _v
        assert _got == _want, "lần đọc %s phải ra %s, được %s" % (_v, _want, _got)
        if _got is not None:
            _g.observe_playback(_got, float(_i * 10))
            _kept.append(_got)
    assert _kept == [114, 134, 144, 144, 174, 174, 194, 204], \
        "833 xen giữa phải bị bỏ, dãy còn lại: %s" % _kept
    assert _g.playback_monotonic()[0] is True, \
        "bỏ 833 thì dãy còn lại phải tăng đơn điệu: %s" % _kept
    assert _g.playback_status() == "increasing"
    print("H1_TOTAL_ONLY_READING_DROPPED_OK", _kept)


def test_h4_runner_vision_confirm_current_frame():
    """H4-runner (1) (vòng sửa sau trial 5, run 43183031119): vision-confirm
    chỉ chạy trên observation HIỆN TẠI — gate VISION_PENDING dựa vào tín
    hiệu tích lũy (motion_seen/activities_seen) nên player tự thoát giữa
    2 observation thì vision vẫn gọi trên khung lưới/khung tải (IPTV_EPG
    trial 5: vision chối 2 lần trên khung tải/lưới). Giờ:
    (a) obs đang ở PlayerActivity + motion True -> vision gọi 1 lần;
    (b) obs đã về MainActivity (lưới) dù motion tích lũy True -> KHÔNG
    gọi vision (trả False, không tính denial);
    (c) obs là màn tải (loading_screen) -> KHÔNG gọi vision, KHÔNG poll;
    (d) obs motion False + watcher báo phát + dump mới xác nhận còn ở
    player, hết tải -> poll thành công, vision gọi;
    (e) obs motion False + watcher báo phát nhưng dump mới vẫn là màn tải
    (spinner đánh lừa poll) -> poll hết 10s, KHÔNG gọi vision."""
    from gate import EvidenceGate
    from missions import get_missions

    class _FV:
        def __init__(self):
            self.calls = []
        def available(self):
            return True
        def remaining(self):
            return 10
        def confirm_target(self, image_bytes, target_desc, timeout=60):
            self.calls.append(target_desc)
            return {"confirmed": True, "quote": "VTV Cần Thơ đang phát"}, None

    _specs = {s.name: s for s in get_missions()}
    _sp = _specs["MISSION_IPTV_EPG_AND_ZAPPING_PLAYER"]
    assert _sp.needs_motion and _sp.needs_vision \
        and _sp.required_activity == "PlayerActivity"
    # Runner phải dùng FakeDevice (như test no_live): main() alias sẵn khi
    # chạy full suite, nhưng test này còn phải chạy được standalone.
    _orig_dev = runner_mod.RealtimeDevice
    runner_mod.RealtimeDevice = FakeDevice

    def _runner():
        _r = runner_mod.RealtimeRunner(out_dir="/tmp/qa_mock_h4v", serial=None,
                                       vision_budget=40, no_vision=False)
        _fv = _FV()
        _r.vision = _fv
        return _r, _fv

    def _obs(activity, motion, loading=False):
        return {"png": _fake_png(1), "frame_ref": "step_044_iptv_epg.jpg",
                "t_offset": 100.0, "activity": activity, "motion": motion,
                "loading_screen": loading}

    # (a) khung hiện tại đúng player + đang phát -> vision gọi 1 lần.
    _r, _fv = _runner()
    _g = EvidenceGate(_sp)
    assert _r._vision_confirm(_sp, _g, _obs(
        "com.kenhlive.tv/.PlayerActivity", True)) is True
    assert len(_fv.calls) == 1 and len(_g.vision_confirmations) == 1, \
        "khung player đang phát thì vision phải được gọi 1 lần"
    # (b) khung hiện tại đã về lưới (player tự thoát) -> không gọi vision.
    _r, _fv = _runner()
    _g = EvidenceGate(_sp)
    _g.motion_seen = True  # tín hiệu tích lũy từ khung trước (cái bẫy cũ)
    _g.activities_seen.add("com.kenhlive.tv/.PlayerActivity")
    assert _r._vision_confirm(_sp, _g, _obs(
        "com.kenhlive.tv/.MainActivity", True)) is False
    assert _fv.calls == [] and _g.vision_denials == 0, \
        "player đã thoát về lưới thì không được gọi vision trên khung lưới"
    # (c) khung hiện tại là màn tải -> không gọi vision, không poll.
    _r, _fv = _runner()
    _g = EvidenceGate(_sp)
    _t0 = time.time()
    assert _r._vision_confirm(_sp, _g, _obs(
        "com.kenhlive.tv/.PlayerActivity", True, loading=True)) is False
    assert _fv.calls == [] and time.time() - _t0 < 5.0, \
        "khung tải thì trả False ngay, không được poll 10s rồi gọi vision"
    # (d) motion chưa đo được ở obs, watcher báo phát, dump mới xác nhận
    # còn ở player + hết tải -> poll thành công, vision gọi.
    _r, _fv = _runner()
    _g = EvidenceGate(_sp)
    _r.device._activity = "com.kenhlive.tv/.PlayerActivity"
    _r.device._dump = dict(FakeDevice.HOME_DUMP)
    _now = time.time()
    _r.watcher._history = [(_now, 12.0), (_now, 11.0)]
    assert _r._vision_confirm(_sp, _g, _obs(
        "com.kenhlive.tv/.PlayerActivity", False)) is True
    assert len(_fv.calls) == 1 and _g.motion_seen is True, \
        "poll xác minh được stream đã phát thì vision phải được gọi"
    # (e) watcher báo phát nhưng dump mới vẫn là màn tải (spinner đánh lừa
    # poll) -> poll hết 10s, KHÔNG gọi vision.
    _r, _fv = _runner()
    _g = EvidenceGate(_sp)
    _r.device._activity = "com.kenhlive.tv/.PlayerActivity"
    _r.device._dump = {
        "focused_sig": "playerBuffering#[800,500][1120,580]",
        "focused_text": "Đang tải luồng…",
        "focused_bounds": "[800,500][1120,580]",
        "focusable_count": 1,
        "all_visible_texts": [("playerBuffering", "Đang tải luồng…")],
        "has_dialog": False, "dialog_ids": [], "selected_ids": [],
        "ui_summary": "[FOCUSED] playerBuffering ('Đang tải luồng…')",
        "osd_visible": False,
    }
    _now = time.time()
    _r.watcher._history = [(_now, 12.0), (_now, 11.0)]
    _t0 = time.time()
    assert _r._vision_confirm(_sp, _g, _obs(
        "com.kenhlive.tv/.PlayerActivity", False)) is False
    assert _fv.calls == [] and time.time() - _t0 >= 9.0, \
        "dump mới vẫn là màn tải thì poll phải chờ hết 10s rồi trả False, không gọi vision"
    runner_mod.RealtimeDevice = _orig_dev
    print("H4_RUNNER_VISION_CONFIRM_CURRENT_FRAME_OK")


def test_h4_runner_loading_screen_not_playing():
    """H4-runner (2) (trial 5 run 43183031119): màn 'Đang tải luồng…'
    (step_044: màn đen + spinner, motion_delta 12.2) KHÔNG được tính là
    đang phát — spinner quay làm watcher/fallback đo motion cao nhưng
    video chưa phát. Giờ _observe trả loading_screen True + motion False
    (motion_delta vẫn giữ số đo thật), gate không tích lũy motion_seen.
    Đối chứng: cùng 2 frame khác nhau rõ, dump không có chữ tải ->
    motion True như cũ."""
    from gate import EvidenceGate
    from missions import get_missions
    _orig_dev = runner_mod.RealtimeDevice
    runner_mod.RealtimeDevice = FakeDevice
    try:
        _loading_dump = {
            "focused_sig": "playerBuffering#[800,500][1120,580]",
            "focused_text": "Đang tải luồng…",
            "focused_bounds": "[800,500][1120,580]",
            "focusable_count": 1,
            "all_visible_texts": [("playerBuffering", "Đang tải luồng…"),
                                  ("channelName", "VTV Cần Thơ")],
            "has_dialog": False, "dialog_ids": [], "selected_ids": [],
            "ui_summary": "[FOCUSED] playerBuffering ('Đang tải luồng…')",
            "osd_visible": False,
        }
        _r = runner_mod.RealtimeRunner(out_dir="/tmp/qa_mock_h4l", serial=None,
                                       vision_budget=0, no_vision=True)
        _r._global_step = 1  # ngoài chu kỳ lưu mỗi 5 bước (1 % 5 != 0)
        _r.device._activity = "com.kenhlive.tv/.PlayerActivity"
        _r.device._dump = dict(_loading_dump)
        _r.watcher._latest_png = _fake_png(5)
        _r.watcher._stable_streak = 5
        _r._prev_obs_png = _fake_png(0)
        _o = _r._observe("MISSION_IPTV_EPG_AND_ZAPPING_PLAYER")
        print("màn tải: loading", _o["loading_screen"], "| motion", _o["motion"],
              "| state", _o["motion_state"], "| delta", round(_o["motion_delta"], 2))
        assert _o["loading_screen"] is True, "dump có 'Đang tải luồng…' thì phải nhận màn tải"
        assert _o["motion"] is False and _o["motion_state"] is False, \
            "màn tải thì motion phải False dù spinner làm delta cao (được %s)" % _o["motion_delta"]
        assert _o["motion_delta"] > 0.35, \
            "motion_delta vẫn giữ số đo thật của spinner (được %s)" % _o["motion_delta"]
        # Gate không tích lũy motion_seen từ khung tải.
        _specs = {s.name: s for s in get_missions()}
        _g = EvidenceGate(_specs["MISSION_IPTV_EPG_AND_ZAPPING_PLAYER"])
        _g.observe("com.kenhlive.tv/.PlayerActivity",
                   [t for _, t in _loading_dump["all_visible_texts"]], [],
                   False, _o["motion"], 100.0)
        assert _g.motion_seen is False, \
            "motion False trên khung tải thì gate không được tích lũy motion_seen"
        # Đối chứng: cùng 2 frame, dump không có chữ tải -> motion True.
        _r._global_step = 2
        _r.device._dump = dict(FakeDevice.HOME_DUMP)
        _r.watcher._latest_png = _fake_png(5)
        _r.watcher._stable_streak = 5
        _r._prev_obs_png = _fake_png(0)
        _o2 = _r._observe("MISSION_IPTV_EPG_AND_ZAPPING_PLAYER")
        print("không tải: loading", _o2["loading_screen"], "| motion", _o2["motion"])
        assert _o2["loading_screen"] is False and _o2["motion"] is True, \
            "không có chữ tải thì 2 frame khác nhau rõ vẫn tính là đang phát"
    finally:
        runner_mod.RealtimeDevice = _orig_dev
    print("H4_RUNNER_LOADING_SCREEN_NOT_PLAYING_OK")


def test_h2_episode_dialog_detected():
    """H2(b) (trial 5 run 43183031119): dialog chọn tập mở rõ (step_051)
    nhưng gate.dialog_seen vẫn false suốt mission. Gốc rễ: 'episodeList'
    trong dialog_id_set là id CHẾT (không tồn tại trong app — layout thật
    là dialog_film_episodes.xml, lưới tập là dialogEpisodesGrid), còn
    dialogBtnClose nằm ở footer, bị cắt khỏi màn hình khi dialog cao hơn
    màn hình nên detector chỉ còn trông vào mỗi id đó. Giờ detector nhận
    dialog qua các id phần trên (dialogFilmTitle/dialogEpisodesGrid/...) +
    mọi id bắt đầu bằng 'dialog'. Kiểm bằng XML dump THẬT (parse như live).
    - (a) dump trial-5 step_051 (KHÔNG có dialogBtnClose — footer ngoài
      màn hình) -> has_dialog True nhờ dialogFilmTitle/dialogEpisodesGrid;
    - (b) chỉ dialogBtnClose -> True (đường cũ giữ nguyên);
    - (c) dialogLeague (dialog RoomPicker) -> True (luật prefix);
    - (d) id dialog mới chưa biết -> True (luật prefix);
    - (e) màn thường (nút CHỌN TẬP, chưa mở dialog) -> False;
    - (f) chỉ tvEpisodeName đơn độc -> False (chip này còn dùng trong
      player nên KHÔNG được tính là dialog — tránh false-positive)."""
    import device as _devmod

    def _fake_xml_h2(nodes):
        parts = ['<hierarchy rotation="0">']
        for _id, _txt, _foc in nodes:
            parts.append(
                '<node index="0" text="%s" resource-id="com.kenhlive.tv:id/%s" '
                'class="android.widget.Button" package="com.kenhlive.tv" '
                'content-desc="" checkable="false" checked="false" clickable="true" '
                'enabled="true" focusable="true" focused="%s" scrollable="false" '
                'long-clickable="false" password="false" selected="false" '
                'bounds="[100,200][500,600]" />' % (_txt, _id, "true" if _foc else "false"))
        parts.append('</hierarchy>')
        return "".join(parts)

    _orig_sh = _devmod.sh
    try:
        # (a) dialog chọn tập trial 5: không có dialogBtnClose.
        _devmod.sh = lambda cmd, timeout=30: _fake_xml_h2([
            ("nav_home", "Trang chủ", False),
            ("dialogFilmPoster", "", False),
            ("dialogFilmTitle", "Tuyệt Thế Chiến Hồn", False),
            ("dialogFilmMeta", "2024 · Hành Động", False),
            ("dialogEpisodesGrid", "", False),
            ("tvEpisodeName", "Tập 1", True)])
        _st = _devmod.RealtimeDevice().dump_ui_state()
        print("dialog chọn tập (không dialogBtnClose) -> has_dialog:",
              _st["has_dialog"], "| dialog_ids:", _st["dialog_ids"],
              "| focused:", _st["focused_sig"])
        assert _st["has_dialog"] is True, \
            "dialog chọn tập phải được nhận dù footer (dialogBtnClose) ngoài màn hình"
        assert "dialogEpisodesGrid" in _st["dialog_ids"] \
            and "dialogFilmTitle" in _st["dialog_ids"]
        assert _st["focused_sig"].startswith("tvEpisodeName#")
        # (b) chỉ dialogBtnClose -> True như trước.
        _devmod.sh = lambda cmd, timeout=30: _fake_xml_h2([
            ("dialogBtnClose", "Đóng", True)])
        assert _devmod.RealtimeDevice().dump_ui_state()["has_dialog"] is True, \
            "dialogBtnClose đơn độc vẫn phải nhận là dialog"
        # (c) dialogLeague (RoomPicker) -> True.
        _devmod.sh = lambda cmd, timeout=30: _fake_xml_h2([
            ("dialogLeague", "Giải đấu", False)])
        assert _devmod.RealtimeDevice().dump_ui_state()["has_dialog"] is True, \
            "dialogLeague của RoomPicker phải được nhận (luật prefix 'dialog')"
        # (d) id dialog mới chưa biết -> True.
        _devmod.sh = lambda cmd, timeout=30: _fake_xml_h2([
            ("dialogSomethingNew", "", False)])
        assert _devmod.RealtimeDevice().dump_ui_state()["has_dialog"] is True, \
            "id bắt đầu bằng 'dialog' thì phải tính là dialog (chống tái phát)"
        # (e) màn thường: nút CHỌN TẬP chưa mở dialog -> False.
        _devmod.sh = lambda cmd, timeout=30: _fake_xml_h2([
            ("nav_home", "Trang chủ", False),
            ("btnHeroEpisodes", "CHỌN TẬP", True)])
        assert _devmod.RealtimeDevice().dump_ui_state()["has_dialog"] is False, \
            "nút CHỌN TẬP trên màn chính không phải dialog"
        # (f) chỉ tvEpisodeName đơn độc -> False (chip còn dùng trong player).
        _devmod.sh = lambda cmd, timeout=30: _fake_xml_h2([
            ("tvEpisodeName", "Tập 1", True)])
        assert _devmod.RealtimeDevice().dump_ui_state()["has_dialog"] is False, \
            "tvEpisodeName đơn độc không được tính là dialog (còn dùng trong player)"
    finally:
        _devmod.sh = _orig_sh
    print("H2_EPISODE_DIALOG_DETECTED_OK")


def test_h2_episode_picker_player_is_not_fail():
    """H2(a) (trial 5 run 43183031119): mission chọn tập FAIL oan — OK trên
    'Tập 1' mở player đúng tập nhưng runner FAIL bằng mẫu mission thể thao
    ('thẻ trận', 'dialog chọn phòng') vì gate coi 'kết thúc ở Player' là
    lỗi. Giờ: OK trên chip tập -> player là hành vi đúng — runner ghi nhận
    dialog theo suy luận (dialog_implied) rồi để gate đánh giá, mission
    PASS; thông báo FAIL cho mission khác ghi theo đúng mission. Chạy
    mission thật trên FakeDevice diễn lại đúng 4 bước trial 5 (đi tới nút
    CHỌN TẬP -> OK mở dialog -> dialog mở nhưng dump không nhận ra
    (has_dialog False, như trial 5) -> OK trên 'Tập 1' -> player)."""
    import shutil as _sh
    _sh.rmtree("/tmp/qa_mock_h2_ep", ignore_errors=True)
    from missions import get_missions
    _specs = {s.name: s for s in get_missions()}
    _sp = _specs["MISSION_PHIM_EPISODE_PICKER_AND_FAVORITE"]

    _DUMP_HOME = {
        "focused_sig": "nav_home#[362,0][563,112]",
        "focused_text": "Trang chủ",
        "focused_bounds": "[362,0][563,112]",
        "focusable_count": 8,
        "all_visible_texts": [("nav_home", "Trang chủ"),
                              ("btnHeroEpisodes", "CHỌN TẬP"),
                              ("heroTitle", "Tuyệt Thế Chiến Hồn")],
        "all_visible_nodes": [
            {"id": "nav_home", "text": "Trang chủ", "bounds": "[362,0][563,112]"},
            {"id": "btnHeroEpisodes", "text": "CHỌN TẬP", "bounds": "[494,518][850,602]"}],
        "has_dialog": False, "dialog_ids": [],
        "selected_ids": ["nav_home"],
        "ui_summary": "[FOCUSED] nav_home ('Trang chủ')",
        "osd_visible": False,
    }
    _DUMP_ON_BUTTON = dict(
        _DUMP_HOME,
        focused_sig="btnHeroEpisodes#[494,518][850,602]",
        focused_text="CHỌN TẬP",
        focused_bounds="[494,518][850,602]",
        ui_summary="[FOCUSED] btnHeroEpisodes ('CHỌN TẬP')")
    # Dialog mở nhưng dump KHÔNG nhận ra (has_dialog False) — đúng tình
    # trạng trial 5 step_051 (footer ngoài màn hình, episodeList là id
    # chết). Không còn node 'CHỌN TẬP' nào với tới được (như dump thật).
    _DUMP_DIALOG_MISSED = {
        "focused_sig": "tvEpisodeName#[386,696][612,772]",
        "focused_text": "Tập 1",
        "focused_bounds": "[386,696][612,772]",
        "focusable_count": 22,
        "all_visible_texts": [("dialogFilmTitle", "Tuyệt Thế Chiến Hồn"),
                              ("dialogSection", "CHỌN SERVER & TẬP PHIM"),
                              ("tvEpisodeName", "Tập 1"),
                              ("tvEpisodeName2", "Tập 2")],
        "all_visible_nodes": [
            {"id": "dialogFilmTitle", "text": "Tuyệt Thế Chiến Hồn",
             "bounds": "[386,60][900,140]"},
            {"id": "tvEpisodeName", "text": "Tập 1", "bounds": "[386,696][612,772]"},
            {"id": "tvEpisodeName2", "text": "Tập 2", "bounds": "[640,696][866,772]"}],
        "has_dialog": False, "dialog_ids": [],
        "selected_ids": [],
        "ui_summary": "[FOCUSED] tvEpisodeName ('Tập 1')",
        "osd_visible": False,
    }
    _DUMP_PLAYER = {
        "focused_sig": "NONE",
        "focused_text": "",
        "focused_bounds": None,
        "focusable_count": 4,
        "all_visible_texts": [("playerTitle", "Tuyệt Thế Chiến Hồn"),
                              ("playerEpisode", "Tập 01")],
        "all_visible_nodes": [],
        "has_dialog": False, "dialog_ids": [],
        "selected_ids": [],
        "ui_summary": "(Không tìm thấy focusable view)",
        "osd_visible": True,
    }

    class _EpDevice(FakeDevice):
        def _oks(self):
            return self.keys.count("OK")

        def _dpads(self):
            return sum(1 for k in self.keys if (k or "").startswith("DPAD"))

        def dump_ui_state(self):
            _n_ok, _n_dpad = self._oks(), self._dpads()
            if _n_ok == 0:
                return dict(_DUMP_ON_BUTTON) if _n_dpad >= 1 else dict(_DUMP_HOME)
            if _n_ok == 1:
                return dict(_DUMP_DIALOG_MISSED)
            return dict(_DUMP_PLAYER)

        def current_activity(self):
            return ("com.kenhlive.tv/.PlayerActivity" if self._oks() >= 2
                    else "com.kenhlive.tv/.MainActivity")

    _orig_dev = runner_mod.RealtimeDevice
    runner_mod.RealtimeDevice = _EpDevice
    try:
        _r = runner_mod.RealtimeRunner(out_dir="/tmp/qa_mock_h2_ep", serial=None,
                                       vision_budget=0, no_vision=True)
        _rep = _r.run([_sp])
    finally:
        runner_mod.RealtimeDevice = _orig_dev
    _res = _r.mission_results[0]
    print("EPISODE_PICKER OK trên Tập 1 -> player:", _res["outcome"],
          "| reason:", _res["reason"][:160], "| keys:", _r.device.keys)
    assert _res["outcome"] == "PASS", \
        "OK trên Tập 1 mở player đúng tập thì mission chọn tập phải PASS (được %s: %s)" \
        % (_res["outcome"], _res["reason"])
    assert _res["evidence"]["dialog_seen"] is True, \
        "dialog phải được ghi nhận (suy luận từ hành vi chọn tập)"
    assert _res["evidence"]["dialog_implied"] is True, \
        "evidence phải ghi rõ dialog_seen là suy luận (dialog_implied), không bịa lặng"
    assert "thẻ trận" not in _res["reason"] \
        and "dialog chọn phòng" not in _res["reason"], \
        "mission chọn tập không được FAIL bằng mẫu mission thể thao"
    assert _r.device.keys.count("OK") == 2, \
        "chỉ bấm OK 2 lần (mở dialog, chọn Tập 1), keys: %s" % _r.device.keys
    print("H2_EPISODE_PICKER_PLAYER_IS_NOT_FAIL_OK")


if __name__ == "__main__":
    sys.exit(main())

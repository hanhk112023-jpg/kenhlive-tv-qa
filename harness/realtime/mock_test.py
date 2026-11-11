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
    assert a_6c.rule == "open_player", \
        "không có thẻ LIVE thì hành vi cũ (OK) — không được chặn mission"
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
    # Không đọc được đồng hồ (unknown) -> KHÔNG chặn PASS (giới hạn đo đã ghi rõ).
    _seq_un = [(float(i * 10), None) for i in range(1, 11)]
    _gu = _gate_pb(_seq_un)
    assert _gu.playback_status() == "unknown"
    _vu, _ru, _ = _gu.evaluate("step_010.jpg")
    print("playback unknown ->", _vu, "|", _ru)
    assert _vu == "PASS"
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
    # without response' — gọi lại ngay sau đó thì thành công 2/3 lần. Retry
    # 2s cũ không đủ; giờ thử lại tối đa 2 lần nữa, backoff 2s rồi 10s.
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
        if _calls["n"] <= 2:
            raise _httpc.RemoteDisconnected("Remote end closed connection without response")
        return _FakeResp()

    assert _vis._is_transport_error(_httpc.RemoteDisconnected("Remote end closed connection without response"))
    assert not _vis._is_transport_error(ValueError("boom"))
    # _post lên URL NIM sẽ acquire() slot của LIMITER toàn cục — snapshot và
    # khôi phục sau test để không làm bẩn số đếm của test F (no-vision).
    from ratelimit import LIMITER as _LIM
    _lim_req, _lim_stamps = _LIM.requests, list(_LIM._stamps)
    _vis._TRANSPORT_BACKOFF_S = (0.05, 0.05)
    _urlreq.urlopen = _flaky_urlopen
    try:
        out11 = _vis._post(_vis.NVIDIA_NIM_BASE, "",
                           {"model": "x", "messages": []}, timeout=5)
    finally:
        _urlreq.urlopen = _orig_urlopen
        _vis._TRANSPORT_BACKOFF_S = _orig_backoff
    print("vision transport retry: urlopen calls", _calls["n"], "->", out11)
    assert _calls["n"] == 3, "lỗi transport phải thử lại tới lần thứ 3"
    assert out11 == '{"found": true}', "lần thứ 3 thành công thì phải trả nội dung"
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


if __name__ == "__main__":
    sys.exit(main())

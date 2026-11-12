#!/usr/bin/env python3
"""KenhLive Realtime QA — driver điều hướng (policy xác định, không kịch bản).

Chọn MỘT hành động theo trạng thái hiện tại. Không vision trong policy, trừ
đường thoát kẹt duy nhất (§6 DESIGN.md). Không có action COMPLETE — chỉ gate
mới kết luận mission. Ghi lại rule đã chọn cho mỗi quyết định để replay được.
"""
import hashlib
import re
from datetime import datetime, timedelta, timezone

MAX_STUCK_LEVELS = 2      # kẹt 2 lần -> FAIL mission
NO_CHANGE_STEPS = 3       # 3 bước không đổi trạng thái = kẹt 1 cấp
# CI-T9 nhóm B mục (3): mission cần trận đang đá được quét tối đa 6 bước
# (bỏ qua thẻ SẮP ĐÁ / cuộn xuống tìm thẻ LIVE) mà không thấy thẻ LIVE
# nào thì kết luận run không có trận đang đá để mở (NO_LIVE_TARGET —
# runner đổi thành UNVERIFIED vì spec có requires_live_row).
_LIVE_SCAN_MAX = 6
# Band nav (y < 140 theo 1080p, CI-T9 mục 3): nhãn nav 'TRỰC TIẾP' không
# phải badge của thẻ trận — không được tính là thẻ LIVE.
_NAV_BAND_Y = 140
# Giờ app hiển thị theo GMT+7 (lịch thi đấu, giờ kickoff).
_GMT7 = timezone(timedelta(hours=7))


def _texts_hash(visible_texts):
    blob = "|".join(t for _, t in (visible_texts or [])[:20])
    return hashlib.md5(blob.encode("utf-8", "ignore")).hexdigest()[:10]


class Action:
    def __init__(self, action_type, action_param="", rule="", thought=""):
        self.type = action_type
        self.param = action_param
        self.rule = rule
        self.thought = thought

    def as_dict(self):
        return {"action_type": self.type, "action_param": self.param,
                "rule": self.rule, "thought": self.thought}


class Driver:
    """Policy: directed launch -> tới đích trực tiếp -> khám phá có hướng -> thoát kẹt."""

    def __init__(self, device, gate, mission, vision=None, now_fn=None):
        self.device = device
        self.gate = gate
        self.mission = mission
        self.vision = vision
        # CI-T9 nhóm B mục (3): đồng hồ chích được cho test (trả datetime
        # theo GMT+7). Mặc định: giờ thật theo GMT+7.
        self._now_fn = now_fn
        # Số bước đã đi qua mà chưa thấy thẻ LIVE nào trong mission cần
        # trận đang đá (quét xuống + bỏ qua thẻ SẮP ĐÁ đều tính).
        self._no_live_steps = 0
        self._state_hist = []      # (focused_sig, texts_hash, activity)
        self._stuck_level = 0
        self._vision_assist_used = False
        self._local_unstick_tried = False  # CI-T8 mục 4: kẹt lần 1 thử thoát
        # cục bộ (DPAD_DOWN, ~9s) trước khi tốn vision-assist (~58s/call)
        self._explore_idx = 0
        self._last_action = None
        self._no_change_streak = 0
        self._revisit_streak = 0  # số lần quay lại cùng state trong 6 bước gần nhất (A-B-A-B)
        self._dismiss_tries = 0    # số lần thử đóng dialog chặn trong mission
        self._webplayer_waited = False      # đã WAIT 1 lần chờ WebPlayer phát chưa
        self._webplayer_play_pressed = False  # đã bấm Play 1 lần trong WebPlayer chưa
        self._long_press_tried = False  # đã long-press yêu thích 1 lần chưa (CI-T5 mục 10)
        self._keyboard_open_tries = 0  # CI-T9 mục 7: số lần OK mở bàn phím (tối đa 2)
        self._keyboard_typed = False  # CI-T9 mục 7: đã gõ từ khóa khi bàn phím mở chưa
        self._seek_idx = 0  # H3: đếm bước quét tìm text mục tiêu (goto_texts)

    def _state_sig(self, ui_state, activity):
        return (ui_state.get("focused_sig", "NONE"),
                _texts_hash(ui_state.get("all_visible_texts")),
                activity or "?")

    def note_state(self, ui_state, activity, motion_playing=False):
        """Gọi sau mỗi observation: cập nhật streak không đổi trạng thái.
        Video đang phát TRONG PLAYER: UI không đổi là BÌNH THƯỜNG (phim chạy,
        không cần bấm gì) — reset streak về 0, nếu không mission player nào
        cũng FAIL oan vì 'kẹt' dù video đang chạy (bài học CI-T2: WebPlayer
        directed FAIL kẹt cấp 2 ở bước 8 dù video phát). Video đứng yên
        (motion False) thì kẹt vẫn tính như thường. Ngoài player, motion vẫn
        tính kẹt bình thường (hero preview nhỏ không che được UI đổi).
        CI-T5: motion_playing=None = UNKNOWN (watcher đói mẫu, chưa đo được
        — CI-T4 VOD FAIL oan: phim phát thật nhưng motion None cả 9 bước
        trong lúc dump WebPlayer 26.6s). Trong player, UNKNOWN KHÔNG được
        tính vào streak kẹt (không tăng, không reset — chỉ ghi sig vào lịch
        sử); ngoài player None xử như False (hành vi cũ)."""
        act = activity or ""
        is_player = "PlayerActivity" in act or "WebPlayerActivity" in act
        # CI-T8 mục 6: đang gõ bàn phím = trạng thái ĐANG ĐỔI (phím nhấn,
        # highlight di chuyển) — dump có thể không đổi vì bàn phím in-app
        # mù với uiautomator, nhưng màn hình vẫn đang tương tác. Reset
        # streak kẹt (như video đang phát trong player), nếu không STRESS
        # gõ phím FAIL oan vì "kẹt" (CI-T7). Check cả dump lẫn ảnh.
        if ui_state.get("keyboard_open") or ui_state.get("keyboard_open_image"):
            self._no_change_streak = 0
            self._revisit_streak = 0
            sig = self._state_sig(ui_state, activity)
            self._state_hist.append(sig)
            if len(self._state_hist) > 12:
                self._state_hist.pop(0)
            return
        if motion_playing is None and is_player:
            sig = self._state_sig(ui_state, activity)
            self._state_hist.append(sig)
            if len(self._state_hist) > 12:
                self._state_hist.pop(0)
            return
        if motion_playing and is_player:
            self._no_change_streak = 0
            self._revisit_streak = 0
            sig = self._state_sig(ui_state, activity)
            self._state_hist.append(sig)
            if len(self._state_hist) > 12:
                self._state_hist.pop(0)
            return
        sig = self._state_sig(ui_state, activity)
        if self._state_hist and self._state_hist[-1] == sig:
            self._no_change_streak += 1
        else:
            self._no_change_streak = 0
        # Luân phiên A-B-A-B (CI-T4, reviewer): focused_sig đổi mỗi bước nên
        # streak không tăng, nhưng màn hình không đổi — CI-T3 EPISODE_PICKER
        # nhảy btnHeroBackHome <-> heroPlay qua lại mà không bao giờ bị tính
        # kẹt. Cùng state xuất hiện lại trong 6 state gần nhất (không phải
        # lặp liên tiếp) = 1 lần quay lại; 2 lần quay lại = kẹt (vision-assist
        # hoặc FAIL). Một lần quay lại đơn (VD bấm BACK về chỗ cũ) chưa đủ.
        if sig in self._state_hist[-6:] and (not self._state_hist or self._state_hist[-1] != sig):
            self._revisit_streak += 1
        else:
            self._revisit_streak = 0
        self._state_hist.append(sig)
        if len(self._state_hist) > 12:
            self._state_hist.pop(0)

    def stuck(self):
        return self._no_change_streak >= NO_CHANGE_STEPS or self._revisit_streak >= 2

    def _focused_card_texts(self, ui_state):
        """Text ứng viên của thẻ đang focus (dùng cho _focused_card_status
        và _kickoff_passed_today). Thứ tự: (1) bounds: text của node giao
        nhau / tâm nằm trong bounds focus mở rộng 40px; (2) cửa sổ ±10 node
        quanh node focus, tìm theo id rồi theo focused_text; (3) text của
        chính view đang focus."""
        texts = ui_state.get("all_visible_texts") or []
        if not texts:
            return []
        cands = []
        fb = ui_state.get("focused_bounds")
        nodes = ui_state.get("all_visible_nodes") or []
        if fb and nodes:
            m = re.findall(r"-?\d+", fb)
            if len(m) >= 4:
                fx1, fy1, fx2, fy2 = map(int, m[:4])
                ex1, ey1, ex2, ey2 = fx1 - 40, fy1 - 40, fx2 + 40, fy2 + 40
                for n in nodes:
                    nm = re.findall(r"-?\d+", n.get("bounds") or "")
                    if len(nm) < 4:
                        continue
                    x1, y1, x2, y2 = map(int, nm[:4])
                    cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
                    if (ex1 <= cx <= ex2 and ey1 <= cy <= ey2) or \
                       (x1 < ex2 and x2 > ex1 and y1 < ey2 and y2 > ey1):
                        cands.append((n.get("text") or "").lower())
        if not cands:
            fsig = ui_state.get("focused_sig", "")
            fid = fsig.split("#")[0] if fsig else ""
            idx = next((i for i, (r, _) in enumerate(texts) if r == fid), None) \
                if fid else None
            if idx is None:
                ftxt = (ui_state.get("focused_text") or "").strip().lower()
                if ftxt:
                    idx = next((i for i, (_, t) in enumerate(texts)
                                if (t or "").strip().lower() == ftxt), None)
            if idx is not None:
                lo, hi = max(0, idx - 10), min(len(texts), idx + 11)
                cands = [t.lower() for _, t in texts[lo:hi]]
        _ft = (ui_state.get("focused_text") or "").lower()
        if _ft:
            cands.append(_ft)
        return cands

    def _focused_card_status(self, ui_state):
        """Trạng thái thẻ trận đang focus: 'live' | 'upcoming' | None.
        CI-T5 mục 3 (CI-T4 PLAYER_STREAMING FAIL A-B-A-B): driver mở thẻ
        [SẮP ĐÁ] ĐTQ Việt Nam 19:00 (chưa đá) -> player 'Đang tải luồng...'
        vô hạn -> tự thoát -> mở lại -> dao động. Chỉ mở thẻ LIVE.
        CI-T6 mục 5: luật này mở rộng cho MỌI mission mở player/dialog
        (kể cả ROOM_PICKER — CI-T5 step_013/014 vẫn mở thẻ INTERF [SẮP ĐÁ]
        vì _focused_card_status trả None: focus là blvCardRoot nhưng badge
        không gắn được — id node text trong dump khác id view đang focus,
        hoặc badge nằm ngoài cửa sổ ±6 node). Fallback mới, theo thứ tự:
        (1) bounds: badge giao nhau / tâm nằm trong bounds focus mở rộng
        40px; (2) cửa sổ ±10 node quanh node focus, tìm theo id rồi theo
        focused_text; (3) text của chính view đang focus. 'LIVE' khớp theo
        từ nguyên (\\blive\\b) để 'socolive' không bị nhận nhầm."""
        cands = self._focused_card_texts(ui_state)
        if any("sắp đá" in t for t in cands):
            return "upcoming"
        if any(re.search(r"\blive\b", t) or "trực tiếp" in t for t in cands):
            return "live"
        return None

    def _now_gmt7(self):
        """Giờ hiện tại theo GMT+7 (giờ app hiển thị)."""
        if self._now_fn is not None:
            return self._now_fn()
        return datetime.now(_GMT7)

    def _kickoff_passed_today(self, ui_state):
        """Trận focus đã bắt đầu theo GIỜ KICKOFF (khi không có badge):
        cửa sổ thẻ có mốc 'Hôm nay' (hoặc ngày DD/MM đúng hôm nay) + một
        giờ kickoff 'HH:MM' đã qua so với giờ hiện tại (GMT+7). CHỈ dùng
        hướng khẳng định, và KHÔNG dùng khi cửa sổ có 'SẮP ĐÁ' (tin badge:
        trận hoãn vẫn chưa đá dù giờ đã qua) hay 'Ngày mai' (giờ ngày mai
        đã qua không có nghĩa là đã đá). Không có mốc ngày thì không kết
        luận (giờ '21:00' không rõ hôm nay hay ngày mai)."""
        cands = self._focused_card_texts(ui_state)
        if any("sắp đá" in t for t in cands):
            return False
        if any("ngày mai" in t for t in cands):
            return False
        now = self._now_gmt7()
        is_today = any("hôm nay" in t for t in cands)
        if not is_today:
            for t in cands:
                dm = re.match(r"^(\d{1,2})/(\d{1,2})$", (t or "").strip())
                if dm and int(dm.group(1)) == now.day \
                        and int(dm.group(2)) == now.month:
                    is_today = True
                    break
        if not is_today:
            return False
        for t in cands:
            tm = re.match(r"^(\d{1,2}):(\d{2})$", (t or "").strip())
            if not tm:
                continue
            hh, mm = int(tm.group(1)), int(tm.group(2))
            if 0 <= hh < 24 and 0 <= mm < 60 \
                    and (hh, mm) <= (now.hour, now.minute):
                return True
        return False

    def _focus_inside_live_card(self, ui_state):
        """Focus đang nằm trong bounds một thẻ chứa badge LIVE/TRỰC TIẾP
        (đường bounds — khi badge không gắn được qua _focused_card_status
        vì id node/khoảng cách). Badge vùng nav (tâm y < 140) không tính:
        nhãn nav 'TRỰC TIẾP' không phải thẻ trận."""
        nodes = ui_state.get("all_visible_nodes") or []
        fb = ui_state.get("focused_bounds")
        if not nodes or not fb:
            return False
        fm = re.findall(r"-?\d+", fb)
        if len(fm) < 4:
            return False
        fcx = (int(fm[0]) + int(fm[2])) // 2
        fcy = (int(fm[1]) + int(fm[3])) // 2
        _card_ids = ("cardroot", "schedcard", "blvcardroot", "livecard", "channelcard")
        for n in nodes:
            t = (n.get("text") or "").lower()
            if not (re.search(r"\blive\b", t) or "trực tiếp" in t):
                continue
            nb = re.findall(r"-?\d+", n.get("bounds") or "")
            if len(nb) < 4:
                continue
            bx, by = (int(nb[0]) + int(nb[2])) // 2, (int(nb[1]) + int(nb[3])) // 2
            if by < _NAV_BAND_Y:
                continue  # badge vùng nav — không phải thẻ trận
            barea = (int(nb[2]) - int(nb[0])) * (int(nb[3]) - int(nb[1]))
            cands = []
            for n2 in nodes:
                nb2 = re.findall(r"-?\d+", n2.get("bounds") or "")
                if len(nb2) < 4:
                    continue
                x1, y1, x2, y2 = map(int, nb2[:4])
                if not (x1 <= bx <= x2 and y1 <= by <= y2):
                    continue
                area = (x2 - x1) * (y2 - y1)
                if area <= barea:
                    continue
                prio = 0 if (n2.get("id") or "").lower() in _card_ids else 1
                cands.append((prio, area, (x1, y1, x2, y2)))
            if not cands:
                continue
            cands.sort()
            card = cands[0][2]
            if card[0] <= fcx <= card[2] and card[1] <= fcy <= card[3]:
                return True
        return False

    def _needs_live_target(self):
        """Mission chỉ được mở trận ĐANG ĐÁ: mission cần player VÀ spec
        đánh dấu requires_live_row (CI-T9 nhóm B mục (3) — hiện chỉ
        MISSION_PLAYER_STREAMING_AND_CONTROLS; SCHEDULE_LIVE_DIRECTED cũng
        có cờ này nhưng không mở player nên không lọt). IPTV_EPG mở kênh
        (không phải trận) nên không bị chặn."""
        m = self.mission
        return (getattr(m, "requires_live_row", False)
                and m.required_activity == "PlayerActivity"
                and not m.directed_launch)

    def _is_confirmed_live_target(self, ui_state):
        """Focus có chắc chắn là trận ĐANG ĐÁ không (để mở player):
        (a) badge LIVE/TRỰC TIẾP gắn được với thẻ focus; (b) focus nằm
        trong bounds thẻ chứa badge LIVE; (c) giờ kickoff hôm nay đã qua.
        Focus ở nav (nav_*) không bao giờ là thẻ trận — nhãn nav
        'TRỰC TIẾP' từng làm _focused_card_status trả 'live' oan."""
        if (ui_state.get("focused_sig") or "").startswith("nav"):
            return False
        if self._focused_card_status(ui_state) == "live":
            return True
        if self._focus_inside_live_card(ui_state):
            return True
        return self._kickoff_passed_today(ui_state)

    def _goto_live_card_action(self, ui_state):
        """Đi tới thẻ LIVE gần nhất theo id/bounds (CI-T6 mục 6): mission cần
        player mà đang ở list thì tìm thẻ có badge LIVE rồi đi theo hướng tới
        nó, thay vì bấm OK mù trên thẻ đang focus (CI-T5 PLAYER_STREAMING
        lang thang ở list, vision chối 2 lần vì chưa bao giờ vào player).
        Trả Action DPAD theo hướng, hoặc None: không thấy thẻ LIVE, hoặc
        focus đã nằm trong bounds thẻ LIVE (caller bấm OK như thường).
        Thẻ = node nhỏ nhất chứa tâm badge (diện tích lớn hơn badge),
        ưu tiên id thẻ quen thuộc.
        CI-T7 mục 2: CẤM khi dialog/panel đang mở (has_dialog) — luật này
        từng đuổi theo badge LIVE ở list NỀN sau overlay (CI-T6: chạy 4 lần
        nhưng sai trạng thái, dao động dialog↔list) thay vì bấm OK trên
        phòng đang focus. Khi panel đã mở, caller phải bấm OK (open_player)
        trên phòng đang focus, không được đi tìm thẻ khác."""
        if ui_state.get("has_dialog"):
            return None
        nodes = ui_state.get("all_visible_nodes") or []
        if not nodes:
            return None
        badges = []
        for n in nodes:
            t = (n.get("text") or "").lower()
            if re.search(r"\blive\b", t) or "trực tiếp" in t:
                nb = re.findall(r"-?\d+", n.get("bounds") or "")
                if len(nb) < 4:
                    continue
                # CI-T9 nhóm B mục (3): nhãn nav 'TRỰC TIẾP' (tâm y <
                # 140) không phải badge của thẻ trận — bỏ qua, không đuổi
                # theo nav thay vì đi xuống thẻ LIVE thật.
                if (int(nb[1]) + int(nb[3])) // 2 < _NAV_BAND_Y:
                    continue
                badges.append((n, tuple(map(int, nb[:4]))))
        if not badges:
            return None
        _card_ids = ("cardroot", "schedcard", "blvcardroot", "livecard", "channelcard")
        for _bn, bb in badges:
            bx, by = (bb[0] + bb[2]) // 2, (bb[1] + bb[3]) // 2
            cands = []
            for n in nodes:
                nb = re.findall(r"-?\d+", n.get("bounds") or "")
                if len(nb) < 4:
                    continue
                x1, y1, x2, y2 = map(int, nb[:4])
                if not (x1 <= bx <= x2 and y1 <= by <= y2):
                    continue
                area = (x2 - x1) * (y2 - y1)
                barea = (bb[2] - bb[0]) * (bb[3] - bb[1])
                if area <= barea:
                    continue
                prio = 0 if (n.get("id") or "").lower() in _card_ids else 1
                cands.append((prio, area, (x1, y1, x2, y2)))
            if not cands:
                continue
            cands.sort()
            card = cands[0][2]
            # focus đã nằm trong thẻ LIVE này -> để caller bấm OK
            fb = ui_state.get("focused_bounds")
            if fb:
                fm = re.findall(r"-?\d+", fb)
                if len(fm) >= 4:
                    fcx = (int(fm[0]) + int(fm[2])) // 2
                    fcy = (int(fm[1]) + int(fm[3])) // 2
                    if card[0] <= fcx <= card[2] and card[1] <= fcy <= card[3]:
                        return None
            cx = (card[0] + card[2]) // 2
            cy = (card[1] + card[3]) // 2
            d = self._direction_to(ui_state, cx, cy)
            if d is None:
                return None  # đã kề tâm thẻ -> caller bấm OK
            key, dx, dy = d
            return Action("KEY", key, rule="goto_live_card",
                          thought="Đi tới thẻ LIVE (%s, lệch %d,%d)" % (key, dx, dy))
        return None

    def _direction_to(self, ui_state, tx, ty):
        """Phím D-pad đi từ focus hiện tại tới điểm đích (tx, ty) theo bounds.
        Trả (key, dx, dy) hoặc None khi đã ở ngay trên đích / không có bounds.
        Trục lệch lớn hơn quyết định hướng."""
        fb = ui_state.get("focused_bounds")
        if not fb:
            return None
        m = re.findall(r"-?\d+", fb)
        if len(m) < 4:
            return None
        fx1, fy1, fx2, fy2 = map(int, m[:4])
        fcx, fcy = (fx1 + fx2) // 2, (fy1 + fy2) // 2
        dx, dy = tx - fcx, ty - fcy
        if abs(dx) < 30 and abs(dy) < 30:
            return None  # đã ở ngay trên đích — để luật khác bấm OK
        if abs(dy) >= abs(dx):
            return ("DPAD_DOWN" if dy > 0 else "DPAD_UP", dx, dy)
        return ("DPAD_RIGHT" if dx > 0 else "DPAD_LEFT", dx, dy)

    def _goto_view_action(self, ui_state, view_ids):
        """Đi tới view đích theo id (CI-T5 mục 9): nếu view đã có trong dump
        (all_visible_nodes có bounds) thì đi theo hướng từ focus tới nó, thay
        vì explore mù (CI-T4 EPISODE_PICKER đi lạc về Home trong khi nút đích
        hiện ngay trên màn hình). Trả Action hoặc None (view chưa thấy / đã
        đứng trên view -> caller dùng luật khác)."""
        nodes = {n.get("id"): n for n in (ui_state.get("all_visible_nodes") or [])}
        for vid in view_ids:
            n = nodes.get(vid)
            if not n:
                continue
            nb = re.findall(r"-?\d+", n.get("bounds") or "")
            if len(nb) < 4:
                continue
            x1, y1, x2, y2 = map(int, nb[:4])
            d = self._direction_to(ui_state, (x1 + x2) // 2, (y1 + y2) // 2)
            if d is None:
                return None
            key, dx, dy = d
            return Action("KEY", key, rule="goto_view",
                          thought="Đi tới view đích %s (%s, lệch %d,%d)"
                                  % (vid, key, dx, dy))
        return None

    def _goto_text_action(self, ui_state, texts):
        """Đi tới nút đích theo nhãn text (VD 'CHỌN TẬP'): tìm node có text
        chứa nhãn (không phân biệt hoa/thường) rồi đi theo hướng bounds.
        Trả Action hoặc None (nhãn chưa thấy / đã đứng trên nút)."""
        wants = [t.lower() for t in (texts or [])]
        if not wants:
            return None
        for n in (ui_state.get("all_visible_nodes") or []):
            txt = (n.get("text") or "").lower()
            if not any(w in txt for w in wants):
                continue
            nb = re.findall(r"-?\d+", n.get("bounds") or "")
            if len(nb) < 4:
                continue
            x1, y1, x2, y2 = map(int, nb[:4])
            d = self._direction_to(ui_state, (x1 + x2) // 2, (y1 + y2) // 2)
            if d is None:
                return None
            key, dx, dy = d
            return Action("KEY", key, rule="goto_view_text",
                          thought="Đi tới nút '%s' (%s, lệch %d,%d)"
                                  % (n.get("text", "")[:20], key, dx, dy))
        return None

    def _dismiss_dialog_action(self, ui_state):
        """Trả Action đóng dialog chặn, hoặc None nếu không phải dialog chặn.
        Dialog chào mừng 'THÔNG BÁO' lần đầu (btnCloseFeedback) chặn MỌI
        mission — phải đóng trước, kể cả mission cần dialog (nó không phải
        dialog đích, và gate sẽ tính pass giả nếu để nó mở — bài học CI-T1:
        harness cũ bấm OK trên btnCloseFeedback ở bước 1, driver mới không
        có luật này nên 16/17 mission kẹt)."""
        if not ui_state.get("has_dialog"):
            self._dismiss_tries = 0
            return None
        dialog_ids = ui_state.get("dialog_ids") or []
        is_welcome = "btnCloseFeedback" in dialog_ids
        if not is_welcome and self.mission.needs_dialog:
            return None  # có thể là dialog đích — để nguyên
        # CI-T7 mục 2: panel chi tiết trận (MatchDetailPanel) KHÔNG phải
        # dialog chặn khi mission cần player — nó là ĐƯỜNG VÀO player: OK
        # trên phòng đang focus mở thẳng player (onPlayRoom). Đóng nó bằng
        # BACK rồi đuổi badge LIVE ở list nền là đúng lỗi A-B-A-B của CI-T6
        # (rule 0c2 chạy 4 lần sai trạng thái). Để nguyên cho luật 0c bấm OK.
        _is_panel = any((d or "").startswith("panel") or d == "blvCardRoot"
                        for d in dialog_ids)
        if _is_panel and self.mission.required_activity in (
                "PlayerActivity", "WebPlayerActivity"):
            return None
        if self._dismiss_tries >= 3:
            return Action("FAIL", "", rule="dialog:blocked",
                          thought="Dialog chặn vẫn mở sau 3 lần đóng thử")
        self._dismiss_tries += 1
        focused_text = (ui_state.get("focused_text") or "").lower()
        focused_sig = ui_state.get("focused_sig", "")
        if any(k in focused_text for k in ("đã hiểu", "đóng", "ok", "bỏ qua", "hủy")) \
                or "close" in focused_sig.lower():
            return Action("KEY", "OK", rule="dismiss_dialog_ok",
                          thought="Đóng dialog chặn bằng OK trên '%s'" % focused_text[:30])
        return Action("KEY", "BACK", rule="dismiss_dialog_back",
                      thought="Đóng dialog chặn bằng BACK")

    def next_action(self, ui_state, activity, frame_png, t_offset):
        """Trả Action hoặc ('FAIL', reason) khi driver quyết định dừng mission."""
        m, gate = self.mission, self.gate
        focused_sig = ui_state.get("focused_sig", "NONE")
        focused_text = (ui_state.get("focused_text") or "").lower()
        act = activity or ""

        # -- 0. Dialog chặn: đóng trước mọi thứ (kể cả trước luật kẹt).
        dismiss = self._dismiss_dialog_action(ui_state)
        if dismiss is not None:
            return dismiss

        # -- 0b. Kẹt: thoát cục bộ lần 1, vision lần 2, FAIL lần 3.
        if self.stuck():
            # CI-T8 mục 4 (tốc độ): vision latency trung bình 57,9s/call là
            # nút thắt (11 call = 637,2s) — kẹt lần 1 thử thoát CỤC BỘ
            # (DPAD_DOWN, ~9s) trước; chỉ tốn vision khi vẫn kẹt sau đó.
            # Kẹt thật (A-B-A-B / đứng yên thật) thì vision vẫn chạy ở lần 2.
            if not self._local_unstick_tried:
                self._local_unstick_tried = True
                self._no_change_streak = 0
                self._revisit_streak = 0
                return Action("KEY", "DPAD_DOWN", rule="stuck:local_unstick",
                              thought="Kẹt lần 1: thử DPAD_DOWN cục bộ trước khi tốn vision")
            if not self._vision_assist_used and self.vision is not None and self.vision.available() \
                    and self.vision.remaining() > 0 and frame_png:
                self._vision_assist_used = True
                self._stuck_level = 1
                tried = ", ".join(self.device.action_history[-4:]) or "chưa bấm gì"
                res, err = self.vision.stuck_assist(frame_png, m.target_desc, tried)
                if res and res.get("action") in ("KEY", "SWITCH_TAB", "BACK") and res.get("param"):
                    self._no_change_streak = 0
                    return Action(res["action"], res["param"], rule="stuck:vision_assist",
                                  thought="Kẹt, vision gợi ý %s %s" % (res["action"], res["param"]))
            self._stuck_level = 2
            if self._revisit_streak >= 2:
                thought = "Kẹt cấp 2: luân phiên qua lại cùng trạng thái (A-B-A-B), màn hình không tiến triển"
            else:
                thought = "Kẹt cấp 2: %d bước liên tiếp không đổi trạng thái" % NO_CHANGE_STEPS
            return Action("FAIL", "", rule="stuck:level2", thought=thought)

        # -- 0b. Sai tab: mission khai tab đích mà đang ở tab khác -> chuyển tab.
        # (Runner đã reset tab đầu mission; luật này là lưới an toàn khi BACK
        # hoặc điều hướng làm lạc tab giữa chừng.)
        if m.tab is not None:
            cur_tab = self.device.detect_tab_index(ui_state)
            if cur_tab is not None and cur_tab != m.tab:
                return Action("SWITCH_TAB", str(m.tab), rule="goto_tab",
                              thought="Đang ở tab %s, mission cần tab %s" % (cur_tab, m.tab))

        # -- 0b2. Mission cần bàn phím thật (CI-T9 mục 7, SEARCH): CI-T8 bàn
        # phím không mở lần nào ở cả 95 bước vì driver chưa từng bấm OK trên
        # ô tìm kiếm — focus tới searchInput (step_079 T4) rồi bỏ đi xuống
        # hàng xu hướng. Luật này: focus đang ở ô nhập -> bấm OK mở bàn phím
        # in-app (tối đa 2 lần); ô nhập hiện trong dump mà chưa focus -> đi
        # tới nó; bàn phím đã mở -> gõ từ khóa qua adb input (TEXT). Bàn phím
        # không mở thì runner đánh UNVERIFIED ở cuối mission (không PASS lặng).
        if m.needs_keyboard and "PlayerActivity" not in act \
                and "WebPlayerActivity" not in act:
            _kb_open = bool(ui_state.get("keyboard_open")
                            or ui_state.get("keyboard_open_image"))
            if _kb_open:
                if not self._keyboard_typed:
                    self._keyboard_typed = True
                    return Action("TEXT", "uefa", rule="keyboard:type",
                                  thought="Bàn phím đã mở — gõ từ khóa 'uefa' qua adb input")
            elif self._keyboard_open_tries < 2:
                _fid = (focused_sig.split("#")[0] or "").lower()
                if "search" in _fid or "tìm" in focused_text or "nhập" in focused_text:
                    self._keyboard_open_tries += 1
                    return Action("KEY", "OK", rule="keyboard:open",
                                  thought="Bấm OK trên ô tìm kiếm để mở bàn phím thật")
                _goto_kb = self._goto_view_action(
                    ui_state, ["searchInput", "edtSearch", "etSearch"])
                if _goto_kb is not None:
                    _goto_kb.rule = "keyboard:goto_input"
                    return _goto_kb

        # -- 0d. Thẻ đang focus là trận CHƯA ĐÁ thì không mở player/dialog từ
        # nó: tìm thẻ LIVE khác (CI-T5 mục 3). CI-T6 mục 5: mở rộng sang MỌI
        # mission (trước đây chỉ mission sẽ bấm OK mở player/dialog) — trận
        # INTERF 19:00 ở ROOM_PICKER step_013/014 CI-T5 đã vào player loading
        # vô hạn + tiêu đề 'null · VIE - CHI' vì thẻ [SẮP ĐÁ] không bị chặn
        # khi mission không thuộc nhóm cũ.
        if "PlayerActivity" not in act and "WebPlayerActivity" not in act \
                and not ui_state.get("has_dialog"):
            if self._focused_card_status(ui_state) == "upcoming":
                # CI-T9 nhóm B mục (3): mission cần trận đang đá mà bỏ qua
                # quá nhiều thẻ SẮP ĐÁ liên tiếp không gặp thẻ LIVE nào thì
                # kết luận run không có trận đang đá để mở (NO_LIVE_TARGET),
                # thay vì đốt hết 8 bước rồi FAIL oan.
                if self._needs_live_target():
                    self._no_live_steps += 1
                    if self._no_live_steps > _LIVE_SCAN_MAX:
                        return Action("FAIL", "", rule="no_live_target",
                                      thought="Bỏ qua %d thẻ [SẮP ĐÁ] liên tiếp mà "
                                              "không gặp thẻ LIVE nào — run không có "
                                              "trận đang đá để mở, chưa kiểm được "
                                              "(UNVERIFIED)" % _LIVE_SCAN_MAX)
                return Action("KEY", "DPAD_DOWN", rule="skip_upcoming_card",
                              thought="Thẻ đang focus là trận [SẮP ĐÁ] (chưa đá) — "
                                      "bỏ qua, tìm thẻ LIVE để mở")

        # -- 0c2. Mission cần player mà đang ở list: đi tới thẻ LIVE rồi mới
        # bấm OK (CI-T6 mục 6; như goto-view-by-id của EPISODE_PICKER).
        # CI-T7 mục 2: gate bằng `not has_dialog` — dialog/panel đang mở
        # (VD MatchDetailPanel đã mở, focus trên blvCardRoot) thì KHÔNG đuổi
        # theo badge LIVE ở list nền sau overlay; rơi xuống luật 0c bấm OK
        # trên phòng đang focus (đường open_player hiện có).
        if (m.required_activity in ("PlayerActivity", "WebPlayerActivity")
                or m.needs_dialog) \
                and not m.directed_launch \
                and "PlayerActivity" not in act \
                and "WebPlayerActivity" not in act \
                and not ui_state.get("has_dialog"):
            goto_live = self._goto_live_card_action(ui_state)
            if goto_live is not None:
                return goto_live

        # -- 0c3. Mission cần trận đang đá mà goto_live không tìm thấy thẻ
        # LIVE nào trong dump (không có badge LIVE, hoặc focus đã đứng trên
        # thẻ LIVE — trường hợp sau đã được xác nhận ở dưới): TUYỆT ĐỐI
        # không bấm OK mù trên focus chưa xác nhận (CI-T9 Thử 3: step_016/
        # 018 bấm OK trên focus không text '' sau khi player thoát, mở nhầm
        # KUW–SYR đá ngày mai). Cuộn xuống tìm thẻ LIVE; quét hết lượt mà
        # không thấy thì FAIL NO_LIVE_TARGET — runner đổi thành UNVERIFIED
        # khi run không có hàng LIVE nào (spec requires_live_row). Panel đã
        # mở (has_dialog) thì không áp: trận đã được chọn lúc mở panel, OK
        # trên phòng đang focus là đường vào player (luật 0c như cũ).
        if self._needs_live_target() \
                and "PlayerActivity" not in act \
                and "WebPlayerActivity" not in act \
                and not ui_state.get("has_dialog"):
            if not self._is_confirmed_live_target(ui_state):
                self._no_live_steps += 1
                if self._no_live_steps > _LIVE_SCAN_MAX:
                    return Action("FAIL", "", rule="no_live_target",
                                  thought="Không thấy thẻ trận LIVE/TRỰC TIẾP nào "
                                          "sau %d bước quét — run không có trận "
                                          "đang đá để mở, chưa kiểm được "
                                          "(UNVERIFIED)" % _LIVE_SCAN_MAX)
                return Action("KEY", "DPAD_DOWN", rule="scan_live_card",
                              thought="Chưa thấy thẻ LIVE — cuộn xuống tìm trận "
                                      "đang đá, không mở trận chưa xác nhận")

        # -- 0c. Mission cần player mà đang ở màn chính -> bấm OK mở player.
        # (Không áp dụng mission directed_launch — launch đã mở sẵn player.)
        # CI-T9 nhóm B mục (3): mission cần trận đang đá chỉ tới đây khi
        # focus ĐÃ xác nhận là trận đang đá (luật 0c3 chặn mọi trường hợp
        # khác) — OK mù trên focus '' / thẻ chưa xác nhận đã bị loại.
        if m.required_activity in ("PlayerActivity", "WebPlayerActivity") \
                and not m.directed_launch \
                and "PlayerActivity" not in act and "WebPlayerActivity" not in act:
            if focused_sig != "NONE":
                return Action("KEY", "OK", rule="open_player",
                              thought="Mở player từ '%s'" % focused_text[:30])

        # -- 1b. Mission có nút đích mở dialog (VD 'CHỌN TẬP'): đi tới đúng
        # nút đó trước khi bấm OK (CI-T5 mục 9). Focus chưa đứng trên nút thì
        # đi theo hướng bounds; đã đứng trên nút (goto trả None) thì rơi
        # xuống luật 1 bấm OK như thường.
        if m.needs_dialog and not ui_state.get("has_dialog") and m.goto_texts:
            goto = self._goto_text_action(ui_state, m.goto_texts)
            if goto is not None:
                return goto

        # -- 1c. Mission cần long-press yêu thích (CI-T5 mục 10, nợ cũ):
        # IPTV favorites chưa từng kiểm tra thật vì driver không bao giờ phát
        # LONG_PRESS (execute đã có sẵn từ đầu nhưng không rule nào dùng).
        # Long-press OK 1 lần/mission trên thẻ đang focus (không phải nav),
        # rồi để gate/driver tiếp tục như thường.
        if m.needs_long_press and not self._long_press_tried:
            if focused_sig != "NONE" and not focused_sig.startswith("nav_"):
                self._long_press_tried = True
                return Action("LONG_PRESS", "OK", rule="favorite_long_press",
                              thought="Long-press OK trên '%s' để lưu kênh yêu thích"
                                      % focused_text[:30])

        # -- 1. Mission có dialog đích mà dialog chưa mở: bấm OK trên focused.
        if m.needs_dialog and not ui_state.get("has_dialog"):
            if focused_sig != "NONE":
                return Action("KEY", "OK", rule="open_dialog",
                              thought="Mở dialog đích từ '%s'" % focused_text[:30])

        # -- 2. Mục tiêu là một view đích (VD railPanel): di chuyển tới nó.
        if m.required_views and not (set(m.required_views) & gate.views_seen):
            if "rail" in m.name.lower():
                return Action("KEY", "DPAD_LEFT", rule="open_rail",
                              thought="Mở sidebar rail bằng DPAD_LEFT")
            goto = self._goto_view_action(ui_state, m.required_views)
            if goto is not None:
                return goto
            return Action("KEY", "DPAD_DOWN", rule="seek_view",
                          thought="Đi tìm view đích %s" % m.required_views[0])

        # -- 3. Player mission: vào player thì mở OSD / kiểm tra stream.
        if "PlayerActivity" in act or "WebPlayerActivity" in act:
            if m.needs_motion and not gate.motion_seen:
                if "WebPlayerActivity" in act:
                    # CI-T5 mục 3: WebPlayer đã mở mà video chưa phát thì
                    # đừng chỉ WAIT mãi — WAIT 1 lần cho stream kịp tải,
                    # rồi bấm Play (OK) 1 lần, sau đó lại WAIT (không bấm
                    # Play liên tục kẻo toggle thành Pause).
                    if self._webplayer_waited and not self._webplayer_play_pressed:
                        self._webplayer_play_pressed = True
                        return Action("KEY", "OK", rule="play_webplayer",
                                      thought="WebPlayer đã mở mà video chưa phát — "
                                              "bấm Play (OK) thay vì chỉ chờ")
                    self._webplayer_waited = True
                return Action("WAIT", "2.0", rule="wait_stream",
                              thought="Chờ video tải và chuyển động")
            if focused_sig == "NONE":
                return Action("KEY", "OK", rule="wake_osd",
                              thought="OSD ẩn (focus NONE) — bấm OK gọi OSD lên")
            return Action("KEY", "DPAD_RIGHT", rule="probe_player",
                          thought="Thử điều khiển player (tua/phải)")

        # -- 3b. H3: mission tìm text mục tiêu (goto_texts, không cần dialog)
        # mà gate chưa thấy trong dump thì QUÉT CHÉO DOWN/RIGHT xen kẽ thay
        # vì explore DOWN,DOWN,RIGHT. Trial 5 (run 43183031119): explore cũ
        # dao động A-B-A-B giữa 2 thẻ NBL/JLC (badge 'SOCO') — DPAD_DOWN từ
        # thẻ này lại rơi về thẻ kia nên không bao giờ xuống tới hàng có
        # 'COLA'. Đi chéo (DOWN đổi hàng, RIGHT đổi cột rồi mới DOWN tiếp)
        # thoát được vòng lặp focus hình học đó. Text đã thấy thì không quét
        # nữa (gate sẽ PASS ở observation sau).
        if m.goto_texts and not m.needs_dialog \
                and "PlayerActivity" not in act \
                and "WebPlayerActivity" not in act:
            _want = [t for t in m.goto_texts if t not in gate.texts_seen]
            if _want:
                self._seek_idx += 1
                if self._seek_idx % 2 == 1:
                    return Action("KEY", "DPAD_DOWN", rule="seek_target_text",
                                  thought="Chưa thấy text '%s' trong dump — "
                                          "quét xuống hàng tiếp theo tìm" % _want[0])
                return Action("KEY", "DPAD_RIGHT", rule="seek_target_text",
                              thought="Chưa thấy text '%s' trong dump — "
                                      "đổi cột trong hàng rồi quét xuống tiếp" % _want[0])

        # -- 4. Khám phá có hướng: xen kẽ DOWN / RIGHT, ưu tiên DOWN qua các hàng.
        self._explore_idx += 1
        if self._explore_idx % 3 == 0:
            return Action("KEY", "DPAD_RIGHT", rule="explore:right",
                          thought="Cuộn ngang trong hàng hiện tại")
        return Action("KEY", "DPAD_DOWN", rule="explore:down",
                      thought="Đi xuống hàng/mục tiếp theo")

    def execute(self, action):
        """Thực thi action trên thiết bị. Trả (ok, settle_s)."""
        d = self.device
        t = action.type
        p = action.param or ""
        if t == "KEY":
            key = p.upper()
            if key in ("DOUBLE_BACK", "BACK_DOUBLE", "BACK2"):
                d.send_key("BACK")
                import time as _t
                _t.sleep(0.25)
                d.send_key("BACK")
                _t.sleep(1.2)
                return True, 1.2
            d.send_key(key or "DPAD_DOWN")
            import time as _t
            _t.sleep(0.7)
            self._last_action = "%s %s" % (t, key)
            return True, 0.7
        if t == "LONG_PRESS":
            d.send_long_press(p or "OK")
            import time as _t
            _t.sleep(1.0)
            return True, 1.0
        if t == "KEYPAD":
            d.send_keypad_digits(str(p or "1"))
            import time as _t
            _t.sleep(1.0)
            return True, 1.0
        if t == "SWITCH_TAB":
            try:
                d.switch_tab(int(p))
            except Exception:
                return False, 0.0
            import time as _t
            _t.sleep(1.2)
            return True, 1.2
        if t == "OPEN_HOME":
            d.open_home()
            import time as _t
            _t.sleep(1.8)
            return True, 1.8
        if t == "LAUNCH_WEB_PLAYER":
            d.launch_web_player()
            import time as _t
            _t.sleep(2.5)
            return True, 2.5
        if t == "LAUNCH_VOD_PLAYER":
            d.launch_vod_player()
            import time as _t
            _t.sleep(6.0)
            return True, 6.0
        if t == "TEXT":
            d.input_text(p or "uefa")
            import time as _t
            _t.sleep(0.8)
            return True, 0.8
        if t == "WAIT":
            try:
                import time as _t
                _t.sleep(float(p or "1.5"))
                return True, float(p or "1.5")
            except ValueError:
                import time as _t
                _t.sleep(1.0)
                return True, 1.0
        if t == "FAIL":
            return False, 0.0
        return False, 0.0

#!/usr/bin/env python3
"""KenhLive Realtime QA — evidence gate (lõi sửa false pass).

KHÔNG AI ĐƯỢC QUYỀN COMPLETE_MISSION. Chỉ gate mới kết luận PASS/FAIL.
PASS = mọi tín hiệu áp dụng đều xanh trên chuỗi quan sát gần nhất (+ vision
xác nhận nếu mission yêu cầu). Thiếu tín hiệu khi hết max_steps -> FAIL kèm
bằng chứng. Mission không tới đích thì FAIL to và rõ — không tự hoàn thành.
"""
import time


class MissionSpec:
    """Spec bằng chứng của một mission (không phải kịch bản bước cứng)."""

    def __init__(self, name, title, description, max_steps,
                 required_activity=None, required_texts=None, required_views=None,
                 needs_dialog=False, needs_motion=False, needs_vision=False,
                 target_desc="", directed_launch=None, min_steps=4, kind="target",
                 tab=None, needs_scroll_top=False, goto_texts=None,
                 needs_long_press=False, needs_playback_progress=False,
                 requires_live_row=False, needs_keyboard=False,
                 playback_no_clock=False):
        self.name = name
        self.title = title
        self.description = description
        self.max_steps = int(max_steps)
        self.min_steps = int(min_steps)
        self.required_activity = required_activity
        self.required_texts = [t.lower() for t in (required_texts or [])]
        self.required_views = list(required_views or [])
        self.needs_dialog = bool(needs_dialog)
        self.needs_motion = bool(needs_motion)
        self.needs_vision = bool(needs_vision)
        self.target_desc = target_desc or title
        self.directed_launch = directed_launch
        self.kind = kind  # "target" | "stress"
        # Tab đích trong MainActivity (MainActivity.kt: 6=TRANG CHỦ, 0=TRỰC TIẾP,
        # 1=LỊCH, 2=IPTV, 3=TÌM KIẾM, 4=CÀI ĐẶT, 5=KHO PHIM). None = không cần
        # tab cụ thể; runner reset về MainActivity + tab này đầu mỗi mission
        # (CI-T2: app kẹt trong PlayerActivity từ mission 4, 7 mission sau FAIL
        # oan vì không có luật quay về MainActivity).
        self.tab = tab
        # CI-T5: header text ('Hôm nay', 'tv360') chỉ có ở đầu danh sách —
        # nếu mission trước để lại danh sách đã cuộn xuống, gate đọc text
        # header sẽ FAIL trung thực nhưng oan (CI-T4 DATA_ACCURACY/SCHEDULE/
        # IPTV_CATEGORIES). Runner gửi UP ×N đầu mission này để header hiện
        # trong viewport trước khi gate đọc.
        self.needs_scroll_top = bool(needs_scroll_top)
        # CI-T5 mục 9: nhãn nút mở dialog đích (VD 'CHỌN TẬP' của
        # EPISODE_PICKER) — driver đi tới đúng nút đó theo text/bounds thay
        # vì bấm OK mù trên focus đang đứng (CI-T4: focus lạc về Home trong
        # khi nút CHỌN TẬP hiện ngay trên màn hình).
        self.goto_texts = [t.lower() for t in (goto_texts or [])]
        # CI-T8 mục 7: mission chỉ có ý nghĩa khi run có hàng LIVE thật
        # (detector (e) 'hàng LIVE chỉ hiện giờ kickoff' chỉ kiểm được khi
        # thấy hàng LIVE). Không thấy hàng LIVE -> UNVERIFIED, không FAIL.
        self.requires_live_row = bool(requires_live_row)
        # CI-T9 mục 7: mission chỉ có ý nghĩa khi bàn phím ảo đã mở thật
        # ít nhất 1 lần trong mission (nhập liệu/tìm kiếm bằng bàn phím).
        # Không mở lần nào -> UNVERIFIED (chưa kiểm được), không PASS lặng.
        self.needs_keyboard = bool(needs_keyboard)
        # (IPTV favorites) — driver trước giờ không bao giờ phát LONG_PRESS
        # nên favorites chưa từng được kiểm tra thật.
        self.needs_long_press = bool(needs_long_press)
        # CI-T6 mục 8: mission player PASS phải có bằng chứng thời gian phát
        # TĂNG giữa 2 quan sát (CI-T5 WebPlayer đóng băng 00:20 qua 3 quan
        # sát vẫn PASS). Chỉ bật cho 2 mission VOD có đồng hồ elapsed: live
        # stream (PLAYER_STREAMING, IPTV_EPG) không có elapsed clock có nghĩa
        # nên ép ở đó sẽ FAIL oan — xem DESIGN §15.8 mục 8.
        self.needs_playback_progress = bool(needs_playback_progress)
        # H1 (trial 9 run 43217017298): OSD WebPlayer KHÔNG CÓ đồng hồ
        # elapsed/total nào (step_065, tour t_013–015: chỉ back / pause /
        # "Tua tới 10s" / list / "TỐC ĐỘ 1X" — khác native player có seekbar
        # "00:25 / 45:36"). Mission WebPlayer KHÔNG được đòi đọc đồng hồ
        # không tồn tại: khi không đọc được đồng hồ lần nào (unknown),
        # bằng chứng phát là motion (cảnh đổi giữa 2 frame quan sát — đã
        # bắt buộc riêng qua needs_motion) + vision (đã bắt buộc riêng qua
        # needs_vision). Video đóng băng vẫn FAIL vì motion không bao giờ
        # xanh; đồng hồ NẾU đọc được mà đứng yên / không đơn điệu thì 2
        # nhánh kia vẫn tố như cũ (không đổi).
        self.playback_no_clock = bool(playback_no_clock)


class EvidenceGate:
    """Tích lũy bằng chứng qua các observation; chỉ GATE kết luận PASS/FAIL."""

    def __init__(self, spec):
        self.spec = spec
        self.steps = 0
        self.activities_seen = set()
        self.texts_seen = set()       # required texts đã thấy (lowercase)
        self.views_seen = set()
        self.dialog_seen = False
        # H2: dialog chọn tập được suy luận từ hành vi (OK trên chip 'Tập N'
        # mở đúng player) khi detector không nhận ra dialog — xem
        # note_dialog_implied(). Cờ này ghi vào evidence để báo cáo trung
        # thực (dialog_seen=True nhờ suy luận, không phải dump trực tiếp).
        self.dialog_implied = False
        self.motion_seen = False
        self.vision_confirmations = []  # [{frame, t, quote}]
        self.vision_denials = 0
        self.outcome = None           # None | "PASS" | "FAIL"
        self.outcome_reason = ""
        self.evidence = {}
        self._failed = False
        self.last_activity = None     # activity ở observation gần nhất
        self.playback_readings = []   # [(t_offset, elapsed_s)] — CI-T6 mục 8
        self._post_seek_positions = set()  # index lần đọc sau tua ngược
        # CI-T7 mục 4: vị trí các lần đọc NGAY SAU một lần tua NGƯỢC
        # (DPAD_LEFT/REWIND trong player) — lần đọc đó được miễn kiểm tra
        # đơn điệu (tua ngược thì đồng hồ lùi là đúng). Tua TỚI (DPAD_RIGHT)
        # KHÔNG miễn: đồng hồ chỉ được tăng, lùi sau tua tới là lỗi thật.

    # -- tích lũy ------------------------------------------------------
    def observe(self, activity, visible_texts, views, has_dialog, motion_playing, t_offset):
        """Một observation ổn định: activity + text dump + views + dialog + motion."""
        self.steps += 1
        self.last_activity = activity
        if activity and activity != "?":
            # Chuẩn hoá: activity ADB trả về dạng "com.kenhlive.tv/.MainActivity"
            # hoặc ".MainActivity" — lưu cả dạng đầy đủ lẫn dạng rút gọn để
            # required_activity ("MainActivity") so khớp được.
            self.activities_seen.add(activity)
            short = activity.split("/")[-1]
            self.activities_seen.add(short)
            if short.startswith("."):
                self.activities_seen.add(short[1:])
        blob = " ".join(visible_texts or []).lower()
        for t in self.spec.required_texts:
            if t and t in blob:
                self.texts_seen.add(t)
        for v in self.spec.required_views:
            if v in (views or []):
                self.views_seen.add(v)
        if has_dialog:
            self.dialog_seen = True
        # CI-T5 mục 5: motion CHỈ tính khi đo được TRONG LÚC đang ở activity
        # đích (so hậu tố như _missing). CI-T4 IPTV_EPG PASS mềm: motion
        # md 24.68 đo ở MainActivity SAU khi player tự thoát, không phải
        # trong player — gate cũ đếm motion ở bất kỳ observation nào.
        if motion_playing:
            req = self.spec.required_activity
            if not req or (activity or "").endswith(req):
                self.motion_seen = True
        self._t_offset = t_offset

    def record_vision(self, confirmed, frame_ref, t_offset, quote=""):
        if confirmed:
            self.vision_confirmations.append({"frame": frame_ref, "t": t_offset, "quote": quote})
        else:
            self.vision_denials += 1

    def note_dialog_implied(self):
        """H2 (trial 5): dialog chọn tập không được detector nhận ra nhưng
        hành vi chứng minh nó đã mở — OK trên chip 'Tập N' (chỉ có trong
        dialog) mở đúng player tập đó. Chỉ runner gọi, chỉ cho mission
        chọn tập, chỉ khi phím OK vừa rồi bấm trên chip tập. Ghi cờ
        dialog_implied vào evidence để không bịa tín hiệu lặng lẽ."""
        self.dialog_seen = True
        self.dialog_implied = True

    # -- CI-T6 mục 8: thời gian phát phải TĂNG --------------------------------
    def note_seek(self):
        """Driver vừa tua NGƯỢC (DPAD_LEFT/REWIND) trong player: lần đọc
        đồng hồ kế tiếp được miễn kiểm tra tăng đơn điệu (đồng hồ lùi là
        đúng sau tua ngược). Chỉ đánh dấu vị trí đọc kế tiếp."""
        self._post_seek_positions.add(len(self.playback_readings))

    def observe_playback(self, elapsed_s, t_offset):
        """Ghi 1 lần đọc đồng hồ elapsed (giây) trong player. None = không đọc
        được ở observation này (không có đồng hồ trên màn hình) — bỏ qua,
        không tính là đóng băng."""
        if elapsed_s is None:
            return
        self.playback_readings.append((t_offset, float(elapsed_s)))

    def playback_monotonic(self):
        """(True, '') nếu các lần đọc tăng đơn điệu (cho phép nhiễu OCR
        nhỏ: lùi <= 2s không tính); (False, chi tiết) nếu có lần lùi > 2s
        mà không phải ngay sau tua ngược. CI-T6 WebPlayer: 00:20 -> 00:00
        -> 00:30 -> 00:20 — max-min = 30s nên playback_status() cũ vẫn
        'increasing' và PASS, dù video thực tế đóng băng 60,3s
        (step_055 = step_059 pixel-identical). Đơn điệu mới là bằng chứng
        phát thật; cần >= 3 lần đọc mới kết luận."""
        vals = [s for _, s in self.playback_readings]
        if len(vals) < 3:
            return True, ""
        for i in range(1, len(vals)):
            if i in self._post_seek_positions:
                continue  # lùi ngay sau tua ngược là đúng, không tính
            if vals[i] < vals[i - 1] - 2.0:
                _a_m, _a_s = divmod(int(vals[i - 1]), 60)
                _b_m, _b_s = divmod(int(vals[i]), 60)
                return False, "%02d:%02d -> %02d:%02d (lùi %.0fs)" % (
                    _a_m, _a_s, _b_m, _b_s, vals[i - 1] - vals[i])
        return True, ""

    def playback_status(self):
        """'increasing' | 'frozen' | 'unknown'.
        increasing: max-min >= 1s giữa các lần đọc. frozen: >=2 lần đọc mà
        không nhích >= 1s (CI-T5: WebPlayer đứng 00:20 qua 3 quan sát).
        unknown: <2 lần đọc — KHÔNG chặn PASS (giới hạn đo đã ghi rõ: đồng
        hồ có thể không hiện trên dump/OCR ở 1 số frame)."""
        if len(self.playback_readings) < 2:
            return "unknown"
        vals = [s for _, s in self.playback_readings]
        return "increasing" if max(vals) - min(vals) >= 1.0 else "frozen"

    # -- đánh giá ------------------------------------------------------
    def _missing(self):
        s = self.spec
        missing = []
        # So khớp activity bằng HẬU TỐ: ADB trả 'com.kenhlive.tv/.phim.WebPlayerActivity'
        # nhưng spec chỉ ghi 'WebPlayerActivity'. Khớp tuyệt đối sẽ FAIL oan
        # mission đã tới đích (bài học từ run 42963719447: WebPlayer đã tới
        # nhưng tên class đầy đủ có tiền tố '.phim.').
        if s.required_activity and not any(
                a.endswith(s.required_activity) for a in self.activities_seen):
            missing.append("activity:%s (đã thấy: %s)" % (
                s.required_activity, sorted(self.activities_seen) or "không có"))
        for t in s.required_texts:
            if t not in self.texts_seen:
                missing.append("text:'%s'" % t)
        for v in s.required_views:
            if v not in self.views_seen:
                missing.append("view:%s" % v)
        if s.needs_dialog and not self.dialog_seen:
            missing.append("dialog: chưa thấy dialog nào mở")
        if s.needs_motion and not self.motion_seen:
            missing.append("motion: video chưa từng chuyển động")
        if s.needs_vision and not self.vision_confirmations:
            missing.append("vision: chưa có xác nhận vision")
        if s.needs_playback_progress:
            _pb = self.playback_status()
            if _pb == "frozen":
                _vals = [s for _, s in self.playback_readings]
                _m, _s = divmod(int(min(_vals)), 60)
                missing.append("playback: thời gian phát đứng yên %02d:%02d qua %d quan sát "
                               "— video đóng băng, không phát thật" % (_m, _s, len(_vals)))
            elif _pb == "unknown" and self.steps >= 2:
                if s.playback_no_clock:
                    # H1 (trial 9 run 43217017298): OSD WebPlayer không có
                    # đồng hồ — không đòi đọc; bằng chứng phát là motion +
                    # vision (2 tín hiệu bắt buộc riêng). Không clock + không
                    # motion thì FAIL ở nhánh motion ("video chưa từng chuyển
                    # động"), không PASS giả. Nhánh này cũng mở đường gọi
                    # vision-confirm: trial 9 mission #14 thiếu cả vision lẫn
                    # playback nên evaluate trả CONTINUE thay vì
                    # VISION_PENDING, vision không bao giờ được gọi.
                    pass
                else:
                    # CI-T7 mục 4: không đọc được đồng hồ sau >= 2 quan sát thì
                    # KHÔNG được PASS tự do nữa (CI-T6: readings [] + unknown ở
                    # mọi mission player mà vẫn PASS). Live: FAIL ở max_steps;
                    # replay downgrade thành UNVERIFIED (thiếu dữ liệu đo).
                    missing.append("playback: không đọc được đồng hồ phát sau %d quan sát "
                                   "— chưa chứng minh video phát thật (UNVERIFIED)" % self.steps)
            else:
                _mono, _mono_detail = self.playback_monotonic()
                if not _mono:
                    missing.append("playback: thời gian phát không tăng đơn điệu "
                                   "(%s) — video có thể đóng băng/khởi động lại, "
                                   "chưa chứng minh phát thật" % _mono_detail)
        return missing

    def _evidence_bundle(self, last_frame_ref):
        return {
            "activities_seen": sorted(self.activities_seen),
            "texts_seen": sorted(self.texts_seen),
            "views_seen": sorted(self.views_seen),
            "dialog_seen": self.dialog_seen,
            "dialog_implied": self.dialog_implied,
            "motion_seen": self.motion_seen,
            "vision_confirmations": list(self.vision_confirmations),
            "vision_denials": self.vision_denials,
            "playback_status": self.playback_status(),
            "playback_readings": list(self.playback_readings),
            "playback_monotonic": self.playback_monotonic()[0],
            "steps": self.steps,
            "frame": last_frame_ref,
        }

    def evaluate(self, last_frame_ref):
        """Trả (verdict, reason, evidence). verdict: PASS | FAIL | CONTINUE.
        Chỉ gọi sau mỗi observation; PASS yêu cầu đủ min_steps."""
        if self.outcome:
            return self.outcome, self.outcome_reason, self.evidence
        s = self.spec
        if s.kind == "stress":
            # Stress: PASS = đi hết max_steps mà app còn foreground, không CRITICAL.
            # CI-T4 (reviewer): nhánh cũ chỉ kiểm steps >= max_steps, KHÔNG
            # kiểm activity — app crash văng về launcher giữa chừng vẫn PASS
            # (lỗ false-pass cấu trúc). Giờ FAIL nếu activity cuối không phải
            # của app KenhLive.
            if self.steps >= s.max_steps:
                last = self.last_activity or ""
                # Chỉ kiểm package: activity ADB trả dạng pkg/class; launcher
                # cũng có class MainActivity nên KHÔNG được so tên class.
                if "com.kenhlive.tv" not in last:
                    self.outcome = "FAIL"
                    self.outcome_reason = ("stress: đi hết %d bước nhưng app không còn "
                                           "foreground (activity cuối: %s) — có thể đã crash/văng"
                                           % (s.max_steps, last or "?"))
                    self.evidence = self._evidence_bundle(last_frame_ref)
                    return self.outcome, self.outcome_reason, self.evidence
                self.outcome = "PASS"
                self.outcome_reason = "stress: đi hết %d bước, app còn foreground" % s.max_steps
                self.evidence = self._evidence_bundle(last_frame_ref)
                return self.outcome, self.outcome_reason, self.evidence
            return "CONTINUE", "", {}
        missing = self._missing()
        if missing == ["vision: chưa có xác nhận vision"]:
            # Mọi tín hiệu rẻ đã xanh, chỉ còn vision: báo VISION_PENDING để
            # runner/replay gọi vision-confirm (không tự PASS, không tự FAIL).
            # Mọi tín hiệu rẻ đã xanh, chỉ còn vision: VISION_PENDING được
            # phép ngay cả ở max_steps (xác nhận là bước cuối, không tốn bước).
            if self.steps < s.min_steps:
                return "CONTINUE", "đủ tín hiệu rẻ nhưng chưa đủ %d bước tối thiểu" % s.min_steps, {}
            return "VISION_PENDING", "đủ tín hiệu rẻ, chờ vision xác nhận", {}
        if not missing:
            if self.steps < s.min_steps:
                return "CONTINUE", "đủ tín hiệu nhưng chưa đủ %d bước tối thiểu" % s.min_steps, {}
            self.outcome = "PASS"
            self.outcome_reason = "đủ mọi tín hiệu áp dụng"
            self.evidence = self._evidence_bundle(last_frame_ref)
            return self.outcome, self.outcome_reason, self.evidence
        if self.steps >= s.max_steps:
            self.outcome = "FAIL"
            self.outcome_reason = "hết %d bước, còn thiếu: %s" % (s.max_steps, "; ".join(missing))
            self.evidence = self._evidence_bundle(last_frame_ref)
            return self.outcome, self.outcome_reason, self.evidence
        return "CONTINUE", "còn thiếu: %s" % "; ".join(missing), {}

    def force_fail(self, reason, last_frame_ref):
        """Driver/gate ép FAIL (launch thất bại, kẹt, sai tab đích)."""
        if self.outcome:
            return self.outcome, self.outcome_reason, self.evidence
        self.outcome = "FAIL"
        self.outcome_reason = reason
        self.evidence = self._evidence_bundle(last_frame_ref)
        return self.outcome, self.outcome_reason, self.evidence

    def missing_summary(self):
        return self._missing()

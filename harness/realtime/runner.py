#!/usr/bin/env python3
"""KenhLive Realtime QA — runner (điều phối vòng perception -> gate -> driver).

Một bước (step) = 1 observation ổn định + detectors cục bộ + gate + 1 hành động.
Vision KHÔNG nằm trong vòng bước — chỉ gọi khi gate đủ tín hiệu rẻ (xác nhận
hoàn thành), detector nghi vấn, hoặc driver kẹt. Mọi con số thời gian được đo
và ghi vào report.timings.
"""
import hashlib
import io
import json
import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from device import RealtimeDevice
from perception import ScreenWatcher, MOTION_PLAYING_PCT
from detectors import run_all_detectors, detect_keyboard_from_image
from vision import VisionClient
from gate import EvidenceGate
from driver import Driver
from judge import HonestJudge
import ocr as ocr_mod
from missions import get_missions

try:
    from video_recorder import VideoRecorder
except Exception:
    VideoRecorder = None


def _playback_seconds_from_text(text):
    """Giây elapsed từ chuỗi 'elapsed / total' (VD '00:20 / 01:05:24',
    '00:20 / 24:14') — lấy số nhỏ hơn (elapsed). None nếu không có cặp
    đó. Dùng chung cho dump text và quote vision (CI-T7 mục 4)."""
    m = re.search(r"(\d{1,2}:\d{2}(?::\d{2})?)\s*/\s*(\d{1,2}:\d{2}(?::\d{2})?)",
                  text or "")
    if not m:
        return None

    def _to_s(tok):
        parts = [int(p) for p in tok.split(":")]
        if len(parts) == 3:
            return parts[0] * 3600 + parts[1] * 60 + parts[2]
        return parts[0] * 60 + parts[1]

    return min(_to_s(m.group(1)), _to_s(m.group(2)))


class RealtimeRunner:
    def __init__(self, out_dir="/tmp/qa_report_realtime", serial=None, vision_budget=40,
                 no_vision=False):
        self.out_dir = out_dir
        self.shots_dir = os.path.join(out_dir, "shots")
        os.makedirs(self.shots_dir, exist_ok=True)
        self.device = RealtimeDevice(serial=serial)
        self.watcher = ScreenWatcher(self.device)
        self.vision = VisionClient(budget=0 if no_vision else vision_budget)
        self.no_vision = no_vision
        self.judge = HonestJudge(out_dir)
        self.recorder = None
        self.timings = {"steps": 0, "observe_s": 0.0, "vision_s": 0.0,
                        "vision_calls": 0, "step_times": []}
        self.timeline = []
        self.findings = []
        self.unverified = []
        self.mission_results = []
        self.start_time = 0
        self.detector_ctx = {"watcher": self.watcher, "reported": set(),
                             "focus_hist": [], "ocr_skipped": 0,
                             "logo_check_frames": []}
        self._global_step = 0
        self._prev_obs_png = None  # frame observation trước (CI-T5: fallback pixel_diff)
        self._saved_shot_hashes = {}  # CI-T7 mục 6: sha256 PNG -> rel path shot đã lưu (dedup)
        self._hero_frame = None  # frame hero Home để vision check cuối run (CI-T5 mục 7)
        self._player_title_frame = None  # frame title player để vision check (CI-T5 mục 7)
        self.vision_check_log = []  # CI-T6 mục 2: mỗi call check_visual đã soi
        # frame nào (frame path + timestamp + crop) — debug cú bỏ sót CI-T5

    # -- helpers -------------------------------------------------------
    def _log_action(self, action):
        """CI-T7 mục 2: ghi rõ luật driver chọn ở mỗi bước vào timeline —
        CI-T6 luật goto_live_card chạy 4 lần nhưng sai trạng thái mà log
        không thấy được (chỉ có print `-> KEY ... [rule]` trên console, CI
        log không giữ đủ). Ghi action (type/param/rule/thought) vào entry
        timeline của bước quan sát vừa xong — action này là hành động driver
        chọn SAU quan sát đó, thực thi rồi mới tới quan sát sau."""
        if action is None or not self.timeline:
            return
        try:
            self.timeline[-1]["action"] = action.as_dict()
        except Exception:
            pass

    def _save_frame(self, png_bytes, label):
        # CI-T7 mục 6: dedup theo nội dung — cùng 1 ảnh PNG thì chỉ lưu 1
        # file, lần sau trả lại đường dẫn đã lưu (không ghi trùng). Áp cho
        # cả _observe lẫn _finish_mission và giữa các mission (046=047,
        # 026=037 ở CI-T6 là cùng 1 ảnh lưu 2 lần).
        if not png_bytes:
            return None
        _h = hashlib.sha256(png_bytes).hexdigest()
        if _h in self._saved_shot_hashes:
            return self._saved_shot_hashes[_h]
        path = os.path.join(self.shots_dir, "%s.jpg" % label)
        try:
            from PIL import Image
            im = Image.open(io.BytesIO(png_bytes)).convert("RGB")
            im.thumbnail((960, 540))
            im.save(path, "JPEG", quality=75)
        except Exception:
            path = path.replace(".jpg", ".png")
            with open(path, "wb") as f:
                f.write(png_bytes)
        _rel = "shots/%s" % os.path.basename(path)
        self._saved_shot_hashes[_h] = _rel
        return _rel

    def _observe(self, mission_name):
        """Một observation: chờ stable frame + UI dump + detectors. Trả dict.
        Ghi breakdown thời gian (wait/dump/detect) để biết nút thắt tốc độ —
        CI-T2 observe p50 13.5s mà không rõ phần nào chậm.
        CI-T7 mục 7: DUMP TRƯỚC, CHỤP SAU, rồi dump kiểm chứng. Trước đây
        chụp screenshot trước rồi dump sau (dump uiautomator mất vài giây)
        nên dialog có thể mở/đóng giữa hai lần lấy mẫu: frame step_051
        không thấy dialog dù dump ghi 'Tập 1' (EPISODE_PICKER PASS mềm).
        Dump lại sau khi chụp: (activity, focused_sig, has_dialog) phải
        giống dump đầu — khác thì chụp lại + dump lại 1 lần, dùng bộ sau
        (trạng thái ổn định quanh lúc chụp). Tốn thêm 1 lần dump/bước
        (~1-3s) nhưng screenshot và dump phải là cùng 1 trạng thái thì
        bằng chứng mới khớp nhau."""
        t0 = time.time()
        t1 = time.time()
        ui_state = self.device.dump_ui_state()
        activity = self.device.current_activity()
        t_dump = round(time.time() - t1, 2)
        t2 = time.time()
        png, waited, timed_out = self.watcher.wait_stable(timeout_s=6.0)
        t_wait = round(time.time() - t2, 2)
        t3 = time.time()
        ui_state2 = self.device.dump_ui_state()
        activity2 = self.device.current_activity()
        t_dump = round(t_dump + (time.time() - t3), 2)

        def _sync_sig(us, act):
            return (act, us.get("focused_sig"), bool(us.get("has_dialog")))

        if _sync_sig(ui_state2, activity2) != _sync_sig(ui_state, activity):
            # Trạng thái đổi ngay quanh lúc chụp — chụp lại + dump lại 1 lần.
            self._sync_retries = getattr(self, "_sync_retries", 0) + 1
            print("      🔄 [Observe] dump/chụp lệch (%s -> %s) — chụp lại + dump lại"
                  % (_sync_sig(ui_state, activity), _sync_sig(ui_state2, activity2)),
                  flush=True)
            t4 = time.time()
            png2, waited2, timed_out2 = self.watcher.wait_stable(timeout_s=3.0)
            t_wait = round(t_wait + (time.time() - t4), 2)
            if png2:
                png, waited, timed_out = png2, waited2, timed_out2
            t5 = time.time()
            ui_state = self.device.dump_ui_state()
            activity = self.device.current_activity()
            t_dump = round(t_dump + (time.time() - t5), 2)
        else:
            ui_state = ui_state2
            activity = activity2
        # OSD đang hiện? = dump có nút điều khiển player (id btn* hoặc nhãn
        # control quen thuộc). Dùng cho detect_player_focus_loss (P0-6).
        _ctrl = {"kênh trước", "kênh kế", "epg", "yêu thích", "cài đặt",
                 "tỉ lệ 16:9", "tập tiếp", "danh sách tập", "về trực tiếp",
                 "tùy chọn", "tốc độ", "phát", "tạm dừng", "chọn tập"}
        ui_state["osd_visible"] = any(
            ("btn" in (rid or "").lower()) or (txt or "").strip().lower() in _ctrl
            for rid, txt in ui_state.get("all_visible_texts", []))
        has_ring, ring_col, _ = self.device.detect_focus_ring(
            png, ui_state.get("focused_bounds"))
        # CI-T8 mục 1: WebPlayer dump không có focused view (WebView mù với
        # uiautomator) — quét viền focus trên ẢNH (vùng OSD dưới) khi dump
        # nói NONE hoặc không thấy vòng. Ảnh có vòng vàng/trắng thì focus
        # CÓ thật (CI-T7 finding #1 giả: viền vàng quanh nút tua lùi/play
        # nhưng dump NONE). Chỉ quét trong player để khỏi tốn mỗi bước.
        image_ring = False
        image_ring_color = "UNKNOWN"
        image_ring_box = None
        if ("PlayerActivity" in (activity or "") or "WebPlayerActivity" in (activity or "")) \
                and (ui_state.get("focused_sig") == "NONE" or not has_ring):
            try:
                image_ring, image_ring_color, _cov, image_ring_box = \
                    self.device.detect_focus_ring_anywhere(png)
            except Exception:
                image_ring = False
            if image_ring:
                has_ring, ring_col = True, image_ring_color
        ui_state["image_focus_ring"] = image_ring
        ui_state["image_focus_box"] = image_ring_box
        motion = self.watcher.is_video_playing()
        motion_delta = self.watcher.motion_delta()
        # CI-T5 mục 2/6: fallback pixel_diff giữa 2 frame quan sát liên tiếp —
        # watcher đói mẫu khi dump dài (cửa sổ 4s trống -> motion_delta -1 =
        # UNKNOWN) nhưng 2 frame observe cách nhau ~10s vẫn đo được video có
        # đổi không. Đo TRƯỚC poll (mục 6): pixel_diff rẻ (~ms), nếu đo được
        # thì bỏ qua poll 3s chờ watcher mẫu.
        fb_diff = ScreenWatcher.fallback_pixel_diff(
            getattr(self, "_prev_obs_png", None), png)
        self._prev_obs_png = png
        # Watcher chưa đủ mẫu cho cửa sổ motion (-1) mà mission đang ở player:
        # chờ tối đa 3s cho đủ mẫu thay vì kết luận 'không chuyển động' oan
        # (CI-T2: 98% bước player đo motion 0.00 dù video đang phát). Chỉ poll
        # khi fallback cũng chưa đo được (fb_diff < 0).
        if motion_delta < 0 and ("PlayerActivity" in (activity or "")
                                 or "WebPlayerActivity" in (activity or "")) \
                and fb_diff < 0:
            deadline = time.time() + 3.0
            while time.time() < deadline:
                motion_delta = self.watcher.motion_delta()
                if motion_delta >= 0:
                    break
                time.sleep(0.3)
            motion = self.watcher.is_video_playing()
        # CI-T5 mục 2 — fallback pixel_diff giữa 2 frame quan sát liên tiếp:
        # watcher đói mẫu khi dump dài (cửa sổ 4s trống -> motion_delta -1 =
        # UNKNOWN) nhưng 2 frame observe cách nhau ~10s vẫn đo được video
        # có đổi không. Chỉ dùng khi watcher chưa đo được; khi đo được thì
        # motion_state = True/False, còn None = thật sự chưa đo được (VD
        # observation đầu tiên, chưa có frame trước).
        motion_state = None  # True | False | None (UNKNOWN)
        motion_source = "watcher"
        if motion_delta >= 0:
            motion_state = bool(motion)
        else:
            if fb_diff >= 0:
                motion = fb_diff >= MOTION_PLAYING_PCT
                motion_state = bool(motion)
                motion_delta = fb_diff  # số đo thật, ghi vào timeline thay vì None
                motion_source = "fallback_pixel_diff"
        # CI-T6 mục 7: hash frame để (a) detector bỏ qua quan sát trùng,
        # (b) không lưu shot trùng. 011=012, 055=056, 075=076 ở CI-T5.
        frame_hash = hashlib.sha256(png).hexdigest() if png else None
        duplicate_frame = (frame_hash is not None
                           and frame_hash == self.detector_ctx.get("frame_hash_prev"))
        self.detector_ctx["frame_hash"] = frame_hash
        # bàn phím ảo đang mở: >=8 text 1 ký tự chữ cái trong dump (đang gõ)
        _singles = [t for _, t in ui_state.get("all_visible_texts", [])
                    if len((t or "").strip()) == 1 and (t or "").strip().isalpha()]
        ui_state["keyboard_open"] = len(_singles) >= 8
        # CI-T8 mục 6: bàn phím ảo kiểm bằng ẢNH mỗi bước (dump mù với bàn
        # phím in-app KenhLive — STRESS CI-T7 gõ phím mà dump không đổi nên
        # detector "kẹt" nổ oan). ~50ms/bước; kết quả vào ui_state để
        # Driver.note_state reset streak + vào ctx để detect_focus_trap
        # dùng lại (không tính lại ở điểm sắp tố).
        kb_img = detect_keyboard_from_image(png) if png else False
        ui_state["keyboard_open_image"] = bool(kb_img)
        self.detector_ctx["keyboard_open_image"] = bool(kb_img)
        t_offset = round(time.time() - self.start_time, 1)
        # Tên frame phân biệt được mission (CI-T4, reviewer): cũ
        # mission_name.lower()[:8] == 'mission_' với MỌI mission (tên đều bắt
        # đầu MISSION_) nên mọi evidence đều là step_NNN_mission_.jpg.
        frame_ref = "step_%03d_%s.jpg" % (
            self._global_step + 1,
            mission_name.lower().replace("mission_", "", 1)[:8])
        t2 = time.time()
        findings = run_all_detectors(png, ui_state, activity, self.detector_ctx,
                                     frame_ref, t_offset, ocr_mod)
        t_detect = round(time.time() - t2, 2)
        self.detector_ctx["frame_hash_prev"] = frame_hash
        # lưu frame khi có defect hoặc mỗi observation thứ 5 (đủ xem lại) —
        # nhưng không lưu shot trùng (frame trùng quan sát trước và không
        # có defect mới: cùng nội dung, đã có frame trước đó).
        saved = None
        if findings or (self._global_step % 5 == 0):
            if not (duplicate_frame and not findings):
                saved = self._save_frame(png, frame_ref.replace(".jpg", ""))
        # CI-T8 mục 3: _save_frame dedup theo nội dung — frame trùng shot
        # đã lưu thì trả lại path CŨ; finding trích dẫn frame_ref MỚI sẽ
        # trỏ file không tồn tại (step_035/042 CI-T7). Viết lại evidence
        # của finding sang path đã lưu thật.
        if saved and os.path.basename(saved) != frame_ref:
            _saved_base = os.path.basename(saved)
            for f in findings:
                if (f.get("evidence") or {}).get("frame") == frame_ref:
                    f["evidence"]["frame"] = _saved_base
        dt = round(time.time() - t0, 2)
        self.timings["observe_s"] += dt
        breakdown = {"wait": t_wait, "dump": t_dump, "detect": t_detect}
        if dt > 15:
            print("      ⏱ observe chậm %.1fs %s" % (dt, breakdown), flush=True)
        return {
            "png": png, "waited_s": t_wait, "timed_out": timed_out,
            "ui_state": ui_state, "activity": activity,
            "has_ring": has_ring, "ring_col": ring_col,
            "image_focus_ring": image_ring, "image_focus_box": image_ring_box,
            "motion": motion, "motion_delta": motion_delta,
            "motion_state": motion_state, "motion_source": motion_source,
            "t_offset": t_offset, "frame_ref": frame_ref,
            "frame_file": saved, "findings": findings,
            "duplicate_frame": duplicate_frame,
            "frame_hash": (frame_hash[:12] if frame_hash else None),
            "keyboard_open": ui_state.get("keyboard_open", False),
            # CI-T7 mục 3: bàn phím phát hiện từ ẢNH (detector ghi vào ctx
            # khi nghi kẹt) — dump không thấy bàn phím in-app nên chỉ ghi
            # dump sẽ thiếu; None = chưa từng nghi kẹt nên chưa kiểm ảnh.
            "keyboard_open_image": self.detector_ctx.get("keyboard_open_image"),
            "observe_s": dt, "observe_breakdown": breakdown,
        }

    @staticmethod
    def _parse_time_token(txt):
        """'MM:SS' / 'H:MM:SS' -> giây, hoặc None."""
        m = re.fullmatch(r"(\d{1,2}):(\d{2})(?::(\d{2}))?", (txt or "").strip())
        if not m:
            return None
        h, mi, s = m.groups()
        return int(h) * 3600 + int(mi) * 60 + int(s) if s else int(h) * 60 + int(mi)

    def _extract_playback_s(self, ui_state, frame_ref, png=None):
        """Đồng hồ elapsed (giây) của player ở observation này, hoặc None.
        CI-T6 mục 8. Ưu tiên dump text dạng 'elapsed / total' (VD '00:20 /
        24:14' — lấy số nhỏ hơn). Không có thì lấy min token thời gian trong
        cache OCR band dưới (BOTTOM_BAR_BAND) của frame hiện tại: đồng hồ
        elapsed là số nhỏ nhất trên thanh seekbar. Fallback OCR đòi >=2 token
        (1 token lẻ không phân biệt được elapsed/total — trả None thay vì
        đoán sai rồi tố đóng băng oan). None = không đọc được — gate coi là
        unknown, không chặn PASS.
        CI-T7 mục 4 (gốc rễ CI-T6: readings [] ở mọi mission player):
        dump WebView không có text -> osd_visible=False -> cả 3 detector đọc
        band dưới đều skip khi osd False (detectors.py:536/582) -> cache OCR
        band dưới TRỐNG -> hàm này luôn None. Sửa: cache trống thì OCR ÉP
        band dưới TRỰC TIẾP TỪ ẢNH (không qua osd_visible từ dump), và ghi
        vào cache để detector sau dùng chung (không OCR lại). Chỉ chạy cho
        2 mission VOD (caller đã gate needs_playback_progress)."""
        texts = [t for _, t in ui_state.get("all_visible_texts", [])]
        for t in texts:
            v = _playback_seconds_from_text(t or "")
            if v is not None:
                return v
        from detectors import BOTTOM_BAR_BAND
        cache = self.detector_ctx.setdefault("_ocr_cache", {})
        key = (frame_ref, BOTTOM_BAR_BAND)
        if key not in cache and png is not None and ocr_mod.available():
            # Cache trống = detector đã skip band dưới (thường vì osd False
            # theo dump) — đọc ép từ ảnh, không dựa osd_visible nữa.
            try:
                cache[key] = ocr_mod.read_boxes(png, region=BOTTOM_BAR_BAND)
            except Exception:
                cache[key] = []
            if len(cache) > 12:
                cache.pop(next(iter(cache)))
        boxes = cache.get(key, [])
        vals = []
        for box in boxes or []:
            v = self._parse_time_token(box.get("text", ""))
            if v is not None:
                vals.append(v)
        return min(vals) if len(vals) >= 2 else None

    def _note_seek_if_needed(self, gate, action, activity):
        """CI-T7 mục 4: driver vừa tua NGƯỢC (DPAD_LEFT/REWIND) trong player
        thì báo gate để lần đọc đồng hồ kế tiếp được miễn kiểm tra đơn điệu
        (tua ngược thì đồng hồ lùi là đúng). Tua TỚI (DPAD_RIGHT — luật
        probe_player) KHÔNG miễn: đồng hồ chỉ được tăng sau tua tới."""
        if action is None or action.type != "KEY":
            return
        if (action.param or "").upper() not in ("DPAD_LEFT", "REWIND"):
            return
        if "PlayerActivity" not in (activity or ""):
            return
        gate.note_seek()

    def _run_directed_launch(self, spec, gate):
        """Launch có định hướng TRƯỚC vòng driver; không tới activity đích -> FAIL."""
        if spec.directed_launch == "LAUNCH_WEB_PLAYER":
            self.device.launch_web_player()
            time.sleep(2.5)
        elif spec.directed_launch == "LAUNCH_VOD_PLAYER":
            self.device.launch_vod_player()
            time.sleep(6.0)
        else:
            return True
        req = spec.required_activity
        if not req:
            return True
        deadline = time.time() + 30
        while time.time() < deadline:
            cur = self.device.current_activity()
            if req in cur:
                gate.activities_seen.add(cur)
                return True
            time.sleep(1.5)
        return False

    def _note_vision_frames(self, spec, obs, last_frame_ref):
        """Giữ 1 frame hero (Home) + 1 frame title player để vision check
        cuối run (CI-T5 mục 7: OCR không tách được chữ chồng). Ưu tiên frame
        WebPlayer (lỗi tiêu đề đè đôi là của WebPlayer); frame native player
        chỉ là fallback nếu cả run không vào WebPlayer lần nào.
        CI-T6 mục 2: giữ frame CUỐI (ổn định nhất), không phải frame đầu —
        frame WebPlayer đầu tiên (lúc loading) có thể chưa hiện lỗi đè đôi,
        trong khi lỗi tồn tại suốt các frame sau (step_063/066/067 CI-T5).
        Kiểm tra trên frame đầu = bỏ sót."""
        if spec.name == "MISSION_HOME_BILLBOARD_6_ROWS":
            self._hero_frame = {"png": obs["png"], "frame": last_frame_ref,
                                "t": obs["t_offset"]}
        act = obs.get("activity") or ""
        if "WebPlayerActivity" in act:
            self._player_title_frame = {"png": obs["png"], "frame": last_frame_ref,
                                        "t": obs["t_offset"], "activity": act}
        elif "PlayerActivity" in act and "WebPlayerActivity" not in (
                (self._player_title_frame or {}).get("activity") or ""):
            self._player_title_frame = {"png": obs["png"], "frame": last_frame_ref,
                                        "t": obs["t_offset"], "activity": act}

    def _vision_overlap_checks(self):
        """CI-T5 mục 7: vision check hero + title player — 2 lỗi thật CI-T3+
        CI-T4 đều sót vì OCR không tách được 2 lớp chữ chồng, chỉ vision mới
        bắt (hero: giờ đè phụ đề step_006/016; WebPlayer: tiêu đề đè đôi
        step_071/082). Tối đa 2 call/run (1 hero + 1 title), crop đúng vùng
        nghi, dùng budget vision hiện có (CI-T4 dùng 5 calls; throttle
        30 req/phút vẫn giữ — 429 là lỗi hạ tầng, không tính lỗi app).
        found=True -> finding HIGH có frame evidence."""
        if self.no_vision or not self.vision.available() or self.vision.remaining() <= 0:
            return
        checks = []
        if self._hero_frame:
            checks.append(("hero", self._hero_frame, (0, 140, 1920, 850),
                           "Trong vùng hero này, có dòng giờ (VD '16:17') ĐÈ LÊN hoặc "
                           "CHỒNG LÊN dòng phụ đề/tiêu đề bên dưới không? Đọc nguyên văn "
                           "2 dòng chữ bị chồng nếu có."))
        if self._player_title_frame:
            checks.append(("player_title", self._player_title_frame, (0, 0, 1920, 280),
                           "Trong vùng tiêu đề player này, có đúng 2 DÒNG TIÊU ĐỀ "
                           "CHỒNG LÊN NHAU không — dòng tiêu đề trên đè lên dòng tiêu đề "
                           "dưới (VD 'Tình Yêu Trong Vỏ Bọc / Tình Yêu Ngụy Trang' đè lên "
                           "'Tình Yêu Ngụy Trang (2026) · Tập 01'), chữ chen nhau không "
                           "đọc được? Đọc nguyên văn cả 2 dòng bị chồng nếu có."))
        for kind, fr, crop, question in checks:
            if self.vision.remaining() <= 0:
                break
            # CI-T6 mục 2: log rõ mỗi call đã soi frame nào (path + timestamp
            # + crop) — CI-T5 không ghi được 2 call check_visual đã soi frame
            # nào nên không debug được cú bỏ sót tiêu đề đè đôi.
            entry = {"kind": kind, "frame": fr["frame"], "t": fr["t"],
                     "crop": list(crop), "question": question}
            print("      🔎 [VISION-CHECK %s] frame=%s t=%.1fs crop=%s"
                  % (kind, fr["frame"], fr["t"], crop), flush=True)
            res, err = self.vision.check_visual(fr["png"], question, crop=crop)
            entry["result"] = ("found" if res and res.get("found")
                               else ("error:%s" % err if res is None else "not_found"))
            if res is not None:
                entry["detail"] = res.get("detail", "")
                entry["quote"] = res.get("quote", "")
            self.vision_check_log.append(entry)
            if res is None:
                self.unverified.append({
                    "check": "vision-overlap-%s" % kind,
                    "reason": "vision call lỗi/không parse được: %s" % (err or "?"),
                    "frame": fr["frame"]})
                continue
            if res.get("found"):
                sev = str(res.get("severity", "HIGH")).upper()
                if sev not in ("CRITICAL", "HIGH", "MEDIUM", "LOW"):
                    sev = "HIGH"
                if kind == "hero":
                    area, issue = "Hero billboard", "Giờ đè lên phụ đề hero"
                    sugg = "Chừa top inset/scrim cho hero; tách dòng giờ khỏi phụ đề"
                else:
                    area, issue = "Player tiêu đề", "Tiêu đề player đè đôi"
                    sugg = "Chỉ hiện 1 dòng tiêu đề trong player, bỏ dòng trùng"
                self.findings.append({
                    "severity": sev, "area": area, "issue": issue,
                    "detail": "Vision xác nhận chữ chồng trong vùng %s: %s"
                              % (kind, res.get("detail", "")),
                    "suggestion": sugg,
                    "evidence": {"frame": fr["frame"], "video_t": fr["t"],
                                 "ui_state": ""},
                })
                print("      🔎 [VISION-OVERLAP %s] %s — %s"
                      % (sev, issue, res.get("detail", "")), flush=True)

    def _vision_confirm(self, spec, gate, obs):
        """Xác nhận hoàn thành bằng vision (1 call) khi gate đủ tín hiệu rẻ."""
        # Player mission cần motion: đừng gọi vision trên frame 'Đang tải
        # luồng...' — poll watcher tới 10s cho motion thật trước đã (CI-T3:
        # PLAYER_STREAMING bị vision chối 2 lần trên frame đang tải, motion
        # 0.00). Hết 10s vẫn không có motion -> trả False KHÔNG gọi vision
        # (không tốn call, không tính là denial — driver sẽ WAIT thêm).
        if spec.needs_motion and not obs.get("motion"):
            deadline = time.time() + 10.0
            while time.time() < deadline:
                if self.watcher.is_video_playing():
                    gate.motion_seen = True
                    obs["motion"] = True
                    break
                time.sleep(0.5)
            if not obs.get("motion"):
                return False
        if self.no_vision or not self.vision.available() or self.vision.remaining() <= 0:
            self.unverified.append({
                "check": "%s vision-confirm" % spec.name,
                "reason": "vision không khả dụng / hết ngân sách — mission không PASS được bằng vision",
                "frame": obs["frame_ref"]})
            return False
        t0 = time.time()
        res, err = self.vision.confirm_target(obs["png"], spec.target_desc)
        self.timings["vision_s"] += round(time.time() - t0, 1)
        if res is None:
            self.unverified.append({
                "check": "%s vision-confirm" % spec.name,
                "reason": "vision call lỗi/không parse được: %s" % (err or "?"),
                "frame": obs["frame_ref"]})
            return False
        gate.record_vision(res.get("confirmed"), obs["frame_ref"],
                           obs["t_offset"], res.get("quote", ""))
        # CI-T7 mục 4: quote vision có thể chứa đồng hồ 'elapsed / total'
        # (VD '00:20 / 01:05:24' — chính nguồn này đã cứu WebPlayer directed
        # ở CI-T2) — parse thành 1 lần đọc playback, không bỏ nguồn thật.
        if spec.needs_playback_progress:
            _pv = _playback_seconds_from_text(res.get("quote", ""))
            if _pv is not None:
                gate.observe_playback(_pv, obs["t_offset"])
        return bool(res.get("confirmed"))

    def _reset_to_mission(self, spec):
        """Đầu mỗi mission (không directed): đưa app về trạng thái xuất phát —
        MainActivity + đúng tab đích. CI-T2: app kẹt trong PlayerActivity từ
        mission 4, 7 mission sau FAIL oan vì không có luật quay về MainActivity
        (BACK tầng 4 của app về TRANG CHỦ, nên BACK từ player là đường về)."""
        if spec.directed_launch:
            return
        for _ in range(3):
            if "MainActivity" in self.device.current_activity():
                break
            self.device.send_key("BACK")
            time.sleep(1.0)
        if "MainActivity" not in self.device.current_activity():
            self.device.launch_app()
            time.sleep(2.0)
        if spec.tab is not None:
            try:
                cur = self.device.detect_tab_index(self.device.dump_ui_state())
            except Exception:
                cur = None
            if cur is not None and cur != spec.tab:
                self.device.switch_tab(spec.tab)
                time.sleep(1.0)

    def _scroll_to_top(self, spec):
        """Đầu mission list (CI-T5 mục 4): gửi UP ×N để header ('Hôm nay',
        'tv360') hiện trong viewport trước khi gate đọc text. Chạy SAU khi
        settle dialog (phím UP trong lúc dialog mở sẽ bị dialog nuốt) và
        chỉ cho mission gắn cờ needs_scroll_top. UP ở mép trên là vô hại
        (focus đã ở hàng đầu thì đứng yên). Nhịp 0.3s/phím — đủ cho focus
        di chuyển, rẻ hơn nhiều so với 1 observation FAIL oan."""
        if spec.directed_launch or not spec.needs_scroll_top:
            return
        for _ in range(8):
            self.device.send_key("UP")
            time.sleep(0.3)

    def _settle_blocking_dialog(self, spec):
        """Đầu mỗi mission: đóng dialog chào mừng lần đầu nếu đang mở, TRƯỚC
        khi gate nhìn thấy nó. Nếu không, dialog đích của mission cần dialog
        sẽ bị tính pass giả trên dialog chào mừng (CI-T1: dialog mở suốt run,
        16/17 mission kẹt). Chỉ đóng dialog welcome (btnCloseFeedback); dialog
        khác để driver xử lý trong vòng lặp. Trả False nếu đóng không được."""
        for _ in range(3):
            ui_state = self.device.dump_ui_state()
            if not ui_state.get("has_dialog"):
                return True
            if "btnCloseFeedback" not in (ui_state.get("dialog_ids") or []):
                return True
            ft = (ui_state.get("focused_text") or "").lower()
            fs = ui_state.get("focused_sig") or ""
            if "close" in fs.lower() or any(k in ft for k in ("đã hiểu", "đóng", "ok")):
                self.device.send_key("OK")
            else:
                self.device.send_key("BACK")
            time.sleep(0.8)
        ui_state = self.device.dump_ui_state()
        if ui_state.get("has_dialog") and "btnCloseFeedback" in (ui_state.get("dialog_ids") or []):
            return False
        return True

    def run_mission(self, spec):
        print("\n🎯 [Realtime] %s — %s" % (spec.name, spec.title), flush=True)
        gate = EvidenceGate(spec)
        driver = Driver(self.device, gate, spec,
                        vision=None if self.no_vision else self.vision)
        last_frame_ref = None
        last_obs = None
        dialog_obs = None  # CI-T8 mục 3: observation đầu tiên thấy dialog mở
        pending_vision_confirm = False
        last_action_rule = None  # rule của action vừa thực thi (CI-T5 mục 9)

        if spec.directed_launch:
            ok = self._run_directed_launch(spec, gate)
            if not ok:
                issue = ("Directed launch %s không mở được %s trong 30s — FAIL, "
                         "không cho tự kết thúc pass giả." % (spec.directed_launch, spec.required_activity))
                finding = {"area": spec.title, "severity": "HIGH", "issue": issue,
                           "detail": "Deep-link đã chạy nhưng activity đích không xuất hiện.",
                           "suggestion": "Kiểm tra deep-link %s và resolver tập phim." % spec.directed_launch,
                           "evidence": {"frame": None, "video_t": round(time.time() - self.start_time, 1),
                                        "ui_state": ""}}
                print("   ❌ [Directed Launch Failed] %s" % issue, flush=True)
                self.findings.append(finding)
                gate.force_fail(issue, None)
                return self._finish_mission(spec, gate, [])

        # Về MainActivity + đúng tab trước khi bắt đầu (mission trước có thể
        # để lại app trong player — CI-T2). Reset TRƯỚC settle: dialog chào
        # mừng nằm trên MainActivity, settle trên player là vô nghĩa.
        self._reset_to_mission(spec)

        # Dialog chào mừng lần đầu phải đóng TRƯỚC khi gate nhìn thấy nó.
        if not self._settle_blocking_dialog(spec):
            issue = "Dialog chào mừng 'THÔNG BÁO' vẫn mở sau 3 lần đóng thử — mission kẹt ngay từ đầu"
            print("   ❌ [Dialog Blocked] %s" % issue, flush=True)
            gate.force_fail(issue, None)
            return self._finish_mission(spec, gate, [])

        # Cuộn lên đầu danh sách để header hiện trước khi gate đọc (CI-T5 §4).
        self._scroll_to_top(spec)

        while gate.steps < spec.max_steps:
            self._global_step += 1
            step_t0 = time.time()
            obs = self._observe(spec.name)
            last_frame_ref = obs["frame_ref"]
            last_obs = obs
            ui_state = obs["ui_state"]
            self._note_vision_frames(spec, obs, last_frame_ref)
            driver.note_state(ui_state, obs["activity"], obs.get("motion_state"))
            self.detector_ctx["last_key"] = self.device.action_history[-1] if self.device.action_history else ""

            # tích lũy bằng chứng vào gate
            texts = [t for _, t in ui_state.get("all_visible_texts", [])]
            views = [rid for rid, _ in ui_state.get("all_visible_texts", [])]
            # CI-T8 mục 3: giữ khung ĐẦU TIÊN thấy dialog mở — mission cần
            # dialog thì frame bằng chứng phải là khung này (step_051: dialog
            # mở thật nhưng khung cuối mission không thấy dialog).
            if dialog_obs is None and ui_state.get("has_dialog"):
                dialog_obs = obs
            # View đang focus cũng tính là "đã thấy" (view không có text thì
            # không có trong all_visible_texts — CI-T5 mục 9: focus đã đứng
            # trên view đích thì gate không được đòi driver đi tìm nữa).
            _fsig = ui_state.get("focused_sig", "")
            if _fsig and _fsig != "NONE":
                _fid = _fsig.split("#")[0]
                if _fid and _fid != "view" and _fid not in views:
                    views.append(_fid)
            gate.observe(obs["activity"], texts, views, ui_state.get("has_dialog"),
                         obs["motion"], obs["t_offset"])
            # CI-T6 mục 8: đồng hồ phát của mission VOD (chỉ 2 mission VOD
            # có needs_playback_progress; live stream không có elapsed).
            # CI-T7 mục 4: truyền cả ảnh để _extract_playback_s OCR ép band
            # dưới khi dump/cache trống (osd False theo dump).
            obs["playback_s"] = None
            if spec.needs_playback_progress:
                obs["playback_s"] = self._extract_playback_s(
                    ui_state, obs["frame_ref"], obs.get("png"))
                gate.observe_playback(obs["playback_s"], obs["t_offset"])
            for f in obs["findings"]:
                print("      🔎 [%s] %s" % (f.get("severity"), f.get("issue")), flush=True)
                self.findings.append(f)

            self.timeline.append({
                "step_id": self._global_step,
                "step_in_mission": gate.steps,
                "time_offset_sec": obs["t_offset"],
                "mission": {"id": spec.name, "title": spec.title},
                "activity": obs["activity"],
                "active_tab": {"index": self.device.detect_tab_index(ui_state)},
                "ui_state": {"focused_view": ui_state.get("focused_sig"),
                             "focused_text": ui_state.get("focused_text"),
                             "focused_bounds": ui_state.get("focused_bounds"),
                             "has_focus_ring": obs["has_ring"],
                             "focus_ring_color": obs["ring_col"],
                             "image_focus_ring": obs.get("image_focus_ring", False),
                             "image_focus_box": obs.get("image_focus_box"),
                             "keyboard_open": ui_state.get("keyboard_open", False),
                             "keyboard_open_image": obs.get("keyboard_open_image")},
                "playback_state": {"is_playing": obs["motion"],
                                   # motion_delta -1 = chưa đủ mẫu để đo (không
                                   # rõ), KHÔNG phải 0.00 = đứng yên. Ghi None
                                   # để không che vấn đề đo motion (CI-T4:
                                   # PlayerActivity đo 0.00 ở 11/11 bước CI-T3
                                   # trong khi video có lúc phát thật).
                                   # CI-T5: khi watcher UNKNOWN mà fallback
                                   # pixel_diff đo được thì motion_delta là
                                   # số fallback (motion_source ghi rõ nguồn).
                                   "motion_delta": (round(obs["motion_delta"], 2)
                                                    if obs["motion_delta"] >= 0 else None),
                                   "motion_source": obs.get("motion_source", "watcher"),
                                   "playback_s": obs.get("playback_s")},
                "screenshot": obs["frame_file"],
                "duplicate_frame": obs.get("duplicate_frame", False),
                "observe_s": obs["observe_s"],
                "observe_breakdown": obs.get("observe_breakdown", {}),
            })
            self.timings["steps"] += 1
            self.timings["step_times"].append(round(time.time() - step_t0, 2))

            # CI-T6 mục 9: check này PHẢI đứng sau timeline.append —
            # bước mở player thay vì dialog vẫn là 1 observation thật,
            # phải ghi vào timeline trước khi FAIL (CI-T5: step_id 14
            # mất vì break trước append, timeline 79 entry mà step 1-80).
            # CI-T5 mục 9: phân biệt OK-mở-dialog vs OK-mở-player. Mission
            # cần dialog mà phím OK vừa rồi (rule open_dialog) lại mở PLAYER
            # (CI-T4 ROOM_PICKER step_018: OK trên thẻ trận mở player 'Đang
            # tải luồng...' chứ không mở dialog chọn phòng) — ghi nhận đúng
            # là 'mở player thay vì dialog' và FAIL ngay (dialog không thể
            # mở từ trong player), không PASS oan, không FAIL mù ở max_steps.
            if (last_action_rule == "open_dialog" and spec.needs_dialog
                    and "PlayerActivity" in (obs["activity"] or "")
                    and not ui_state.get("has_dialog") and not gate.dialog_seen):
                gate.force_fail(
                    "OK mở PLAYER thay vì dialog đích: bấm OK trên thẻ trận mở "
                    "%s (không thấy dialog chọn phòng) — mission cần dialog, "
                    "không phải player" % obs["activity"],
                    last_frame_ref)
                print("   ❌ [Mission FAIL] %s" % gate.outcome_reason, flush=True)
                break

            verdict, reason, _ev = gate.evaluate(last_frame_ref)
            if verdict == "VISION_PENDING":
                # Mọi tín hiệu rẻ đã xanh, chỉ còn vision: xác nhận 1 lần.
                ok = self._vision_confirm(spec, gate, obs)
                if not ok:
                    # Chưa xác nhận được: tiếp tục đi, tối đa 2 lần chối.
                    if gate.vision_denials >= 2:
                        gate.force_fail(
                            "vision 2 lần không xác nhận mục tiêu '%s' trên frame" % spec.target_desc,
                            last_frame_ref)
                        break
                    act = driver.next_action(ui_state, obs["activity"], obs["png"], obs["t_offset"])
                    self._log_action(act)
                    if act.type == "FAIL":
                        gate.force_fail(act.thought, last_frame_ref)
                        break
                    driver.execute(act)
                    self._note_seek_if_needed(gate, act, obs["activity"])
                    last_action_rule = act.rule
                    continue
                verdict, reason, _ev = gate.evaluate(last_frame_ref)
            if verdict == "PASS":
                print("   ✅ [Mission PASS] %s" % reason, flush=True)
                break
            if verdict == "FAIL":
                print("   ❌ [Mission FAIL] %s" % reason, flush=True)
                break

            action = driver.next_action(ui_state, obs["activity"], obs["png"], obs["t_offset"])
            self._log_action(action)
            print("      -> %s %s [%s]" % (action.type, action.param, action.rule), flush=True)
            if action.type == "FAIL":
                gate.force_fail(action.thought, last_frame_ref)
                print("   ❌ [Mission FAIL] %s" % action.thought, flush=True)
                break
            driver.execute(action)
            self._note_seek_if_needed(gate, action, obs["activity"])
            last_action_rule = action.rule

        if gate.outcome is None:
            verdict, reason, _ev = gate.evaluate(last_frame_ref)
            # Hết bước nhưng chỉ còn vision chưa xác nhận: cho 1 lần xác nhận
            # cuối (tối đa 2 lần chối tổng cộng) trước khi FAIL.
            if verdict == "VISION_PENDING" and spec.needs_vision \
                    and gate.vision_denials < 2 and last_obs:
                ok = self._vision_confirm(spec, gate, last_obs)
                if ok:
                    verdict, reason, _ev = gate.evaluate(last_frame_ref)
                if verdict != "PASS":
                    gate.force_fail(
                        "hết bước, vision %s xác nhận mục tiêu '%s'"
                        % ("không" if gate.vision_denials else "chưa kịp", spec.target_desc),
                        last_frame_ref)
                else:
                    print("   ✅ [Mission PASS] %s" % reason, flush=True)
            elif verdict != "PASS":
                gate.force_fail(reason or "hết bước mà gate chưa đủ tín hiệu", last_frame_ref)
                print("   ❌ [Mission FAIL] %s" % gate.outcome_reason, flush=True)

        # ảnh cuối mission + PSS
        pss = self.device.get_pss_memory_mb()
        if pss > 0:
            print("   📊 [Telemetry] RAM PSS: %.1f MB" % pss, flush=True)
        # CI-T8 mục 7: mission cần hàng LIVE thật mà run không có hàng LIVE
        # nào -> UNVERIFIED (chưa kiểm được detector (e)), không FAIL oan,
        # không tính vào tỉ lệ pass (judge coi outcome ngoài PASS/FAIL là
        # undecided). Điều kiện chạy sau khi gate đã kết luận xong. Kể cả
        # PASS cũng đổi: text nav "Trực tiếp" có sẵn ở mọi tab nên PASS
        # trên text đó mà không thấy hàng LIVE nào thì mission chưa kiểm
        # được gì — chỉ khi detector đã thấy hàng LIVE (cờ schedule_live_seen
        # đặt trong _observe) thì PASS mới giữ.
        # CI-T9 mục 4: PASS chỉ giữ khi đã thấy hàng LIVE CÓ tỉ số
        # (cờ schedule_live_with_score) — hàng LIVE không tỉ số thì
        # detector (e) đã tố bằng finding, mission chưa kiểm được trận
        # đang đá hiển thị tỉ số nên cũng UNVERIFIED, không PASS mềm.
        if getattr(spec, "requires_live_row", False):
            _live_seen = bool(self.detector_ctx.get("schedule_live_seen"))
            _live_scored = bool(self.detector_ctx.get("schedule_live_with_score"))
            if not _live_seen:
                gate.outcome = "UNVERIFIED"
                gate.outcome_reason = ("Không có hàng LIVE nào ở tab Lịch trong run này — "
                                       "chưa kiểm được tỉ số trận đang đá (UNVERIFIED)")
                print("   ❓ [Mission UNVERIFIED] %s: run không có hàng LIVE" % spec.name, flush=True)
            elif not _live_scored:
                gate.outcome = "UNVERIFIED"
                gate.outcome_reason = ("Có hàng LIVE ở tab Lịch nhưng không hàng nào có tỉ số — "
                                       "chưa kiểm được trận đang đá hiển thị tỉ số (UNVERIFIED)")
                print("   ❓ [Mission UNVERIFIED] %s: hàng LIVE không có tỉ số" % spec.name, flush=True)
        return self._finish_mission(spec, gate, last_obs and [last_obs] or [],
                                    dialog_obs=dialog_obs)

    def _finish_mission(self, spec, gate, _obs, dialog_obs=None):
        res = {"name": spec.name, "title": spec.title,
               "outcome": gate.outcome or "FAIL",
               "reason": gate.outcome_reason or "?",
               "evidence": gate.evidence, "steps": gate.steps}
        # CI-T8 mục 3 (step_051): mission cần dialog thì frame bằng chứng
        # phải là khung dialog ĐÃ THẤY (không phải khung cuối mission, lúc
        # đó dialog có thể đã đóng). Lưu khung dialog nếu chưa có, viết lại
        # evidence frame sang path đã lưu thật (kể cả khi dedup trả path cũ).
        if gate.outcome and spec.needs_dialog and dialog_obs is not None:
            _d_png = dialog_obs.get("png")
            _d_ref = dialog_obs.get("frame_ref")
            if _d_png and _d_ref:
                _d_saved = self._save_frame(
                    _d_png, _d_ref[:-4] if _d_ref.endswith(".jpg") else _d_ref)
                if _d_saved:
                    _d_base = os.path.basename(_d_saved)
                    if isinstance(res.get("evidence"), dict):
                        res["evidence"]["frame"] = _d_base
                    res["evidence_frame_dialog"] = _d_saved
        # Bằng chứng (vision confirm) phải tồn tại trên đĩa cho MỌI outcome:
        # frame chỉ được lưu khi có defect hoặc mỗi bước thứ 5, nên frame của
        # mission có thể chưa được lưu (CI-T2: step_085 trích dẫn trong
        # evidence của WebPlayer directed nhưng file thiếu trong artifact;
        # CI-T3: 6/7 frame evidence của mission FAIL thiếu). Lưu PNG của
        # observation cuối nếu file chưa tồn tại — PASS hay FAIL đều cần.
        if gate.outcome and _obs:
            last = _obs[0]
            png = last.get("png")
            frame_ref = (gate.evidence or {}).get("frame") or last.get("frame_ref")
            if png and frame_ref:
                path = os.path.join(self.shots_dir, os.path.basename(frame_ref))
                if not os.path.exists(path):
                    # CI-T7 mục 6: _finish_mission là đường bypass của check
                    # duplicate trong _observe — frame cuối mission có thể
                    # trùng hệt 1 shot đã lưu (CI-T6: 046=047, 026=037
                    # identical). Trùng thì KHÔNG lưu file mới, ghi rõ shot
                    # nào được dùng lại (bằng chứng vẫn có, không trùng file).
                    _h = hashlib.sha256(png).hexdigest()
                    if _h in self._saved_shot_hashes:
                        _dup = self._saved_shot_hashes[_h]
                        res["evidence_frame_duplicate_of"] = _dup
                        # CI-T8 mục 3: evidence phải trỏ file TỒN TẠI — viết
                        # lại frame sang shot đã lưu thay vì tên mới
                        # (step_035/042 CI-T7: evidence trỏ file không có).
                        if isinstance(res.get("evidence"), dict):
                            res["evidence"]["frame"] = os.path.basename(_dup)
                        print("   📸 [Evidence] frame cuối mission trùng shot đã lưu "
                              "(%s) — không lưu trùng, dùng lại %s"
                              % (gate.outcome, _dup), flush=True)
                    else:
                        saved = self._save_frame(png, frame_ref[:-4] if frame_ref.endswith(".jpg") else frame_ref)
                        if saved:
                            print("   📸 [Evidence] lưu frame cuối mission (%s): %s" % (gate.outcome, saved), flush=True)
        # CI-T8 mục 3: frame bằng chứng thiếu trên đĩa thì FAIL ỒN ÀO —
        # không được PASS/FAIL lặng lẽ với evidence trỏ file không tồn tại
        # (step_035/step_042 CI-T7). Kiểm tra sau mọi bước lưu/dedup ở trên.
        _ev_frame = (res.get("evidence") or {}).get("frame")
        if _ev_frame:
            _ev_path = os.path.join(self.shots_dir, os.path.basename(_ev_frame))
            if not os.path.exists(_ev_path):
                res["evidence_frame_missing"] = True
                res["reason"] = (res.get("reason") or "") + \
                    " | BẰNG CHỨNG THIẾU: frame %s không có trên đĩa" % _ev_frame
                # Chỉ PASS mới bị lật thành FAIL; UNVERIFIED (CI-T8 mục 7:
                # chưa kiểm được) giữ nguyên — thiếu frame không biến một
                # mission chưa kiểm được thành lỗi app.
                if res["outcome"] == "PASS":
                    res["outcome"] = "FAIL"
                    gate.outcome = "FAIL"
                    gate.outcome_reason = res["reason"]
                print("   ❌ [Evidence] frame bằng chứng %s THIẾU trên đĩa — FAIL ồn ào"
                      % _ev_frame, flush=True)
        self.mission_results.append(res)
        return res

    def run(self, missions):
        print("\n" + "=" * 65, flush=True)
        print("🚀 [KenhLive Realtime Vision QA] — perception rẻ, gate bằng chứng", flush=True)
        print("=" * 65 + "\n", flush=True)
        self.start_time = time.time()
        # Watcher PHẢI chạy trước mọi mission: nếu không start, wait_stable
        # chờ hết 8s mỗi bước, motion luôn False, mission cần motion FAIL oan.
        self.watcher.start()
        if VideoRecorder is not None:
            try:
                self.recorder = VideoRecorder(out_dir=self.out_dir)
                self.recorder.start()
            except Exception as e:
                print("⚠️ [VideoRecorder] %s" % e, flush=True)
        self.device.checkpoint_logcat()
        launch_ms = self.device.launch_app()
        print("📱 Khởi động app: %sms" % launch_ms if launch_ms > 0 else "📱 Không bắt được focus ngay", flush=True)
        time.sleep(1.5)
        for spec in missions:
            try:
                self.run_mission(spec)
            except Exception as e:
                print("   ⚠️ Mission %s lỗi: %s" % (spec.name, e), flush=True)
                import traceback
                traceback.print_exc()
                self.mission_results.append({
                    "name": spec.name, "title": spec.title, "outcome": "FAIL",
                    "reason": "runner exception: %s" % e, "evidence": {}, "steps": 0})
        # CI-T7 mục 5: DỪNG QUAY TRƯỚC giai đoạn post-processing dài (vision
        # check cuối run + dựng reel): xin dừng mềm để chunk cuối kết thúc
        # bằng expiry 175s tự nhiên trong lúc vision check chạy, thay vì bị
        # SIGINT cắt giữa chừng ở cuối run (CI-T6: video chỉ 79%, chunk cuối
        # mất moov). stop_and_save() sau vision check sẽ join worker (đã
        # thoát hoặc gần thoát) + kéo chunk đã finalize.
        if self.recorder:
            try:
                self.recorder.request_graceful_stop()
            except Exception as e:
                print("⚠️ [VideoRecorder] request_graceful_stop lỗi: %s" % e, flush=True)
        # Vision check hero + title player (CI-T5 mục 7): tối đa 2 call/run,
        # sau khi mọi mission xong (frame đã giữ trong run_mission).
        try:
            self._vision_overlap_checks()
        except Exception as e:
            print("   ⚠️ Vision overlap check lỗi: %s" % e, flush=True)
        video_info = None
        if self.recorder:
            try:
                video_info = self.recorder.stop_and_save()
            except Exception as e:
                print("⚠️ [VideoRecorder] %s" % e, flush=True)
        duration = round(time.time() - self.start_time)
        return self.finish(duration, video_info)

    def finish(self, duration_sec, video_info=None):
        try:
            self.watcher.stop()
        except Exception:
            pass
        video_file = None
        video_speed_factor = 1.0
        video_recorded_seconds = 0.0
        if isinstance(video_info, dict):
            v = video_info.get("full_tour")
            if v and os.path.exists(v):
                video_file = os.path.basename(v)
            video_speed_factor = video_info.get("speed_factor") or 1.0
            video_recorded_seconds = video_info.get("recorded_seconds") or 0.0
        elif isinstance(video_info, str) and os.path.exists(video_info):
            video_file = os.path.basename(video_info)
        # defect reel: video_t là thời gian thật, phải chia cho hệ số tốc độ
        # của tour (CI-T3: reel sai 4x). Ghi hệ số vào report để kiểm chứng.
        # CI-T8 mục 2: dùng chunk_map (QA_t -> tour_t theo từng chunk) khi
        # có — chia đều bị lệch do khoảng trống giữa các chunk.
        reel_path, reel_entries = self.judge.build_defect_reel(
            os.path.join(self.out_dir, video_file) if video_file else None, self.findings,
            speed_factor=video_speed_factor,
            chunk_map=(video_info.get("chunk_map") if isinstance(video_info, dict) else None))
        timings = dict(self.timings)
        step_times = timings.pop("step_times", [])
        if step_times:
            s = sorted(step_times)
            timings["per_step_p50_s"] = s[len(s) // 2]
            timings["per_step_p95_s"] = s[int(len(s) * 0.95)] if len(s) > 1 else s[0]
            timings["per_step_mean_s"] = round(sum(s) / len(s), 2)
        # CI-T8 mục 9: định nghĩa đo phải rõ ràng trong report — per_step_*
        # là WALL TIME mỗi bước (observe + gate + hành động driver + chờ ổn
        # định), KHÔNG phải chỉ observe. Reviewer CI-T7 tính lại từ timeline
        # observe_s (chỉ observe) nên ra p95/mean thấp hơn (20.01/8.91 so
        # với 21.95/9.61) — không phải lỗi tính, là khác định nghĩa. Ghi rõ
        # định nghĩa + percentiles observe-only từ timeline để 2 dãy số tự
        # khớp nhau trong cùng report.
        timings["per_step_definition"] = (
            "wall time mỗi bước = observe (wait+dump+detect) + gate + "
            "hành động driver + chờ ổn định; observe_* chỉ tính observe")
        _obs_times = sorted(
            e.get("observe_s") for e in self.timeline
            if isinstance(e.get("observe_s"), (int, float)))
        if _obs_times:
            timings["observe_p50_s"] = _obs_times[len(_obs_times) // 2]
            timings["observe_p95_s"] = _obs_times[int(len(_obs_times) * 0.95)] \
                if len(_obs_times) > 1 else _obs_times[0]
            timings["observe_mean_s"] = round(sum(_obs_times) / len(_obs_times), 2)
        timings["vision_calls"] = self.vision.calls_total
        timings["sync_retries"] = getattr(self, "_sync_retries", 0)  # CI-T7 mục 7
        timings["vision_s"] = round(sum(self.vision.latencies), 1)  # tổng mọi
        # loại vision call (confirm + stuck_assist + check); CI-T2 ghi 7.7s vì
        # chỉ cộng confirm — thực tế 7 call × 12.4s ≈ 87s.
        timings["vision_latency_mean_s"] = (
            round(sum(self.vision.latencies) / len(self.vision.latencies), 1)
            if self.vision.latencies else 0.0)
        timings["ocr_skipped_frames"] = self.detector_ctx.get("ocr_skipped", 0)
        report = self.judge.judge(
            self.mission_results, self.findings, self.unverified,
            duration_sec=duration_sec,
            vision_calls={"total": self.vision.calls_total,
                          "by_reason": dict(self.vision.calls_by_reason),
                          "provider": self.vision.provider},
            timings=timings)
        report["video"] = video_file
        report["video_speed_factor"] = video_speed_factor
        report["video_recorded_seconds"] = video_recorded_seconds
        # CI-T7 mục 5: screenrecord đã chết xác minh bằng pidof trước khi
        # chờ moov (False = vẫn chạy lúc dừng — chunk cuối có nguy cơ mất).
        if isinstance(video_info, dict):
            report["video_screenrecord_exited"] = video_info.get("screenrecord_exited")
            report["video_graceful_stop"] = video_info.get("graceful_stop")
        # CI-T6 mục 2: log vision check (frame nào, crop nào, kết quả gì) phải
        # nằm trong report để lần sau debug được cú bỏ sót mà không cần đoán.
        report["vision_checks"] = list(self.vision_check_log)
        report["defect_reel"] = os.path.basename(reel_path) if reel_path else None
        report["defect_reel_entries"] = reel_entries
        # CI-T6 mục 3: báo rõ reel khớp bao nhiêu finding (entry vượt tour
        # bị kẹp thì không tính là khớp đúng thời điểm).
        # CI-T8 mục 2: thêm số đoạn khớp NỘI DUNG với shot trích dẫn
        # (content_verified) — 'covered' chỉ tính theo timestamp.
        _cov = sum(1 for e in reel_entries if e.get("covered", True))
        _cv = sum(1 for e in reel_entries if e.get("content_verified") is True)
        _nver = sum(1 for e in reel_entries if e.get("content_verified") is not None)
        _clamp = sum(1 for e in reel_entries if e.get("clamped"))
        report["defect_reel_coverage"] = {
            "covered": _cov, "content_verified": _cv,
            "total": len(reel_entries), "clamped": _clamp,
            "text": "%d/%d finding%s%s%s" % (
                _cov, len(reel_entries),
                " (%d đoạn bị kẹp do vượt tour)" % _clamp if _clamp else "",
                " · nội dung khớp: %d/%d" % (_cv, _nver) if _nver else "",
                " · timebase: %s" % (video_info.get("timebase") if isinstance(video_info, dict) else "uniform"))}
        print("   🎞️ [Reel] cover %s" % report["defect_reel_coverage"]["text"], flush=True)
        if isinstance(video_info, dict) and video_info.get("timebase"):
            report["video_timebase"] = video_info.get("timebase")
            report["video_chunk_map"] = video_info.get("chunk_map")
        # CI-T6 mục 10: ghi rõ provider thật ở cấp report (không ghi 'NIM'
        # khi provider là OPENAI — CI-T5 report ghi nim_usage.provider đúng
        # là OPENAI nhưng dòng in + HTML vẫn ghi 'NIM requests'). requests
        # đếm được là số gửi tới endpoint_host (limiter chỉ throttle host
        # NIM — xem DESIGN §8.1).
        report["vision_provider"] = self.vision.provider
        report["vision_endpoint_host"] = self.vision.endpoint_host
        # CI-T8 mục 7: run có thấy hàng LIVE nào ở tab Lịch không — nếu
        # không thì detector (e) chưa được kiểm: ghi UNTESTED vào unverified,
        # không im lặng như CI-T7.
        _live_seen = bool(self.detector_ctx.get("schedule_live_seen"))
        report["schedule_live_seen"] = _live_seen
        # CI-T9 mục 4: run có thấy hàng LIVE CÓ tỉ số không (gate mission
        # chỉ giữ PASS khi cờ này đặt — xem run_mission).
        report["schedule_live_with_score"] = bool(
            self.detector_ctx.get("schedule_live_with_score"))
        if not _live_seen:
            # judge giữ reference list unverified nên append vào
            # self.unverified là đủ — không append thêm vào report.
            self.unverified.append({
                "reason": "schedule_live_no_score",
                "detail": "Run không có hàng LIVE nào ở tab Lịch — detector (e) "
                          "'hàng LIVE chỉ hiện giờ kickoff thay vì tỉ số' chưa được "
                          "kiểm (UNTESTED, không phải PASS)",
                "severity": "UNTESTED"})
        # CI-T8 mục 5: fallback provider đã dùng (nếu có) — ghi rõ để biết
        # bao nhiêu vision call chạy qua provider dự phòng (nim_usage cũng
        # có fallback_provider/fallback_used).
        if getattr(self.vision, "fallback_used", 0):
            report["vision_fallback"] = {"provider": self.vision.fallback_provider,
                                         "used": self.vision.fallback_used}
        # NIM usage (luật cứng 40 req/phút): requests đã dùng + có chạm 429?
        report["nim_usage"] = self.vision.nim_stats()
        report["screenshots"] = [(e.get("mission", {}).get("id", ""), e.get("screenshot"))
                                 for e in self.timeline if e.get("screenshot")]
        with open(os.path.join(self.out_dir, "qa_report.json"), "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        self.judge.render_html(report, os.path.join(self.out_dir, "qa_report.html"))
        # qa_session.json tương thích replay (timeline như harness cũ)
        session_manifest = {
            "session_id": "RT-%d" % int(self.start_time),
            "duration_sec": duration_sec,
            "final_score": report["score"],
            "video_tour": video_file,
            "timeline": self.timeline,
            "stats": {"total_steps": len(self.timeline),
                      "defects_count": len(self.findings)},
            "ai_brain": {"provider": self.vision.provider},
        }
        with open(os.path.join(self.out_dir, "qa_session.json"), "w", encoding="utf-8") as f:
            json.dump(session_manifest, f, ensure_ascii=False, indent=2)
        print("\n🏁 Realtime QA xong trong %ss — điểm %d/100, %s, vision %d calls | "
              "Vision: %s qua %s · requests %d (giới hạn 30/phút), chạm 429: %s" % (
            duration_sec, report["score"], report["missions_passed"],
            self.vision.calls_total,
            self.vision.provider, self.vision.endpoint_host or "?",
            report["nim_usage"].get("requests_used", 0),
            "CÓ — LỖI THIẾT KẾ, SỬA Ở VÒNG SAU" if report["nim_usage"].get("hit_429") else "không"), flush=True)
        return report

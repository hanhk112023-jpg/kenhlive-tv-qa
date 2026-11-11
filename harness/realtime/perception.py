#!/usr/bin/env python3
"""KenhLive Realtime QA — vòng perception (watcher lấy mẫu liên tục, rẻ).

Thay cho "mỗi bước gọi vision 22s": watcher chạy nền, lấy mẫu screencap
~1,2s/lần, tính pixel-diff cục bộ (PIL) để biết màn hình có đang đổi không.
Runner chỉ làm việc nặng (UI dump, detector) khi màn hình đã ỔN ĐỊNH.
Vision không nằm trong vòng này.
"""
import threading
import time

from device import RealtimeDevice

DIFF_CHANGE_PCT = 1.5      # trên ngưỡng này: màn hình đang đổi
STABLE_SAMPLES = 2         # số mẫu liên tiếp dưới ngưỡng để coi là ổn định
SAMPLE_PERIOD_S = 1.0      # chu kỳ lấy mẫu
MOTION_WINDOW_S = 4.0      # cửa sổ đo motion video (CI-T2: cửa sổ 2s với chu
                           # kỳ 1.2s chỉ chứa ~1.7 mẫu -> motion_delta hay
                           # trả -1 (thiếu mẫu) nên 98% bước player đo 0.00
                           # dù video đang phát; cửa sổ 4s chứa ~3-4 mẫu)
MOTION_PLAYING_PCT = 0.35  # motion trung bình trên ngưỡng này: video đang chạy


class ScreenWatcher:
    """Thread lấy mẫu màn hình liên tục. Không gọi vision, không gọi uiautomator."""

    def __init__(self, device, period_s=SAMPLE_PERIOD_S):
        self.device = device
        self.period_s = period_s
        self._stop = threading.Event()
        self._thread = None
        self._lock = threading.Lock()
        self._latest_png = None
        self._latest_small = None
        self._last_diff = -1.0
        self._samples = 0
        self._stable_streak = 0
        self._history = []  # (t, diff) — để đo motion trong cửa sổ ngắn
        self._started_at = None

    def start(self):
        self._started_at = time.time()
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        time.sleep(0.3)

    def stop(self):
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=3)

    def _loop(self):
        while not self._stop.is_set():
            t0 = time.time()
            png = self.device.screencap_bytes()
            if png:
                diff = -1.0
                with self._lock:
                    if self._latest_png is not None:
                        diff = RealtimeDevice.pixel_diff(self._latest_png, png)
                    self._latest_png = png
                    self._last_diff = diff
                    self._samples += 1
                    now = time.time()
                    self._history.append((now, max(0.0, diff)))
                    self._history = [(tt, d) for (tt, d) in self._history
                                     if now - tt <= MOTION_WINDOW_S + 1.0]
                    if diff >= 0.0 and diff < DIFF_CHANGE_PCT:
                        self._stable_streak += 1
                    elif diff >= DIFF_CHANGE_PCT:
                        self._stable_streak = 0
            dt = time.time() - t0
            time.sleep(max(0.05, self.period_s - dt))

    # -- truy vấn trạng thái (thread-safe, nhanh) ----------------------
    def latest_png(self):
        with self._lock:
            return self._latest_png

    def last_diff(self):
        with self._lock:
            return self._last_diff

    def is_stable(self):
        with self._lock:
            return self._stable_streak >= STABLE_SAMPLES

    def motion_delta(self):
        """Motion trung bình trong cửa sổ MOTION_WINDOW_S (%). -1 nếu chưa đủ mẫu."""
        with self._lock:
            now = time.time()
            win = [d for (tt, d) in self._history if now - tt <= MOTION_WINDOW_S]
        if len(win) < 2:
            return -1.0
        return sum(win) / len(win)

    @staticmethod
    def fallback_pixel_diff(png_a, png_b):
        """% khác biệt giữa 2 frame quan sát liên tiếp (RealtimeDevice.
        pixel_diff trên ảnh 160x90, rẻ ~ms). -1.0 khi chưa đủ frame.
        CI-T5: watcher đói mẫu khi dump WebPlayer dài (26.6s) — cửa sổ
        motion 4s không còn mẫu nào nên motion_delta = -1 (UNKNOWN) dù
        phim đang phát (CI-T4 VOD FAIL oan). Runner dùng fallback này để
        đo motion trực tiếp từ 2 frame đã có, thay vì kết luận 'đứng yên'."""
        return RealtimeDevice.pixel_diff(png_a, png_b)

    def is_video_playing(self):
        d = self.motion_delta()
        return d >= MOTION_PLAYING_PCT if d >= 0 else False

    def sample_count(self):
        with self._lock:
            return self._samples

    def wait_stable(self, timeout_s=8.0):
        """Chờ màn hình ổn định (2 mẫu liên tiếp diff < ngưỡng). Trả (png, waited_s).
        Hết timeout thì trả frame mới nhất + waited_s (kèm cờ timeout=True).
        Video đang phát: màn hình không bao giờ 'ổn định' (diff luôn cao) — lấy
        frame mới nhất sau ~2.5s thay vì chờ hết 8s, nếu không mỗi bước ở
        mission player tốn 8s chờ vô ích."""
        t0 = time.time()
        while time.time() - t0 < timeout_s:
            if self.is_stable():
                png = self.latest_png()
                if png:
                    return png, round(time.time() - t0, 2), False
            if time.time() - t0 > 2.5 and self.is_video_playing():
                return self.latest_png(), round(time.time() - t0, 2), True
            time.sleep(0.15)
        return self.latest_png(), round(time.time() - t0, 2), True

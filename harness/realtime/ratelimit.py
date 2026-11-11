#!/usr/bin/env python3
"""KenhLive Realtime QA — rate limiter cho NVIDIA NIM (luật cứng Evelyn 13:42).

NIM giới hạn 40 request/phút. Harness tự giới hạn ở **30 req/phút** (chừa
biên an toàn), KHÔNG BAO GIỜ burst. Mọi call NIM — vision điều hướng,
confirm, check defect, judge — đều đi qua đúng một limiter duy nhất này.

- Sliding window 60s, đếm request đã gửi; acquire() chặn cho tới khi có slot.
- Gặp HTTP 429: KHÔNG retry dồn dập. Đọc Retry-After (nếu có), chờ hết cửa
  sổ, rồi chạy tiếp ở tốc độ thấp hơn một nửa (15 req/phút) cho tới hết run.
- 429 là lỗi HẠ TẦNG, không phải lỗi app: limiter chỉ ghi log + đếm; caller
  phải biến kết quả thành UNVERIFIED, không bao giờ thành finding hay trừ điểm.
- Stats được báo cáo trong mọi report: requests đã dùng, số lần chạm 429,
  tổng thời gian chờ throttle. Chạm trần 429 trong một lần chạy = lỗi thiết
  kế, phải sửa ở vòng sau.
"""
import threading
import time

# 30 req/phút: dưới trần 40 của NIM với biên 25%.
MAX_PER_MIN = 30
WINDOW_S = 60.0
# Sau 429: chờ tối thiểu từng này + Retry-After (nếu có), rồi giảm một nửa.
BACKOFF_MIN_S = 60.0


class RateLimiter:
    """Một limiter duy nhất cho cả process. Thread-safe."""

    def __init__(self, max_per_min=MAX_PER_MIN, window_s=WINDOW_S):
        self.max_per_min = float(max_per_min)
        self.window_s = float(window_s)
        self._lock = threading.Lock()
        self._stamps = []          # thời gian gửi request (monotonic)
        self.requests = 0          # tổng request đã gửi
        self.retries = 0           # số lần gửi lại sau 429/lỗi (mỗi lần gửi lại ĐÃ đếm trong requests)
        self.throttled_waits = 0   # số lần phải chờ slot
        self.throttled_wait_s = 0.0
        self.hits_429 = 0          # số lần nhận 429
        self.backoff_until = 0.0   # monotonic: không gửi trước thời điểm này
        self.degraded = False      # True sau 429: tốc độ giảm một nửa
        self._degraded_max = max_per_min

    def _effective_max(self):
        return self._degraded_max if self.degraded else self.max_per_min

    def _prune(self, now):
        cut = now - self.window_s
        self._stamps = [t for t in self._stamps if t > cut]

    def acquire(self, timeout=300.0):
        """Chặn cho tới khi có slot trong cửa sổ. Trả thời gian đã chờ (s).
        Sleep LUÔN ngoài lock để stats()/record_429() từ thread khác không bị
        chặn trong lúc chờ."""
        waited = 0.0
        deadline = time.monotonic() + timeout
        while True:
            with self._lock:
                now = time.monotonic()
                if now < self.backoff_until:
                    wait = min(self.backoff_until - now, deadline - now)
                    if wait <= 0:
                        raise TimeoutError("rate limiter: hết thời gian chờ backoff 429")
                    self.throttled_waits += 1
                    self.throttled_wait_s += wait
                    waited += wait
                else:
                    self._prune(now)
                    if len(self._stamps) < self._effective_max():
                        self._stamps.append(now)
                        self.requests += 1
                        return round(waited, 2)
                    # Chờ request cũ nhất rơi khỏi cửa sổ (+ biên 0.5s).
                    wait = self._stamps[0] + self.window_s - now + 0.5
                    if wait <= 0:
                        wait = 0.5
                    wait = min(wait, deadline - now)
                    if wait <= 0:
                        raise TimeoutError("rate limiter: hết thời gian chờ slot")
                    self.throttled_waits += 1
                    self.throttled_wait_s += wait
                    waited += wait
            time.sleep(wait)

    def wait_backoff(self, timeout=300.0):
        """Chờ hết cửa sổ backoff 429 mà KHÔNG chiếm slot, KHÔNG đếm request.
        Dùng sau record_429, trước lần gửi lại: lần acquire() tiếp theo mới
        là request thật (nó đã được acquire() đếm). CI-T4: _post cũ gọi
        acquire() để chờ rồi acquire() lại để gửi — 1 lần gửi lại đếm thành
        2 requests (6 vision calls -> 8 NIM requests trong replay tự chạy)."""
        waited = 0.0
        deadline = time.monotonic() + timeout
        while True:
            with self._lock:
                now = time.monotonic()
                if now >= self.backoff_until:
                    return round(waited, 2)
                wait = min(self.backoff_until - now, deadline - now)
                if wait <= 0:
                    raise TimeoutError("rate limiter: hết thời gian chờ backoff 429")
                self.throttled_waits += 1
                self.throttled_wait_s += wait
                waited += wait
            time.sleep(wait)

    def note_retry(self):
        """Ghi một lần gửi lại (chỉ đếm riêng để đọc stats, không cộng requests
        ở đây — request gửi lại đã đếm trong acquire() của nó)."""
        with self._lock:
            self.retries += 1

    def record_429(self, retry_after_s=None):
        """Ghi một lần 429: chờ hết cửa sổ rồi giảm tốc độ một nửa."""
        with self._lock:
            self.hits_429 += 1
            wait = BACKOFF_MIN_S
            if retry_after_s:
                try:
                    wait = max(wait, float(retry_after_s))
                except Exception:
                    pass
            self.backoff_until = max(self.backoff_until,
                                     time.monotonic() + wait)
            self.degraded = True
            self._degraded_max = max(5.0, self.max_per_min / 2.0)
        return wait

    def stats(self):
        with self._lock:
            return {
                "requests_used": self.requests,
                "retries": self.retries,
                "limit_per_min": int(self.max_per_min),
                "effective_limit_per_min": int(self._effective_max()),
                "hit_429": self.hits_429 > 0,
                "hits_429": self.hits_429,
                "degraded_after_429": self.degraded,
                "throttled_waits": self.throttled_waits,
                "throttled_wait_s": round(self.throttled_wait_s, 1),
            }


# Một instance duy nhất cho cả process: mọi provider NIM dùng chung.
LIMITER = RateLimiter()

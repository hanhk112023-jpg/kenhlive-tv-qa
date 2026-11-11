#!/usr/bin/env python3
"""KenhLive Realtime QA — vision client (dùng ít, dùng đúng chỗ).

Provider chain GIỐNG harness cũ, đọc từ biến môi trường mà preflight của
qa-suite.yml đã set (OPENAI_API_BASE/KEY/MODEL = Gemini / NVIDIA NIM /
Meteor). Không hardcode key, không thêm provider mới.

Chỉ dùng cho 3 việc (DESIGN.md §8):
  1. confirm_target — xác nhận mục tiêu mission trên frame ổn định gần nhất.
  2. check_visual   — xác minh một defect nghi vấn (crop vùng nghi).
  3. stuck_assist    — gợi ý hành động khi driver kẹt.
Timeout 30s, retry 1. Không parse được / timeout -> None (UNVERIFIED),
KHÔNG bao giờ trả điểm mặc định.

Rate limit (luật cứng Evelyn 2026-11-11 13:42): NIM giới hạn 40 req/phút.
Mọi call tới integrate.api.nvidia.com đều qua ratelimit.LIMITER (tối đa
30 req/phút, không burst). Gặp HTTP 429: ghi nhận, chờ hết cửa sổ, thử lại
đúng 1 lần ở tốc độ giảm một nửa; 429 lần 2 -> RateLimitedError, caller
phải biến thành UNVERIFIED (lỗi hạ tầng, KHÔNG phải lỗi app, không trừ điểm).
"""
import base64
import io
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

UA = "KenhLive-RealtimeQA/1.0"


class RateLimitedError(Exception):
    """NIM trả 429 lần 2 (sau 1 lần chờ + retry). Lỗi hạ tầng, không phải app."""


def _is_nim_url(url):
    from urllib.parse import urlparse
    return urlparse(url or "").netloc.lower() == "integrate.api.nvidia.com"


# Backoff giữa các lần thử lại khi gặp lỗi HẠ TẦNG transport (NIM đóng kết
# nối giữa chừng): lần 1 chờ 2s, lần 2 chờ 10s. Hằng số module để mock test
# có thể rút ngắn khi kiểm chứng offline.
_TRANSPORT_BACKOFF_S = (2, 10)


def _is_transport_error(e):
    """Lỗi hạ tầng mạng (không phải lỗi app/model): kết nối bị đóng/reset,
    timeout, broken pipe — đáng thử lại. Lỗi khác (HTTP 4xx, JSON hỏng)
    thì không."""
    if isinstance(e, (ConnectionError, TimeoutError)):
        return True
    if isinstance(e, urllib.error.URLError):
        reason = getattr(e, "reason", None)
        if isinstance(reason, (ConnectionError, TimeoutError)):
            return True
    msg = str(e).lower()
    return any(k in msg for k in ("remote end closed", "closed connection",
                                  "timed out", "connection reset",
                                  "broken pipe", "connection aborted"))

DEEPSEEK_BASE = os.environ.get("DEEPSEEK_API_BASE", os.environ.get("FREEDEEPSEEK_API_BASE", ""))
DEEPSEEK_KEY = os.environ.get("DEEPSEEK_API_KEY", "free")
DEEPSEEK_MODEL = os.environ.get("DEEPSEEK_MODEL", "deepseek-v4-flash")

ANTIGRAVITY_BASE = os.environ.get("ANTIGRAVITY_API_BASE", "")
ANTIGRAVITY_KEY = os.environ.get("ANTIGRAVITY_API_KEY", "")
ANTIGRAVITY_MODEL = os.environ.get("ANTIGRAVITY_MODEL", "gemini-3.8-flash")

KILO_BASE = os.environ.get("KILO_API_BASE", "https://api.kilo.ai/api/gateway/v1/chat/completions")
KILO_KEY = os.environ.get("KILO_API_KEY", "")
KILO_MODEL = os.environ.get("KILO_MODEL", "kilo-auto/free")

OPENAI_BASE = os.environ.get("OPENAI_API_BASE", "")
OPENAI_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "")

NVIDIA_NIM_BASE = "https://integrate.api.nvidia.com/v1/chat/completions"
NVIDIA_NIM_MODEL = "nvidia/nemotron-3.5-super-vl-120b-a12b"

REASONING_MODELS = ("nemotron-3.5-super-vl", "step-5", "nemotron-nano")


def _max_tokens_for(model, default):
    m = (model or "").lower()
    if any(k in m for k in REASONING_MODELS):
        return max(default, 5000)
    return default


def _normalize_url(url):
    u = (url or "").rstrip("/")
    if u.endswith("/chat/completions"):
        return u
    if u.endswith("/v1"):
        return "%s/chat/completions" % u
    return "%s/chat/completions" % u


def _compress_b64(png_bytes, max_side=960, quality=75):
    try:
        from PIL import Image
        im = Image.open(io.BytesIO(png_bytes)).convert("RGB")
        im.thumbnail((max_side, max_side * 9 // 16))
        buf = io.BytesIO()
        im.save(buf, format="JPEG", quality=quality)
        return base64.b64encode(buf.getvalue()).decode()
    except Exception:
        return base64.b64encode(png_bytes).decode() if png_bytes else ""


def _post(url, key, payload, timeout, user=None, surrogate=None,
          surrogate_host=None):
    is_nim = _is_nim_url(url)
    headers = {"Content-Type": "application/json", "User-Agent": UA}
    if surrogate is None:
        headers["Authorization"] = "Bearer " + key
    if user:
        headers["x-agent-session"] = user
        payload["user"] = user
    req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers=headers)
    if surrogate is not None:
        sys_path = "/opt/muse/skills/custom-connector-setup/bin"
        if sys_path not in sys.path:
            sys.path.insert(0, sys_path)
        from dynamic_credentials import add_surrogate_to_request
        add_surrogate_to_request(req, surrogate, allowed_hosts=[surrogate_host])
    for attempt in range(3):
        try:
            if is_nim:
                # Luật cứng 40 req/phút của NIM: throttle client-side ở 30/phút.
                from ratelimit import LIMITER
                LIMITER.acquire()
            raw = urllib.request.urlopen(req, timeout=timeout).read().decode()
            if raw.strip().startswith("data:"):
                parts = []
                for line in raw.splitlines():
                    line = line.strip()
                    if line.startswith("data:"):
                        chunk = line[5:].strip()
                        if chunk == "[DONE]":
                            break
                        try:
                            ch = json.loads(chunk)
                            d = (ch.get("choices") or [{}])[0].get("delta") or {}
                            parts.append(d.get("content") or d.get("reasoning_content") or "")
                        except Exception:
                            pass
                return "".join(parts).strip()
            data = json.loads(raw)
            msg = (data.get("choices") or [{}])[0].get("message") or {}
            out = msg.get("content") or msg.get("reasoning_content") or ""
            if isinstance(out, list):
                out = "".join(p.get("text", "") if isinstance(p, dict) else str(p) for p in out)
            return str(out).strip()
        except urllib.error.HTTPError as e:
            if e.code == 429:
                # 429 là lỗi HẠ TẦNG: không retry dồn dập, không tính vào app.
                if is_nim:
                    from ratelimit import LIMITER
                    retry_after = None
                    try:
                        retry_after = e.headers.get("Retry-After")
                    except Exception:
                        pass
                    LIMITER.record_429(retry_after)
                    if attempt == 0:
                        # Chờ hết cửa sổ rồi thử lại đúng 1 lần ở tốc độ đã
                        # giảm một nửa. wait_backoff KHÔNG chiếm slot/không
                        # đếm request — chỉ lần gửi lại mới tính (CI-T4: cũ
                        # acquire() thêm 1 lần để chờ nên 6 calls đếm thành 8).
                        LIMITER.wait_backoff()
                        LIMITER.note_retry()
                        continue
                raise RateLimitedError("rate_limited_429")
            if attempt >= 1:
                raise
            time.sleep(2)
        except Exception as e:
            # Lỗi transport hạ tầng (NIM đóng kết nối giữa chừng): thử lại
            # tối đa 2 lần nữa với backoff dài dần (2s rồi 10s). Bằng chứng
            # replay R6: check P0-3 rớt 2 lần liên tiếp với 'Remote end
            # closed connection' nhưng gọi lại ngay sau đó thành công 2/3
            # lần (found=True) — retry 2s cũ không đủ để qua cơn chập chờn.
            # Mỗi lần thử lại là 1 request thật (đếm trong requests_used),
            # không tính là retry-429, không ảnh hưởng điểm app.
            if _is_transport_error(e) and attempt < 2:
                time.sleep(_TRANSPORT_BACKOFF_S[attempt])
                continue
            if attempt >= 1:
                raise
            time.sleep(2)
    return ""


def _extract_json(text):
    if not text:
        return None
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if not m:
        return None
    try:
        return json.loads(re.sub(r",\s*([\]}])", r"\1", m.group(0)))
    except Exception:
        return None


class VisionClient:
    """Vision dùng cho xác nhận + xác minh defect. Đếm số call để giữ ngân sách."""

    def __init__(self, budget=40):
        self.budget = int(budget)
        self.calls_total = 0
        self.calls_by_reason = {}
        self.latencies = []
        self.provider = self._detect_provider()
        self.endpoint_host = self._detect_endpoint_host()

    def _detect_endpoint_host(self):
        """Host thật mà request vision được gửi tới — KHÁC provider khi
        provider chạy qua URL tương thích NIM (CI-T5: provider OPENAI nhưng
        request đi tới integrate.api.nvidia.com nên limiter NIM vẫn đếm;
        report ghi 'NIM requests' là sai nhãn dù số đếm đúng). Dùng để ghi
        nhãn đúng trong report: 'Vision: OPENAI qua integrate.api.nvidia.com'.
        NONE -> '' (không có endpoint)."""
        from urllib.parse import urlparse
        _base = {"NVIDIA_NIM": NVIDIA_NIM_BASE,
                 "OPENAI": OPENAI_BASE,
                 "DEEPSEEK_WEB": DEEPSEEK_BASE,
                 "ANTIGRAVITY": ANTIGRAVITY_BASE,
                 "KILO": KILO_BASE}.get(self.provider, "")
        return urlparse(_base or "").netloc.lower() or ""

    def _detect_provider(self):
        if DEEPSEEK_BASE:
            return "DEEPSEEK_WEB"
        if ANTIGRAVITY_KEY and ANTIGRAVITY_BASE:
            return "ANTIGRAVITY"
        if KILO_KEY and KILO_BASE:
            return "KILO"
        if OPENAI_KEY and OPENAI_BASE:
            return "OPENAI"
        # Không có env provider (chạy local) -> NVIDIA NIM qua surrogate của
        # connector custom.nvidia (đã đăng ký, không cần key mới).
        try:
            sys_path = "/opt/muse/skills/custom-connector-setup/bin"
            if sys_path not in sys.path:
                sys.path.insert(0, sys_path)
            import dynamic_credentials  # noqa: F401
            return "NVIDIA_NIM"
        except Exception:
            return "NONE"

    def available(self):
        return self.provider != "NONE"

    def remaining(self):
        return max(0, self.budget - self.calls_total)

    def nim_stats(self):
        """Thống kê limiter NIM cho report (requests đã dùng / chạm 429?).
        requests_used = số request THẬT đã gửi (gửi lại sau 429 cũng tính,
        vì nó là 1 request thật; chờ backoff thì KHÔNG tính — xem
        ratelimit.wait_backoff). provider ghi rõ để biết số này thuộc về ai
        (CI-T3 chạy provider OPENAI qua URL NIM-compatible nên limiter vẫn
        đếm, nhưng report cũ không ghi provider)."""
        try:
            from ratelimit import LIMITER
            stats = LIMITER.stats()
            stats["provider"] = self.provider
            stats["endpoint_host"] = self.endpoint_host
            return stats
        except Exception:
            return {"requests_used": 0, "limit_per_min": 30,
                    "hit_429": False, "hits_429": 0, "provider": self.provider,
                    "endpoint_host": self.endpoint_host}

    def _chat(self, prompt, image_bytes, max_tokens, timeout, reason, user="qa_realtime",
              max_side=960):
        if not self.available() or self.remaining() <= 0:
            return None, "unavailable_or_budget"
        b64 = _compress_b64(image_bytes, max_side=max_side)
        content = [{"type": "text", "text": prompt}]
        if b64:
            content.append({"type": "image_url",
                            "image_url": {"url": "data:image/jpeg;base64,%s" % b64}})
        msgs = [{"role": "user", "content": content}]
        t0 = time.time()
        raw = ""
        err = None
        try:
            if self.provider == "NVIDIA_NIM":
                raw = _post(NVIDIA_NIM_BASE, "",
                            {"model": NVIDIA_NIM_MODEL, "temperature": 0.1,
                             "max_tokens": _max_tokens_for(NVIDIA_NIM_MODEL, max_tokens),
                             "messages": msgs}, timeout, user=user,
                            surrogate="custom.nvidia",
                            surrogate_host="integrate.api.nvidia.com")
            elif self.provider == "DEEPSEEK_WEB":
                raw = _post(_normalize_url(DEEPSEEK_BASE), DEEPSEEK_KEY,
                            {"model": DEEPSEEK_MODEL, "temperature": 0.1,
                             "max_tokens": _max_tokens_for(DEEPSEEK_MODEL, max_tokens),
                             "messages": msgs}, timeout, user=user)
            elif self.provider == "ANTIGRAVITY":
                raw = _post(_normalize_url(ANTIGRAVITY_BASE), ANTIGRAVITY_KEY,
                            {"model": ANTIGRAVITY_MODEL, "temperature": 0.1,
                             "max_tokens": _max_tokens_for(ANTIGRAVITY_MODEL, max_tokens),
                             "messages": msgs}, timeout)
            elif self.provider == "KILO":
                raw = _post(KILO_BASE, KILO_KEY,
                            {"model": KILO_MODEL, "temperature": 0.1,
                             "max_tokens": _max_tokens_for(KILO_MODEL, max_tokens),
                             "messages": msgs}, timeout)
            else:
                raw = _post(_normalize_url(OPENAI_BASE), OPENAI_KEY,
                            {"model": OPENAI_MODEL, "temperature": 0.1,
                             "max_tokens": _max_tokens_for(OPENAI_MODEL, max_tokens),
                             "messages": msgs}, timeout, user=user)
        except Exception as e:
            err = str(e)[:120]
        dt = round(time.time() - t0, 1)
        self.calls_total += 1
        self.calls_by_reason[reason] = self.calls_by_reason.get(reason, 0) + 1
        self.latencies.append(dt)
        if err or not raw:
            return None, "error:%s" % (err or "empty")
        return _extract_json(raw), None

    # -- 3 trường hợp dùng duy nhất ------------------------------------
    def confirm_target(self, image_bytes, target_desc, timeout=30):
        """Xác nhận mục tiêu có đang hiển thị không. Trả dict {confirmed, quote} hoặc None."""
        prompt = (
            "Bạn đang xem ảnh chụp màn hình Android TV 1920x1080 của app KenhLive. "
            "Mục tiêu cần xác nhận: %s\n"
            "Chỉ trả JSON: {\"confirmed\": true/false, \"quote\": \"chuỗi chữ bạn NHÌN THẤY "
            "chứng minh mục tiêu (trích nguyên văn, tối đa 12 từ)\"}. "
            "Không thấy rõ thì confirmed=false. Không bịa." % target_desc)
        res, err = self._chat(prompt, image_bytes, max_tokens=600, timeout=timeout,
                              reason="confirm_target")
        if res is None:
            return None, err
        return {"confirmed": bool(res.get("confirmed")),
                "quote": str(res.get("quote", ""))[:120]}, None

    def check_visual(self, image_bytes, question, timeout=30, crop=None, max_side=None):
        """Xác minh một defect nghi vấn. Trả dict {found, severity, detail} hoặc None.
        crop=(x0,y0,x1,y1) theo tọa độ 1920x1080: cắt đúng vùng nghi trước khi
        hỏi — model tập trung, ít bỏ sót lỗi ở mép/vùng nhỏ. Vùng crop được gửi
        ở độ phân giải cao hơn (max_side 1280) để lỗi vài px vẫn nhìn thấy."""
        if crop:
            try:
                from PIL import Image
                im = Image.open(io.BytesIO(image_bytes)).convert("RGB")
                w, h = im.size
                x0, y0, x1, y1 = crop
                box = (int(x0 * w / 1920), int(y0 * h / 1080),
                       int(x1 * w / 1920), int(y1 * h / 1080))
                buf = io.BytesIO()
                im.crop(box).save(buf, format="PNG")
                image_bytes = buf.getvalue()
            except Exception:
                pass
        prompt = (
            "Bạn đang xem ảnh chụp màn hình Android TV 1920x1080 của app KenhLive. "
            "Câu hỏi kiểm tra: %s\n"
            "Trước khi kết luận, HÃY ĐỌC NGUYÊN VĂN tất cả dòng chữ nhìn thấy "
            "trong ảnh (ghi vào trường quote, mỗi dòng cách nhau bằng ' | '). "
            "Chỉ trả JSON: {\"found\": true/false, "
            "\"severity\": \"CRITICAL|HIGH|MEDIUM|LOW\", "
            "\"detail\": \"mô tả đúng vị trí và bằng chứng nhìn thấy (tối đa 25 từ, "
            "TRÍCH NGUYÊN VĂN dòng chữ bị chồng nếu có)\", "
            "\"quote\": \"nguyên văn các dòng chữ nhìn thấy\"}. "
            "Không chắc chắn thì found=false." % question)
        res, err = self._chat(prompt, image_bytes, max_tokens=1200, timeout=timeout,
                              reason="check_visual",
                              max_side=max_side or (1280 if crop else 960))
        if res is None:
            return None, err
        return {"found": bool(res.get("found")),
                "severity": str(res.get("severity", "MEDIUM")).upper(),
                "detail": str(res.get("detail", ""))[:200],
                "quote": str(res.get("quote", ""))[:300]}, None

    def stuck_assist(self, image_bytes, target_desc, tried, timeout=30):
        """Kẹt: hỏi nên bấm gì tiếp. Trả dict {action, param} hoặc None."""
        prompt = (
            "Bạn đang xem ảnh chụp màn hình Android TV của app KenhLive. "
            "Người kiểm thử đang kẹt: đã thử %s mà màn hình không đổi. "
            "Mục tiêu: %s\n"
            "Chỉ trả JSON: {\"action\": \"KEY|SWITCH_TAB|BACK\", "
            "\"param\": \"DPAD_DOWN|DPAD_UP|DPAD_LEFT|DPAD_RIGHT|OK|BACK|0|1|2|3|4|5|6\"}. "
            "Chỉ chọn 1 hành động hợp lý nhất." % (tried, target_desc))
        res, err = self._chat(prompt, image_bytes, max_tokens=600, timeout=timeout,
                              reason="stuck_assist")
        if res is None:
            return None, err
        return {"action": str(res.get("action", "")),
                "param": str(res.get("param", ""))}, None

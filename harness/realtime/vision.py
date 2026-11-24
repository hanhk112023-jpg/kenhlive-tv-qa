#!/usr/bin/env python3
"""KenhLive Realtime QA — vision client (reasoning_effort=high + 1M Session History).

Provider chain GIỐNG harness cũ, đọc từ biến môi trường mà preflight của
qa-suite.yml / qa-realtime-trial.yml đã set (OPENAI_API_BASE/KEY/MODEL =
Gemini / NVIDIA NIM / Meteor). Không hardcode key, không thêm provider mới.

Nâng cấp:
  - Mặc định bật `reasoning_effort = "high"` (tùy chỉnh qua `QA_REASONING_EFFORT`),
    nâng `max_tokens >= 8192` để thinking token không cắt mất JSON kết quả, và tự
    động fallback cache theo host nếu gateway từ chối tham số `reasoning_effort` (HTTP 400/422).
  - Gắn kết `SessionHistory` (không gian lịch sử phiên 1M context): mọi lượt gọi
    vision đều nhận ngữ cảnh lịch sử toàn phiên + lịch sử hội thoại đa lượt (chỉ ảnh
    lượt hiện tại được gửi dưới dạng base64 để gọn nhẹ và không chạm giới hạn ảnh).
  - Trích xuất JSON cân bằng dấu ngoặc từ cuối chuỗi trước, tránh vỡ khi reasoning
    chứa dấu `{...}`.
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
from urllib.parse import urlparse

try:
    from history import SessionHistory
except Exception:
    SessionHistory = None

UA = "KenhLive-RealtimeQA/2.0"

REASONING_EFFORT = os.environ.get("QA_REASONING_EFFORT", "high").strip().lower()
_DISABLED_REASONING_VALUES = ("", "off", "none", "false", "0")
_NO_REASONING_EFFORT_HOSTS = set()


class RateLimitedError(Exception):
    """NIM trả 429 lần 2 (sau 1 lần chờ + retry). Lỗi hạ tầng, không phải app."""


def _is_nim_url(url):
    return urlparse(url or "").netloc.lower() == "integrate.api.nvidia.com"


_TRANSPORT_BACKOFF_S = (2,)


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

REASONING_MODELS = (
    "nemotron", "step-5", "gemini-2.5", "gemini-3",
    "deepseek-r1", "o1", "o3", "o4", "qwq", "claude",
)


def _is_reasoning_enabled(effort=None):
    eff = (REASONING_EFFORT if effort is None else str(effort)).strip().lower()
    return eff not in _DISABLED_REASONING_VALUES


def _max_tokens_for(model, default, reasoning_effort=None):
    eff = (REASONING_EFFORT if reasoning_effort is None else str(reasoning_effort)).strip().lower()
    m = (model or "").lower()
    if eff == "high" or any(k in m for k in REASONING_MODELS):
        return max(int(default), 8192)
    if eff not in _DISABLED_REASONING_VALUES:
        return max(int(default), 4096)
    return int(default)


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
        im.thumbnail((max_side, max_side))
        buf = io.BytesIO()
        im.save(buf, format="JPEG", quality=quality)
        return base64.b64encode(buf.getvalue()).decode()
    except Exception:
        return base64.b64encode(png_bytes).decode() if png_bytes else ""


def _build_request(url, key, payload, user=None, surrogate=None, surrogate_host=None):
    headers = {"Content-Type": "application/json", "User-Agent": UA}
    if surrogate is None and key:
        headers["Authorization"] = "Bearer " + key
    if user:
        headers["x-agent-session"] = user
        payload["user"] = user
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers)
    if surrogate is not None:
        sys_path = "/opt/muse/skills/custom-connector-setup/bin"
        if sys_path not in sys.path:
            sys.path.insert(0, sys_path)
        from dynamic_credentials import add_surrogate_to_request
        add_surrogate_to_request(req, surrogate, allowed_hosts=[surrogate_host])
    return req


def _msg_text(msg):
    if not isinstance(msg, dict):
        return ""
    for field in ("content", "reasoning_content"):
        val = msg.get(field)
        if isinstance(val, list):
            txt = "".join(p.get("text", "") if isinstance(p, dict) else str(p) for p in val).strip()
        elif val is not None:
            txt = str(val).strip()
        else:
            txt = ""
        if txt:
            return txt
    return ""


def _post(url, key, payload, timeout, user=None, surrogate=None,
          surrogate_host=None, reasoning_effort=None):
    is_nim = _is_nim_url(url)
    host = urlparse(url or "").netloc.lower()
    payload = dict(payload)
    eff = (REASONING_EFFORT if reasoning_effort is None else str(reasoning_effort)).strip().lower()
    if eff not in _DISABLED_REASONING_VALUES and host not in _NO_REASONING_EFFORT_HOSTS:
        payload.setdefault("reasoning_effort", eff)

    req = _build_request(url, key, payload, user=user, surrogate=surrogate,
                         surrogate_host=surrogate_host)
    for attempt in range(2):
        try:
            if is_nim:
                from ratelimit import LIMITER
                LIMITER.acquire()
            raw = urllib.request.urlopen(req, timeout=timeout).read().decode("utf-8")
            if raw.strip().startswith("data:"):
                content_parts = []
                reasoning_parts = []
                for line in raw.splitlines():
                    line = line.strip()
                    if line.startswith("data:"):
                        chunk = line[5:].strip()
                        if chunk == "[DONE]":
                            break
                        try:
                            ch = json.loads(chunk)
                            d = (ch.get("choices") or [{}])[0].get("delta") or {}
                            if d.get("content"):
                                content_parts.append(d["content"])
                            if d.get("reasoning_content"):
                                reasoning_parts.append(d["reasoning_content"])
                        except Exception:
                            pass
                joined = "".join(content_parts).strip()
                return joined if joined else "".join(reasoning_parts).strip()
            data = json.loads(raw)
            msg = (data.get("choices") or [{}])[0].get("message") or {}
            return _msg_text(msg)
        except urllib.error.HTTPError as e:
            if e.code == 429:
                if is_nim:
                    from ratelimit import LIMITER
                    retry_after = None
                    try:
                        retry_after = e.headers.get("Retry-After")
                    except Exception:
                        pass
                    LIMITER.record_429(retry_after)
                    if attempt == 0:
                        LIMITER.wait_backoff()
                        LIMITER.note_retry()
                        continue
                raise RateLimitedError("rate_limited_429")
            # Tự động fallback nếu endpoint không nhận tham số reasoning_effort
            if e.code in (400, 422) and "reasoning_effort" in payload:
                err_body = ""
                try:
                    err_body = e.read().decode("utf-8", "replace").lower()
                except Exception:
                    err_body = str(e).lower()
                if any(tok in err_body for tok in ("reasoning", "unknown", "unrecognized", "extra", "invalid", "unsupported")):
                    if host:
                        _NO_REASONING_EFFORT_HOSTS.add(host)
                    payload.pop("reasoning_effort", None)
                    req = _build_request(url, key, payload, user=user,
                                         surrogate=surrogate, surrogate_host=surrogate_host)
                    continue
            if attempt >= 1:
                raise
            time.sleep(2)
        except Exception as e:
            if _is_transport_error(e) and attempt < 1:
                time.sleep(_TRANSPORT_BACKOFF_S[attempt])
                continue
            if attempt >= 1:
                raise
            time.sleep(2)
    return ""


def _parse_json_candidate(chunk):
    if not chunk:
        return None
    cleaned = re.sub(r",\s*([\]}])", r"\1", chunk.strip())
    try:
        obj = json.loads(cleaned)
        return obj if isinstance(obj, dict) else None
    except Exception:
        return None


def _extract_json(text):
    """Trích JSON dict hợp lệ CUỐI CÙNG — an toàn khi reasoning chứa nhiều `{...}`."""
    if not text:
        return None
    s = str(text).strip()
    # 1. Ưu tiên các code block ```json ... ``` từ cuối lên
    fenced = re.findall(r"```(?:json)?\s*(\{.*?\})\s*```", s, flags=re.IGNORECASE | re.DOTALL)
    for block in reversed(fenced):
        parsed = _parse_json_candidate(block)
        if parsed is not None:
            return parsed
    # 2. Quét mọi vị trí '{' từ CUỐI về ĐẦU bằng raw_decode cân bằng ngoặc
    dec = json.JSONDecoder()
    for idx in range(len(s) - 1, -1, -1):
        if s[idx] != "{":
            continue
        substr = s[idx:]
        try:
            obj, _end = dec.raw_decode(substr)
            if isinstance(obj, dict):
                return obj
        except Exception:
            # Thử dọn trailing comma trên đoạn ngoặc cân bằng
            depth = 0
            in_str = False
            esc = False
            end_pos = -1
            for j, ch in enumerate(substr):
                if in_str:
                    if esc:
                        esc = False
                    elif ch == "\\":
                        esc = True
                    elif ch == '"':
                        in_str = False
                else:
                    if ch == '"':
                        in_str = True
                    elif ch == "{":
                        depth += 1
                    elif ch == "}":
                        depth -= 1
                        if depth == 0:
                            end_pos = j + 1
                            break
            if end_pos > 0:
                parsed = _parse_json_candidate(substr[:end_pos])
                if parsed is not None:
                    return parsed
    return None


class VisionClient:
    """Vision dùng cho xác nhận + xác minh defect + thoát kẹt với 1M Session History."""

    def __init__(self, budget=40, history=None, reasoning_effort=None):
        self.budget = int(budget)
        self.calls_total = 0
        self.calls_by_reason = {}
        self.latencies = []
        self.provider = self._detect_provider()
        self.endpoint_host = self._detect_endpoint_host()
        self.fallback_provider = None
        self.fallback_used = 0
        self.reasoning_effort = (
            REASONING_EFFORT if reasoning_effort is None else str(reasoning_effort).strip().lower()
        )
        if history is not None:
            self.history = history
        elif SessionHistory is not None:
            self.history = SessionHistory()
        else:
            self.history = None

    def _detect_endpoint_host(self):
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
        try:
            from ratelimit import LIMITER
            stats = LIMITER.stats()
            stats["provider"] = self.provider
            stats["endpoint_host"] = self.endpoint_host
            stats["fallback_provider"] = self.fallback_provider
            stats["fallback_used"] = self.fallback_used
            stats["reasoning_effort"] = self.reasoning_effort
            return stats
        except Exception:
            return {"requests_used": 0, "limit_per_min": 30,
                    "hit_429": False, "hits_429": 0, "provider": self.provider,
                    "endpoint_host": self.endpoint_host,
                    "fallback_provider": self.fallback_provider,
                    "fallback_used": self.fallback_used,
                    "reasoning_effort": self.reasoning_effort}

    @staticmethod
    def _provider_configured(name):
        if name == "DEEPSEEK_WEB":
            return bool(DEEPSEEK_BASE)
        if name == "ANTIGRAVITY":
            return bool(ANTIGRAVITY_KEY and ANTIGRAVITY_BASE)
        if name == "KILO":
            return bool(KILO_KEY and KILO_BASE)
        if name == "OPENAI":
            return bool(OPENAI_KEY and OPENAI_BASE)
        if name == "NVIDIA_NIM":
            try:
                sys_path = "/opt/muse/skills/custom-connector-setup/bin"
                if sys_path not in sys.path:
                    sys.path.insert(0, sys_path)
                import dynamic_credentials  # noqa: F401
                return True
            except Exception:
                return False
        return False

    def _pick_fallback(self):
        _hosts = {
            "NVIDIA_NIM": urlparse(NVIDIA_NIM_BASE).netloc.lower(),
            "OPENAI": urlparse(_normalize_url(OPENAI_BASE) or "").netloc.lower(),
            "DEEPSEEK_WEB": urlparse(_normalize_url(DEEPSEEK_BASE) or "").netloc.lower(),
            "ANTIGRAVITY": urlparse(_normalize_url(ANTIGRAVITY_BASE) or "").netloc.lower(),
            "KILO": urlparse(_normalize_url(KILO_BASE) or "").netloc.lower(),
        }
        _primary_host = _hosts.get(self.provider, "")
        for name in ("DEEPSEEK_WEB", "ANTIGRAVITY", "KILO", "OPENAI", "NVIDIA_NIM"):
            if name == self.provider:
                continue
            if not self._provider_configured(name):
                continue
            if _hosts.get(name, "") and _hosts[name] == _primary_host:
                continue
            return name
        return None

    def _chat_once(self, provider, msgs, max_tokens, timeout, user="qa_realtime"):
        """Một lần gửi tới đúng 1 provider. Trả raw text (raise khi lỗi)."""
        eff = self.reasoning_effort
        if eff == "high":
            timeout = max(int(timeout), 90)
        if provider == "NVIDIA_NIM":
            return _post(NVIDIA_NIM_BASE, "",
                         {"model": NVIDIA_NIM_MODEL, "temperature": 0.1,
                          "max_tokens": _max_tokens_for(NVIDIA_NIM_MODEL, max_tokens, eff),
                          "messages": msgs}, timeout, user=user,
                         surrogate="custom.nvidia",
                         surrogate_host="integrate.api.nvidia.com",
                         reasoning_effort=eff)
        elif provider == "DEEPSEEK_WEB":
            return _post(_normalize_url(DEEPSEEK_BASE), DEEPSEEK_KEY,
                         {"model": DEEPSEEK_MODEL, "temperature": 0.1,
                          "max_tokens": _max_tokens_for(DEEPSEEK_MODEL, max_tokens, eff),
                          "messages": msgs}, timeout, user=user,
                         reasoning_effort=eff)
        elif provider == "ANTIGRAVITY":
            return _post(_normalize_url(ANTIGRAVITY_BASE), ANTIGRAVITY_KEY,
                         {"model": ANTIGRAVITY_MODEL, "temperature": 0.1,
                          "max_tokens": _max_tokens_for(ANTIGRAVITY_MODEL, max_tokens, eff),
                          "messages": msgs}, timeout,
                         reasoning_effort=eff)
        elif provider == "KILO":
            return _post(KILO_BASE, KILO_KEY,
                         {"model": KILO_MODEL, "temperature": 0.1,
                          "max_tokens": _max_tokens_for(KILO_MODEL, max_tokens, eff),
                          "messages": msgs}, timeout,
                         reasoning_effort=eff)
        else:
            return _post(_normalize_url(OPENAI_BASE), OPENAI_KEY,
                         {"model": OPENAI_MODEL, "temperature": 0.1,
                          "max_tokens": _max_tokens_for(OPENAI_MODEL, max_tokens, eff),
                          "messages": msgs}, timeout, user=user,
                         reasoning_effort=eff)

    def _attempt(self, provider, msgs, max_tokens, timeout, reason, user="qa_realtime"):
        t0 = time.time()
        raw = ""
        err = None
        try:
            raw = self._chat_once(provider, msgs, max_tokens, timeout, user)
        except Exception as e:
            err = str(e)[:120]
        dt = round(time.time() - t0, 1)
        self.calls_total += 1
        self.calls_by_reason[reason] = self.calls_by_reason.get(reason, 0) + 1
        self.latencies.append(dt)
        return raw, err

    def _build_messages(self, prompt, b64_image=None, context=None):
        if self.history is not None:
            return self.history.build_messages(prompt, b64_image=b64_image, context=context)
        content = [{"type": "text", "text": prompt}]
        if b64_image:
            content.append({"type": "image_url",
                            "image_url": {"url": "data:image/jpeg;base64,%s" % b64_image}})
        return [{"role": "user", "content": content}]

    def _chat(self, prompt, image_bytes, max_tokens, timeout, reason, user="qa_realtime",
              max_side=960, context=None):
        if not self.available() or self.remaining() <= 0:
            return None, "unavailable_or_budget"
        b64 = _compress_b64(image_bytes, max_side=max_side)
        msgs = self._build_messages(prompt, b64_image=b64, context=context)
        raw, err = self._attempt(self.provider, msgs, max_tokens, timeout, reason, user)
        if (err or not raw) and self.remaining() > 0:
            fb = self._pick_fallback()
            if fb:
                self.fallback_provider = fb
                self.fallback_used += 1
                raw, err = self._attempt(fb, msgs, max_tokens, timeout, reason, user)
                if err or not raw:
                    return None, "error:%s (fallback %s)" % ((err or "empty"), fb)
        if err or not raw:
            return None, "error:%s" % (err or "empty")
        parsed = _extract_json(raw)
        if self.history is not None:
            self.history.record_vision_turn(reason, prompt, raw, parsed=parsed, meta=context)
        if parsed is None:
            return None, "invalid_json"
        return parsed, None

    # -- 3 trường hợp dùng duy nhất ------------------------------------
    def confirm_target(self, image_bytes, target_desc, timeout=60, context=None):
        """Xác nhận mục tiêu có đang hiển thị không. Trả dict {confirmed, quote, confidence} hoặc None."""
        prompt = (
            "Bạn đang xem ảnh chụp màn hình của app KenhLive.\n"
            "Mục tiêu cần xác nhận: %s\n"
            "Yêu cầu kiểm tra kỹ trước khi trả lời:\n"
            "1. Đối chiếu ảnh với [NGỮ CẢNH UI HIỆN TẠI] (activity, has_dialog, loading_screen, motion) và lịch sử phiên.\n"
            "2. Nếu màn hình đang hiện 'Đang tải...', 'Đang tải luồng...', spinner hoặc sai activity/tab -> confirmed=false.\n"
            "3. Chỉ trả JSON: {\"confirmed\": true/false, \"confidence\": \"high|medium|low\", "
            "\"quote\": \"chuỗi chữ bạn NHÌN THẤY chứng minh mục tiêu (trích nguyên văn, tối đa 16 từ)\"}.\n"
            "Không thấy rõ hoặc không chắc chắn thì confirmed=false. Tuyệt đối không bịa." % target_desc)
        res, err = self._chat(prompt, image_bytes, max_tokens=1000, timeout=timeout,
                              reason="confirm_target", context=context)
        if res is None:
            return None, err
        confirmed = bool(res.get("confirmed"))
        confidence = str(res.get("confidence", "medium")).lower()
        quote = str(res.get("quote", "")).strip()[:160]
        if confirmed and confidence == "low" and not quote:
            confirmed = False
        return {"confirmed": confirmed,
                "quote": quote[:120],
                "confidence": confidence}, None

    def check_visual(self, image_bytes, question, timeout=60, crop=None, max_side=None, context=None):
        """Xác minh một defect nghi vấn. Trả dict {found, severity, detail, quote} hoặc None."""
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
            "Bạn đang xem ảnh chụp màn hình của app KenhLive.\n"
            "Câu hỏi kiểm tra: %s\n"
            "Trước khi kết luận, HÃY ĐỌC NGUYÊN VĂN tất cả dòng chữ nhìn thấy trong ảnh "
            "(ghi vào trường quote, mỗi dòng cách nhau bằng ' | '). Kiểm tra các lỗi đã báo ở lịch sử phiên để tránh kết luận nhầm.\n"
            "Chỉ trả JSON: {\"found\": true/false, "
            "\"severity\": \"CRITICAL|HIGH|MEDIUM|LOW\", "
            "\"detail\": \"mô tả đúng vị trí và bằng chứng nhìn thấy (tối đa 30 từ, TRÍCH NGUYÊN VĂN dòng chữ lỗi nếu có)\", "
            "\"quote\": \"nguyên văn các dòng chữ nhìn thấy\"}. "
            "Không chắc chắn hoặc ảnh không đúng loại màn hình cần kiểm thì found=false." % question)
        res, err = self._chat(prompt, image_bytes, max_tokens=1600, timeout=timeout,
                              reason="check_visual",
                              max_side=max_side or (1280 if crop else 960),
                              context=context)
        if res is None:
            return None, err
        return {"found": bool(res.get("found")),
                "severity": str(res.get("severity", "MEDIUM")).upper(),
                "detail": str(res.get("detail", ""))[:200],
                "quote": str(res.get("quote", ""))[:300]}, None

    def stuck_assist(self, image_bytes, target_desc, tried, timeout=60, context=None):
        """Kẹt: hỏi nên bấm gì tiếp có đối chiếu toàn bộ lịch sử phiên."""
        act_ctx = str((context or {}).get("activity") or "")
        in_player = ("PlayerActivity" in act_ctx) or ("WebPlayerActivity" in act_ctx)
        prompt = (
            "Bạn đang xem ảnh chụp màn hình app KenhLive.\n"
            "Người kiểm thử đang kẹt: gần đây đã thử [%s] mà màn hình không đổi.\n"
            "Mục tiêu mission: %s\n"
            "Hãy đọc kỹ [KHÔNG GIAN LỊCH SỬ PHIÊN QA] để xem những phím/rule nào đã thử ở các bước trước mà UNCHANGED, từ đó chọn bước KHÁC hợp lý nhất.\n"
            "%s"
            "Chỉ trả JSON: {\"action\": \"KEY|SWITCH_TAB|BACK\", "
            "\"param\": \"DPAD_DOWN|DPAD_UP|DPAD_LEFT|DPAD_RIGHT|OK|BACK|0|1|2|3|4|5|6\"}. "
            "Chỉ chọn 1 hành động hợp lý nhất." % (
                tried, target_desc,
                "CẢNH BÁO: Đang ở trong player — TUYỆT ĐỐI KHÔNG chọn SWITCH_TAB.\n" if in_player else ""
            ))
        res, err = self._chat(prompt, image_bytes, max_tokens=1000, timeout=timeout,
                              reason="stuck_assist", context=context)
        if res is None:
            return None, err
        act_out = str(res.get("action", "")).strip().upper()
        param_out = str(res.get("param", "")).strip()
        # Bảo vệ chống SWITCH_TAB nhầm khi đang ở trong player
        if in_player and act_out == "SWITCH_TAB":
            act_out = "KEY"
            param_out = "BACK"
        return {"action": act_out, "param": param_out}, None

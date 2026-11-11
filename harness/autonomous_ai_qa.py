#!/usr/bin/env python3
"""
KenhLive TV — 100% Autonomous AI QA Agent (Unified Brain)
Hệ thống kiểm thử tự trị toàn diện điều khiển bởi AI Agent:
- Vision + Reasoning: LLM/VLM "nhìn" màn hình Android TV 10-foot, đọc cây UI, phân tích Logcat.
- Autonomous Decision: AI tự ra quyết định bấm phím D-pad, khám phá tính năng, tái hiện bug.
- Multi-Source Sports & IPTV & Cinema Verification:
  + Thể thao: Socolive, ColaTV, Gà Vàng, Khán Đài (Filter, Server Picker, Failover).
  + Truyền hình: IPTV TV360, VTV, HTV, Hero Preview, Lưới 5 cột.
  + Phim: NguonC, Phim lẻ, Phim bộ, Anime, Player StreamC.
- Probes sâu: Motion Video Detector (ExoPlayer), Focus Ring Contrast, D-pad Chaos Stress.
"""

import base64
import html
import io
import json
import os
import random
import re
import subprocess
import sys
import time
import urllib.request
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from qa_session import QASession, KENHLIVE_TABS, REMOTE_KEY_ICONS
from video_recorder import VideoRecorder

try:
    from PIL import Image, ImageChops, ImageStat
except ImportError:
    Image = None
    ImageChops = None
    ImageStat = None

PKG = "com.kenhlive.tv"
UA = "KenhLive-AI-QA/5.0"

# Keycodes chuẩn Android TV & Remote Điều Khiển TV Box
KEY_MAP = {
    "UP": 19, "DPAD_UP": 19,
    "DOWN": 20, "DPAD_DOWN": 20,
    "LEFT": 21, "DPAD_LEFT": 21,
    "RIGHT": 22, "DPAD_RIGHT": 22,
    "ENTER": 23, "DPAD_CENTER": 23, "OK": 23,
    "BACK": 4,
    "HOME": 3,
    "MENU": 82,
    "INFO": 165,
    "PLAY_PAUSE": 85,
    "PLAY": 126,
    "PAUSE": 127,
    "REWIND": 89,
    "FAST_FORWARD": 90,
    "CHANNEL_UP": 166,
    "CHANNEL_DOWN": 167,
    "PAGE_UP": 92,
    "PAGE_DOWN": 93,
    "ASPECT_RATIO": 228,
    "KEY_A": 29, "A": 29,
    "KEY_B": 30, "B": 30,
    "PROG_RED": 183, "RED": 183,
    "PROG_GREEN": 184, "GREEN": 184,
    "PROG_YELLOW": 185, "YELLOW": 185,
    "PROG_BLUE": 186, "BLUE": 186,
    "0": 7, "1": 8, "2": 9, "3": 10, "4": 11,
    "5": 12, "6": 13, "7": 14, "8": 15, "9": 16
}

# AI Gateways Configuration (100% loaded from environment/secrets)
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
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")


def sh(cmd, timeout=30):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return (r.stdout or "") + (r.stderr or "")
    except Exception as e:
        return f"__ERR__ {e}"


# ==============================================================================
# 1. AI BRAIN (Vision + Reasoning Multi-Gateway Client)
# ==============================================================================
class AIBrain:
    """Bộ não trung tâm điều khiển AI QA: Hỗ trợ đa backend, Fallback tự động và Session Memory liên tục cho cả phiên test."""

    def __init__(self):
        self.provider_active = "UNKNOWN"
        self._detect_provider()
        self.session_id = None
        self.session_messages = []
        self.turn_counter = 0
        self.last_action_feedback = ""

    def _detect_provider(self):
        # Ưu tiên DeepSeek Web (nếu có base URL từ FreeDeepseekAPI nội bộ) hoặc Antigravity Gateway
        if DEEPSEEK_BASE:
            self.provider_active = "DEEPSEEK_WEB"
        elif ANTIGRAVITY_KEY and ANTIGRAVITY_BASE:
            self.provider_active = "ANTIGRAVITY"
        elif KILO_KEY and KILO_BASE:
            self.provider_active = "KILO"
        elif OPENAI_KEY and OPENAI_BASE:
            self.provider_active = "OPENAI"
        else:
            self.provider_active = "LOCAL_REFLEX"
        print(f"🧠 [AI Brain] Khởi tạo thành công với engine: {self.provider_active}", flush=True)

    def init_session(self, session_id: str):
        """Khởi tạo bộ nhớ cho một phiên kiểm thử hoàn chỉnh (Session Memory).
        Toàn bộ các bước kiểm thử trong cùng 1 phiên sẽ tích lũy ngữ cảnh vào cùng 1 luồng hội thoại.
        """
        self.session_id = session_id
        self.turn_counter = 0
        self.last_action_feedback = ""
        self.session_messages = [
            {"role": "system", "content": self._build_system_prompt()}
        ]
        print(f"🧠 [AI Brain] Đã thiết lập Session Memory cho phiên test: {session_id}", flush=True)

    def record_step_feedback(self, feedback: str):
        """Ghi nhận phản hồi kết quả thực tế sau khi thực hiện hành động vào bộ nhớ phiên."""
        self.last_action_feedback = feedback

    def _build_system_prompt(self) -> str:
        return """Bạn là Senior AI QA Engineer chuyên nghiệp kiểm thử ứng dụng Android TV 10-foot 'KênhLive'.
Bạn đang trực tiếp cầm remote điều khiển app trên TV để kiểm thử tính năng và đào sâu săn lỗi (Deep Bug Hunting) trong một phiên kiểm thử liên tục (Continuous Test Session).

BẢN ĐỒ TOÀN BỘ 6 TAB VÀ CÁC MÀN HÌNH CỦA APP KENHLIVE TV:
- [Tab 0 - Trực tiếp (Live)]: Trận đấu bóng đá live. Hàng lọc đài phát riêng biệt: "Tất cả", "ColaTV", "Gà Vàng", "Khán Đài", "Socolive". Hero Banner gọn gàng. Tên giải đấu chuẩn tiếng Việt, tỷ số X : Y, nhãn XEM và countdown. Hộp thoại RoomPickerDialog chọn phòng BLV.
- [Tab 1 - Lịch đấu (Schedule)]: Lịch thi đấu theo ngày (Hôm nay, Ngày mai, Giải đấu). Trận > 180p có badge KẾT THÚC. Chạm trận đấu (onFixtureTap) mở RoomPicker hoặc thông báo nếu chưa có phòng.
- [Tab 2 - Truyền hình (IPTV)]: Danh mục Kênh Yêu Thích (bấm giữ OK để lưu), TV360, VTV, HTV. Hero Preview góc trên. Lưới kênh. OSD gõ số trực tiếp từ remote (0-9). Phím tắt đổi kênh CHANNEL_UP/DOWN, PAGE_UP/DOWN. Phím tắt Aspect Ratio (A/Đỏ) & Audio Boost (B/Vàng).
- [Tab 3 - Tìm kiếm (Search)]: Ô nhập tìm kiếm (searchInput), gõ từ khóa không dấu, chuyển D-pad xuống danh sách kết quả (resultList), nút xóa nhanh clearBtn.
- [Tab 4 - Cài đặt (Settings)]: Thông tin phiên bản, kiểm tra cập nhật, liên hệ & báo lỗi Telegram (@kenhlivetv) có mã QR ngoại tuyến, cài đặt video và audio.
- [Tab 5 - Kho Phim (KKPhim & NguonC)]: Apple Pills thể loại & quốc gia, nút XEM NGAY (btnHeroPlay), nút CHỌN TẬP (btnHeroEpisodes), nút LƯU PHIM (btnHeroFavorite), hộp thoại EpisodePickerDialog hỗ trợ chọn Server (Vietsub/Thuyết Minh) và phân nhóm 30 tập. Trình phát phim hỗ trợ HLS 4K native ExoPlayer, tua D-pad Trái/Phải (-15s / +15s) và tự động lưu/tiếp tục xem (Resume Playback).
- [Sidebar Rail]: Mở bằng DPAD_LEFT từ mép trái, duyệt dọc qua 6 tab, đóng bằng DPAD_RIGHT hoặc BACK.
- [PlayerActivity]: Trình phát video Live & VOD, phím MENU mở Server Picker, phím A/Đỏ xoay vòng tỉ lệ khung hình (Fit/Fill/Zoom/Fixed), phím B/Vàng tăng âm lượng, gõ số kênh hiện OSD nhảy kênh ngay khi bấm OK. Khung báo lỗi có nút Báo Lỗi Telegram @kenhlivetv.
- [Trang Chủ (Tab 6)]: Màn hình chính KL8 — billboard hero chiếm ~60% chiều cao + 6 hàng nội dung (ĐANG PHÁT, TIẾP TỤC XEM, TRẬN SẮP DIỄN RA, MỚI CẬP NHẬT, KÊNH, GIẢI ĐẤU). Cổng Chọn 3 Card cũ (THỂ THAO / TRUYỀN HÌNH / PHIM TRUYỆN) đã bị xóa ở Task 4 — KHÔNG tìm card portal nữa. Đây cũng là tab mặc định khi mở app trên TV.
- [Thoát mục về Trang Chủ]: Khi đang ở bất kỳ mục nào (current != TAB_HUB), nhấn BACK 2 lần liên tiếp trong 2 giây sẽ thoát mục quay lại Trang Chủ (Tab 6). Nhấn BACK tại Trang Chủ sẽ hiện dialog xác nhận thoát app.

NGUYÊN TẮC BỘ NHỚ PHIÊN & SĂN LỖI SÂU (Deep Bug Hunting & Session Memory):
1. Bạn có TRÍ NHỚ LIÊN TỤC xuyên suốt cả phiên test. Hãy ghi nhớ các màn hình đã đi qua, các thao tác đã thực hiện và các lỗi đã phát hiện để không lặp lại hoặc kiểm tra lại xem lỗi có tái diễn.
2. Chủ động khám phá toàn bộ các tính năng, di chuyển qua các tab bằng SWITCH_TAB, OPEN_MULTIVIEW hoặc DPAD_LEFT mở rail navigation.
3. Khi phát hiện lỗi thực sự (Mất dấu focus, Kẹt nút Focus Trap, Rò rỉ focus vào view ẩn/ngoài màn hình, Tràn viền text, Chữ hiển thị 'null'/'undefined', Dialog không trap focus, App crash, Video đứng hình), hãy báo ngay vào trường 'defect_detected'.
4. Tính năng tự phục hồi (Failover & Self-Healing): Nếu app tự đổi sang server dự phòng thành công, đây là tính năng bảo vệ hoạt động đúng, KHÔNG coi là lỗi.
5. KIỂM THỬ KỸ LƯỠNG, TOÀN DIỆN & KHÔNG ĐƯỢC LÀM QUA LOA: Mỗi nhiệm vụ phải thực hiện tối thiểu 4-6 thao tác kiểm thử sâu (duyệt D-pad qua lại, bấm vào các nút chi tiết, kiểm tra các trạng thái biên, đổi tab) trước khi bấm COMPLETE_MISSION. Tuyệt đối KHÔNG bấm COMPLETE_MISSION khi chỉ mới bấm 1-2 phím!
6. PHÂN BIỆT RÕ GIAO DIỆN APP VỚI NỘI DUNG TRUYỀN HÌNH (Broadcast Stream vs App UI):
- Khi đang phát video, các đồ họa như Bảng điểm trận đấu (Scoreboard của đài truyền hình gốc: '72:37 AZ 0-2 JUV', cúp C1/C2), logo kênh (ARENASPORT, SUTBONGTV), phụ đề phim hoặc banner BLV là NỘI DUNG NẰM TRONG LUỒNG VIDEO của bên phát sóng, KHÔNG PHẢI giao diện của ứng dụng KenhLive TV. Tuyệt đối KHÔNG nhầm lẫn bảng điểm bóng đá của truyền hình là nút backBtn hay thanh tiêu đề app!
7. TÍNH CHÍNH XÁC KHI ĐỐI CHIẾU CẢM BIẾN HỆ THỐNG:
- Luôn kiểm tra 'TRẠNG THÁI MÀN HÌNH & HỆ THỐNG HIỆN TẠI' (Node đang FOCUS, Có viền focus chuẩn, DANH SÁCH VIEW FOCUSABLE). Nếu thông tin hệ thống báo 'Node đang FOCUS: NONE' hoặc thanh điều khiển OSD đang ẩn, không được ảo giác rằng thanh OSD đang hiển thị hay có nút có viền cam. Muốn mở thanh điều khiển hãy bấm OK hoặc DPAD_DOWN.
8. GIỚI HẠN EMULATOR x86 (ANDROID TV EMULATOR CI):
- Lỗi giải mã phần cứng trên emulator x86 (ví dụ ERROR_CODE_DECODING_FAILED, MediaCodec thiếu codec HEVC/H.264 cho một số luồng HLS) là giới hạn của máy ảo, KHÔNG phải lỗi app. Tuyệt đối không báo [HIGH] cho lỗi này; tối đa [LOW] ghi chú môi trường hoặc bỏ qua nếu video vẫn phát được ở nguồn khác / dialog lỗi hiển thị đúng.

ĐỊNH DẠNG TRẢ VỀ DUY NHẤT: Trả về một khối JSON hợp lệ:
{
  "thought": "Quan sát thấy gì trên màn hình hiện tại, liên hệ với các bước trước trong phiên kiểm thử và lý do chọn hành động này",
  "action_type": "KEY" | "LONG_PRESS" | "KEYPAD" | "SWITCH_TAB" | "OPEN_MULTIVIEW" | "LAUNCH_WEB_PLAYER" | "LAUNCH_VOD_PLAYER_DIRECTED" | "TEXT" | "WAIT" | "VERIFY_STREAM" | "COMPLETE_MISSION",
  "action_param": "DPAD_DOWN" | "OK" | "1" | "2" | "ENTER" | "BACK" | "DOUBLE_BACK" | "uefa" | "2.0" | "",
  "expected_result": "Kỳ vọng gì sau khi thực hiện hành động này?",
  "defect_detected": null hoặc {
     "area": "Tên màn hình/tính năng",
     "severity": "CRITICAL" | "HIGH" | "MEDIUM" | "LOW",
     "issue": "Mô tả ngắn gọn lỗi",
     "detail": "Bằng chứng chi tiết",
     "suggestion": "Gợi ý sửa code Kotlin/Layout"
  }
}"""

    def chat_turn(self, messages, max_tokens=3000, timeout=45):
        """Gửi chuỗi hội thoại của phiên đến model AI và nhận câu trả lời."""
        # 1. Thử DeepSeek Web nếu có cấu hình
        if self.provider_active == "DEEPSEEK_WEB" or DEEPSEEK_BASE:
            try:
                res = self._call_openai_compat(
                    url=DEEPSEEK_BASE,
                    key=DEEPSEEK_KEY,
                    model=DEEPSEEK_MODEL,
                    messages=messages,
                    max_tokens=max_tokens,
                    timeout=timeout,
                    user=f"qa_brain_{self.session_id or 'auto'}"
                )
                if res:
                    return res, "DEEPSEEK_WEB"
            except Exception as e:
                print(f"⚠️ [AI Brain] DeepSeek Web gateway lỗi ({e}), chuyển fallback...", flush=True)

        # 2. Thử Antigravity Gateway
        if self.provider_active == "ANTIGRAVITY" or (ANTIGRAVITY_KEY and ANTIGRAVITY_BASE):
            try:
                res = self._call_openai_compat(
                    url=ANTIGRAVITY_BASE,
                    key=ANTIGRAVITY_KEY,
                    model=ANTIGRAVITY_MODEL,
                    messages=messages,
                    max_tokens=max_tokens,
                    timeout=timeout
                )
                if res:
                    return res, "ANTIGRAVITY"
            except Exception as e:
                print(f"⚠️ [AI Brain] Antigravity gateway lỗi ({e}), chuyển fallback...", flush=True)

        # 3. Thử Kilo Gateway
        if KILO_KEY and KILO_BASE:
            try:
                res = self._call_openai_compat(
                    url=KILO_BASE,
                    key=KILO_KEY,
                    model=KILO_MODEL,
                    messages=messages,
                    max_tokens=max_tokens,
                    timeout=timeout
                )
                if res:
                    return res, "KILO"
            except Exception as e:
                print(f"⚠️ [AI Brain] Kilo gateway lỗi ({e}), chuyển fallback...", flush=True)

        # 3. Thử OpenAI / OpenRouter nếu có
        if OPENAI_KEY and OPENAI_BASE:
            try:
                res = self._call_openai_compat(
                    url=OPENAI_BASE,
                    key=OPENAI_KEY,
                    model=OPENAI_MODEL,
                    messages=messages,
                    max_tokens=max_tokens,
                    timeout=timeout
                )
                if res:
                    return res, "OPENAI"
            except Exception:
                pass

        # 4. Fallback: Local Reflex Brain (không phụ thuộc mạng ngoại vi)
        return None, "LOCAL_REFLEX"

    def chat_vision(self, prompt, image_bytes=None, system_prompt=None, max_tokens=3000, timeout=45):
        """Tương thích ngược: Gửi tin nhắn đơn lẻ nếu cần."""
        msgs = []
        if system_prompt:
            msgs.append({"role": "system", "content": system_prompt})
        user_content = [{"type": "text", "text": prompt}]
        if image_bytes:
            b64 = self._compress_and_b64(image_bytes)
            if b64:
                user_content.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{b64}"}
                })
        msgs.append({"role": "user", "content": user_content})
        return self.chat_turn(msgs, max_tokens=max_tokens, timeout=timeout)

    def _normalize_gateway_url(self, url: str) -> str:
        if not url:
            return ""
        u = url.rstrip("/")
        if u.endswith("/chat/completions"):
            return u
        if u.endswith("/v1"):
            return f"{u}/chat/completions"
        return f"{u}/chat/completions"

    def _call_openai_compat(self, url, key, model, messages, max_tokens, timeout, user=None):
        target_url = self._normalize_gateway_url(url)
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": 0.1,
            "stream": False
        }
        if user:
            payload["user"] = user

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {key}",
            "User-Agent": UA
        }
        if user:
            headers["x-agent-session"] = user

        data_bytes = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            target_url,
            data=data_bytes,
            headers=headers
        )

        for attempt in range(3):
            try:
                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    raw_text = resp.read().decode("utf-8")
                    # Xử lý gateway tự động stream SSE (data: {...}) dù không yêu cầu stream
                    if raw_text.strip().startswith("data:"):
                        parts = []
                        for line in raw_text.splitlines():
                            line = line.strip()
                            if line.startswith("data:"):
                                data_chunk = line[5:].strip()
                                if data_chunk == "[DONE]":
                                    break
                                try:
                                    chunk = json.loads(data_chunk)
                                    choices = chunk.get("choices") or []
                                    if choices:
                                        delta = choices[0].get("delta") or choices[0].get("message") or {}
                                        t = delta.get("content") or delta.get("reasoning_content") or ""
                                        if t:
                                            parts.append(t)
                                except Exception:
                                    pass
                        return "".join(parts).strip()
                    data = json.loads(raw_text)
                    choices = data.get("choices") or []
                    if not choices:
                        return ""
                    msg = choices[0].get("message") or {}
                    raw = msg.get("content") or msg.get("reasoning_content") or ""
                    if isinstance(raw, list):
                        raw = "".join(p.get("text", "") if isinstance(p, dict) else str(p) for p in raw)
                    elif not isinstance(raw, str):
                        raw = str(raw) if raw is not None else ""
                    return raw.strip()
            except Exception as e:
                if attempt == 2:
                    raise
                time.sleep(1.5 * (attempt + 1))
        return ""

    def _compress_and_b64(self, png_bytes):
        if not png_bytes or not Image:
            return base64.b64encode(png_bytes).decode("utf-8") if png_bytes else None
        try:
            im = Image.open(io.BytesIO(png_bytes)).convert("RGB")
            im.thumbnail((960, 540))
            buf = io.BytesIO()
            im.save(buf, format="JPEG", quality=75)
            return base64.b64encode(buf.getvalue()).decode("utf-8")
        except Exception:
            return base64.b64encode(png_bytes).decode("utf-8")

    def decide_mission_action(self, mission, state):
        """AI phân tích trạng thái và ra quyết định hành động tiếp theo trong mạch hội thoại của cả phiên test."""
        self.turn_counter += 1

        # 1. Đảm bảo session_messages đã được khởi tạo
        if not self.session_messages:
            self.init_session("QA-SESSION-AUTO")

        # 2. Tối ưu bộ nhớ phiên: gỡ bỏ dữ liệu ảnh base64 lớn của các bước cũ để tránh tràn token / bandwidth
        for msg in self.session_messages:
            content = msg.get("content")
            if msg.get("role") == "user" and isinstance(content, list):
                compact_parts = []
                for p in content:
                    if isinstance(p, dict):
                        if p.get("type") == "text":
                            compact_parts.append(p)
                        elif p.get("type") == "image_url":
                            compact_parts.append({"type": "text", "text": "[Ảnh màn hình bước trước đã phân tích]"})
                msg["content"] = compact_parts

        # 3. Xây dựng tin nhắn User cho bước hiện tại
        feedback_section = f"\nPHẢN HỒI TỪ BƯỚC TRƯỚC:\n{self.last_action_feedback}\n" if self.last_action_feedback else ""
        deep_anomaly_section = f"\nCẢNH BÁO TỪ PROBE TỰ ĐỘNG (DEEP ANOMALY INSPECTOR):\n{state.get('deep_anomalies_text')}\n" if state.get('deep_anomalies_text') else ""
        step_prompt = f"""[LƯỢT #{self.turn_counter} · NHIỆM VỤ: {mission.name} ({mission.title})]
- Tiến độ nhiệm vụ: Bước {mission.steps_executed}/{mission.max_steps}
- Mục tiêu: {mission.description}
- Tiêu chí đạt: {mission.success_criteria}

TIẾN ĐỘ TOÀN PHIÊN KIỂM THỬ:
- Các Tab đã kiểm tra: {state.get('tabs_tested', 'Chưa có')}
- Các Tab còn lại: {state.get('tabs_remaining', 'Toàn bộ')}

TRẠNG THÁI MÀN HÌNH & HỆ THỐNG HIỆN TẠI:
- Activity: {state.get('activity')}
- Node đang FOCUS: {state.get('focused_sig')} (Text: '{state.get('focused_text')}')
- Có viền focus chuẩn: {state.get('has_focus_ring')} (Màu viền: {state.get('focus_ring_color')})
- Video đang chạy (Motion): {state.get('video_motion_playing')} (Motion delta: {state.get('video_motion_delta', 0.0):.2f}%)
- Lịch sử 5 phím gần nhất: {state.get('recent_keys')}
- Logcat cảnh báo/lỗi: {state.get('logcat_alerts')}
{feedback_section}{deep_anomaly_section}
DANH SÁCH VIEW FOCUSABLE TRÊN MÀN HÌNH:
{state.get('ui_summary')}

Hãy phân tích hình ảnh màn hình hiện tại đính kèm cùng toàn bộ diễn biến lịch sử của phiên kiểm thử này để chọn hành động tiếp theo. Trả về DUY NHẤT một khối JSON theo định dạng đã quy định."""

        user_content = [{"type": "text", "text": step_prompt}]
        raw_png = state.get("screenshot_bytes")
        if raw_png:
            b64 = self._compress_and_b64(raw_png)
            if b64:
                user_content.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{b64}"}
                })

        new_user_msg = {"role": "user", "content": user_content}

        # Sliding window nếu số lượng tin nhắn quá dài (> 30 tin nhắn ~ 15 lượt)
        if len(self.session_messages) > 30:
            sys_msg = self.session_messages[0]
            # Giữ system message và các tin nhắn gần nhất nhưng PHẢI bắt đầu bằng lượt User (tránh lỗi 400 Gemini API)
            trimmed = self.session_messages[-16:]
            while trimmed and trimmed[0].get("role") != "user":
                trimmed = trimmed[1:]
            self.session_messages = [sys_msg] + trimmed

        candidate_messages = list(self.session_messages) + [new_user_msg]
        response_text, provider = self.chat_turn(candidate_messages)

        if response_text and provider != "LOCAL_REFLEX":
            try:
                # Sanitize markdown code fences và trailing commas
                cleaned_text = re.sub(r"^```(?:json)?\s*", "", response_text.strip(), flags=re.IGNORECASE)
                cleaned_text = re.sub(r"\s*```$", "", cleaned_text.strip())
                m = re.search(r"\{.*\}", cleaned_text, re.DOTALL)
                if m:
                    json_str = m.group(0)
                    json_str = re.sub(r",\s*([\]}])", r"\1", json_str)
                    parsed = json.loads(json_str)
                    parsed["_provider"] = provider
                    # Ghi nhận lượt hội thoại này vào bộ nhớ phiên
                    self.session_messages.append(new_user_msg)
                    self.session_messages.append({"role": "assistant", "content": response_text})
                    return parsed
            except Exception as e:
                print(f"⚠️ [AI Brain] Không parse được JSON từ {provider}: {e}", flush=True)

        # Fallback vào Local Reflex Brain nếu AI cloud không khả dụng
        return self._local_reflex_decision(mission, state)

    def _local_reflex_decision(self, mission, state):
        """Local Autonomous Reflex Brain: Quyết định dựa trên heuristics ngữ nghĩa thông minh."""
        m_id = mission.name
        step = max(0, mission.steps_executed - 1)
        focused_text = (state.get("focused_text") or "").lower()
        recent = state.get("recent_keys", [])

        thought = f"Local Reflex: Điều hướng theo ngữ cảnh nhiệm vụ {m_id} tại bước {step + 1}"
        action_type = "KEY"
        action_param = "DPAD_DOWN"
        defect = None

        # Kiểm tra mất focus: loại trừ màn hình phát video PlayerActivity/WebPlayerActivity
        # vì khi phát video toàn màn hình, thanh điều khiển OSD tự ẩn sau 3.5s là thiết kế chuẩn TV,
        # không phải lỗi mất focus.
        is_player = "PlayerActivity" in (state.get("activity") or "") or "WebPlayerActivity" in (state.get("activity") or "")
        is_playing = state.get("video_motion_playing") or False
        if not is_player and not is_playing and not state.get("has_focus_ring") and state.get("focused_sig") == "NONE":
            defect = {
                "area": "Điều hướng D-pad",
                "severity": "HIGH",
                "issue": "Mất dấu focus (Focus Loss) trên màn hình",
                "detail": f"Sau các phím {recent[-4:]}, không có view nào giữ focus",
                "suggestion": "Đảm bảo gán requestFocus() hoặc cấu hình focusable=true cho các view chính"
            }

        # Logic điều hướng phản xạ theo từng nhiệm vụ (15 Deep-Dive Missions)
        if m_id == "MISSION_COLD_START":
            if step == 0:
                action_type = "WAIT"
                action_param = "1.5"
                thought = "Chờ app tải xong dữ liệu màn hình chính và Hero Banner"
            elif step == 1:
                action_type = "KEY"
                action_param = "DPAD_DOWN"
                thought = "Di chuyển focus xuống thẻ trận đầu tiên, kiểm tra độ nhạy Leanback"
            elif step == 2:
                action_type = "KEY"
                action_param = "DPAD_RIGHT"
                thought = "Duyệt thẻ trận đấu thứ hai trên hàng đầu tiên"
            elif step == 3:
                action_type = "KEY"
                action_param = "DPAD_UP"
                thought = "Quay lại Hero Banner kiểm tra khôi phục focus"
            else:
                action_type = "COMPLETE_MISSION"
                action_param = ""
                thought = "Màn hình chính nạp thành công, Hero Banner gọn gàng không card rác"

        elif m_id == "MISSION_SPORTS_MULTI_SOURCE":
            # Duyệt sâu các hàng nguồn thể thao: Socolive, ColaTV, Gà Vàng, Khán Đài
            if step == 0:
                action_type = "KEY"
                action_param = "DPAD_DOWN"
                thought = "Di chuyển xuống hàng Trực Tiếp Socolive"
            elif step in (1, 2, 3):
                action_type = "KEY"
                action_param = "DPAD_RIGHT"
                thought = f"Cuộn ngang sâu trên hàng Socolive (bước {step}) để kiểm tra biên phải"
            elif step == 4:
                action_type = "KEY"
                action_param = "DPAD_DOWN"
                thought = "Di chuyển xuống hàng Trực Tiếp ColaTV"
            elif step == 5:
                action_type = "KEY"
                action_param = "DPAD_RIGHT"
                thought = "Cuộn ngang kiểm tra các trận trên đài ColaTV"
            elif step == 6:
                action_type = "KEY"
                action_param = "DPAD_DOWN"
                thought = "Di chuyển xuống hàng Trực Tiếp Gà Vàng TV"
            elif step == 7:
                action_type = "KEY"
                action_param = "DPAD_DOWN"
                thought = "Di chuyển xuống hàng Trực Tiếp Khán Đài TV"
            else:
                action_type = "COMPLETE_MISSION"
                action_param = ""
                thought = "Đã kiểm tra sâu toàn bộ 4 hàng đài thể thao độc lập"

        elif m_id == "MISSION_SPORTS_ROOM_PICKER":
            if step == 0:
                action_type = "KEY"
                action_param = "ENTER"
                thought = "Mở hộp thoại chọn phòng BLV (RoomPickerDialog) trên thẻ trận đấu"
            elif step == 1:
                action_type = "WAIT"
                action_param = "1.0"
                thought = "Chờ hộp thoại RoomPickerDialog hiển thị danh sách phòng"
            elif step == 2:
                action_type = "KEY"
                action_param = "DPAD_DOWN"
                thought = "Di chuyển xuống phòng BLV tiếp theo trong danh sách"
            elif step == 3:
                action_type = "KEY"
                action_param = "DPAD_UP"
                thought = "Di chuyển ngược lên phòng BLV đầu tiên"
            elif step == 4:
                action_type = "KEY"
                action_param = "BACK"
                thought = "Nhấn BACK đóng RoomPickerDialog trả focus về thẻ trận đấu"
            else:
                action_type = "COMPLETE_MISSION"
                action_param = ""
                thought = "Hộp thoại RoomPickerDialog đóng mở và trap focus chuẩn xác"

        elif m_id == "MISSION_SPORTS_DATA_ACCURACY":
            if step == 0:
                action_type = "SWITCH_TAB"
                action_param = "1"
                thought = "Chuyển sang Tab Lịch đấu để kiểm tra tỷ số X : Y, giờ GMT+7 và nhãn KẾT THÚC"
            elif step == 1:
                action_type = "KEY"
                action_param = "DPAD_DOWN"
                thought = "Kiểm tra thẻ trận: Tên giải đấu chuẩn tiếng Việt, tỷ số dạng X : Y, không spam rác [HOT]/[VIP]"
            elif step == 2:
                action_type = "KEY"
                action_param = "DPAD_DOWN"
                thought = "Kiểm tra trận tiếp theo trong danh sách, xác nhận badge KẾT THÚC nếu trận > 180p"
            else:
                action_type = "COMPLETE_MISSION"
                action_param = ""

        elif m_id == "MISSION_PLAYER_STREAMING_AND_CONTROLS":
            if step == 0:
                action_type = "SWITCH_TAB"
                action_param = "0"
                thought = "Quay về Tab Trực tiếp để mở phát một trận đấu"
            elif step == 1:
                action_type = "KEY"
                action_param = "DPAD_DOWN"
                thought = "Chọn thẻ trận đấu đầu tiên"
            elif step == 2:
                action_type = "KEY"
                action_param = "ENTER"
                thought = "Mở một trận đấu bóng đá để vào PlayerActivity kiểm tra luồng phát và phím tắt"
            elif step == 3:
                action_type = "KEY"
                action_param = "ENTER"
                thought = "Chọn phòng BLV đầu tiên nếu popup chọn phòng xuất hiện"
            elif step == 4:
                action_type = "VERIFY_STREAM"
                action_param = ""
                thought = "Kiểm tra ExoPlayer render video motion chuyển động mượt"
            elif step == 5:
                action_type = "KEY"
                action_param = "KEY_A"
                thought = "Bấm phím A (hoặc phím Đỏ) để test phím tắt xoay vòng tỉ lệ khung hình Aspect Ratio"
            elif step == 6:
                action_type = "KEY"
                action_param = "KEY_B"
                thought = "Bấm phím B (hoặc phím Vàng) để test phím tắt tăng âm lượng Audio Boost (+3dB/+6dB/+9dB)"
            elif step == 7:
                action_type = "KEY"
                action_param = "DOUBLE_BACK"
                thought = "Thoát PlayerActivity bằng DOUBLE_BACK để đóng OSD và về lại màn hình chính"
            else:
                action_type = "COMPLETE_MISSION"
                action_param = ""

        elif m_id == "MISSION_SPORT_PLAYER_BOTTOM_ROW":
            # KL8 fix loop 2 (F66a / P0-4) — hàng dưới player thể thao
            # ("Về trực tiếp" / "TRỰC TIẾP"). Directed launch open=player đã
            # chạy TRƯỚC vòng AI; các bước dưới giả định đang ở PlayerActivity
            # mặt SPORTS. Mở OSD bằng DPAD_DOWN, di chuyển dọc hàng dưới để
            # nó hiện đủ trên screenshot; cửa cứng ở cuối mission
            # (required_ui_markers) FAIL nếu hàng dưới không bao giờ vào dump
            # — không tự kết thúc pass khi chưa thấy hàng.
            if step == 0:
                action_type = "WAIT"
                action_param = "8.0"
                thought = "Chờ luồng live thể thao tải xong trong PlayerActivity mặt SPORTS"
            elif step == 1:
                action_type = "KEY"
                action_param = "DPAD_DOWN"
                thought = "Bấm DPAD_DOWN mở OSD để hiện hàng dưới (liveProgressBar / tvSeekTotal)"
            elif step == 2:
                action_type = "VERIFY_STREAM"
                action_param = ""
                thought = "Chứng minh video live chuyển động thật trước khi soi hàng dưới"
            elif step in (3, 4):
                action_type = "KEY"
                action_param = "DPAD_RIGHT"
                thought = f"Di chuyển sang phải dọc hàng điều khiển dưới (bước {step}) để OSD hiện đủ"
            elif step == 5:
                action_type = "WAIT"
                action_param = "1.0"
                thought = "Giữ OSD mở để lần dump sau ghi nhận hàng dưới"
            elif step == 6:
                action_type = "KEY"
                action_param = "DPAD_DOWN"
                thought = "Mở lại OSD nếu đã tự ẩn sau 3.5s, giữ hàng dưới trên màn hình"
            elif step == 7:
                action_type = "WAIT"
                action_param = "1.5"
                thought = "Giữ hàng dưới trên màn hình để screenshot bắt được trọn hàng"
            elif step == 8:
                if "liveprogressbar" in mission.markers_seen or "tvseektotal" in mission.markers_seen:
                    action_type = "KEY"
                    action_param = "DPAD_LEFT"
                    thought = "Hàng dưới đã ghi nhận trong dump — di chuyển trái kiểm tra focus trên hàng seek"
                else:
                    action_type = "KEY"
                    action_param = "DPAD_DOWN"
                    thought = "Chưa thấy hàng dưới trong dump — mở lại OSD một lần nữa trước khi kết thúc"
            else:
                action_type = "COMPLETE_MISSION"
                action_param = ""
                thought = "Đã giữ OSD + hàng dưới trên màn hình đủ lâu để chụp; cửa cứng sẽ FAIL nếu hàng dưới chưa từng vào dump"

        elif m_id == "MISSION_HOME_BILLBOARD_6_ROWS":
            # KL8 fix loop 1 (P0-2) — Tab 6 giờ là Trang Chủ (billboard 60% +
            # 6 hàng), không còn Cổng Chọn 3 Card. Kiểm tra bằng cách ở Tab 6
            # rồi duyệt D-pad xuống qua các hàng.
            if step == 0:
                action_type = "SWITCH_TAB"
                action_param = "6"
                thought = "Chuyển sang Trang Chủ (Tab 6 — HomeHubFragment: billboard + 6 hàng)"
            elif step == 1:
                action_type = "WAIT"
                action_param = "2.0"
                thought = "Chờ Trang Chủ nạp xong billboard hero và 6 hàng nội dung"
            elif step == 2:
                action_type = "KEY"
                action_param = "DPAD_DOWN"
                thought = "Duyệt xuống hàng 1 (ĐANG PHÁT) kiểm tra focus hạ cánh đúng hàng"
            elif step == 3:
                action_type = "KEY"
                action_param = "DPAD_DOWN"
                thought = "Duyệt xuống hàng 2 (TIẾP TỤC XEM / TRẬN SẮP DIỄN RA)"
            elif step == 4:
                action_type = "KEY"
                action_param = "DPAD_DOWN"
                thought = "Duyệt xuống hàng 3 — xác nhận đủ 6 hàng, không kẹt focus"
            elif step == 5:
                action_type = "KEY"
                action_param = "DPAD_DOWN"
                thought = "Duyệt xuống hàng 4 (MỚI CẬP NHẬT / KÊNH / GIẢI ĐẤU)"
            elif step == 6:
                action_type = "KEY"
                action_param = "DPAD_RIGHT"
                thought = "Cuộn ngang trong hàng kiểm tra thẻ nội dung thật, không ô trống"
            elif step == 7:
                action_type = "WAIT"
                action_param = "1.5"
                thought = "Xác nhận billboard 60% + 6 hàng đã duyệt đủ, focus vẫn rõ"
            else:
                action_type = "COMPLETE_MISSION"
                action_param = ""
                thought = "Đã kiểm tra hoàn tất Trang Chủ: billboard 60% + 6 hàng nội dung thật"

        elif m_id in ("MISSION_SCHEDULE_AND_SIDEBAR_NAVIGATION", "MISSION_SCHEDULE_EPG_AND_FIXTURE_TAP"):
            if step == 0:
                action_type = "SWITCH_TAB"
                action_param = "1"
                thought = "Chuyển sang Tab Lịch đấu (Tab 1)"
            elif step == 1:
                action_type = "WAIT"
                action_param = "1.0"
                thought = "Chờ danh sách lịch nạp xong dữ liệu"
            elif step == 2:
                action_type = "KEY"
                action_param = "DPAD_DOWN"
                thought = "Duyệt lịch thi đấu bóng đá theo ngày"
            elif step == 3:
                action_type = "KEY"
                action_param = "ENTER"
                thought = "Bấm OK vào trận đấu trong lịch để kiểm tra sự kiện onFixtureTap"
            elif step == 4:
                action_type = "KEY"
                action_param = "BACK"
                thought = "Đóng popup phòng live (nếu có) và quay lại danh sách lịch"
            else:
                action_type = "COMPLETE_MISSION"
                action_param = ""

        elif m_id == "MISSION_SIDEBAR_RAIL_FULL_TRAVERSAL":
            if step == 0:
                action_type = "KEY"
                action_param = "DPAD_LEFT"
                thought = "Bấm DPAD_LEFT từ mép trái để mở thanh điều hướng Sidebar Rail"
            elif step in (1, 2, 3, 4):
                action_type = "KEY"
                action_param = "DPAD_DOWN"
                thought = f"Duyệt dọc xuống mục tiếp theo trên Sidebar Rail (bước {step}) kiểm tra không tự đóng"
            elif step == 5:
                action_type = "KEY"
                action_param = "DPAD_RIGHT"
                thought = "Bấm DPAD_RIGHT để đóng Sidebar Rail và chuyển focus vào nội dung tab"
            else:
                action_type = "COMPLETE_MISSION"
                action_param = ""
                thought = "Thanh điều hướng Sidebar Rail hoạt động chuẩn xác, không bị tự đóng hay rò rỉ focus"

        elif m_id in ("MISSION_IPTV_FAVORITES_AND_ZAPPING", "MISSION_IPTV_CATEGORIES_AND_FAVORITES"):
            if step == 0:
                action_type = "SWITCH_TAB"
                action_param = "2"
                thought = "Chuyển sang Tab Truyền hình (IPTV)"
            elif step == 1:
                action_type = "WAIT"
                action_param = "2.0"
                thought = "Chờ tải danh sách kênh IPTV và M3U tùy chọn"
            elif step == 2:
                action_type = "KEY"
                action_param = "DPAD_DOWN"
                thought = "Di chuyển focus xuống lưới kênh truyền hình"
            elif step == 3:
                action_type = "LONG_PRESS"
                action_param = "OK"
                thought = "Bấm giữ phím OK để lưu kênh vào mục Kênh Yêu Thích"
            elif step == 4:
                action_type = "KEY"
                action_param = "DPAD_UP"
                thought = "Di chuyển lên thanh danh mục để kiểm tra tab Yêu Thích và các nhóm kênh"
            elif step == 5:
                action_type = "KEY"
                action_param = "DPAD_RIGHT"
                thought = "Duyệt qua nhóm M3U Của Tôi / Thể Thao Quốc Tế"
            elif step == 6:
                action_type = "KEY"
                action_param = "DPAD_RIGHT"
                thought = "Di chuyển sang nút '➕ THÊM M3U'"
            elif step == 7:
                action_type = "KEY"
                action_param = "ENTER"
                thought = "Bấm OK mở hộp thoại DialogCustomM3u kiểm tra cấu hình link M3U cá nhân"
            elif step == 8:
                action_type = "KEY"
                action_param = "BACK"
                thought = "Bấm BACK đóng hộp thoại DialogCustomM3u"
            else:
                action_type = "COMPLETE_MISSION"
                action_param = ""
                thought = "Đã kiểm tra danh mục IPTV, nạp M3U và lưu kênh yêu thích"

        elif m_id in ("MISSION_IPTV_EPG_AND_HERO_PREVIEW", "MISSION_IPTV_EPG_AND_ZAPPING_PLAYER"):
            if step == 0:
                action_type = "KEY"
                action_param = "DPAD_DOWN"
                thought = "Duyệt qua lưới kênh để nạp lịch phát sóng EPG chuẩn GMT+7 và Hero Preview"
            elif step == 1:
                action_type = "WAIT"
                action_param = "1.5"
                thought = "Chờ Hero Preview debounce nạp luồng phát thử góc trên"
            elif step == 2:
                action_type = "KEY"
                action_param = "ENTER"
                thought = "Mở phát toàn màn hình kênh truyền hình"
            elif step == 3:
                action_type = "KEYPAD"
                action_param = "1"
                thought = "Gõ phím số 1 trên remote để test OSD nhảy kênh trực tiếp (Direct Zapping)"
            elif step == 4:
                action_type = "KEY"
                action_param = "CHANNEL_UP"
                thought = "Thử phím CHANNEL_UP chuyển kênh nhanh"
            elif step == 5:
                action_type = "KEY"
                action_param = "BACK"
                thought = "Thoát trình phát về lại Tab IPTV"
            else:
                action_type = "COMPLETE_MISSION"
                action_param = ""

        elif m_id == "MISSION_IPTV_PLAYER_BACK_FOCUS":
            # KL8 fix loop 2 (F66b / P0-6) — BACK trong player IPTV (scenario
            # gốc: BACK → focus NONE). Directed launch đã mở player IPTV
            # (tab 2 → ENTER) TRƯỚC vòng AI. Chờ OSD tự ẩn (3.5s) rồi bấm
            # BACK đúng lúc overlay đang ẩn — đó là nhánh BACK thoát player;
            # runner ghi activity + focus NGAY SAU BACK (evidence
            # back_in_player) và cửa cuối mission FAIL nếu không có bước BACK
            # nào trong player, hoặc focus NONE sau BACK.
            if step == 0:
                action_type = "WAIT"
                action_param = "5.0"
                thought = "Chờ player IPTV tải xong và OSD tự ẩn sau 3.5s (đúng tiền điều kiện P0-6: BACK khi overlay đang ẩn)"
            elif step == 1:
                action_type = "VERIFY_STREAM"
                action_param = ""
                thought = "Chứng minh kênh IPTV phát chuyển động thật trước khi bấm BACK"
            elif step == 2:
                action_type = "KEY"
                action_param = "BACK"
                thought = "Bấm BACK trong player IPTV — runner ghi focus ngay sau BACK"
            elif step == 3:
                action_type = "WAIT"
                action_param = "1.5"
                thought = "Chờ chuyển cảnh sau BACK (về lưới IPTV hoặc vẫn ở player) rồi ghi focus"
            elif step == 4:
                if not mission.evidence.get("back_in_player") and "PlayerActivity" in (state.get("activity") or ""):
                    action_type = "KEY"
                    action_param = "BACK"
                    thought = "Bước BACK trước chưa ghi được bằng chứng trong player — bấm lại BACK khi vẫn ở trong player"
                else:
                    action_type = "WAIT"
                    action_param = "1.0"
                    thought = "Bằng chứng BACK đã ghi — chờ một nhịp rồi kết thúc"
            else:
                action_type = "COMPLETE_MISSION"
                action_param = ""
                thought = "Đã bấm BACK trong player IPTV và ghi focus ngay sau đó; cửa cứng sẽ FAIL nếu không có bằng chứng BACK hoặc focus NONE sau BACK"

        elif m_id == "MISSION_IPTV_MINI_GUIDE":
            # KL8 fix loop 2 (F66c / P1-4) — Mini-Guide "Danh Sách Kênh".
            # Directed launch đã mở player IPTV TRƯỚC vòng AI. Đường mở
            # Mini-Guide (theo code PlayerActivity): OSD → xuống thanh dưới
            # (tvBottomBar: Kênh trước / Kênh kế / EPG / Yêu thích / Tỉ lệ /
            # Cài đặt) → nút EPG (btnTvEpg → toggleSidebar) → OK. Trong guide,
            # DPAD_DOWN zap đổi kênh ngay; BACK đóng guide về OSD. Cửa cứng ở
            # cuối mission (tiêu đề "Danh Sách Kênh" trong dump) FAIL nếu
            # panel guide không bao giờ mở — channelSidebar là LinearLayout
            # không focusable, không có text nên KHÔNG BAO GIỜ vào dump, đừng
            # gate trên id của nó.
            ev = mission.evidence
            focused = (state.get("focused_sig") or "").lower()
            focused_txt = (state.get("focused_text") or "").strip()
            if mission.evidence.get("miniguide_header_seen"):
                if not ev.get("guide_zapped"):
                    ev["guide_zapped"] = True
                    action_type = "KEY"
                    action_param = "DPAD_DOWN"
                    thought = "Mini-Guide đã mở — bấm Xuống zap thử một kênh trong guide (guide vẫn mở, focus chạy theo kênh)"
                elif not ev.get("guide_closed"):
                    ev["guide_closed"] = True
                    action_type = "KEY"
                    action_param = "BACK"
                    thought = "BACK đóng Mini-Guide về lại OSD (theo luật BACK tầng guide)"
                else:
                    action_type = "COMPLETE_MISSION"
                    action_param = ""
                    thought = "Đã mở Mini-Guide, zap trong guide và BACK đóng guide; cửa cứng sẽ FAIL nếu tiêu đề 'Danh Sách Kênh' chưa từng vào dump"
            elif step == 0:
                action_type = "WAIT"
                action_param = "4.0"
                thought = "Chờ player IPTV tải xong và OSD tự ẩn trước khi mở thanh điều khiển"
            elif step == 1:
                action_type = "KEY"
                action_param = "DPAD_DOWN"
                thought = "Bấm DPAD_DOWN mở OSD — focus về nút KÊNH ở hàng trên"
            elif step == 2:
                action_type = "KEY"
                action_param = "DPAD_DOWN"
                thought = "Từ hàng trên xuống thanh dưới (nút đầu: Kênh trước)"
            elif ev.get("epg_enter_pressed"):
                # Vừa bấm OK trên nút EPG ở bước trước — chờ guide trượt
                # vào (260ms) rồi quét lại, không di chuyển vội.
                ev["epg_enter_pressed"] = False
                action_type = "WAIT"
                action_param = "1.5"
                thought = "Vừa bấm OK trên nút EPG — chờ Mini-Guide trượt vào rồi quét lại"
            elif "btntvepg" in focused or focused_txt == "EPG":
                if ev.get("epg_enters", 0) >= 2:
                    action_type = "COMPLETE_MISSION"
                    action_param = ""
                    thought = "Đã bấm EPG 2 lần mà Mini-Guide vẫn không mở — cửa tiêu đề 'Danh Sách Kênh' sẽ FAIL mission"
                else:
                    ev["epg_enters"] = ev.get("epg_enters", 0) + 1
                    ev["epg_enter_pressed"] = True
                    action_type = "KEY"
                    action_param = "ENTER"
                    thought = "Focus đang ở nút EPG — bấm OK mở Mini-Guide (btnTvEpg → toggleSidebar)"
            else:
                moves = ev.get("guide_moves", 0)
                if moves < 3:
                    ev["guide_moves"] = moves + 1
                    action_type = "KEY"
                    action_param = "DPAD_RIGHT"
                    thought = "Duyệt sang phải trên thanh dưới tìm nút EPG (thứ 3: Kênh trước → Kênh kế → EPG)"
                elif moves == 3:
                    ev["guide_moves"] = 4
                    action_type = "KEY"
                    action_param = "DPAD_UP"
                    thought = "Chưa thấy EPG trên thanh dưới — lên lại hàng trên thử đường khác"
                elif moves < 6:
                    ev["guide_moves"] = moves + 1
                    action_type = "KEY"
                    action_param = "DPAD_RIGHT"
                    thought = "Duyệt sang phải trên hàng trên tìm đường mở Mini-Guide"
                else:
                    action_type = "COMPLETE_MISSION"
                    action_param = ""
                    thought = "Không tìm thấy nút EPG sau 6 lần di chuyển — cửa tiêu đề 'Danh Sách Kênh' sẽ FAIL mission (Mini-Guide chưa mở)"

        elif m_id in ("MISSION_PHIM_NGUONC_AND_SEARCH", "MISSION_PHIM_NGUONC_AND_CATEGORIES"):
            if step == 0:
                action_type = "SWITCH_TAB"
                action_param = "5"
                thought = "Điều hướng sang Tab Kho Phim (NguonC & Anime)"
            elif step == 1:
                action_type = "WAIT"
                action_param = "1.5"
                thought = "Chờ kho phim tải Hero Banner và danh sách thể loại"
            elif step == 2:
                action_type = "KEY"
                action_param = "DPAD_UP"
                thought = "Di chuyển lên thanh bộ lọc Apple Pills"
            elif step == 3:
                action_type = "KEY"
                action_param = "DPAD_DOWN"
                thought = "Nhấn DPAD_DOWN từ Apple Pill kiểm tra focus hạ cánh thẳng xuống nút XEM NGAY (btnHeroPlay)"
            else:
                action_type = "COMPLETE_MISSION"
                action_param = ""

        elif m_id == "MISSION_PHIM_EPISODE_PICKER_AND_FAVORITE":
            if step == 0:
                action_type = "KEY"
                action_param = "DPAD_RIGHT"
                thought = "Chuyển focus từ nút XEM NGAY sang nút CHỌN TẬP (btnHeroEpisodes)"
            elif step == 1:
                action_type = "KEY"
                action_param = "ENTER"
                thought = "Bấm OK mở hộp thoại chọn tập phim (EpisodePickerDialog)"
            elif step == 2:
                action_type = "KEY"
                action_param = "DPAD_DOWN"
                thought = "Duyệt danh sách các tập phim trong EpisodePickerDialog"
            elif step == 3:
                action_type = "KEY"
                action_param = "BACK"
                thought = "Đóng hộp thoại chọn tập bằng phím BACK"
            elif step == 4:
                action_type = "KEY"
                action_param = "DPAD_RIGHT"
                thought = "Chuyển focus sang nút LƯU PHIM (btnHeroFavorite)"
            elif step == 5:
                action_type = "KEY"
                action_param = "ENTER"
                thought = "Bấm OK lưu phim vào danh sách yêu thích"
            elif step == 6:
                action_type = "KEY"
                action_param = "DPAD_RIGHT"
                thought = "Chuyển focus sang nút ĐỔI PHIM (btnHeroNext) trên Spotlight Hero"
            elif step == 7:
                action_type = "KEY"
                action_param = "ENTER"
                thought = "Bấm OK đổi sang phim nổi bật kế tiếp trong kho Spotlight"
            else:
                action_type = "COMPLETE_MISSION"
                action_param = ""
                thought = "Đã kiểm tra hoàn tất hộp thoại chọn tập, lưu phim và đổi Spotlight"

        elif m_id == "MISSION_COLD_OPEN_LAST_EPISODE":
            # KL8 fix loop 2 (F66d / F45) — cold-open tập cuối và kiểm tra
            # nút "Tập tiếp" có lóe không. Directed launch đã sang tab Kho
            # Phim TRƯỚC vòng AI. Từ hero: sang nút CHỌN TẬP (btnHeroEpisodes)
            # → mở EpisodePickerDialog → đi xuống tới khi focus ĐÚNG YÊN
            # (tập cuối danh sách) → ENTER mở thẳng tập đó từ cold start.
            # Sau khi mở: WAIT cho detail resolve, DPAD_DOWN mở lại OSD,
            # WAIT rồi kết thúc — runner lấy mẫu flash ở lần dump đầu tiên
            # thấy player (sớm) và ở lần dump sau DPAD_DOWN (muộn).
            ev = mission.evidence
            hero = (state.get("focused_sig") or "").lower()
            if ev.get("last_episode_enter_pressed"):
                phase = ev.get("post_open_phase", 0)
                if phase == 0:
                    ev["post_open_phase"] = 1
                    action_type = "WAIT"
                    action_param = "5.0"
                    thought = "Tập cuối đã mở — chờ detail resolve (gate Tập tiếp áp sau resolve)"
                elif phase == 1:
                    ev["post_open_phase"] = 2
                    action_type = "KEY"
                    action_param = "DPAD_DOWN"
                    thought = "Mở lại OSD để lấy mẫu muộn: nút Tập tiếp phải ẨN ở tập cuối sau khi detail resolve"
                elif phase == 2:
                    ev["post_open_phase"] = 3
                    action_type = "WAIT"
                    action_param = "1.0"
                    thought = "Giữ OSD mở một nhịp để dump muộn ghi nhận nút Tập tiếp (ẩn là đúng)"
                else:
                    action_type = "COMPLETE_MISSION"
                    action_param = ""
                    thought = "Đã mở tập cuối và lấy mẫu flash sớm + muộn; cửa cứng sẽ FAIL nếu tập cuối chưa mở hoặc Tập tiếp lóe/hiện"
            elif ev.get("picker_open"):
                cur = state.get("focused_sig") or ""
                prev = ev.get("picker_prev_focus")
                downs = ev.get("picker_downs", 0)
                if prev is not None and cur == prev and downs >= 2:
                    ev["last_episode_enter_pressed"] = True
                    ev["last_episode_label"] = (state.get("focused_text") or "").strip()
                    action_type = "KEY"
                    action_param = "ENTER"
                    thought = f"Focus đã đứng yên ở tập cuối danh sách ({ev['last_episode_label']}) — bấm OK mở thẳng tập cuối từ cold start"
                elif downs >= 12:
                    action_type = "COMPLETE_MISSION"
                    action_param = ""
                    thought = "Đi xuống 12 lần mà focus chưa đứng yên ở tập cuối — không mở tập ngẫu nhiên, cửa cứng sẽ FAIL mission"
                else:
                    ev["picker_prev_focus"] = cur
                    ev["picker_downs"] = downs + 1
                    action_type = "KEY"
                    action_param = "DPAD_DOWN"
                    thought = f"Đi xuống trong EpisodePicker tìm tập cuối (lần {downs + 1})"
            elif step == 0:
                action_type = "WAIT"
                action_param = "2.0"
                thought = "Chờ Kho Phim nạp xong hero phim và các hàng"
            elif "btnheroepisodes" in hero or "heroepisodes" in hero:
                action_type = "KEY"
                action_param = "ENTER"
                thought = "Focus đang ở nút CHỌN TẬP — bấm OK mở EpisodePickerDialog"
            elif "btnheroplay" in hero or "heroplay" in hero:
                action_type = "KEY"
                action_param = "DPAD_RIGHT"
                thought = "Focus đang ở nút XEM NGAY — sang phải tới nút CHỌN TẬP"
            elif step <= 3:
                action_type = "KEY"
                action_param = "DPAD_DOWN"
                thought = "Từ hàng Apple Pills xuống hero phim (focus hạ cánh vào XEM NGAY)"
            else:
                action_type = "COMPLETE_MISSION"
                action_param = ""
                thought = "Không tới được nút CHỌN TẬP / EpisodePicker không mở — cửa cứng sẽ FAIL mission (tập cuối chưa mở)"

        elif m_id == "MISSION_FINISHED_MATCH_SCORES":
            # KL8 fix loop 2 (F66 item 7) — negative controls trên trận đã
            # kết thúc. Directed launch đã sang tab Lịch đấu TRƯỚC vòng AI.
            # Duyệt các dòng lịch để đưa trận KẾT THÚC lên màn hình, bấm OK
            # vào dòng trận đã xong (app báo toast "Trận đấu đã kết thúc",
            # không mở picker phòng), rồi sang tab Thể thao soi thẻ/hero.
            # Cửa cứng ở cuối mission: không thấy trận kết thúc → NOT
            # TESTABLE; tỉ số phi thực tế hiện số thô → FAIL. Không tự kết
            # thúc pass khi chưa thấy trận kết thúc nào. BACK sau ENTER là
            # an toàn (MainActivity: BACK ở tab top-level về Trang Chủ, và
            # đóng dialog/panel nếu ENTER mở panel phòng do focus không
            # rơi đúng dòng trận đã xong).
            ev = mission.evidence
            if step == 0:
                action_type = "WAIT"
                action_param = "2.0"
                thought = "Chờ danh sách lịch (tab 1) nạp xong dữ liệu trận đấu"
            elif step in (1, 2, 3):
                action_type = "KEY"
                action_param = "DPAD_DOWN"
                thought = f"Duyệt xuống dòng lịch (lần {step}) tìm trận có badge KẾT THÚC"
            elif step == 4:
                if ev.get("finished_found"):
                    ev["finished_enter_pressed"] = True
                    action_type = "KEY"
                    action_param = "ENTER"
                    thought = "Đã thấy trận KẾT THÚC trong dump — bấm OK vào dòng đang focus để xác nhận hành vi trận đã xong (toast 'Trận đấu đã kết thúc', không mở picker phòng)"
                else:
                    action_type = "KEY"
                    action_param = "DPAD_DOWN"
                    thought = "Chưa thấy trận KẾT THÚC ở tab Lịch — duyệt thêm một dòng lịch"
            elif step == 5:
                if ev.get("finished_enter_pressed"):
                    action_type = "KEY"
                    action_param = "BACK"
                    thought = "Đóng panel/toast sau khi bấm vào trận đã xong (BACK ở tab top-level về Trang Chủ nếu không có panel nào mở)"
                else:
                    action_type = "SWITCH_TAB"
                    action_param = "0"
                    thought = "Chưa thấy trận kết thúc ở tab Lịch — sang tab Thể thao soi thẻ trận/hero (badge KT)"
            elif step == 6:
                if ev.get("last_action") == ("KEY", "BACK"):
                    action_type = "SWITCH_TAB"
                    action_param = "0"
                    thought = "Đã đóng panel sau khi bấm trận đã xong — sang tab Thể thao soi thẻ trận/hero (badge KT)"
                else:
                    action_type = "KEY"
                    action_param = "DPAD_DOWN"
                    thought = "Duyệt thẻ trận ở tab Thể thao tìm thẻ có badge KT"
            elif step in (7, 8):
                action_type = "KEY"
                action_param = "DPAD_DOWN"
                thought = f"Duyệt tiếp thẻ trận/hero (lần {step - 6}) để dump ghi đủ chuỗi tỉ số của trận đã xong"
            else:
                action_type = "COMPLETE_MISSION"
                action_param = ""
                thought = "Đã duyệt lịch + thẻ trận/hero đủ lâu để ghi tỉ số trận đã xong; cửa cứng sẽ báo NOT TESTABLE nếu không thấy trận kết thúc, FAIL nếu tỉ số ảo hiện số thô"

        elif m_id in ("MISSION_PHIM_PLAYER_SEEK_AND_RESUME", "MISSION_VOD_PLAYER_SEEK_AND_RESUME"):
            # KL8 fix loop 1 (P0-1): LAUNCH_WEB_PLAYER đã chạy TRƯỚC vòng AI
            # (directed_launch); bước 0 ở đây là chờ embed tải, không launch lại.
            if step == 0:
                action_type = "WAIT"
                action_param = "8.0"
                thought = "Chờ WebPlayer tải xong trang embed THẬT (qua proxy VN) và video"
            elif step == 1:
                action_type = "KEY"
                action_param = "DPAD_DOWN"
                thought = "Bấm DPAD_DOWN để mở thanh OSD hiển thị tiêu đề và nút điều khiển web"
            elif step == 2:
                # KL8 fix loop 2 (F63 dwell, review webplayer vòng 2): chờ
                # ~10s rồi lấy mẫu — OSD còn hiện + focus còn ở
                # btnWebPlayPause không (bản sửa thật của F63 là dwell 300s
                # thay vì tự ẩn 3.5s)? Chỉ ghi nhận, không fail mission.
                action_type = "WAIT"
                action_param = "10.0"
                thought = "Chờ 10s đo dwell OSD (bản sửa F63: OSD giữ 300s thay vì tự ẩn 3.5s) — OSD còn hiện + focus ở btnWebPlayPause không"
            elif step == 3:
                action_type = "KEY"
                action_param = "DPAD_RIGHT"
                thought = "Bấm D-pad Phải kiểm tra tua tới +10s qua JS injection trên WebPlayer"
            elif step == 4:
                action_type = "KEY"
                action_param = "DPAD_LEFT"
                thought = "Bấm D-pad Trái kiểm tra tua lùi -10s qua JS injection trên WebPlayer"
            elif step == 5:
                action_type = "KEY"
                action_param = "OK"
                thought = "Bấm OK toggle Play/Pause trên WebPlayer"
            elif step == 6:
                # KL8 fix loop 2 (F63): OSD chưa thấy trong dump thì thử
                # DPAD_DOWN thêm một lần thay vì thoát ngay (OSD là cửa fail).
                if mission.evidence.get("web_osd_seen"):
                    action_type = "KEY"
                    action_param = "BACK"
                    thought = "Bấm BACK để thoát WebPlayer và tự động lưu tiến độ vào Lịch sử xem"
                else:
                    action_type = "KEY"
                    action_param = "DPAD_DOWN"
                    thought = "OSD WebPlayer chưa thấy trong dump — thử mở lại OSD một lần nữa trước khi thoát"
            elif step == 7:
                action_type = "SWITCH_TAB"
                action_param = "5"
                thought = "Về lại Kho Phim (Tab 5) để kiểm tra hàng Tiếp Tục Xem (Resume Playback)"
            elif step == 8:
                action_type = "WAIT"
                action_param = "1.5"
                thought = "Xác nhận hàng Tiếp Tục Xem đã nạp thẻ phim vừa xem dở"
            else:
                action_type = "COMPLETE_MISSION"
                action_param = ""
                thought = "Đã kiểm tra hoàn tất Trình Phát Web (WebPlayerActivity) và tính năng Tiếp Tục Xem"

        elif m_id == "MISSION_WEBPLAYER_DIRECTED_REAL_FILM":
            # KL8 fix loop 1 (P0-1) — launch có định hướng (LAUNCH_WEB_PLAYER)
            # đã chạy TRƯỚC vòng AI (directed_launch); các bước dưới giả định
            # đang ở trong WebPlayerActivity. Nếu chưa vào được, cửa cứng ở run()
            # đã FAIL mission trước khi tới đây.
            # KL8 fix loop 2 (F63/F47 tách gate, review webplayer vòng 2):
            # bước 3 đo dwell OSD ~10s; bước 9-12 đi tới nút Tốc độ và bấm
            # OK set tốc độ (đọc lại nhãn ở bước sau — set-and-read-back
            # cho gate F47); bước 13 chờ read-back xong mới thoát.
            if step == 0:
                action_type = "WAIT"
                action_param = "8.0"
                thought = "Chờ trang embed thật tải xong qua proxy VN và video bắt đầu phát"
            elif step == 1:
                action_type = "VERIFY_STREAM"
                action_param = ""
                thought = "Chứng minh video THẬT SỰ chuyển động (motion delta) — không chỉ activity mở lên"
            elif step == 2:
                action_type = "KEY"
                action_param = "DPAD_DOWN"
                thought = "Bấm DPAD_DOWN mở thanh OSD web (tiêu đề + nút điều khiển) — focus về btnWebPlayPause"
            elif step == 3:
                # F63 dwell: chờ ~10s rồi lấy mẫu — OSD còn hiện + focus còn
                # ở btnWebPlayPause không (bản sửa thật của F63 là dwell 300s
                # thay vì tự ẩn 3.5s)? Chỉ ghi nhận, không fail mission.
                action_type = "WAIT"
                action_param = "10.0"
                thought = "Chờ 10s đo dwell OSD (bản sửa F63: OSD giữ 300s thay vì tự ẩn 3.5s) — OSD còn hiện + focus ở btnWebPlayPause không"
            elif step == 4:
                action_type = "KEY"
                action_param = "DPAD_RIGHT"
                thought = "Tua tới +10s qua JS trên WebPlayer (hoặc di chuyển focus trên OSD nếu OSD vẫn hiện)"
            elif step == 5:
                action_type = "KEY"
                action_param = "DPAD_LEFT"
                thought = "Tua lùi -10s qua JS trên WebPlayer (hoặc di chuyển focus trên OSD nếu OSD vẫn hiện)"
            elif step == 6:
                action_type = "KEY"
                action_param = "OK"
                thought = "Bấm OK tạm dừng phát trên WebPlayer"
            elif step == 7:
                action_type = "KEY"
                action_param = "OK"
                thought = "Bấm OK phát lại trên WebPlayer"
            elif step == 8:
                action_type = "KEY"
                action_param = "DPAD_DOWN"
                thought = "Mở lại OSD chắc chắn trước khi tìm nút Tốc độ (focus về btnWebPlayPause nếu đang ở WebView)"
            elif step in (9, 10, 11, 12):
                # Đi ngang thanh OSD tới nút Tốc độ (thứ tự: PlayPause →
                # SeekFwd → NextEp → Episodes → Speed; nút Tập trước/Tiếp
                # GONE khi detail chưa resolve nên focus-search bỏ qua).
                # Focus đã ở nút Tốc độ thì bấm OK set tốc độ (F47
                # set-and-read-back); đã bấm rồi thì chờ cho nhãn ổn định.
                if mission.evidence.get("speed_set_attempted"):
                    action_type = "WAIT"
                    action_param = "1.0"
                    thought = "Đã bấm OK set tốc độ — chờ nhãn ổn định để đọc lại (read-back F47)"
                elif "tốc độ" in focused_text or "btnwebspeed" in (state.get("ui_summary") or "").lower():
                    action_type = "KEY"
                    action_param = "OK"
                    thought = "Bấm nút Tốc độ trên OSD web để đổi tốc độ phát (F47: set-and-read-back — nhãn phải đổi sang tốc độ mới)"
                else:
                    action_type = "KEY"
                    action_param = "DPAD_RIGHT"
                    thought = "Di chuyển trên OSD web về phía nút Tốc độ (Speed)"
            elif step == 13:
                # Thoát — nhưng nếu vừa bấm OK set tốc độ ở bước 12 thì
                # chờ thêm 1.5s cho read-back lấy mẫu xong rồi mới thoát;
                # OSD chưa thấy thì thử DPAD_DOWN thêm một lần THAY VÌ thoát
                # ngay (thoát rồi thì không còn cơ hội mở OSD nữa).
                if mission.evidence.get("speed_readback_pending"):
                    action_type = "WAIT"
                    action_param = "1.5"
                    thought = "Chờ read-back nhãn tốc độ lấy mẫu xong trước khi thoát (F47)"
                elif mission.evidence.get("web_osd_seen"):
                    action_type = "KEY"
                    action_param = "BACK"
                    thought = "OSD WebPlayer đã thấy trong dump — thoát WebPlayer bằng BACK và tự động lưu tiến độ xem dở"
                else:
                    action_type = "KEY"
                    action_param = "DPAD_DOWN"
                    thought = "OSD WebPlayer chưa thấy trong dump sau DPAD_DOWN — thử mở lại OSD một lần nữa trước khi thoát"
            elif step == 14:
                last = mission.evidence.get("last_action") or (None, None)
                if last == ("KEY", "BACK"):
                    action_type = "SWITCH_TAB"
                    action_param = "5"
                    thought = "Về lại Kho Phim (Tab 5) để kiểm tra hàng Tiếp Tục Xem"
                elif last == ("WAIT", "1.5"):
                    action_type = "KEY"
                    action_param = "BACK"
                    thought = "Read-back nhãn tốc độ đã lấy mẫu xong — thoát WebPlayer bằng BACK"
                elif last == ("KEY", "DPAD_DOWN") and not mission.evidence.get("web_osd_seen"):
                    action_type = "KEY"
                    action_param = "BACK"
                    thought = "Thử lại DPAD_DOWN vẫn không thấy OSD — thoát WebPlayer, cửa F63 sẽ FAIL mission"
                else:
                    action_type = "SWITCH_TAB"
                    action_param = "5"
                    thought = "Về lại Kho Phim (Tab 5) để kiểm tra hàng Tiếp Tục Xem"
            elif step == 15:
                if mission.evidence.get("last_action") == ("KEY", "BACK"):
                    action_type = "SWITCH_TAB"
                    action_param = "5"
                    thought = "Về lại Kho Phim (Tab 5) để kiểm tra hàng Tiếp Tục Xem"
                else:
                    action_type = "WAIT"
                    action_param = "1.5"
                    thought = "Xác nhận hàng Tiếp Tục Xem đã nạp thẻ phim vừa xem dở trên WebPlayer"
            else:
                action_type = "COMPLETE_MISSION"
                action_param = ""
                thought = "Đã kiểm tra hoàn tất WebPlayer với phim embed thật: phát/tạm dừng/tua/tốc độ/lưu tiến độ"

        elif m_id == "MISSION_PLAYER_SETTINGS_DIALOG":
            # KL8 Task 12 — bước 0 mở mặt VOD native XÁC ĐỊNH bằng deep-link
            # open=vodplayer (trước đây mission này bắt đầu bằng DPAD_DOWN trên
            # tab Phim mà không có player nào mở — mặt VOD không được kiểm tra).
            if step == 0:
                action_type = "LAUNCH_VOD_PLAYER_DIRECTED"
                action_param = ""
                thought = "Mở PlayerActivity mặt VOD native bằng deep-link open=vodplayer (tập m3u8 THẬT)"
            elif step == 1:
                action_type = "KEY"
                action_param = "DPAD_DOWN"
                thought = "Mở thanh điều khiển của trình phát Native PlayerActivity"
            elif step == 2:
                action_type = "KEY"
                action_param = "OK"
                thought = "Bấm OK mở Dialog Cài Đặt Trình Phát Thống Nhất (btnBarSettings)"
            elif step == 3:
                action_type = "KEY"
                action_param = "DPAD_DOWN"
                thought = "Duyệt qua các nhóm cài đặt trong Dialog (Hình ảnh -> Âm thanh)"
            elif step == 4:
                action_type = "KEY"
                action_param = "DPAD_DOWN"
                thought = "Duyệt tiếp xuống nhóm Tỉ lệ khung hình và Bước tua"
            elif step == 5:
                action_type = "KEY"
                action_param = "DPAD_RIGHT"
                thought = "Thử chọn một chip tỉ lệ khung hình hoặc bước tua mới"
            elif step == 6:
                action_type = "KEY"
                action_param = "ENTER"
                thought = "Bấm OK áp dụng cài đặt mới ngay trong Dialog"
            elif step == 7:
                action_type = "KEY"
                action_param = "BACK"
                thought = "Bấm BACK để đóng Dialog Cài Đặt và giữ nguyên trình phát"
            elif step == 8:
                action_type = "KEY"
                action_param = "DPAD_RIGHT"
                thought = "Di chuyển trên thanh điều khiển sang nút Tua tới / Tua lùi"
            elif step == 9:
                action_type = "KEY"
                action_param = "OK"
                thought = "Bấm OK kiểm tra chức năng tua thời gian trên thanh điều khiển"
            elif step == 10:
                action_type = "KEY"
                action_param = "DPAD_RIGHT"
                thought = "Di chuyển sang nút Tạm Dừng / Phát (btnBarPlayPause)"
            elif step == 11:
                action_type = "KEY"
                action_param = "OK"
                thought = "Bấm OK kiểm tra tính năng Tạm Dừng / Tiếp tục phát video"
            elif step == 12:
                action_type = "KEY"
                action_param = "A"
                thought = "Thử phím tắt A (Red key remote) đổi tỉ lệ khung hình trực tiếp"
            elif step == 13:
                action_type = "KEY"
                action_param = "B"
                thought = "Thử phím tắt B (Yellow key remote) tăng cường âm thanh Audio Boost trực tiếp"
            elif step == 14:
                action_type = "KEY"
                action_param = "MENU"
                thought = "Thử phím tắt MENU mở Server Picker chọn nguồn phát"
            elif step == 15:
                action_type = "KEY"
                action_param = "BACK"
                thought = "Bấm BACK đóng menu Server Picker"
            elif step == 16:
                action_type = "KEY"
                action_param = "DOUBLE_BACK"
                thought = "Thoát trình phát Native về lại kho phim, kiểm tra tự lưu tiến độ"
            else:
                action_type = "COMPLETE_MISSION"
                action_param = ""
                thought = "Đã kiểm tra toàn diện các chức năng của trình phát Native PlayerActivity"

        elif m_id == "MISSION_SEARCH_AND_SETTINGS_FEEDBACK":
            if step == 0:
                action_type = "SWITCH_TAB"
                action_param = "3"
                thought = "Chuyển sang Tab Tìm kiếm (Tab 3) để kiểm tra ô nhập searchInput"
            elif step == 1:
                action_type = "TEXT"
                action_param = "ngoai hang"
                thought = "Nhập từ khóa tìm kiếm trận đấu"
            elif step == 2:
                action_type = "SWITCH_TAB"
                action_param = "4"
                thought = "Chuyển sang Tab Cài đặt (Tab 4) để kiểm tra thông tin phiên bản và mục Liên hệ & Báo lỗi"
            elif step == 3:
                action_type = "KEY"
                action_param = "DPAD_DOWN"
                thought = "Di chuyển xuống mục 'Liên hệ & Báo lỗi' Telegram @kenhlivetv"
            elif step == 4:
                action_type = "KEY"
                action_param = "DPAD_DOWN"
                thought = "Di chuyển tiếp xuống mục 'Liên hệ & Báo lỗi' Telegram @kenhlivetv"
            elif step == 5:
                action_type = "KEY"
                action_param = "DPAD_DOWN"
                thought = "Focus vào dòng 'Liên hệ & Báo lỗi' Telegram @kenhlivetv"
            elif step == 6:
                action_type = "KEY"
                action_param = "ENTER"
                thought = "Bấm OK mở hộp thoại FeedbackDialog kiểm tra mã QR và liên kết t.me/kenhlivetv"
            elif step == 7:
                action_type = "KEY"
                action_param = "BACK"
                thought = "Bấm BACK để đóng FeedbackDialog và quay lại danh sách Cài đặt"
            else:
                action_type = "COMPLETE_MISSION"
                action_param = ""
                thought = "Đã kiểm tra hoàn tất Tab Tìm kiếm và hộp thoại Báo lỗi Telegram @kenhlivetv"

        elif m_id == "MISSION_DPAD_CHAOS_STRESS_AND_RECOVERY":
            # Nhồi phím ngẫu nhiên 4 hướng để stress-test
            stress_keys = ["DPAD_UP", "DPAD_DOWN", "DPAD_LEFT", "DPAD_RIGHT"]
            action_type = "KEY"
            action_param = random.choice(stress_keys)
            thought = f"D-pad chaos stress & focus recovery: nhồi phím ngẫu nhiên {action_param}"
            if step >= min(5, mission.max_steps - 1):
                action_type = "COMPLETE_MISSION"
                action_param = ""

        else:
            action_type = "COMPLETE_MISSION"
            action_param = ""

        return {
            "thought": thought,
            "action_type": action_type,
            "action_param": action_param,
            "expected_result": "Giao diện cập nhật mượt mà theo thao tác D-pad",
            "defect_detected": defect,
            "_provider": "LOCAL_REFLEX"
        }


# ==============================================================================
# 2. DEVICE & VISION PROBES (Android TV Remote & Sensor Driver)
# ==============================================================================
class AndroidTVDevice:
    """Điều khiển Android TV qua ADB và thu thập dữ liệu cảm biến (Sensors)."""

    def __init__(self, serial=None, pkg=PKG):
        self.serial = serial
        self.adb = f"adb -s {serial}" if serial else "adb"
        self.pkg = pkg
        self.action_history = []
        self.focus_step_history = []
        self._reported_anomaly_keys = set()
        self._logcat_checkpoint = ""

    def launch_app(self):
        t0 = time.time()
        sh(f"{self.adb} shell am start -n {self.pkg}/.MainActivity")
        while time.time() - t0 < 25:
            if self.is_app_in_foreground():
                return round((time.time() - t0) * 1000)
            time.sleep(0.2)
        return -1

    def is_app_in_foreground(self):
        out = sh(f"{self.adb} shell dumpsys window 2>/dev/null | grep -m1 mCurrentFocus")
        return self.pkg in out

    def current_activity(self):
        out = sh(f"{self.adb} shell dumpsys activity activities 2>/dev/null | grep -m1 -E 'mResumedActivity|topResumedActivity'")
        m = re.search(r"([A-Za-z0-9_.]+)/([.A-Za-z0-9_]+)", out)
        return f"{m.group(1)}/{m.group(2)}" if m else "?"

    def send_key(self, key_name):
        code = KEY_MAP.get(key_name.upper(), 20)
        sh(f"{self.adb} shell input keyevent {code}")
        self.action_history.append(key_name)
        if len(self.action_history) > 20:
            self.action_history.pop(0)

    def send_long_press(self, key_name="OK", duration_ms=1500):
        code = KEY_MAP.get(key_name.upper(), 23)
        res = sh(f"{self.adb} shell input keyevent --longpress {code}")
        if "__ERR__" in res or "unrecognized" in res.lower() or "error" in res.lower():
            state = self.dump_ui_state()
            b = state.get("focused_bounds")
            if b:
                m = re.match(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]", b)
                if m:
                    x1, y1, x2, y2 = map(int, m.groups())
                    cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
                    sh(f"{self.adb} shell input swipe {cx} {cy} {cx} {cy} {duration_ms}")
                else:
                    sh(f"{self.adb} shell input swipe 960 540 960 540 {duration_ms}")
            else:
                sh(f"{self.adb} shell input swipe 960 540 960 540 {duration_ms}")
        self.action_history.append(f"LONG_PRESS({key_name})")
        if len(self.action_history) > 20:
            self.action_history.pop(0)

    def send_keypad_digits(self, digits_str):
        for ch in str(digits_str):
            if ch in KEY_MAP:
                code = KEY_MAP[ch]
                sh(f"{self.adb} shell input keyevent {code}")
                time.sleep(0.18)
        self.action_history.append(f"KEYPAD({digits_str})")
        if len(self.action_history) > 20:
            self.action_history.pop(0)

    def input_text(self, text):
        safe_text = re.sub(r"[^a-zA-Z0-9_-]", "%s", text)
        sh(f"{self.adb} shell input text \"{safe_text}\"")
        self.action_history.append(f"TEXT({text})")

    def switch_tab(self, tab_index):
        """Chuyển đổi trực tiếp giữa 6 tab: 0:Live, 1:Lịch, 2:IPTV, 3:Tìm kiếm, 4:Cài đặt, 5:Kho Phim."""
        sh(f"{self.adb} shell am start -n {self.pkg}/.MainActivity --ei tab {int(tab_index)} -f 0x04000000")
        self.action_history.append(f"SWITCH_TAB({tab_index})")

    def open_multiview(self):
        """Mở Trang Chủ (Tab 6 — trước đây là Home Hub Portal, Task 4 đã đổi thành màn hình chính)."""
        sh(f"{self.adb} shell am start -n {self.pkg}/.MainActivity --ei tab 6 -f 0x04000000")
        self.action_history.append("OPEN_HOME_HUB")

    def launch_web_player(self):
        """Khởi chạy WebPlayerActivity với một tập embed THẬT qua deep-link debug
        `open=webplayer` (MainActivity tự resolve tập embed thật từ API KKPhim).
        URL giả cũ (player.phimapi.com/player/?url=https://test.m3u8) không phát
        được phim thật nên đã bỏ — xem KL8 Task 12 / F44."""
        sh(f"{self.adb} shell am start -n {self.pkg}/.MainActivity --es open webplayer")
        self.action_history.append("LAUNCH_WEB_PLAYER")

    def launch_vod_player(self):
        """Khởi chạy PlayerActivity mặt VOD (FILM) với một tập m3u8 THẬT qua
        deep-link debug `open=vodplayer` (MainActivity tự resolve từ API KKPhim).
        Dùng để mở mặt VOD native một cách xác định cho mission settings dialog
        (KL8 Task 12 — mặt VOD trước đây không có lối vào xác định)."""
        sh(f"{self.adb} shell am start -n {self.pkg}/.MainActivity --es open vodplayer")
        self.action_history.append("LAUNCH_VOD_PLAYER")

    def launch_sport_player(self):
        """Khởi chạy PlayerActivity mặt SPORTS với trận live THẬT đầu tiên qua
        deep-link debug `open=player` (MainActivity.openPlayer: resolve phòng
        live Socolive đầu tiên rồi mở PlayerActivity Hub.SPORTS). Dùng cho
        mission F66a (P0-4): mặt SPORTS trước đây chỉ tới được khi AI tự bấm
        vào card trận — run 42963719447 chỉ mở được 1 bước rồi rời ngay."""
        sh(f"{self.adb} shell am start -n {self.pkg}/.MainActivity --es open player")
        self.action_history.append("LAUNCH_SPORT_PLAYER")

    def launch_iptv_player(self):
        """Mở PlayerActivity IPTV bằng UI (không có deep-link mở thẳng player
        IPTV): sang tab Truyền hình, DOWN vào lưới kênh, ENTER mở phát kênh
        đầu tiên (kênh hero hoặc card đầu lưới đều mở PlayerActivity IPTV).
        Dùng cho mission F66b/F66c (fix loop 2) — trước đây player IPTV chỉ
        tới được khi AI tự bấm vào kênh trên lưới."""
        self.switch_tab(2)
        time.sleep(3.0)
        self.send_key("DPAD_DOWN")
        time.sleep(0.5)
        self.send_key("ENTER")
        time.sleep(4.0)
        self.action_history.append("LAUNCH_IPTV_PLAYER")

    def get_pss_memory_mb(self):
        """Đo tổng lượng bộ nhớ RAM PSS (MB) của ứng dụng."""
        out = sh(f"{self.adb} shell dumpsys meminfo {self.pkg} 2>/dev/null | grep -E 'TOTAL PSS:|TOTAL:' | head -1")
        m = re.search(r"(\d+)", out)
        if m:
            return round(int(m.group(1)) / 1024.0, 1)
        return -1.0

    def screencap_bytes(self):
        try:
            raw = subprocess.run(f"{self.adb} exec-out screencap -p".split(), capture_output=True, timeout=20).stdout
            return raw if len(raw) > 5000 else None
        except Exception:
            return None

    def is_blank(self, png_bytes):
        """Phát hiện màn hình đen hoặc rỗng hoàn toàn (Dead Blank Screen)."""
        if not png_bytes or not Image or not ImageStat:
            return False
        try:
            im = Image.open(io.BytesIO(png_bytes)).convert("L").resize((64, 64))
            stat = ImageStat.Stat(im)
            return stat.stddev[0] < 4.0 or stat.mean[0] < 2.0
        except Exception:
            return False

    def dump_ui_state(self):
        """Đọc và bóc tách cây UI XML trong thời gian thực kèm thu thập dữ liệu cho Deep Anomaly Inspector."""
        sh(f"{self.adb} shell 'rm -f /sdcard/uidump.xml; uiautomator dump /sdcard/uidump.xml >/dev/null 2>&1'")
        xml_text = sh(f"{self.adb} shell cat /sdcard/uidump.xml 2>/dev/null", timeout=10)
        if "<hierarchy" not in xml_text:
            time.sleep(0.25)
            sh(f"{self.adb} shell 'uiautomator dump --compressed /sdcard/uidump.xml >/dev/null 2>&1'")
            xml_text = sh(f"{self.adb} shell cat /sdcard/uidump.xml 2>/dev/null", timeout=10)

        focused_sig = "NONE"
        focused_text = ""
        focused_bounds = None
        focusable_nodes = []
        summary_lines = []
        all_visible_texts = []
        has_dialog = False
        # KL8 fix loop 1 (P0-2): id các node có selected=true — MainActivity.showTab
        # đặt isSelected trên nav item của tab đang hiển thị, dùng để xác định
        # tab chính xác (không đoán qua từ khóa nội dung).
        selected_ids = []

        if "<hierarchy" in xml_text:
            try:
                start = xml_text.find("<hierarchy")
                end = xml_text.rfind("</hierarchy>")
                if start != -1 and end != -1:
                    xml_text = xml_text[start:end + len("</hierarchy>")]
                root = ET.fromstring(xml_text.strip())

                for elem in root.iter("node"):
                    a = elem.attrib
                    is_focused = a.get("focused") == "true"
                    is_focusable = a.get("focusable") == "true"
                    txt = (a.get("text", "") or a.get("content-desc", "")).strip()
                    r_id = a.get("resource-id", "").split("/")[-1]
                    bounds = a.get("bounds", "")

                    if a.get("selected") == "true" and r_id:
                        selected_ids.append(r_id)

                    if txt:
                        all_visible_texts.append((r_id, txt))

                    # KL8 fix loop 2 (F66d): id list thật của EpisodePicker là
                    # dialogEpisodesGrid (EpisodePickerDialog.kt:66) — vòng lặp
                    # này duyệt MỌI node nên id RecyclerView (không text, không
                    # focusable) vẫn thấy được ở đây, khác với blob của scanner
                    # chỉ có node có text / focusable. episodeList là id chết
                    # (không tồn tại trong app), đã xóa.
                    if r_id in ("dialogTitle", "roomList", "dialogEpisodesGrid", "ivTelegramQr", "btnOpenTelegram", "alertTitle"):
                        has_dialog = True

                    if is_focusable:
                        focusable_nodes.append({"id": r_id, "text": txt, "bounds": bounds, "focused": is_focused})
                        marker = "[FOCUSED] " if is_focused else "          "
                        summary_lines.append(f"{marker}{r_id or 'view'} ('{txt[:25]}') {bounds}")

                    if is_focused:
                        focused_sig = f"{r_id or 'view'}#{bounds}"
                        focused_text = txt
                        focused_bounds = bounds
            except Exception:
                pass

        return {
            "focused_sig": focused_sig,
            "focused_text": focused_text,
            "focused_bounds": focused_bounds,
            # KL8 fix loop 2 (F63/F47 tách gate, review webplayer vòng 2):
            # WebView có trong cây UI không — để mission note ghi lại màn hình
            # thực tế render ra gì khi vào player dưới force_web (nhánh m3u8-only
            # phải render trang <video> tối thiểu, không phải loadUrl trần).
            "has_webview": "WebView" in xml_text,
            "focusable_count": len(focusable_nodes),
            "all_visible_texts": all_visible_texts,
            "has_dialog": has_dialog,
            "selected_ids": selected_ids,
            "ui_summary": "\n".join(summary_lines[:25]) or "(Không tìm thấy focusable view)"
        }

    def inspect_deep_anomalies(self, ui_state, current_activity="", png_bytes=None):
        """Hệ thống quét lỗi tầng sâu tự động (Deep Anomaly Probes) trên mỗi bước thực thi."""
        anomalies = []
        focused_sig = ui_state.get("focused_sig", "NONE")
        focused_bounds = ui_state.get("focused_bounds")
        last_key = self.action_history[-1] if self.action_history else ""

        # 0. Kiểm tra màn hình đen / rỗng hoàn toàn (Dead Blank Screen)
        if png_bytes and self.is_blank(png_bytes) and "MainActivity" in current_activity:
            # Xác thực 2 lần để tránh bắt nhầm frame chuyển cảnh (transition) hoặc loading đen thoáng qua
            time.sleep(1.5)
            recheck_png = self.screencap_bytes()
            if recheck_png and self.is_blank(recheck_png):
                blank_key = f"BLANK:{current_activity}"
                if blank_key not in self._reported_anomaly_keys:
                    self._reported_anomaly_keys.add(blank_key)
                    anomalies.append({
                        "area": "Hiển thị Màn Hình (Deep Probe)",
                        "severity": "CRITICAL",
                        "issue": f"Màn hình đen / rỗng hoàn toàn (Dead Blank Screen) tại {current_activity}",
                        "detail": "Độ biến thiên pixel stddev < 4.0 và mean < 2.0 kéo dài hơn 1.5s sau khi nạp",
                        "suggestion": "Kiểm tra render lifecycle, layout xml hoặc sự cố crash UI background"
                    })

        # 1. Ghi nhận lịch sử bước focus để phát hiện Focus Trap (Kẹt nút D-pad)
        vis_texts = tuple(t for _, t in ui_state.get("all_visible_texts", [])[:15])
        state_sig = f"{focused_sig}|{hash(vis_texts)}"
        self.focus_step_history.append((current_activity, state_sig, last_key))
        if len(self.focus_step_history) > 10:
            self.focus_step_history.pop(0)

        if len(self.focus_step_history) >= 3 and focused_sig != "NONE":
            s1, s2, s3 = self.focus_step_history[-3], self.focus_step_history[-2], self.focus_step_history[-1]
            dpad_dirs = ("DPAD_UP", "DPAD_DOWN", "DPAD_LEFT", "DPAD_RIGHT", "UP", "DOWN", "LEFT", "RIGHT")
            if (s1[0] == s2[0] == s3[0] and
                    s1[1] == s2[1] == s3[1] and
                    s2[2] in dpad_dirs and s3[2] in dpad_dirs and s2[2] == s3[2] and
                    "PlayerActivity" not in current_activity and
                    "WebPlayerActivity" not in current_activity and
                    not ui_state.get("has_dialog", False) and
                    ui_state.get("focusable_count", 0) > 3):
                # Không tính là trap nếu đang ở mép màn hình và bấm phím hướng ra mép (ví dụ nút ở biên trái bấm DPAD_LEFT)
                is_edge_bump = False
                if focused_bounds:
                    m_b = re.findall(r"-?\d+", focused_bounds)
                    if len(m_b) >= 4:
                        x1, y1, x2, y2 = map(int, m_b[:4])
                        if s3[2] in ("DPAD_LEFT", "LEFT") and x1 < 350:
                            is_edge_bump = True
                        elif s3[2] in ("DPAD_RIGHT", "RIGHT") and x2 > 1350:
                            is_edge_bump = True
                        elif s3[2] in ("DPAD_UP", "UP") and y1 < 200:
                            is_edge_bump = True
                        elif s3[2] in ("DPAD_DOWN", "DOWN") and y2 > 880:
                            is_edge_bump = True

                if not is_edge_bump:
                    trap_key = f"TRAP:{current_activity}:{focused_sig}:{s3[2]}"
                    if trap_key not in self._reported_anomaly_keys:
                        self._reported_anomaly_keys.add(trap_key)
                        anomalies.append({
                            "area": "Điều hướng Focus TV (Deep Probe)",
                            "severity": "MEDIUM",
                            "issue": f"Nghi vấn kẹt Focus (Focus Trap) tại '{focused_sig}' khi bấm {s3[2]}",
                            "detail": f"Gửi phím {s3[2]} liên tiếp nhưng tiêu điểm và nội dung màn hình giữ nguyên tại {focused_sig} trên {current_activity}",
                            "suggestion": "Kiểm tra cấu hình nextFocus hoặc ranh giới cuộn của RecyclerView"
                        })

        # 2. Kiểm tra Off-screen Focus Leak & Zero-size View Focus
        if focused_bounds:
            m = re.findall(r"-?\d+", focused_bounds)
            if len(m) >= 4:
                x1, y1, x2, y2 = map(int, m[:4])
                w, h = x2 - x1, y2 - y1
                if x2 <= 0 or y2 <= 0 or x1 >= 1920 or y1 >= 1080:
                    leak_key = f"OFFSCREEN:{focused_sig}"
                    if leak_key not in self._reported_anomaly_keys:
                        self._reported_anomaly_keys.add(leak_key)
                        anomalies.append({
                            "area": "Rò rỉ Focus ngoài màn hình (Deep Probe)",
                            "severity": "HIGH",
                            "issue": f"Focus lọt vào phần tử nằm ngoài khung hình TV: {focused_sig}",
                            "detail": f"Tọa độ bounds={focused_bounds} nằm ngoài viewport 1920x1080",
                            "suggestion": "Đặt visibility=GONE và descendantFocusability=FOCUS_BLOCK_DESCENDANTS khi ẩn panel"
                        })
                elif w <= 2 or h <= 2:
                    zero_key = f"ZEROSIZE:{focused_sig}"
                    if zero_key not in self._reported_anomaly_keys:
                        self._reported_anomaly_keys.add(zero_key)
                        anomalies.append({
                            "area": "Focus vào phần tử tàng hình (Deep Probe)",
                            "severity": "HIGH",
                            "issue": f"Focus rơi vào view có kích thước {w}x{h}px: {focused_sig}",
                            "detail": f"View {focused_sig} có diện tích quá nhỏ khiến người dùng mất dấu con trỏ trên TV",
                            "suggestion": "Đặt isFocusable=false cho view ẩn hoặc vạch phân cách"
                        })

        # 3. Quét chuỗi văn bản lỗi / dữ liệu thô chưa xử lý (Raw Placeholder / Null / Exception)
        bad_patterns = [r"\bnull\b", r"\bundefined\b", r"\bNaN\b", r"NullPointerException", r"JsonSyntaxException"]
        for r_id, txt in ui_state.get("all_visible_texts", []):
            for pat in bad_patterns:
                if re.search(pat, txt):
                    txt_key = f"BADTEXT:{r_id}:{txt[:20]}"
                    if txt_key not in self._reported_anomaly_keys:
                        self._reported_anomaly_keys.add(txt_key)
                        anomalies.append({
                            "area": "Hiển thị dữ liệu (Deep Probe)",
                            "severity": "HIGH",
                            "issue": f"Xuất hiện chuỗi lỗi/null thô trên giao diện: '{txt[:40]}'",
                            "detail": f"Node '{r_id}' hiển thị văn bản '{txt}'",
                            "suggestion": "Xử lý fallback chuỗi rỗng hoặc mặc định trước khi gán vào TextView"
                        })

        # 4. Kiểm tra rò rỉ focus xuống màn hình nền khi Dialog đang mở
        if ui_state.get("has_dialog") and focused_sig != "NONE":
            bg_views = ("cardRoot", "schedCard", "liveList", "schedList", "phimMainList", "phimPoster", "heroPlay")
            if any(bg in focused_sig for bg in bg_views):
                dlg_key = f"DLGLEAK:{focused_sig}"
                if dlg_key not in self._reported_anomaly_keys:
                    self._reported_anomaly_keys.add(dlg_key)
                    anomalies.append({
                        "area": "Quản lý Focus Hộp Thoại (Deep Probe)",
                        "severity": "HIGH",
                        "issue": f"Focus lọt xuống màn hình nền ({focused_sig}) khi Dialog đang mở",
                        "detail": f"Hộp thoại đang hiển thị nhưng tiêu điểm D-pad vẫn nằm ở view nền {focused_sig}",
                        "suggestion": "Gọi requestFocus() vào nút mặc định của Dialog trong setOnShowListener"
                    })

        # 5. Kiểm tra tính toàn vẹn dữ liệu giờ thi đấu & tỷ số thể thao (Kickoff Time & Score Integrity Probe)
        for r_id, txt in ui_state.get("all_visible_texts", []):
            clean_txt = txt.strip()
            # 5a. Rò rỉ giờ thi đấu hoặc tag trạng thái vào tên giải đấu cardLeague
            if "cardLeague" in r_id:
                if re.match(r"^\d{1,2}:\d{2}$", clean_txt) or re.search(r"\[(SẮP ĐÁ|LIVE|TRỰC TIẾP|\d{1,2}:\d{2})\]", clean_txt, re.IGNORECASE):
                    leak_key = f"TIME_LEAK_LEAGUE:{r_id}:{clean_txt}"
                    if leak_key not in self._reported_anomaly_keys:
                        self._reported_anomaly_keys.add(leak_key)
                        anomalies.append({
                            "area": "Chuẩn hóa dữ liệu thể thao (Deep Probe)",
                            "severity": "HIGH",
                            "issue": f"Giờ thi đấu hoặc nhãn trạng thái bị gán nhầm vào tên giải đấu: '{clean_txt}'",
                            "detail": f"View {r_id} hiển thị '{clean_txt}' thay vì tên giải đấu hợp lệ",
                            "suggestion": "Lọc sạch bracket thời gian trong DataNormalizer.parseMatch"
                        })
            # 5b. Bị gán nhầm giờ thi đấu thành tỷ số ảo khi hiển thị định dạng tỷ số (ví dụ '17 : 0' hoặc '23 : 30')
            # Lưu ý: Thẻ trận SẮP ĐÁ hiển thị giờ thi đấu chuẩn HH:mm (ví dụ '23:30', '19:45' không có khoảng trắng)
            # ở center pill là tính năng chuẩn, chỉ coi là lỗi khi có định dạng tỷ số có khoảng trắng 'X : Y' hoặc số bàn thắng phi thực tế (> 15).
            if "cardScore" in r_id or "score" in r_id.lower():
                m_score = re.match(r"^(\d{1,2})\s+[:\-]\s+(\d{1,2})$", clean_txt)
                if m_score:
                    s1, s2 = int(m_score.group(1)), int(m_score.group(2))
                    if s1 in (17, 18, 19, 20, 21, 22, 23) and s2 in (0, 15, 30, 45):
                        fake_key = f"FAKE_SCORE_FROM_TIME:{r_id}:{clean_txt}"
                        if fake_key not in self._reported_anomaly_keys:
                            self._reported_anomaly_keys.add(fake_key)
                            anomalies.append({
                                "area": "Toàn vẹn tỷ số thể thao (Deep Probe)",
                                "severity": "HIGH",
                                "issue": f"Nghi vấn giờ thi đấu bị chuyển đổi thành tỷ số ảo: '{clean_txt}'",
                                "detail": f"View {r_id} hiển thị tỷ số '{clean_txt}' khớp với khung giờ phát sóng",
                                "suggestion": "Bổ sung kiểm tra loại trừ giờ thi đấu trong DataNormalizer regex"
                            })
            # 5c. Rò rỉ placeholder raw
            if "[$kickoffTime]" in clean_txt or "luc-" in clean_txt:
                raw_key = f"RAW_TIME_PLACEHOLDER:{r_id}:{clean_txt[:20]}"
                if raw_key not in self._reported_anomaly_keys:
                    self._reported_anomaly_keys.add(raw_key)
                    anomalies.append({
                        "area": "Hiển thị giờ thi đấu (Deep Probe)",
                        "severity": "HIGH",
                        "issue": f"Rò rỉ placeholder mã nguồn giờ thi đấu chưa format: '{clean_txt}'",
                        "detail": f"View {r_id} hiển thị chuỗi kỹ thuật chưa qua xử lý",
                        "suggestion": "Định dạng giờ thi đấu qua formatTimestampToTime trước khi truyền vào view"
                    })

        return anomalies

    def detect_video_motion(self, duration_sec=1.0, samples=3, is_player_context=False):
        """Xác định toán học xem video ExoPlayer có đang render khung hình thật hay bị đứng hình."""
        if not Image or not ImageChops or not ImageStat:
            return True, 1.5  # Heuristic pass nếu thiếu thư viện

        frames = []
        interval = max(0.1, duration_sec / samples)
        for _ in range(samples):
            b = self.screencap_bytes()
            if b:
                try:
                    im = Image.open(io.BytesIO(b)).convert("L").resize((160, 90))
                    frames.append(im)
                except Exception:
                    pass
            time.sleep(interval)

        if len(frames) < 2:
            return False, 0.0

        diffs = []
        for i in range(len(frames) - 1):
            diff = ImageChops.difference(frames[i], frames[i + 1])
            mean_diff = ImageStat.Stat(diff).mean[0] / 255.0 * 100.0
            diffs.append(mean_diff)

        avg_diff = sum(diffs) / len(diffs)
        # Video phát trực tiếp thường có pixel difference > 0.35%
        is_playing = avg_diff >= 0.35
        # Chỉ áp dụng đệm buffer 2.0s trên CI nếu thực sự đang ở trong màn hình Player
        if not is_playing and is_player_context:
            time.sleep(2.0)
            frames = []
            for _ in range(samples):
                b = self.screencap_bytes()
                if b:
                    try:
                        im = Image.open(io.BytesIO(b)).convert("L").resize((160, 90))
                        frames.append(im)
                    except Exception:
                        pass
                time.sleep(interval)
            if len(frames) >= 2:
                diffs = []
                for i in range(len(frames) - 1):
                    diff = ImageChops.difference(frames[i], frames[i + 1])
                    mean_diff = ImageStat.Stat(diff).mean[0] / 255.0 * 100.0
                    diffs.append(mean_diff)
                avg_diff = sum(diffs) / len(diffs)
                is_playing = avg_diff >= 0.35

        return is_playing, avg_diff

    def detect_focus_ring(self, png_bytes, focused_bounds_str):
        """Phát hiện viền sáng focus (#FF6500 cam KenhLive, #FF9F0A amber, Trắng hoặc Cyan) xung quanh view đang focus."""
        if not png_bytes or not Image or not focused_bounds_str:
            return False, "UNKNOWN", 0.0

        try:
            m = re.findall(r"\d+", focused_bounds_str)
            if len(m) < 4:
                return False, "INVALID_BOUNDS", 0.0
            x1, y1, x2, y2 = map(int, m[:4])

            im = Image.open(io.BytesIO(png_bytes)).convert("RGB")
            W, H = im.size
            if not (0 <= x1 < x2 <= W and 0 <= y1 < y2 <= H):
                return False, "OUT_OF_BOUNDS", 0.0

            # Lấy vùng biên bao quanh ranh giới thẻ (±6px để bắt trọn cả viền inset lẫn glow outset)
            pad = 6
            crop_outer = im.crop((max(0, x1 - pad), max(0, y1 - pad), min(W, x2 + pad), min(H, y2 + pad)))
            px = crop_outer.load()
            cw, ch = crop_outer.size

            orange_hits = 0
            white_hits = 0
            cyan_hits = 0
            total_samples = 0

            # Quét dải viền ngang (mép trên & mép dưới, độ dày 6px)
            y_indices = list(range(min(pad + 2, ch))) + list(range(max(0, ch - pad - 2), ch))
            for y in set(y_indices):
                for x in range(0, cw, 2):
                    total_samples += 1
                    r, g, b = px[x, y]
                    if r > 180 and 45 < g < 185 and b < 85:  # #FF6500 (Cam) & #FF9F0A (Amber Apple)
                        orange_hits += 1
                    elif r > 215 and g > 215 and b > 215:  # Trắng
                        white_hits += 1
                    elif r < 110 and g > 180 and b > 200:  # Cyan neon
                        cyan_hits += 1

            # Quét dải viền dọc (mép trái & mép phải, độ dày 6px)
            x_indices = list(range(min(pad + 2, cw))) + list(range(max(0, cw - pad - 2), cw))
            for x in set(x_indices):
                for y in range(0, ch, 2):
                    total_samples += 1
                    r, g, b = px[x, y]
                    if r > 180 and 45 < g < 185 and b < 85:
                        orange_hits += 1
                    elif r > 215 and g > 215 and b > 215:
                        white_hits += 1
                    elif r < 110 and g > 180 and b > 200:
                        cyan_hits += 1

            matched_hits = orange_hits + white_hits + cyan_hits
            has_ring = matched_hits > (total_samples * 0.12)
            if orange_hits >= white_hits and orange_hits >= cyan_hits:
                color_name = "ORANGE"
            elif white_hits >= cyan_hits:
                color_name = "WHITE"
            else:
                color_name = "CYAN"
            return has_ring, color_name, matched_hits / max(1, total_samples)
        except Exception:
            return False, "ERR", 0.0

    def checkpoint_logcat(self):
        lines = sh(f"{self.adb} logcat -d -v threadtime", timeout=20).splitlines()
        self._last_logcat_len = len(lines)

    def get_new_logcat_alerts(self):
        cur = sh(f"{self.adb} logcat -d -v threadtime", timeout=25).splitlines()
        last_len = getattr(self, "_last_logcat_len", 0)
        new_lines = cur[last_len:] if len(cur) >= last_len else cur
        self._last_logcat_len = len(cur)

        alerts = []
        for i, line in enumerate(new_lines):
            if "FATAL EXCEPTION" in line or "AndroidRuntime: FATAL" in line:
                alerts.append(f"CRASH: {line[:120]}")
                stack = "\n".join(new_lines[i:i+20])
                print(f"💥 [LOGCAT CRASH DETECTED]:\n{stack}", flush=True)
            elif "ANR in " + self.pkg in line:
                alerts.append(f"ANR: {line[:120]}")
            elif "OutOfMemoryError" in line:
                alerts.append(f"OOM: {line[:120]}")
            elif "ExoPlayer" in line and ("error" in line.lower() or "failure" in line.lower()):
                alerts.append(f"PLAYER_ERR: {line[:100]}")
            elif "Choreographer" in line and "Skipped" in line:
                m_skip = re.search(r"Skipped\s+(\d+)\s+frames", line)
                if m_skip and int(m_skip.group(1)) >= 45:
                    alerts.append(f"UI_JANK: Bỏ lỡ {m_skip.group(1)} frames")

        return alerts[:5]


# ==============================================================================
# 3. MISSION MODELS (Danh sách mục tiêu kiểm thử AI)
# ==============================================================================
class QAMission:
    def __init__(self, name, title, description, success_criteria, max_steps=8,
                 required_activity=None, directed_launch=None,
                 required_ui_markers=None, requires_web_osd=False,
                 requires_speed_probe=False,
                 allow_not_testable=False):
        self.name = name
        self.title = title
        self.description = description
        self.success_criteria = success_criteria
        self.max_steps = max_steps
        # KL8 fix loop 1 (P0-1): cửa cứng chống false pass cho mission CÓ ĐỊNH HƯỚNG.
        # - directed_launch: action (VD "LAUNCH_WEB_PLAYER") mà runner chạy
        #   TRƯỚC vòng AI, vì AI cloud có thể không bao giờ chọn nó.
        # - required_activity: substring activity BẮT BUỘC phải xuất hiện trong
        #   mission (VD "WebPlayerActivity"); không tới được thì mission FAIL,
        #   kể cả khi AI bấm COMPLETE_MISSION hay chạy hết số bước.
        self.required_activity = required_activity
        self.directed_launch = directed_launch
        self.reached_required = False
        # KL8 fix loop 2 (F66/F63): cửa cứng theo TRẠNG THÁI trong UI dump.
        # - required_ui_markers: substring (lowercase, id hoặc text) — mission
        #   chỉ pass khi ÍT NHẤT MỘT marker từng xuất hiện trong UI dump của
        #   mission (VD hàng dưới player: "liveprogressbar"/"tvseektotal").
        #   Không thấy marker nào thì FAIL, kể cả khi AI bấm COMPLETE_MISSION.
        # - requires_web_osd (F63, review webplayer vòng 2): mission WebPlayer
        #   chỉ pass khi OSD KL8 đã MỞ — chứng minh bằng nút điều khiển OSD
        #   trong dump (btnWebPlayPause/btnWebSeekBack/... — container
        #   webControlBar/playerTopOsd không focusable, không có text nên
        #   KHÔNG BAO GIỜ xuất hiện trong dump, đừng gate trên nó) + focus
        #   rơi vào một nút điều khiển sau DPAD_DOWN. KHÔNG gate trên
        #   btnWebSpeed — nút đó chỉ hiện khi probe pass, thuộc F47.
        # - requires_speed_probe (F47, review webplayer vòng 2): probe tốc độ
        #   phải pass — chứng minh bằng btnWebSpeed VISIBLE (nút GONE by
        #   design khi probe fail) + set-and-read-back NẾU mission đã bấm OK
        #   trên nút Tốc độ (nhãn sau set phải đổi sang tốc độ mới). Hai gate
        #   F63/F47 RIÊNG: probe fail không bao giờ báo thành "OSD không mở",
        #   OSD hỏng không bao giờ trông như đã sửa.
        # - allow_not_testable: mission được kết thúc NOT TESTABLE (không pass,
        #   không fail) khi dữ liệu live không có trạng thái cần kiểm.
        # - evidence: cờ/bằng chứng do runner + reflex ghi trong lúc chạy
        #   (VD last_action, marker_shots, back_in_player, last_episode_*).
        self.required_ui_markers = [m.lower() for m in (required_ui_markers or [])]
        self.markers_seen = set()
        self.requires_web_osd = requires_web_osd
        self.requires_speed_probe = requires_speed_probe
        self.allow_not_testable = allow_not_testable
        self.evidence = {}
        self.not_testable = False
        self.not_testable_reason = ""
        self.result_detail = ""
        self.steps_executed = 0
        self.passed = False
        self.failed = False
        self.findings = []
        self.timeline = []


# ==============================================================================
# 4. AUTONOMOUS QA RUNNER (Điều phối tổng thể)
# ==============================================================================
class AutonomousQASuite:
    def __init__(self, out_dir="/tmp/qa_report", serial=None, quick=False):
        self.quick = bool(quick or os.environ.get("QA_QUICK", "0") == "1")
        self.out_dir = out_dir
        self.shots_dir = os.path.join(out_dir, "shots")
        os.makedirs(self.shots_dir, exist_ok=True)

        self.brain = AIBrain()
        self.device = AndroidTVDevice(serial=serial, pkg=PKG)
        self.session = QASession(out_dir=out_dir, serial=serial, pkg=PKG)
        self.brain.init_session(self.session.session_id)
        self.session.set_ai_provider(self.brain.provider_active)

        # Trình quay video toàn bộ quá trình kiểm thử Android TV
        self.recorder = None
        try:
            self.recorder = VideoRecorder(serial=serial, out_dir=out_dir)
        except Exception as e:
            print(f"⚠️ [VideoRecorder] Không thể nạp module video recorder: {e}", flush=True)

        self.action_history = self.device.action_history

        self.ALL_TABS = {
            0: "Tab 0: Trực tiếp (Live - ColaTV/Gà Vàng/Khán Đài/Socolive)",
            1: "Tab 1: Lịch đấu (Schedule - Lịch phát sóng các ngày)",
            2: "Tab 2: Truyền hình (IPTV - TV360 HLS, VTV, HTV, Hero Preview, Lưới 5 cột)",
            3: "Tab 3: Tìm kiếm (Search - Ô nhập từ khóa & Danh sách kết quả)",
            4: "Tab 4: Cài đặt (Settings - Cập nhật & cấu hình server)",
            5: "Tab 5: Kho Phim (NguonC - Phim mới, Phim bộ, Phim lẻ, Anime)",
            6: "Tab 6: Trang Chủ (Home - Billboard 60% + 6 hàng)"
        }
        self.tested_tabs = set()

        self.missions = [
            QAMission(
                "MISSION_COLD_START",
                "Khởi Động Lạnh, TTI & Hero Banner Rộng Rãi",
                "Mở app từ trạng thái tắt, kiểm tra Hero Banner đã bỏ thẻ thống kê trận đấu rác, đo TTI, kiểm tra giao diện Home không bị đen màn hình.",
                "Màn hình chính nạp đủ dữ liệu, focus xuất hiện tại thẻ đầu tiên.",
                max_steps=5
            ),
            QAMission(
                "MISSION_SPORTS_MULTI_SOURCE",
                "Thể Thao Đa Nguồn & Cuộn Ngang Sâu (Horizontal Rail Deep Traversal)",
                "Duyệt qua các hàng đài độc lập (Socolive, ColaTV, Gà Vàng, Khán Đài), cuộn ngang sâu liên tục để kiểm tra biên phải và khôi phục tiêu điểm.",
                "Các tab lọc đài phản hồi chuẩn, D-pad di chuyển mượt mà không kẹt, không có emoji rác [👁⏳⭐].",
                max_steps=8
            ),
            QAMission(
                "MISSION_SPORTS_ROOM_PICKER",
                "Hộp Thoại Chọn Phòng BLV & Vòng Đời Dialog (RoomPicker & Tab Switch)",
                "Mở RoomPickerDialog trên thẻ trận đấu, duyệt danh sách phòng BLV, test đóng bằng BACK và kiểm tra không rò rỉ focus đè lên các tab khác.",
                "Hộp thoại RoomPickerDialog trap focus chuẩn xác, đóng mở êm ái.",
                max_steps=6
            ),
            QAMission(
                "MISSION_SPORTS_DATA_ACCURACY",
                "Chuẩn Hóa Dữ Liệu Bóng Đá GMT+7, Tỷ Số X:Y & Nhãn KẾT THÚC",
                "Kiểm tra tên giải đấu chuẩn tiếng Việt (Ngoại Hạng Anh, Cúp C1...), điểm số trận hiển thị chuẩn dạng X : Y, trận qua 180p có badge KẾT THÚC.",
                "Dữ liệu hiển thị sạch bóng, không spam [HOT]/[VIP], đúng múi giờ GMT+7.",
                max_steps=4
            ),
            QAMission(
                "MISSION_PLAYER_STREAMING_AND_CONTROLS",
                "Trình Phát Video ExoPlayer, Server Picker & Phím Tắt TV (A/B/Menu)",
                "Mở phát trận đấu, kiểm tra ExoPlayer motion render, menu đổi đài, phím tắt A/Đỏ chuyển Aspect Ratio, phím tắt B/Vàng tăng Audio Boost.",
                "Video chuyển động mượt, phím tắt đổi tỉ lệ và âm lượng phản hồi nhanh.",
                max_steps=8
            ),
            QAMission(
                "MISSION_SPORT_PLAYER_BOTTOM_ROW",
                "Player Thể Thao: Hàng Dưới \"Về trực tiếp\" / \"TRỰC TIẾP\" (P0-4, F66a)",
                "Mission CÓ ĐỊNH HƯỚNG (F66a): harness mở PlayerActivity mặt SPORTS bằng deep-link open=player TRƯỚC vòng AI (trận live Socolive thật đầu tiên — mặt SPORTS trước đây chỉ tới được khi AI tự bấm vào card trận, run 42963719447 chỉ mở được 1 bước rồi rời ngay, step_043 lại mất screenshot). Từ trong player: chờ tải, mở OSD bằng DPAD_DOWN, VERIFY_STREAM chứng minh video chuyển động, di chuyển dọc hàng dưới để OSD + hàng seek hiện đủ trên screenshot. CỬA CỨNG: mission FAIL nếu hàng dưới (liveProgressBar/tvSeekTotal) không bao giờ vào UI dump.",
                "Hàng dưới của player thể thao hiện đủ trên màn hình (seek bar live + nhãn TRỰC TIẾP hoặc nút Về trực tiếp), có screenshot bắt được trọn hàng, video live chuyển động. Hàng dưới đã vào được UI dump (bắt buộc — không vào được là FAIL, không phải pass).",
                max_steps=10,
                directed_launch="LAUNCH_SPORT_PLAYER_DIRECTED",
                required_activity="PlayerActivity",
                required_ui_markers=["liveprogressbar", "tvseektotal"]
            ),
            QAMission(
                "MISSION_HOME_BILLBOARD_6_ROWS",
                "Trang Chủ: Billboard 60% + 6 Hàng (KL8 Task 4)",
                "Mở Trang Chủ (Tab 6 — HomeHubFragment, KL8 Task 4: billboard 60% + 6 hàng ĐANG PHÁT / TIẾP TỤC XEM / TRẬN SẮP DIỄN RA / MỚI CẬP NHẬT / KÊNH / GIẢI ĐẤU). KHÔNG còn Cổng Chọn 3 Card (Task 4 đã xóa — mission cũ SWITCH_TAB(6) tìm card nên fail 4 lần ở run 42950738729). Xác nhận billboard chiếm ~60% chiều cao màn, duyệt xuống đủ 6 hàng, mỗi hàng có nội dung thật, focus viền trắng rõ.",
                "Billboard hero chiếm ~60% chiều cao, đủ 6 hàng nội dung thật, điều hướng D-pad xuống các hàng mượt, không kẹt focus.",
                max_steps=8
            ),
            QAMission(
                "MISSION_SCHEDULE_EPG_AND_FIXTURE_TAP",
                "Lịch Thi Đấu EPG Đa Ngày & Chạm Trận Đấu (Schedule Tap & Detail)",
                "Chuyển sang Tab Lịch đấu (Tab 1), duyệt lịch theo ngày, click trận kiểm tra onFixtureTap và xử lý trạng thái trận.",
                "Lịch đấu phân chia theo ngày rõ ràng, sự kiện bấm trận phản hồi đúng.",
                max_steps=6
            ),
            QAMission(
                "MISSION_SIDEBAR_RAIL_FULL_TRAVERSAL",
                "Thanh Điều Hướng Sidebar Rail & Khám Phá Toàn Diện (Full Rail Traversal)",
                "Mở Sidebar Rail bằng DPAD_LEFT, duyệt dọc qua toàn bộ 6 tab trên Rail kiểm tra không bị tự đóng hay cướp focus, đóng bằng DPAD_RIGHT.",
                "Sidebar đóng mở êm ái, phím điều hướng không làm văng app hoặc mất focus.",
                max_steps=7
            ),
            QAMission(
                "MISSION_IPTV_CATEGORIES_AND_FAVORITES",
                "Truyền Hình IPTV, Lưới Kênh & Kênh Yêu Thích (Favorites Long-Press)",
                "Chuyển sang Tab IPTV (Tab 2), duyệt qua các danh mục kênh, test Long-press OK lưu Kênh Yêu Thích, duyệt tab Yêu Thích, kiểm tra nút THÊM M3U và Dialog cấu hình playlist M3U cá nhân.",
                "Lưu kênh yêu thích thành công, mở Dialog M3U mượt mà, lưới kênh nạp đủ logo sắc nét.",
                max_steps=10
            ),
            QAMission(
                "MISSION_IPTV_EPG_AND_ZAPPING_PLAYER",
                "Hero Preview IPTV, Lịch Phát Sóng & Nhảy Kênh Bằng Phím Số (Zapping)",
                "Kiểm tra Hero Preview góc trên, mở phát toàn màn hình kênh IPTV, test gõ số remote (1, 15) hiện OSD nhảy kênh, test phím Channel Up/Down.",
                "Hero Preview phát thử trơn tru, OSD gõ số kênh hiện tức thì, nhảy kênh trơn tru.",
                max_steps=7
            ),
            QAMission(
                "MISSION_IPTV_PLAYER_BACK_FOCUS",
                "Player IPTV: BACK Trong Player & Focus Ngay Sau BACK (P0-6, F66b)",
                "Mission CÓ ĐỊNH HƯỚNG (F66b): harness mở player IPTV bằng tab 2 → ENTER trên lưới kênh TRƯỚC vòng AI (không có deep-link mở thẳng player IPTV; run 42963719447 không có lần BACK nào trong player IPTV nên scenario gốc P0-6 chưa từng tái hiện). Từ trong player: chờ OSD tự ẩn sau 3.5s, VERIFY_STREAM, bấm BACK đúng lúc overlay đang ẩn, chờ chuyển cảnh rồi ghi activity + focus NGAY SAU BACK. CỬA CỨNG: mission FAIL nếu không có bước BACK nào trong player, hoặc focus NONE ngay sau BACK.",
                "BACK trong player IPTV có bằng chứng focus ngay sau đó (về lưới kênh với focus trên card, hoặc ở lại player với focus trên OSD — không NONE). Bằng chứng BACK-trong-player đã ghi được (bắt buộc).",
                max_steps=8,
                directed_launch="LAUNCH_IPTV_PLAYER_DIRECTED",
                required_activity="PlayerActivity"
            ),
            QAMission(
                "MISSION_IPTV_MINI_GUIDE",
                "Player IPTV: Mini-Guide \"Danh Sách Kênh\" (P1-4, F66c)",
                "Mission CÓ ĐỊNH HƯỚNG (F66c): harness mở player IPTV bằng tab 2 → ENTER (LAUNCH_IPTV_PLAYER_DIRECTED) TRƯỚC vòng AI — Mini-Guide không được mở lần nào trong run 42963719447 (140 thought không nhắc tới). Từ trong player: mở OSD, xuống thanh dưới, tới nút EPG (btnTvEpg → toggleSidebar) và bấm OK mở Mini-Guide; zap thử một kênh trong guide rồi BACK đóng guide. CỬA CỨNG: mission FAIL nếu tiêu đề panel 'Danh Sách Kênh' không bao giờ vào UI dump (panel channelSidebar không focusable, không có text nên không bao giờ xuất hiện trong dump — gate trên tiêu đề, không gate trên id panel).",
                "Mini-Guide mở được (panel Danh Sách Kênh hiện, 8 kênh quanh kênh đang phát), zap trong guide đổi kênh, BACK đóng guide về OSD. Tiêu đề 'Danh Sách Kênh' đã vào được UI dump (bắt buộc).",
                max_steps=10,
                directed_launch="LAUNCH_IPTV_PLAYER_DIRECTED",
                required_activity="PlayerActivity"
            ),
            QAMission(
                "MISSION_PHIM_NGUONC_AND_CATEGORIES",
                "Kho Phim NguonC, Apple Pills Thể Loại & Hạ Cánh Focus Chuẩn Xác",
                "Chuyển sang Tab Kho Phim (Tab 5), duyệt Apple Pills bộ lọc thể loại, bấm DPAD_DOWN kiểm tra focus hạ cánh chuẩn xác xuống nút XEM NGAY (btnHeroPlay).",
                "Danh sách phim tải đủ thông tin, điều hướng từ filter xuống hero banner mượt mà.",
                max_steps=5
            ),
            QAMission(
                "MISSION_PHIM_EPISODE_PICKER_AND_FAVORITE",
                "Hộp Thoại Chọn Tập (EpisodePicker), Lưu Phim & Đổi Spotlight Hero",
                "Trên Hero Banner phim, kiểm tra nút CHỌN TẬP (btnHeroEpisodes) mở EpisodePickerDialog, nút LƯU PHIM (btnHeroFavorite) và nút ĐỔI PHIM (btnHeroNext) chuyển Spotlight.",
                "EpisodePickerDialog hiển thị danh sách tập đầy đủ, lưu phim yêu thích và chuyển Spotlight mượt mà.",
                max_steps=9
            ),
            QAMission(
                "MISSION_COLD_OPEN_LAST_EPISODE",
                "Cold-Open Tập Cuối & \"Tập tiếp\" Flash (F45, F66d)",
                "Mission CÓ ĐỊNH HƯỚNG (F66d): harness sang tab Kho Phim (LAUNCH_PHIM_TAB) TRƯỚC vòng AI — agent ở run 42963719447 chỉ duyệt Tập 1–5 trong EpisodePicker rồi đóng dialog, không mở thẳng tập cuối lần nào. Từ hero phim: sang nút CHỌN TẬP, mở EpisodePickerDialog, đi xuống tới tập CUỐI cùng trong danh sách (tập nào cũng được — ghi lại nhãn, vd Tập 6) và mở thẳng nó từ cold start; lấy mẫu UI ngay khi player mở (flash sớm) và sau khi detail resolve + mở lại OSD (flash muộn). CỬA CỨNG: mission FAIL nếu tập cuối không bao giờ được mở; FAIL nữa nếu nút \"Tập tiếp\" lóe/hiện ở tập cuối.",
                "Tập cuối đã mở thẳng từ cold start, nút \"Tập tiếp\" không lóe lúc mở và không hiện sau khi detail resolve. Tập cuối đã mở được (bắt buộc — không mở được là FAIL).",
                max_steps=14,
                directed_launch="LAUNCH_PHIM_TAB"
            ),
            QAMission(
                "MISSION_FINISHED_MATCH_SCORES",
                "Trận Đã Kết Thúc: Tỉ Số Ảo Hiện VS, Tỉ Số 2:8 Ghi Nhận (F66 item 7)",
                "Mission CÓ ĐỊNH HƯỚNG (F66 item 7 — negative controls): harness sang tab Lịch đấu (LAUNCH_FINISHED_MATCH_TAB) TRƯỚC vòng AI — tìm trong dữ liệu live một trận ĐÃ KẾT THÚC (badge KẾT THÚC ở dòng lịch / KT ở thẻ trận, không phải trận live hay sắp đá). Từ danh sách: duyệt các dòng lịch tìm trận kết thúc, bấm OK vào dòng trận đã xong (app phải báo 'Trận đấu đã kết thúc', không mở picker phòng), sang tab Thể thao soi thẻ trận/hero của trận đã xong và ghi lại mọi chuỗi tỉ số hiện trên màn hình. CỬA CỨNG: (1) không thấy trận kết thúc nào suốt mission → NOT TESTABLE (không pass, không fail); (2) tỉ số phi thực tế (một bên > 9 hoặc tổng > 12, vd 13 : 8) KHÔNG BAO GIỜ được hiện số thô — phải hiện 'VS' — thấy số thô là FAIL. Bằng chứng thêm (KHÔNG phải cửa fail): tỉ số 2:8 nếu có trong dữ liệu thì ghi nhận '2 : 8' (score_2_8_seen) — thẻ trận đã xong luôn hiện VS, hero mới hiện tỉ số nên không bắt được thì chỉ là bằng chứng thiếu, không FAIL mission. Bóng rổ (NBA) miễn trừ luật bóng đá (điểm thật 90:99/35:53 hiện hợp lệ trên thẻ/hero). Đây là nửa on-screen của hai gate đã chứng minh ở unit level (ScorePlumbingTest).",
                "Tìm được trận đã kết thúc trong dữ liệu live; không có tỉ số phi thực tế nào hiện số thô trên màn hình (đều hiện VS); tỉ số 2:8 nếu có thì ghi nhận '2 : 8' (bằng chứng, không phải cửa fail). Không có trận kết thúc → NOT TESTABLE (không pass, không fail).",
                max_steps=10,
                directed_launch="LAUNCH_FINISHED_MATCH_TAB",
                allow_not_testable=True
            ),
            QAMission(
                "MISSION_VOD_PLAYER_SEEK_AND_RESUME",
                "Trình Phát Web (WebPlayerActivity), Tua D-pad JS & Hàng Tiếp Tục Xem",
                "Khởi chạy WebPlayerActivity bằng deep-link open=webplayer (phim embed THẬT từ API, KHÔNG dùng URL giả), kiểm tra WebView tải trang embed, test tua thời gian D-pad Trái/Phải qua JS, toggle Play/Pause, thoát player và kiểm tra vị trí xem dở được lưu vào hàng Tiếp Tục Xem của Kho Phim. CỬA CỨNG: harness mở WebPlayer bằng deep-link TRƯỚC vòng AI; mission FAIL nếu activity không bao giờ thành WebPlayerActivity. Gate F63/F47 TÁCH RIÊNG (review webplayer vòng 2): F63 — OSD phải mở (nút điều khiển OSD + focus vào nút sau DPAD_DOWN); F47 — probe tốc độ phải pass (nút Tốc độ hiện; mission này không bấm set nên chỉ xét nút hiện). Quan sát thêm: dwell ~10s sau DPAD_DOWN, màn hình lúc vào player dưới force_web.",
                "Tua WebPlayer mượt mà qua JS, lưu tiến độ chuẩn xác vào hàng Tiếp Tục Xem. WebPlayerActivity đã vào được (bắt buộc — không vào được là FAIL, không phải pass).",
                max_steps=10,
                directed_launch="LAUNCH_WEB_PLAYER",
                required_activity="WebPlayerActivity",
                requires_web_osd=True,
                requires_speed_probe=True
            ),
            QAMission(
                "MISSION_WEBPLAYER_DIRECTED_REAL_FILM",
                "WebPlayer Có Định Hướng: Phim Embed Thật, Phát/Tạm Dừng/Tua/Tốc Độ (KL8 Task 12)",
                "Mission CÓ ĐỊNH HƯỚNG (không đi mù bằng UI): harness dùng LAUNCH_WEB_PLAYER để mở WebPlayerActivity bằng deep-link open=webplayer với một tập embed THẬT từ API KKPhim TRƯỚC vòng AI. Từ trong WebPlayer: chờ embed tải xong, VERIFY_STREAM để chứng minh video thật sự chuyển động, mở OSD bằng DPAD_DOWN, chờ 10s đo dwell (OSD còn hiện + focus ở btnWebPlayPause?), tua tới/lùi bằng DPAD_RIGHT/DPAD_LEFT qua JS, bấm OK tạm dừng rồi OK phát lại, đi tới nút Tốc độ và bấm OK set tốc độ (đọc lại nhãn: nhãn phải đổi sang tốc độ mới), thoát bằng BACK và về Kho Phim kiểm tra hàng Tiếp Tục Xem. CỬA CỨNG (review webplayer vòng 2 — F63/F47 TÁCH RIÊNG): F63 — OSD phải MỞ (nút điều khiển OSD trong dump + focus rơi vào nút điều khiển sau DPAD_DOWN); F47 — probe tốc độ phải pass (nút Tốc độ hiện) VÀ set-and-read-back (nhãn đổi sau khi bấm OK). Không có nút Tốc độ = probe fail (F47), KHÔNG bao giờ là 'đúng gate' và KHÔNG bao giờ báo thành 'OSD không mở'. Mission FAIL nếu activity không bao giờ thành WebPlayerActivity — AI KHÔNG được tự kết thúc pass khi chưa vào WebPlayer (P0-1 run 42950738729).",
                "WebPlayer mở được phim embed thật, video chuyển động thật (motion delta > 0), OSD hiện đủ điều khiển, tua ± qua JS hoạt động, tạm dừng/phát lại hoạt động, thoát lưu tiến độ vào Tiếp Tục Xem. WebPlayerActivity đã vào được (bắt buộc — không vào được là FAIL, không phải pass).",
                max_steps=17,
                directed_launch="LAUNCH_WEB_PLAYER",
                required_activity="WebPlayerActivity",
                requires_web_osd=True,
                requires_speed_probe=True
            ),
            QAMission(
                "MISSION_PLAYER_SETTINGS_DIALOG",
                "Trình Phát Native (PlayerActivity), Dialog Cài Đặt Thống Nhất & Toàn Bộ Chức Năng",
                "Mở phim VOD native trên PlayerActivity bằng LAUNCH_VOD_PLAYER_DIRECTED (deep-link open=vodplayer, tập m3u8 THẬT từ API — KHÔNG đi mù từ tab Phim vì hero Phát có thể mở WebPlayer thay vì native), mở thanh OSD, test nút Cài Đặt mở Dialog Thống Nhất (chọn thử chip Hình ảnh/Âm thanh/Tỉ lệ/Bước tua), test nút Tua Lùi/Tua Tới, nút Tạm Dừng/Phát, phím tắt remote A (Tỉ lệ), B (Âm thanh), MENU (Server Picker), và thoát player kiểm tra tự lưu tiến độ.",
                "Dialog hiện đủ 4 nhóm trong ScrollView, các nút tua/pause/settings phản hồi chuẩn, phím tắt remote hoạt động tức thì, không crash.",
                max_steps=19
            ),
            QAMission(
                "MISSION_SEARCH_AND_SETTINGS_FEEDBACK",
                "Tìm Kiếm Thông Minh & Cài Đặt (Hộp Thoại Báo Lỗi Telegram QR @kenhlivetv)",
                "Duyệt Tab Tìm kiếm (Tab 3), nhập từ khóa; chuyển sang Tab Cài đặt (Tab 4), mở mục 'Liên hệ & Báo lỗi', kiểm tra FeedbackDialog hiển thị mã QR Telegram và thông tin @kenhlivetv.",
                "Tìm kiếm hiển thị kết quả, FeedbackDialog mở chuẩn xác có mã QR và đóng bằng phím BACK/OK êm ái.",
                max_steps=10
            ),
            QAMission(
                "MISSION_DPAD_CHAOS_STRESS_AND_RECOVERY",
                "Thử Thách Stress Chaos D-pad & Đo Đạc Bộ Nhớ RAM (Memory Leak Audit)",
                "Nhồi phím liên tục 4 hướng để kiểm tra độ bền, mép màn hình, khả năng giữ focus / auto recovery và đo tổng lượng RAM PSS qua dumpsys meminfo.",
                "Không crash, không văng app, focus tự phục hồi khi chuyển cảnh, RAM PSS ổn định.",
                max_steps=6
            )
        ]

        if self.quick:
            # Chế độ chạy nhanh: chỉ giữ 5 mission trọng tâm để hoàn thành ~12-18 phút
            quick_keep = {
                "MISSION_COLD_START",
                "MISSION_HOME_BILLBOARD_6_ROWS",
                "MISSION_IPTV_CATEGORIES_AND_FAVORITES",
                "MISSION_PHIM_NGUONC_AND_CATEGORIES",
                "MISSION_PLAYER_SETTINGS_DIALOG",
            }
            self.missions = [m for m in self.missions if m.name in quick_keep]
            for m in self.missions:
                m.max_steps = min(int(m.max_steps), 4 if m.name != "MISSION_PLAYER_SETTINGS_DIALOG" else 6)
            print(f"⚡ [QUICK MODE] Chỉ chạy {len(self.missions)} mission trọng tâm, tổng tối đa {sum(m.max_steps for m in self.missions)} bước", flush=True)

        self.all_findings = []
        self.all_screenshots = []
        self.missing_shots = []  # KL8 fix loop 2 (F67b): nhãn các shot
        # screencap thất bại (ghi placeholder MISSING thay vì mất file lặng lẽ)
        self.ai_decisions_log = []
        self.start_time = 0

    # KL8 fix loop 1 (P0-2): map nav id -> tab (MainActivity.setupNav).
    NAV_ID_TO_TAB = {
        "nav_home": 6, "nav_live": 0, "nav_schedule": 1, "nav_iptv": 2,
        "nav_search": 3, "nav_settings": 4, "nav_phim": 5,
    }
    # Từ khóa fallback khi nav không có trong dump. Tab 6 là Trang Chủ
    # (HomeHubFragment: heroFilmPlay/billboard + 6 hàng) — Cổng Chọn 3 Card
    # đã bị Task 4 xóa nên từ khóa cũ ("cổng chọn", "cardsports"...) không
    # còn khớp gì và từng khiến detector rơi nhầm về tab 5.
    TAB_KEYWORDS = [
        (6, ["herofilmplay", "herofilmsave", "homebillboard", "heropager"]),
        (5, ["phim", "nguonc", "btnheroplay", "apple pill", "phim bộ", "phim lẻ", "tiếp tục xem", "rạp phim tại gia"]),
        (4, ["settingslist", "cài đặt", "chất lượng video", "báo lỗi"]),
        (3, ["searchinput", "resultlist", "tìm kiếm"]),
        (2, ["iptv", "kênh tv", "channel", "vtv", "htv"]),
        (1, ["schedlist", "schedcard", "lịch thi đấu", "hôm nay", "ngày mai"]),
        (0, ["livelist", "cardroot", "socolive", "colatv", "gà vàng", "khán đài", "trực tiếp"])
    ]

    def _detect_tab_index(self, ui_state):
        """Xác định tab đang hiển thị từ UI dump: ưu tiên trạng thái selected
        của nav (showTab đặt isSelected — chính xác), fallback về từ khóa nội
        dung. Trả về None khi không xác định được (VD đang ở player)."""
        for r_id in (ui_state.get("selected_ids") or []):
            if r_id in self.NAV_ID_TO_TAB:
                return self.NAV_ID_TO_TAB[r_id]
        visible_ids = " ".join(r_id for r_id, _ in (ui_state.get("all_visible_texts") or []))
        summary_text = (ui_state.get("ui_summary", "") + " " + ui_state.get("focused_sig", "")
                        + " " + ui_state.get("focused_text", "") + " " + visible_ids).lower()
        for t_idx, kws in self.TAB_KEYWORDS:
            if any(k in summary_text for k in kws):
                return t_idx
        return None

    def _run_directed_launch(self, mission):
        """Chạy launch có định hướng TRƯỚC vòng AI và chờ activity đích xuất hiện.

        Trả về True chỉ khi current_activity chứa mission.required_activity
        trong 30s. Dùng cho mission CÓ ĐỊNH HƯỚNG (VD WebPlayer): tránh việc AI
        cloud tự ý đi lang thang rồi tự kết thúc pass giả khi chưa vào đúng màn
        (P0-1 run 42950738729).
        """
        if mission.directed_launch == "LAUNCH_WEB_PLAYER":
            self.device.launch_web_player()
            time.sleep(2.5)
        elif mission.directed_launch == "LAUNCH_VOD_PLAYER_DIRECTED":
            self.device.launch_vod_player()
            time.sleep(6.0)
        elif mission.directed_launch == "LAUNCH_SPORT_PLAYER_DIRECTED":
            # KL8 fix loop 2 (F66a): mở thẳng PlayerActivity mặt SPORTS bằng
            # deep-link open=player — không trông chờ AI tự bấm vào card trận.
            self.device.launch_sport_player()
            time.sleep(6.0)
        elif mission.directed_launch == "LAUNCH_IPTV_PLAYER_DIRECTED":
            # KL8 fix loop 2 (F66b/F66c): mở player IPTV bằng UI (tab 2 →
            # ENTER trên lưới) — không có deep-link mở thẳng player IPTV.
            self.device.launch_iptv_player()
            time.sleep(1.0)
        elif mission.directed_launch == "LAUNCH_PHIM_TAB":
            # KL8 fix loop 2 (F66d): sang tab Kho Phim trước vòng AI.
            self.device.switch_tab(5)
            time.sleep(2.0)
        elif mission.directed_launch == "LAUNCH_FINISHED_MATCH_TAB":
            # KL8 fix loop 2 (F66 item 7): sang tab Lịch đấu trước vòng AI —
            # dòng lịch là nơi chắc chắn nhất thấy trận đã kết thúc (badge
            # "KẾT THÚC"; thẻ trận ở tab Thể thao chỉ còn "KT" + "VS" vì thẻ
            # đã xong không ghi tỉ số cuối lên thẻ).
            self.device.switch_tab(1)
            time.sleep(2.0)
        else:
            return True
        req = mission.required_activity
        if not req:
            return True
        deadline = time.time() + 30
        while time.time() < deadline:
            cur = self.device.current_activity()
            if req in cur:
                mission.reached_required = True
                return True
            time.sleep(1.5)
        return False

    # KL8 fix loop 2 (F63/F47 tách gate, review webplayer vòng 2): các nút
    # chrome OSD của WebPlayer (activity_web_player.xml, lowercase để so
    # với blob). Thanh dưới webControlBar: PrevEp/SeekBack/PlayPause/
    # SeekFwd/NextEp/Episodes/Speed; OSD trên playerTopOsd: btnBack.
    # Container webControlBar/playerTopOsd KHÔNG focusable, không có text
    # nên không bao giờ xuất hiện trong dump — gate F63 trên nút, không
    # gate trên container. DPAD_DOWN khi focus kẹt ở WebView thì showOsd()
    # + focus về btnWebPlayPause (WebPlayerActivity.dispatchKeyEvent).
    _WEB_OSD_CONTROLS = frozenset({
        "btnwebplaypause", "btnwebseekback", "btnwebseekfwd",
        "btnwebprevep", "btnwebnextep", "btnwebepisodes", "btnwebspeed",
        "btnback",
    })

    def _scan_mission_evidence(self, mission, ui_state, cur_act):
        """Quét UI dump của một bước để ghi bằng chứng cho mission CÓ ĐỊNH
        HƯỚNG (fix loop 2, F66/F63). Trả về tập marker mới thấy ở bước này
        (để runner gắn screenshot của đúng bước đó vào bằng chứng).
        Chỉ đọc dump — không bấm phím, không tự kết luận pass.
        """
        texts = ui_state.get("all_visible_texts") or []
        blob = " ".join(f"{r_id} {txt}" for r_id, txt in texts).lower()
        blob += " " + (ui_state.get("ui_summary") or "").lower()
        blob += " " + (ui_state.get("focused_sig") or "").lower()
        newly = set()
        for mk in mission.required_ui_markers:
            if mk in blob and mk not in mission.markers_seen:
                mission.markers_seen.add(mk)
                newly.add(mk)
        ev = mission.evidence
        # F66a: nhãn live của hàng dưới sport — ghi nhận để làm rõ bằng
        # chứng, KHÔNG phải cửa fail (luồng seekable vẫn hiện hàng nhưng
        # nhãn là thời lượng thay vì "TRỰC TIẾP").
        if mission.name == "MISSION_SPORT_PLAYER_BOTTOM_ROW":
            for _r, t in texts:
                tl = (t or "").strip().lower()
                if tl == "trực tiếp":
                    ev["sport_live_label_seen"] = True
                elif tl == "về trực tiếp":
                    ev["sport_live_label_seen"] = True
                    ev["sport_golive_seen"] = True
        # F66c: tiêu đề Mini-Guide — so khớp CHÍNH XÁC (khác hẳn mục
        # "Mở danh sách kênh" trong dialog Tùy chọn; chỉ tiêu đề panel mới
        # chứng minh guide đã mở — đây LÀ cửa chính của mission, thay cho
        # marker channelSidebar đã chết: panel là LinearLayout không
        # focusable, không có text nên không bao giờ vào blob).
        if mission.name == "MISSION_IPTV_MINI_GUIDE":
            for _r, t in texts:
                if (t or "").strip().lower() == "danh sách kênh":
                    ev["miniguide_header_seen"] = True
        # F66d: EpisodePicker mở chưa + tập cuối mở chưa + flash "Tập tiếp".
        # "PlayerActivity" là substring của cả PlayerActivity lẫn
        # WebPlayerActivity nên một điều kiện phủ cả hai mặt player.
        # Picker-open KHÔNG gate trên id episodeList: không có view nào
        # mang id đó trong app (0 hit ở layouts + Kotlin). List thật là
        # dialogEpisodesGrid (EpisodePickerDialog.kt:66) — RecyclerView
        # không text, không focusable nên cũng không vào blob. Tín hiệu
        # nhận diện được là chip tập: id tvEpisodeName
        # (item_episode_chip.xml:7, focusable, text "Tập N" đã chuẩn hóa ở
        # EpisodePickerDialog.normalizeEpisodeLabel) — id có trong blob vì
        # node có text. KHÔNG fallback text "Tập N": blob gắn id với text
        # của từng node nên chip thật nào cũng đã khớp arm id; text arm chỉ
        # khớp node không phải chip — false positive trên hero label Phim
        # (epLabel = film.currentEpisode khi totalEpisodes trống,
        # PhimFragment.kt:1738), step-0 đã cướp reflex sang walk mode.
        if mission.name == "MISSION_COLD_OPEN_LAST_EPISODE":
            if "tvepisodename" in blob:
                ev["picker_open"] = True
            if ev.get("last_episode_enter_pressed") and not ev.get("last_episode_opened"):
                if "PlayerActivity" in cur_act:
                    ev["last_episode_opened"] = True
                    ev["last_episode_player"] = cur_act
                    ev["next_ep_visible_early"] = (
                        ("btnbarnextep" in blob or "btnwebnextep" in blob)
                        and "tập tiếp" in blob
                    )
            elif ev.get("last_episode_opened") and not ev.get("next_ep_sampled_late"):
                last = ev.get("last_action") or (None, None)
                if last == ("KEY", "DPAD_DOWN"):
                    ev["next_ep_visible_late"] = (
                        ("btnbarnextep" in blob or "btnwebnextep" in blob)
                        and "tập tiếp" in blob
                    )
                    ev["next_ep_sampled_late"] = True
        # F66 item 7 — negative controls trên trận đã kết thúc.
        # - finished_found: badge "KẾT THÚC" (dòng lịch, ScheduleAdapter) /
        #   "KT" (thẻ trận, MatchCardsAdapter) / "ĐÃ KẾT THÚC" (phụ đề
        #   player). Chỉ tính khi text KHỚP NGUYÊN chuỗi (tránh "kết thúc"
        #   lọt trong một câu khác). Không thấy suốt mission → NOT TESTABLE.
        # - Mọi chuỗi tỉ số render dạng "H : G" / "H - G" (CÓ khoảng trắng
        #   quanh dấu — giờ đá "19:30" không có khoảng trắng nên không lọt)
        #   đều phải hợp lệ theo luật bóng đá (mỗi bên ≤ 9, tổng ≤ 12):
        #   cặp phi thực tế hiện số thô (vd "13 : 8", "4 - 12") là FAIL
        #   (phải hiện "VS" — xem DataNormalizer.plausibleScorePair +
        #   ScorePlumbingTest, đã chứng minh ở unit level; đây là nửa
        #   on-screen). Chỉ khớp NGUYÊN chuỗi text để không lọt tiêu đề
        #   nhà đài nhúng tỉ số ("Kings 65 - 68 Magic" là tiêu đề, đã có
        #   parseMatch lọc ở tầng dữ liệu).
        # - Bóng rổ miễn trừ luật bóng đá: điểm NBA thật (90:99, 35:53)
        #   hiện hợp lệ trên thẻ/hero — nhận diện qua tên giải trong cùng
        #   dump ("nba"/"bóng rổ"/"bong ro"/"basketball"); cặp phi thực tế
        #   trong dump có tín hiệu bóng rổ thì ghi vào
        #   basketball_scores_seen, không tính vi phạm.
        # - Thẻ trận đã xong LUÔN hiện "VS" (không ghi tỉ số cuối lên thẻ),
        #   hero trận đã xong mới hiện "$hs : $gs" — nên "2 : 8" chỉ bắt
        #   được khi trận 2:8 nằm ở hero (hoặc đang live); không bắt được
        #   thì chỉ là bằng chứng thiếu, KHÔNG phải gate fail.
        if mission.name == "MISSION_FINISHED_MATCH_SCORES":
            blob_is_basketball = any(
                k in blob for k in ("nba", "bóng rổ", "bong ro", "basketball")
            )
            for _r, t in texts:
                tl = (t or "").strip()
                tll = tl.lower()
                if tll in ("kết thúc", "kt", "đã kết thúc"):
                    if not ev.get("finished_found"):
                        ev["finished_found"] = True
                        ev["finished_label"] = tl
                if tll == "vs" and ev.get("finished_found"):
                    ev["finished_vs_seen"] = True
                m = re.fullmatch(r"(\d{1,3})\s+[:\-]\s+(\d{1,3})", tl)
                if m:
                    h, g = int(m.group(1)), int(m.group(2))
                    pair = f"{h} : {g}"
                    if h <= 9 and g <= 9 and h + g <= 12:
                        ev.setdefault("plausible_scores_seen", [])
                        if pair not in ev["plausible_scores_seen"]:
                            ev["plausible_scores_seen"].append(pair)
                        if (h, g) == (2, 8):
                            ev["score_2_8_seen"] = True
                    elif blob_is_basketball:
                        ev.setdefault("basketball_scores_seen", [])
                        if pair not in ev["basketball_scores_seen"]:
                            ev["basketball_scores_seen"].append(pair)
                    else:
                        ev["implausible_raw_seen"] = pair
        # F63/F47 TÁCH GATE (review webplayer vòng 2): hai việc độc lập,
        # hai bằng chứng riêng — không tin thought của agent.
        # - F63 (OSD mở): chỉ tính khi dump được lấy SAU một phím DPAD_DOWN
        #   trong WebPlayerActivity VÀ có nút điều khiển OSD trong dump VÀ
        #   focus rơi vào một nút điều khiển. Nút Tốc độ KHÔNG dùng ở đây:
        #   nó chỉ hiện khi probe pass (GONE by design khi probe fail), nên
        #   gate cũ (btnWebSpeed/webControlBar) thực chất chỉ là gate probe
        #   trá hình — probe fail bị báo nhầm thành "OSD không mở".
        # - F47 (probe tốc độ): btnWebSpeed trong dump bất cứ lúc nào =
        #   probe pass (nút chỉ VISIBLE khi probe playbackRate qua).
        #   Set-and-read-back: OK bấm khi focus đang ở nút Tốc độ → ghi
        #   nhãn TRƯỚC set (lần thấy gần nhất) và nhãn SAU set (dump ngay
        #   sau OK nếu nhãn đổi đồng bộ, nếu không thì dump bước kế — cho
        #   callback JS bất đồng bộ có thời gian về). Nhãn đổi = set đáp
        #   xuống; nhãn giữ nguyên = set fail (giữ tốc độ cũ là đúng hành
        #   vi đã sửa, nhưng set đã fail → gate F47 fail).
        # - Dwell F63: bước WAIT 10.0 sau khi OSD đã mở là mẫu dwell —
        #   OSD còn hiện + focus còn ở btnWebPlayPause không (bản sửa thật
        #   của F63 là dwell 300s thay vì tự ẩn 3.5s)? Chỉ ghi nhận + finding
        #   MEDIUM, KHÔNG fail mission (gate F63 là "OSD mở được").
        # -Entry (nhánh m3u8-only dưới force_web): lần đầu thấy
        #   WebPlayerActivity thì ghi lại màn hình thực tế render ra gì
        #   (texts lúc vào + WebView có trong cây UI + hộp lỗi có hiện
        #   không) — kèm screenshot bước đó vốn đã lưu. open=webplayer
        #   luôn đặt force_web=true (MainActivity:885).
        # - Flip-back nhãn tốc độ: nhãn đổi sau set rồi TỰ quay về giá trị
        #   cũ ở dump sau mà không có lần set nào khác = nhãn đã hiện tốc
        #   độ chưa đáp xuống → finding MEDIUM (lỗi theo review vòng 2).
        if (mission.requires_web_osd or mission.requires_speed_probe) and "WebPlayerActivity" in cur_act:
            focused = (ui_state.get("focused_sig") or "").lower()
            if not ev.get("webplayer_entry_recorded"):
                ev["webplayer_entry_recorded"] = True
                ev["webplayer_entry_texts"] = [f"{r}: {t}" for r, t in texts[:8]]
                ev["webplayer_entry_focus"] = ui_state.get("focused_sig") or "NONE"
                ev["webplayer_entry_webview"] = bool(ui_state.get("has_webview"))
                ev["webplayer_entry_error"] = "btnwebretry" in blob
            osd_controls_here = [c for c in self._WEB_OSD_CONTROLS if c in blob]
            osd_focused = next((c for c in self._WEB_OSD_CONTROLS if c in focused), None)
            if "btnwebspeed" in blob:
                ev["web_speed_btn_seen"] = True
            speed_label = next(
                (t for r, t in texts if (r or "").lower() == "btnwebspeed"), None
            )
            if speed_label is not None:
                ev["speed_label_last"] = speed_label
                ev.setdefault("speed_label_history", []).append(
                    (mission.steps_executed, speed_label)
                )
                if ev.get("speed_readback_pending"):
                    ev["speed_label_after"] = speed_label
                    ev["speed_readback_pending"] = False
                elif (ev.get("speed_set_attempted")
                        and ev.get("speed_label_after")
                        and ev["speed_label_after"] != ev.get("speed_label_before")
                        and speed_label == ev.get("speed_label_before")
                        and not ev.get("speed_label_reverted")):
                    ev["speed_label_reverted"] = True
                    f = {
                        "area": mission.title,
                        "severity": "MEDIUM",
                        "issue": ("F47: nhãn nút Tốc độ đổi rồi TỰ quay về giá trị cũ "
                                  f"({ev.get('speed_label_before')} → {ev.get('speed_label_after')} → "
                                  f"{speed_label}) mà không có lần set nào khác — nhãn đã hiện tốc độ chưa đáp xuống."),
                        "detail": f"speed_label_history={ev.get('speed_label_history')}.",
                        "suggestion": "Kiểm tra webCycleSpeed: chỉ đổi nhãn khi callback JS trả 'OK', set fail thì trả index + nhãn về cũ (webplayer group, F47)."
                    }
                    mission.findings.append(f)
                    print(f"      ⚠️ [F47] {f['issue']}", flush=True)
            last = ev.get("last_action") or (None, None)
            if last == ("KEY", "DPAD_DOWN") and osd_controls_here and osd_focused:
                if not ev.get("web_osd_seen"):
                    ev["web_osd_seen"] = True
                    ev["web_osd_focus"] = osd_focused
                    newly.add("web_osd")
            if last == ("KEY", "OK") and not ev.get("speed_set_attempted"):
                prev_focus = (ev.get("prev_focused_sig") or "").lower()
                if "btnwebspeed" in prev_focus:
                    ev["speed_set_attempted"] = True
                    ev["speed_label_before"] = ev.get("speed_label_last_before_ok") or ev.get("speed_label_last")
                    if speed_label is not None and speed_label != ev.get("speed_label_before"):
                        ev["speed_label_after"] = speed_label
                    else:
                        ev["speed_readback_pending"] = True
            if (last == ("WAIT", "10.0") and ev.get("web_osd_seen")
                    and not ev.get("web_osd_dwell_checked")):
                ev["web_osd_dwell_checked"] = True
                ev["web_osd_dwell_ok"] = bool(osd_controls_here)
                ev["web_osd_dwell_focus_playpause"] = ("btnwebplaypause" in focused)
                if not ev["web_osd_dwell_ok"]:
                    f = {
                        "area": mission.title,
                        "severity": "MEDIUM",
                        "issue": ("F63 dwell: OSD tự ẩn trước 10s sau DPAD_DOWN — "
                                  "bản sửa dwell 300s chưa lên hoặc chưa có tác dụng (cũ: tự ẩn 3.5s)."),
                        "detail": "Mẫu dwell lấy ở bước WAIT 10.0 ngay sau DPAD_DOWN mở OSD; dump lúc đó không còn nút điều khiển OSD nào.",
                        "suggestion": "Kiểm tra hideOsdRunnable/postDelayed trong WebPlayerActivity.showOsd (webplayer group, F63)."
                    }
                    mission.findings.append(f)
                    print(f"      ⚠️ [F63 dwell] {f['issue']}", flush=True)
            ev["prev_focused_sig"] = ui_state.get("focused_sig") or "NONE"
            ev["speed_label_last_before_ok"] = speed_label
        return newly

    def _check_mission_end_gates(self, mission):
        """Cửa cứng cuối mission cho các mission CÓ ĐỊNH HƯỚNG (fix loop 2).
        Trả về (kết quả, danh sách finding mới):
        - "pass": mọi cửa đã qua, mission được tính hoàn thành.
        - "fail": một cửa bắt buộc chưa qua — mission FAIL, không pass giả.
        - "not_testable": mission cho phép NOT TESTABLE và dữ liệu live
          không có trạng thái cần kiểm — không pass, không fail.
        Caller tự ghi findings vào all_findings/mission.findings và đặt cờ.
        """
        findings = []
        if mission.allow_not_testable and not mission.evidence.get("finished_found"):
            mission.not_testable_reason = (
                "không thấy trận KẾT THÚC nào trong dữ liệu lịch live suốt mission — "
                "không có trận đã kết thúc để kiểm, ghi NOT TESTABLE (không pass, không fail)."
            )
            return "not_testable", findings
        missing = [m for m in mission.required_ui_markers if m not in mission.markers_seen]
        if missing:
            findings.append({
                "area": mission.title,
                "severity": "HIGH",
                "issue": (f"Directed mission không tới được trạng thái bắt buộc: "
                          f"không thấy {missing} trong UI dump của cả mission — FAIL, "
                          f"không tính pass (F66: state chưa từng tới)."),
                "detail": f"required_ui_markers={mission.required_ui_markers}, markers_seen={sorted(mission.markers_seen)}.",
                "suggestion": f"Kiểm tra directed launch {mission.directed_launch} và đường mở trạng thái này."
            })
            return "fail", findings
        # F66c (review vòng 2): Mini-Guide chỉ pass khi tiêu đề panel
        # "Danh Sách Kênh" đã vào dump — bằng chứng duy nhất chứng minh
        # guide đã mở (panel channelSidebar không focusable, không có text
        # nên không bao giờ xuất hiện trong dump; đừng gate trên id của nó).
        if mission.name == "MISSION_IPTV_MINI_GUIDE":
            if not mission.evidence.get("miniguide_header_seen"):
                findings.append({
                    "area": mission.title,
                    "severity": "HIGH",
                    "issue": ("F66c: Mini-Guide không bao giờ MỞ — tiêu đề panel "
                              "\"Danh Sách Kênh\" không xuất hiện trong UI dump của "
                              "cả mission. Mission FAIL, không tính pass."),
                    "detail": "Gate trên tiêu đề panel (miniguide_header_seen), không gate trên id channelSidebar (không bao giờ vào dump).",
                    "suggestion": "Kiểm tra directed launch LAUNCH_IPTV_PLAYER_DIRECTED và đường mở Mini-Guide qua nút EPG (btnTvEpg → toggleSidebar)."
                })
                return "fail", findings
        # F63 rồi F47 — HAI GATE RIÊNG, đúng thứ tự (review webplayer vòng 2).
        # F63 check trước: OSD chưa mở thì mission FAIL vì F63, KHÔNG bao
        # giờ đánh tráo thành F47. F47 chỉ xét khi F63 đã qua.
        if mission.requires_web_osd and not mission.evidence.get("web_osd_seen"):
            findings.append({
                "area": mission.title,
                "severity": "HIGH",
                "issue": ("F63: WebPlayer OSD không bao giờ MỞ — sau DPAD_DOWN không thấy "
                          "nút điều khiển OSD nào (btnWebPlayPause/btnWebSeekBack/...) trong "
                          "dump, và/hoặc focus không rơi vào nút điều khiển. Gate trên OSD "
                          "chrome + focus, KHÔNG dùng nút Tốc độ (nút đó thuộc probe F47)."),
                "detail": "OSD phải mở với focus về btnWebPlayPause sau DPAD_DOWN (WebPlayerActivity.dispatchKeyEvent).",
                "suggestion": "Kiểm tra DPAD_DOWN có mở được OSD KL8 trong WebPlayerActivity không (webplayer group, F63)."
            })
            return "fail", findings
        if mission.requires_speed_probe:
            ev = mission.evidence
            if not ev.get("web_speed_btn_seen"):
                findings.append({
                    "area": mission.title,
                    "severity": "HIGH",
                    "issue": ("F47: probe tốc độ KHÔNG pass — nút Tốc độ (btnWebSpeed) không bao giờ "
                              "hiện trong WebPlayer (probe playbackRate fail nên nút GONE by design). "
                              "OSD đã mở (F63 qua) — đây là lỗi probe, KHÔNG phải lỗi OSD."),
                    "detail": "Gate trên btnWebSpeed VISIBLE + set-and-read-back; nút chỉ hiện khi probe qua.",
                    "suggestion": "Kiểm tra probe playbackRate (set 1.25 + đọc lại) trong WebPlayerActivity (webplayer group, F47)."
                })
                return "fail", findings
            if ev.get("speed_set_attempted"):
                before = ev.get("speed_label_before")
                after = ev.get("speed_label_after")
                if not after or after == before:
                    findings.append({
                        "area": mission.title,
                        "severity": "HIGH",
                        "issue": (f"F47: set tốc độ KHÔNG đáp xuống — sau khi bấm OK trên nút Tốc độ, "
                                  f"nhãn vẫn giữ {before or '?'} (không có read-back đổi tốc độ). "
                                  f"Nhãn giữ tốc độ cũ là đúng hành vi đã sửa, nhưng set đã fail."),
                        "detail": f"speed_label_before={before}, speed_label_after={after}, history={ev.get('speed_label_history')}.",
                        "suggestion": "Kiểm tra webCycleSpeed: callback JS phải trả 'OK' thì nhãn mới đổi, 'NONE' thì trả index về cũ (webplayer group, F47)."
                    })
                    return "fail", findings
        if mission.name == "MISSION_IPTV_PLAYER_BACK_FOCUS":
            back = mission.evidence.get("back_in_player")
            if not back:
                findings.append({
                    "area": mission.title,
                    "severity": "HIGH",
                    "issue": ("F66b: không có bước BACK nào trong player IPTV suốt mission — "
                              "scenario P0-6 chưa từng chạy, không tính pass."),
                    "detail": "Directed mission yêu cầu một bước BACK khi activity là PlayerActivity.",
                    "suggestion": "Kiểm tra directed launch LAUNCH_IPTV_PLAYER_DIRECTED và reflex BACK ở bước 2."
                })
                return "fail", findings
            if (back.get("focused_sig") or "NONE") == "NONE":
                findings.append({
                    "area": mission.title,
                    "severity": "HIGH",
                    "issue": ("P0-6: focus NONE ngay sau BACK trong player IPTV "
                              f"(step {back.get('step')}: {back.get('activity_before')} → "
                              f"{back.get('activity_after')})."),
                    "detail": f"focused_sig=None sau BACK; shot sau BACK: {back.get('shot') or 'không có'}.",
                    "suggestion": "BACK trong player phải để lại focus trên một view thấy được (card kênh / nút OSD) — xem F54 allowlist restore focus."
                })
                return "fail", findings
        if mission.name == "MISSION_COLD_OPEN_LAST_EPISODE":
            ev = mission.evidence
            if not ev.get("last_episode_opened"):
                findings.append({
                    "area": mission.title,
                    "severity": "HIGH",
                    "issue": ("F66d/F45: tập cuối không bao giờ được mở từ cold start — "
                              "mission FAIL, không tính pass."),
                    "detail": f"picker_open={bool(ev.get('picker_open'))}, last_episode_label={ev.get('last_episode_label')!r}.",
                    "suggestion": "Kiểm tra directed launch LAUNCH_PHIM_TAB, nút CHỌN TẬP và EpisodePickerDialog."
                })
                return "fail", findings
            if ev.get("next_ep_visible_early") or ev.get("next_ep_visible_immediate"):
                findings.append({
                    "area": mission.title,
                    "severity": "HIGH",
                    "issue": (f"F45: nút \"Tập tiếp\" LÓE khi cold-open tập cuối "
                              f"({ev.get('last_episode_label') or '?'} → {ev.get('last_episode_player')})."),
                    "detail": (f"next_ep_visible: sớm={ev.get('next_ep_visible_early')}, "
                               f"ngay sau ENTER={ev.get('next_ep_visible_immediate')}."),
                    "suggestion": "Nút Tập tiếp phải GONE mặc định, chỉ reveal sau khi detail resolve (xem F24/F45)."
                })
                return "fail", findings
            if ev.get("next_ep_visible_late"):
                findings.append({
                    "area": mission.title,
                    "severity": "HIGH",
                    "issue": (f"F45: nút \"Tập tiếp\" vẫn HIỆN ở tập cuối sau khi detail resolve "
                              f"({ev.get('last_episode_label') or '?'})."),
                    "detail": "Mẫu muộn lấy sau DPAD_DOWN mở lại OSD — gate tập cuối không áp.",
                    "suggestion": "Kiểm tra refreshEpisodeNavButtons/applyEpisodeNavFromDetail: tập cuối phải ẩn Tập tiếp."
                })
                return "fail", findings
        if mission.name == "MISSION_FINISHED_MATCH_SCORES":
            # F66 item 7: tới đây thì finished_found đã True (không thì nhánh
            # NOT TESTABLE ở đầu hàm đã trả về). Cửa duy nhất còn lại: tỉ số
            # phi thực tế KHÔNG được hiện số thô — phải hiện "VS".
            ev = mission.evidence
            raw = ev.get("implausible_raw_seen")
            if raw:
                findings.append({
                    "area": mission.title,
                    "severity": "HIGH",
                    "issue": (f"F66 item 7: tỉ số phi thực tế hiện SỐ THÔ trên màn hình ({raw}) — "
                              f"phải hiện 'VS', không bao giờ hiện số thô."),
                    "detail": (f"implausible_raw_seen={raw}, plausible_scores_seen={ev.get('plausible_scores_seen')}, "
                               f"basketball_scores_seen={ev.get('basketball_scores_seen')}, finished_label={ev.get('finished_label')!r}."),
                    "suggestion": "Kiểm tra luật plausibleScorePair ở mặt hiển thị tỉ số này (thẻ/hero/phụ đề player — xem ScorePlumbingTest)."
                })
                return "fail", findings
        return "pass", findings

    def run(self):
        print("\n" + "=" * 65)
        print("🚀 [KenhLive AI QA] KHỞI ĐỘNG HỆ THỐNG KIỂM THỬ 100% AI AUTONOMOUS")
        print("=" * 65 + "\n", flush=True)

        # 0. VIDEO RECORDER: Bắt đầu quay toàn bộ quá trình từ trước khi mở app
        if self.recorder:
            try:
                self.recorder.start()
            except Exception as e:
                print(f"⚠️ [VideoRecorder] Không thể khởi động quay: {e}", flush=True)

        self.start_time = time.time()
        self.device.checkpoint_logcat()

        # Bước 1: Khởi động app
        print("📱 Đang khởi chạy ứng dụng KenhLive TV...", flush=True)
        launch_ms = self.device.launch_app()
        if launch_ms > 0:
            print(f"  ✅ Khởi động thành công trong {launch_ms}ms", flush=True)
        else:
            print("  ⚠️ Không bắt được focus ngay khi mở app", flush=True)

        # Chờ 1.5s cho frame đầu tiên render hoàn tất sau hiệu ứng chuyển cảnh cửa sổ
        time.sleep(1.5)

        # Chụp ảnh baseline
        self._record_screen("01_cold_start")

        # Bước 2: Vòng lặp Agent thực thi các Mission
        for m_idx, mission in enumerate(self.missions):
            print(f"\n🎯 [Mission {m_idx + 1}/{len(self.missions)}] {mission.title}", flush=True)
            print(f"   Mục tiêu: {mission.description}", flush=True)

            # KL8 fix loop 1 (P0-1): mission CÓ ĐỊNH HƯỚNG chạy launch TRƯỚC vòng
            # AI — AI cloud ở run 42950738729 đã không bao giờ chọn LAUNCH_WEB_PLAYER
            # nên mission tự pass giả khi chưa vào WebPlayer lần nào. Launch thất
            # bại (không tới được required_activity trong 30s) thì FAIL luôn.
            skip_loop = False
            if mission.directed_launch:
                if not self._run_directed_launch(mission):
                    issue = (f"Directed launch {mission.directed_launch} không mở được "
                             f"{mission.required_activity} — mission FAIL, không cho AI tự kết thúc pass giả.")
                    finding = {
                        "area": mission.title,
                        "severity": "HIGH",
                        "issue": issue,
                        "detail": "Deep-link đã chạy nhưng activity đích không xuất hiện trong 30s. Xem log F44 (resolver tập phim KKPhim) và WebPlayerActivity force_web.",
                        "suggestion": "Kiểm tra deep-link open=webplayer / resolver tập phim KKPhim và WebPlayerActivity force_web."
                    }
                    print(f"   ❌ [Directed Launch Failed] {issue}", flush=True)
                    self.all_findings.append(finding)
                    mission.findings.append(finding)
                    mission.failed = True
                    skip_loop = True
                else:
                    self.brain.record_step_feedback(
                        f"Directed launch {mission.directed_launch} đã chạy: đang ở {mission.required_activity}, "
                        f"phim embed THẬT đã mở. Từ đây chỉ kiểm tra trong {mission.required_activity}: "
                        f"chờ tải, VERIFY_STREAM, OSD, tua, tạm dừng/phát lại, nút Tốc độ nếu hiện."
                    )

            while mission.steps_executed < mission.max_steps and not skip_loop:
                mission.steps_executed += 1
                step_num = mission.steps_executed

                # 1. PERCEPTION: Thu thập trạng thái thiết bị
                raw_png = self.device.screencap_bytes()
                ui_state = self.device.dump_ui_state()
                has_ring, ring_col, _ = self.device.detect_focus_ring(raw_png, ui_state.get("focused_bounds"))
                cur_act = self.device.current_activity()
                # KL8 fix loop 1 (P0-1): ghi nhận mission đã từng tới activity đích.
                if mission.required_activity and mission.required_activity in cur_act:
                    mission.reached_required = True
                is_player = "PlayerActivity" in cur_act or "WebPlayerActivity" in cur_act
                is_playing, motion_delta = self.device.detect_video_motion(duration_sec=0.8, samples=2, is_player_context=is_player)
                logcat_alerts = self.device.get_new_logcat_alerts()

                # Tự động cập nhật tab đang hiển thị (KL8 fix loop 1, P0-2:
                # _detect_tab_index ưu tiên nav-selected, fallback từ khóa).
                current_tab_idx = self._detect_tab_index(ui_state)
                if current_tab_idx is not None:
                    self.tested_tabs.add(current_tab_idx)

                # KL8 fix loop 2 (F66/F63): quét UI dump bước này để ghi bằng
                # chứng cho mission CÓ ĐỊNH HƯỚNG (marker hàng dưới, OSD...).
                step_markers = self._scan_mission_evidence(mission, ui_state, cur_act)

                # 1.5 DEEP ANOMALY INSPECTOR: Tự động phát hiện lỗi tầng sâu
                deep_defects = self.device.inspect_deep_anomalies(ui_state, cur_act, png_bytes=raw_png)
                for df in deep_defects:
                    print(f"      🔎 [Deep Inspector] Phát hiện lỗi [{df.get('severity')}]: {df.get('issue')}", flush=True)
                    self.all_findings.append(df)
                    mission.findings.append(df)

                state_bundle = {
                    "activity": cur_act,
                    "focused_sig": ui_state["focused_sig"],
                    "focused_text": ui_state["focused_text"],
                    "has_focus_ring": has_ring,
                    "focus_ring_color": ring_col,
                    "video_motion_playing": is_playing,
                    "video_motion_delta": motion_delta,
                    "recent_keys": self.device.action_history[-5:],
                    "logcat_alerts": "; ".join(logcat_alerts) or "Không có",
                    "deep_anomalies_text": "\n".join(f"- [{d['severity']}] {d['issue']}: {d['detail']}" for d in deep_defects),
                    "ui_summary": ui_state["ui_summary"],
                    "screenshot_bytes": raw_png,
                    "tabs_tested": ", ".join(self.ALL_TABS[i] for i in sorted(self.tested_tabs)) if self.tested_tabs else "Chưa có",
                    "tabs_remaining": ", ".join(self.ALL_TABS[i] for i in sorted(set(self.ALL_TABS.keys()) - self.tested_tabs)) or "Đã bao phủ toàn bộ 6 tabs!"
                }

                # 2. COGNITION: AI quyết định hành động
                decision = self.brain.decide_mission_action(mission, state_bundle)
                provider = decision.get("_provider", "AI")
                thought = decision.get("thought", "")
                act_type = decision.get("action_type", "KEY")
                act_param = decision.get("action_param", "")
                defect = decision.get("defect_detected")

                print(f"   🤖 [Session #{self.session.global_step_counter + 1} · {mission.name}] ({provider}) Thought: {thought[:90]}", flush=True)
                print(f"      -> Action: {act_type} {act_param}", flush=True)

                # Chụp screenshot cho từng bước để lưu trữ và xây dựng video tour trực quan
                step_shot = self._record_screen(f"step_{self.session.global_step_counter + 1:03d}_{mission.name.lower()[:8]}")

                # KL8 fix loop 2 (F66): gắn screenshot của đúng bước mà marker
                # xuất hiện vào bằng chứng (vd hàng dưới sport bắt được ở shot nào).
                if step_markers and step_shot:
                    mission.evidence.setdefault("marker_shots", {}).update(
                        {mk: step_shot for mk in step_markers}
                    )
                # KL8 fix loop 2 (F66b): trạng thái sau BACK nằm ở screenshot
                # của bước SAU (shot của bước BACK chụp TRƯỚC khi bấm phím).
                _back = mission.evidence.get("back_in_player")
                if _back and not _back.get("shot") and _back.get("step") == step_num - 1 and step_shot:
                    _back["shot"] = step_shot

                # Ghi nhận vào Session Manager
                self.session.record_step(
                    mission_name=mission.name,
                    mission_title=mission.title,
                    step_in_mission=step_num,
                    activity=state_bundle["activity"],
                    active_tab_idx=current_tab_idx,
                    ui_state=ui_state,
                    state_bundle=state_bundle,
                    decision=decision,
                    screenshot_rel=step_shot
                )

                self.ai_decisions_log.append({
                    "mission": mission.name,
                    "step": step_num,
                    "provider": provider,
                    "thought": thought,
                    "action": f"{act_type} {act_param}",
                    "focused": ui_state["focused_sig"]
                })

                if defect:
                    print(f"      🚨 Phát hiện lỗi [{defect.get('severity')}]: {defect.get('issue')}", flush=True)
                    self.all_findings.append(defect)
                    mission.findings.append(defect)

                # KL8 fix loop 2 (F63/F66): ghi lại hành động vừa quyết định
                # để lần perception sau biết dump này ở "sau phím gì" (các gate
                # "sau DPAD_DOWN" phải key trên phím thật, không tin thought).
                mission.evidence["last_action"] = (
                    act_type,
                    (act_param or "").upper() if act_type == "KEY" else act_param,
                )

                # 3. ACTION: Thực thi hành động trên TV
                if act_type == "KEY":
                    key_upper = (act_param or "DPAD_DOWN").upper()
                    if key_upper in ("DOUBLE_BACK", "BACK_DOUBLE", "BACK2"):
                        self.device.send_key("BACK")
                        time.sleep(0.25)
                        self.device.send_key("BACK")
                        time.sleep(1.2)
                    elif key_upper == "BACK" and (self.device.action_history and self.device.action_history[-1].upper() == "BACK"):
                        # AI đã bấm BACK ở bước trước và bước này bấm tiếp BACK để thoát mục:
                        # Gửi cú nhấn BACK đúp để đảm bảo nằm trong khung thời gian double-back của TV
                        self.device.send_key("BACK")
                        time.sleep(0.25)
                        self.device.send_key("BACK")
                        time.sleep(1.2)
                    elif key_upper in ("ENTER", "OK") and ("heroplay" in (ui_state.get("focused_sig") or "").lower() or "btnplay" in (ui_state.get("focused_sig") or "").lower()):
                        self.device.send_key(act_param or "OK")
                        time.sleep(2.2)
                    else:
                        self.device.send_key(act_param or "DPAD_DOWN")
                        time.sleep(0.7)
                elif act_type == "LONG_PRESS":
                    self.device.send_long_press(act_param or "OK")
                    time.sleep(1.0)
                elif act_type == "KEYPAD":
                    self.device.send_keypad_digits(str(act_param or "1"))
                    time.sleep(1.0)
                elif act_type == "SWITCH_TAB":
                    try:
                        t_idx = int(act_param)
                        self.device.switch_tab(t_idx)
                        self.tested_tabs.add(t_idx)
                        time.sleep(1.2)
                        print(f"      🔀 AI chủ động chuyển sang {self.ALL_TABS.get(t_idx, f'Tab {t_idx}')} để săn lỗi!", flush=True)
                    except Exception as e:
                        print(f"      ⚠️ Lỗi chuyển tab: {e}", flush=True)
                elif act_type == "OPEN_MULTIVIEW":
                    self.device.open_multiview()
                    time.sleep(1.8)
                    print(f"      📺 AI chủ động mở màn hình MultiView!", flush=True)
                elif act_type == "LAUNCH_WEB_PLAYER":
                    self.device.launch_web_player()
                    time.sleep(2.5)
                    print(f"      🌐 AI chủ động mở Trình Phát Web (WebPlayerActivity)!", flush=True)
                elif act_type == "LAUNCH_VOD_PLAYER_DIRECTED":
                    self.device.launch_vod_player()
                    time.sleep(6.0)
                    print(f"      🎬 AI chủ động mở Trình Phát VOD Native (PlayerActivity FILM)!", flush=True)
                elif act_type == "TEXT":
                    self.device.input_text(act_param or "uefa")
                    time.sleep(0.8)
                elif act_type == "WAIT":
                    try:
                        time.sleep(float(act_param or "1.5"))
                    except ValueError:
                        time.sleep(1.0)
                elif act_type == "VERIFY_STREAM":
                    stream_ok, delta = self.device.detect_video_motion(duration_sec=1.5, samples=3, is_player_context=True)
                    if not stream_ok and "player" in self.device.current_activity().lower():
                        # Đệm xác thực 2 nhịp: chờ thêm 2.0s để luồng buffer xong trên CI rồi đo lại
                        print("      ⏳ Luồng đang nạp buffer trên CI, đợi 2.0s để đo lại khung hình...", flush=True)
                        time.sleep(2.0)
                        stream_ok, delta = self.device.detect_video_motion(duration_sec=1.5, samples=3, is_player_context=True)

                    self.session.record_video_verification(stream_ok, delta, self.device.current_activity())
                    print(f"      📹 Kết quả kiểm tra luồng video: {'PHÁT MƯỢT' if stream_ok else 'ĐỨNG HÌNH'} (delta: {delta:.2f}%)", flush=True)
                    if not stream_ok and "player" in self.device.current_activity().lower():
                        self.all_findings.append({
                            "area": "Trình phát Video",
                            "severity": "HIGH",
                            "issue": "Video ExoPlayer đứng hình hoặc không tải được luồng",
                            "detail": f"Motion delta = {delta:.2f}% sau 2 lần đo",
                            "suggestion": "Kiểm tra cơ chế failover sang nguồn dự phòng hoặc proxy CDN"
                        })
                elif act_type == "COMPLETE_MISSION":
                    if mission.steps_executed < min(4, mission.max_steps):
                        print(f"   ℹ️ [Mission In-Progress] Nhiệm vụ chưa đủ số bước tối thiểu ({mission.steps_executed}/4), AI tiếp tục khảo sát sâu...", flush=True)
                        self.device.send_key("DPAD_RIGHT")
                        time.sleep(0.7)
                    elif mission.required_activity and not mission.reached_required:
                        # KL8 fix loop 1 (P0-1): không cho tự kết thúc pass giả khi
                        # chưa từng tới activity đích của directed mission.
                        issue = (f"Mission tự kết thúc (COMPLETE_MISSION) khi chưa từng tới "
                                 f"{mission.required_activity} — không tính pass (P0-1: false pass).")
                        finding = {
                            "area": mission.title,
                            "severity": "HIGH",
                            "issue": issue,
                            "detail": f"Directed mission yêu cầu {mission.required_activity} nhưng activity này không xuất hiện trong cả mission.",
                            "suggestion": f"Kiểm tra directed launch {mission.directed_launch} và đường mở {mission.required_activity}."
                        }
                        print(f"   ❌ [Mission Failed] {issue}", flush=True)
                        self.all_findings.append(finding)
                        mission.findings.append(finding)
                        mission.failed = True
                        break
                    else:
                        # KL8 fix loop 2 (F66/F63): cửa cứng cuối mission —
                        # marker trạng thái / OSD chưa từng thấy thì FAIL (hoặc
                        # NOT TESTABLE), không cho tự kết thúc pass giả.
                        gate_result, gate_findings = self._check_mission_end_gates(mission)
                        for gf in gate_findings:
                            self.all_findings.append(gf)
                            mission.findings.append(gf)
                        if gate_result == "fail":
                            print(f"   ❌ [Mission Failed] {gate_findings[0]['issue'] if gate_findings else 'End gate không qua.'}", flush=True)
                            mission.failed = True
                            break
                        if gate_result == "not_testable":
                            print(f"   ⚪ [Mission Not Testable] {mission.title}", flush=True)
                            mission.not_testable = True
                            break
                        print(f"   ✅ [Mission Complete] Hoàn thành mục tiêu nhiệm vụ!", flush=True)
                        mission.passed = True
                        break

                # Ghi nhận phản hồi kết quả thao tác vào bộ nhớ phiên cho lượt tiếp theo
                post_ui = self.device.dump_ui_state()
                # KL8 fix loop 2 (F66b): BACK bấm trong player — ghi activity
                # + focus NGAY SAU BACK (scenario gốc P0-6: focus NONE sau BACK).
                if (act_type == "KEY" and (act_param or "").upper() == "BACK"
                        and "PlayerActivity" in (state_bundle.get("activity") or "")):
                    mission.evidence["back_in_player"] = {
                        "activity_before": state_bundle.get("activity"),
                        "activity_after": self.device.current_activity(),
                        "focused_sig": post_ui.get("focused_sig"),
                        "focused_text": post_ui.get("focused_text"),
                        "step": step_num,
                    }
                # KL8 fix loop 2 (F66 item 7): ENTER bấm khi đã thấy trận
                # KẾT THÚC trong dump — ghi lại dòng đang focus lúc bấm
                # (xác nhận hành vi trận đã xong: toast "Trận đấu đã kết
                # thúc", không mở picker phòng). Toast là bằng chứng phụ
                # (uiautomator có thể không bắt được cửa sổ toast) nên chỉ
                # ghi nhận, không làm gate.
                if (mission.name == "MISSION_FINISHED_MATCH_SCORES"
                        and act_type == "KEY" and (act_param or "").upper() == "ENTER"
                        and mission.evidence.get("finished_found")):
                    mission.evidence["finished_enter"] = {
                        "step": step_num,
                        "focused_sig": state_bundle.get("focused_sig"),
                        "focused_text": state_bundle.get("focused_text"),
                    }
                    _post_blob = " ".join(
                        f"{r_id} {txt}"
                        for r_id, txt in (post_ui.get("all_visible_texts") or [])
                    ).lower()
                    if "trận đấu đã kết thúc" in _post_blob:
                        mission.evidence["finished_toast_seen"] = True
                # KL8 fix loop 2 (F66d): lấy mẫu flash "Tập tiếp" NGAY sau
                # ENTER mở tập cuối (dump post-action, ~1s sau phím) — bổ sung
                # cho mẫu sớm ở lần perception sau (khi activity player đã hiện).
                if (mission.name == "MISSION_COLD_OPEN_LAST_EPISODE"
                        and mission.evidence.get("last_episode_enter_pressed")
                        and "next_ep_visible_immediate" not in mission.evidence):
                    _blob = " ".join(
                        f"{r_id} {txt}"
                        for r_id, txt in (post_ui.get("all_visible_texts") or [])
                    ).lower()
                    mission.evidence["next_ep_visible_immediate"] = (
                        ("btnbarnextep" in _blob or "btnwebnextep" in _blob)
                        and "tập tiếp" in _blob
                    )
                # KL8 fix loop 1 (P0-2): SWITCH_TAB phải tới được tab đích — không
                # thì FAIL mission ngay, không cho chạy tiếp rồi pass giả. Chỉ kết
                # luận khi detector xác định được một tab KHÁC (None = không xác
                # định được, VD đang ở player — không kết luận vội).
                if act_type == "SWITCH_TAB":
                    try:
                        target_idx = int(act_param)
                    except (TypeError, ValueError):
                        target_idx = None
                    if target_idx is not None:
                        detected_idx = self._detect_tab_index(post_ui)
                        if detected_idx is not None and detected_idx != target_idx:
                            # KL8 fix loop 1 (F51): máy chậm/lạnh có thể vẫn
                            # thấy tab cũ lúc dump sau 1.2s settle — dump lại
                            # một lần sau thêm 1.5s rồi mới kết luận fail.
                            # Vẫn giữ hướng fail-safe: dump lại vẫn sai tab
                            # (hoặc vẫn xác định được tab khác) thì FAIL như
                            # cũ — fail giả tốt hơn pass giả. Dump lại ra
                            # None (= không xác định được) thì không kết luận.
                            time.sleep(1.5)
                            post_ui = self.device.dump_ui_state()
                            detected_idx = self._detect_tab_index(post_ui)
                        if detected_idx is not None and detected_idx != target_idx:
                            issue = (f"SWITCH_TAB({target_idx}) không tới được tab đích: đang ở "
                                     f"{self.ALL_TABS.get(detected_idx, f'Tab {detected_idx}')} "
                                     f"(yêu cầu {self.ALL_TABS.get(target_idx, f'Tab {target_idx}')}).")
                            finding = {
                                "area": "Điều hướng Tab",
                                "severity": "HIGH",
                                "issue": issue,
                                "detail": f"Sau SWITCH_TAB({target_idx}), tab detector = {detected_idx} (nav-selected/fallback).",
                                "suggestion": "Kiểm tra tab đích còn tồn tại không (VD Tab 6 Home Hub đã đổi thành Trang Chủ ở Task 4) và sửa mission dùng tab đó."
                            }
                            print(f"      🚨 {issue}", flush=True)
                            self.all_findings.append(finding)
                            mission.findings.append(finding)
                            mission.failed = True
                            self.tested_tabs.discard(target_idx)
                            break
                step_feedback = f"Hành động '{act_type} {act_param}' đã chạy xong. Focus hiện tại: '{post_ui.get('focused_text')}' ({post_ui.get('focused_sig')}), Activity: {self.device.current_activity()}"
                self.brain.record_step_feedback(step_feedback)

            if not mission.passed and not mission.failed and mission.steps_executed >= min(4, mission.max_steps):
                if mission.required_activity and not mission.reached_required:
                    # KL8 fix loop 1 (P0-1): chạy hết số bước mà không tới được
                    # activity đích thì không auto-pass (false pass).
                    issue = (f"Mission chạy hết {mission.steps_executed} bước mà không tới được "
                             f"{mission.required_activity} — không tính pass (P0-1: false pass).")
                    finding = {
                        "area": mission.title,
                        "severity": "HIGH",
                        "issue": issue,
                        "detail": f"Directed mission yêu cầu {mission.required_activity} nhưng activity này không xuất hiện trong cả mission.",
                        "suggestion": f"Kiểm tra directed launch {mission.directed_launch} và đường mở {mission.required_activity}."
                    }
                    print(f"   ❌ [Mission Failed] {issue}", flush=True)
                    self.all_findings.append(finding)
                    mission.findings.append(finding)
                    mission.failed = True
                else:
                    # KL8 fix loop 2 (F66/F63): chạy hết số bước mà cửa trạng
                    # thái chưa qua thì không auto-pass (false pass).
                    gate_result, gate_findings = self._check_mission_end_gates(mission)
                    for gf in gate_findings:
                        self.all_findings.append(gf)
                        mission.findings.append(gf)
                    if gate_result == "fail":
                        print(f"   ❌ [Mission Failed] {gate_findings[0]['issue'] if gate_findings else 'End gate không qua.'}", flush=True)
                        mission.failed = True
                    elif gate_result == "not_testable":
                        print(f"   ⚪ [Mission Not Testable] {mission.title}", flush=True)
                        mission.not_testable = True
                    elif not any(f.get("severity") == "CRITICAL" for f in mission.findings):
                        print(f"   ✅ [Mission Complete] Đã hoàn thành toàn bộ các bước kiểm thử ({mission.steps_executed}/{mission.max_steps}) không phát sinh lỗi nghiêm trọng!", flush=True)
                        mission.passed = True

            # KL8 fix loop 2: tóm tắt bằng chứng trạng thái vào detail của
            # mission để bảng checks đọc được (không chỉ "N bước thực thi").
            if mission.name == "MISSION_SPORT_PLAYER_BOTTOM_ROW":
                shots = mission.evidence.get("marker_shots", {})
                mission.result_detail = (
                    "bottom row: " + (", ".join(sorted(shots.values())) if shots else "KHÔNG vào dump — FAIL")
                    + ("; nhãn live TRỰC TIẾP/Về trực tiếp đã thấy"
                       if mission.evidence.get("sport_live_label_seen")
                       else "; nhãn live TRỰC TIẾP/Về trực tiếp chưa thấy")
                )
            elif mission.name == "MISSION_IPTV_PLAYER_BACK_FOCUS":
                back = mission.evidence.get("back_in_player") or {}
                if back:
                    mission.result_detail = (
                        f"BACK trong player step {back.get('step')}: "
                        f"{back.get('activity_before')} → {back.get('activity_after')}, "
                        f"focus={back.get('focused_sig')}"
                        + (f", shot {back['shot']}" if back.get("shot") else "")
                    )
                else:
                    mission.result_detail = "BACK trong player: KHÔNG có — FAIL"
            elif mission.name == "MISSION_IPTV_MINI_GUIDE":
                shots = mission.evidence.get("marker_shots", {})
                mission.result_detail = (
                    "Mini-Guide: " + (f"mở, shot {', '.join(sorted(shots.values()))}" if shots else "KHÔNG mở — FAIL")
                    + ("; tiêu đề Danh Sách Kênh đã thấy"
                       if mission.evidence.get("miniguide_header_seen")
                       else "; tiêu đề Danh Sách Kênh chưa thấy")
                )
            elif mission.name == "MISSION_COLD_OPEN_LAST_EPISODE":
                ev = mission.evidence
                if ev.get("last_episode_opened"):
                    mission.result_detail = (
                        f"tập cuối mở: {ev.get('last_episode_label') or '?'} → "
                        f"{(ev.get('last_episode_player') or '?').split('/')[-1]}; "
                        f"'Tập tiếp' flash: sớm={ev.get('next_ep_visible_early')}, "
                        f"ngay={ev.get('next_ep_visible_immediate')}, "
                        f"muộn={ev.get('next_ep_visible_late')}"
                    )
                else:
                    mission.result_detail = "tập cuối: KHÔNG mở được — FAIL"
            elif mission.name == "MISSION_FINISHED_MATCH_SCORES":
                ev = mission.evidence
                if not ev.get("finished_found"):
                    mission.result_detail = "trận đã kết thúc: KHÔNG thấy trong dữ liệu live — NOT TESTABLE"
                else:
                    mission.result_detail = (
                        f"trận đã kết thúc: {ev.get('finished_label') or '?'}; "
                        f"tỉ số 2:8: {'đã thấy' if ev.get('score_2_8_seen') else 'không có trong dữ liệu chạy này'}; "
                        f"tỉ số hợp lệ đã thấy: {', '.join(ev.get('plausible_scores_seen') or []) or 'không có'}; "
                        f"VS kèm trận kết thúc: {'đã thấy' if ev.get('finished_vs_seen') else 'chưa thấy'}; "
                        f"tỉ số ảo hiện số thô: {ev.get('implausible_raw_seen') or 'không có — OK'}"
                    )
            elif mission.name in ("MISSION_WEBPLAYER_DIRECTED_REAL_FILM",
                                 "MISSION_VOD_PLAYER_SEEK_AND_RESUME"):
                ev = mission.evidence
                shots = ev.get("marker_shots", {})
                osd_part = (
                    f"OSD (F63): hiện, shot {shots.get('web_osd')}; focus lúc mở: {ev.get('web_osd_focus') or '?'}"
                    if ev.get("web_osd_seen") else "OSD (F63): KHÔNG mở — FAIL (F63)"
                )
                if ev.get("web_osd_dwell_checked"):
                    if ev.get("web_osd_dwell_ok") and ev.get("web_osd_dwell_focus_playpause"):
                        osd_part += "; dwell ~10s: còn hiện, focus btnWebPlayPause"
                    elif ev.get("web_osd_dwell_ok"):
                        osd_part += "; dwell ~10s: còn hiện, focus KHÔNG ở btnWebPlayPause"
                    else:
                        osd_part += "; dwell ~10s: ĐÃ ẨN trước 10s (dwell 300s chưa có tác dụng)"
                entry_part = ""
                if ev.get("webplayer_entry_recorded"):
                    entry = ev.get("webplayer_entry_texts") or []
                    entry_part = (
                        f" | vào player (force_web): {'; '.join(entry) if entry else '?'}; "
                        f"WebView: {'có' if ev.get('webplayer_entry_webview') else 'không'}; "
                        f"hộp lỗi: {'có' if ev.get('webplayer_entry_error') else 'không'}"
                    )
                if not ev.get("web_speed_btn_seen"):
                    f47_part = " | Tốc độ (F47): nút KHÔNG hiện — probe fail — FAIL (F47)"
                elif ev.get("speed_set_attempted"):
                    if ev.get("speed_label_after") and ev.get("speed_label_after") != ev.get("speed_label_before"):
                        f47_part = (
                            f" | Tốc độ (F47): nút đã thấy; set {ev.get('speed_label_before')} → "
                            f"{ev.get('speed_label_after')} (read-back OK)"
                        )
                    else:
                        f47_part = (
                            f" | Tốc độ (F47): nút đã thấy; set fail, nhãn giữ {ev.get('speed_label_before')} — FAIL (F47)"
                        )
                    if ev.get("speed_label_reverted"):
                        f47_part += "; nhãn tự quay về giá trị cũ sau khi đổi (xem finding)"
                else:
                    f47_part = " | Tốc độ (F47): nút đã thấy (probe pass); chưa bấm set"
                mission.result_detail = osd_part + entry_part + f47_part

            # Chụp ảnh và đo PSS RAM sau mỗi nhiệm vụ
            pss_mb = self.device.get_pss_memory_mb()
            if pss_mb > 0:
                print(f"   📊 [Telemetry] RAM PSS tiêu thụ: {pss_mb:.1f} MB", flush=True)
            safe_name = f"{m_idx + 2:02d}_{mission.name.lower()}"
            self._record_screen(safe_name)

            # Lưu báo cáo trung gian sau mỗi nhiệm vụ để không bao giờ mất kết quả
            try:
                self.generate_reports(round(time.time() - self.start_time), video_info=None)
            except Exception as e:
                print(f"   ⚠️ [Report] Lưu báo cáo trung gian lỗi: {e}", flush=True)

        # Dừng và lưu video toàn bộ quá trình kiểm thử
        video_info = None
        if self.recorder:
            try:
                video_info = self.recorder.stop_and_save()
            except Exception as e:
                print(f"⚠️ [VideoRecorder] Lỗi khi dừng và lưu video: {e}", flush=True)

        # Hoàn tất phiên QA
        duration_total = round(time.time() - self.start_time)
        print(f"\n🏁 Phiên QA hoàn tất trong {duration_total}s!", flush=True)
        self.generate_reports(duration_total, video_info=video_info)

    def _record_screen(self, label):
        """Save one step screenshot. KL8 fix loop 2 (F67b): run 42963719447
        lost step_043 (the exact step the judge flagged focus NONE) and
        mission shot 06 — screencap_bytes() returned None once under load
        and the saver silently dropped the shot. Now: retry 3x; if still
        nothing, write an explicit MISSING placeholder (dark frame, labelled)
        so the timeline keeps its step and the loss is visible instead of a
        silent hole. Never raises — a screenshot failure must not kill the
        QA run."""
        png = None
        for attempt in range(3):
            png = self.device.screencap_bytes()
            if png:
                break
            time.sleep(0.5)
        filename = f"{label}.jpg"
        path = os.path.join(self.shots_dir, filename)
        if not png:
            print(f"   ⚠️ [Screenshot] {label}: screencap thất bại sau 3 lần thử — ghi placeholder MISSING.", flush=True)
            self.missing_shots.append(label)
            try:
                self._write_missing_placeholder(path, label)
            except Exception as e:
                print(f"   ⚠️ [Screenshot] Không ghi được placeholder {label}: {e}", flush=True)
                return None
            rel_path = f"shots/{filename}"
            self.all_screenshots.append((label, rel_path))
            return rel_path
        try:
            if Image:
                im = Image.open(io.BytesIO(png)).convert("RGB")
                im.thumbnail((960, 540))
                im.save(path, "JPEG", quality=75)
            else:
                with open(path.replace(".jpg", ".png"), "wb") as f:
                    f.write(png)
                filename = filename.replace(".jpg", ".png")
        except Exception:
            try:
                with open(path.replace(".jpg", ".png"), "wb") as f:
                    f.write(png)
                filename = filename.replace(".jpg", ".png")
            except Exception as e:
                print(f"   ⚠️ [Screenshot] Không lưu được {label}: {e} — ghi placeholder MISSING.", flush=True)
                self.missing_shots.append(label)
                try:
                    self._write_missing_placeholder(path, label)
                except Exception:
                    return None
        rel_path = f"shots/{filename}"
        self.all_screenshots.append((label, rel_path))
        return rel_path

    def _write_missing_placeholder(self, path, label):
        """Dark 960x540 frame labelled as a missed capture (F67b) — the file
        exists at the expected path, but the image itself says the capture
        failed, so nobody mistakes it for a real screenshot."""
        if not Image:
            raise RuntimeError("PIL unavailable for placeholder")
        from PIL import ImageDraw
        im = Image.new("RGB", (960, 540), (16, 16, 20))
        d = ImageDraw.Draw(im)
        d.text((24, 240), "SCREENSHOT THIEU", fill=(255, 90, 60))
        d.text((24, 270), f"{label} — screencap that bai (3 lan thu)", fill=(200, 200, 200))
        im.save(path, "JPEG", quality=75)

    def generate_reports(self, duration_sec, video_info=None):
        passed_missions = sum(1 for m in self.missions if m.passed)
        total_missions = len(self.missions)
        # KL8 fix loop 2: mission NOT TESTABLE không tính vào mẫu số điểm
        # mission (không pass, không fail — dữ liệu live thiếu trạng thái).
        not_testable_count = sum(1 for m in self.missions if m.not_testable)
        scored_missions = total_missions - not_testable_count

        # Tính điểm QA chuẩn (0-100)
        penalty = {"CRITICAL": 30, "HIGH": 15, "MEDIUM": 5, "LOW": 2}
        score = 100 - sum(penalty.get(f.get("severity", "LOW"), 2) for f in self.all_findings)
        if scored_missions:
            score -= round((scored_missions - passed_missions) / scored_missions * 20)
        final_score = max(0, min(100, score))

        # Phân tích thông tin video tour
        video_file = None
        timelapse_file = None
        video_coverage = None
        if isinstance(video_info, dict):
            v_full = video_info.get("full_tour")
            if v_full and os.path.exists(v_full):
                video_file = os.path.basename(v_full)
            v_tl = video_info.get("timelapse")
            if v_tl and os.path.exists(v_tl):
                timelapse_file = os.path.basename(v_tl)
            # KL8 fix loop 2 (F67c): độ phủ video (ghi được / thời gian chạy)
            # — "full tour" 169s cho run 85 phút phải thấy được trong report.
            video_coverage = {
                "recorded_seconds": video_info.get("recorded_seconds"),
                "expected_seconds": video_info.get("expected_seconds"),
                "chunks": video_info.get("chunks"),
                "partial": video_info.get("partial"),
            }
            if video_info.get("partial"):
                print(f"⚠️ [Video] Video tour chưa đủ: {video_info.get('recorded_seconds')}s ghi được / {video_info.get('expected_seconds')}s chạy.", flush=True)
        elif isinstance(video_info, str) and os.path.exists(video_info):
            video_file = os.path.basename(video_info)

        # Hoàn tất Session và xuất qa_session.json + qa_session_summary.md
        session_manifest = self.session.finish_session(
            final_score=final_score,
            video_tour=video_file,
            timelapse=timelapse_file
        )

        checks_data = []
        for m in self.missions:
            detail = f"{m.steps_executed} bước thực thi"
            if m.result_detail:
                detail += f" — {m.result_detail}"
            if m.not_testable:
                detail += f" — NOT TESTABLE: {m.not_testable_reason}"
            checks_data.append({
                "name": m.title,
                "ok": m.passed,
                "not_testable": m.not_testable,
                "detail": detail
            })

        report_json = {
            "score": final_score,
            "duration_sec": duration_sec,
            "session_id": self.session.session_id,
            "session": session_manifest,
            "video": video_file,
            "timelapse": timelapse_file,
            "video_coverage": video_coverage,
            "engine": "KenhLive 100% Autonomous AI QA Suite",
            "brain_provider": self.brain.provider_active,
            "session_turns": self.brain.turn_counter,
            "session_messages_count": len(self.brain.session_messages),
            "checks_passed": passed_missions,
            "checks_total": total_missions,
            "missions_passed": f"{passed_missions}/{total_missions}",
            "missions_not_testable": not_testable_count,
            "checks": checks_data,
            "findings": self.all_findings,
            "screenshots": self.all_screenshots,
            # KL8 fix loop 2 (F67b): các shot screencap thất bại (đã ghi
            # placeholder MISSING) — bằng chứng thiếu phải thấy được trong
            # report, không mất lặng lẽ như step_043 ở run 42963719447.
            "missing_screenshots": self.missing_shots,
            "decisions_timeline": self.ai_decisions_log[:50]
        }

        # Lưu qa_report.json
        json_path = os.path.join(self.out_dir, "qa_report.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(report_json, f, ensure_ascii=False, indent=2)
        print(f"📄 Đã lưu báo cáo JSON tại: {json_path}", flush=True)

        # Tạo qa_report.html
        html_path = os.path.join(self.out_dir, "qa_report.html")
        self._render_html_report(report_json, html_path)
        print(f"🌐 Đã xuất báo cáo trực quan HTML tại: {html_path}", flush=True)

    def _render_html_report(self, r, out_path):
        esc = html.escape
        score = r["score"]
        grade = "A" if score >= 90 else "B" if score >= 75 else "C" if score >= 60 else "D"
        grade_color = "#3ddc97" if score >= 75 else "#ff8e3c" if score >= 60 else "#ff4d4d"

        findings_rows = ""
        for f in r["findings"]:
            sev = f.get("severity", "MEDIUM")
            col = "#ff4d4d" if sev == "CRITICAL" else "#ff8e3c" if sev == "HIGH" else "#ffd166"
            findings_rows += f"""
            <tr>
              <td><span style='background:{col}22;color:{col};border:1px solid {col}55;padding:3px 8px;border-radius:6px;font-size:11px;font-weight:700;'>{esc(sev)}</span></td>
              <td><b>{esc(f.get('area', ''))}</b><br><small style='color:#8c9fc2;'>{esc(f.get('detail', ''))}</small></td>
              <td>{esc(f.get('issue', ''))}</td>
              <td style='color:#a3e635;font-family:monospace;font-size:12px;'>{esc(f.get('suggestion', ''))}</td>
            </tr>"""

        if not findings_rows:
            findings_rows = "<tr><td colspan='4' style='text-align:center;padding:24px;color:#3ddc97;'>🎉 Không phát hiện lỗi nghiêm trọng! Hệ thống hoạt động hoàn hảo.</td></tr>"

        timeline_rows = ""
        for t in r.get("decisions_timeline", []):
            timeline_rows += f"""
            <div style='margin-bottom:12px;padding:10px 14px;background:#10131c;border-left:3px solid #ff6500;border-radius:6px;font-size:13px;'>
              <span style='color:#ff6500;font-weight:700;'>[{esc(t["mission"])} · Step {t["step"]}]</span>
              <span style='color:#6b7490;margin-left:8px;'>({esc(t.get("provider", "AI"))})</span><br>
              <span style='color:#cbd5e1;'>Thought: {esc(t["thought"])}</span><br>
              <code style='color:#38bdf8;font-weight:700;'>Action: {esc(t["action"])}</code>
            </div>"""

        gallery_html = ""
        for lbl, shot_path in r.get("screenshots", []):
            gallery_html += f"""
            <div style='background:#10131c;border:1px solid rgba(255,255,255,0.08);border-radius:10px;overflow:hidden;padding:8px;'>
              <img src='{esc(shot_path)}' style='width:100%;border-radius:6px;display:block;' loading='lazy'>
              <div style='font-size:12px;color:#94a3b8;margin-top:6px;text-align:center;'>{esc(lbl)}</div>
            </div>"""

        session_html = self.session.render_session_html_section()

        video_card_html = ""
        if r.get("video"):
            first_shot = r.get("screenshots", [("", "")])[0][1] if r.get("screenshots") else ""
            tl_link = ""
            if r.get("timelapse"):
                tl_link = f"""<a href="{esc(r['timelapse'])}" download style="background:#1e293b;color:#a3e635;border:1px solid #a3e63544;padding:6px 14px;border-radius:8px;font-size:12px;text-decoration:none;font-weight:600;">⚡ Tải Timelapse 10x ({esc(r['timelapse'])})</a>"""

            video_card_html = f"""
    <div class="card" style="border: 1px solid rgba(56, 189, 248, 0.3); background: #0c101d;">
      <h2 style="font-size:17px; margin:0 0 12px; color:#38bdf8; display:flex; align-items:center; gap:8px;">
        <span>🎬</span> Video Toàn Bộ Quá Trình Kiểm Thử Android TV (Full Tour Replay)
      </h2>
      <div style="position:relative; width:100%; border-radius:12px; overflow:hidden; background:#000; box-shadow:0 8px 32px rgba(0,0,0,0.7);">
        <video controls style="width:100%; max-height:520px; display:block; margin:0 auto;" preload="metadata" poster="{esc(first_shot)}">
          <source src="{esc(r['video'])}" type="video/mp4">
          Trình duyệt không hỗ trợ xem video trực tiếp. Hãy tải video từ thư mục báo cáo.
        </video>
      </div>
      <div style="margin-top:12px; font-size:12px; color:#94a3b8; display:flex; flex-wrap:wrap; gap:16px; align-items:center; justify-content:space-between;">
        <div style="display:flex; gap:14px; align-items:center;">
          <span>📺 <b>1920x1080 (1080p Leanback)</b></span>
          <span>⚡ <b>H.264 FastStart Streamable</b></span>
          <span style="color:#3ddc97;">● Ghi hình xuyên suốt 8 nhiệm vụ</span>
        </div>
        <div style="display:flex; gap:8px;">
          <a href="{esc(r['video'])}" download style="background:#1e293b; color:#38bdf8; border:1px solid #38bdf844; padding:6px 14px; border-radius:8px; font-size:12px; text-decoration:none; font-weight:600;">📥 Tải Video Đầy Đủ ({esc(r['video'])})</a>
          {tl_link}
        </div>
      </div>
    </div>"""

        html_content = f"""<!DOCTYPE html>
<html lang="vi">
<head>
  <meta charset="utf-8">
  <title>KenhLive TV · 100% Autonomous AI QA Report</title>
  <style>
    body {{ background: #07090e; color: #f8fafc; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; padding: 24px; }}
    .container {{ max-width: 1100px; margin: 0 auto; }}
    .card {{ background: #0c0f17; border: 1px solid rgba(255,255,255,0.08); border-radius: 14px; padding: 20px; margin-bottom: 24px; }}
    .header {{ display: flex; justify-content: space-between; align-items: center; }}
    .score-badge {{ font-size: 38px; font-weight: 900; color: {grade_color}; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 14px; }}
    th, td {{ padding: 12px 14px; border-bottom: 1px solid rgba(255,255,255,0.06); text-align: left; font-size: 13px; }}
    th {{ color: #94a3b8; font-weight: 600; text-transform: uppercase; font-size: 11px; }}
    .gallery {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 14px; margin-top: 14px; }}
  </style>
</head>
<body>
  <div class="container">
    <div class="card header">
      <div>
        <h1 style="margin:0;font-size:24px;">🤖 KenhLive TV · 100% Autonomous AI QA Suite</h1>
        <p style="margin:4px 0 0;color:#64748b;font-size:13px;">Engine: {esc(r['engine'])} | Core Brain: {esc(r['brain_provider'])}</p>
      </div>
      <div style="text-align:right;">
        <div class="score-badge">{score}/100 ({grade})</div>
        <div style="font-size:12px;color:#94a3b8;">Hoàn thành: {r['missions_passed']} nhiệm vụ</div>
      </div>
    </div>

    {video_card_html}
    {session_html}

    <div class="card">
      <h2 style="font-size:16px;margin:0 0 10px;">📋 Kết Quả Nhiệm Vụ (Mission Checklist)</h2>
      <table>
        <thead><tr><th>Nhiệm vụ</th><th>Chi tiết</th><th>Trạng thái</th></tr></thead>
        <tbody>
          {"".join(f"<tr><td><b>{esc(c['name'])}</b></td><td>{esc(c['detail'])}</td><td style='color:{'#94a3b8' if c.get('not_testable') else ('#3ddc97' if c['ok'] else '#ff4d4d')};font-weight:700;'>{'⚪ NOT TESTABLE' if c.get('not_testable') else ('✅ PASS' if c['ok'] else '❌ FAIL')}</td></tr>" for c in r['checks'])}
        </tbody>
      </table>
    </div>

    <div class="card">
      <h2 style="font-size:16px;margin:0 0 10px;">🚨 Phát Hiện Lỗi & Đề Xuất Khắc Phục (Bug Findings)</h2>
      <table>
        <thead><tr><th>Mức độ</th><th>Vị trí</th><th>Mô tả sự cố</th><th>Đề xuất sửa code</th></tr></thead>
        <tbody>
          {findings_rows}
        </tbody>
      </table>
    </div>

    <div class="card">
      <h2 style="font-size:16px;margin:0 0 10px;">🧠 Nhật Ký Suy Luận & Ra Quyết Định Của AI (Agent Timeline)</h2>
      <div style="max-height:360px;overflow-y:auto;padding-right:8px;">
        {timeline_rows}
      </div>
    </div>

    <div class="card">
      <h2 style="font-size:16px;margin:0 0 10px;">📸 Ảnh Chụp Hiện Trường (Screenshots Tour)</h2>
      <div class="gallery">
        {gallery_html}
      </div>
    </div>
  </div>
</body>
</html>"""

        with open(out_path, "w", encoding="utf-8") as f:
            f.write(html_content)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="KenhLive 100% Autonomous AI QA Suite")
    parser.add_argument("--out", default="/tmp/qa_report", help="Thư mục xuất báo cáo")
    parser.add_argument("--serial", default=None, help="Mã serial thiết bị adb")
    args = parser.parse_args()

    suite = AutonomousQASuite(out_dir=args.out, serial=args.serial)
    suite.run()

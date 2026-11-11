#!/usr/bin/env python3
"""KenhLive Realtime QA — detector cục bộ (không vision, không mạng).

Chạy trên mọi stable frame: (frame PNG 1920x1080, ui_state dict, activity,
context lịch sử). Mỗi detector trả 0..n finding dict:
  {severity, area, issue, detail, suggestion, evidence: {frame, t, ui_state}}
hoặc ghi vào ctx["needs_vision"] khi cần vision xác minh (VD logo sai).

Ánh xạ sang P0 của run 42950738729 (VISUAL-REVIEW.md):
  focus_loss             -> P0-6   text_overlap    -> P0-3 (phụ; vision là chính
                                      vì OCR không tách được 2 lớp chữ chồng)
  clipped_text          -> P0-4   row_overflow    -> P0-7
  subtitle_seekbar       -> P0-5 (chính: hình học OCR, nhãn giờ làm mốc)
  wrong_logo             -> P0-8 (đẩy vision)      fake_score -> luật Task 5
OCR đắt (~3.6s/band): chỉ OCR band, cache theo frame, gate mỗi 3 bước
(_ocr_due). Không gate -> ~1 giờ OCR cho 1 run full.
"""
import re

# Vùng màn hình TV 1920x1080
NAV_BAND = (0, 0, 1920, 140)          # top nav
HERO_BAND = (0, 140, 1920, 850)      # hero billboard — CI-T4 (reviewer):
                                      # step_006 đồng hồ 15:44 đè lên phụ đề
                                      # hero bị sót vì OCR chỉ soi nav + band
                                      # dưới; vùng hero trước đó không bao giờ
                                      # được OCR. Chỉ chạy ngoài player (trong
                                      # player vùng này là nội dung video).
BOTTOM_BAR_BAND = (0, 850, 1920, 1080)  # seekbar + hàng nút player
SCREEN_W, SCREEN_H = 1920, 1080

BAD_TEXT_PATTERNS = [r"\bnull\b", r"\bundefined\b", r"\bNaN\b",
                     r"NullPointerException", r"JsonSyntaxException",
                     r"\[\$[a-zA-Z_]+\]"]
# Giờ HH:mm đội lốt tỉ số "X : Y" (VD 17 : 0, 23 : 30). Giờ đá bóng
# thực tế bắt đầu từ 15:00 (ca 15:00/16:00 có thật) nên nhánh giờ bao cả
# 15, 16 — CI-T5: nhánh này KHÔNG phụ thuộc môn thể thao (giờ đá đội lốt
# tỉ số thì tố dù là context bóng rổ).
FAKE_SCORE_TIME = ((15, 16, 17, 18, 19, 20, 21, 22, 23), (0, 15, 30, 45))

# Từ khóa ngữ cảnh môn thể thao (CI-T5, VISUAL-REVIEW §9 mục 1): luật
# plausibility (một đội > 9 / tổng > 12) là luật BÓNG ĐÁ — tỉ số bóng rổ
# thật 54:71 (NBL, CI-T4 step_012) bị tố oan vì detector không đọc ngữ cảnh.
BASKETBALL_KEYWORDS = ("bóng rổ", "basketball", "nbl", "nba")
FOOTBALL_KEYWORDS = ("bóng đá", "afc", "saff", "v-league", "vleague",
                     "v.league", "soccer", "football")


def _sport_context(all_visible_texts):
    """('basketball' | 'football' | None) từ text lân cận trong cùng dump."""
    blob = " ".join(t for _, t in (all_visible_texts or [])).lower()
    if any(k in blob for k in BASKETBALL_KEYWORDS):
        return "basketball"
    if any(k in blob for k in FOOTBALL_KEYWORDS):
        return "football"
    return None


def _mk(severity, area, issue, detail, suggestion, frame_ref, t_offset, ui_sig):
    return {
        "severity": severity, "area": area, "issue": issue,
        "detail": detail, "suggestion": suggestion,
        "evidence": {"frame": frame_ref, "video_t": t_offset, "ui_state": ui_sig},
    }


def _boxes_overlap(a, b):
    ox = max(0, min(a["x1"], b["x1"]) - max(a["x0"], b["x0"]))
    oy = max(0, min(a["y1"], b["y1"]) - max(a["y0"], b["y0"]))
    inter = ox * oy
    if inter <= 0:
        return 0.0
    area_a = (a["x1"] - a["x0"]) * (a["y1"] - a["y0"])
    area_b = (b["x1"] - b["x0"]) * (b["y1"] - b["y0"])
    return inter / max(1, min(area_a, area_b))


def detect_blank(frame_png, ui_state, activity, ctx, frame_ref, t_offset):
    """Màn đen/rỗng: stddev thấp + xác thực 2 lần (frame mới nhất của watcher)."""
    from device import RealtimeDevice
    if not RealtimeDevice.is_blank(frame_png):
        return []
    # xác thực lần 2 bằng frame mới nhất của watcher (tránh bắt nhầm transition);
    # KHÔNG sleep — watcher đã lấy mẫu liên tục ~1.2s.
    watcher = ctx.get("watcher")
    png2 = watcher.latest_png() if watcher else None
    if png2 and png2 is not frame_png and not RealtimeDevice.is_blank(png2):
        return []
    if "MainActivity" not in (activity or ""):
        return []
    key = "BLANK:%s" % activity
    if key in ctx.setdefault("reported", set()):
        return []
    ctx["reported"].add(key)
    return [_mk("CRITICAL", "Hiển thị Màn Hình", "Màn hình đen / rỗng hoàn toàn",
                "stddev pixel < 4.0 kéo dài hơn 1.5s sau khi nạp tại %s" % activity,
                "Kiểm tra render lifecycle, layout xml hoặc crash UI background",
                frame_ref, t_offset, ui_state.get("focused_sig", ""))]


def detect_focus_loss(ui_state, activity, ctx, frame_ref, t_offset):
    """Mất focus: focused NONE ngoài player, đã settle (không phải OSD tự ẩn)."""
    if ui_state.get("focused_sig") != "NONE":
        return []
    if "PlayerActivity" in (activity or "") or "WebPlayerActivity" in (activity or ""):
        return []
    key = "FOCUSLOSS:%s" % activity
    if key in ctx.setdefault("reported", set()):
        return []
    ctx["reported"].add(key)
    return [_mk("HIGH", "Điều hướng D-pad", "Mất dấu focus (Focus Loss) trên màn hình",
                "Không có view nào giữ focus tại %s (focused=NONE, không phải player)" % activity,
                "Đảm bảo requestFocus() hoặc focusable=true cho view chính",
                frame_ref, t_offset, "NONE")]


def detect_player_focus_loss(ui_state, activity, ctx, frame_ref, t_offset):
    """Mất focus TRONG player (P0-6): OSD/hàng nút đang hiện (osd_visible)
    nhưng focused NONE — khác OSD tự ẩn (lúc đó không có nút nào hiện).
    Chạy khi runner đã tính ui_state['osd_visible'] từ UI dump."""
    if "PlayerActivity" not in (activity or "") and "WebPlayerActivity" not in (activity or ""):
        return []
    if ui_state.get("focused_sig") != "NONE":
        return []
    if not ui_state.get("osd_visible"):
        return []  # OSD ẩn -> focus NONE là bình thường, không báo
    key = "PLAYERFOCUSLOSS:%s" % activity
    if key in ctx.setdefault("reported", set()):
        return []
    ctx["reported"].add(key)
    return [_mk("HIGH", "Player", "Mất focus trong player khi OSD đang hiện",
                "Hàng nút điều khiển đang hiện nhưng không nút nào giữ focus "
                "tại %s (focused=NONE sau BACK/OSD)" % activity,
                "Sau khi hiện OSD lại, trả focus về 1 control hợp lý (VD nút EPG)",
                frame_ref, t_offset, "NONE")]


def detect_keyboard_from_image(frame_png):
    """Bàn phím ảo đang mở, nhận từ ẢNH (pixel) — không dựa dump.
    CI-T7 mục 3: bàn phím QWERTY in-app của KenhLive không có node nào
    trong dump (ui_state chỉ có 5 trường focused) nên guard đếm ký tự 1
    chữ trong dump không thấy gì — CI-T6 tố oan focus-trap MEDIUM ở
    step_066/067 trong khi người dùng đang gõ (phím focus đổi ⇧ -> 'z'
    -> 'q' -> '▶'). Chữ ký pixel (đo trên frame thật CI-T6): >= 3 dải
    ngang dày đặc pixel 'xám phím' (độ sáng 40-70) ở nửa dưới màn hình, mỗi
    dải cao 20-45px (theo H/540), cách đều nhau (tỉ lệ khoảng cách max/min
    <= 1.5) — chính là 4 hàng phím QWERTY. Kiểm trên 29 frame CI-T6:
    bắt 3/3 frame có bàn phím (066/067/071), 0 FP trên 26 frame còn lại.
    Chỉ downscale tối đa về 960 rộng (1920->960 vẫn bắt được; downscale
    về 480 làm mờ phím, mất tín hiệu — đã kiểm). Quét rẻ (step 2 theo x),
    nhưng caller chỉ gọi khi nghi kẹt (lazy) nên không tốn mỗi bước."""
    if not frame_png:
        return False
    try:
        from PIL import Image
        import io as _io
        im = Image.open(_io.BytesIO(frame_png)).convert("L")
        if im.width > 960:
            im = im.resize((960, int(im.height * 960 / im.width)), Image.BILINEAR)
        W, H = im.size
        px = im.load()
        sc = H / 540.0
        x0, x1 = int(W * 0.30), int(W * 0.75)
        thr = 0.30 * (x1 - x0)
        # Số pixel xám-phím trên mỗi hàng (step 2 theo x, nhân 2 lại).
        runs = []
        s = None
        for y in range(H):
            c = 0
            for x in range(x0, x1, 2):
                if 40 <= px[x, y] <= 70:
                    c += 1
            if c * 2 >= thr and s is None:
                s = y
            elif c * 2 < thr and s is not None:
                runs.append((s, y - 1))
                s = None
        if s is not None:
            runs.append((s, H - 1))
        merged = []
        for r in runs:
            if merged and r[0] - merged[-1][1] <= max(4, int(4 * sc)):
                merged[-1] = (merged[-1][0], r[1])
            else:
                merged.append(r)
        cands = []
        for (a, b) in merged:
            h = b - a + 1
            cy = (a + b) / 2.0
            if 20 * sc <= h <= 45 * sc and cy >= 0.55 * H:
                cands.append((a + b) / 2.0)
        if len(cands) < 3:
            return False
        gaps = [cands[i + 1] - cands[i] for i in range(len(cands) - 1)]
        return max(gaps) / max(1.0, min(gaps)) <= 1.5
    except Exception:
        return False


def detect_focus_trap(ui_state, activity, ctx, frame_ref, t_offset, frame_png=None):
    """Kẹt focus: cùng focused sig sau 3 phím D-PAD cùng hướng, không phải mép.
    CI-T6 mục 7: chỉ tính quan sát KHÁC NHAU — frame trùng quan sát trước
    (011=012, 055=056, 075=076 ở CI-T5 là cùng 1 frame chụp lại) không được
    tính là 1 quan sát mới (hist từng nhận 2 entry giống hệt từ 1 trạng thái
    thật -> tố kẹt oan); và không tố khi bàn phím ảo đang mở (focus đứng yên
    vì đang gõ là đúng, không phải kẹt).
    CI-T7 mục 3: bàn phím kiểm bằng ẢNH (detect_keyboard_from_image) khi đã
    đủ 3 quan sát nghi kẹt — guard dump (keyboard_open từ đếm ký tự) không
    thấy bàn phím in-app của KenhLive (dump không có node phím). Check ảnh
    chỉ chạy lazy ở điểm sắp tố (không tốn mỗi bước); kết quả cache theo
    frame_hash trong ctx, ghi vào ctx['keyboard_open_image'] để runner log
    vào timeline."""
    fh = ctx.get("frame_hash")
    if fh and fh == ctx.get("frame_hash_prev"):
        return []  # frame trùng — không append hist, không tính quan sát mới
    if ui_state.get("keyboard_open"):
        return []  # đang gõ bàn phím: focus đứng yên là đúng
    hist = ctx.setdefault("focus_hist", [])
    focused_sig = ui_state.get("focused_sig", "NONE")
    focused_bounds = ui_state.get("focused_bounds")
    last_key = ctx.get("last_key", "")
    hist.append((activity, focused_sig, last_key))
    if len(hist) > 10:
        hist.pop(0)
    if len(hist) < 3 or focused_sig == "NONE":
        return []
    s1, s2, s3 = hist[-3], hist[-2], hist[-1]
    dpad_dirs = ("DPAD_UP", "DPAD_DOWN", "DPAD_LEFT", "DPAD_RIGHT", "UP", "DOWN", "LEFT", "RIGHT")
    if not (s1[0] == s2[0] == s3[0] and s1[1] == s2[1] == s3[1]
            and s2[2] in dpad_dirs and s3[2] in dpad_dirs and s2[2] == s3[2]):
        return []
    if "PlayerActivity" in (activity or "") or "WebPlayerActivity" in (activity or ""):
        return []
    if ui_state.get("has_dialog"):
        return []
    if ui_state.get("focusable_count", 0) <= 3:
        return []
    # mép màn hình: bấm hướng ra mép thì đứng yên là đúng
    if focused_bounds:
        m = re.findall(r"-?\d+", focused_bounds)
        if len(m) >= 4:
            x1, y1, x2, y2 = map(int, m[:4])
            d = s3[2]
            if (d in ("DPAD_LEFT", "LEFT") and x1 < 350) or \
               (d in ("DPAD_RIGHT", "RIGHT") and x2 > 1350) or \
               (d in ("DPAD_UP", "UP") and y1 < 200) or \
               (d in ("DPAD_DOWN", "DOWN") and y2 > 880):
                return []
    key = "TRAP:%s:%s:%s" % (activity, focused_sig, s3[2])
    if key in ctx.setdefault("reported", set()):
        return []
    # CI-T7 mục 3: sắp tố kẹt thì kiểm bàn phím bằng ẢNH trước đã — đang
    # gõ thì đứng yên là đúng, không phải kẹt. Cache theo frame_hash.
    if frame_png is not None:
        _kb_cache = ctx.setdefault("_kb_image_cache", {})
        _fh = ctx.get("frame_hash") or frame_ref
        if _fh not in _kb_cache:
            _kb_cache[_fh] = detect_keyboard_from_image(frame_png)
            if len(_kb_cache) > 12:
                _kb_cache.pop(next(iter(_kb_cache)))
        ctx["keyboard_open_image"] = _kb_cache[_fh]
        if _kb_cache[_fh]:
            return []
    ctx["reported"].add(key)
    return [_mk("MEDIUM", "Điều hướng Focus TV", "Nghi vấn kẹt Focus (Focus Trap)",
                "Gửi phím %s liên tiếp nhưng tiêu điểm và nội dung giữ nguyên tại '%s'" % (s3[2], focused_sig),
                "Kiểm tra nextFocus hoặc ranh giới cuộn của RecyclerView",
                frame_ref, t_offset, focused_sig)]


def detect_offscreen_or_zero_focus(ui_state, activity, ctx, frame_ref, t_offset):
    b = ui_state.get("focused_bounds")
    sig = ui_state.get("focused_sig", "NONE")
    if not b or sig == "NONE":
        return []
    m = re.findall(r"-?\d+", b)
    if len(m) < 4:
        return []
    x1, y1, x2, y2 = map(int, m[:4])
    w, h = x2 - x1, y2 - y1
    if x2 <= 0 or y2 <= 0 or x1 >= SCREEN_W or y1 >= SCREEN_H:
        key = "OFFSCREEN:%s" % sig
        if key in ctx.setdefault("reported", set()):
            return []
        ctx["reported"].add(key)
        return [_mk("HIGH", "Rò rỉ Focus ngoài màn hình",
                    "Focus lọt vào phần tử nằm ngoài khung hình TV: %s" % sig,
                    "bounds=%s nằm ngoài viewport 1920x1080" % b,
                    "Đặt visibility=GONE và focusability=FOCUS_BLOCK_DESCENDANTS khi ẩn panel",
                    frame_ref, t_offset, sig)]
    if w <= 2 or h <= 2:
        key = "ZEROSIZE:%s" % sig
        if key in ctx.setdefault("reported", set()):
            return []
        ctx["reported"].add(key)
        return [_mk("HIGH", "Focus vào phần tử tàng hình",
                    "Focus rơi vào view có kích thước %dx%d px: %s" % (w, h, sig),
                    "View %s có diện tích quá nhỏ khiến người dùng mất dấu con trỏ" % sig,
                    "Đặt isFocusable=false cho view ẩn hoặc vạch phân cách",
                    frame_ref, t_offset, sig)]
    return []


def detect_dialog_focus_leak(ui_state, activity, ctx, frame_ref, t_offset):
    if not ui_state.get("has_dialog"):
        return []
    sig = ui_state.get("focused_sig", "NONE")
    bg_views = ("cardRoot", "schedCard", "liveList", "schedList", "phimMainList", "phimPoster", "heroPlay")
    if sig == "NONE" or not any(v in sig for v in bg_views):
        return []
    key = "DLGLEAK:%s" % sig
    if key in ctx.setdefault("reported", set()):
        return []
    ctx["reported"].add(key)
    return [_mk("HIGH", "Quản lý Focus Hộp Thoại",
                "Focus lọt xuống màn hình nền (%s) khi Dialog đang mở" % sig,
                "Hộp thoại đang hiển thị nhưng tiêu điểm D-pad vẫn nằm ở view nền",
                "Gọi requestFocus() vào nút mặc định của Dialog trong setOnShowListener",
                frame_ref, t_offset, sig)]


def detect_bad_text(ui_state, activity, ctx, frame_ref, t_offset):
    out = []
    for r_id, txt in ui_state.get("all_visible_texts", []):
        for pat in BAD_TEXT_PATTERNS:
            if re.search(pat, txt):
                key = "BADTEXT:%s:%s" % (r_id, txt[:20])
                if key in ctx.setdefault("reported", set()):
                    continue
                ctx["reported"].add(key)
                out.append(_mk("HIGH", "Hiển thị dữ liệu",
                               "Xuất hiện chuỗi lỗi/null thô trên giao diện: '%s'" % txt[:40],
                               "Node '%s' hiển thị văn bản '%s'" % (r_id, txt),
                               "Xử lý fallback chuỗi rỗng hoặc mặc định trước khi gán vào TextView",
                               frame_ref, t_offset, r_id))
    return out


def detect_fake_score(ui_state, activity, ctx, frame_ref, t_offset):
    """Giờ thi đấu đội lốt tỉ số + tỉ số phi lý (luật Task 5: >9 một đội hoặc tổng >12).
    CHỈ tố khi cùng giá trị trên cùng view đã thấy ở 2 observation khác nhau
    (ổn định qua thời gian). Đồng hồ trận đấu MM:SS đổi mỗi lần thấy —
    15:11 -> 17:23 -> 20:25 — nên không bao giờ tới lần thứ 2; tỉ số giả
    đứng yên thì tới. CI-T3 tố oan 3 đồng hồ ('15: 11', '17: 23', '23: 28')
    vì tố ngay lần đầu thấy. Evidence frame = lần thấy thứ 2 (frame trích
    dẫn phải chứa ĐÚNG giá trị bị tố — CI-T3 tố '17:23' trên frame chỉ có
    '15:11'). Lưu ý: all_visible_texts đã lọc node ngoài viewport ở
    device.dump_ui_state (CI-T4) nên giá trị tố luôn nằm trên màn hình."""
    out = []
    seen = ctx.setdefault("_score_seen", {})  # r_id -> (value, frame_ref, t_offset)
    # CI-T5: ngữ cảnh môn thể thao lấy từ TOÀN BỘ text dump lần này (VD
    # subtitle hero "Liên đoàn Bóng rổ Quốc gia Úc" ở cùng observation với
    # card tỉ số — CI-T4 detector không dùng nên tố oan 54:71).
    sport = _sport_context(ui_state.get("all_visible_texts", []))
    for r_id, txt in ui_state.get("all_visible_texts", []):
        clean = txt.strip()
        if "cardscore" not in r_id.lower() and "score" not in r_id.lower():
            continue
        m = re.match(r"^(\d{1,2})\s+[:\-]\s+(\d{1,2})$", clean)
        if not m:
            continue
        s1, s2 = int(m.group(1)), int(m.group(2))
        is_time = s1 in FAKE_SCORE_TIME[0] and s2 in FAKE_SCORE_TIME[1]
        is_implausible = s1 > 9 or s2 > 9 or (s1 + s2) > 12
        suspicious = is_time or is_implausible
        if not suspicious:
            # Giá trị bình thường (VD 0:0, 2:1): xóa ghi nhận cũ — view này
            # trước đó mang giá trị khác (đồng hồ đã đổi) thì không còn nợ.
            seen.pop(r_id, None)
            continue
        prev = seen.get(r_id)
        if prev is None or prev[0] != clean:
            # Lần đầu thấy giá trị này trên view này — ghi nhận, chưa tố.
            seen[r_id] = (clean, frame_ref, t_offset)
            continue
        # Cùng giá trị ở observation thứ 2 -> ổn định, không phải đồng hồ
        # đang chạy: tố, với frame lần này (chứa đúng giá trị bị tố).
        if is_time:
            key = "FAKE_SCORE_FROM_TIME:%s:%s" % (r_id, clean)
            if key in ctx.setdefault("reported", set()):
                continue
            ctx["reported"].add(key)
            out.append(_mk("HIGH", "Toàn vẹn tỷ số thể thao",
                           "Nghi vấn giờ thi đấu bị chuyển đổi thành tỷ số ảo: '%s'" % clean,
                           "View %s hiển thị tỉ số '%s' khớp với khung giờ phát sóng "
                           "(ổn định qua 2 lần quan sát, không phải đồng hồ đang chạy)"
                           % (r_id, clean),
                           "Bổ sung kiểm tra loại trừ giờ thi đấu trong DataNormalizer regex",
                           frame_ref, t_offset, r_id))
        elif sport == "basketball":
            # CI-T5: tỉ số bóng rổ thật (VD 54:71 NBL) — luật plausibility
            # bóng đá không áp được, BỎ QUA nhánh implausible. Nhánh giờ
            # đội lốt tỉ số ở trên vẫn tố, không phụ thuộc môn.
            continue
        else:
            # Không rõ môn (None) hoặc context bóng đá: giữ hành vi cũ —
            # tố theo luật plausibility (thẻ tỉ số nằm ở tab thể thao, mặc
            # định là bóng đá cho tới khi có từ khóa bóng rổ).
            key = "IMPLAUSIBLE_SCORE:%s:%s" % (r_id, clean)
            if key in ctx.setdefault("reported", set()):
                continue
            ctx["reported"].add(key)
            out.append(_mk("HIGH", "Toàn vẹn tỷ số thể thao",
                           "Tỷ số phi lý hiển thị trên thẻ trận: '%s'" % clean,
                           "View %s hiển thị '%s' — một đội > 9 hoặc tổng > 12 "
                           "(ổn định qua 2 lần quan sát)" % (r_id, clean),
                           "Ẩn tỉ số, hiện VS theo luật plausibility (Task 5)",
                           frame_ref, t_offset, r_id))
    return out


def detect_schedule_live_no_score(ui_state, activity, ctx, frame_ref, t_offset):
    """Hàng LIVE ở tab Lịch chỉ hiện giờ kickoff thay vì tỉ số (CI-T7 mục 9).
    Lỗi thật từ CI-T3, mắt thấy ở step_030 CI-T6: hàng LIVE hiện '18:30' /
    '18:35' (giờ đá) thay vì tỉ số đang diễn ra. Dump phẳng không gắn được
    badge với thẻ nên gom node theo HÀNG (tâm dọc bounds gần nhau, ±60px
    theo 1080p): hàng nào có badge LIVE + token giờ kickoff 'HH:MM'
    (không khoảng trắng — tỉ số app render dạng 'X : Y' có khoảng trắng)
    mà KHÔNG có token tỉ số thì tố. Hàng 'SẮP ĐÁ' hiện giờ kickoff là đúng
    nên loại. Cần thấy 2 lần quan sát (ổn định, tránh trạng thái chuyển
    tiếp lúc list đang cập nhật). Chỉ chạy khi dump có ngữ cảnh lịch
    (id chứa 'sched') để không tố nhầm list thể thao."""
    if "MainActivity" not in (activity or ""):
        return []
    nodes = ui_state.get("all_visible_nodes") or []
    if not any("sched" in (n.get("id") or "").lower() for n in nodes):
        return []
    _time_re = re.compile(r"^\d{1,2}:\d{2}$")
    _score_re = re.compile(r"^\d{1,2}\s+[:\-]\s+\d{1,2}$")
    _live_re = re.compile(r"\blive\b", re.IGNORECASE)
    # Gom node có bounds theo hàng (tâm dọc).
    rows = []
    for n in nodes:
        txt = (n.get("text") or "").strip()
        if not txt:
            continue
        m = re.findall(r"-?\d+", n.get("bounds") or "")
        if len(m) < 4:
            continue
        y1, y2 = int(m[1]), int(m[3])
        cy = (y1 + y2) / 2.0
        placed = False
        for r in rows:
            if abs(cy - r["cy"]) <= 60:
                r["nodes"].append((n, txt))
                r["cy"] = (r["cy"] * (len(r["nodes"]) - 1) + cy) / len(r["nodes"])
                placed = True
                break
        if not placed:
            rows.append({"cy": cy, "nodes": [(n, txt)]})
    out = []
    seen = ctx.setdefault("_sched_live_noscore_seen", {})
    for r in rows:
        texts = [t for _, t in r["nodes"]]
        low = [t.lower() for t in texts]
        if any("sắp đá" in t for t in low):
            continue  # trận chưa đá: hiện giờ kickoff là đúng
        if not any(_live_re.search(t) or "trực tiếp" in t for t in low):
            continue  # không phải hàng LIVE
        times = [t for t in texts if _time_re.match(t)]
        if not times:
            continue
        if any(_score_re.match(t) for t in texts):
            continue  # hàng đã có tỉ số -> đúng, không tố
        sig = " | ".join(sorted(texts))[:60]
        key = (times[0], sig)
        if key not in seen:
            seen[key] = (frame_ref, t_offset)
            continue  # lần đầu thấy — ghi nhận, chưa tố
        _fkey = "SCHED_LIVE_NOSCORE:%s:%s" % (times[0], sig[:30])
        if _fkey in ctx.setdefault("reported", set()):
            continue
        ctx["reported"].add(_fkey)
        out.append(_mk("HIGH", "Lịch thi đấu",
                       "Hàng LIVE chỉ hiện giờ kickoff thay vì tỉ số: '%s'" % times[0],
                       "Hàng LIVE '%s' hiện giờ kickoff '%s' mà không có tỉ số "
                       "(ổn định qua 2 lần quan sát)" % (sig[:40], times[0]),
                       "Hiện tỉ số trực tiếp cho trận đang diễn ra; giờ kickoff chỉ dùng cho trận chưa đá",
                       frame_ref, t_offset, ""))
    return out


def detect_row_overflow(ui_state, activity, ctx, frame_ref, t_offset):
    """Header '— N kênh' với N quá lớn trong một hàng (P0-7: TV360 75 kênh)."""
    out = []
    for r_id, txt in ui_state.get("all_visible_texts", []):
        m = re.search(r"(\d+)\s*kênh", txt)
        if not m:
            continue
        n = int(m.group(1))
        if n >= 30:
            key = "ROW_OVERFLOW:%s:%d" % (txt[:30], n)
            if key in ctx.setdefault("reported", set()):
                continue
            ctx["reported"].add(key)
            out.append(_mk("HIGH", "Truyền hình IPTV",
                           "Một hàng chứa %d kênh (quá tải, không duyệt nổi): '%s'" % (n, txt[:40]),
                           "Row header '%s' — hàng vượt ngưỡng 30 kênh" % txt,
                           "Tách hàng theo nhóm đài (F21: nhánh tên đài trước nhánh URL)",
                           frame_ref, t_offset, r_id))
    return out


def _img_size(frame_png):
    """(W, H) thật của frame. Ảnh lưu có thể 960x540, live 1920x1080."""
    try:
        from PIL import Image
        import io as _io
        return Image.open(_io.BytesIO(frame_png)).size
    except Exception:
        return (SCREEN_W, SCREEN_H)


def _band_real(band, W, H):
    """Band (x0,y0,x1,y1) hệ 1920x1080 -> pixel thật của ảnh."""
    x0, y0, x1, y1 = band
    return (int(x0 * W / SCREEN_W), int(y0 * H / SCREEN_H),
            int(x1 * W / SCREEN_W), int(y1 * H / SCREEN_H))


def _ocr_boxes_cached(ctx, frame_ref, frame_png, ocr, region):
    """Cache box OCR theo (frame, region): 3 detector OCR dùng chung 1 lần
    đọc, không OCR lại full frame mỗi detector."""
    key = (frame_ref, region)
    cache = ctx.setdefault("_ocr_cache", {})
    if key not in cache:
        cache[key] = ocr.read_boxes(frame_png, region=region) if region \
            else ocr.read_boxes(frame_png)
        if len(cache) > 12:
            cache.pop(next(iter(cache)))
    return cache[key]


def _ocr_due(ctx):
    """Gate OCR: đắt (~3.6s/band) nên chỉ chạy mỗi 3 bước hoặc khi runner ép
    (force_ocr). Không gate -> 136 bước × 2 lần OCR full frame ≈ 1 giờ."""
    ctx["steps_since_ocr"] = ctx.get("steps_since_ocr", 0) + 1
    if ctx.get("force_ocr") or ctx["steps_since_ocr"] >= 3:
        ctx["steps_since_ocr"] = 0
        ctx["force_ocr"] = False
        return True
    return False


def _plausible_text(t):
    """Box OCR có phải chữ thật không: ≥2 chữ cái Unicode và dài ≥3 ký tự.
    CI-T2: 10/11 finding là OCR đọc nhầm nội dung video thành box rác
    ('‹©', '1Ì', '¬c:', '7A', 'ý', 'D', '¬') — tất cả đều rớt guard này,
    trong khi chữ UI thật ('VTV4 HD', 'TRANG CHỦ', 'TRỰC…', 'bản', 'mãi')
    đều qua.
    CI-T3 (reviewer): 'LPđPfUHPBIHUALI' — 15 chữ cái liền nhau, 0 khoảng
    trắng — qua được guard cũ vì đủ chữ cái, nhưng không phải từ thật:
    + token dài nhất > 12 ký tự liền nhau -> rác (từ tiếng Việt/Anh trên UI
      này không dài thế; 'Socolive' 8, 'KenhLive' 8, 'TRANG CHỦ' có khoảng
      trắng). Token dài > 6 ký tự mà tỉ lệ nguyên âm < 0.15 -> rác.
      Guard nguyên âm KHÔNG áp cho token ngắn (acronym 'VTV4', 'HD' không
      có nguyên âm vẫn là chữ thật)."""
    t = (t or "").strip()
    if len(t) < 3 or sum(1 for ch in t if ch.isalpha()) < 2:
        return False
    _vowels = set("aeiouyàáâãèéêìíòóôõùúûüýăạảấầẩẫậắằẳẵặẹẻẽếềểễệỉịọỏốồổỗộớờởỡợụủứừửữựỳỵỷỹ")
    for tok in t.split():
        letters = [ch for ch in tok if ch.isalpha()]
        if len(tok) > 12:
            return False
        if len(letters) > 6:
            nv = sum(1 for ch in letters if ch.lower() in _vowels)
            if nv / len(letters) < 0.15:
                return False
    return True


def _same_baseline(a, b):
    """Hai box có cùng baseline/dòng OCR không (tâm dọc gần nhau)."""
    ha, hb = a["y1"] - a["y0"], b["y1"] - b["y0"]
    if ha <= 0 or hb <= 0:
        return False
    ca, cb = (a["y0"] + a["y1"]) / 2.0, (b["y0"] + b["y1"]) / 2.0
    return abs(ca - cb) <= max(3.0, 0.5 * min(ha, hb))


def _ocr_boxes_pairwise_overlap(boxes, band=None):
    """Cặp box chồng nhau đáng kể (IoU trên box nhỏ > 0.3) trong vùng band.
    BỎ QUA cặp trùng OCR (CI-T6 mục 1): box nhỏ ≥90% nằm trong box lớn VÀ
    cùng baseline/dòng — đó là 1 text bị tesseract PSM 11 trả trùng 2 lần,
    không phải 2 text đè nhau (FP "Xem"/"ngay" 93% ở step_010 CI-T5)."""
    if band:
        x0, y0, x1, y1 = band
        boxes = [b for b in boxes
                 if not (b["x1"] < x0 or b["x0"] > x1 or b["y1"] < y0 or b["y0"] > y1)]
    hits = []
    for i in range(len(boxes)):
        for j in range(i + 1, len(boxes)):
            a, b = boxes[i], boxes[j]
            if a["text"] == b["text"]:
                continue
            ov = _boxes_overlap(a, b)
            if ov > 0.30:
                if ov >= 0.90 and _same_baseline(a, b):
                    continue  # trùng OCR cùng dòng, không phải chữ đè chữ
                hits.append((a, b, ov))
    return hits


def detect_text_overlap(frame_png, ui_state, activity, ctx, frame_ref, t_offset, ocr):
    """Chữ đè chữ (P0-3 hero đè nav) qua OCR boxes từng BAND (không OCR full
    frame — đắt). OCR không có -> ghi skipped, không kết luận.
    Guard chống false positive (đúc từ vòng test):
    - Band nav BỎ QUA trên frame player: nội dung video (phụ đề phim, credit)
      làm OCR đọc nhầm thành chữ app.
    - Ngưỡng chồng 0.40 + tỉ lệ chiều cao 2 box <= 2.0: loại box OCR vỡ
      (nhãn nút kề nhau bị đọc tràn sang nhau, VD 'THANH' vs 'Phụ' 31%).
    - Bỏ box chỉ toàn ký tự lạ (không có chữ/số) — nhiễu OCR.
    Lưu ý: OCR KHÔNG tách được 2 lớp chữ chồng khít (P0-3 step_065: tesseract
    gộp 'VTV4 HD' vào nav, không ra box riêng) — P0-3 vẫn cần vision xác minh;
    detector này là đường phụ."""
    if not ocr.available():
        ctx["ocr_skipped"] = ctx.get("ocr_skipped", 0) + 1
        return []
    is_player = "PlayerActivity" in (activity or "") or "WebPlayerActivity" in (activity or "")
    osd = ui_state.get("osd_visible")
    W, H = _img_size(frame_png)
    out = []
    for band, name in ((NAV_BAND, "top nav"), (HERO_BAND, "hero"),
                       (BOTTOM_BAR_BAND, "seekbar/hàng nút")):
        if name == "top nav" and is_player:
            continue
        # CI-T5 mục 6: hero band chỉ soi mỗi 2 lần OCR-due (ctx flag do
        # run_all_detectors đặt) — hero là band đắt nhất (~45–60% thời gian
        # OCR 3 band) mà 2 vòng CI-T3/CI-T4 không bắt thêm lỗi hero nào.
        if name == "hero" and not ctx.get("hero_ocr_due", True):
            continue
        # Band hero trong player là nội dung video (phim đang phát) — OCR
        # đọc nhầm thành chữ app, như band nav. Chỉ soi hero ngoài player.
        if name == "hero" and is_player:
            continue
        # Band dưới trên frame player khi OSD ẨN chỉ có nội dung video
        # (phụ đề phim, credit) — OCR đọc nhầm thành chữ app (CI-T2: finding
        # 7-10). osd=None (không rõ, vd replay dữ liệu cũ) thì vẫn chạy.
        if name == "seekbar/hàng nút" and is_player and osd is False:
            continue
        boxes = _ocr_boxes_cached(ctx, frame_ref, frame_png, ocr, band)
        if len(boxes) < 2:
            continue
        # CI-T6 mục 1: gộp các box cùng 1 dòng OCR thành 1 cụm TRƯỚC khi so
        # chồng (ocr.cluster_same_line_boxes) — "Xem"+"ngay" thành 1 cụm
        # "Xem ngay", không còn cặp để tố. Cụm là list mới, cache box thô
        # không đổi nên detector clipped/subtitle không bị ảnh hưởng.
        _cluster = getattr(ocr, "cluster_same_line_boxes", None)
        if _cluster is not None:
            boxes = _cluster(boxes)
            if len(boxes) < 2:
                continue
        for a, b, ov in _ocr_boxes_pairwise_overlap(boxes, _band_real(band, W, H)):
            if ov <= 0.40:
                continue
            ha, hb = a["y1"] - a["y0"], b["y1"] - b["y0"]
            if ha <= 0 or hb <= 0 or max(ha, hb) / min(ha, hb) > 2.0:
                continue
            if not _plausible_text(a["text"]) or not _plausible_text(b["text"]):
                continue
            key = "OVERLAP:%s:%s:%s" % (name, a["text"], b["text"])
            if key in ctx.setdefault("reported", set()):
                continue
            ctx["reported"].add(key)
            out.append(_mk("HIGH", "Chữ đè chữ (%s)" % name,
                           "Chữ '%s' đè lên '%s' (chồng %.0f%%)" % (a["text"], b["text"], ov * 100),
                           "Vùng %s: box %s %s vs %s %s" % (name, a["text"], (a["x0"], a["y0"], a["x1"], a["y1"]),
                                                          b["text"], (b["x0"], b["y0"], b["x1"], b["y1"])),
                           "Chừa top inset/scrim cho hero; neo phụ đề lên trên seekbar + hàng nút khi OSD hiện",
                           frame_ref, t_offset, ui_state.get("focused_sig", "")))
    return out


def detect_clipped_text(frame_png, ui_state, activity, ctx, frame_ref, t_offset, ocr):
    """Chữ bị cắt: từ OCR kết thúc '…' chạm mép phải, hoặc text dài tràn bounds (P0-4).
    CHỈ chạy trên frame player: ở màn lưới, '…' là cắt ngắn mô tả bình thường
    (VD step_065: 'không...' trong card kênh) — không phải lỗi.
    Dùng box band dưới đã cache (nút player nằm ở đó), so mép phải theo chiều
    rộng THẬT của ảnh."""
    if "PlayerActivity" not in (activity or "") and "WebPlayerActivity" not in (activity or ""):
        return []
    if not ocr.available():
        ctx["ocr_skipped"] = ctx.get("ocr_skipped", 0) + 1
        return []
    # OSD ẩn -> band dưới chỉ có nội dung video, không có chữ UI nào để cắt.
    # osd=None (không rõ, vd replay dữ liệu cũ) thì vẫn chạy.
    if ui_state.get("osd_visible") is False:
        return []
    W, H = _img_size(frame_png)
    boxes = _ocr_boxes_cached(ctx, frame_ref, frame_png, ocr, BOTTOM_BAR_BAND)
    out = []
    for b in boxes:
        txt = b["text"]
        # Guard mép/độ cao (CI-T2 finding 1-2): box cao 0px ở y=1079 và box
        # rộng cả màn hình (1920px) đều là nhiễu OCR ở mép, không phải chữ.
        if (b["y1"] - b["y0"]) < 4 or (b["x1"] - b["x0"]) < 4:
            continue
        if (b["x1"] - b["x0"]) > W * 0.80:
            continue
        if txt.endswith("…") or txt.endswith("..."):
            # Token quá ngắn ('1a…') không đủ bằng chứng là chữ bị cắt thật.
            if len(txt.rstrip("….").strip()) < 4:
                continue
            near_right = b["x1"] >= W * 0.92
            in_bottom_bar = b["y0"] >= _band_real(BOTTOM_BAR_BAND, W, H)[1]
            if near_right or in_bottom_bar:
                key = "CLIPPED:%s:%d,%d" % (txt, b["x0"], b["y0"])
                if key in ctx.setdefault("reported", set()):
                    continue
                ctx["reported"].add(key)
                out.append(_mk("HIGH", "Chữ bị cắt",
                               "Chữ bị cắt cụt: '%s'" % txt,
                               "Từ '%s' kết thúc bằng '…' tại (%d,%d)-(%d,%d)%s" % (
                                   txt, b["x0"], b["y0"], b["x1"], b["y1"],
                                   " — sát mép phải" if near_right else " — trong hàng nút dưới"),
                               "Cân lại hàng nút / cho nút đủ chỗ, không để chữ chạm mép",
                               frame_ref, t_offset, ui_state.get("focused_sig", "")))
    return out


def detect_subtitle_seekbar_overlap(frame_png, ui_state, activity, ctx, frame_ref, t_offset, ocr):
    """Phụ đề đè lên thanh seekbar (P0-5) bằng HÌNH HỌC OCR, không cần vision:
    nhãn giờ seekbar ('03:07', '21:06') cho ra hàng seekbar; box phụ đề nào
    có chữ (không phải nhãn giờ) mà cắt ngang hàng đó là lỗi. Dùng box band
    dưới đã cache — không tốn thêm lần OCR nào."""
    if "PlayerActivity" not in (activity or "") and "WebPlayerActivity" not in (activity or ""):
        return []
    if not ocr.available():
        ctx["ocr_skipped"] = ctx.get("ocr_skipped", 0) + 1
        return []
    # Seekbar chỉ tồn tại khi OSD hiện; OSD ẩn thì không có gì để phụ đề đè.
    # osd=None (không rõ, vd replay dữ liệu cũ) thì vẫn chạy.
    if ui_state.get("osd_visible") is False:
        return []
    boxes = _ocr_boxes_cached(ctx, frame_ref, frame_png, ocr, BOTTOM_BAR_BAND)
    if not boxes:
        return []
    time_re = re.compile(r"^\d{1,2}:\d{2}(:\d{2})?$")
    times = [b for b in boxes if time_re.match(b["text"].strip())]
    if not times:
        return []  # không thấy mốc seekbar -> không kết luận (không bịa)
    row_top = min(b["y0"] for b in times)
    row_bottom = max(b["y1"] for b in times)
    subs = []
    for b in boxes:
        t = b["text"].strip()
        if time_re.match(t):
            continue  # nhãn giờ là một phần của hàng seekbar, không phải phụ đề
        # Phụ đề tiếng Việt có từ 2 ký tự ('há', 'đi') nên chỉ cần ≥2 chữ cái,
        # không yêu cầu dài ≥3 như chữ UI (kẻo mất P0-5 thật ở replay).
        if sum(1 for ch in t if ch.isalpha()) < 2:
            continue
        if b["y0"] < row_bottom and b["y1"] > row_top:
            subs.append(b)
    if len(subs) < 2:
        return []  # cần >= 2 box chữ cắt ngang để loại nhiễu OCR 1 box
    key = "SUBSEEK:%d:%s" % (int(row_top / 10), subs[0]["text"][:12])
    if key in ctx.setdefault("reported", set()):
        return []
    ctx["reported"].add(key)
    return [_mk("HIGH", "Player VOD", "Phụ đề đè lên thanh seekbar",
                "Phụ đề cắt ngang hàng seekbar (y %d-%d): %s" % (
                    row_top, row_bottom,
                    ", ".join("'%s'" % b["text"] for b in subs[:4])),
                "Khi OSD hiện, neo phụ đề lên trên seekbar + hàng nút (tính cả tvBottomBar)",
                frame_ref, t_offset, ui_state.get("focused_sig", ""))]


def detect_wrong_logo(ui_state, activity, ctx, frame_ref, t_offset):
    """Logo kênh sai (P0-8) không kết luận được từ UI dump: đẩy vào hàng đợi
    vision. Trả finding dạng 'needs_vision' — judge KHÔNG tính là defect
    cho tới khi vision xác minh."""
    texts = dict(ui_state.get("all_visible_texts", []))
    # ChannelBadge fallback text thường là node text logo; đối chiếu tên kênh
    # với chuỗi logo khi cả hai cùng hiện trên một card là việc của vision.
    # Ở đây chỉ ghi nhận "có cặp logo+tên để soi" khi thấy nhiều kênh VTV.
    names = [t for _, t in ui_state.get("all_visible_texts", []) if t.startswith("VTV")]
    if len(names) >= 3:
        ctx.setdefault("logo_check_frames", []).append(
            {"frame": frame_ref, "t": t_offset, "activity": activity})
    return []


def run_all_detectors(frame_png, ui_state, activity, ctx, frame_ref, t_offset, ocr):
    """Chạy toàn bộ detector cục bộ trên một stable frame. Trả (findings, vision_queue).
    Detector OCR (text_overlap / clipped / subtitle-seekbar) chỉ chạy khi
    _ocr_due (mỗi 3 bước hoặc force_ocr) và dùng chung cache box theo band —
    OCR full frame mỗi bước sẽ tốn ~26s/bước, phá mục tiêu <30 phút."""
    findings = []
    findings += detect_blank(frame_png, ui_state, activity, ctx, frame_ref, t_offset)
    findings += detect_focus_loss(ui_state, activity, ctx, frame_ref, t_offset)
    findings += detect_player_focus_loss(ui_state, activity, ctx, frame_ref, t_offset)
    findings += detect_focus_trap(ui_state, activity, ctx, frame_ref, t_offset, frame_png)
    findings += detect_offscreen_or_zero_focus(ui_state, activity, ctx, frame_ref, t_offset)
    findings += detect_dialog_focus_leak(ui_state, activity, ctx, frame_ref, t_offset)
    findings += detect_bad_text(ui_state, activity, ctx, frame_ref, t_offset)
    findings += detect_fake_score(ui_state, activity, ctx, frame_ref, t_offset)
    findings += detect_schedule_live_no_score(ui_state, activity, ctx, frame_ref, t_offset)
    findings += detect_row_overflow(ui_state, activity, ctx, frame_ref, t_offset)
    if _ocr_due(ctx):
        # CI-T5 mục 6: hero band là band OCR đắt nhất — đo local trên frame
        # thật CI-T4 (960x540): hero 1.1–2.0s trong tổng 2.5–3.4s cho 3 band
        # (~45–60%), trong khi CI-T3+CI-T4 hero OCR không bắt thêm lỗi nào
        # (OCR không tách được 2 lớp chữ chồng — lỗi đó sang vision, mục 7).
        # Chỉ soi hero mỗi 2 lần OCR-due (tức mỗi ~6 bước); nav + band dưới
        # giữ nguyên mỗi lần due. Tiết kiệm ~25% thời gian detect mỗi chu kỳ.
        ctx["hero_ocr_count"] = ctx.get("hero_ocr_count", 0) + 1
        ctx["hero_ocr_due"] = (ctx["hero_ocr_count"] % 2 == 1)
        findings += detect_text_overlap(frame_png, ui_state, activity, ctx, frame_ref, t_offset, ocr)
        findings += detect_clipped_text(frame_png, ui_state, activity, ctx, frame_ref, t_offset, ocr)
        findings += detect_subtitle_seekbar_overlap(frame_png, ui_state, activity, ctx, frame_ref, t_offset, ocr)
    detect_wrong_logo(ui_state, activity, ctx, frame_ref, t_offset)
    return findings

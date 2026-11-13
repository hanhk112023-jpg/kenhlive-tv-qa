#!/usr/bin/env python3
"""KenhLive Realtime QA — tầng thiết bị (device layer, tự chứa).

KHÔNG import autonomous_ai_qa.py (file đó đang bị fix loop 1 sửa song song).
Các lệnh adb/uiautomator ở đây chép lại từ các pattern đã chứng minh trong
harness cũ (AndroidTVDevice/Probes) và giữ nguyên ngữ nghĩa.
"""
import io
import json
import math
import re
import subprocess
import time
import xml.etree.ElementTree as ET

try:
    from PIL import Image, ImageChops, ImageStat
except ImportError:  # pragma: no cover
    Image = ImageChops = ImageStat = None

PKG = "com.kenhlive.tv"

KEY_MAP = {
    "UP": 19, "DPAD_UP": 19, "DOWN": 20, "DPAD_DOWN": 20,
    "LEFT": 21, "DPAD_LEFT": 21, "RIGHT": 22, "DPAD_RIGHT": 22,
    "ENTER": 23, "DPAD_CENTER": 23, "OK": 23,
    "BACK": 4, "HOME": 3, "MENU": 82,
    "PLAY_PAUSE": 85, "PLAY": 126, "PAUSE": 127,
    "REWIND": 89, "FAST_FORWARD": 90,
    "CHANNEL_UP": 166, "CHANNEL_DOWN": 167,
    "PAGE_UP": 92, "PAGE_DOWN": 93,
    "A": 29, "KEY_A": 29, "B": 30, "KEY_B": 30,
    "RED": 183, "PROG_RED": 183, "GREEN": 184, "PROG_GREEN": 184,
    "YELLOW": 185, "PROG_YELLOW": 185, "BLUE": 186, "PROG_BLUE": 186,
    "0": 7, "1": 8, "2": 9, "3": 10, "4": 11, "5": 12, "6": 13,
    "7": 14, "8": 15, "9": 16,
}

# Từ khóa fallback xác định tab khi nav-selected không có trong dump.
TAB_KEYWORDS = [
    (6, ["herofilmplay", "herofilmsave", "homebillboard", "heropager"]),
    (5, ["phim", "nguonc", "btnheroplay", "apple pill", "phim bộ", "phim lẻ", "tiếp tục xem", "rạp phim tại gia"]),
    (4, ["settingslist", "cài đặt", "chất lượng video", "báo lỗi"]),
    (3, ["searchinput", "resultlist", "tìm kiếm"]),
    (2, ["iptv", "kênh tv", "channel", "vtv", "htv"]),
    (1, ["schedlist", "schedcard", "lịch thi đấu", "hôm nay", "ngày mai"]),
    (0, ["livelist", "cardroot", "socolive", "colatv", "gà vàng", "khán đài", "trực tiếp"]),
]
NAV_ID_TO_TAB = {
    "nav_home": 6, "nav_live": 0, "nav_schedule": 1, "nav_iptv": 2,
    "nav_search": 3, "nav_settings": 4, "nav_phim": 5,
}


def sh(cmd, timeout=30):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return (r.stdout or "") + (r.stderr or "")
    except Exception as e:
        return "__ERR__ %s" % e


def _fit_circle(points):
    """Fit vòng tròn (Kasa, bình phương tối thiểu) qua các điểm.
    Trả (cx, cy, r) hoặc None khi điểm suy biến (thẳng hàng / r <= 0).
    Dùng cho đường nhận vòng focus tròn: vòng bị JPEG làm mờ có thể vỡ
    thành nửa trên/dưới — bbox của nửa vòng không phải bbox của vòng nên
    không fit ellipse theo bbox được, phải fit theo điểm."""
    n = len(points)
    if n < 8:
        return None
    sx = sy = sxx = syy = sxy = sz = sxz = syz = 0.0
    for (x, y) in points:
        z = x * x + y * y
        sx += x
        sy += y
        sxx += x * x
        syy += y * y
        sxy += x * y
        sz += z
        sxz += x * z
        syz += y * z
    # [sxx sxy sx; sxy syy sy; sx sy n] [D;E;F] = [-sxz;-syz;-sz]
    a = [[sxx, sxy, sx, -sxz], [sxy, syy, sy, -syz], [sx, sy, float(n), -sz]]
    for i in range(3):
        piv = max(range(i, 3), key=lambda r: abs(a[r][i]))
        if abs(a[piv][i]) < 1e-9:
            return None
        a[i], a[piv] = a[piv], a[i]
        for r in range(i + 1, 3):
            f = a[r][i] / a[i][i]
            for c in range(i, 4):
                a[r][c] -= f * a[i][c]
    sol = [0.0] * 3
    for i in (2, 1, 0):
        sol[i] = (a[i][3] - sum(a[i][j] * sol[j] for j in range(i + 1, 3))) / a[i][i]
    d, e, f = sol
    cx, cy = -d / 2.0, -e / 2.0
    r2 = (d * d + e * e) / 4.0 - f
    if r2 <= 0:
        return None
    return cx, cy, math.sqrt(r2)


class RealtimeDevice:
    """ADB + uiautomator + screencap, không phụ thuộc model AI."""

    def __init__(self, serial=None, pkg=PKG):
        self.serial = serial
        self.adb = "adb -s %s" % serial if serial else "adb"
        self.pkg = pkg
        self.action_history = []
        self._reported_anomaly_keys = set()
        self._last_logcat_len = 0

    # -- app lifecycle -------------------------------------------------
    def launch_app(self):
        t0 = time.time()
        sh("%s shell am start -n %s/.MainActivity" % (self.adb, self.pkg))
        while time.time() - t0 < 25:
            if self.is_app_in_foreground():
                return round((time.time() - t0) * 1000)
            time.sleep(0.2)
        return -1

    def is_app_in_foreground(self):
        out = sh("%s shell dumpsys window 2>/dev/null | grep -m1 mCurrentFocus" % self.adb)
        return self.pkg in out

    def current_activity(self):
        out = sh("%s shell dumpsys activity activities 2>/dev/null | grep -m1 -E 'mResumedActivity|topResumedActivity'" % self.adb)
        m = re.search(r"([A-Za-z0-9_.]+)/([.A-Za-z0-9_]+)", out)
        return "%s/%s" % (m.group(1), m.group(2)) if m else "?"

    # -- input ---------------------------------------------------------
    def _note(self, label):
        self.action_history.append(label)
        if len(self.action_history) > 20:
            self.action_history.pop(0)

    def send_key(self, key_name):
        code = KEY_MAP.get((key_name or "DPAD_DOWN").upper(), 20)
        sh("%s shell input keyevent %d" % (self.adb, code))
        self._note(key_name)

    def send_long_press(self, key_name="OK", duration_ms=1500):
        code = KEY_MAP.get((key_name or "OK").upper(), 23)
        res = sh("%s shell input keyevent --longpress %d" % (self.adb, code))
        if "__ERR__" in res or "unrecognized" in res.lower() or "error" in res.lower():
            state = self.dump_ui_state()
            b = state.get("focused_bounds")
            if b:
                mm = re.match(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]", b)
                if mm:
                    x1, y1, x2, y2 = map(int, mm.groups())
                    sh("%s shell input swipe %d %d %d %d %d" % (self.adb, (x1 + x2) // 2, (y1 + y2) // 2, (x1 + x2) // 2, (y1 + y2) // 2, duration_ms))
                else:
                    sh("%s shell input swipe 960 540 960 540 %d" % (self.adb, duration_ms))
            else:
                sh("%s shell input swipe 960 540 960 540 %d" % (self.adb, duration_ms))
        self._note("LONG_PRESS(%s)" % key_name)

    def send_keypad_digits(self, digits_str):
        for ch in str(digits_str):
            if ch in KEY_MAP:
                sh("%s shell input keyevent %d" % (self.adb, KEY_MAP[ch]))
                time.sleep(0.18)
        self._note("KEYPAD(%s)" % digits_str)

    def input_text(self, text):
        safe = re.sub(r"[^a-zA-Z0-9_-]", "", text)
        sh('%s shell input text "%s"' % (self.adb, safe))
        self._note("TEXT(%s)" % text)

    def switch_tab(self, tab_index):
        sh("%s shell am start -n %s/.MainActivity --ei tab %d -f 0x04000000" % (self.adb, self.pkg, int(tab_index)))
        self._note("SWITCH_TAB(%d)" % int(tab_index))

    def open_home(self):
        self.switch_tab(6)
        self._note("OPEN_HOME_HUB")

    def launch_web_player(self):
        """Deep-link open=webplayer (F44): MainActivity tự resolve tập embed thật."""
        sh("%s shell am start -n %s/.MainActivity --es open webplayer" % (self.adb, self.pkg))
        self._note("LAUNCH_WEB_PLAYER")

    def launch_vod_player(self):
        """Deep-link open=vodplayer: PlayerActivity mặt VOD, tập m3u8 thật."""
        sh("%s shell am start -n %s/.MainActivity --es open vodplayer" % (self.adb, self.pkg))
        self._note("LAUNCH_VOD_PLAYER")

    def launch_multiview(self):
        """Mở thẳng MultiViewActivity (explicit intent; activity không có
        intent-filter nên không đi qua deep-link MainActivity). Mission
        MISSION_MULTIVIEW_DIRECTED: MultiView tự nạp trận live thật, không
        cần extra (không trận live -> trạng thái trống trung thực)."""
        sh("%s shell am start -n %s/.MultiViewActivity" % (self.adb, self.pkg))
        self._note("LAUNCH_MULTIVIEW")

    # -- perception inputs ---------------------------------------------
    def screencap_bytes(self):
        try:
            raw = subprocess.run(("%s exec-out screencap -p" % self.adb).split(),
                                 capture_output=True, timeout=20).stdout
            return raw if len(raw) > 5000 else None
        except Exception:
            return None

    @staticmethod
    def is_blank(png_bytes):
        if not png_bytes or not Image or not ImageStat:
            return False
        try:
            im = Image.open(io.BytesIO(png_bytes)).convert("L").resize((64, 64))
            stat = ImageStat.Stat(im)
            return stat.stddev[0] < 4.0 or stat.mean[0] < 2.0
        except Exception:
            return False

    @staticmethod
    def pixel_diff(png_a, png_b, size=(160, 90)):
        """% khác biệt trung bình giữa 2 frame (PIL thuần). -1.0 nếu lỗi."""
        if not png_a or not png_b or not Image:
            return -1.0
        try:
            a = Image.open(io.BytesIO(png_a)).convert("RGB").resize(size)
            b = Image.open(io.BytesIO(png_b)).convert("RGB").resize(size)
            diff = ImageChops.difference(a, b).convert("L")
            return float(ImageStat.Stat(diff).mean[0] / 255.0 * 100.0)
        except Exception:
            return -1.0

    @staticmethod
    def video_scene_diff(png_a, png_b):
        """% khác biệt trung bình trong VÙNG VIDEO của WebPlayer, LOẠI TRỪ
        chrome app (top OSD ~15% trên, bottom control ~22% dưới) và hộp
        giữa (~40% giữa màn: logo 'io' + vòng ▶ — F63 trial 10 w_011–w_017:
        logo 'io' xoay tạo motion 5.25 nhưng player đóng băng 00:10/46:01,
        logo xoay KHÔNG được tính là đổi cảnh). Trả -1.0 khi không đo được."""
        if not png_a or not png_b or not Image:
            return -1.0
        try:
            a = Image.open(io.BytesIO(png_a)).convert("RGB").resize((480, 270))
            b = Image.open(io.BytesIO(png_b)).convert("RGB").resize((480, 270))
            diff = ImageChops.difference(a, b).convert("L")
            W, H = diff.size
            # Band video giữ lại: x 8%-92%, y 15%-78% (trừ top OSD +
            # bottom control bar của app lẫn control của embed).
            bx0, by0, bx1, by1 = (int(0.08 * W), int(0.15 * H),
                                 int(0.92 * W), int(0.78 * H))
            # Hộp giữa loại trừ: x 30%-70%, y 28%-72% (logo 'io' + nút play).
            cx0, cy0, cx1, cy1 = (int(0.30 * W), int(0.28 * H),
                                 int(0.70 * W), int(0.72 * H))
            band = diff.crop((bx0, by0, bx1, by1))
            center = diff.crop((cx0, cy0, cx1, cy1))
            mb = ImageStat.Stat(band).mean[0]
            mc = ImageStat.Stat(center).mean[0]
            ab = band.size[0] * band.size[1]
            ac = center.size[0] * center.size[1]
            kept = (mb * ab - mc * ac) / max(1, ab - ac)
            return float(kept / 255.0 * 100.0)
        except Exception:
            return -1.0

    def webplayer_progress_probe(self):
        """Vị trí phát THẬT của WebPlayerActivity — đọc giá trị mà probe JS
        của app tự đo, KHÔNG qua OCR đồng hồ.

        WebPlayerActivity chạy queryPlaybackPosition mỗi 3s
        (webPlaybackProbeJs: <video>.currentTime*1000 / JWPlayer.
        getPosition()*1000 -> pos ms, kèm paused/duration) và khi
        currentPositionMs > 5s gọi saveCurrentProgress ->
        WatchHistoryManager.saveProgressAsync ghi
        watch_history.position_ms vào SQLite kenhlive_cinema.db mỗi lần
        probe. Harness đọc lại đúng position_ms đó qua `run-as` (QA cài
        APK debug nên run-as hoạt động) — cùng một con số probe JS đo được.

        Trả dict {pos_ms, duration_ms, slug, episode_slug,
        last_watched_at} khi đọc được DB — pos_ms=None nếu đọc được nhưng
        chưa có hàng tiến độ nào (player chưa lưu lần nào). Trả None khi
        KÊNH ĐỌC LỖI (run-as từ chối / DB chưa tồn tại / parse hỏng sau 2
        lần thử) — phân biệt 'không đo được' (gate -> UNVERIFIED) với
        'đo được mà vị trí không tăng' (gate -> FAIL đóng băng)."""
        import os
        import sqlite3
        import tempfile

        def _read():
            raw = subprocess.run(
                ("%s exec-out run-as %s cat /data/data/%s/databases/kenhlive_cinema.db"
                 % (self.adb, self.pkg, self.pkg)).split(),
                capture_output=True, timeout=30).stdout
            if len(raw) < 100 or raw[:16] != b"SQLite format 3\x00":
                return "NO_DB"
            fd, tmp = tempfile.mkstemp(suffix=".db")
            try:
                with os.fdopen(fd, "wb") as f:
                    f.write(raw)
                con = sqlite3.connect(tmp)
                try:
                    row = con.execute(
                        "SELECT slug, episode_slug, position_ms, duration_ms, "
                        "last_watched_at FROM watch_history "
                        "ORDER BY last_watched_at DESC LIMIT 1").fetchone()
                finally:
                    con.close()
            finally:
                try:
                    os.unlink(tmp)
                except OSError:
                    pass
            if row is None:
                return {"pos_ms": None, "duration_ms": None, "slug": None,
                        "episode_slug": None, "last_watched_at": None}
            return {"pos_ms": int(row[2]) if row[2] else None,
                    "duration_ms": int(row[3]) if row[3] else None,
                    "slug": row[0], "episode_slug": row[1],
                    "last_watched_at": int(row[4]) if row[4] else None}

        for _ in range(2):
            try:
                res = _read()
                return None if res == "NO_DB" else res
            except Exception:
                continue
        return None

    def dump_ui_state(self):
        """Đọc cây UI qua uiautomator. Trả dict dùng chung cho gate/detector/driver.
        Gộp rm + dump + cat vào MỘT lần gọi adb (CI-T2: mỗi observe gọi 3 lần
        adb riêng cho dump, cộng với dumpsys activity — nút thắt tốc độ)."""
        xml_text = sh("%s shell 'rm -f /sdcard/uidump.xml; uiautomator dump /sdcard/uidump.xml >/dev/null 2>&1; cat /sdcard/uidump.xml' 2>/dev/null" % self.adb, timeout=20)
        if "<hierarchy" not in xml_text:
            time.sleep(0.25)
            xml_text = sh("%s shell 'uiautomator dump --compressed /sdcard/uidump.xml >/dev/null 2>&1; cat /sdcard/uidump.xml' 2>/dev/null" % self.adb, timeout=20)

        focused_sig, focused_text, focused_bounds = "NONE", "", None
        focusable_nodes, summary_lines, all_visible_texts = [], [], []
        all_visible_nodes = []  # CI-T5: (id, text, bounds) để driver biết
        # badge "SẮP ĐÁ"/"LIVE" có nằm trên cùng thẻ với view đang focus không
        # (chỉ có r_id + text thì không gắn được badge với thẻ).
        selected_ids, has_dialog = [], False
        dialog_ids = []
        dialog_bounds = None  # H15: bounds hợp của dialog đang mở (None nếu không có)
        # ID dialog đã biết (cập nhật sau CI-T1): btnCloseFeedback = nút đóng
        # của dialog chào mừng "THÔNG BÁO" lần đầu; dialogBtnClose = nút đóng
        # của dialog chọn tập. dialog_ids trả về để driver phân biệt dialog
        # chặn (welcome) với dialog đích (roomList/dialogEpisodesGrid/...).
        # CI-T7 mục 1: thêm id của MatchDetailPanel — cái mở ra khi bấm thẻ
        # trận là PANEL chi tiết (LiveFragment.openGroupPicker -> dialog
        # dialog_match_detail.xml, KHÔNG phải RoomPickerDialog độc lập).
        # Gốc rễ CI-T6 (ROOM_PICKER + PLAYER_STREAMING): không id panel nào
        # có trong set này nên has_dialog=False suốt lúc panel mở -> driver
        # bấm OK tiếp -> mở player. 13 id panel* lấy bằng grep layout
        # dialog_match_detail.xml (chỉ đọc app source); ngoài ra coi mọi id
        # bắt đầu bằng "panel" hoặc "blvCardRoot" (card phòng trong panel,
        # focus lúc panel mở — step_011 CI-T6) là dialog đang mở. An toàn:
        # không id layout nào khác bắt đầu bằng "panel" (channelCarouselPanel
        # / sportOptionsPanel đều KẾT THÚC bằng "Panel").
        # H2 (trial 5 run 43183031119): 'episodeList' cũ KHÔNG tồn tại
        # trong app (grep toàn bộ res/layout và java/ đều không có) — id
        # THẬT của dialog chọn tập (dialog_film_episodes.xml) là
        # dialogEpisodesGrid + các id dialogFilm*/dialogBtn*; dialogBtnClose
        # nằm ở footer, bị cắt khỏi màn hình khi dialog cao hơn màn hình
        # (step_051: không thấy nút Đóng/Lưu Phim) nên không được trông vào
        # mỗi mình nó — các id phần trên dialog (tiêu đề, poster, meta,
        # lưới tập) luôn có trong dump khi dialog mở. Ngoài set tường minh,
        # mọi id bắt đầu bằng "dialog" đều tính là dialog: grep toàn bộ
        # res/layout cho thấy mọi @+id/dialog* đều thuộc layout dialog
        # (dialogFilm* = EpisodePickerDialog, dialogLeague = RoomPicker,
        # dialogTitle = dialog chào mừng) — không id màn thường nào bắt
        # đầu bằng "dialog".
        dialog_id_set = ("dialogTitle", "roomList", "ivTelegramQr",
                         "btnOpenTelegram", "alertTitle", "btnCloseFeedback",
                         "dialogBtnClose",
                         "dialogFilmBackdrop", "dialogFilmPoster",
                         "dialogFilmTitle", "dialogFilmOrigTitle",
                         "dialogFilmBadgesRow", "dialogFilmMeta",
                         "dialogFilmCrew", "dialogFilmDesc",
                         "dialogServersRow", "dialogChunksRow",
                         "dialogEpisodesGrid", "dialogNoEpisodes",
                         "dialogLoading", "dialogBtnPlay",
                         "dialogBtnFavorite", "dialogBtnDeleteHistory",
                         "panelLeague", "panelBadge", "panelHostName",
                         "panelHostIcon", "panelScore", "panelClock",
                         "panelGuestIcon", "panelGuestName", "panelBlvTitle",
                         "panelBlvList", "panelSameTimeTitle",
                         "panelSameTimeList", "panelPlay")
        if "<hierarchy" in xml_text:
            try:
                start = xml_text.find("<hierarchy")
                end = xml_text.rfind("</hierarchy>")
                if start != -1 and end != -1:
                    xml_text = xml_text[start:end + len("</hierarchy>")]
                root = ET.fromstring(xml_text.strip())
                # H15 (judge-guard): bounds HỢP của toàn bộ node thuộc
                # dialog đang mở — node khớp tiêu chí dialog + MỌI node con
                # cháu của nó (đệ quy, vì dump là cây XML lồng nhau). Dùng
                # để kiểm claim 'focus lọt xuống nền khi dialog mở': focus
                # nằm TRONG dialog_bounds nghĩa là focus đang ở nội dung
                # dialog (VD mục 'Trận cùng giờ' của chính dialog BLV),
                # không phải lọt nền. Node dialog không có descendant
                # (VD alertTitle là lá) chỉ đóng góp bounds của chính nó —
                # guard khi đó không kết luận được (giữ claim, không giấu).
                _dlg_bounds = None

                def _union_bounds(acc, bounds_str):
                    m = re.findall(r"-?\d+", bounds_str or "")
                    if len(m) < 4:
                        return acc
                    x1, y1, x2, y2 = map(int, m[:4])
                    if acc is None:
                        return [x1, y1, x2, y2]
                    return [min(acc[0], x1), min(acc[1], y1),
                            max(acc[2], x2), max(acc[3], y2)]

                def _is_dialog_node(r_id):
                    return r_id in dialog_id_set or r_id.startswith("panel") \
                        or r_id.startswith("dialog") or r_id == "blvCardRoot"

                def _walk(elem, in_dialog):
                    nonlocal _dlg_bounds, has_dialog
                    nonlocal focused_sig, focused_text, focused_bounds
                    a = elem.attrib
                    is_focused = a.get("focused") == "true"
                    is_focusable = a.get("focusable") == "true"
                    txt = (a.get("text", "") or a.get("content-desc", "")).strip()
                    r_id = a.get("resource-id", "").split("/")[-1]
                    bounds = a.get("bounds", "")
                    # Lọc node ngoài viewport (CI-T4, reviewer): RecyclerView
                    # giữ cả node chưa cuộn tới trong dump — text của chúng
                    # KHÔNG có trên màn hình nhưng vẫn lọt vào
                    # all_visible_texts, làm (a) fake-score tố giá trị không
                    # có trên frame trích dẫn, (b) gate PASS nhờ text chỉ
                    # tồn tại ở node offscreen (VD 'mới cập nhật' chưa cuộn
                    # tới). Node không parse được bounds thì giữ lại (không
                    # chứng minh được là ngoài màn hình).
                    _in_view = True
                    if bounds:
                        _m = re.findall(r"-?\d+", bounds)
                        if len(_m) >= 4:
                            _x1, _y1, _x2, _y2 = map(int, _m[:4])
                            _in_view = _x2 > 0 and _y2 > 0 and _x1 < 1920 and _y1 < 1080
                    if a.get("selected") == "true" and r_id:
                        selected_ids.append(r_id)
                    if txt and _in_view:
                        all_visible_texts.append((r_id, txt))
                        all_visible_nodes.append({"id": r_id, "text": txt, "bounds": bounds})
                    _dlg_node = _is_dialog_node(r_id)
                    if (_dlg_node or in_dialog) and bounds:
                        _dlg_bounds = _union_bounds(_dlg_bounds, bounds)
                    # Chỉ node KHỚP tiêu chí dialog mới vào dialog_ids /
                    # has_dialog (như code cũ) — node con cháu chỉ góp
                    # bounds vào dialog_bounds, không làm nhiễu danh sách id.
                    if _dlg_node:
                        has_dialog = True
                        if r_id and r_id not in dialog_ids:
                            dialog_ids.append(r_id)
                    if is_focusable:
                        focusable_nodes.append({"id": r_id, "text": txt, "bounds": bounds, "focused": is_focused})
                        marker = "[FOCUSED] " if is_focused else "          "
                        summary_lines.append("%s%s ('%s') %s" % (marker, r_id or "view", txt[:25], bounds))
                    if is_focused:
                        focused_sig = "%s#%s" % (r_id or "view", bounds)
                        focused_text = txt
                        focused_bounds = bounds
                    for _ch in elem:
                        _walk(_ch, in_dialog or _dlg_node)

                for _top in root:
                    _walk(_top, False)
                if _dlg_bounds is not None:
                    dialog_bounds = "[%d,%d][%d,%d]" % tuple(_dlg_bounds)
            except Exception:
                pass
        return {
            "focused_sig": focused_sig,
            "focused_text": focused_text,
            "focused_bounds": focused_bounds,
            "focusable_count": len(focusable_nodes),
            "all_visible_texts": all_visible_texts,
            "all_visible_nodes": all_visible_nodes,
            "has_dialog": has_dialog,
            "dialog_ids": dialog_ids,
            "dialog_bounds": dialog_bounds,
            "selected_ids": selected_ids,
            "ui_summary": "\n".join(summary_lines[:25]) or "(Không tìm thấy focusable view)",
        }

    def detect_tab_index(self, ui_state):
        """Ưu tiên nav-selected, fallback từ khóa nội dung. None = không xác định."""
        for r_id in (ui_state.get("selected_ids") or []):
            if r_id in NAV_ID_TO_TAB:
                return NAV_ID_TO_TAB[r_id]
        visible_ids = " ".join(r for r, _ in (ui_state.get("all_visible_texts") or []))
        blob = (ui_state.get("ui_summary", "") + " " + ui_state.get("focused_sig", "")
                + " " + ui_state.get("focused_text", "") + " " + visible_ids).lower()
        for t_idx, kws in TAB_KEYWORDS:
            if any(k in blob for k in kws):
                return t_idx
        return None

    def detect_focus_ring_anywhere(self, png_bytes, band=None):
        """Tìm viền focus BẤT KỲ ĐÂU trong band — dùng khi dump không có
        focused view (WebPlayer: WebView mù với uiautomator, focused=NONE
        nhưng mắt thấy viền vàng quanh nút OSD — CI-T7 finding #1 giả).
        Band mặc định = hàng nút OSD dưới (0,850,1920,1080) hệ 1920x1080.
        Một 'vòng focus' = cụm pixel vàng/trắng có bbox cỡ nút
        (rộng 50-650px, cao 30-170px) với pixel tập trung ở CHU VI của box
        (>= 45% pixel nằm sát 4 cạnh) và KHÔNG đặc (tỉ lệ lấp <= 0.6) —
        loại khối vàng/trắng đặc (logo, thumbnail, nội dung video).
        CI-T9 (1): THÊM đường nhận vòng tròn/ellipse — test chu vi loại
        vòng tròn (hình tròn nội tiếp chỉ chạm cạnh bbox ở 4 điểm; CI-T8
        step_066/076 có vòng trắng rõ quanh nút pause mà vẫn False 95/95
        bước). Một component được nhận thêm khi EITHER (a) fit ellipse
        theo bbox: >= 55% điểm có bán kính chuẩn hóa |rho-1| <= 0.20 và
        phủ >= 8/12 cung 30 độ, OR (b) fit vòng tròn theo điểm (Kasa):
        >= 60% điểm cách tâm một bán kính (sai số <= max(2.5px, 12% r)),
        phủ >= 5/12 cung, r trong 10-175px (ảnh downscale 960) và bbox
        tương thích với r. Đường hình chữ nhật cũ GIỮ NGUYÊN.
        Ngưỡng trắng 190 thay vì 215 (CI-T9 (1): viền mỏng qua JPEG còn
        ~190 ở mép, 215 làm vòng vỡ thành mảnh < 30px) và nối component
        dung sai +-2px theo y (vòng cong đứng nhảy 2px giữa 2 cột mẫu).
        Trả (found, color, coverage, box_1920) — box None khi không thấy.
        Rẻ: chỉ quét band dưới ở 960 rộng (~55k điểm)."""
        if not png_bytes or not Image:
            return False, "UNKNOWN", 0.0, None
        try:
            im = Image.open(io.BytesIO(png_bytes)).convert("RGB")
            W, H = im.size
            bx0, by0, bx1, by1 = band or (0, 850, 1920, 1080)
            x0 = int(bx0 * W / 1920)
            y0 = int(by0 * H / 1080)
            x1 = int(bx1 * W / 1920)
            y1 = int(by1 * H / 1080)
            if x1 <= x0 or y1 <= y0:
                return False, "UNKNOWN", 0.0, None
            if W > 960:
                im = im.resize((960, int(H * 960 / W)), Image.BILINEAR)
                W, H = im.size
                x0 = int(bx0 * W / 1920)
                y0 = int(by0 * H / 1080)
                x1 = int(bx1 * W / 1920)
                y1 = int(by1 * H / 1080)
            px = im.load()
            # Mask: điểm vàng/trắng, quét bước 2 theo x, bước 1 theo y.
            pts = {}  # (sx, y) -> 'YELLOW' | 'WHITE'
            for y in range(y0, y1):
                for x in range(x0, x1, 2):
                    r, g, b = px[x, y]
                    if r >= 170 and g >= 120 and b <= 120 and (r - b) >= 80 and (r - g) <= 100:
                        pts[(x, y)] = "YELLOW"
                    elif r >= 190 and g >= 190 and b >= 190:
                        pts[(x, y)] = "WHITE"
            if len(pts) < 30:
                return False, "UNKNOWN", 0.0, None
            # Connected components 8-hướng (lệch ±2 theo x do bước quét 2,
            # CI-T9 (1): dung sai ±2 theo y — vòng cong đứng nhảy 2px giữa
            # 2 cột mẫu, ±1 làm vòng vỡ thành 2 nửa trên/dưới).
            seen = set()
            best = None  # (score, color, coverage, box_960)
            for seed in list(pts):
                if seed in seen:
                    continue
                stack = [seed]
                seen.add(seed)
                comp = []
                while stack:
                    cx, cy = stack.pop()
                    comp.append((cx, cy))
                    for nx in (cx - 2, cx, cx + 2):
                        for ny in (cy - 2, cy - 1, cy, cy + 1, cy + 2):
                            nb = (nx, ny)
                            if nb in pts and nb not in seen:
                                seen.add(nb)
                                stack.append(nb)
                if len(comp) < 30:
                    continue
                xs = [p[0] for p in comp]
                ys = [p[1] for p in comp]
                wx0, wx1, wy0, wy1 = min(xs), max(xs), min(ys), max(ys)
                # Bbox theo hệ 1920x1080 (x mẫu đã là tọa độ pixel thật
                # của ảnh downscale, bước quét 2 — KHÔNG nhân 2 nữa).
                b1920 = (int(wx0 * 1920 / W), int(wy0 * 1080 / H),
                         int((wx1 + 2) * 1920 / W), int((wy1 + 1) * 1080 / H))
                bw1920 = b1920[2] - b1920[0]
                bh1920 = b1920[3] - b1920[1]
                if not (50 <= bw1920 <= 650 and 30 <= bh1920 <= 170):
                    continue
                # Tỉ lệ lấp: mỗi điểm mẫu đại diện ~2px ảnh downscale; vòng
                # rỗng có tỉ lệ thấp (~0.1), khối đặc ~1.0.
                area_down = max(1.0, (wx1 - wx0 + 1) * 2.0 * (wy1 - wy0 + 1))
                fill = (len(comp) * 2.0) / area_down
                if fill > 0.6:
                    continue
                # (1) Đường cũ — giữ nguyên: pixel tập trung ở chu vi hình
                # chữ nhật, trong 3px (ảnh downscale) tính từ 4 cạnh bbox.
                per = 0
                for (pxx, pyy) in comp:
                    if pyy - wy0 <= 3 or wy1 - pyy <= 3 or \
                       pxx - wx0 <= 3 or wx1 - pxx <= 3:
                        per += 1
                cov = per / max(1, len(comp))
                # (2) CI-T9 (1): đường vòng tròn/ellipse.
                # (2a) Ellipse theo bbox: bán kính chuẩn hóa rho ~ 1.
                ecx = (wx0 + wx1) / 2.0
                ecy = (wy0 + wy1) / 2.0
                erx = max(1.0, (wx1 - wx0) / 2.0)
                ery = max(1.0, (wy1 - wy0) / 2.0)
                rho_ok = 0
                sectors = set()
                for (pxx, pyy) in comp:
                    rho = math.sqrt(((pxx - ecx) / erx) ** 2 + ((pyy - ecy) / ery) ** 2)
                    if abs(rho - 1.0) <= 0.20:
                        rho_ok += 1
                    sectors.add(int((math.degrees(math.atan2(pyy - ecy, pxx - ecx)) % 360) // 30))
                rho_frac = rho_ok / max(1, len(comp))
                ellipse_ok = rho_frac >= 0.55 and len(sectors) >= 8
                # (2b) Vòng tròn fit theo điểm (Kasa): cứu nửa vòng / cung
                # vỡ — bbox của nửa vòng không phải bbox của vòng.
                circle_frac = 0.0
                circle_ok = False
                fit = _fit_circle(comp)
                if fit is not None:
                    fcx, fcy, fr = fit
                    if 10.0 <= fr <= 175.0:
                        tol = max(2.5, 0.12 * fr)
                        d_ok = 0
                        fsectors = set()
                        for (pxx, pyy) in comp:
                            if abs(math.hypot(pxx - fcx, pyy - fcy) - fr) <= tol:
                                d_ok += 1
                            fsectors.add(int((math.degrees(math.atan2(pyy - fcy, pxx - fcx)) % 360) // 30))
                        circle_frac = d_ok / max(1, len(comp))
                        cbw, cbh = wx1 - wx0 + 1, wy1 - wy0 + 1
                        circle_ok = (circle_frac >= 0.60 and len(fsectors) >= 5
                                     and max(cbw, cbh) <= 2.5 * fr
                                     and min(cbw, cbh) >= 0.4 * fr)
                if cov < 0.45 and not ellipse_ok and not circle_ok:
                    continue
                score = max(cov, rho_frac if ellipse_ok else 0.0,
                            circle_frac if circle_ok else 0.0)
                cols = {}
                for p in comp:
                    cols[pts[p]] = cols.get(pts[p], 0) + 1
                color = "YELLOW" if cols.get("YELLOW", 0) >= cols.get("WHITE", 0) else "WHITE"
                if best is None or score > best[0]:
                    best = (score, color, round(score, 2), b1920)
            if best is None:
                return False, "UNKNOWN", 0.0, None
            return True, best[1], best[2], best[3]
        except Exception:
            return False, "ERR", 0.0, None

    def detect_focus_ring(self, png_bytes, focused_bounds_str):
        """Viền focus cam/amber/trắng/cyan quanh bounds đang focus (PIL thuần)."""
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
            pad = 6
            crop = im.crop((max(0, x1 - pad), max(0, y1 - pad), min(W, x2 + pad), min(H, y2 + pad)))
            px = crop.load()
            cw, ch = crop.size
            orange = white = cyan = total = 0

            def scan(pxset):
                nonlocal orange, white, cyan, total
                for (x, y) in pxset:
                    total += 1
                    r, g, b = px[x, y]
                    if r > 180 and 45 < g < 185 and b < 85:
                        orange += 1
                    elif r > 215 and g > 215 and b > 215:
                        white += 1
                    elif r < 110 and g > 180 and b > 200:
                        cyan += 1

            ys = list(range(min(pad + 2, ch))) + list(range(max(0, ch - pad - 2), ch))
            scan([(x, y) for y in set(ys) for x in range(0, cw, 2)])
            xs = list(range(min(pad + 2, cw))) + list(range(max(0, cw - pad - 2), cw))
            scan([(x, y) for x in set(xs) for y in range(0, ch, 2)])
            matched = orange + white + cyan
            color = "ORANGE" if orange >= white and orange >= cyan else ("WHITE" if white >= cyan else "CYAN")
            return matched > (total * 0.12), color, matched / max(1, total)
        except Exception:
            return False, "ERR", 0.0

    # -- telemetry -----------------------------------------------------
    def get_pss_memory_mb(self):
        out = sh("%s shell dumpsys meminfo %s 2>/dev/null | grep -E 'TOTAL PSS:|TOTAL:' | head -1" % (self.adb, self.pkg))
        m = re.search(r"(\d+)", out)
        return round(int(m.group(1)) / 1024.0, 1) if m else -1.0

    def checkpoint_logcat(self):
        lines = sh("%s logcat -d -v threadtime" % self.adb, timeout=20).splitlines()
        self._last_logcat_len = len(lines)

    def get_new_logcat_alerts(self):
        cur = sh("%s logcat -d -v threadtime" % self.adb, timeout=25).splitlines()
        last_len = getattr(self, "_last_logcat_len", 0)
        new_lines = cur[last_len:] if len(cur) >= last_len else cur
        self._last_logcat_len = len(cur)
        alerts = []
        for i, line in enumerate(new_lines):
            if "FATAL EXCEPTION" in line or "AndroidRuntime: FATAL" in line:
                alerts.append("CRASH: %s" % line[:120])
            elif "ANR in %s" % self.pkg in line:
                alerts.append("ANR: %s" % line[:120])
            elif "OutOfMemoryError" in line:
                alerts.append("OOM: %s" % line[:120])
            elif "ExoPlayer" in line and ("error" in line.lower() or "failure" in line.lower()):
                alerts.append("PLAYER_ERR: %s" % line[:100])
            elif "Choreographer" in line and "Skipped" in line:
                mm = re.search(r"Skipped\s+(\d+)\s+frames", line)
                if mm and int(mm.group(1)) >= 45:
                    alerts.append("UI_JANK: Bỏ lỡ %s frames" % mm.group(1))
        return alerts[:5]

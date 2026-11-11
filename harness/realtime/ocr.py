#!/usr/bin/env python3
"""KenhLive Realtime QA — OCR (tesseract, chỉ có ở CI).

Workflow qa-suite.yml cài `tesseract-ocr tesseract-ocr-vie` + `pytesseract`.
Local: đã cài tesseract 5.3.4 + gói `vie` ngày 2026-11-11 (apt) để replay
dùng được OCR — `available()` vẫn là cổng kiểm tra duy nhất: không có OCR
thì detector dùng OCR phải ghi `skipped`, không được bịa text.

Quy ước tọa độ: mọi `region` là (x0, y0, x1, y1) theo hệ tham chiếu
1920x1080; ảnh có thể là 960x540 (harness cũ downscale khi lưu) hoặc
1920x1080 (live) — `_scale_region` tự scale. Trả về box theo tọa độ ảnh GỐC.
"""
import io
import subprocess


def available():
    """True khi đọc được text bằng tesseract (pytesseract hoặc binary CLI)."""
    try:
        import pytesseract  # noqa: F401
        return True
    except ImportError:
        pass
    try:
        r = subprocess.run(["tesseract", "--version"], capture_output=True, timeout=5)
        return r.returncode == 0
    except Exception:
        return False


def _scale_region(region, W, H):
    """region=(x0,y0,x1,y1) theo hệ tọa độ tham chiếu 1920x1080 -> pixel thật.
    Ảnh lưu có thể là 960x540 (harness cũ downscale) hoặc 1920x1080 (live)."""
    x0, y0, x1, y1 = (int(v) for v in region)
    sx, sy = W / 1920.0, H / 1080.0
    return (max(0, int(x0 * sx)), max(0, int(y0 * sy)),
            min(W, int(x1 * sx)), min(H, int(y1 * sy)))


def _load_image(png_bytes, region=None):
    from PIL import Image
    im = Image.open(io.BytesIO(png_bytes)).convert("RGB")
    if region:
        x0, y0, x1, y1 = _scale_region(region, im.width, im.height)
        if x1 <= x0 or y1 <= y0:
            return None
        im = im.crop((x0, y0, x1, y1))
    return im


def read_text(png_bytes, region=None, lang="vie"):
    """Đọc text trong ảnh (hoặc vùng). Trả '' khi OCR không khả dụng."""
    if png_bytes is None:
        return ""
    im = _load_image(png_bytes, region)
    if im is None:
        return ""
    try:
        import pytesseract
        big = im.resize((im.width * 3, im.height * 3))
        return pytesseract.image_to_string(big, lang=lang, config="--psm 6").strip()
    except ImportError:
        pass
    except Exception:
        return ""
    try:
        import tempfile, os
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            im.save(f.name)
            path = f.name
        try:
            big = im.resize((im.width * 3, im.height * 3))
            big.save(path)
            r = subprocess.run(["tesseract", path, "stdout", "-l", lang, "--psm", "6"],
                               capture_output=True, text=True, timeout=30)
            return (r.stdout or "").strip()
        finally:
            try:
                os.remove(path)
            except Exception:
                pass
    except Exception:
        return ""


def cluster_same_line_boxes(boxes, y_tol_frac=0.5, gap_tol_frac=0.6):
    """Gộp các box OCR cùng 1 dòng thành 1 cụm (khử trùng PSM 11).

    Gốc rễ FP HIGH CI-T5 ("Xem ngay" step_010): tesseract PSM 11 trả 2 box
    gần trùng nhau cho cùng 1 dòng chữ ("Xem" / "ngay") — detector so chồng
    sau đó tố 2 box này đè nhau 93%. Guard chuỗi con ("Xem" in "ngay") là
    SAI (False, đã kiểm bằng code) — 2 box là 2 TỪ của cùng 1 dòng, không
    phải chuỗi con của nhau.
    Hai box cùng cụm khi (a) cùng baseline/dòng: tâm dọc gần nhau
    (|cy_a - cy_b| <= max(3px, 0.5*min(h))) VÀ (b) kề nhau theo chiều
    ngang: khoảng cách ngang <= max(6px, 0.6*min(h)) (từ kề nhau cách 1
    khoảng trắng, hoặc chồng lên nhau). Hai từ xa nhau trên cùng dòng
    (VD "TRANG CHỦ" ... "TRỰC TIẾP") KHÔNG gộp (gap lớn) — cụm không nuốt
    cả hàng. Hai dòng chữ THẬT chồng nhau (tiêu đề đè đôi, khác baseline)
    KHÔNG gộp — vẫn tố được.
    Chỉ dùng cho so chồng (detect_text_overlap); các detector khác
    (clipped/subtitle) vẫn dùng box thô để không mất P0-4/P0-5.
    Trả list cụm mới [{text, x0, y0, x1, y1, conf}]; không sửa list gốc."""
    boxes = list(boxes or [])
    if len(boxes) < 2:
        return boxes
    parent = list(range(len(boxes)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def union(i, j):
        ri, rj = find(i), find(j)
        if ri != rj:
            parent[ri] = rj

    for i in range(len(boxes)):
        for j in range(i + 1, len(boxes)):
            a, b = boxes[i], boxes[j]
            ha, hb = a["y1"] - a["y0"], b["y1"] - b["y0"]
            if ha <= 0 or hb <= 0:
                continue
            ca, cb = (a["y0"] + a["y1"]) / 2.0, (b["y0"] + b["y1"]) / 2.0
            if abs(ca - cb) > max(3.0, y_tol_frac * min(ha, hb)):
                continue  # khác dòng -> không gộp
            gap = max(b["x0"] - a["x1"], a["x0"] - b["x1"])
            if gap > max(6.0, gap_tol_frac * min(ha, hb)):
                continue  # cùng dòng nhưng xa nhau -> 2 cụm riêng
            union(i, j)
    groups = {}
    for i, b in enumerate(boxes):
        groups.setdefault(find(i), []).append(b)
    out = []
    for members in groups.values():
        members.sort(key=lambda b: b["x0"])
        out.append({
            "text": " ".join(m["text"] for m in members),
            "x0": min(m["x0"] for m in members),
            "y0": min(m["y0"] for m in members),
            "x1": max(m["x1"] for m in members),
            "y1": max(m["y1"] for m in members),
            "conf": max(m["conf"] for m in members),
        })
    return out


def read_boxes(png_bytes, region=None, lang="vie", min_conf=30):
    """Trả [{text, x0, y0, x1, y1, conf}] theo tọa độ ảnh GỐC (1920x1080).
    [] khi OCR không khả dụng. Dùng cho detector text_overlap / clipped_text."""
    if png_bytes is None:
        return []
    try:
        from PIL import Image
        im = Image.open(io.BytesIO(png_bytes)).convert("RGB")
        W, H = im.size
        ox, oy = 0, 0
        if region:
            x0, y0, x1, y1 = _scale_region(region, W, H)
            ox, oy = x0, y0
            im = _load_image(png_bytes, region)
            if im is None:
                return []
        import pytesseract
        big = im.resize((im.width * 2, im.height * 2))
        data = pytesseract.image_to_data(big, lang=lang, config="--psm 11",
                                         output_type=pytesseract.Output.DICT)
        scale = 0.5
        out = []
        n = len(data.get("text", []))
        for i in range(n):
            txt = (data["text"][i] or "").strip()
            if not txt:
                continue
            try:
                conf = float(data["conf"][i])
            except Exception:
                conf = -1
            if conf < min_conf:
                continue
            x0 = ox + int(data["left"][i] * scale)
            y0 = oy + int(data["top"][i] * scale)
            x1 = x0 + int(data["width"][i] * scale)
            y1 = y0 + int(data["height"][i] * scale)
            out.append({"text": txt, "x0": x0, "y0": y0, "x1": x1, "y1": y1, "conf": conf})
        return out
    except ImportError:
        return []
    except Exception:
        return []

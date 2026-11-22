#!/usr/bin/env python3
"""Preflight kiểm tra API ẢNH thật cho 3 tab (Thể thao / IPTV / Phim).

Chạy TRƯỚC emulator trong CI (có mạng), output `image_audit.json` đưa vào
artifact. Không dùng PIL (bị lỗi _imaging trên机器 này) — đo kích thước ảnh
bằng ffprobe (đã là dependency bắt buộc của video_recorder).

Nguyên tắc (bài học card Phim 2026-11-22):
- KKPhim (phimapi.com): poster_url = DỌC (2:3), thumb_url = NGANG (16:9).
- NguonC (phim.nguonc.com): NGƯỢC LẠI. Mọi consumer phải khớp hướng này;
  script chỉ ghi nhận hướng THỰC TẾ của API đang chạy, không giả định.
- HTTP 200 + decode được ảnh chưa đủ: phải đo w/h và so với kỳ vọng của
  từng consumer (hero ngang, card dọc) rồi báo rõ URL nào sai.

Exit code luôn 0 (report là đầu ra; workflow không fail vì 1 ảnh chết),
trừ khi không ghi được file output.
"""
import argparse
import json
import os
import re
import subprocess
import tempfile
import time
import urllib.request
from urllib.parse import urlparse

UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 KenhLiveQA/1.0"
PHIM_API = "https://phimapi.com/danh-sach/phim-moi-cap-nhat?page=1"
SPORTS_API = "https://json.vnres.co/all_live_rooms.json?callback=rooms&v=1&_=1"
IPTV_M3U = "app/app/src/main/assets/fallback_vn.m3u"


def fetch(url, timeout=25):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def image_size(data):
    """Trả (w,h) qua ffprobe, hoặc None nếu không decode được."""
    fd, path = tempfile.mkstemp(suffix=".img")
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
        out = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "v:0",
             "-show_entries", "stream=width,height", "-of", "csv=p=0", path],
            capture_output=True, timeout=20).stdout.decode("utf-8", "replace").strip()
        m = re.search(r"(\d+)\s*,\s*(\d+)", out)
        if m:
            return int(m.group(1)), int(m.group(2))
        return None
    except Exception:
        return None
    finally:
        try:
            os.unlink(path)
        except OSError:
            pass


def orientation(w, h):
    if not w or not h:
        return "unknown"
    r = w / float(h)
    if r >= 1.25:
        return "landscape"
    if r <= 0.80:
        return "portrait"
    return "square"


def check_image(checks, source, url, kind, expect=None, note=""):
    """Tải 1 ảnh, đo kích thước thật, append 1 check vào report."""
    c = {"source": source, "kind": kind, "url": url,
         "host": urlparse(url).netloc if url else "", "note": note,
         "expect": expect, "http": None, "w": None, "h": None,
         "orientation": "unknown", "ok": False, "error": ""}
    try:
        raw = fetch(url)
        c["http"] = 200
        c["bytes"] = len(raw)
        size = image_size(raw)
        if not size:
            c["error"] = "ffprobe không decode được ảnh (file hỏng / HTML / hotlink block)"
        else:
            c["w"], c["h"] = size
            c["orientation"] = orientation(*size)
            if expect and c["orientation"] != expect and c["orientation"] != "unknown":
                c["error"] = "hướng ảnh %s, kỳ vọng %s (%dx%d)" % (
                    c["orientation"], expect, c["w"], c["h"])
            else:
                c["ok"] = True
    except Exception as e:
        c["error"] = "%s: %s" % (type(e).__name__, str(e)[:120])
    checks.append(c)
    return c


def audit_phim(checks, limit):
    raw = fetch(PHIM_API)
    data = json.loads(raw.decode("utf-8", "replace"))
    items = data.get("items") or []
    rows = []
    for it in items[:limit]:
        slug = it.get("slug") or it.get("_id") or "?"
        for kind, key, expect in (("poster", "poster_url", "portrait"),
                                  ("thumb", "thumb_url", "landscape")):
            url = it.get(key) or ""
            if not url:
                checks.append({"source": "phim", "kind": kind, "url": "", "slug": slug,
                               "expect": expect, "ok": False,
                               "error": "API trả rỗng trường %s" % key})
                continue
            if url.startswith("/"):
                url = "https://phimimg.com" + url
            c = check_image(checks, "phim", url, kind, expect, note="slug=%s" % slug)
            c["slug"] = slug
            rows.append("%s %s %s" % (slug, kind, c["orientation"]))
    return len(items), rows


def audit_sports(checks, limit):
    txt = fetch(SPORTS_API).decode("utf-8", "replace")
    m = re.search(r"\{.*\}", txt, re.DOTALL)
    data = json.loads(m.group(0)) if m else {}
    urls = []

    def walk(node):
        if isinstance(node, dict):
            for k, v in node.items():
                if any(s in k.lower() for s in ("icon", "logo", "avatar", "image", "cover")) \
                        and isinstance(v, str) and v.startswith("http") and v not in urls:
                    urls.append(v)
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)

    walk(data.get("data") or data)
    for url in urls[:limit]:
        # icon BLV thường là ảnh vuông; chỉ bắt buộc decode được, không ép hướng.
        check_image(checks, "sports", url, "anchor_icon", expect=None,
                    note="Socolive live rooms")
    return len(urls), urls[:limit]


def audit_iptv(checks, app_dir, limit):
    path = os.path.join(app_dir, "app/src/main/assets/fallback_vn.m3u")
    if not os.path.exists(path):
        path = IPTV_M3U
    if not os.path.exists(path):
        checks.append({"source": "iptv", "kind": "m3u", "url": path, "ok": False,
                       "error": "không tìm thấy fallback_vn.m3u"})
        return 0, []
    txt = open(path, "r", encoding="utf-8", errors="replace").read()
    urls = re.findall(r'tvg-logo="(https?://[^"]+)"', txt)
    seen = []
    for u in urls:
        if u not in seen:
            seen.append(u)
    for url in seen[:limit]:
        # logo kênh có thể vuông/dọc/ngang tùy nguồn — chỉ yêu cầu tải được.
        check_image(checks, "iptv", url, "channel_logo", expect=None,
                    note="fallback_vn.m3u")
    return len(seen), seen[:limit]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="qa_out/image_audit.json")
    ap.add_argument("--app-dir", default="app")
    ap.add_argument("--limit", type=int, default=5)
    args = ap.parse_args()

    checks = []
    meta = {}
    for name, fn in (("phim", lambda: audit_phim(checks, args.limit)),
                     ("sports", lambda: audit_sports(checks, args.limit)),
                     ("iptv", lambda: audit_iptv(checks, args.app_dir, args.limit))):
        t0 = time.time()
        try:
            meta[name] = fn()
        except Exception as e:
            meta[name] = "ERROR: %s: %s" % (type(e).__name__, str(e)[:150])
        print("[image-audit] %s xong %.1fs" % (name, time.time() - t0), flush=True)

    summary = {
        "total": len(checks),
        "ok": sum(1 for c in checks if c.get("ok")),
        "failed": sum(1 for c in checks if not c.get("ok")),
        "by_source": {},
    }
    for c in checks:
        s = summary["by_source"].setdefault(c.get("source", "?"),
                                            {"total": 0, "ok": 0, "failed": 0})
        s["total"] += 1
        s["ok" if c.get("ok") else "failed"] += 1
    report = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "api": {"phim": PHIM_API, "sports": SPORTS_API, "iptv_m3u": IPTV_M3U},
        "fetched": meta,
        "summary": summary,
        "checks": checks,
        "failed_checks": [c for c in checks if not c.get("ok")],
    }
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print("[image-audit] %d checks, %d ok, %d failed -> %s"
          % (summary["total"], summary["ok"], summary["failed"], args.out), flush=True)
    for c in report["failed_checks"][:20]:
        print("  FAIL [%s/%s] %s — %s" % (c.get("source"), c.get("kind"),
                                          (c.get("url") or "")[:110], c.get("error")),
              flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

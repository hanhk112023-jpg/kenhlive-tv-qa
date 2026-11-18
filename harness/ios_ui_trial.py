#!/usr/bin/env python3
"""iOS UI trial — deterministic checks + AI visual judgement on simulator screenshots.

Reuses harness.ai_judge.judge_screen so the rubric matches the Android QA runs.
Never raises on AI failure: a vision outage is reported, not silently passed.
"""
import argparse, json, os, sys

from PIL import Image, ImageStat


def load_judge():
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    try:
        import ai_judge
        return ai_judge
    except Exception as exc:  # pragma: no cover
        print("ai_judge unavailable: %s" % exc, file=sys.stderr)
        return None


def shot_check(path):
    """Return (jpeg_bytes, nonblank_bool, stddev)."""
    im = Image.open(path).convert("RGB")
    # downscale to keep base64 payload small
    im.thumbnail((900, 900))
    std = sum(ImageStat.Stat(im).stddev) / 3.0
    import io
    buf = io.BytesIO()
    im.save(buf, format="JPEG", quality=80)
    return buf.getvalue(), std >= 6.0, round(std, 2)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--shots", required=True, help="directory with .png screenshots")
    ap.add_argument("--out", default="ios_ui_report.json")
    ap.add_argument("--launched", default="1")
    args = ap.parse_args()

    judge = load_judge()
    report = {
        "engine": "KenhLive iOS UI Trial",
        "app_launched": args.launched == "1",
        "screens": [],
        "findings": [],
        "vision_available": bool(judge and (os.environ.get("OPENAI_API_BASE") or
                                             os.environ.get("DEEPSEEK_API_BASE") or
                                             os.environ.get("KILO_API_BASE"))),
    }

    for fn in sorted(os.listdir(args.shots)):
        if not fn.lower().endswith((".png", ".jpg", ".jpeg")):
            continue
        path = os.path.join(args.shots, fn)
        try:
            jpeg, nonblank, std = shot_check(path)
        except Exception as exc:
            report["screens"].append({"file": fn, "error": str(exc)})
            continue
        entry = {"file": fn, "non_blank": nonblank, "contrast_stddev": std}
        if not nonblank:
            report["findings"].append({"severity": "high", "screen": fn,
                                       "issue": "Screenshot is blank/black — screen may not have rendered"})
        if judge and report["vision_available"]:
            try:
                raw = judge.judge_screen("iOS " + fn, jpeg)
                entry["judge"] = raw[:4000]
                if raw and any(k in raw.lower() for k in ("critical", "crash", "blocker")):
                    report["findings"].append({"severity": "high", "screen": fn,
                                               "issue": "AI judge flagged critical issue", "detail": raw[:1200]})
            except Exception as exc:
                entry["judge_error"] = str(exc)
        report["screens"].append(entry)

    report["passed"] = (report["app_launched"] and bool(report["screens"])
                        and not [f for f in report["findings"] if f["severity"] == "high"])
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(json.dumps({"screens": len(report["screens"]),
                      "findings": len(report["findings"]),
                      "passed": report["passed"],
                      "vision": report["vision_available"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""KenhLive Realtime QA — honest judge (không điểm mặc định).

Điểm = 100 - phạt trên defect ĐÃ XÁC MINH (bảng phạt giữ nguyên report.score
để so được với baseline: CRITICAL 25, HIGH 12, MEDIUM 5, LOW 1 + tối đa 20
cho mission FAIL). Mỗi defect phải có evidence {frame, video_t, ui_state}.
Vision/judge không parse được, timeout, hay thiếu bằng chứng -> UNVERIFIED
(ghi riêng, không tính pass, không cộng/trừ điểm). Mỗi PASS phải có evidence
bundle. Defect reel: cắt ±3s quanh mỗi defect từ video full (ffmpeg).
"""
import json
import os
import subprocess

PENALTY = {"CRITICAL": 25, "HIGH": 12, "MEDIUM": 5, "LOW": 1, "INFO": 0}
SEV_ORDER = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "INFO": 4}


def score_from(findings, checks_passed, checks_total):
    s = 100 - sum(PENALTY.get(f.get("severity", "LOW"), 1) for f in findings)
    if checks_total:
        s -= round((checks_total - checks_passed) / checks_total * 20)
    return max(0, min(100, s))


class HonestJudge:
    """Nhận findings đã xác minh + kết quả mission -> verdict có bằng chứng."""

    def __init__(self, out_dir):
        self.out_dir = out_dir

    def judge(self, missions, findings, unverified, engine="KenhLive Realtime Vision QA",
              duration_sec=0, vision_calls=None, timings=None):
        """missions: [{name, title, outcome, reason, evidence, steps}].
        findings: defect đã xác minh (mỗi cái có evidence).
        unverified: [{check, reason, frame}] — chỗ mù, KHÔNG tính điểm."""
        # UNVERIFIED không tính vào tỷ lệ pass/fail (thiếu dữ liệu, không phải
        # lỗi) — chỉ liệt kê riêng, không cộng/trừ điểm.
        decided = [m for m in missions if m.get("outcome") in ("PASS", "FAIL")]
        undecided = [m for m in missions if m.get("outcome") not in ("PASS", "FAIL")]
        passed = sum(1 for m in decided if m["outcome"] == "PASS")
        total = len(decided)
        sc = score_from(findings, passed, total)
        checks = [{
            "name": m["title"], "ok": m["outcome"] == "PASS",
            "outcome": m["outcome"],
            "detail": "%s — %s (%d bước)" % (m["outcome"], m["reason"], m["steps"]),
            "evidence": m.get("evidence", {}),
        } for m in missions]
        report = {
            "engine": engine,
            "score": sc,
            "duration_sec": duration_sec,
            "missions_passed": "%d/%d" % (passed, total),
            "missions_unverified": len(undecided),
            "checks_passed": passed,
            "checks_total": total,
            "checks": checks,
            "findings": sorted(findings, key=lambda f: (SEV_ORDER.get(f.get("severity", "LOW"), 9),
                                                         f.get("area", ""))),
            "unverified": unverified,
            "vision_calls": vision_calls or {},
            "timings": timings or {},
            "verdict": ("PASS" if sc >= 75 and (passed / total if total else 0) >= 0.8
                        and not any(f.get("severity") == "CRITICAL" for f in findings)
                        else "NEEDS_FIX"),
            # Verdict KHÔNG chỉ nhìn điểm: CI-T1 cho điểm 81/100 trong khi
            # 16/17 mission FAIL (điểm trừ tối đa cho mission FAIL chỉ 20) —
            # verdict PASS lúc đó là nói dối. PASS cần điểm ≥75 VÀ tỉ lệ
            # pass ≥80% VÀ không có CRITICAL.
        }
        return report

    def _tour_duration(self, video_path):
        """Độ dài tour (giây) qua ffprobe; None khi không đọc được (thiếu
        ffmpeg / file hỏng) — lúc đó reel giữ hành vi cũ, không kẹp."""
        try:
            r = subprocess.run(
                ["ffprobe", "-v", "error", "-show_entries", "format=duration",
                 "-of", "default=noprint_wrappers=1:nokey=1", video_path],
                capture_output=True, text=True, timeout=30)
            d = float((r.stdout or "").strip())
            return d if d > 0 else None
        except Exception:
            return None

    def build_defect_reel(self, video_path, findings, out_name="defect_reel.mp4",
                          speed_factor=1.0):
        """Cắt ±3s quanh mỗi defect -> defect_reel.mp4 + danh sách timestamps.
        Trả (reel_path|None, reel_entries). Không có video/defect -> (None, []).
        video_t trong evidence là THỜI GIAN THẬT của run; vị trí cắt trong file
        phải chia cho speed_factor của tour (video >600s bị tăng tốc 4-8x).
        CI-T3: cắt video_t trực tiếp vào file 4x -> 3/5 đoạn rỗng (vượt 226s),
        2/5 đoạn lệch nội dung; reel chỉ 18.6s thay vì 30s.
        CI-T6 mục 3: entry có video_t VƯỢT độ dài tour thì KẸP đoạn cắt về
        cuối tour (seg_start = tour_len - 6s) thay vì cắt ngoài file — đoạn
        đó vẫn xem được (dù không đúng thời điểm defect) và được gắn cờ
        clamped=True, covered=False để report báo rõ 'reel cover x/y
        finding' (CI-T5: entry 3 video_t 177.6s vượt tour 175.2s -> chỉ
        còn 0.6s xem được, reel chỉ khớp 2/3 finding)."""
        try:
            speed_factor = float(speed_factor) if speed_factor else 1.0
        except Exception:
            speed_factor = 1.0
        if speed_factor < 1.0:
            speed_factor = 1.0
        entries = []
        tour_len = self._tour_duration(video_path) \
            if video_path and os.path.exists(video_path) else None
        for f in findings:
            ev = f.get("evidence") or {}
            t = ev.get("video_t")
            if t is None or not video_path or not os.path.exists(video_path):
                continue
            vt = round(float(t) / speed_factor, 1)
            # Kẹp: thời điểm defect nằm trong tour thì covered; vượt tour
            # thì đoạn cắt kẹp về 6s cuối tour (vẫn xem được, nhưng không
            # còn đúng thời điểm). tour_len None -> không kết luận, giữ cũ.
            covered = True if tour_len is None else vt <= tour_len + 0.5
            clamped = bool(tour_len is not None and vt > tour_len + 0.5)
            if tour_len is not None:
                start = max(0.0, min(vt - 3.0, tour_len - 6.0))
                seg_s = round(min(6.0, tour_len - start), 1)
            else:
                start = max(0.0, vt - 3.0)
                seg_s = 6.0
            entries.append({"t": float(t), "video_t": vt,
                            "speed_factor": speed_factor,
                            "frame": ev.get("frame", ""),
                            "severity": f.get("severity", ""), "issue": f.get("issue", ""),
                            "covered": covered, "clamped": clamped,
                            "seg_start": round(start, 1), "seg_s": seg_s})
        if not entries or not video_path or not os.path.exists(video_path):
            return None, entries
        entries.sort(key=lambda e: e["t"])
        reel_path = os.path.join(self.out_dir, out_name)
        parts = os.path.join(self.out_dir, "reel_parts.txt")
        tmp_files = []
        try:
            with open(parts, "w") as fh:
                for i, e in enumerate(entries):
                    start = e.get("seg_start", max(0.0, e["video_t"] - 3.0))
                    seg = os.path.join(self.out_dir, "_reel_seg_%02d.mp4" % i)
                    subprocess.run(
                        ["ffmpeg", "-y", "-v", "error", "-ss", str(start), "-i", video_path,
                         "-t", "6", "-c", "copy", seg],
                        capture_output=True, timeout=120)
                    if os.path.exists(seg) and os.path.getsize(seg) > 2000:
                        tmp_files.append(seg)
                        fh.write("file '%s'\n" % os.path.abspath(seg))
            if tmp_files:
                subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0",
                                "-i", parts, "-c", "copy", reel_path],
                               capture_output=True, timeout=120)
            if not os.path.exists(reel_path) or os.path.getsize(reel_path) < 2000:
                return None, entries
            return reel_path, entries
        except Exception:
            return None, entries
        finally:
            for f in tmp_files:
                try:
                    os.remove(f)
                except Exception:
                    pass
            try:
                os.remove(parts)
            except Exception:
                pass

    def render_html(self, report, out_path):
        """HTML gọn: điểm, bảng mission kèm evidence, bảng defect kèm frame, reel."""
        def esc(s):
            import html
            return html.escape(str(s or ""))
        sc = report["score"]
        color = "#3ddc97" if sc >= 75 else "#ff8e3c" if sc >= 60 else "#ff4d4d"
        rows = ""
        for c in report["checks"]:
            ev = c.get("evidence") or {}
            ev_txt = "activity: %s | texts: %s | vision: %d xác nhận" % (
                ", ".join((ev.get("activities_seen") or [])[:3]),
                ", ".join((ev.get("texts_seen") or [])[:4]),
                len(ev.get("vision_confirmations") or []))
            oc = c.get("outcome", "PASS" if c["ok"] else "FAIL")
            badge = {"PASS": "✅ PASS", "FAIL": "❌ FAIL"}.get(oc, "❓ UNVERIFIED")
            rows += ("<tr><td><b>%s</b></td><td>%s</td>"
                     "<td class='%s'>%s</td><td style='font-size:11px;color:#94a3b8'>%s</td></tr>" % (
                         esc(c["name"]), esc(c["detail"]),
                         "pass" if oc == "PASS" else ("fail" if oc == "FAIL" else ""),
                         badge, esc(ev_txt)))
        frows = ""
        for f in report["findings"]:
            ev = f.get("evidence") or {}
            frows += ("<tr><td>%s</td><td><b>%s</b><br><small style='color:#8c9fc2'>%s</small></td>"
                      "<td>%s</td><td style='font-size:11px'>frame %s @ %ss</td></tr>" % (
                          esc(f.get("severity", "")), esc(f.get("area", "")),
                          esc(f.get("detail", "")), esc(f.get("issue", "")),
                          esc(ev.get("frame", "?")), esc(ev.get("video_t", "?"))))
        urows = "".join("<li>%s — %s</li>" % (esc(u.get("check", "")), esc(u.get("reason", "")))
                         for u in report.get("unverified", []))
        vc = report.get("vision_calls", {})
        tm = report.get("timings", {})
        nu = report.get("nim_usage", {})
        # Nối chuỗi bằng placeholder thay vì %-format: CSS có 'width:100%'
        # làm %-format crash (ValueError: unsupported format character ';').
        doc = ("<!DOCTYPE html><html lang='vi'><head><meta charset='utf-8'>"
               "<title>KenhLive · Realtime Vision QA Report</title>"
               "<style>body{background:#07090e;color:#f8fafc;font-family:system-ui,sans-serif;padding:24px}"
               ".wrap{max-width:1100px;margin:0 auto}.card{background:#0c0f17;border:1px solid rgba(255,255,255,.08);"
               "border-radius:14px;padding:20px;margin-bottom:22px}table{width:100%;border-collapse:collapse;font-size:13px}"
               "th,td{padding:10px 12px;border-bottom:1px solid rgba(255,255,255,.06);text-align:left;vertical-align:top}"
               "th{color:#94a3b8;text-transform:uppercase;font-size:11px}.pass{color:#3ddc97;font-weight:700}"
               ".fail{color:#ff4d4d;font-weight:700}h2{font-size:14px;text-transform:uppercase;letter-spacing:1px;color:#94a3b8}</style>"
               "</head><body><div class='wrap'>"
               "<div class='card'><h1 style='margin:0'>📺 KenhLive · Realtime Vision QA</h1>"
               "<p style='color:#64748b'>Engine: __ENGINE__</p>"
               "<div style='font-size:44px;font-weight:900;color:__COLOR__'>__SCORE__/100</div>"
               "<div>Hoàn thành: __PASSED__ nhiệm vụ · Vision calls: __VCALLS__ · Thời gian: __DUR__s</div>"
               "<div style='font-size:12px;color:#94a3b8'>Timings: __TIMINGS__</div>"
               "<div style='font-size:12px;color:#94a3b8'>Vision: __VPROV__ qua __VHOST__ · requests: __NIM_REQ__ (giới hạn __NIM_LIM__/phút) · Chạm 429: __NIM_429__</div>"
               "<div style='font-size:12px;color:#94a3b8'>Reel: __REEL__</div>"
               "<div style='margin-top:8px;font-weight:700'>Verdict: __VERDICT__</div></div>"
               "<div class='card'><h2>Nhiệm vụ (PASS phải có evidence bundle)</h2>"
               "<table><tr><th>Nhiệm vụ</th><th>Kết quả</th><th>Trạng thái</th><th>Bằng chứng</th></tr>__ROWS__</table></div>"
               "<div class='card'><h2>Defect đã xác minh (__NFIND__)</h2>"
               "<table><tr><th>Mức độ</th><th>Vị trí</th><th>Vấn đề</th><th>Bằng chứng</th></tr>__FROWS__</table></div>"
               "<div class='card'><h2>Chỗ chưa xác minh được (__NUNV__) — không tính điểm, không tính pass</h2><ul>__UROWS__</ul></div>"
               "</div></body></html>")
        for token, val in [
                ("__ENGINE__", esc(report.get("engine", ""))),
                ("__COLOR__", color),
                ("__SCORE__", str(sc)),
                ("__PASSED__", esc(report.get("missions_passed", ""))),
                ("__VCALLS__", str(esc(vc.get("total", 0)))),
                ("__DUR__", str(esc(report.get("duration_sec", 0)))),
                ("__TIMINGS__", esc(json.dumps(tm, ensure_ascii=False))),
                ("__NIM_REQ__", str(nu.get("requests_used", "?"))),
                ("__NIM_LIM__", str(nu.get("limit_per_min", "?"))),
                ("__NIM_429__", "CÓ" if nu.get("hit_429") else "không"),
                ("__VPROV__", esc(nu.get("provider") or report.get("vision_provider", "?"))),
                ("__VHOST__", esc(nu.get("endpoint_host") or report.get("vision_endpoint_host", "?"))),
                ("__REEL__", esc((report.get("defect_reel_coverage") or {}).get("text", "—"))),
                ("__VERDICT__", esc(report.get("verdict", ""))),
                ("__ROWS__", rows),
                ("__NFIND__", str(len(report["findings"]))),
                ("__FROWS__", frows),
                ("__NUNV__", str(len(report.get("unverified", [])))),
                ("__UROWS__", urows)]:
            doc = doc.replace(token, val)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(doc)
        return out_path

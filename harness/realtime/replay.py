#!/usr/bin/env python3
"""Offline replay trial cho KenhLive Realtime QA (§12 DESIGN.md).

Chạy logic mới (EvidenceGate + detectors cục bộ + vision xác minh) trên
artifact đã lưu của run 42950738729 (qa_session.json timeline 136 bước,
154 ảnh, full_qa_tour.mp4) — KHÔNG cần emulator.

Đo: thời gian chạy, recall P0-1..P0-8, false pass, số vision call.
P0 nào bắt được bằng tín hiệu rẻ (timeline/detector) thì không tốn vision;
chỉ P0-3/4/5/7/8 (lỗi nhìn) mới cần 1 vision call mỗi cái, trên đúng frame
đã được mắt người xác nhận trong VISUAL-REVIEW.md.
"""
import argparse
import io
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from gate import EvidenceGate
from vision import VisionClient
from judge import HonestJudge
from missions import get_missions
from device import RealtimeDevice

# Old mission id (fragment) -> new MissionSpec name (missions.py).
# "HOME_HUB_3_CARDS" không có spec mới (mission lỗi thời, Tab 6 đã xóa) ->
# xử lý riêng: FAIL bằng tab check (P0-2).
MISSION_MAP = {
    "COLD_START": "MISSION_COLD_START",
    "SPORTS_MULTI_SOURCE": "MISSION_SPORTS_MULTI_SOURCE",
    "SPORTS_ROOM_PICKER": "MISSION_SPORTS_ROOM_PICKER",
    "SPORTS_DATA_ACCURACY": "MISSION_SPORTS_DATA_ACCURACY",
    "IPTV_CATEGORIES": "MISSION_IPTV_CATEGORIES_AND_FAVORITES",
    "IPTV_EPG_AND_ZAPPING": "MISSION_IPTV_EPG_AND_ZAPPING_PLAYER",
    "PHIM_NGUONC": "MISSION_PHIM_NGUONC_AND_CATEGORIES",
    "PHIM_EPISODE_PICKER": "MISSION_PHIM_EPISODE_PICKER_AND_FAVORITE",
    "SCHEDULE_EPG": "MISSION_SCHEDULE_EPG_AND_FIXTURE_TAP",
    "SEARCH_AND_SETTINGS": "MISSION_SEARCH_AND_SETTINGS_FEEDBACK",
    "SIDEBAR_RAIL": "MISSION_SIDEBAR_RAIL_FULL_TRAVERSAL",
    "PLAYER_SETTINGS_DIALOG": "MISSION_PLAYER_SETTINGS_DIALOG",
    "PLAYER_STREAMING_AND_CONTROLS": "MISSION_PLAYER_STREAMING_AND_CONTROLS",
    "VOD_PLAYER_SEEK_AND_RESUME": "MISSION_VOD_PLAYER_SEEK_AND_RESUME",
    "WEBPLAYER_DIRECTED_REAL_FILM": "MISSION_WEBPLAYER_DIRECTED_REAL_FILM",
    "DPAD_CHAOS_STRESS": "MISSION_DPAD_CHAOS_STRESS_AND_RECOVERY",
    "HOME_HUB_3_CARDS": None,
}

# P0 -> vision check (frame + câu hỏi + crop vùng nghi theo 1920x1080).
# Crop là bài học vòng 1: hỏi trên full frame, model bỏ sót lỗi ở mép
# (P0-3) và lỗi "nằm giữa" mơ hồ (P0-5).
P0_VISION_CHECKS = {
    "P0-3": ("step_065_mission_.jpg",
             "Đọc nguyên văn từng dòng chữ trong ảnh crop này (vùng nav trên cùng "
             "của màn hình IPTV), từ trên xuống dưới. Có dòng chữ nào ĐÈ LÊN hoặc "
             "CHỒNG LÊN dòng chữ khác không (VD tiêu đề kênh 'VTV4 HD' đè lên chữ "
             "nav 'TRANG CHỦ', 'ĐÀI TRUYỀN HÌNH VIỆT NAM' đè lên 'TÌM KIẾM')? "
             "Nếu có, trích nguyên văn cả hai dòng bị chồng.",
             (0, 0, 1920, 280)),
    "P0-4": ("step_026_mission_.jpg",
             "Ở hàng nút dưới cùng của player Thể thao: nút nào bị CẮT CHỮ ở mép "
             "phải? Đọc nguyên văn phần chữ còn nhìn thấy (VD 'TRỰC…') và tên nút "
             "kề ngay sau nó.",
             (1000, 780, 1920, 1080)),
    "P0-5": ("step_091_mission_.jpg",
             "Trong ảnh crop này (vùng dưới của player VOD): xác định 3 thứ theo "
             "chiều dọc từ trên xuống — (a) dòng phụ đề trắng, (b) thanh seekbar "
             "ngang có chấm tròn và thời gian, (c) hàng nút bên dưới. Đo khoảng "
             "cách dọc giữa dòng phụ đề và thanh seekbar: bao nhiêu px, chạm nhau "
             "hay cách nhau? Phần dưới của dòng phụ đề có bị hàng nút bên dưới "
             "CHE PHỦ một phần không? Trả lời rõ: 'chạm/đè' hay 'cách nhau X px', "
             "kèm trích nguyên văn câu phụ đề.",
             (0, 780, 1920, 1080)),
    "P0-7": ("step_057_mission_.jpg",
             "Có header/hàng nào ghi số kênh lớn bất thường không (VD 'TV360 "
             "— 75 kênh', một hàng chứa khoảng 75 kênh)? Trích đúng chữ số "
             "nhìn thấy.",
             None),
    "P0-8": ("step_057_mission_.jpg",
             "Có card kênh nào hiện logo/text logo sai không khớp tên kênh "
             "không (VD logo 'ANTV' trên card kênh 'VTV Cần Thơ')? Chỉ rõ "
             "card số mấy, logo gì, tên kênh gì.",
             None),
}

P0_INFO = {
    "P0-1": ("WebPlayer mission 0 bước tới WebPlayerActivity", "gate"),
    "P0-2": ("Home Hub: SWITCH_TAB(6) 4 lần, tab kẹt ở 5", "gate"),
    "P0-3": ("Hero IPTV đè top nav", "vision"),
    "P0-4": ("Nút 'Về trực tiếp' bị cắt", "ocr"),
    "P0-5": ("Phụ đề VOD đè seekbar + nút", "ocr-geometry"),
    "P0-6": ("Mất focus sau BACK trong player IPTV (step 59)", "detector"),
    "P0-7": ("1 hàng TV360 chứa 75 kênh", "vision"),
    "P0-8": ("Logo ANTV sai cho VTV Cần Thơ", "vision"),
}


def _frame_bytes(shots_dir, name):
    path = os.path.join(shots_dir, name)
    if not os.path.exists(path):
        return None, path
    with open(path, "rb") as f:
        return f.read(), path


def main():
    ap = argparse.ArgumentParser(description="KenhLive Realtime QA — offline replay")
    ap.add_argument("--artifacts", required=True,
                    help="thư mục qa-report của run cũ (có qa_session.json + shots/)")
    ap.add_argument("--out", default="/tmp/qa_realtime_replay")
    ap.add_argument("--vision-budget", type=int, default=10)
    ap.add_argument("--no-vision", action="store_true")
    args = ap.parse_args()

    t_start = time.time()
    os.makedirs(args.out, exist_ok=True)
    session_path = os.path.join(args.artifacts, "qa_session.json")
    shots_dir = os.path.join(args.artifacts, "shots")
    with open(session_path, encoding="utf-8") as f:
        session = json.load(f)
    timeline = session.get("timeline", [])
    old_report = {}
    rp = os.path.join(args.artifacts, "qa_report.json")
    if os.path.exists(rp):
        with open(rp, encoding="utf-8") as f:
            old_report = json.load(f)

    specs = {s.name: s for s in get_missions()}
    vision = VisionClient(budget=0 if args.no_vision else args.vision_budget)
    findings = []
    unverified = []
    mission_results = []

    # --- 1. Group timeline theo mission, chạy gate offline --------------
    missions_grouped = []
    for e in timeline:
        mid = e.get("mission", {}).get("id", "?")
        if missions_grouped and missions_grouped[-1][0] == mid:
            missions_grouped[-1][1].append(e)
        else:
            missions_grouped.append((mid, [e]))

    # tab-target check (P0-2): SWITCH_TAB(N) >=3 lần mà tab không tới N
    tab_check = {}
    for mid, entries in missions_grouped:
        for e in entries:
            a = e.get("action") or {}
            if a.get("type") == "SWITCH_TAB":
                try:
                    n = int(a.get("param"))
                except Exception:
                    continue
                tab_check.setdefault(mid, {}).setdefault(n, {"tries": 0, "reached": False})
                tab_check[mid][n]["tries"] += 1
        for n, info in tab_check.get(mid, {}).items():
            for e in entries:
                if (e.get("active_tab") or {}).get("index") == n:
                    info["reached"] = True

    for mid, entries in missions_grouped:
        title = entries[0].get("mission", {}).get("title", mid)
        spec_name = None
        for frag, name in MISSION_MAP.items():
            if frag in mid:
                spec_name = name
                break
        # Case đặc biệt 1: Home Hub — không còn spec (Tab 6 đã xóa, mission lỗi
        # thời). Kết luận trực tiếp từ tab check: SWITCH_TAB(6) >=3 lần không
        # tới được -> FAIL (P0-2), không cần spec.
        if spec_name is None:
            tab_fails = ["SWITCH_TAB(%d) %d lần, tab đích không xuất hiện" % (n, i["tries"])
                         for n, i in tab_check.get(mid, {}).items()
                         if i["tries"] >= 3 and not i["reached"]]
            if tab_fails:
                mission_results.append({
                    "name": mid, "title": title, "outcome": "FAIL",
                    "reason": "; ".join(tab_fails),
                    "evidence": {"tab_check": tab_check.get(mid, {})},
                    "steps": len(entries), "old_mission_id": mid})
                print("  ❌ %-22s FAIL — %s" % (mid[:22], "; ".join(tab_fails)[:100]), flush=True)
            else:
                mission_results.append({
                    "name": mid, "title": title, "outcome": "UNVERIFIED",
                    "reason": "không có MissionSpec tương đương — không tự kết luận",
                    "evidence": {}, "steps": len(entries), "old_mission_id": mid})
                unverified.append({"check": mid,
                                   "reason": "không có spec tương đương trong missions.py",
                                   "frame": entries[-1].get("screenshot", "")})
            continue
        # Case đặc biệt 2: VOD Seek — spec MỚI đổi required_activity sang
        # WebPlayerActivity, run cũ chạy native PlayerActivity. So sánh trực
        # tiếp sẽ FAIL oan do đổi định nghĩa, không phải lỗi app -> UNVERIFIED,
        # ghi rõ giới hạn; CI trial sẽ kiểm chứng spec mới.
        if spec_name == "MISSION_VOD_PLAYER_SEEK_AND_RESUME":
            mission_results.append({
                "name": spec_name, "title": title, "outcome": "UNVERIFIED",
                "reason": "spec mới đổi sang WebPlayerActivity, run cũ chạy native "
                          "PlayerActivity — không so được; cần CI trial",
                "evidence": {}, "steps": len(entries), "old_mission_id": mid})
            unverified.append({"check": spec_name,
                               "reason": "định nghĩa mission đổi sau run 42950738729",
                               "frame": entries[-1].get("screenshot", "")})
            print("  ❓ %-22s UNVERIFIED — spec đổi sang WebPlayer, run cũ native" % spec_name[:22], flush=True)
            continue
        spec = specs[spec_name]
        gate = EvidenceGate(spec)
        for e in entries:
            ui = e.get("ui_state") or {}
            focused = ui.get("focused_view") or "NONE"
            view_id = focused.split("#")[0] if focused != "NONE" else "NONE"
            texts = [ui.get("focused_text")] if ui.get("focused_text") else []
            views = [view_id] if view_id != "NONE" else []
            motion = bool((e.get("playback_state") or {}).get("is_playing")) and \
                float((e.get("playback_state") or {}).get("motion_delta") or 0) > 0.35
            # Suy dialog từ focused_view (timeline cũ không có trường dialog):
            # focused view chứa "dialog" (VD select_dialog_listview).
            has_dialog = "dialog" in (focused or "").lower()
            gate.observe(e.get("activity", ""), texts, views, has_dialog, motion,
                         float(e.get("time_offset_sec") or 0))
            # CI-T6 mục 8: timeline mới ghi playback_s (đồng hồ elapsed);
            # timeline cũ không có -> None -> unknown, không chặn PASS.
            gate.observe_playback((e.get("playback_state") or {}).get("playback_s"),
                                  float(e.get("time_offset_sec") or 0))
            # P0-6 detector: focus NONE trong player sau BACK
            if focused == "NONE" and "PlayerActivity" in (e.get("activity") or ""):
                gate.focus_lost_seen = True
        # tab-target: mission nào SWITCH_TAB nhiều lần mà không tới -> FAIL
        for n, info in tab_check.get(mid, {}).items():
            if info["tries"] >= 3 and not info["reached"]:
                gate.force_fail(
                    "SWITCH_TAB(%d) %d lần mà tab đích không bao giờ xuất hiện "
                    "(tab kẹt ở index khác) — mission lỗi thời hoặc tab không tồn tại" % (
                        n, info["tries"]),
                    entries[-1].get("screenshot", ""))
        verdict, reason, ev = gate.evaluate(entries[-1].get("screenshot", ""))
        if verdict == "VISION_PENDING":
            # Mọi tín hiệu rẻ đã xanh, chỉ còn vision-confirm trên frame cuối.
            if args.no_vision or not vision.available():
                verdict, reason = "UNVERIFIED", "cần vision-confirm, vision không khả dụng"
                unverified.append({"check": spec.name, "reason": reason,
                                   "frame": entries[-1].get("screenshot", "")})
            else:
                last = entries[-1]
                shot = (last.get("screenshot") or "").split("/")[-1]
                png, _ = _frame_bytes(shots_dir, shot)
                if png:
                    res, err = vision.confirm_target(png, spec.target_desc)
                    if res is not None:
                        gate.record_vision(res.get("confirmed"), shot,
                                           float(last.get("time_offset_sec") or 0),
                                           res.get("quote", ""))
                        verdict, reason, ev = gate.evaluate(shot)
                    else:
                        unverified.append({"check": "%s vision-confirm" % spec.name,
                                           "reason": "vision lỗi: %s" % (err or "?"), "frame": shot})
                        verdict, reason = "FAIL", "vision-confirm thất bại — không PASS giả"
                else:
                    verdict, reason = "UNVERIFIED", "thiếu frame cuối để vision-confirm"
                    unverified.append({"check": spec.name, "reason": reason, "frame": shot})
        # Downgrade trung thực: replay chỉ có focused_text (không có full UI
        # dump như live), nên tín hiệu text:/dialog: thiếu KHÔNG chứng minh
        # app lỗi — chỉ ghi UNVERIFIED, không FAIL oan. Activity/motion/view
        # thiếu thì timeline đủ dữ liệu -> FAIL thật. CI-T6 mục 8: playback:
        # cũng downgrade (timeline cũ không có playback_s; không đủ dữ liệu
        # để kết luận video đóng băng).
        if verdict in ("FAIL", "CONTINUE"):
            missing = gate.missing_summary()
            if missing and all(m.startswith("text:") or m.startswith("dialog:")
                               or m.startswith("playback:") for m in missing):
                verdict = "UNVERIFIED"
                reason = ("replay thiếu dữ liệu: timeline cũ chỉ có focused text, "
                          "không có full UI dump — không kết luận được (%s)" % "; ".join(missing))
                unverified.append({"check": spec.name, "reason": reason,
                                   "frame": entries[-1].get("screenshot", "")})
            elif verdict == "CONTINUE":
                if spec.kind == "stress":
                    verdict = "UNVERIFIED"
                    reason = "stress mission chưa đủ bước trong timeline cũ"
                    unverified.append({"check": spec.name, "reason": reason,
                                       "frame": entries[-1].get("screenshot", "")})
                else:
                    verdict = "FAIL"
                    reason = "hết bước, còn thiếu: %s" % "; ".join(gate.missing_summary())
        mission_results.append({
            "name": spec.name, "title": title, "outcome": verdict,
            "reason": reason, "evidence": ev, "steps": len(entries),
            "old_mission_id": mid})
        print("  %s %-22s %s — %s" % (
            "✅" if verdict == "PASS" else ("❌" if verdict == "FAIL" else "❓"),
            spec.name, verdict, reason[:110]), flush=True)

    # --- 2. Detectors cục bộ trên toàn bộ frame -------------------------
    t_det0 = time.time()
    frames_checked = 0
    focus_none_steps = []
    blank_steps = []
    for e in timeline:
        shot = (e.get("screenshot") or "").split("/")[-1]
        if not shot:
            continue
        png, _ = _frame_bytes(shots_dir, shot)
        if not png:
            continue
        frames_checked += 1
        ui = e.get("ui_state") or {}
        if RealtimeDevice.is_blank(png):
            blank_steps.append(e["step_id"])
        if (ui.get("focused_view") or "NONE") == "NONE" and \
                "PlayerActivity" in (e.get("activity") or ""):
            focus_none_steps.append(e["step_id"])
    det_s = round(time.time() - t_det0, 1)

    # --- 2b. OCR hình học trên frame khóa (P0-4 clipped, P0-5 subtitle) -----
    # Vòng 4: detector OCR đã sửa (cache band, gate, guard false positive) —
    # P0-5 bắt bằng hình học (phụ đề cắt ngang hàng seekbar), không chờ vision.
    p0_results = {}
    for p0, (desc, method) in P0_INFO.items():
        p0_results[p0] = {"title": desc, "method": method, "caught": False,
                          "evidence": {}, "note": ""}
    import ocr as _ocr_mod
    from detectors import detect_clipped_text as _f_clipped, \
        detect_subtitle_seekbar_overlap as _f_subseek
    t_ocr0 = time.time()
    ocr_checks = {
        "P0-4": ("step_026_mission_.jpg", "PlayerActivity", _f_clipped),
        "P0-5": ("step_091_mission_.jpg", "PlayerActivity", _f_subseek),
    }
    for p0, (frame, act, fn) in ocr_checks.items():
        png, _ = _frame_bytes(shots_dir, frame)
        if not png:
            p0_results_note = "không có frame %s" % frame
            unverified.append({"check": p0, "reason": p0_results_note, "frame": frame})
            continue
        if not _ocr_mod.available():
            unverified.append({"check": p0, "reason": "OCR không khả dụng (thiếu tesseract)",
                               "frame": frame})
            continue
        ctx = {"reported": set(), "focus_hist": [], "ocr_skipped": 0}
        ui = {"focused_sig": "NONE", "focused_text": "", "focused_bounds": None,
              "all_visible_texts": []}
        found = fn(png, ui, act, ctx, frame, 0, _ocr_mod)
        if found:
            p0_results[p0]["caught"] = True
            p0_results[p0]["method"] = "ocr-geometry"
            p0_results[p0]["evidence"] = {"frame": frame,
                                          "detector": found[0]["issue"],
                                          "detail": found[0]["detail"][:200]}
            findings.append(found[0])
            print("  🔎 %s %s — OCR bắt: %s" % (p0, frame, found[0]["issue"][:80]), flush=True)
        else:
            print("  🔎 %s %s — OCR không thấy (để vision thử)" % (p0, frame), flush=True)
    ocr_s = round(time.time() - t_ocr0, 1)

    # --- 3. Vision xác minh P0 lỗi nhìn ----------------------------------
    t_vision0 = time.time()
    # P0-1 / P0-2: từ kết quả gate của mission tương ứng
    for m in mission_results:
        if m.get("old_mission_id") == "MISSION_WEBPLAYER_DIRECTED_REAL_FILM":
            p0_results["P0-1"]["caught"] = (m["outcome"] == "FAIL")
            p0_results["P0-1"]["evidence"] = {"mission_outcome": m["outcome"],
                                              "reason": m["reason"], "steps": m["steps"]}
            if m["outcome"] == "FAIL":
                findings.append({"area": "WebPlayer (directed)", "severity": "CRITICAL",
                                 "issue": "Mission WebPlayer không tới được WebPlayerActivity",
                                 "detail": m["reason"],
                                 "evidence": {"frame": "steps 96-102", "video_t": None,
                                              "ui_state": "activity: PlayerActivity -> MainActivity"}})
        if m.get("old_mission_id") == "MISSION_HOME_HUB_3_CARDS_AND_CANVA_LOGOS":
            p0_results["P0-2"]["caught"] = (m["outcome"] == "FAIL")
            p0_results["P0-2"]["evidence"] = {"mission_outcome": m["outcome"],
                                              "reason": m["reason"], "steps": m["steps"]}
            if m["outcome"] == "FAIL":
                findings.append({"area": "Home Hub", "severity": "HIGH",
                                 "issue": "Tab 6 (Home Hub) không còn tồn tại — mission lỗi thời",
                                 "detail": m["reason"],
                                 "evidence": {"frame": "steps 32-41", "video_t": None,
                                              "ui_state": "SWITCH_TAB(6) x4, tab kẹt ở 5"}})
    # P0-6: detector focus NONE trong player
    if 59 in focus_none_steps:
        p0_results["P0-6"]["caught"] = True
        p0_results["P0-6"]["evidence"] = {"frame": "step_059_mission_.jpg",
                                          "focus_none_steps_in_player": focus_none_steps}
        findings.append({"area": "Player IPTV (BACK)", "severity": "HIGH",
                         "issue": "Mất focus sau khi bấm BACK trong player IPTV",
                         "detail": "focused_view = NONE ở step 59; focus NONE trong player ở các step %s" % focus_none_steps,
                         "evidence": {"frame": "step_059_mission_.jpg", "video_t": None,
                                      "ui_state": "focused_view NONE, PlayerActivity"}})
    else:
        p0_results["P0-6"]["note"] = "không thấy focus NONE ở step 59 trong timeline"
    # P0-3/4/5/7/8: vision
    if not args.no_vision and vision.available():
        for p0, (frame, question, crop) in P0_VISION_CHECKS.items():
            png, path = _frame_bytes(shots_dir, frame)
            if not png:
                p0_results[p0]["note"] = "không có frame %s" % frame
                unresolved = {"check": p0, "reason": "thiếu frame", "frame": frame}
                unverified.append(unresolved)
                continue
            res, err = vision.check_visual(png, question, crop=crop)
            if res is None:
                p0_results[p0]["note"] = "vision lỗi: %s" % (err or "?")
                unverified.append({"check": p0, "reason": "vision lỗi: %s" % (err or "?"),
                                   "frame": frame})
                continue
            sev = res.get("severity", "MEDIUM")
            # OCR có thể đã bắt trước (P0-4/P0-5): vision chỉ bổ sung, không
            # ghi đè catch của OCR, không append finding trùng.
            if res.get("found") and not p0_results[p0]["caught"]:
                p0_results[p0]["caught"] = True
                p0_results[p0]["evidence"] = {"frame": frame,
                                              "vision": res.get("detail", "")[:200],
                                              "severity": sev,
                                              "crop": crop}
                findings.append({"area": P0_INFO[p0][0], "severity": sev,
                                 "issue": "Replay vision xác nhận: %s" % P0_INFO[p0][0],
                                 "detail": res.get("detail", ""),
                                 "evidence": {"frame": frame, "video_t": None,
                                              "ui_state": "vision check_visual"}})
            elif res.get("found"):
                p0_results[p0]["evidence"]["vision_also_confirmed"] = \
                    res.get("detail", "")[:200]
            print("  👁 %s %s — found=%s (%s) %s" % (
                p0, frame, res.get("found"), sev, (res.get("detail") or "")[:90]), flush=True)
    elif not vision.available():
        for p0 in P0_VISION_CHECKS:
            p0_results[p0]["note"] = "vision không khả dụng — chạy --no-vision hoặc thiếu provider"

    # --- 4. Tổng kết -----------------------------------------------------
    duration = round(time.time() - t_start, 1)
    vision_s = round(time.time() - t_vision0, 1)
    passed = sum(1 for m in mission_results if m["outcome"] == "PASS")
    failed = sum(1 for m in mission_results if m["outcome"] == "FAIL")
    unv = sum(1 for m in mission_results if m["outcome"] == "UNVERIFIED")
    caught = [p for p, r in p0_results.items() if r["caught"]]
    false_pass_new = sum(1 for m in mission_results
                         if m["outcome"] == "PASS" and not m.get("evidence"))
    judge = HonestJudge(args.out)
    report = judge.judge(mission_results, findings, unverified,
                         engine="KenhLive Realtime Vision QA (offline replay)",
                         duration_sec=duration,
                         vision_calls={"total": vision.calls_total,
                                       "by_reason": dict(vision.calls_by_reason),
                                       "provider": vision.provider},
                         timings={"replay_wall_s": duration,
                                  "detectors_s": det_s,
                                  "ocr_keyframes_s": ocr_s,
                                  "vision_s": vision_s,
                                  "frames_checked": frames_checked,
                                  "vision_latency_mean_s": round(sum(vision.latencies) / len(vision.latencies), 1) if vision.latencies else 0.0,
                                  "baseline_wall_s": 4466})
    report["p0_recall"] = {
        "caught": len(caught), "total": len(P0_INFO),
        "caught_list": caught,
        "missed_list": [p for p in P0_INFO if p not in caught],
        "per_p0": p0_results,
    }
    report["false_passes_new"] = false_pass_new
    # NIM usage (luật cứng 40 req/phút): requests đã dùng + có chạm 429?
    report["nim_usage"] = vision.nim_stats()
    # CI-T6 mục 10: ghi rõ provider thật ở cấp report (như runner).
    report["vision_provider"] = vision.provider
    report["vision_endpoint_host"] = vision.endpoint_host
    report["old_judge"] = {"score": old_report.get("score"),
                           "checks_passed": old_report.get("checks_passed"),
                           "checks_total": old_report.get("checks_total")}
    report["missions_summary"] = {"pass": passed, "fail": failed, "unverified": unv}
    with open(os.path.join(args.out, "replay_report.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 60)
    print("REPLAY XONG: %ss (baseline 4466s) | mission %d PASS / %d FAIL / %d UNVERIFIED" % (
        duration, passed, failed, unv))
    print("P0 recall: %d/%d (%s) | missed: %s" % (
        len(caught), len(P0_INFO), ", ".join(caught) or "-",
        ", ".join(p for p in P0_INFO if p not in caught) or "không có"))
    print("False pass mới (PASS không evidence): %d | vision calls: %d (%s), %.1fs | score: %d/100" % (
        false_pass_new, vision.calls_total, vision.provider, vision_s, report["score"]))
    nu = report["nim_usage"]
    print("Vision: %s qua %s · requests: %d (giới hạn 30/phút) | chạm 429: %s | chờ throttle: %d lần, %.1fs" % (
        vision.provider, vision.endpoint_host or "?",
        nu.get("requests_used", 0),
        "CÓ — LỖI THIẾT KẾ, SỬA Ở VÒNG SAU" if nu.get("hit_429") else "không",
        nu.get("throttled_waits", 0), nu.get("throttled_wait_s", 0.0)))
    print("Report: %s/replay_report.json" % args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())

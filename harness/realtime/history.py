#!/usr/bin/env python3
"""KenhLive Realtime QA — Không gian lịch sử phiên 1M-context (SessionHistory).

Cho model AI có context 1M token nhìn thấy TOÀN BỘ hành trình kiểm thử đã qua:
- Từng mission đã chạy (PASS / FAIL / UNVERIFIED / RUNNING) + mục tiêu.
- Từng bước quan sát (#step, timestamp, activity, tab, focus, dialog, OSD,
  loading, motion, action đã bấm, rule, state_changed).
- Toàn bộ defect/finding đã phát hiện (chống báo trùng) và cảnh báo lặp/kẹt.
- Chuỗi hội thoại đa lượt (multi-turn messages) giữa QA và model xuyên suốt phiên,
  giữ 100% văn bản trong ngân sách 1M token và tự động loại bỏ payload ảnh base64
  của các lượt cũ (chỉ lượt HIỆN TẠI mới mang image_url) để payload gọn, nhanh
  và không vượt giới hạn số ảnh/request của provider.
"""
import json
import os
import time

DEFAULT_CONTEXT_WINDOW_TOKENS = int(os.environ.get("QA_CONTEXT_WINDOW", "1000000"))
MAX_HISTORY_CHARS = int(os.environ.get("QA_HISTORY_MAX_CHARS", "650000"))

SYSTEM_PROMPT = """Bạn là Senior AI QA Verifier cho ứng dụng Android TV / Mobile 'KenhLive TV'.
Bạn đang vận hành trong một phiên kiểm thử liên tục có KHÔNG GIAN LỊCH SỬ 1M CONTEXT (Session History Space) ghi lại toàn bộ các mission, các bước quan sát, hành động đã thực hiện, chuyển trạng thái, phát hiện lỗi và các lượt phân tích trước đó.

NGUYÊN TẮC CỐT LÕI (GIẢM SAI LẦM TỐI ĐA):
1. ĐỐI CHIẾU HAI CHIỀU (Visual + UI Telemetry):
   - Luôn đọc khối [NGỮ CẢNH UI HIỆN TẠI] (activity, focused_sig, focused_text, has_dialog, osd_visible, loading_screen, motion, visible_texts) KÈM ảnh chụp màn hình trước khi kết luận.
   - Tuyệt đối KHÔNG bịa chữ không nhìn thấy trên ảnh; luôn trích nguyên văn text nhìn thấy vào trường quote.
2. SỬ DỤNG LỊCH SỬ PHIÊN 1M CONTEXT:
   - Đọc khối [KHÔNG GIAN LỊCH SỬ PHIÊN QA] và các lượt hội thoại trước để biết rõ màn hình nào đã đi qua, phím nào vừa bấm, có thay đổi trạng thái hay không, và những lỗi nào đã được ghi nhận.
   - Khi gợi ý hành động thoát kẹt (stuck_assist): KHÔNG lặp lại phím/hành động vừa dẫn đến `state_changed=False` trên cùng trạng thái; TUYỆT ĐỐI KHÔNG trả `SWITCH_TAB` khi đang ở `PlayerActivity` hoặc `WebPlayerActivity`.
3. PHÂN BIỆT RÕ NỘI DUNG STREAM VÀ UI APP:
   - Scoreboard đài truyền hình, logo kênh gốc (VTV/HTV/Cola/Soco...), đồng hồ trận đấu nằm trong luồng video phát sóng KHÔNG phải UI/nút bấm của KenhLive.
   - Khung đang hiện "Đang tải..." / "Đang tải luồng..." / màn đen spinner KHÔNG được xác nhận là video đang phát thật (`confirmed=false`).
4. ĐỊNH DẠNG ĐẦU RA:
   - Suy luận kỹ ở phần reasoning (nếu model hỗ trợ), sau đó trả kết quả cuối cùng là DUY NHẤT một khối JSON hợp lệ đúng schema được yêu cầu."""


def _compact_text(text, max_len=360):
    s = " ".join(str(text or "").split())
    if len(s) > max_len:
        return s[:max_len - 3] + "..."
    return s


class SessionHistory:
    """Bộ nhớ sự kiện + hội thoại đa lượt 1M-context cho toàn bộ phiên QA."""

    def __init__(self, session_id=None, context_window_tokens=DEFAULT_CONTEXT_WINDOW_TOKENS,
                 max_history_chars=MAX_HISTORY_CHARS):
        self.session_id = session_id or ("RT-%d" % int(time.time()))
        self.started_at = time.strftime("%Y-%m-%dT%H:%M:%S%z")
        self.context_window_tokens = int(context_window_tokens)
        self.max_history_chars = int(max_history_chars)
        self.missions = []
        self.steps = []
        self.findings = []
        self.vision_turns = []
        self._chat_turns = []  # [(user_text, assistant_text)] — thuần text, không giữ ảnh cũ
        self._finding_keys = set()
        self._last_state_sig = None

    # -- lifecycle / telemetry recording -------------------------------
    def start_mission(self, spec, t_offset=0.0):
        entry = {
            "name": getattr(spec, "name", str(spec)),
            "title": getattr(spec, "title", ""),
            "target_desc": getattr(spec, "target_desc", ""),
            "tab": getattr(spec, "tab", None),
            "started_t": round(float(t_offset or 0.0), 1),
            "ended_t": None,
            "outcome": "RUNNING",
            "reason": "",
            "steps": 0,
        }
        self.missions.append(entry)
        return entry

    def end_mission(self, result, t_offset=0.0):
        name = (result or {}).get("name")
        target = None
        for m in reversed(self.missions):
            if m["name"] == name:
                target = m
                break
        if target is None and name:
            target = {
                "name": name,
                "title": (result or {}).get("title", ""),
                "target_desc": "",
                "tab": None,
                "started_t": round(float(t_offset or 0.0), 1),
            }
            self.missions.append(target)
        if target is not None:
            target["ended_t"] = round(float(t_offset or 0.0), 1)
            target["outcome"] = (result or {}).get("outcome", "UNKNOWN")
            target["reason"] = _compact_text((result or {}).get("reason", ""), 260)
            target["steps"] = int((result or {}).get("steps", 0) or 0)

    def record_step(self, step_id, mission_name, obs, tab=None):
        ui = (obs or {}).get("ui_state") or {}
        act = (obs or {}).get("activity") or ""
        act_short = act.split(".")[-1] if "." in act else (act or "?")
        fsig = ui.get("focused_sig") or "NONE"
        ftext = _compact_text(ui.get("focused_text") or "", 50)
        has_dlg = bool(ui.get("has_dialog"))
        dlg_ids = list(ui.get("dialog_ids") or [])[:6]
        fhash = (obs or {}).get("frame_hash")
        sig = (act_short, fsig, has_dlg, fhash)
        state_changed = True if self._last_state_sig is None else (sig != self._last_state_sig)
        self._last_state_sig = sig

        vis_texts = []
        for _, t in (ui.get("all_visible_texts") or [])[:12]:
            ct = _compact_text(t, 40)
            if ct and ct not in vis_texts:
                vis_texts.append(ct)

        entry = {
            "step_id": int(step_id),
            "mission": str(mission_name or ""),
            "t_offset": round(float((obs or {}).get("t_offset") or 0.0), 1),
            "activity": act_short,
            "tab": tab,
            "focused_sig": fsig,
            "focused_text": ftext,
            "has_dialog": has_dlg,
            "dialog_ids": dlg_ids,
            "osd_visible": bool(ui.get("osd_visible")),
            "loading_screen": bool((obs or {}).get("loading_screen")),
            "motion": (obs or {}).get("motion"),
            "motion_delta": (
                round(float(obs["motion_delta"]), 2)
                if isinstance((obs or {}).get("motion_delta"), (int, float)) and obs["motion_delta"] >= 0
                else None
            ),
            "visible_texts": vis_texts,
            "action": None,
            "rule": None,
            "action_thought": None,
            "state_changed": state_changed,
            "findings_count": len((obs or {}).get("findings") or []),
            "frame_ref": (obs or {}).get("frame_ref") or "",
        }
        self.steps.append(entry)
        return entry

    def record_action(self, step_id, action):
        if action is None or not self.steps:
            return
        target = None
        for s in reversed(self.steps):
            if s["step_id"] == int(step_id):
                target = s
                break
        if target is None:
            target = self.steps[-1]
        a_type = getattr(action, "type", None) or (action.get("type") if isinstance(action, dict) else "")
        a_param = getattr(action, "param", None) or (action.get("param") if isinstance(action, dict) else "")
        a_rule = getattr(action, "rule", None) or (action.get("rule") if isinstance(action, dict) else "")
        a_thought = getattr(action, "thought", None) or (action.get("thought") if isinstance(action, dict) else "")
        target["action"] = ("%s %s" % (a_type, a_param)).strip()
        target["rule"] = str(a_rule or "")
        target["action_thought"] = _compact_text(a_thought or "", 140)

    def record_finding(self, finding, mission_name=None):
        if not isinstance(finding, dict):
            return
        ev = finding.get("evidence") or {}
        key = (
            str(finding.get("area") or ""),
            str(finding.get("issue") or ""),
            str(ev.get("frame") or ""),
        )
        if key in self._finding_keys:
            return
        self._finding_keys.add(key)
        self.findings.append({
            "severity": str(finding.get("severity") or "MEDIUM").upper(),
            "area": str(finding.get("area") or ""),
            "issue": _compact_text(finding.get("issue") or "", 160),
            "detail": _compact_text(finding.get("detail") or "", 200),
            "frame": str(ev.get("frame") or ""),
            "video_t": ev.get("video_t"),
            "mission": str(mission_name or ""),
        })

    # -- vision multi-turn conversation memory -------------------------
    def record_vision_turn(self, reason, user_text, assistant_text, parsed=None, meta=None):
        meta = meta if isinstance(meta, dict) else {}
        turn_id = len(self.vision_turns) + 1
        frame_ref = meta.get("frame_ref") or ""
        step_id = meta.get("step_id")
        mission = meta.get("mission") or ""
        t_offset = meta.get("t_offset")
        compact_user = "[Lượt Vision #%d · reason=%s · mission=%s · step=%s · frame=%s]\n%s\n[Ảnh frame %s đã được phân tích]" % (
            turn_id, reason, mission or "?", step_id if step_id is not None else "?",
            frame_ref or "?", _compact_text(user_text, 900), frame_ref or ("#%d" % turn_id)
        )
        compact_assistant = _compact_text(assistant_text or json.dumps(parsed or {}, ensure_ascii=False), 1200)
        self._chat_turns.append((compact_user, compact_assistant))
        self._trim_chat_turns()

        verdict = ""
        if isinstance(parsed, dict):
            if "confirmed" in parsed:
                verdict = "confirmed=%s quote=%s" % (parsed.get("confirmed"), _compact_text(parsed.get("quote", ""), 80))
            elif "found" in parsed:
                verdict = "found=%s sev=%s detail=%s" % (
                    parsed.get("found"), parsed.get("severity", ""), _compact_text(parsed.get("detail", ""), 100))
            elif "action" in parsed:
                verdict = "%s %s" % (parsed.get("action", ""), parsed.get("param", ""))
        self.vision_turns.append({
            "call_id": turn_id,
            "reason": str(reason),
            "mission": str(mission),
            "step_id": step_id,
            "t_offset": t_offset,
            "frame_ref": str(frame_ref),
            "prompt_summary": _compact_text(user_text, 220),
            "verdict": verdict or _compact_text(assistant_text, 140),
            "ok": parsed is not None,
        })

    def _chat_chars(self):
        return sum(len(u) + len(a) for u, a in self._chat_turns)

    def _trim_chat_turns(self):
        # Giữ lịch sử đa lượt trong không gian 1M (~650k ký tự thuần text)
        budget = max(8000, int(self.max_history_chars * 0.65))
        while len(self._chat_turns) > 1 and self._chat_chars() > budget:
            self._chat_turns.pop(0)

    # -- rendering episodic memory & multi-turn messages ---------------
    def render_episodic_memory(self, current_mission=None, max_chars=240000):
        lines = [
            "Session: %s | Context window: %d tokens | Missions: %d | Steps: %d | Findings: %d | Vision calls: %d" % (
                self.session_id, self.context_window_tokens,
                len(self.missions), len(self.steps), len(self.findings), len(self.vision_turns)
            )
        ]
        if self.missions:
            lines.append("\n1) TRẠNG THÁI CÁC MISSION ĐÃ/ĐANG CHẠY:")
            for m in self.missions:
                tag = "[ĐANG CHẠY] " if (current_mission and m["name"] == current_mission and m["outcome"] == "RUNNING") else ""
                rsn = (" — %s" % m["reason"]) if m.get("reason") else ""
                lines.append("  - %s%s (%s): %s | steps=%d%s" % (
                    tag, m["name"], m["title"], m["outcome"], m.get("steps", 0), rsn
                ))

        if self.findings:
            lines.append("\n2) CÁC DEFECT ĐÃ PHÁT HIỆN (KHÔNG BÁO TRÙNG):")
            for idx, f in enumerate(self.findings, 1):
                lines.append("  - #%d [%s] %s | %s (frame=%s @ %ss, mission=%s)" % (
                    idx, f["severity"], f["area"], f["issue"],
                    f["frame"] or "?", f["video_t"] if f["video_t"] is not None else "?",
                    f["mission"] or "?"
                ))

        if self.steps:
            lines.append("\n3) NHẬT KÝ TOÀN BỘ CÁC BƯỚC ĐÃ LÀM (THEO THỨ TỰ THỜI GIAN):")
            no_change_tail = 0
            for st in reversed(self.steps):
                if not st.get("state_changed"):
                    no_change_tail += 1
                else:
                    break
            for st in self.steps:
                flags = []
                if st["has_dialog"]:
                    flags.append("DLG(%s)" % ",".join(st["dialog_ids"][:2]))
                if st["osd_visible"]:
                    flags.append("OSD")
                if st["loading_screen"]:
                    flags.append("LOADING")
                if st["motion"] is True:
                    flags.append("MOTION=%.2f%%" % (st["motion_delta"] or 0.0))
                elif st["motion"] is False:
                    flags.append("STILL")
                act_str = st["action"] or "NONE"
                if st["rule"]:
                    act_str += " [%s]" % st["rule"]
                chg = "changed" if st["state_changed"] else "UNCHANGED"
                lines.append("  - #%03d t=%.1fs %s | act=%s tab=%s | focus=%s('%s') | %s | -> %s (%s)" % (
                    st["step_id"], st["t_offset"], st["mission"],
                    st["activity"], st["tab"] if st["tab"] is not None else "?",
                    st["focused_sig"], st["focused_text"],
                    ",".join(flags) or "normal", act_str, chg
                ))
            if no_change_tail >= 2:
                lines.append("  ! CẢNH BÁO KẸT: %d bước gần nhất KHÔNG ĐỔI TRẠNG THÁI (tránh lặp lại cùng hành động vừa thử)." % no_change_tail)

        if self.vision_turns:
            lines.append("\n4) TÓM TẮT CÁC LƯỢT VISION TRƯỚC ĐÓ:")
            for vt in self.vision_turns[-40:]:
                lines.append("  - Vision #%d (%s @ step=%s, frame=%s): %s" % (
                    vt["call_id"], vt["reason"],
                    vt["step_id"] if vt["step_id"] is not None else "?",
                    vt["frame_ref"] or "?", vt["verdict"]
                ))

        text = "\n".join(lines)
        if len(text) > max_chars:
            # Nếu quá dài bất thường, giữ phần đầu (missions + findings) và phần bước gần nhất
            head = "\n".join(lines[:min(len(lines), 45)])
            tail = text[-(max_chars - len(head) - 120):]
            text = head + "\n... [đã rút gọn phần giữa vượt ngưỡng] ...\n" + tail
        return text

    def build_messages(self, current_prompt, b64_image=None, context=None):
        """Tạo danh sách messages OpenAI-compatible: system + lịch sử đa lượt (text-only) + lượt hiện tại (kèm ảnh hiện tại)."""
        context = context if isinstance(context, dict) else {}
        msgs = [{"role": "system", "content": SYSTEM_PROMPT}]

        # Giữ toàn bộ các lượt hội thoại trước (thuần text — không chứa base64 image cũ)
        used_chars = len(SYSTEM_PROMPT)
        memory_block = self.render_episodic_memory(current_mission=context.get("mission"))
        ctx_lines = []
        if context:
            ctx_lines.append("[NGỮ CẢNH UI HIỆN TẠI]")
            for k in ("mission", "step_id", "t_offset", "frame_ref", "activity", "tab",
                      "focused_sig", "focused_text", "has_dialog", "dialog_ids",
                      "osd_visible", "loading_screen", "motion", "motion_delta", "visible_texts"):
                if k in context and context[k] is not None and context[k] != "":
                    ctx_lines.append("- %s: %s" % (k, context[k]))
        ctx_block = "\n".join(ctx_lines)

        current_text = "[KHÔNG GIAN LỊCH SỬ PHIÊN QA (1M CONTEXT)]\n%s\n\n%s\n\n[NHIỆM VỤ HIỆN TẠI]\n%s" % (
            memory_block, ctx_block, current_prompt
        )
        remaining_budget = max(4000, self.max_history_chars - used_chars - len(current_text))

        retained_pairs = []
        acc = 0
        for u_txt, a_txt in reversed(self._chat_turns):
            pair_len = len(u_txt) + len(a_txt)
            if acc + pair_len > remaining_budget and retained_pairs:
                break
            retained_pairs.append((u_txt, a_txt))
            acc += pair_len
        retained_pairs.reverse()

        for u_txt, a_txt in retained_pairs:
            msgs.append({"role": "user", "content": u_txt})
            msgs.append({"role": "assistant", "content": a_txt})

        if b64_image:
            content = [
                {"type": "text", "text": current_text},
                {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,%s" % b64_image}},
            ]
        else:
            content = current_text
        msgs.append({"role": "user", "content": content})
        return msgs

    def stats(self):
        episodic_chars = len(self.render_episodic_memory())
        total_chars = episodic_chars + self._chat_chars()
        return {
            "session_id": self.session_id,
            "context_window_tokens": self.context_window_tokens,
            "missions_recorded": len(self.missions),
            "steps_recorded": len(self.steps),
            "findings_recorded": len(self.findings),
            "vision_turns": len(self.vision_turns),
            "chat_turns_retained": len(self._chat_turns),
            "estimated_chars": total_chars,
            "estimated_tokens": max(1, total_chars // 4),
        }

    def save(self, out_dir):
        os.makedirs(out_dir, exist_ok=True)
        json_path = os.path.join(out_dir, "session_history.json")
        md_path = os.path.join(out_dir, "session_history.md")
        payload = {
            "session_id": self.session_id,
            "started_at": self.started_at,
            "stats": self.stats(),
            "missions": self.missions,
            "steps": self.steps,
            "findings": self.findings,
            "vision_turns": self.vision_turns,
        }
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        md_doc = "# KenhLive QA · Session History Space (1M Context)\n\n" + self.render_episodic_memory(max_chars=500000) + "\n"
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md_doc)
        return json_path, md_path

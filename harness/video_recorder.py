#!/usr/bin/env python3
"""
KenhLive Video Recorder — Quay toàn bộ video màn hình Android TV emulator bằng adb screenrecord.
Hỗ trợ quay dài liên tục (vượt qua giới hạn 3 phút của Android) bằng cách chia chunk và ghép bằng ffmpeg.
Tự động sinh video streamable (+faststart), nén tối ưu dung lượng (<50MB) và video tua nhanh Timelapse 10x.
"""

import glob
import json
import os
import subprocess
import threading
import time


class VideoRecorder:
    def __init__(self, serial=None, out_dir="/tmp/qa_report", max_total_seconds=7200):
        self.serial = serial
        self.adb = f"adb -s {serial}" if serial else "adb"
        self.out_dir = os.path.abspath(out_dir)
        os.makedirs(self.out_dir, exist_ok=True)
        self.max_total_seconds = max_total_seconds
        self.stop_event = threading.Event()
        self.worker_thread = None
        self.remote_chunks = []
        self.local_chunks = []
        self.final_mp4 = os.path.join(self.out_dir, "full_qa_tour.mp4")
        self.timelapse_mp4 = os.path.join(self.out_dir, "qa_timelapse.mp4")
        self.is_recording = False
        self._keep_chunks_on_failure = False
        # Hệ số tốc độ tour cuối (1.0 = không tăng tốc). Judge CẦN con số này
        # để cắt defect reel đúng vị trí: video_t là thời gian THẬT của run, vị
        # trí trong file = video_t / speed_factor (CI-T3: reel cắt video_t
        # trực tiếp vào file 4x -> 3/5 đoạn rỗng, 2/5 lệch nội dung).
        self._speed_factor = 1.0
        self._recorded_seconds = 0.0
        self._start_wall = 0.0  # KL8 fix loop 2 (F67c): mốc wall-clock để tính độ phủ video
        self._norm_chunks = []  # KL8 fix loop 2 (F67c): chunk đã chuẩn hóa (CFR) để ghép
        self._current_remote = None  # CI-T5 mục 8: chunk đang quay dở lúc dừng
        self._current_started_at = 0.0
        self._finalize_timeout_s = 60.0  # chờ chunk cuối finalize tối đa
        # (CI-T6 mục 3: 20s cũ chưa đủ để moov flush xong trong ca xấu;
        # chờ này chỉ tốn thời gian khi chunk lỗi — chunk tốt về ngay sau
        # khi size ổn định + probe thấy moov, thường ~2-4s).

    def start(self):
        print(f"📹 [VIDEO RECORDER] Bắt đầu quay toàn bộ quá trình test Android TV 1080p...", flush=True)
        # Xóa các file quay cũ còn sót trên thiết bị
        subprocess.run(f"{self.adb} shell rm -f /sdcard/qa_rec_*.mp4", shell=True, capture_output=True)
        self.stop_event.clear()
        self.is_recording = True
        self._start_wall = time.time()
        self.worker_thread = threading.Thread(target=self._record_loop, daemon=True)
        self.worker_thread.start()
        time.sleep(1.5)  # Chờ screenrecord khởi động thực tế trên emulator

    def _record_loop(self):
        idx = 0
        t0 = time.time()
        fast_fail_streak = 0
        while not self.stop_event.is_set() and (time.time() - t0 < self.max_total_seconds):
            idx += 1
            remote_path = f"/sdcard/qa_rec_{idx:02d}.mp4"
            self.remote_chunks.append(remote_path)
            self._current_remote = remote_path  # CI-T5 mục 8: chunk đang quay
            self._current_started_at = time.time()
            # adb screenrecord trên emulator Android TV: 1280x720 2.5Mbps (tránh tràn buffer phần mềm OMX err=-10005)
            cmd = f"{self.adb} shell screenrecord --time-limit 175 --bit-rate 2500000 --size 1280x720 {remote_path}"
            t_chunk0 = time.time()
            p = subprocess.Popen(cmd, shell=True)
            while p.poll() is None:
                if self.stop_event.is_set():
                    # Gửi SIGINT (signal 2) để screenrecord đóng file MP4 hợp lệ
                    subprocess.run(f"{self.adb} shell 'pkill -2 screenrecord 2>/dev/null || kill -2 $(pidof screenrecord) 2>/dev/null || true'", shell=True, capture_output=True)
                    try:
                        p.wait(timeout=6)
                    except Exception:
                        pass
                    # CI-T5 mục 8: chờ screenrecord thoát HẲN (moov atom chỉ
                    # được ghi khi thoát sạch) thay vì giết client adb rồi
                    # trả về ngay — file pull về lúc đó sẽ thiếu moov (lỗi
                    # CI-T4 chunk_08: 'moov atom not found', mất ~160s cuối).
                    self._wait_for_screenrecord_exit(timeout=10.0)
                    return
                time.sleep(0.5)
            # KL8 fix loop 2 (F67c): screenrecord chết ngay (vd /sdcard đầy,
            # "already recording") thì vòng lặp cũ quay tít tạo chunk rỗng và
            # spam adb suốt phiên. Chờ 5s rồi mới thử chunk sau.
            if time.time() - t_chunk0 < 5.0:
                fast_fail_streak += 1
                if fast_fail_streak == 1 or fast_fail_streak % 5 == 0:
                    print(f"⚠️ [VIDEO RECORDER] screenrecord chết nhanh (chunk {idx}, streak {fast_fail_streak}) — chờ 5s trước chunk sau.", flush=True)
                time.sleep(5.0)
            else:
                fast_fail_streak = 0

    def _screenrecord_running(self):
        """True khi còn tiến trình screenrecord trên thiết bị."""
        try:
            res = subprocess.run(f"{self.adb} shell pidof screenrecord",
                                 shell=True, capture_output=True, text=True)
            return bool((res.stdout or "").strip())
        except Exception:
            return False

    def _wait_for_screenrecord_exit(self, timeout=10.0):
        """Chờ screenrecord thoát hẳn (moov chỉ ghi khi thoát sạch)."""
        deadline = time.time() + timeout
        while time.time() < deadline:
            if not self._screenrecord_running():
                return True
            time.sleep(0.5)
        return False

    def _device_file_size(self, remote):
        """Kích thước file trên thiết bị (byte) hoặc None khi không đọc được
        (file chưa xuất hiện / stat không hỗ trợ — caller coi như chưa sẵn)."""
        try:
            res = subprocess.run(f"{self.adb} shell stat -c %s {remote}",
                                 shell=True, capture_output=True, text=True)
            return int((res.stdout or "").strip())
        except Exception:
            return None

    def _wait_chunk_finalized(self, remote, timeout=20.0):
        """Chờ chunk đang quay dở được finalize (CI-T5 mục 8, lỗi CI-T4):
        screenrecord chỉ ghi moov atom khi thoát sạch (SIGINT); stop_and_save
        cũ ls + pull ngay sau join nên tóm được file đang ghi dở (không moov)
        rồi rm luôn bản gốc trên máy -> chunk cuối mất hẳn (CI-T4: chunk_08
        ~160s cuối — SEARCH + STRESS — 'moov atom not found' ở bước chuẩn
        hóa, video chỉ 1225/1534s). Chờ tới khi (a) không còn tiến trình
        screenrecord VÀ (b) kích thước file ổn định qua 2 lần đo cách nhau
        1s. Trả True nếu file đã ổn định, False nếu hết timeout (caller vẫn
        pull thử — chunk xấu sẽ tự rớt ở bước chuẩn hóa, không phá cả lần
        ghép). Giữ nguyên fix _dur + chuẩn hóa CFR (F67c)."""
        deadline = time.time() + timeout
        last_size = -1
        stable = 0
        while time.time() < deadline:
            if self._screenrecord_running():
                time.sleep(1.0)
                continue
            size = self._device_file_size(remote)
            if size is None or size <= 0:
                time.sleep(1.0)  # file chưa xuất hiện / chưa có dữ liệu
                continue
            if size == last_size:
                stable += 1
                if stable >= 1:  # 2 lần đo liên tiếp cùng size, cách nhau 1s
                    return True
            else:
                stable = 0
            last_size = size
            time.sleep(1.0)
        return False

    def _wait_chunk_finalized_moov(self, remote, timeout=60.0):
        """Chờ chunk cuối finalize tới khi ffprobe THẤY moov atom (CI-T6
        mục 3). CI-T5: chunk cuối vẫn mất ở bước chuẩn hóa vì 'moov atom
        not found' (video chỉ 700.5/843s = 83%) dù mục 8 đã chờ 'size ổn
        định 2 lần đọc' — size ổn định KHÔNG chứng minh moov đã ghi (file
        vẫn có thể đang ghi dở / pull bị cắt ngắn). Hai pha:
        (1) chờ size ổn định như cũ (_wait_chunk_finalized);
        (2) pull thử về file tạm + ffprobe: có moov (has_video và dur > 0)
        thì xong; chưa có thì chờ 2s rồi pull lại (tối đa 30s / 5 lần) —
        moov có thể flush muộn sau khi tiến trình thoát.
        Trả True nếu chunk cuối đã có moov; False nếu hết timeout (caller
        vẫn pull thử như cũ — chunk xấu sẽ tự rớt ở bước chuẩn hóa, không
        phá cả lần ghép). Timeout mặc định 60s (mục 8 cũ: 20s)."""
        if not self._wait_chunk_finalized(remote, timeout=timeout):
            print(f"📹 [VIDEO RECORDER] Chunk cuối {os.path.basename(remote)}: "
                  f"không ổn định sau {timeout:.0f}s — bỏ qua chờ moov, pull thử.",
                  flush=True)
            return False
        probe_tmp = os.path.join(self.out_dir, "_moov_probe.mp4")
        deadline = time.time() + 30.0
        attempts = 0
        while time.time() < deadline and attempts < 5:
            attempts += 1
            try:
                subprocess.run(f"{self.adb} pull {remote} {probe_tmp}",
                               shell=True, capture_output=True)
                dur, has_video, _nf = self._probe_video(probe_tmp)
                if has_video and dur > 0:
                    print(f"📹 [VIDEO RECORDER] Chunk cuối {os.path.basename(remote)}: "
                          f"đã có moov (ffprobe đọc được {dur:.1f}s) sau {attempts} lần pull thử.",
                          flush=True)
                    return True
                print(f"📹 [VIDEO RECORDER] Chunk cuối {os.path.basename(remote)}: "
                      f"pull thử lần {attempts} chưa thấy moov — chờ 2s rồi pull lại.",
                      flush=True)
            except Exception as e:
                print(f"📹 [VIDEO RECORDER] Lỗi khi probe moov chunk cuối: {e}", flush=True)
            time.sleep(2.0)
        print(f"📹 [VIDEO RECORDER] Chunk cuối {os.path.basename(remote)}: "
              f"KHÔNG có moov sau {attempts} lần pull thử — vẫn pull về, "
              f"chunk xấu sẽ tự rớt ở bước chuẩn hóa (video có thể thiếu đoạn cuối).",
              flush=True)
        return False

    def _probe_video(self, path):
        """(duration_s, has_video_stream, nb_frames) qua ffprobe JSON.
        File hỏng/không đọc được -> (0.0, False, 0)."""
        try:
            pr = subprocess.run(
                ["ffprobe", "-v", "error",
                 "-show_entries", "format=duration",
                 "-show_entries", "stream=codec_type,nb_frames",
                 "-of", "json", path],
                capture_output=True, text=True)
            data = json.loads(pr.stdout or "{}")
            dur = float((data.get("format") or {}).get("duration") or 0.0)
            has_video = any(s.get("codec_type") == "video" for s in data.get("streams", []))
            nf = 0
            for s in data.get("streams", []):
                if s.get("codec_type") == "video":
                    try:
                        nf = int(s.get("nb_frames") or 0)
                    except (TypeError, ValueError):
                        nf = 0
                    break
            return dur, has_video, nf
        except Exception:
            return 0.0, False, 0

    def _concat_norm(self, norm_files, out_path):
        """Ghép các chunk đã chuẩn hóa (cùng codec, CFR) bằng stream copy
        (concat demuxer tự dời timestamp từng file). Nếu thời lượng ra
        thiếu so với tổng đầu vào thì thử lại bằng re-encode concat.
        Trả về (out_path, duration_s); lỗi -> (out_path, 0.0) + log stderr."""
        expected = sum(self._probe_video(c)[0] for c in norm_files)
        concat_list = os.path.join(self.out_dir, "concat.txt")
        with open(concat_list, "w") as f:
            for c in norm_files:
                f.write(f"file '{os.path.abspath(c)}'\n")
        res = subprocess.run(
            ["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0",
             "-i", concat_list, "-c", "copy", "-movflags", "+faststart", out_path],
            capture_output=True, text=True)
        dur, _hv, _nf = self._probe_video(out_path)
        if res.returncode == 0 and expected > 0 and dur >= 0.9 * expected:
            return out_path, dur
        if res.returncode != 0:
            print(f"⚠️ [VIDEO RECORDER] Ghep stream-copy that bai (rc={res.returncode}): {(res.stderr or '')[-400:]}", flush=True)
        else:
            print(f"⚠️ [VIDEO RECORDER] Ghep stream-copy thieu thoi luong ({dur:.1f}s < {expected:.1f}s) — thu lai bang re-encode.", flush=True)
        res2 = subprocess.run(
            ["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0",
             "-fflags", "+genpts", "-i", concat_list,
             "-c:v", "libx264", "-preset", "veryfast", "-crf", "26",
             "-pix_fmt", "yuv420p", "-movflags", "+faststart", out_path],
            capture_output=True, text=True)
        if res2.returncode != 0:
            print(f"⚠️ [VIDEO RECORDER] Ghep re-encode that bai (rc={res2.returncode}): {(res2.stderr or '')[-400:]}", flush=True)
            return out_path, 0.0
        dur, _hv, _nf = self._probe_video(out_path)
        if expected > 0 and dur < 0.9 * expected:
            # Ghép "thành công" nhưng thiếu thời lượng (vd 1 chunk hỏng giữa
            # chừng bị bỏ qua) — trả 0 để caller giữ chunk chuẩn hóa dài nhất.
            print(f"⚠️ [VIDEO RECORDER] Ghep re-encode thieu thoi luong ({dur:.1f}s < {expected:.1f}s).", flush=True)
            return out_path, 0.0
        return out_path, dur

    def stop_and_save(self):
        if not self.is_recording:
            return None
        self.is_recording = False
        print("📹 [VIDEO RECORDER] Đang dừng quay màn hình và thu thập video từ thiết bị...", flush=True)
        self.stop_event.set()
        subprocess.run(f"{self.adb} shell 'pkill -2 screenrecord 2>/dev/null || kill -2 $(pidof screenrecord) 2>/dev/null || true'", shell=True, capture_output=True)
        if self.worker_thread:
            self.worker_thread.join(timeout=8)
        time.sleep(2.0)  # Chờ mp4 header được finalize trên Android filesystem

        # CI-T6 mục 3: chờ chunk đang quay dở finalize tới khi ffprobe THẤY
        # moov (không chỉ size ổn định như CI-T5 mục 8 — video CI-T5 vẫn
        # chỉ 83% vì chunk cuối mất ở normalize do 'moov atom not found').
        current = getattr(self, "_current_remote", None)
        if current:
            subprocess.run(f"{self.adb} shell 'pkill -2 screenrecord 2>/dev/null || kill -2 $(pidof screenrecord) 2>/dev/null || true'", shell=True, capture_output=True)
            ok = self._wait_chunk_finalized_moov(current, timeout=self._finalize_timeout_s)
            print(f"📹 [VIDEO RECORDER] Chunk cuối {os.path.basename(current)}: "
                  f"{'đã finalize (có moov), kéo về ghép cùng' if ok else 'CHƯA chắc có moov sau %.0fs — vẫn pull thử, chunk xấu sẽ tự rớt ở bước chuẩn hóa' % self._finalize_timeout_s}", flush=True)

        # Tìm toàn bộ các chunk thực tế có trên thiết bị
        res = subprocess.run(f"{self.adb} shell 'ls /sdcard/qa_rec_*.mp4 2>/dev/null'", shell=True, capture_output=True, text=True)
        device_files = [line.strip() for line in res.stdout.splitlines() if line.strip().endswith(".mp4")]
        all_remotes = sorted(list(set(self.remote_chunks + device_files)))

        # Kéo các chunks về local (kèm kiểm tra đủ byte: pull thiếu thì pull
        # lại 1 lần; chỉ xóa bản trên máy khi bản local đã đủ — tránh mất
        # chunk vì pull dở, như chunk cuối CI-T4).
        for i, remote in enumerate(all_remotes):
            local_path = os.path.join(self.out_dir, f"chunk_{i+1:02d}.mp4")
            subprocess.run(f"{self.adb} pull {remote} {local_path}", shell=True, capture_output=True)
            want = self._device_file_size(remote)
            got = os.path.getsize(local_path) if os.path.exists(local_path) else 0
            if want and got < want:
                print(f"⚠️ [VIDEO RECORDER] Pull thieu {os.path.basename(local_path)} ({got}/{want} byte) — pull lai.", flush=True)
                subprocess.run(f"{self.adb} pull {remote} {local_path}", shell=True, capture_output=True)
                got = os.path.getsize(local_path) if os.path.exists(local_path) else 0
            if got > 2000:
                self.local_chunks.append(local_path)
            if got and (not want or got >= want):
                subprocess.run(f"{self.adb} shell rm -f {remote}", shell=True, capture_output=True)

        if not self.local_chunks:
            duration_sec = 0.0
            print("⚠️ [VIDEO RECORDER] Không kéo được chunk video từ thiết bị, kích hoạt cơ chế ghép video từ ảnh chụp màn hình (Screenshot Stitching)...", flush=True)
            shots_dir = os.path.join(self.out_dir, "shots")
            shot_files = sorted(glob.glob(os.path.join(shots_dir, "*.jpg")) + glob.glob(os.path.join(shots_dir, "*.png")))
            if shot_files:
                img_list = os.path.join(self.out_dir, "img_list.txt")
                with open(img_list, "w") as f:
                    for s in shot_files:
                        f.write(f"file '{s}'\nduration 1.8\n")
                    f.write(f"file '{shot_files[-1]}'\n")
                cmd_img = f"ffmpeg -y -f concat -safe 0 -i {img_list} -vf 'scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2' -c:v libx264 -preset veryfast -r 25 -pix_fmt yuv420p -movflags +faststart {self.final_mp4}"
                subprocess.run(cmd_img, shell=True, capture_output=True)
            if not os.path.exists(self.final_mp4) or os.path.getsize(self.final_mp4) < 2000:
                return None
            raw_full = self.final_mp4
            # Stitch fallback: mỗi shot 1.8s — nội dung rải khắp phiên nhưng
            # chỉ là slideshow, tính là video CHƯA ĐỦ ở cuối hàm.
            raw_duration_sec = len(shot_files) * 1.8 if shot_files else 0.0
        else:
            # Ghep video (fix loop 2, F67c): moi chunk screenrecord co
            # timestamp rieng bat dau tu 0 nen stream-copy hay loi timestamp.
            # Run 42963719447: concat ghep loi (hoac chunk hong khien ghep
            # loi) roi fallback GIU 1 chunk duy nhat (175s, mang ca tag
            # com.android.version) -> "full tour" 169s cho run 85 phut.
            # Ghep kieu moi: validate + CHUAN HOA TUNG chunk rieng (CFR 30fps)
            # truoc — 1 chunk hong chi lam mat chunk do, khong pha ca lan
            # ghep — roi moi concat cac file chuan hoa. Loi ffmpeg nao cung
            # ghi stderr ra log (truoc day capture_output roi bo di, ca
            # timelapse mat cung khong ai biet vi sao).
            raw_full = os.path.join(self.out_dir, "raw_full.mp4")
            duration_sec = 0.0

            def _dur(path):
                """Đọc thời lượng chunk. Trả -1.0 nếu KHÔNG ĐỌC ĐƯỢC (không rõ),
                thay vì 0.0. Lỗi CI-T1 + cả run cũ 42963719447: chunk
                screenrecord đọc format=duration ra N/A trên runner CI nên bị
                loại hết (30 lần 'Bo chunk hong'), video chỉ còn chunk 1
                (176s) trong khi run dài 15-89 phút."""
                for args in (
                        f"ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 \"{path}\"",
                        f"ffprobe -v error -select_streams v:0 -show_entries stream=duration -of default=noprint_wrappers=1:nokey=1 \"{path}\""):
                    try:
                        pr = subprocess.run(args, shell=True, capture_output=True, text=True)
                        val = float((pr.stdout or "").strip())
                        if val > 0:
                            return val
                    except Exception:
                        pass
                print(f"⚠️ [VIDEO RECORDER] Không đọc được duration của {os.path.basename(path)} (ffprobe trả N/A) — giữ lại để ghép thử, không loại.", flush=True)
                return -1.0

            valid = []
            for c in self.local_chunks:
                # _probe_video trả (0.0, False, 0) cho chunk thật mà ffprobe
                # chỉ đọc ra N/A (float("N/A") raise) — KHÔNG được loại ngay
                # như validation cũ, nếu không lỗi CI-T1 tái diễn. Kiểm tra
                # bằng _dur + kích thước file trước khi loại; chunk giữ lại
                # vẫn qua bước chuẩn hóa từng chunk (F67c) — chunk rác thật
                # sẽ tự rớt ở đó, không phá cả lần ghép.
                dur, has_video, nframes = self._probe_video(c)
                if dur > 1.0 and has_video:
                    if nframes and dur > 0 and nframes / dur < 5.0:
                        print(f"⚠️ [VIDEO RECORDER] Chunk fps thap: {os.path.basename(c)} ({nframes / dur:.1f} fps, {dur:.0f}s) — emulator screenrecord doi CPU, video se giat.", flush=True)
                    valid.append((c, dur))
                    continue
                d2 = _dur(c)
                if (d2 > 1.0 or d2 < 0) and os.path.getsize(c) > 2000:
                    # d2 < 0 = không đọc được nhưng file có thật: giữ lại.
                    valid.append((c, d2))
                else:
                    print(f"⚠️ [VIDEO RECORDER] Bo chunk hong: {os.path.basename(c)} (duration {dur:.1f}s, video={has_video})", flush=True)
            if not valid:
                print("⚠️ [VIDEO RECORDER] Khong co chunk nao hop le, giu chunk dau tien.", flush=True)
                valid = [(self.local_chunks[0], 0.0)]
                self._keep_chunks_on_failure = True

            # Chuẩn hóa từng chunk riêng (CFR 30fps, cùng 1280x720) — chunk
            # nào re-encode lỗi thì bỏ chunk đó, không phá cả lần ghép.
            self._norm_chunks = []
            for i, (c, _d) in enumerate(valid):
                out = os.path.join(self.out_dir, f"norm_{i + 1:02d}.mp4")
                res_norm = subprocess.run(
                    ["ffmpeg", "-y", "-v", "error", "-fflags", "+genpts", "-i", c,
                     "-vf", "scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2,fps=30",
                     "-c:v", "libx264", "-preset", "veryfast", "-crf", "26",
                     "-pix_fmt", "yuv420p", out],
                    capture_output=True, text=True)
                if res_norm.returncode != 0 or not os.path.exists(out) or os.path.getsize(out) < 2000:
                    print(f"⚠️ [VIDEO RECORDER] Chuan hoa chunk loi, bo: {os.path.basename(c)}: {(res_norm.stderr or '')[-300:]}", flush=True)
                    continue
                self._norm_chunks.append(out)
            if not self._norm_chunks:
                print("⚠️ [VIDEO RECORDER] Khong chuan hoa duoc chunk nao, giu chunk dai nhat.", flush=True)
                # Duration chưa biết (-1) thì so bằng kích thước file (fix QA).
                raw_full = max(valid, key=lambda x: (x[1], os.path.getsize(x[0])))[0]
                duration_sec = max(valid, key=lambda x: (x[1], os.path.getsize(x[0])))[1]
                self._keep_chunks_on_failure = True
            elif len(self._norm_chunks) == 1:
                raw_full = self._norm_chunks[0]
                duration_sec, _hv, _nf = self._probe_video(raw_full)
            else:
                raw_full, duration_sec = self._concat_norm(self._norm_chunks, raw_full)
                if duration_sec <= 1.0:
                    print("⚠️ [VIDEO RECORDER] Ghep cac chunk chuan hoa that bai — giu chunk chuan hoa DAI NHAT.", flush=True)
                    raw_full = max(self._norm_chunks, key=lambda p: self._probe_video(p)[0])
                    duration_sec, _hv, _nf = self._probe_video(raw_full)
                    self._keep_chunks_on_failure = True
            raw_duration_sec = duration_sec

            # Kiểm tra thời lượng và kích thước file
            raw_size = os.path.getsize(raw_full) if os.path.exists(raw_full) else 0
            print(f"🎬 [VIDEO] File raw hoàn chỉnh: {raw_size//(1024*1024)}MB, thời lượng: {duration_sec:.1f}s", flush=True)

            # Nếu thời lượng dài (> 10 phút do thời gian chờ AI suy nghĩ), tự động tăng tốc 6x
            # để video toàn cảnh trọn vẹn từ đầu đến cuối chỉ dài 5-8 phút, xem được toàn bộ các thao tác và < 40MB
            if duration_sec > 600.0 or raw_size > 45 * 1024 * 1024:
                speed_factor = max(4.0, min(8.0, duration_sec / 360.0))
                self._speed_factor = speed_factor
                self._recorded_seconds = duration_sec
                pts_factor = 1.0 / speed_factor
                print(f"🎬 [VIDEO] Tối ưu hóa thời lượng tour ({duration_sec:.0f}s -> {duration_sec*pts_factor:.0f}s, speed {speed_factor:.1f}x) để xem trọn vẹn mọi thao tác trên Telegram...", flush=True)
                cmd_opt = f"ffmpeg -y -i {raw_full} -filter:v 'setpts={pts_factor:.4f}*PTS' -c:v libx264 -preset veryfast -crf 26 -pix_fmt yuv420p -movflags +faststart {self.final_mp4}"
                res_opt = subprocess.run(cmd_opt, shell=True, capture_output=True, text=True)
                if res_opt.returncode != 0:
                    print(f"⚠️ [VIDEO RECORDER] Tang toc loi (rc={res_opt.returncode}): {(res_opt.stderr or '')[-300:]}", flush=True)
            else:
                # Stream-copy nhanh kèm di chuyển moov atom lên đầu (+faststart) để xem online không cần đợi tải hết
                cmd_fast = f"ffmpeg -y -i {raw_full} -c copy -movflags +faststart {self.final_mp4}"
                res_fast = subprocess.run(cmd_fast, shell=True, capture_output=True, text=True)
                if not os.path.exists(self.final_mp4) or os.path.getsize(self.final_mp4) < 2000:
                    if res_fast.returncode != 0:
                        print(f"⚠️ [VIDEO RECORDER] Stream-copy that bai (rc={res_fast.returncode}): {(res_fast.stderr or '')[-300:]}", flush=True)
                    # Nếu -c copy gặp lỗi bitstream, fallback re-encode veryfast
                    cmd_reencode = f"ffmpeg -y -i {raw_full} -c:v libx264 -preset veryfast -crf 26 -pix_fmt yuv420p -movflags +faststart {self.final_mp4}"
                    res_re = subprocess.run(cmd_reencode, shell=True, capture_output=True, text=True)
                    if res_re.returncode != 0:
                        print(f"⚠️ [VIDEO RECORDER] Re-encode fallback loi (rc={res_re.returncode}): {(res_re.stderr or '')[-300:]}", flush=True)

            if not os.path.exists(self.final_mp4):
                if os.path.exists(raw_full):
                    os.rename(raw_full, self.final_mp4)

        # Tạo bản tua nhanh 10x Timelapse Preview (chuẩn android-tv-qa)
        if os.path.exists(self.final_mp4) and os.path.getsize(self.final_mp4) > 2000:
            print(f"⚡ [VIDEO] Đang tạo video tua nhanh 10x Timelapse Preview...", flush=True)
            cmd_timelapse = f"ffmpeg -y -i {self.final_mp4} -filter:v 'setpts=0.1*PTS' -c:v libx264 -preset veryfast -crf 26 -pix_fmt yuv420p -movflags +faststart {self.timelapse_mp4}"
            res_tl = subprocess.run(cmd_timelapse, shell=True, capture_output=True, text=True)
            if res_tl.returncode != 0:
                # KL8 fix loop 2 (F67c): run 42963719447 timelapse=None mà
                # không có dòng log nào — lỗi ffmpeg phải thấy được.
                print(f"⚠️ [VIDEO RECORDER] Timelapse loi (rc={res_tl.returncode}): {(res_tl.stderr or '')[-300:]}", flush=True)

        # Dọn dẹp các chunk tạm (GIU LAI neu ghep loi de khong mat hinh anh goc)
        _probe_tmp = os.path.join(self.out_dir, "_moov_probe.mp4")
        if os.path.exists(_probe_tmp):
            try:
                os.remove(_probe_tmp)
            except Exception:
                pass
        if getattr(self, "_keep_chunks_on_failure", False):
            print("⚠️ [VIDEO RECORDER] Giu cac chunk goc trong qa_out vi ghep video loi.", flush=True)
        else:
            for c in self.local_chunks:
                if c != self.final_mp4 and os.path.exists(c):
                    try: os.remove(c)
                    except Exception: pass
            for c in getattr(self, "_norm_chunks", []):
                if c != self.final_mp4 and c != raw_full and os.path.exists(c):
                    try: os.remove(c)
                    except Exception: pass
            if raw_full != self.final_mp4 and os.path.exists(raw_full):
                try: os.remove(raw_full)
                except Exception: pass

        final_sz = os.path.getsize(self.final_mp4) if os.path.exists(self.final_mp4) else 0
        tl_sz = os.path.getsize(self.timelapse_mp4) if os.path.exists(self.timelapse_mp4) else 0
        if tl_sz < 1000:
            print("⚠️ [VIDEO RECORDER] Timelapse rong/that bai, kiem tra log ffmpeg.", flush=True)
        # KL8 fix loop 2 (F67c): báo độ phủ — video "full tour" phải cover
        # gần trọn phiên; run 42963719447 chỉ có 169s/5121s mà report không
        # hề ghi gì (chỉ có timelapse=None lặng lẽ).
        expected = 0.0
        if getattr(self, "_start_wall", 0):
            expected = max(0.0, time.time() - self._start_wall)
        partial = bool(expected > 0 and raw_duration_sec < 0.9 * expected)
        if partial:
            print(f"⚠️ [VIDEO RECORDER] Video tour CHUA DU: {raw_duration_sec:.0f}s ghi duoc / {expected:.0f}s chay ({len(getattr(self, '_norm_chunks', []))} chunk chuan hoa).", flush=True)
        print(f"🎬 [VIDEO TOUR HOÀN TẤT] File: {self.final_mp4} ({final_sz//1024} KB) | Timelapse: {self.timelapse_mp4} ({tl_sz//1024} KB)", flush=True)

        return {
            "full_tour": self.final_mp4,
            "timelapse": self.timelapse_mp4 if tl_sz > 1000 else None,
            "recorded_seconds": round(raw_duration_sec, 1),
            # Hệ số tốc độ của full_tour (1.0 = không tăng tốc): judge CẦN
            # chia video_t cho hệ số này khi cắt defect reel (CI-T4: reel cắt
            # video_t trực tiếp vào file 4x -> 3/5 đoạn rỗng, 2/5 lệch).
            "speed_factor": round(self._speed_factor, 2),
            "expected_seconds": round(expected, 1),
            "chunks": len(getattr(self, "_norm_chunks", [])),
            "partial": partial,
        }

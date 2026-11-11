# Switch-over: từ harness QA cũ sang Realtime Vision QA

> **CHƯA ÁP DỤNG. Tài liệu này chỉ là kế hoạch chuẩn bị sẵn. Evelyn quyết
> định sau khi thấy số trial (CI-T3 full trên main + CI-T4 nếu có). Không
> merge gì khi chưa có lệnh của cô ấy.**

## Thay đổi duy nhất (1 dòng lệnh trong 1 file)

File `.github/workflows/qa-suite.yml`, bước "Chạy QA Suite trên Android TV
emulator", đổi đúng dòng chạy:

```diff
-            python3 qa/kenhlive_qa/run_qa.py --out qa_out $ARGS || true
+            python3 qa/kenhlive_qa/realtime/run_realtime.py --out qa_out $ARGS || true
```

Không đổi gì khác:
- **Giữ nguyên:** preflight AI (Gemini → NVIDIA NIM → Meteor) — `VisionClient`
  đọc cùng biến môi trường `OPENAI_API_BASE/KEY/MODEL` mà preflight đã set;
  build debug APK; proxy VN; KVM; `tesseract-ocr` + `pytesseract`;
  emulator `tv_1080p`; upload artifact `qa-report`; bước `ci_report.py`
  (đọc được `qa_report.json` mới — cùng key `score/checks/findings/video`).
- **Giữ nguyên:** timeout 150 phút (realtime nhanh hơn, không cần tăng).
- **Giữ nguyên:** input `quick` (5 mission trọng tâm).

## Sửa kèm (cùng commit, nhỏ)

1. `qa-suite.yml`, bước "Install deps": không cần thêm gì — `tesseract-ocr`
   + `pytesseract` đã có (detector OCR dùng chúng).
2. Xóa file workflow trial `.github/workflows/qa-realtime-trial.yml` (đã hết
   nhiệm vụ) và nhánh `qa-realtime-trial` sau khi switch-over chạy ổn 1 lần.
3. `qa/kenhlive_qa/run_qa.py`, `autonomous_ai_qa.py`, `ai_judge.py` cũ:
   **không xóa ngay** — giữ lại 1 release để rollback; xóa sau khi realtime
   chạy ổn trên main 2 lần liên tiếp.

## Tiêu chí quyết định (số trial phải đạt trước khi switch)

| Chỉ số | Cần đạt |
|---|---|
| CI-T1 (quick, 5 mission) | Chạy xong, wall time < 20 phút, 0 crash, report đầy đủ (`qa_report.json` + video + `nim_usage`) |
| CI-T2 (full, 17 mission) | Wall time < 30 phút, 0 crash |
| CI-T3 (full, 17 mission, từ main) | Wall time < 30 phút — **ĐẠT: QA 1019s (16m59s), workflow ~22 phút** (run 42988753134) |
| False pass | 0 mission PASS không có evidence bundle |
| **False positive của findings (thêm sau review độc lập CI-T3)** | **0 finding HIGH là false positive** (kiểm bằng mắt từng finding). CI-T3: 4/5 finding HIGH là giả (1 OCR rác + 3 đồng hồ trận đấu) → **CHƯA ĐẠT**, phải sửa ở CI-T4 rồi chạy lại. Tiêu chí này trước đây thiếu nên harness vẫn "đạt" dù 80% finding giả — không được lặp lại. |
| Mọi frame evidence trích dẫn phải tồn tại | 0 frame trích dẫn thiếu trong artifact. CI-T3: 6/7 frame evidence của mission FAIL thiếu → **CHƯA ĐẠT**, sửa ở CI-T4. |
| Defect reel khớp report | Reel đủ 6s/finding, các đoạn đúng nội dung tại thời điểm trích dẫn. CI-T3: reel 18.6s thay vì 30s, 3/5 đoạn rỗng (sai hệ số 4x) → **CHƯA ĐẠT**, sửa ở CI-T4. |
| WebPlayer | Tới được `WebPlayerActivity` (deep-link F44) + vision xác nhận OSD, hoặc FAIL to kèm bằng chứng — không pass giả |
| NIM | 0 lần chạm 429; requests/run ≤ 40 (trần code), ≤ 30/phút (limiter) |
| Eye check | Xem video + defect reel, khớp với report (không tin điểm mù) |

## Rollback (nếu realtime lỗi trên main)

Đổi đúng 1 dòng lệnh trên về `run_qa.py`. Không cần revert code
`realtime/` — nó là thư mục riêng, không ảnh hưởng harness cũ.

## Rủi ro đã biết khi switch

- **Vision latency:** Nemotron ~11–22s/call; nếu preflight rơi về model
  chậm, full run có thể chỉ còn ~35–40 phút thay vì <30. Ngân sách 40 call
  là trần; nếu vượt, mission còn lại chạy chế độ cục bộ thuần (ghi rõ
  `vision_skipped: budget`).
- **Tesseract ở CI:** nếu `tesseract-ocr-vie` lỗi, detector OCR chuyển sang
  vision (đắt hơn, vẫn đúng) và ghi `ocr_skipped`.
- **Activity tên đầy đủ:** gate so khớp activity bằng hậu tố
  (`.phim.WebPlayerActivity` khớp spec `WebPlayerActivity`) — đã sửa sau bài
  học run 42963719447.
- **429 NIM:** limiter 30/phút + backoff 60s + giảm một nửa; 429 là lỗi hạ
  tầng, không trừ điểm app. Nếu CI-T1/T2 chạm 429 thì đó là lỗi thiết kế,
  phải sửa trước khi switch.

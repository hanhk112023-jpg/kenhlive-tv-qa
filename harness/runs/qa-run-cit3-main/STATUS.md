# CI-T3 — HOÀN TẤT CHẠY, CHỜ REVIEWER (2026-11-11 ~16:10 VN)

## Merge QA lên main — XONG
- KL8 merge 54287ff + QA merge aec0695 + DESIGN.md CI-T3 row 706ff78.
  Main head hiện tại: 706ff78. Build APK merge 42988749595 SUCCESS.

## CI-T3 chính thức (main, run 42988753134) — SUCCESS, ~22 phút workflow
- QA 1019s (16m59s) — DƯỚI 30 phút ✅. 90 bước, 10/17 PASS (từ 4/17 ở CI-T2),
  0 UNVERIFIED, điểm 32/100 NEEDS_FIX. Vision 4 calls, NIM 5/30, 0×429.
  Observe p50 3.65s (CI-T2: 13.46s); dump là nút thắt (p50 1.60s, tổng 321.7s,
  max 29.14s). Video 904s (6 chunk) → 4x thành 226s, độ phủ 89%.
- Eye-review: qa-run-42988753134/VISUAL-REVIEW.md — 0 false pass; findings
  1 thật (hàng Địa Phương 66 kênh) / 4 giả (OCR rác + 3 đồng hồ trận đấu);
  bỏ sót 3 lỗi thật (hero giờ đè phụ đề; Schedule hàng LIVE hiện giờ đá;
  WebPlayer tiêu đề đè đôi). Xác minh sửa đúng: P0-8 logo, F62 sau load,
  F63 WebPlayer OSD + seek 00:10→00:20.
- Lỗi harness còn lại (CI-T4): reel sai 4x; fake-score nhầm đồng hồ; frame
  evidence của FAIL thiếu 6 cái; detector kẹt không bắt luân phiên A-B-A-B;
  motion native player 0.00 ở cả 11 bước.

## Run đối chứng (trial 42988508129, build cũ)
10/17 PASS, điểm 20, QA 1014s, NIM 5, 0×429 — cùng 10/17, khác phân bổ
(IPTV_EPG PASS / VOD_PLAYER FAIL, ngược main) → motion/kẹt flaky.

## Đang chờ
- Reviewer độc lập (spawn 2026-11-11 ~16:10): verdict SWITCH-READY hay
  NEEDS-CI-T4 + danh sách sửa tối thiểu. Kết quả sẽ về tự động.
## Sau reviewer
- Báo cáo cuối cho parent: design doc, file + dòng, bảng so sánh baseline,
  verdict reviewer, giới hạn thật, switch-over (CHƯA áp dụng — chờ quyết).

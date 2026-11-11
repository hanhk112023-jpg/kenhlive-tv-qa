# QA runs — báo cáo các lần chạy QA (chỉ bản text)

Thư mục này lưu bền báo cáo text của toàn bộ lần chạy QA KenhLive
(harness cũ `qa/kenhlive_qa/` + harness realtime mới `qa/kenhlive_qa/realtime/`).

Mỗi thư mục con là 1 lần chạy (đặt tên theo số run trên GitHub Actions),
gồm: `VISUAL-REVIEW.md` (mắt kiểm video + từng ảnh), `qa_report.json`,
`qa_session.json`, `qa_report.html`, báo cáo replay (`replay_*_report.json`).

## Video / ảnh chụp KHÔNG có trong git

Video (`full_qa_tour.mp4`, `defect_reel.mp4`, `qa_timelapse.mp4`, các chunk)
và ảnh chụp (`.jpg`) cố tình KHÔNG commit: tổng khoảng 1 GB cho toàn bộ
các lần chạy, đẩy vào git sẽ làm repo phình vĩnh viễn và clone chậm.

Chúng vẫn có trên GitHub, dưới dạng **artifact của từng lần chạy CI**:
Actions → chọn run theo số → Artifacts (vd: `qa-report`, `qa-report-realtime`).

## Lưu ý

- `qa-realtime-trial2/` (bản tải tay của CI-T2) không lưu riêng ở đây vì
  nội dung text của nó trùng hệt `qa-run-42979726992/` (cùng 1 lần chạy).
- Số liệu tổng hợp từng vòng (thời gian, PASS/FAIL, P0 recall, NIM) xem ở
  `qa/kenhlive_qa/realtime/DESIGN.md` §15.

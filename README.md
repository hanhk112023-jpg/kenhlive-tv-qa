# KenhLive TV — QA tests

Repo này chứa toàn bộ QA test của KenhLive TV: code harness + toàn bộ bằng chứng
các lần chạy (báo cáo, ảnh chụp, video).

## Cấu trúc

- `harness/` — code QA: harness cũ (`autonomous_ai_qa.py`, `run_qa.py`,
  `ai_judge.py`...) + harness realtime mới (`realtime/`).
- `workflows/` — bản sao 2 workflow CI chạy QA (`qa-suite.yml`,
  `qa-realtime-trial.yml`).
- `runs/<số run>/` — từng lần chạy QA: `VISUAL-REVIEW.md` (mắt kiểm video +
  từng ảnh), `qa_report.json`, `qa_session.json`, ảnh (`.jpg`), video (`.mp4`:
  full tour, defect reel, timelapse).
- `runs/qa-realtime-trial2/` — bản tải tay của CI-T2, trùng nội dung text với
  `qa-run-42979726992` nhưng giữ lại vì có các chunk video gốc.

## CI chạy ở đâu?

CI vẫn chạy ở repo app [hanhk112023-jpg/kenhlive-tv](https://github.com/hanhk112023-jpg/kenhlive-tv)
(harness chạy từ checkout đó). Repo này là nơi lưu trữ / lưu bền: code harness
+ toàn bộ bằng chứng, để repo app không bị phình vì video (toàn bộ ~1,1 GB).
Sau mỗi vòng trial mới, báo cáo + video được đẩy sang đây.

## Số liệu tổng hợp

Xem `harness/realtime/DESIGN.md` §15 (bảng từng vòng: thời gian, PASS/FAIL,
P0 recall, NIM requests, 429s).

## Liên kết

- App: https://github.com/hanhk112023-jpg/kenhlive-tv

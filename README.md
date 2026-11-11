# KenhLive TV — QA tests

Repo này chứa toàn bộ QA test của KenhLive TV: code harness + toàn bộ bằng chứng
các lần chạy (báo cáo, ảnh chụp, video).

## Cấu trúc

- `harness/` — code QA: harness cũ (`autonomous_ai_qa.py`, `run_qa.py`,
  `ai_judge.py`...) + harness realtime mới (`realtime/`) + 2 công cụ CI
  (`ci_report.py`, `ci_sub_to_yaml.py`). Đây là bản sao của `qa/kenhlive_qa/`
  bên repo app, đồng bộ mới nhất tới head `ec66890` (CI-T7: mục 1 xong, mục 2
  làm dở chưa kiểm chứng — tiếp tục sửa ở đây, không sửa trong repo app nữa).
- `.github/workflows/` — 3 workflow CI chạy QA ở repo này
  (`qa-realtime-trial.yml`, `qa-suite.yml`, `unit-tests.yml`).
- `runs/<số run>/` — từng lần chạy QA: `VISUAL-REVIEW.md` (mắt kiểm video +
  từng ảnh), `qa_report.json`, `qa_session.json`, ảnh (`.jpg`), video (`.mp4`:
  full tour, defect reel, timelapse).
- `runs/qa-realtime-trial2/` — bản tải tay của CI-T2, trùng nội dung text với
  `qa-run-42979726992` nhưng giữ lại vì có các chunk video gốc.

## CI chạy ở đâu?

CI chạy ở chính repo này (từ khi dọn repo 2026-11-11): workflow checkout mã
nguồn app riêng tư ([kenhlive-tv](https://github.com/hanhk112023-jpg/kenhlive-tv),
deploy key chỉ-đọc `APP_CHECKOUT_KEY`) + chạy harness trong `./harness`.
Chạy tay ở tab Actions (workflow_dispatch). Repo app không còn workflow hay
code QA nào; repo [kenhlive-tv-build](https://github.com/hanhk112023-jpg/kenhlive-tv-build)
chỉ build APK/IPA, không chạy QA.

## Secret cần có (repo này)

- `APP_CHECKOUT_KEY` — đã có (deploy key chỉ-đọc của repo app).
- **Cần bạn thêm** (mình không đọc được giá trị secret cũ để copy sang):
  - `NVIDIA_API_KEY` — key NVIDIA NIM (AI brain chính của QA realtime).
  - `GEMINI_API_KEY` — key Google AI Studio (ưu tiên nếu có).
  - `METEOR_API_KEY` — gateway Meteor (fallback).
  - `YUNA_PROXY_YAML` / `YUNA_SUB_URL` — proxy VN, **tùy chọn** (không có
    thì workflow chạy không qua proxy; một số API VN có thể chặn IP
    datacenter).
- Thêm ở: repo này → Settings → Secrets and variables → Actions.

## Số liệu tổng hợp

Xem `harness/realtime/DESIGN.md` §15 (bảng từng vòng: thời gian, PASS/FAIL,
P0 recall, NIM requests, 429s).

## Liên kết

- App: https://github.com/hanhk112023-jpg/kenhlive-tv

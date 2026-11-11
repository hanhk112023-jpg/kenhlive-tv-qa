# KenhLive TV — Build & QA (1 dự án duy nhất)

Repo công khai duy nhất để build và test app KenhLive: build APK/IPA + chạy QA.

## Mã nguồn ở đâu?

Mã nguồn nằm ở 2 repo **riêng tư** (chỉ có mã nguồn app):

- Android TV: `hanhk112023-jpg/kenhlive-tv`
- iOS: `hanhk112023-jpg/kenhlive-ios`

Repo này chỉ chứa workflow build + QA, code QA, tài liệu và bằng chứng chạy.
Workflow kéo mã nguồn về bằng deploy key chỉ-đọc (`APP_CHECKOUT_KEY`,
`IOS_CHECKOUT_KEY` trong Secrets), nên mã nguồn không nằm ở đây.

## Build làm gì? (`build.yml`)

Chạy tay ở Actions → Run workflow, hoặc khi push lên repo này:

- **APK Android**: build bản debug từ `kenhlive-tv@main` → artifact
  `kenhlive-tv-debug`.
- **IPA iOS**: build không ký từ `kenhlive-ios@main` (XcodeGen + xcodebuild
  archive, `CODE_SIGNING_ALLOWED=NO`) → artifact `KenhLive-iOS-ipa`.
  IPA không ký, cài qua TrollStore / Esign / AltStore như trước giờ.

## QA làm gì? (`qa-realtime-trial.yml`, `qa-suite.yml`, `unit-tests.yml`)

Chạy tay ở Actions → Run workflow:

- `harness/` — code QA: harness cũ (`autonomous_ai_qa.py`, `run_qa.py`,
  `ai_judge.py`...) + harness realtime mới (`realtime/`) + 2 công cụ CI
  (`ci_report.py`, `ci_sub_to_yaml.py`). Đồng bộ từ `qa/kenhlive_qa/` của
  repo app tới head `ec66890` (CI-T7: mục 1 xong, mục 2 làm dở chưa kiểm
  chứng — tiếp tục sửa ở đây).
- `runs/<số run>/` — từng lần chạy QA: `VISUAL-REVIEW.md` (mắt kiểm video +
  từng ảnh), `qa_report.json`, `qa_session.json`, ảnh (`.jpg`), video (`.mp4`:
  full tour, defect reel, timelapse).
- `runs/qa-realtime-trial2/` — bản tải tay của CI-T2, trùng nội dung text với
  `qa-run-42979726992` nhưng giữ lại vì có các chunk video gốc.

## Số liệu QA tổng hợp

Xem `harness/realtime/DESIGN.md` §15 (bảng từng vòng: thời gian, PASS/FAIL,
P0 recall, NIM requests, 429s).

## Chưa có

- **APK release có ký**: cần keystore — chỉ bạn giữ, chưa đưa vào đây.
- **Tạo Release công khai tự động + báo Telegram**: chưa làm, chờ bạn quyết.

## Secret cần có (repo này)

- `APP_CHECKOUT_KEY`, `IOS_CHECKOUT_KEY` — đã có (deploy key chỉ-đọc).
- **Cần bạn thêm** (mình không đọc được giá trị secret cũ để copy sang):
  - `NVIDIA_API_KEY` — key NVIDIA NIM (AI brain chính của QA realtime).
  - `GEMINI_API_KEY` — key Google AI Studio (ưu tiên nếu có).
  - `METEOR_API_KEY` — gateway Meteor (fallback).
  - `YUNA_PROXY_YAML` / `YUNA_SUB_URL` — proxy VN, **tùy chọn** (không có
    thì workflow chạy không qua proxy; một số API VN có thể chặn IP
    datacenter).
- Thêm ở: repo này → Settings → Secrets and variables → Actions.

## Liên kết

- Mã nguồn Android: https://github.com/hanhk112023-jpg/kenhlive-tv (riêng tư)
- Mã nguồn iOS: https://github.com/hanhk112023-jpg/kenhlive-ios (riêng tư)

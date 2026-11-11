# KenhLive TV — Build & QA

**KenhLive** là app xem thể thao trực tiếp, truyền hình và phim — chạy trên
Android TV và iPhone.

Repo này là **1 dự án duy nhất, công khai**, để build app và chạy QA. Mọi
lần build và mọi lần test đều chạy ở đây, công khai hết.

## Tải app ở đâu?

Vào **Actions** → lần chạy **Build KenhLive TV & iOS** mới nhất → kéo xuống
mục **Artifacts** để tải:

- `kenhlive-tv-debug` — file APK Android (bản debug, cài trực tiếp lên TV/box).
- `KenhLive-iOS-ipa` — file IPA iPhone (không ký, cài qua
  TrollStore / Esign / AltStore).

Bản build mới nhất (run 43038264453, ngày 11/11/2026):

- APK debug, mã SHA-256 duy nhất để kiểm file nguyên vẹn:
  ```
  b56614ac3fd5c237848129f8e8074d3e1426a8fcf6a4a2a2c0d3ad01abc33b85
  ```
  Ai tải APK về thì chạy `sha256sum` — ra đúng mã này là file không bị đổi.
  File `app-debug.apk.sha256` đi kèm trong artifact nào cũng có, khỏi tính tay.
- IPA không ký, 1 MB.

Chưa có **bản release có ký** — cần keystore, chỉ chủ repo giữ.

## Vì sao repo này công khai mà mã nguồn vẫn riêng tư?

Mã nguồn app nằm ở 2 repo **riêng tư**, chỉ có mã nguồn:

- Android TV: `hanhk112023-jpg/kenhlive-tv`
- iOS: `hanhk112023-jpg/kenhlive-ios`

Repo này chỉ chứa: workflow build, code QA, tài liệu và bằng chứng chạy.
Lúc build, workflow kéo mã nguồn về bằng deploy key chỉ-đọc
(`APP_CHECKOUT_KEY`, `IOS_CHECKOUT_KEY` trong Secrets), build xong là xóa —
mã nguồn không bao giờ nằm ở đây, cũng không đẩy ngược ra công khai.

Tên 2 repo riêng tư có hiện trong file workflow là vì GitHub Actions cần
ghi đúng tên kho mới lấy được code về build. Chỉ tên kho là thấy được, code
không ra ngoài. Muốn hết hẳn thì chỉ có 1 cách: mở công khai luôn cả mã nguồn.

## Build làm gì? (`build.yml`)

Chạy tay ở **Actions → Build KenhLive TV & iOS → Run workflow**, hoặc tự
chạy mỗi khi push lên repo này:

- **APK Android**: build bản debug từ `kenhlive-tv@main` → artifact
  `kenhlive-tv-debug` (kèm file `.sha256`).
- **IPA iOS**: build không ký từ `kenhlive-ios@main` (XcodeGen + xcodebuild
  archive, `CODE_SIGNING_ALLOWED=NO`) → artifact `KenhLive-iOS-ipa`.

## QA làm gì?

Chạy tay ở **Actions → Run workflow**:

- `qa-realtime-trial.yml` — **QA realtime mới** (đang dùng để thay harness cũ):
  quay video liên tục, kiểm bằng vision như người thật, kết quả có bằng chứng
  từng bước. Tốc độ mục tiêu: dưới 30 phút/lần chạy.
- `qa-suite.yml` — harness QA cũ (đang được thay bằng realtime).
- `unit-tests.yml` — unit test của app.
- `harness/` — code QA: harness cũ (`autonomous_ai_qa.py`, `run_qa.py`,
  `ai_judge.py`...) + harness realtime mới (`realtime/`) + 2 công cụ CI
  (`ci_report.py`, `ci_sub_to_yaml.py`).
- `runs/<số run>/` — từng lần chạy QA: `VISUAL-REVIEW.md` (mắt kiểm video +
  từng ảnh), `qa_report.json`, `qa_session.json`, ảnh (`.jpg`), video (`.mp4`:
  full tour, defect reel, timelapse).

Trạng thái QA: vòng CI-T6 **PASS** lần đầu (14/17 nhiệm vụ, 79/100, 0 lỗi
nghiêm trọng giả). Vòng CI-T7 đang sửa dở (mục 1 xong, mục 2 chưa kiểm chứng).
Số liệu từng vòng xem ở `harness/realtime/DESIGN.md` §15.

## Cần thêm gì? (chủ repo tự thêm)

- **Keystore** để ký APK release — chưa có, chỉ chủ repo giữ.
- **Tạo Release công khai tự động + báo Telegram** — chưa làm, chờ quyết.
- **Secret cho QA** (mình không đọc được giá trị secret cũ để copy sang) —
  thêm ở repo này → Settings → Secrets and variables → Actions:
  - `NVIDIA_API_KEY` — key NVIDIA NIM (AI brain chính của QA realtime).
  - `GEMINI_API_KEY` — key Google AI Studio (ưu tiên nếu có).
  - `METEOR_API_KEY` — gateway Meteor (fallback).
  - `YUNA_PROXY_YAML` / `YUNA_SUB_URL` — proxy VN, **tùy chọn** (không có
    thì workflow chạy không qua proxy; một số API VN có thể chặn IP
    datacenter).

## Liên kết

- Mã nguồn Android: https://github.com/hanhk112023-jpg/kenhlive-tv (riêng tư)
- Mã nguồn iOS: https://github.com/hanhk112023-jpg/kenhlive-ios (riêng tư)

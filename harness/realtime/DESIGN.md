# QA Realtime Vision — Thiết kế (KL8 Task 12, lệnh Evelyn 2026-11-11)

> Lệnh: "Thiết kế lại qa test hay biến nó thành realtime qa vision test, tăng tốc độ
> test và kiểm tra như người thật, kết hợp vision và video để ai test nhanh nhất
> có thể — tranh lòng vòng mà cứ tuân theo luật mình đặt ra chẳng có tác dụng và
> nhận thức gì."
>
> Tài liệu này là thiết kế DUY NHẤT mà code trong `realtime/` tuân theo. Code không
> có trong thiết kế thì không được viết; thiết kế đổi thì sửa tài liệu trước.

## 1. Vấn đề của harness cũ (đã kiểm chứng, không tranh cãi lại)

Baseline: run **42950738729** — 74 phút 26 giây, 136 bước, 154 ảnh, judge **88/100**
nhưng mắt người chấm chỉ **~70/100**. Biên bản: `qa-run-42950738729/VISUAL-REVIEW.md`.

| # | Lỗi gốc | Bằng chứng |
|---|---|---|
| R1 | **Vision call mỗi bước là nút thắt thời gian.** Mỗi bước gọi `chat_vision` (nemotron, ~22s) rồi mới quyết định. 136 bước × ~33s ≈ 74 phút; vision chiếm ~67% thời gian. | `autonomous_ai_qa.py:362` `decide_mission_action`, `chat_turn` timeout 45s |
| R2 | **Mission tự kết thúc bằng lời của agent.** System prompt *dặn* làm 4–6 check sâu trước `COMPLETE_MISSION` nhưng không có gì *ép*. `_local_reflex_decision` có ~20 nhánh `COMPLETE_MISSION` cứng theo số bước. Agent nói xong là pass. | `autonomous_ai_qa.py:163` (prompt, rule 5), `:453` (reflex) |
| R3 | **Judge có điểm mặc định.** `ai_judge._parse_json` trả score **85, ok=True, findings=[]** khi parse JSON thất bại — pass giả bằng code. | `ai_judge.py:221` |
| R4 | **Video và vision tách rời.** Video quay liên tục nhưng review vẫn là 154 ảnh tĩnh; video chỉ để xem lại, không tham gia phán quyết. | `video_recorder.py`, `VISUAL-REVIEW.md` §Phương pháp |
| R5 | **False pass có cấu trúc.** Mission WebPlayer 0 bước vào WebPlayer vẫn pass (lần thứ 4 liên tiếp); mission Home Hub kiểm tra Tab 6 đã xóa vẫn pass. Không có cơ chế nào bắt được. | P0-1, P0-2 |

Hệ quả: điểm số không đo được chất lượng thật; lỗi nhìn thấy bằng mắt (P0-3..P0-8)
chỉ lộ ra khi người xem lại toàn bộ ảnh — đúng việc Evelyn đã dặn không được tin.

## 2. Mục tiêu và chỉ số thành công (đo được, không tuyên bố suông)

| Chỉ số | Baseline (cũ) | Mục tiêu (mới) | Đo bằng |
|---|---|---|---|
| Wall time full run | 74m26s | **< 30 phút** (mục tiêu; báo số thật dù đạt hay không) | `run_realtime.py` log + CI run |
| Vision calls / run | 136 (1/bước) | **≤ 40** (chỉ khi cần xác nhận) | `vision_calls` trong report |
| NIM requests / run | — (không đếm) | **≤ 40** và **≤ 30/phút** qua limiter; **0 lần chạm 429** | `nim_usage` trong report |
| P0 recall (offline replay) | — | **8/8** (mục tiêu làm việc, Evelyn 13:39; thiết kế ban đầu ghi ≥7/8) | `replay.py` |
| WebPlayer mission | pass giả | **FAIL to, kèm bằng chứng** (nếu không vào được WebPlayer) | replay + CI trial |
| False pass | 2/17 check | **0** — pass nào cũng có bằng chứng đính kèm | gate log |
| Điểm judge | 88 (lạm phát) | điểm = 100 − phạt trên defect **đã xác minh**; không có điểm mặc định | `judge.py` |

**Nguyên tắc thiết kế, theo thứ tự ưu tiên:**
1. **Bằng chứng thắng lời nói.** Không có bằng chứng thì không có pass.
2. **Rẻ trước, đắt sau.** Tín hiệu cục bộ (UI dump, pixel diff, OCR) quyết định
   điều hướng; vision chỉ dùng để *xác nhận* và *phán quyết thị giác*.
3. **Phản ứng với màn hình hiện tại, không đi theo kịch bản.** Không có danh sách
   bước cứng cho từng mission; driver chọn hành động theo trạng thái đang thấy.
4. **Thất bại to và rõ.** Mission không tới đích thì FAIL, kèm bằng chứng — không
   bao giờ tự hoàn thành.

## 3. Kiến trúc tổng thể

```
┌─────────────────────────────────────────────────────────────────┐
│ run_realtime.py (CLI: --out --quick --missions --vision-budget) │
└──────────────┬──────────────────────────────────────────────────┘
               │  điều phối
┌──────────────▼──────────────────────────────────────────────────┐
│ runner.py — RealtimeRunner                                      │
│  VideoRecorder (cũ, import) quay liên tục 1280x720              │
│  ┌─────────────┐  ┌────────────┐  ┌──────────┐  ┌───────────┐    │
│  │ perception  │→ │ detectors  │→ │ gate     │→ │ driver    │    │
│  │ (watcher)   │  │ (cục bộ)   │  │ (bằng    │  │ (chọn     │    │
│  └─────────────┘  └────────────┘  │ chứng)   │  │ hành động)│    │
│        ▲                         └────┬─────┘  └─────┬─────┘    │
│        │  stable frame                │ vision chỉ   │ adb key   │
│        │  + UI dump                   │ khi cần      │ /launch   │
│  ┌─────┴────────┐  ┌──────────────┐    ▼              ▼           │
│  │ device.py    │  │ ocr.py       │ vision.py    device.py       │
│  │ (adb, dump)  │  │ (tesseract)  │ (OpenAI-compat)               │
│  └──────────────┘  └──────────────┘                               │
│  ┌──────────────┐  ┌──────────────┐                              │
│  │ judge.py     │  │ missions.py  │  replay.py (offline)         │
│  │ (điểm thật)  │  │ (mục tiêu)   │  (chạy lại artifact cũ)      │
│  └──────────────┘  └──────────────┘                              │
└─────────────────────────────────────────────────────────────────┘
  Xuất: qa_report.json (superset định dạng cũ) + qa_report.html
        + qa_session.json (timeline tương thích replay)
        + defect_reel.mp4 + defect_frames/ (ảnh + timestamp)
```

**Quy tắc biên:**
- Mới hoàn toàn, chỉ nằm trong `qa/kenhlive_qa/realtime/` (+ docs). **Không sửa**
  `autonomous_ai_qa.py`, `run_qa.py`, `ai_judge.py`, `qa-suite.yml`, `qa/ci_report.py`,
  app code — cho tới khi fix loop 1 xong. Được phép **import** `video_recorder.py`
  (ổn định, không ai sửa) và dùng lại bảng phạt của `report.score`.
- Không key API mới. Vision dùng đúng provider chain cũ qua biến môi trường mà
  preflight của `qa-suite.yml` đã set (`OPENAI_API_BASE/KEY/MODEL`): Gemini free
  tier → NVIDIA NIM nemotron → Meteor. Không hardcode key.

## 4. Vòng perception realtime (thay cho "vision mỗi bước")

`perception.py` — `ScreenWatcher` chạy độc lập với vòng quyết định:

1. **Lấy mẫu liên tục, rẻ:** `adb screencap` mỗi ~1,2s, thu nhỏ 160×90, tính
   pixel-diff (PIL `ImageChops`, như `probes.pixel_diff`) so với frame ổn định
   gần nhất. Chi phí mỗi mẫu < 0,1s CPU local.
2. **Phát hiện đổi màn hình:** diff > 1,5% → màn hình đang đổi (chuyển cảnh /
   video đang chạy trong vùng nhỏ không tính — video motion chỉ đo trong vùng
   player, ngưỡng riêng). Diff < 1,5% trong 2 mẫu liên tiếp → **stable frame**.
3. **Chỉ khi stable mới làm việc nặng:** chụp full frame 1920×1080 (giữ PNG) +
   `uiautomator dump` (parse: focused view/text/bounds, focusable list,
   `selected` nav ids, toàn bộ text nhìn thấy) + `current_activity`. Đấy là
   **một quan sát** (observation) — đơn vị dữ liệu duy nhất driver/gate dùng.
4. **Video là nguồn sự thật thứ hai:** `VideoRecorder` vẫn quay liên tục.
   Sau run, defect nào cũng map về timestamp video để cắt defect reel.
   Frame trích từ video chỉ dùng để *xem lại*, không dùng để quyết định
   realtime (video 1280×720, chunk 175s, có độ trễ).

**Ngân sách thời gian mỗi bước (mục tiêu):** watcher mẫu 0,1s + settle ~1s +
dump UI ~1,5s + detectors cục bộ ~0,3s + hành động + settle ~1s ≈ **3,5–4s**,
so với ~33s của harness cũ. Vision không nằm trong vòng này.

## 5. Evidence-gated completion (sửa R2, R5 — lõi của thiết kế này)

`gate.py` — `EvidenceGate`. **Agent/driver KHÔNG BAO GIỜ được quyền
`COMPLETE_MISSION`.** Chỉ gate mới kết luận PASS/FAIL.

### 5.1. Tín hiệu (signal) — 4 loại, mỗi loại có nguồn độc lập

| Tín hiệu | Nguồn | Ai thu |
|---|---|---|
| `activity` | `dumpsys activity` — tên activity đang foreground | `device.py` |
| `ui_text` | UI dump / OCR — chuỗi text bắt buộc xuất hiện | `device.py` + `ocr.py` |
| `motion` | pixel-diff video trong vùng player ≥ 0,35% | `perception.py` |
| `vision` | vision xác nhận mục tiêu trên frame ổn định gần nhất | `vision.py`, **1 lần** |

### 5.2. Spec của một mission (`missions.py`)

```python
MissionSpec(
  name="MISSION_WEBPLAYER_DIRECTED_REAL_FILM",
  required_activity="WebPlayerActivity",   # bắt buộc từng xuất hiện
  required_texts=["Tốc độ"],              # phải thấy trong UI dump/OCR (nếu áp dụng)
  required_views=[],                       # resource-id bắt buộc (nếu áp dụng)
  needs_motion=True,                       # video phải chuyển động thật
  needs_vision=True,                       # cần vision xác nhận frame cuối
  min_steps=4, max_steps=12,
  directed_launch="LAUNCH_WEB_PLAYER",     # chạy TRƯỚC vòng driver
)
```

Mỗi mission khai **tập tín hiệu áp dụng** (không phải mission nào cũng cần cả 4;
VD mission Home không cần motion). Gate PASS khi và chỉ khi **mọi tín hiệu
áp dụng đều xanh trên cùng một chuỗi quan sát gần nhất**, và vision (nếu áp
dụng) xác nhận trên frame ổn định gần nhất. Thiếu bất kỳ tín hiệu nào khi hết
`max_steps` → **FAIL**, kèm bằng chứng (activity đã thấy, text đã thấy/thiếu,
frame cuối, số bước).

### 5.3. Vì sao P0-1 trở nên không thể xảy ra

**So khớp activity bằng hậu tố** (sửa sau run 42963719447): ADB trả tên đầy
đủ `com.kenhlive.tv/.phim.WebPlayerActivity` nhưng spec chỉ ghi
`WebPlayerActivity` — khớp tuyệt đối sẽ FAIL oan mission đã tới đích. Gate
dùng `any(a.endswith(required) for a in activities_seen)`.

Mission WebPlayer: `required_activity="WebPlayerActivity"`. Ở run cũ, activity
trong cả mission chỉ là `PlayerActivity` → `MainActivity`. Gate không bao giờ
thấy tín hiệu `activity` → không có đường nào tới PASS. Driver có "nói" gì cũng
vô nghĩa: không có action `COMPLETE` trong `driver.py`. Đây là sửa **bằng cấu
trúc**, không bằng lời dặn trong prompt.

Tương tự P0-2: mission Home khai `required_texts` theo billboard + 6 hàng
(VD "ĐANG PHÁT", "MỚI CẬP NHẬT") thay vì tab số; `SWITCH_TAB` tới tab đích
không tới được → gate FAIL ngay (đã có tiền lệ ở fix loop 1, giữ nguyên ngữ
nghĩa).

## 6. Driver điều hướng (thay cho "kịch bản cứng ~20 nhánh")

`driver.py` — policy xác định (deterministic), chọn **một** hành động theo trạng
thái hiện tại. Không vision trong policy, trừ hai đường thoát ghi rõ dưới đây.

Thứ tự ưu tiên khi chọn hành động:
1. **Directed launch** (nếu mission có): chạy trước vòng lặp; không tới
   `required_activity` trong 30s → FAIL ngay (không vào vòng lặp).
2. **Tới đích trực tiếp:** nếu mục tiêu là tab → `SWITCH_TAB(n)`; nếu mục tiêu
   là dialog và focused view là nút mở dialog → `OK`.
3. **Khám phá có hướng:** lần lượt `DPAD_DOWN` / `DPAD_RIGHT` qua các vùng chưa
   thăm; sau mỗi phím, so sánh focused view + diff: nếu **không đổi gì sau 3
   phím liên tiếp** → `BACK` một lần rồi thử hướng khác.
4. **Thoát khi kẹt (chỉ 2 đường hỏi vision):**
   - Kẹt lần 1 (không đổi trạng thái 3 bước): hỏi vision **một lần**
     "màn hình này đang ở đâu, nên bấm gì để tới <mục tiêu>?" → làm theo nếu
     hành động trả về hợp lệ, không thì `BACK`.
   - Kẹt lần 2: **FAIL mission** (stuck), đính kèm frame + UI dump cuối.
5. **Hết `max_steps` mà gate chưa đủ tín hiệu → FAIL** (không auto-pass).

Driver ghi lại mọi quyết định + lý do (rule nào đã chọn) vào timeline để
replay được. Không có `random`, không có "thought" tự do của model trong vòng
điều hướng.

## 7. Detectors cục bộ (chạy trên mọi stable frame, không tốn vision)

`detectors.py` — mỗi detector trả `{severity, area, issue, detail, suggestion,
evidence: {frame, t, ui_state}}`. Tất cả chạy bằng PIL/regex/UI dump:

| Detector | Bắt được | Ánh xạ P0 |
|---|---|---|
| `blank_screen` (stddev < 4, xác thực 2 lần) | màn đen/rỗng | — |
| `focus_loss` (focused NONE ngoài player, đã settle) | mất focus | **P0-6** |
| `focus_trap` (cùng focused sig sau 3 phím D-pad cùng hướng, không phải mép) | kẹt focus | P1-1 họ hàng |
| `offscreen_focus` / `zero_size_focus` (bounds ngoài 1920×1080 hoặc ≤2px) | focus rò | — |
| `dialog_focus_leak` (dialog mở mà focus ở view nền) | dialog không trap | P1-3 họ hàng |
| `bad_text` (null/undefined/NaN/`[$...]` trong text) | chuỗi thô | — |
| `fake_score` (giờ `HH:mm` đội lốt tỉ số `X : Y`, tỉ số phi lý >9/ >12 tổng) | tỉ số ảo | (luật Task 5) |
| `text_overlap` (OCR boxes chồng nhau trong vùng nav / seekbar / hàng nút) | chữ đè chữ | **P0-3, P0-5** |
| `clipped_text` (OCR text kết thúc "…" + text chạm mép phải của bounds) | chữ bị cắt | **P0-4**, P1-4 |
| `row_overflow` (header "— N kênh" với N > 30 trong một hàng) | hàng quá tải | **P0-7** |
| `wrong_logo` | cần so text logo vs tên kênh → **đẩy vào hàng đợi vision**, không tự kết luận | **P0-8** |

**OCR** (`ocr.py`): tesseract `vie`, chỉ có ở CI (workflow cài). Local không có
→ detector OCR trả `skipped` và ghi rõ; replay local dùng vision thay thế cho
5 frame khóa (xem §10). Ngưỡng: OCR chỉ chạy trên **frame ổn định + vùng nghi
vấn** (nav bar, seekbar, hàng nút), không OCR toàn màn mỗi bước.

## 8. Vision — dùng ít, dùng đúng chỗ

`vision.py` — `VisionClient` (OpenAI-compatible, provider chain như §3, timeout
30s, retry 1, `max_tokens` nhỏ: 600 cho xác nhận, 1200 cho kiểm defect).

**Chỉ gọi trong 3 trường hợp, theo thứ tự:**
1. **Xác nhận hoàn thành** — khi gate đã đủ các tín hiệu rẻ: 1 call trên frame
   ổn định gần nhất, prompt "mục tiêu <X> có đang hiển thị không? trả lời JSON
   {confirmed, quote}". Không xác nhận → không PASS (mission tiếp tục đi, tối
   đa 2 lần xác nhận/mission).
2. **Xác minh defect nghi vấn** — detector cục bộ nghi (vd overlap 70% chắc):
   1 call crop vùng nghi vấn để khẳng định/bác. Bác → không ghi defect.
3. **Thoát kẹt** — như §6 bước 4 (tối đa 1 call/mission).

**Ngân sách:** mặc định 40 calls/run full (18 mission). Vượt ngân sách → các
mission còn lại chạy chế độ cục bộ thuần và ghi rõ `vision_skipped: budget` —
không bịa kết quả. Model nhanh được ưu tiên qua preflight (Gemini flash rẻ
hơn nemotron về latency — xem §11).

Không dùng vision để *điều hướng từng bước* nữa: đó chính là R1.

### 8.1. Rate limit NIM — 40 request/phút (luật cứng, Evelyn 2026-11-11 13:42)

NIM giới hạn **40 request/phút** — không chỗ nào trong thiết kế/code cũ nhắc
tới, Evelyn cho biết ngày 13:42. Đây là luật cứng, xử lý bằng code, không
bằng lời hứa:

- **`ratelimit.py` — một limiter duy nhất cho cả process** (sliding window
  60s): mọi call tới `integrate.api.nvidia.com` đều qua `LIMITER.acquire()`
  trước khi gửi, giới hạn **30 req/phút** (chừa biên 25% dưới trần 40),
  không bao giờ burst. Kể cả vision điều hướng, confirm, check defect và
  judge — không có đường nào vòng qua limiter.
- **Ngân sách chứng minh được:** trần cứng theo code là 40 vision call/run
  (`vision_budget=40` mặc định) + replay 5 check ≈ **≤ 45 request/run**,
  trong khi 30 phút × 30 req/phút = 900 cho phép. Điều hướng bằng tín hiệu
  rẻ (UI dump, activity, frame diff) là **bắt buộc**, không phải tối ưu tùy
  chọn — gọi vision mỗi bước (136 call) vẫn dưới 900 nhưng sẽ chạm trần
  phút ở những phút dồn dập và làm run chậm vì throttle.
- **Gặp 429 thì lùi, không đấm tiếp:** `_post` bắt `HTTPError 429` riêng —
  đọc `Retry-After` (nếu có), `record_429()` (chờ tối thiểu 60s rồi giảm tốc
  độ một nửa còn 15 req/phút cho tới hết run), thử lại **đúng 1 lần**. 429
  lần 2 → `RateLimitedError` → caller biến thành **UNVERIFIED**. **429 là lỗi
  hạ tầng, không bao giờ là finding, không trừ điểm app, chỉ ghi log.**
- **Judge cũng throttle:** judge sau run không chấm hàng trăm ảnh song song —
  thiết kế này không có bước judge bulk: defect đến từ detectors cục bộ +
  tối đa ~5 check vision tuần tự qua limiter. Mọi call judge (nếu có thêm)
  cũng đi qua cùng limiter.
- **Báo cáo:** mọi report đều có `nim_usage: {requests_used, limit_per_min,
  hit_429, hits_429, throttled_waits, throttled_wait_s}`. **Chạm 429 trong
  một lần chạy = lỗi thiết kế, phải sửa ở vòng sau, không phải chuyện
  bình thường.**

## 9. Honest judge (sửa R3)

`judge.py` — `HonestJudge`:

- **Không có điểm mặc định.** Vision/judge không parse được, timeout, hay
  thiếu bằng chứng → kết quả là **`UNVERIFIED`** (ghi rõ, không tính pass,
  không cộng điểm, không trừ điểm — nhưng liệt kê riêng trong báo cáo để người
  đọc thấy chỗ mù).
- **Điểm = 100 − phạt trên defect ĐÃ XÁC MINH.** Mỗi defect phải có
  `evidence: {frame_file, video_t, ui_state, detector|vision}`. Bảng phạt giữ
  nguyên `report.score` để so được với baseline (CRITICAL 25, HIGH 12, MEDIUM
  5, LOW 1 + tối đa 20 cho mission FAIL).
- **Mỗi PASS phải có evidence bundle:** activity đã thấy + texts/views đã thấy
  + vision confirmation (nếu áp dụng) + frame cuối + timestamp. Không có bundle
  thì mission đó là FAIL, không phải PASS.
- **Defect reel:** từ video full, cắt các đoạn ±3s quanh mỗi defect (ffmpeg)
  thành `defect_reel.mp4` + danh sách timestamp. Người review xem reel 1–2 phút
  là thấy hết lỗi, thay vì xem 154 ảnh.
- Báo cáo xuất `qa_report.json` (superset: giữ các key cũ `score/checks/findings`
  để `qa/ci_report.py` không vỡ + thêm `evidence`, `vision_calls`, `timings`,
  `unverified`) và `qa_report.html` gọn (điểm, bảng mission kèm evidence link,
  bảng defect kèm frame, link reel).

## 10. Replay trial (kiểm chứng offline, trước khi chạy CI)

`replay.py` — chạy lại artifact run 42950738729 **không cần emulator**:

- Đầu vào: `qa-run-42950738729/qa-report/{qa_session.json, qa_report.json,
  shots/*.jpg, full_qa_tour.mp4}`.
- Tái hiện timeline 136 bước: mỗi entry có `activity`, `ui_state`
  (focused_view/text/bounds, has_focus_ring), `mission`, `time_offset_sec`,
  `screenshot`. Chạy qua `EvidenceGate` + `detectors` cục bộ (focus-loss,
  blank, bad-text, fake-score từ dữ liệu timeline).
- 5 frame khóa (P0-3/4/5/7/8) chạy qua `vision.py` để xác minh thị giác — cùng
  code vision với live runner, không viết riêng.
- Đầu ra: `replay_report.json` — thời gian chạy, **P0 recall** (mỗi P0-1..P0-8:
  bắt được / bỏ sót / bằng cách nào), verdict WebPlayer (phải là FAIL), số
  vision calls, và những gì replay **không** kiểm được (VD: detector OCR không
  có tesseract local; motion không đo lại được từ ảnh tĩnh).
- Mục tiêu: recall **8/8** + WebPlayer FAIL + 0 false pass. Không đạt thì sửa
  thiết kế/code, không sửa số liệu.

## 11. Tốc độ — mô hình và cách đo thật

Mô hình thời gian full run (136 bước):
- Cũ: 136 × ~33s ≈ 74 phút (vision 22s/bước).
- Mới: 136 × ~4s ≈ 9 phút điều hướng + vision ≤ 40 calls × ~8–22s ≈ 5–15 phút
  + setup chung (build APK, emulator, proxy — như cũ ~10 phút) ≈ **20–30 phút**.
- Biến số lớn nhất là latency vision (nemotron ~22s/call trên NIM; Gemini
  flash nhanh hơn nhiều nếu preflight chọn Gemini). **Đo thật trên CI trial,
  không khẳng định trước.**

Quick mode (5 mission như cũ): mục tiêu < 12 phút tổng.

## 12. CI trial và switch-over (tách bạch)

- **Trial:** nhánh riêng `qa-realtime-trial` (từ head `redesign/apple-kl8`),
  chỉ chứa file mới `realtime/` + workflow mới `qa-realtime-trial.yml` (copy
  khung `qa-suite.yml`, chạy `run_realtime.py --quick`). Dispatch 1 lần, đo
  wall time, steps, defects. Không động `qa-suite.yml` trên `apple-kl8`.
- **Switch-over:** chuẩn bị sẵn, **KHÔNG áp dụng**: file `SWITCHOVER.md` mô
  tả đúng 1 thay đổi — `qa-suite.yml` đổi lệnh chạy từ `run_qa.py` sang
  `run_realtime.py` (+ giữ preflight/build/emulator nguyên). Evelyn quyết sau
  khi thấy số trial. Không merge gì.

## 13. Rủi ro & giới hạn (nói trước, không giấu)

1. **Vision latency vẫn là biến số.** Nemotron ~22s/call; nếu preflight rơi về
   model chậm, full run có thể chỉ còn ~35–40 phút thay vì ~25. Ngân sách
   40 calls là trần để tránh vượt.
2. **OCR phụ thuộc tesseract ở CI.** Nếu `tesseract-ocr-vie` lỗi, detector
   overlap/clip chuyển sang vision (đắt hơn, vẫn đúng).
3. **WebView UI dump nghèo nàn.** Nội dung trong WebView ít khi lộ qua
   uiautomator — mission WebPlayer dựa vào activity + motion + vision, không
   dựa vào text trong dump. Nếu embed không load, motion = 0 → FAIL đúng.
4. **Emulator x86 vẫn lỗi codec** (P1-5): `ERROR_CODE_DECODING_FAILED` là
   giới hạn máy ảo, không phải lỗi app — judge không trừ điểm cho nó, chỉ ghi
   chú. Cần máy thật để kết luận.
5. **Replay không thay được live run.** Replay chứng minh gate/detector đúng
   trên dữ liệu cũ; chỉ CI trial mới đo được tốc độ thật.
6. **Fix loop 1 đang sửa harness cũ song song.** Harness mới không được import
   code từ `autonomous_ai_qa.py` (đang bị sửa) — tự chứa `device.py`/`vision.py`
   riêng; chỉ import `video_recorder.py` (ổn định).

## 14. Định dạng báo cáo (tương thích)

`qa_report.json` giữ mọi key cũ (`score, duration_sec, checks, findings,
screenshots, missions_passed, video`) + thêm:
`evidence: {mission: {signals, frame, t}}`, `vision_calls: {total, by_reason}`,
`timings: {per_step_p50, vision_total_s, total_s}`, `unverified: [...]`,
`defect_reel: "defect_reel.mp4"`, `engine: "KenhLive Realtime Vision QA"`,
`nim_usage: {requests_used, limit_per_min, hit_429, hits_429,
throttled_waits, throttled_wait_s}` (luật 40 req/phút, §8.1).
`qa_session.json` giữ timeline như cũ để `replay.py` đọc được cả hai loại run.

## 15. Vòng lặp cải thiện — đo, chỉnh, chạy lại (lệnh Evelyn 2026-11-11 13:39)

Không build một lần rồi xong. Sau mỗi lần chạy (replay offline hoặc CI trial),
ghi một dòng vào bảng này: thời gian, số bước, P0 bắt được/tổng, false pass,
NIM requests đã dùng/giới hạn, có chạm 429 không — rồi chỉnh và chạy lại.
Mục tiêu làm việc: **full run < 30 phút, P0 recall 8/8, 0 false pass, 0 lần
chạm 429**. Tối thiểu 2 vòng lặp có số đo trước khi báo cáo. Nếu sau 2 vòng
vẫn chưa đạt, báo rõ hiện đạt bao nhiêu, kẹt ở đâu, cần đổi hướng gì.

| Vòng | Loại | Thời gian | Bước | P0 recall | False pass | NIM requests / giới hạn | Chạm 429? | Chỉnh gì → kết quả |
|---|---|---|---|---|---|---|---|---|
| R1 (replay) | offline, run 42950738729 | 52.3s (chỉ phân tích; ≠ wall time live) | 136 (timeline cũ) | **6/8** — sót P0-3, P0-5 | 0 | **5 / 30-phút** | không | Khởi đầu: gate activity, tab check, detector focus NONE, vision full-frame. Vision full-frame bỏ sót P0-3 (overlap ở mép trên) và P0-5 (phụ đề "nằm giữa"). Bug phát hiện: gate so activity tuyệt đối (`MainActivity` ≠ `com.kenhlive.tv/.MainActivity`) → FAIL oan mọi mission; deadlock VISION_PENDING (evaluate chỉ PASS khi đã có vision, runner chỉ gọi vision khi đã PASS). |
| R2 (replay) | offline, run 42950738729 | 85.0s | 136 | **7/8** — sót P0-5 | 0 | **6 / 30-phút** | không | Sửa: (1) gate chuẩn hoá activity (lưu cả dạng đầy đủ + rút gọn); (2) verdict `VISION_PENDING` — được phép ngay cả ở max_steps, runner/replay xác nhận vision rồi mới kết luận (mission player-streaming PASS lại); (3) `check_visual` hỗ trợ crop vùng nghi + câu hỏi ép đọc nguyên văn; (4) `detect_player_focus_loss` mới (P0-6 trong player, OSD hiện mà focus NONE) + `detect_blank` bỏ sleep 1.5s; (5) judge không tính UNVERIFIED như FAIL. P0-3 bắt được nhờ crop nav (0,0,1920,280). P0-5 vẫn sót: model 2 lần đều nói phụ đề "nằm giữa seekbar và nút, không chạm" — cần crop chặt + hỏi khoảng cách. |
| R3 (replay) | offline, run 42950738729 | 87.3s | 136 | **7/8** — sót P0-5 | 0 | **7 / 30-phút** (6 call + 1 retry) | không | Thêm: limiter NIM 30/phút (§8.1) + `ratelimit.py` (unit test PASS: throttle 2.5s, backoff 429 = 60s, giảm một nửa); `check_visual` crop gửi ở 1280 (lỗi vài px vẫn thấy); P0-5 crop chặt (780–1080) + hỏi khoảng cách px. **Kết quả: P0-5 KHÔNG do vision bác — call rớt mạng** (`Remote end closed connection`, lỗi hạ tầng NIM, đã retry 1 lần) → 7 requests cho 6 call. Bài học: vision không đáng tin cho P0-5 (2 lần bác + 1 lần rớt). |
| R4 (replay) | offline, run 42950738729 | 94.8s | 136 | **8/8** ✅ | 0 | **6 / 30-phút** | không | Đổi hướng P0-5 sang **OCR hình học** (không chờ vision): `detect_subtitle_seekbar_overlap` — nhãn giờ seekbar (`03:07`/`21:06`) làm mốc hàng seekbar, box phụ đề cắt ngang hàng đó là lỗi; đã trực tiếp xem ảnh step_065 xác nhận P0-3 thật nhưng OCR không tách được 2 lớp chữ chồng (vision là đường chính cho P0-3). Sửa thêm: OCR chỉ đọc band + cache theo frame + gate mỗi 3 bước (không gate ≈ 1 giờ OCR/run); band scale theo kích thước thật (ảnh lưu 960×540, live 1920×1080); guard false positive (nav band bỏ qua ở player, ngưỡng chồng 0.40, tỉ lệ chiều cao ≤2, clipped chỉ ở player — đã loại 5 false positive ở step_065/091). P0-4 cũng bắt bằng OCR (`TRỰC...`); P0-3 vision (crop nav). Tesseract cài local 5.3.4 + `vie` để replay dùng được OCR. **Mục tiêu replay đạt: 8/8, 0 false pass, NIM 6/30-phút, 0×429.** Điểm replay 0/100 là điểm THẬT của build cũ (8 P0 đã xác minh, phạt 115 > 100 → clamp 0) — không phải lỗi harness. |
| CI-T1 | LIVE, run 42976407479 (full 17 mission — push dispatch không có input nên `quick` rỗng, xem §15.1) | **919s QA (15m19s) / 21m cả workflow** | 76 | không áp dụng (harness hỏng, không đo được recall) | 0 false pass (16 FAIL đều có bằng chứng) nhưng **1 false PASS ở verdict** | **0 / 30-phút** (vision không được gọi lần nào) | không | **THẤT BẠI — tìm ra 5 lỗi (đã sửa hết, xem §15.1): (1) watcher không start() → motion luôn False, không frame nào, observe 10.5s/bước; (2) dialog chào mừng "THÔNG BÁO" lần đầu chặn suốt run, driver không có luật đóng nó (harness cũ bấm OK trên btnCloseFeedback ở bước 1); (3) render_html crash %-format (CSS `width:100%`) → mất qa_report.html + qa_session.json; (4) verdict PASS khi 16/17 FAIL (điểm 81 vì trừ mission FAIL tối đa 20); (5) video chỉ 176s — `_dur()` đọc N/A nên 6 chunk đều bị loại (cả run cũ 42963719447 cũng chỉ 169s, 30× 'Bo chunk hong' — lỗi hệ thống của recorder). Tích cực: deep-link WebPlayer tới đúng `.phim.WebPlayerActivity` live; preflight chọn đúng NVIDIA nemotron; 0×429; gate FAIL đúng thay vì pass giả. |
| R5 (replay run mới) | offline, run 42963719447 (fix loop 1 re-run) | 3.1s (no-vision) | 140 | **không áp dụng** — P0 cũ đã sửa, bảng P0-1..P0-8 vô nghĩa trên run này | 0 | **2 / 30-phút** (chỉ 2 check có đích) | không | Validation thứ hai, không nằm trong chuỗi P0 cũ: (1) sửa **gate so khớp activity bằng hậu tố** — activity thật là `.phim.WebPlayerActivity`, khớp tuyệt đối sẽ FAIL oan mission đã tới đích (bài học trực tiếp từ run này); sau sửa, WebPlayer mission về đúng `VISION_PENDING` (activity + motion xanh, chờ vision). (2) **F63 bắt được:** vision xác nhận OSD trên step_105 → `confirmed: False` (chỉ thấy giờ embed `09:22 / 24:14`, không có OSD KL8) → mission FAIL trong replay có vision — lỗi mà judge cũ tính pass 17/17. (3) **F64 bắt được:** vision thấy pill `0` trên cả 2 card POR–OKC và SAC–ORL (step_007). (4) F65: timeline step 43 = focus NONE trong PlayerActivity, file ảnh bị thiếu (lỗ hổng bằng chứng của run cũ) — detector mới cần `osd_visible` nên chỉ kết luận được một phần offline; để CI trial kiểm chứng live. (5) Rail mission vẫn FAIL (P1-1 còn nguyên qua cả 2 run). 4 mission PASS có evidence, 0 false pass. Điểm replay run mới 96/100 là **không so được** (không có finding nào từ P0 cũ — run này đã sửa hết P0 đó). |

| R4c (replay, hậu CI-T2) | offline, run 42950738729 — kiểm chứng guard OCR + OSD gate mới | 82.2s | 136 | **8/8** ✅ — giữ nguyên | 0 | **7 / 30-phút** (6 vision calls + 1 retry) | không | Guard CI-T2 không làm mất recall: P0-4 vẫn bắt ('TRỰC...', token 4 ký tự qua guard ≥4), P0-5 vẫn bắt bằng OCR hình học (OSD gate mặc định chạy khi `osd_visible` là None — dữ liệu replay cũ không có OSD state), P0-3 vision crop nav, P0-7/P0-8 vision. Mock test trên frame THẬT CI-T2 chứng minh guard giết được false positive: step_091 (OSD ẩn) 0 finding (trước: 4 finding giả #7-10), step_094 (OSD hiện) đúng 1 finding thật (phụ đề đè seekbar). |
| CI-T2 | LIVE, run 42979726992 (full 17 mission) | **2277s QA (37m57s) / 43m02s cả workflow** | 112 | không áp dụng (P0 cũ đã sửa trên build fix loop 1) | 0 false pass (4 PASS đều có bằng chứng) nhưng **10/11 finding là false positive OCR** | **8 / 30-phút** (7 vision calls) | không | Mục tiêu <30 phút **CHƯA ĐẠT** (38 phút QA) nhưng nhanh ~2× so với cũ 74–89 phút. 4/17 PASS (COLD_START, VOD_PLAYER, PLAYER_SETTINGS_DIALOG, STRESS), điểm 0/100, verdict NEEDS_FIX (trung thực — xem §15.3). Nút thắt: (1) **kẹt trong PlayerActivity từ mission 3** — 7 mission FAIL oan vì không có luật quay về (ROOM_PICKER OK mở player, không ai BACK); (2) observe p50 13.5s (p90 34.3s) — dump + OCR chậm, chưa đo được phần nào; (3) motion đo 0.00 ở 98% bước player dù video đang phát (watcher 1.2s + cửa sổ 2s → <2 mẫu); (4) video vẫn 175s: **ffmpeg không có trên CI runner** (`rc=127: ffmpeg: not found`) — `_dur` fix đã giữ đủ 13 chunk nhưng concat không chạy được; (5) `vision_s` báo 7.7s trong khi 7 call × 12.4s ≈ 87s (chỉ cộng confirm). Eye-review 11 finding: **1 thật** (P0-5-class: phụ đề WebPlayer đè seekbar step_094 — phụ đề của web embed, fix native player không chạm tới), **10 giả** (OCR đọc nhầm nội dung video: box rác 1–2 ký tự, box cao 0px ở mép 1079, box rộng cả màn hình). |
| R5 (replay, hậu CI-T4) | offline, run 42950738729 — kiểm chứng sửa reviewer (reel, fake-score, A-B-A-B, stress gate, guard OCR, hero band) không làm mất recall | 132.7s | 136 | **8/8** ✅ — giữ nguyên (P0-1..P0-8, 2 PASS / 4 FAIL / 11 UNVERIFIED) | 0 | **8 / 30-phút** (6 vision calls) | không | Recall giữ nguyên sau mọi sửa CI-T4. **8 requests = 6 calls + 2 lần gửi lại do transport lỗi** ("Remote end closed connection", P0-5 check_visual) — đều là request thật, đếm ĐÚNG (reviewer thắc mắc 6 calls → 8 requests: đó là retry transport, không phải lỗi đếm; lỗi đếm thật chỉ ở đường chờ backoff 429, đã sửa bằng `wait_backoff()` — 0×429 nên không kích hoạt ở đây). Score 0/100 là điểm THẬT của build cũ (8 P0 đã xác minh → phạt 115 → kẹp 0), không phải lỗi harness. Mock 13/13 PASS (7 test mới CI-T4). |
| CI-T4 | LIVE, run 42993141273 trên main@767cb7e (full 17 mission, dispatch quick=false) | **1534s QA (25m34s) / ~30 phút cả workflow** | 95 | không áp dụng | **0 false pass** (8 PASS đều có bằng chứng thật, đã kiểm bằng mắt) nhưng **1/2 finding là false positive** (tỉ số bóng rổ 54:71) | **5 / 30-phút** (5 vision calls, 0 retry) | không | **Tốc độ vẫn <30 phút ✅ nhưng CHẬM LẠI** (1019s → 1534s). 8/17 PASS (từ 10/17): IPTV_EPG PASS lại (nhưng motion đo ở MainActivity, không phải trong player — PASS mềm); DATA_ACCURACY + SCHEDULE FAIL 'hôm nay' và IPTV_CATEGORIES FAIL 'tv360' — TRUNG THỰC hơn CI-T3 (header đã cuộn mất; CI-T3 PASS được nhờ dump chứa text offscreen — đúng lỗ reviewer chỉ ra). PLAYER_STREAMING FAIL A-B-A-B đúng (mở thẻ [SẮP ĐÁ] chưa đá → loading vô hạn → player tự thoát → dao động). VOD_PLAYER FAIL oan (phim thực sự phát — step_078 — nhưng motion đo None do watcher đói mẫu trong lúc dump WebPlayer 26.6s → stuck nổ sai). Breakdown observe: wait 141s / dump 443.4s (p90 21.5s) / detect 396.9s (tăng từ 55.8s — band hero OCR mới: bước 45/48 detect 64–73s, mà không bắt thêm lỗi hero nào). Reel ĐÃ SỬA ✅ (12.3s = 2×6s, đúng nội dung, speed_factor 4.0 trong report). Frame evidence ✅ (17/17 mission + 2/2 finding đều tồn tại). Eye-review (VISUAL-REVIEW.md): finding 1 thật (66 kênh) / 1 giả (54:71 bóng rổ NBL — luật plausibility bóng đá không áp cho bóng rổ; tỉ số tick 54:69→54:71 nên là thật); sót 3 lỗi thật (hero giờ đè phụ đề step_006/016; WebPlayer đè đôi tiêu đề step_071/082; hero title cắt trái — chưa chắc). Video chỉ 80% (1225/1534s, chunk cuối mất khi dừng quay). Điểm 65 (bỏ FP → 77). **Kết luận: CHƯA SWITCH — NEEDS-CI-T5** (tiêu chí 0 HIGH FP + eye check khớp report chưa đạt). Xem §15.6. |
| CI-T5 | LIVE, run 43010818257 trên main@bd6186d (full 17 mission, dispatch quick=false) | **843s QA (14m03s) / ~19 phút cả workflow** | 79 | không áp dụng | **0 false pass** (12 PASS đều có bằng chứng thật, đã kiểm bằng mắt 32/32 shot + 5 frame video) nhưng **1/3 finding là false positive HIGH** ("Xem ngay" bị tách đôi) + 1 MEDIUM chưa xác nhận | **8 / 30-phút** (8 vision calls: confirm 4 + stuck_assist 2 + check_visual 2, retries 0) | không | **Tốc độ ĐẠT MẠNH: 843s (−45% so với T4 1534s, T3 1019s)** — hero OCR mỗi 2 lần due + đo fallback. 12/17 PASS (từ 8/17): DATA_ACCURACY + SCHEDULE_EPG PASS lại nhờ cuộn lên đầu (header "Hôm nay" hiện); EPISODE_PICKER PASS nhờ goto-view-by-id (dialog Tập 1–8 thật); VOD_PLAYER PASS lại (FAIL oan T4 đã hết — native phát tới 02:08). Mock 24/24 PASS (13 cũ + 11 mới CI-T5, đã chạy lại độc lập EXIT=0); replay R6 giữ 8/8 P0, 0 false pass (sau fix mục 11 vision retry transport). Eye-review (VISUAL-REVIEW.md): finding 1 thật (66 kênh) / 1 giả HIGH ("Xem ngay" sạch trong crop 3× — detector tách 1 text thành 2 box) / 1 MEDIUM chưa xác nhận (focus trap: step_075=076 trùng sha, step_081 focus đã di chuyển). Sót lỗi thật: WebPlayer đè đôi tiêu đề CÒN NGUYÊN (step_063/066/067 + crop 2×) mà vision check 2 call KHÔNG bắt được; tiêu đề player "null · VIE - CHI" (step_015, trận [SẮP ĐÁ] mở player loading vô hạn — luật LIVE-only chưa bao phủ ROOM_PICKER); hero giờ đè phụ đề KHÔNG tái hiện (tour t=5s sạch). Video 83% (700.5/843s — chunk cuối vẫn mất ở normalize vì moov); reel 12.83s nhưng entry 3 (video_t 177.6s) VƯỢT tour 175.2s → chỉ 2/3 đoạn xem được. Điểm 65 (bỏ FP HIGH → 77; bỏ cả MEDIUM → 82). **Kết luận: CHƯA SWITCH — NEEDS-CI-T6** (tiêu chí 0 HIGH FP + eye check khớp report chưa đạt). Xem §15.7. |
| CI-T6 | LIVE, run 43027661716 trên main@ba1e55b (full 17 mission, dispatch quick=false) | **887s QA (14m47s) / ~20 phút cả workflow** | 72 | không áp dụng | **0 false pass theo luật gate** (14 PASS đều đạt điều kiện gate — 3 PASS mềm: IPTV_EPG, EPISODE_PICKER, WEBPLAYER_DIRECTED; WEBPLAYER_DIRECTED yếu nhất: không có bằng chứng phát nào, frame đóng băng 60,3s) nhưng **1/2 finding là false positive MEDIUM** (focus trap, bàn phím đang mở) | **5 / 30-phút** (5 vision calls: confirm 2 + stuck_assist 1 + check_visual 2, provider OPENAI, 0 retry) | không | **Verdict PASS lần đầu (79/100, 14/17).** Mục 2 vision check bắt được HIGH thật (tiêu đề WebPlayer đè đôi, step_059) — lỗi 3 vòng không bắt được; mục 1 hết FP "Xem ngay"; mục 9 step_id liên tục 1–72, không thiếu; mock 33/33 PASS (24 cũ + 9 mới); replay R7 giữ 8/8 P0, 0 false pass (tự chạy lại — NIM hết chập chờn, 6–7/8 của implementer đúng là lỗi transport; report đã lưu ở qa-run-43027661716/replay_R7_report.json). Eye-review (VISUAL-REVIEW.md): finding 1 thật (đè đôi tiêu đề) / 1 giả MEDIUM (focus trap: highlight phím đổi ⇧ (step_066) → 'z' (067) → 'q' → '▶' — bàn phím di chuyển được; guard đếm ký tự trong dump không có gì để đếm vì ui_state chỉ có 5 trường focused). 3 PASS mềm: EPISODE_PICKER (frame step_051 không thấy dialog dù dump ghi "Tập 1"), IPTV_EPG (frame chỉ thấy list), WEBPLAYER_DIRECTED (playback_readings [] — mục 8 chưa ghi được reading nào vì band dưới chưa từng được OCR: osd_visible=False chặn cả 3 detector; thời gian KHÔNG tăng đơn điệu 00:20→00:00→00:30→00:20, step_055=step_059 pixel-identical = đóng băng 60,3s). FAIL trung thực: ROOM_PICKER (dialog đã mở step 10 nhưng driver bấm tiếp vào player — gốc rễ: id của MatchDetailPanel không có trong dialog_id_set nên has_dialog=False; cái mở ra là detail panel, không phải RoomPickerDialog), PLAYER_STREAMING (dao động dialog↔list — luật goto-player mục 6 CHẠY 4 lần nhưng sai trạng thái, rule 0c2 không kiểm has_dialog), NAV_RAIL (rail không mở — lỗi app). Sót lỗi thật: Schedule hàng LIVE hiện giờ kickoff thay vì tỉ số (18:30/18:35, còn từ T3); player native "Đang tải luồng…" vô hạn + spinner đè nút ▶ PHÁT (step_012); hàng 66 kênh không được kiểm (driver không tới); nút "ÂM THANH & PHỤ ĐỀ" bị cắt mép phải khi focus (step_061/063, tour_160/165). Video 79% (702.8/887s, 4 chunk — moov-wait 60s đã chạy và thất bại, writer không finalize); reel 12.03s, cover 1/2 (entry 2 kẹp, video_t 178.3s > tour 175.77s). Điểm 79 (bỏ MEDIUM giả → 84). **Kết luận: CHƯA SWITCH — NEEDS-CI-T7** (0 HIGH FP ✅ lần đầu, nhưng eye check khớp report + reel/video chưa đạt). Xem §15.9. |
| CI-T3 | LIVE, run 42988753134 trên main@aec0695 (full 17 mission, dispatch quick=false) | **1019s QA (16m59s) / ~22 phút cả workflow** | 90 | không áp dụng (P0 cũ đã sửa; F62–F67 của fix loop 2 là đích kiểm chứng mới) | **0 false pass** (10 PASS đều có bằng chứng, đã kiểm bằng mắt) nhưng **4/5 finding là false positive** | **5 / 30-phút** (4 vision calls + 1 retry) | không | **MỤC TIÊU TỐC ĐỘ ĐẠT: <30 phút** ✅ (QA 17 phút, từ 38 phút CI-T2, baseline 74m26s). 10/17 PASS (từ 4/17): reset về MainActivity+tab chạy — 5 mission trước FAIL vì kẹt player nay PASS. Observe p50 3.65s (CI-T2: 13.46s); breakdown: dump p50 1.60s nhưng tổng 321.7s (60% observe, max 29.14s) — nút thắt tiếp là uiautomator dump. vision_s 90.0s (đã sửa đúng). Video 904s (6 chunk chuẩn hóa) → tăng tốc 4x thành 226s, độ phủ 89% — đủ cả run lần đầu. Eye-review (VISUAL-REVIEW.md): finding 1 thật (hàng Địa Phương 66 kênh) / 4 giả (1 OCR rác 'LPđPfUHPBIHUALI' + 3 đồng hồ trận đấu 15:11/17:23/20:25 bị tố là tỉ số); bỏ sót 3 lỗi thật (hero: giờ đè phụ đề; Schedule: hàng LIVE hiện giờ đá thay vì tỉ số; WebPlayer: tiêu đề đè đôi). Xác minh sửa đúng: P0-8 logo VTV Cần Thơ, F62 tỉ số Home sau load, F63 WebPlayer OSD + seek 00:10→00:20, settings dialog sạch. Lỗi harness còn lại (đợt CI-T4): reel sai 4x, fake-score nhầm đồng hồ, frame evidence của FAIL thiếu 6 cái, detector kẹt không bắt luân phiên A-B-A-B, motion native player 0.00 ở cả 11 bước. |

### 15.1. Bài học CI-T1 (run 42976407479) — 5 lỗi, đã sửa hết trước CI-T2

| # | Lỗi ở CI-T1 | Bằng chứng | Sửa |
|---|---|---|---|
| 1 | **Watcher không bao giờ `start()`** | `motion_seen: false` mọi mission; `screenshots: []`; `observe_s` 800s/76 bước = 10.5s/bước (timeout `wait_stable` 8s mỗi lần); vision-assist không chạy được vì `frame_png=None` → 0 vision call. | `runner.run()` gọi `watcher.start()` sau khi ghi `start_time`, `finish()` gọi `watcher.stop()`; `perception.wait_stable` thêm lối thoát: video đang phát (motion ≥0.35%) thì lấy frame mới nhất sau 2.5s thay vì chờ 8s (video không bao giờ "ổn định"). Mock runner: observe 1.8–1.9s cho 3 bước (trước: 8s+/bước). |
| 2 | **Dialog chào mừng "THÔNG BÁO" lần đầu chặn cả run** | Eye-review 4 frame video (0s–135s) giống hệt nhau: dialog Telegram che màn hình, nút "ĐÃ HIỂU / ĐÓNG" focus đỏ. Harness cũ bấm OK trên `btnCloseFeedback` ở bước 1 (xem timeline run 42963719447); driver mới không có luật đóng dialog → `Kẹt cấp 2` ở 16/17 mission. | `device.dump_ui_state` trả thêm `dialog_ids` (thêm `btnCloseFeedback`, `dialogBtnClose`); `driver` luật 0 `_dismiss_dialog_action` (OK nếu focus vào nút đóng, không thì BACK, tối đa 3 lần rồi FAIL rõ lý do); `runner._settle_blocking_dialog` đóng dialog welcome NGAY ĐẦU mỗi mission, trước khi gate nhìn thấy nó (tránh pass giả: dialog welcome thỏa `needs_dialog` của mission khác). Mock: `DIALOG_DISMISS_OK`. |
| 3 | **`render_html` crash** | Log CI: `ValueError: unsupported format character ';'` ở cuối run (bị `\|\| true` nuốt) → mất `qa_report.html` + `qa_session.json`. Nguyên nhân: template dùng `%`-format, CSS chứa `width:100%`. | Nối chuỗi bằng placeholder `__TOKEN__` + `.replace()` (không dùng `%`-format); thêm dòng NIM vào HTML. Mock: HTML render OK. |
| 4 | **Verdict PASS khi 16/17 FAIL** | Điểm 81/100 (trừ mission FAIL tối đa 20 điểm) + verdict `PASS` dù chỉ 1/17 pass — nói dối kiểu mới. | Verdict PASS cần đủ 3 điều: điểm ≥75 **và** tỉ lệ pass ≥80% **và** không CRITICAL. Mock: 1/17 pass, điểm 81 → `NEEDS_FIX` (`VERDICT_OK`). |
| 5 | **Video chỉ 176s (1 chunk)** | `_dur()` đọc `ffprobe format=duration` ra N/A → trả 0.0 → mọi chunk bị loại "hỏng". Run cũ 42963719447 cũng chỉ 169s, 30× "Bo chunk hong" — **lỗi hệ thống của recorder, video các run cũ cũng chỉ là chunk đầu (~3 phút)**; bằng chứng đầy đủ của run cũ là 154 ảnh + timeline, không phải video. | `video_recorder.py` (đã được duyệt giữ, 2026-11-11 14:24): `_dur` fallback sang stream duration, trả **-1.0 khi không đọc được** (không rõ ≠ hỏng), chunk -1 được giữ để ghép thử, concat quyết định; fallback chọn chunk dài nhất theo **kích thước file** khi duration chưa biết. Ranh giới từ giờ: không sửa thêm file nào ngoài `realtime/` + workflow trial nếu chưa hỏi. |

### 15.2. Kiểm chứng local cho fix `_dur` (2026-11-11, trước CI-T2)

`video_recorder.py` import OK. Chạy thật `VideoRecorder.stop_and_save()` với adb
giả (`/tmp/test_vr_dur.py`), chunk mẫu tạo bằng ffmpeg: `good.mp4` 5s đọc được
duration; `na1/na2.mp4` là raw H.264 đổi tên `.mp4` — ffprobe trả `N/A` cả
format lẫn stream duration (đúng như chunk screenrecord ở CI) nhưng vẫn
decode được; `short.mp4` 0.5s; `garbage.mp4` 5 KB rác.

| Run | Chunk | Kết quả | Kết luận |
|---|---|---|---|
| A | [good 5s] | final 5.0s | Duration đọc được → ghép bình thường. |
| B | [na 4s, na 4s] | **final 8.0s**, log có "Không đọc được duration", KHÔNG có "Bo chunk hong" | **Chứng minh fix:** 2 chunk N/A được giữ + ghép thành 8s (code cũ loại cả 2, chỉ còn chunk đầu ~4s — đúng lỗi CI-T1/42963719447). |
| C | [short 0.5s] | final 0.5s, log có "Bo chunk hong" | File ngắn/hỏng thật vẫn bị loại (hành vi cũ giữ nguyên). |
| D | [good 5s, garbage 5 KB] | final 5.0s | Concat lỗi vì chunk rác → fallback chunk dài nhất (good), không crash. |
| E | [na 4s, good 5s] | final 4.1s | **Hạn chế đã biết:** trộn 2 định dạng khác nhau (raw H.264 + mp4) thì ffmpeg concat làm rơi đoạn sau do PTS rác của raw H.264. Không phải case thật — mọi chunk screenrecord cùng 1 format/timebase (như run B). Chỉ yêu cầu: có video ra, không crash. |

`VR_DUR_OK` (5/5). Replay vòng 4 chạy lại sau các sửa judge/device (`/tmp/qa_realtime_replay_round4b`, 106.2s): **P0 recall 8/8, 0 false pass, 6 vision calls, 7 NIM requests, 0×429** — không đổi so với vòng 4.

### 15.3. Bài học CI-T2 (run 42979726992) — và kế hoạch CI-T3

| # | Vấn đề ở CI-T2 | Bằng chứng | Sửa cho CI-T3 |
|---|---|---|---|
| 1 | **Kẹt trong PlayerActivity từ mission 3** — 7 mission FAIL oan chỉ vì không quay về được MainActivity | Timeline: SPORTS_ROOM_PICKER (bước 4) OK mở player; 7 mission sau (SPORTS_DATA_ACCURACY, HOME_BILLBOARD, SCHEDULE_EPG, SIDEBAR_RAIL, IPTV_CATEGORIES, PHIM_NGUONC, SEARCH_AND_SETTINGS) đều FAIL "missing activity MainActivity". Video v_700/v_1200: app đứng yên trong player SCTV2 giữa run, toast "Đã thêm SCTV2 vào Yêu Thích" (long-press favorite thật ra đã chạy). | `MissionSpec.tab` (13 mission gán tab đích: 6=TRANG CHỦ, 0=TRỰC TIẾP, 1=LỊCH, 2=IPTV, 3=TÌM KIẾM, 5=KHO PHIM); `runner._reset_to_mission` — BACK ×3 → `launch_app()` → SWITCH_TAB đích, chạy đầu mỗi mission không-directed, TRƯỚC settle dialog; driver luật 0b (sai tab → SWITCH_TAB) + luật 0c (mission cần player, đang ở MainActivity, focus ≠ NONE → OK mở player). Mock: `RESET_OK` (PlayerActivity + tab 0 → BACK về MainActivity + SWITCH_TAB 6 trước khi mission chạy). |
| 2 | **Motion đo 0.00 dù video đang phát** | Timeline: 95 bước player, motion_delta p50 0.00, p90 0.00, >0.35 = 2%. IPTV_EPG FAIL "motion: video chưa từng chuyển động" trong khi step_071/v_700/v_1200 thấy video phát rõ. | `perception.py`: MOTION_WINDOW_S 2.0→4.0s (cửa sổ 2s với sample 1.2s chỉ có ~1.7 mẫu — `motion_delta` trả -1 khi <2 mẫu, timeline lưu 0.0), SAMPLE_PERIOD_S 1.2→1.0s; `runner._observe`: ở player mà motion_delta == -1 thì poll tối đa 3s chờ đủ mẫu; `driver.note_state`: video đang phát TRONG PLAYER thì reset streak kẹt về 0 (UI không đổi là bình thường khi phim chạy — WebPlayer directed ở CI-T2 FAIL "kẹt cấp 2" ở bước 8 dù video phát); ngoài player vẫn tính kẹt ở 3 bước. Mock: `MOTION_STUCK_OK` (7 trạng thái giống nhau + motion trong player → không kẹt; không motion → kẹt ở 3). |
| 3 | **Observe chậm: p50 13.5s, p90 34.3s, max 57s** | Timeline CI-T2: observe_s tổng 1764.8s/112 bước; 25 bước >20s (tập trung ở PlayerActivity/WebPlayerActivity, bước 89–92 WebPlayer: 23.5/43.2/32.9/34.9s). CI-T1 là 10.5s/bước (watcher chết, timeout 8s + dump/detect ~2.5s); CI-T2 chậm hơn vì frame thật khiến OCR thực sự chạy. | Đo trước tối ưu sau: `_observe` ghi breakdown `{wait, dump, detect}` vào timeline + in cảnh báo khi observe >15s; `device.dump_ui_state` gộp rm + dump + cat vào 1 lần adb (trước: 3 lần riêng); kết quả breakdown ở CI-T3 mới cho biết phần nào là nút thắt thật. |
| 4 | **Video vẫn 175s — ffmpeg không có trên CI runner** | Log 08:11:09Z: `Ghep video that bai (rc=127): /bin/sh: 1: ffmpeg: not found`. `_dur` fix đã làm đúng việc (13 chunk giữ lại, log "Không đọc được duration … giữ lại để ghép thử" ×13, 0× "Bo chunk hong"); chỉ concat không chạy được. | Workflow trial: Install deps cài thêm `ffmpeg` (ghi chú trích CI-T2 rc=127). Chứng minh local: nối 13 chunk artifact bằng ffmpeg local → `full_reconstructed.mp4` 1926s (11 chunk × 175s; chunk_13 loại — "moov atom not found", đang ghi thì run kết thúc). |
| 5 | **`vision_s` báo sai** | Report CI-T2: `vision_s` 7.7s — chỉ cộng đường confirm; thực tế 7 call × 12.4s trung bình ≈ 87s. | `runner.finish()`: `vision_s = round(sum(self.vision.latencies), 1)` — tổng mọi loại call, ghi rõ trong code. |
| 6 | **`step_085` thiếu trong artifact** | WebPlayer directed mission PASS với bằng chứng vision ("00:20 / 24:14") nhưng frame step_085 trích dẫn không có trong artifact — runner chỉ lưu frame khi có defect hoặc mỗi bước thứ 5; frame của vision confirm không được lưu. | `runner._finish_mission`: khi mission PASS có bằng chứng vision, lưu frame xác nhận (PNG cuối của mission) ra `shots/<frame_ref>` nếu chưa có — bằng chứng trích dẫn phải tồn tại trên đĩa. *(Làm trước khi commit CI-T3.)* |
| 7 | **10/11 finding là OCR đọc nhầm nội dung video** | Eye-review: #1 box cao 0px ở y=1079 (step_052, OSD sạch); #2 box rộng cả màn hình (0,1020)-(1920,1079); #3 'Maldiv…' vs '‹©' 87% (step_004); #4 '1Ì' vs '¬c:' 42%; #5/#6 '7A' vs 'ý'/'¬' 77%; #7/#8 '"7a' vs '7'/'9`' 92%/82% (step_091, OSD ẩn — chỉ là frame anime, phụ đề là của video); #9/#10 '¬:' vs 'D'/'xế' 88%/100% (step_094, credit tiếng Nhật ở mép). Mẫu chung: box rác 1–2 ký tự, box ở mép màn hình, OCR trên nội dung video khi OSD ẩn. | Guard trong `detectors.py`: (a) helper `_plausible_text` — box overlap phải có ≥2 chữ cái và dài ≥3 (giết '‹©', '1Ì', '¬c:', '7A', 'ý', 'D', '¬'; giữ 'VTV4 HD'/'TRANG CHỦ'/'TRỰC…'); (b) clipped: bỏ box cao/rộng <4px (mép 0px) và box rộng >80% màn hình, token cắt (trừ '…') ≥4 ký tự (giữ P0-4 'TRỰC…'); (c) **OSD gate**: trên frame player, bỏ qua detector OCR band dưới (overlap band dưới, clipped, subtitle) khi `osd_visible` là False tường minh; None (không rõ, vd replay dữ liệu cũ) thì chạy như trước. Finding 11 thật (step_094, OSD hiện) được giữ. (d) subtitle detector: box cắt ngang phải có ≥2 chữ cái (từ tiếng Việt 2 ký tự như 'há' vẫn tính; 'W8' rớt nhưng còn 'bản','mãi' → đủ ≥2 box, finding giữ). Mock: `OSD_GATE_OK` trên frame thật (step_091 OSD ẩn → 0 finding; step_094 OSD hiện → đúng 1 finding subtitle đè seekbar). |
| 8 | **1 finding THẬT: phụ đề WebPlayer đè seekbar (P0-5-class)** | step_094: phụ đề "Vừa khỏi phải thấy bản mặt khó ưa" cắt ngang seekbar y 869–890, OSD hiện, seekbar 00:25/23:49, nút TUA ±10S / TẬP TIẾP / DANH SÁCH TẬP / ÂM THANH & PHỤ ĐỀ. Phụ đề này là của web embed, fix neo phụ đề của native player không chạm tới. | Harness: không đổi gì — detector đã bắt đúng, guard mới giữ finding này (OSD hiện). Báo cho parent/fix loop: lỗi thuộc về WebPlayer embed, cần fix riêng (không phải lỗi harness). |

**Lệnh Evelyn 2026-11-11 15:16:** dừng MỌI việc khác, tập trung 100% vào nâng cấp/sửa bộ QA mới. Fix loop 2 đã đóng (QA re-run 42979216404 hủy — chạy lại được từ head f3863ab). **Lệnh 15:18:** khi bộ QA mới XONG, đẩy thẳng lên main — không cần duyệt riêng. Merge chỉ QA (realtime/ + workflow trial + fix `video_recorder.py`); trial branch đang ngồi trên apple-kl8 nên merge thường sẽ kéo cả KL8 vào main — CẤM, chỉ cherry-pick commit QA. Merge KL8 app vẫn cần cô ấy duyệt riêng sau. **Lệnh 15:25 ("Gộp cả KL8 lên main luôn"): KL8 ĐÃ MERGE lên main cùng ngày ở 54287ff** (132 file, audit 175/175, Build 42987064612 SUCCESS) — và cô ấy cho phép QA merge thẳng qa-realtime-trial vào main mới (plain merge, vì c4de57e đã nằm trong lịch sử main). **Hệ quả cho CI-T3: fix loop 2 (F62/F63/F64/F65/F66/F67) ĐÃ NẰM trong merge 54287ff — CI-T3 từ main là lần kiểm chứng ĐẦU TIÊN xem các fix đó có chạy thật không** (QA re-run của loop 2 đã bị hủy). Lưu ý merge: `video_recorder.py` trên main có thêm F67c của loop 2 (`import json`, `_start_wall`, `_norm_chunks` — chuẩn hóa chunk CFR) mà trial branch chưa có; khi merge phải giữ CẢ F67c VÀ fix `_dur` của QA (xung đột phải giải bằng tay, kiểm chứng lại bằng test `_dur` trước khi đẩy main).

### 15.4. CI-T3 eye-review (run 42988753134) — tóm tắt, chi tiết ở qa-run-42988753134/VISUAL-REVIEW.md

- **0 false pass** (10/17 PASS đều có bằng chứng thật, kiểm bằng mắt từng ảnh).
  Nhưng findings: **1 thật / 4 giả** — precision kém, chưa đạt chuẩn switch-over
  ("eye check matches report").
- 4 FP: (1) overlap 'LPđPfUHPBIHUALI' — OCR hallucinate chữ hero, qua guard
  vì đủ chữ cái; (2–4) '15 : 11' / '17 : 23' / '23 : 28' — đồng hồ trận đấu
  MM:SS tăng dần (15:11 → 17:23 → 20:25), detector tố nhầm là tỉ số; frame
  trích dẫn không chứa đúng giá trị bị tố (giá trị từ card ngoài màn hình).
- 3 lỗi thật bị bỏ sót: hero Sports — giờ "15:44" đè phụ đề (step_006/016);
  Schedule — 2/4 hàng LIVE hiện giờ đá 15:00 thay vì tỉ số (step_021/031/033);
  WebPlayer — tiêu đề đè đôi (step_073/076/077).
- Xác minh sửa đúng trên main: P0-8 logo, F62 tỉ số Home (sau load), F63
  WebPlayer OSD + seek, settings dialog, search, IPTV EPG.
- Harness còn phải sửa (CI-T4): reel dùng `video_t` giờ thật cắt vào video
  đã tăng tốc 4x → 3/5 đoạn rỗng, 2 đoạn lệch; frame evidence của mission FAIL
  thiếu 6 cái (`_finish_mission` chỉ lưu khi PASS); detector kẹt không bắt
  luân phiên A-B-A-B (EPISODE_PICKER focus nhảy btnHeroBackHome ↔ heroPlay 9
  bước); motion native player = 0.00 ở cả 11 bước lấy mẫu (stream bóng rổ NBL
  thật ra đã phát — thấy trong reel — nhưng mission PLAYER_STREAMING check
  quá sớm, chỉ gặp frame "Đang tải luồng...").
- Run đối chứng trial 42988508129 (build cũ): 10/17 PASS, điểm 20, QA 1014s,
  NIM 5, 0×429 — cùng 10/17, khác phân bổ (IPTV_EPG PASS / VOD_PLAYER FAIL,
  ngược với main) → motion/kẹt flaky theo thời điểm, không phụ thuộc build.

### 15.5. Reviewer độc lập (2026-11-11) — verdict NEEDS-CI-T4

Reviewer (agent 0005a1a4) tự chạy lại replay (102.8s: **8/8 P0, 0 false pass,
6 vision calls, 8 NIM requests, 0×429** — khớp R4/R4c) và tự kiểm code +
artifact CI-T3. Kết luận: tốc độ (17p), recall P0 offline (8/8), 0 false
pass đều đạt — nhưng **4/5 finding là giả (80% FP), defect reel sai hoàn
toàn, 6/7 frame bằng chứng của mission FAIL không tồn tại**, và 2 lỗ
false-pass cấu trúc chưa ai phát hiện. Switch bây giờ là thay một harness nói
dối kiểu cũ bằng một harness nói dối kiểu mới, chỉ rẻ hơn.

| # | Lỗi reviewer tìm được | Bằng chứng | Sửa cho CI-T4 |
|---|---|---|---|
| 1 | **Reel sai 4x (P0)** | `judge.py:74-94` cắt `video_t` trực tiếp; `video_recorder.py:168-172` tăng tốc 904s → 4x → 226s, `stop_and_save` không trả hệ số. Reel entries t=[25.1, 202.5, **292.2, 411.4, 552.2**] — 3 cái > 226s → rỗng; reel 18.6s thay vì 30s. | `stop_and_save()` trả `speed_factor` + `recorded_seconds`; `build_defect_reel(..., speed_factor)` chia `video_t` cho hệ số, ghi `video_t` (vị trí trong file) + `speed_factor` vào entry; runner ghi `video_speed_factor` vào report. Mock `REEL_4X_OK`: tour 12s→4x→3.2s, reel đủ 6.4s, entries video_t=[1.2, 2.5]. |
| 2 | **Fake-score nhầm đồng hồ MM:SS (P0)** | `detectors.py:29` nhánh giờ chỉ khớp HH:MM (phút thứ 2 ∈ {0,15,30,45}), không bao giờ khớp đồng hồ phút:giây (15:11, 17:23, 20:25, 23:28) → rơi vào nhánh phi lý. Không lọc bounds, không kiểm ổn định. Step_027 hiện "15 : 11" nhưng finding tố "17 : 23" trên đúng frame đó. | (a) **Gốc:** `device.dump_ui_state` lọc node có bounds ngoài viewport 1920×1080 khỏi `all_visible_texts` (node không parse được bounds thì giữ) — diệt cả FP fake-score lẫn rủi ro gate PASS nhờ text offscreen. (b) `detect_fake_score` chỉ tố khi cùng giá trị trên cùng view đã thấy ở **2 observation khác nhau** (đồng hồ đổi mỗi lần thấy → không bao giờ tố; tỉ số giả đứng yên → tố); evidence frame = lần thấy thứ 2 (chứa đúng giá trị tố). Mock `FAKE_SCORE_CLOCK_OK`. |
| 3 | **Dump không lọc bounds (P0, gốc của #2)** | `device.py:220` gom mọi node có text, kể cả node ngoài viewport của RecyclerView. | Xem #2(a). |
| 4 | **Frame FAIL thiếu (P0)** | `runner.py:371` chỉ lưu frame khi PASS; 6/7 frame evidence của mission FAIL thiếu trên đĩa (step_012/018/040/050/057/069). | `_finish_mission` lưu frame cuối cho **mọi** outcome (bỏ điều kiện `== "PASS"`). Mock `FAIL_FRAME_OK`: frame evidence của mission FAIL tồn tại trên đĩa. |
| 5 | **Kẹt A-B-A-B không bị bắt (P0)** | `driver.py:52-78` chỉ bắt "đứng yên"; EPISODE_PICKER nhảy btnHeroBackHome ↔ heroPlay qua lại nên không kẹt. | `note_state` thêm `_revisit_streak`: cùng state xuất hiện lại trong 6 state gần nhất = 1 lần quay lại; **2 lần quay lại = kẹt** (vision-assist hoặc FAIL cấp 2). Mock `STUCK_ABAB_OK`. |
| 6 | **Guard OCR chuỗi rác (P1)** | `_plausible_text` chỉ đếm chữ cái: 'LPđPfUHPBIHUALI' (15 chữ cái liền nhau) qua được. | Thêm: token dài nhất > 12 ký tự liền nhau → rác; token > 6 chữ cái mà tỉ lệ nguyên âm < 0.15 → rác (không áp cho token ngắn: acronym 'VTV4', 'HD' không nguyên âm vẫn thật). Mock `PLAUSIBLE_GARBAGE_OK`. |
| 7 | **Motion native player (P1)** | Vision xác nhận "đang phát" trên frame "Đang tải luồng..." (PLAYER_STREAMING chối 2 lần); `runner.py:294` ghi motion_delta -1 (chưa đo được) thành 0.00 (đứng yên). | `_vision_confirm`: mission cần motion mà obs hiện tại không có motion → **poll watcher tới 10s** trước khi gọi vision; hết 10s vẫn không có → trả False KHÔNG gọi vision, không tính denial. Timeline ghi `motion_delta: null` khi -1 (replay đã chịu được null: `or 0`). |
| 8 | **Stress gate không kiểm foreground (P1)** | `gate.py:137-142` kind stress chỉ cần `steps >= max_steps` là PASS; app crash văng về launcher vẫn PASS. | Stress PASS cần activity cuối thuộc package `com.kenhlive.tv` (chỉ kiểm package — launcher cũng có class MainActivity nên không so tên class). Mock `STRESS_GATE_OK`. |
| 9 | **Đếm NIM trùng (P2)** | Retry = 2 requests trong thống kê (acquire trong vòng retry + acquire để chờ backoff): 6 calls → 8 requests; CI-T3: 4 calls → 5 requests. | `ratelimit.wait_backoff()`: chờ hết backoff KHÔNG chiếm slot, KHÔNG đếm request; `note_retry()` đếm riêng retries; `nim_stats()` thêm `provider`. Mock `RATELIMIT_WAIT_OK`. |
| 10 | **OCR band hero thiếu (P2)** | Step_006 giờ đè phụ đề hero bị sót: OCR chỉ soi band nav (0–140) + band dưới (850–1080), vùng hero (140–850) không bao giờ được OCR. | Thêm `HERO_BAND=(0,140,1920,850)` vào `detect_text_overlap`, chỉ ngoài player (trong player vùng này là nội dung video). |
| 11 | **Tên frame không truy được mission (P2)** | `runner.py:110` `mission_name.lower()[:8]` = `"mission_"` với mọi mission. | Frame slug = tên mission bỏ tiền tố `MISSION_`, lấy 8 ký tự đầu (VD `cold_sta`, `sports_m`). |
| 12 | **Nợ ghi rõ, chưa làm trong CI-T4** | Driver không bao giờ phát `LONG_PRESS` (IPTV favorites chưa từng kiểm tra thật); ROOM_PICKER/EPISODE_PICKER không phân biệt "OK mở dialog" vs "OK mở player" (2 mission này có thể không PASS được bằng driver hiện tại — cần luật riêng, không phải lỗi app). | Ghi nợ ở đây + SWITCHOVER.md; làm ở vòng sau nếu cần. |
| 13 | **Tài liệu stale** | `missions.py` docstring "18 mission" nhưng chỉ có 17; SWITCHOVER.md không có tiêu chí FP findings (về mặt chữ harness vẫn "đạt" dù 80% finding giả) và vẫn viết "quyết sau CI-T1+CI-T2". | Docstring → 17. SWITCHOVER.md: thêm tiêu chí **0 HIGH false-positive** + quyết sau CI-T3/CI-T4 thay vì CI-T2; sửa code chết `runner.py:273` (`views = [n["id"] for n in []]`). |

Điểm 32/100 của CI-T3 là số học đúng nhưng bị FP chi phối: 60 điểm phạt
findings (48 điểm từ 4 FP) + 8 điểm phạt 7 mission FAIL. Sau khi sửa FP, điểm
kỳ vọng ~80 với cùng build — khi đọc điểm phải báo rõ điều này.

**Kiểm chứng sửa CI-T4 (local, trước khi commit):** mock 13/13 PASS
(6 cũ DIALOG_DISMISS/MOTION_STUCK/VERDICT/RESET/OSD_GATE/MOCK_RUNNER +
7 mới REEL_4X/FAKE_SCORE_CLOCK/STUCK_ABAB/STRESS_GATE/PLAUSIBLE_GARBAGE/
FAIL_FRAME/RATELIMIT_WAIT); replay R5 (xem bảng §15) — mục tiêu giữ 8/8.

### 15.6. CI-T4 eye-review (run 42993141273) — tóm tắt, chi tiết ở qa-run-42993141273/VISUAL-REVIEW.md

- **Sửa CI-T4 đều chạy đúng:** reel 12.3s đủ 2 đoạn đúng nội dung (speed_factor
  4.0 trong report); frame evidence 17/17 mission + 2/2 finding đều tồn tại;
  FP đồng hồ và FP OCR rác biến mất hoàn toàn; kẹt A-B-A-B bắt được thật;
  stress gate kiểm foreground; NIM 5 requests = đúng 5 vision calls, 0×429.
- **Nhưng có FP loại mới:** '54 : 71' là tỉ số bóng rổ NBL thật đang tick
  (54:69 → 54:71), luật plausibility bóng đá không áp được cho bóng rổ.
  Precision 1/2 (CI-T3: 1/5). Tiêu chí switch-over "0 HIGH FP" CHƯA ĐẠT.
- **False-negative mới:** VOD_PLAYER FAIL kẹt trong khi phim thực sự phát
  (step_078) — watcher đói mẫu khi dump WebPlayer 26.6s nên motion = None,
  no-change streak nổ sai trong player.
- **FAIL trung thực mới (tốt):** DATA_ACCURACY/SCHEDULE FAIL 'hôm nay',
  IPTV_CATEGORIES FAIL 'tv360' — header đã cuộn mất; CI-T3 PASS được là nhờ
  dump chứa text offscreen (đúng lỗ reviewer chỉ ra), giờ đã đóng.
- **Sót 3 lỗi thật:** hero giờ đè phụ đề (step_006/016 — band hero OCR không
  tách được 2 lớp chữ chồng); WebPlayer đè đôi tiêu đề (step_071/082); hero
  title cắt trái (chưa chắc — có thể là trạng thái cuộn).
- **Tốc độ:** QA 1534s (25m34s) vẫn <30p nhưng chậm lại từ 1019s — band hero
  OCR làm detect tăng 55.8s → 396.9s; dump vẫn nút thắt lớn nhất (443.4s,
  p90 21.5s). Video chỉ 80% (chunk cuối mất khi dừng quay).
- **Kết luận: CHƯA SWITCH — NEEDS-CI-T5.** Danh sách sửa CI-T5 (10 mục, xem
  VISUAL-REVIEW.md §9): fake-score theo môn thể thao; motion fallback
  pixel_diff + không tính kẹt khi motion UNKNOWN trong player; driver chỉ mở
  thẻ LIVE + bấm Play khi WebPlayer chưa phát; driver cuộn lên đầu cho list
  mission; gate gắn motion với activity đích; giảm chi phí hero OCR; vision
  check hero + title player; giữ chunk cuối video; driver đi tới view đích
  theo id; LONG_PRESS (nợ cũ).

### 15.7. CI-T5 eye-review (run 43010818257) — tóm tắt, chi tiết ở qa-run-43010818257/VISUAL-REVIEW.md

- **Sửa CI-T5 đều chạy đúng (mắt):** fake-score theo môn (bóng rổ 79:52→81:56
  tick thật, không bị tố); VOD_PLAYER PASS lại (FAIL oan T4 hết); cuộn lên
  đầu đầu mission list (DATA_ACCURACY + SCHEDULE_EPG PASS lại, header "Hôm
  nay" hiện); goto-view-by-id (EPISODE_PICKER PASS, dialog Tập 1–8 thật);
  ROOM_PICKER FAIL đúng lý do "OK mở PLAYER thay vì dialog"; tốc độ
  1534s → 843s (−45%). Mock 24/24 PASS (chạy lại độc lập EXIT=0);
  replay R6 giữ 8/8 P0, 0 false pass.
- **Nhưng có FP HIGH loại mới:** "Xem ngay" (step_010) — crop 3× cho thấy pill
  đỏ sạch hoàn toàn; detector tách 1 text thành 2 box rồi tố chồng 93%.
  Precision findings 1/3 (CI-T4: 1/2). Tiêu chí "0 HIGH FP" CHƯA ĐẠT.
- **Vision check hero/title (mục 7) bỏ sót đúng lỗi nó cần bắt:** tiêu đề
  WebPlayer đè đôi còn nguyên (step_063/066/067 + crop 2×) mà 2 call
  `check_visual` không sinh finding. Hero giờ đè phụ đề thì KHÔNG tái hiện
  (tour t=5s sạch — có thể đã hết hoặc tùy trạng thái hero).
- **Lỗi thật mới thấy bằng mắt:** tiêu đề player "null · VIE - CHI"
  (step_015, trận [SẮP ĐÁ] INTERF 19:00 mở player → "Đang tải luồng…" vô
  hạn — luật LIVE-only chưa bao phủ ROOM_PICKER); IPTV player cũng loading
  rồi tự thoát (step_051→052); rail vẫn không mở bằng DPAD_LEFT (app);
  hàng 66 kênh còn nguyên.
- **Video + reel:** 83% (700.5/843s — chunk cuối vẫn mất ở normalize vì
  `moov atom not found`, mục 8 chỉ làm được nửa đường). Reel 12.83s:
  entry 1+2 khớp đúng nội dung, entry 3 (video_t 177.6s) VƯỢT tour 175.2s
  → chỉ còn 0.6s (reviewer độc lập trích reel t=12.5s: thấy thoáng màn
  Tìm kiếm + bàn phím — đoạn 3 CÓ tồn tại nhưng không đủ 6s).
- **Điểm 65** = 100 − 24 (2 HIGH) − 5 (1 MEDIUM) − 6 (5/17 FAIL); bỏ FP
  HIGH → 77; bỏ cả MEDIUM chưa xác nhận → 82. Vẫn NEEDS_FIX.
- **Kiểm chứng sửa CI-T5 (local, trước khi commit):** mock 24/24 PASS
  (13 baseline + 11 mới CI-T5); replay R6 8/8 P0; Build APK xanh từng
  commit (12 commit 05c9b3e→bd6186d, QA-only, diff đã kiểm: không code app).
- **Kết luận: CHƯA SWITCH — NEEDS-CI-T6.** Danh sách sửa CI-T6 (10 mục, xem
  VISUAL-REVIEW.md §9 + bổ sung sau review độc lập): text-overlap chỉ tố
  khi box nhỏ ≥~90% nằm trong box lớn + cùng baseline/dòng OCR (SỬA: guard
  chuỗi con như ghi ban đầu là SAI — "Xem" in "ngay" = False, đã kiểm bằng
  code; gốc rễ là `ocr.py read_boxes` PSM 11 không khử trùng); debug vision
  check title (crop + prompt + regression test bằng step_063; log rõ 2 call
  `check_visual` đã soi frame nào); chờ moov khi finalize video (độ phủ
  >95%); reel kẹp entry vượt tour + báo reel cover; sửa spec
  IPTV_CATEGORIES ('tv360' chỉ là ảnh logo) + SPORTS_MULTI_SOURCE
  ('socolive' không tồn tại dạng text); mở rộng LIVE-only sang ROOM_PICKER;
  goto-player cho PLAYER_STREAMING; focus-trap chỉ nổ khi ≥2 quan sát khác
  nhau + không có bàn phím; bỏ shot trùng hash; yêu cầu bằng chứng thời
  gian phát tăng giữa 2 quan sát cho mọi mission player PASS (WebPlayer
  đóng băng 00:20 qua 3 quan sát mà vẫn PASS — reviewer phát hiện); điều
  tra timeline thiếu step_id 14 (79 entry, id 1–80 thiếu 14); kiểm
  `video_recorder.py` (dùng chung với harness cũ) trước switch; ghi rõ
  provider thật trong report (CI-T5 là OPENAI, không phải NVIDIA NIM).
  App (không phải harness — ghi cho fix loop): WebPlayer đè đôi tiêu đề,
  title "null · VIE - CHI", logo player "BOX MOVIE" sai cho kênh 360 Hoa
  Ngữ (crop xác nhận), spinner loading đè nút ▶ PHÁT, SẮP ĐÁ loading vô
  hạn rồi tự thoát, rail không mở, hàng 66 kênh. ("Về trực tiếp" kề sát
  "TRỰC TIẾP" — crop cho thấy có khe hở, KHÔNG phải lỗi đè.)

### 15.8. CI-T6 — danh sách sửa (10 mục, VISUAL-REVIEW.md §9 + §10)

Bảng này ghi từng mục CI-T6 khi xong (1 mục = 1 commit trên main, Build APK
xanh từng commit, mock + replay giữ nguyên). Replay baseline trước CI-T6
(chạy local 2026-11-11, đã gồm code mục 1+2 trong cây): **8/8 P0, 0 false
pass, 6 vision calls, 8 requests (6 call + 2 retry transport), 0×429**,
missions 3 PASS / 3 FAIL / 11 UNVERIFIED, điểm 0/100 (điểm THẬT của build cũ).
Mock baseline trước CI-T6: 26/26 _OK (24 cũ + N1 + N2) sau khi cài lại
tesseract 5.3.4 + vie local (VM restart làm mất bản cài ngày 2026-11-11).
Lưu ý môi trường: NIM qua surrogate chập chờn theo thời điểm (connection
reset ~10s/lần thử, đã gặp 4 lần liên tiếp rồi tự hết; helper-style POST
không User-Agent chạy 200 trong 5.5s — không phải lỗi header; retry
transport trong `vision._post` vẫn là lưới an toàn đúng).

| Mục | Sửa | Kiểm chứng |
|---|---|---|
| 1 | Text-overlap: gộp box cùng dòng OCR thành 1 cụm trước khi so chồng (`ocr.cluster_same_line_boxes`) + bỏ qua cặp trùng (box nhỏ ≥90% nằm trong box lớn + cùng baseline). Guard chuỗi con là SAI. | Mock N1: cặp box thật CI-T5 ("Xem" 432,927,482,986 vs "ngay" 400,929,590,984, chồng 93%) -> 0 cặp; frame step_010 thật -> 0 finding "Xem"; chữ đè thật khác baseline vẫn tố. Replay sau sửa giữ 8/8 P0. |
| 2 | Vision check hero/title: giữ frame CUỐI thay vì frame đầu (frame WebPlayer đầu lúc loading có thể chưa hiện lỗi đè đôi — nghi vấn chính cho cú bỏ sót CI-T5); prompt hỏi rõ "có đúng 2 DÒNG TIÊU ĐỀ CHỒNG LÊN NHAU không" + ép đọc nguyên văn vào trường `quote` trong `check_visual`; log rõ mỗi call (frame path + timestamp + crop) vào `vision_check_log` + report `vision_checks`. | Kiểm chứng live nemotron trên step_063 thật: prompt cũ -> found=True HIGH (13.7s); prompt mới -> found=True HIGH (19.3s), quote đủ cả 2 dòng. Mock N2: câu hỏi chứa "2 DÒNG TIÊU ĐỀ"+"CHỒNG LÊN NHAU", soi đúng bytes step_063, finding HIGH kèm frame, log đủ frame/t/crop, frame cuối thắng frame đầu. |
| 3 | Video chunk cuối: chờ finalize tới khi ffprobe THẤY moov (`video_recorder._wait_chunk_finalized_moov`: size ổn định rồi pull thử + probe, chưa có moov thì pull lại tối đa 5 lần; timeout mặc định 20s -> 60s). Reel: kẹp entry có video_t vượt độ dài tour về 6s cuối tour (`clamped`, `covered=False`) + báo rõ "reel cover x/y finding" trong report + HTML. | Mock B8 vẫn PASS (chunk cuối finalize sau 1.5s + pull đầu cắt ngắn -> đủ ~9s; không finalize -> giữ chunk đầu ~5s, không treo); N3: lần 1 chưa moov -> pull lại, lần 2 có moov -> True; không moov -> False sau 5 lần, không treo. Test G: entry 5.0s vượt tour 3.2s -> clamped, seg_start 0.0. |
| 4 | Sửa spec: SPORTS_MULTI_SOURCE `required_texts ["socolive"]` -> `["cola"]` ('socolive' không tồn tại dạng text trên màn — chỉ có nhãn 'COLA'/'SOCO' + 'BLV [ColaTV]'); IPTV_CATEGORIES `["tv360"]` -> `["kênh"]` ('tv360' chỉ tồn tại dạng ẢNH logo + chip bị cắt còn 'T'; header hàng 'Địa Phương — 66 kênh' là tín hiệu kiểm chứng được). | Gate: 'COLA'/'66 kênh' khớp mục tiêu mới, 'Socolive' đơn độc không khớp 'cola'. Quét timeline replay cũ: 'cola'/'kênh' không có trong focused_text -> cả 2 mission vẫn UNVERIFIED như trước, P0 recall không đổi. Mock Test L vẫn FAIL đúng như thiết kế (mock dump không có text đó). |
| 5 | Luật LIVE-only mở rộng cho MỌI mission (trước đây chỉ mission cần player/dialog): thẻ [SẮP ĐÁ] không được mở player ở bất kỳ mission nào — trận INTERF 19:00 ở ROOM_PICKER step_013/014 CI-T5 đã vào player loading vô hạn + tiêu đề 'null · VIE - CHI'. Củng cố `_focused_card_status`: (1) bounds giao nhau / tâm trong bounds focus mở rộng 40px; (2) cửa sổ ±10 node quanh node focus, tìm theo id rồi theo focused_text; (3) text của chính view focus. | Mock N4: hình CI-T5 ROOM_PICKER (không bounds, fid lệch, chỉ tìm được qua focused_text) -> `skip_upcoming_card`; mission SCHEDULE_EPG (không cần player/dialog) cũng skip. Mock cũ B3 vẫn PASS (thẻ LIVE mở bình thường, 'socolive' không bị nhận nhầm LIVE). |
| 6 | PLAYER_STREAMING: luật goto-player `_goto_live_card_action` (trước luật open_player): tìm thẻ có badge LIVE, đi theo hướng tới nó bằng DPAD (thẻ = node nhỏ nhất chứa tâm badge, ưu tiên id thẻ quen thuộc); đã đứng trên thẻ LIVE / không có thẻ LIVE thì hành vi cũ. Áp cho mission cần player hoặc cần dialog, không phải directed launch. | Mock N4b: focus ở nav, thẻ LIVE ở dưới -> `goto_live_card` DPAD_DOWN; đã đứng trên thẻ LIVE -> OK `open_player`; không có thẻ LIVE -> OK cũ. |
| 7 | Focus-trap chỉ tính quan sát KHÁC NHAU: runner băm sha256 frame mỗi `_observe`, detector bỏ qua (không append hist) khi hash trùng quan sát trước; không tố khi bàn phím ảo đang mở (≥8 text 1 ký tự chữ cái trong dump — đang gõ, focus đứng yên là đúng). Không lưu shot khi frame trùng quan sát trước và không có defect mới (timeline ghi `duplicate_frame`). | Mock N5: cùng frame 3× + DPAD_DOWN -> không tố, hist 1 entry; 3 frame khác nhau cùng sig + cùng hướng -> 1 finding MEDIUM; bàn phím mở -> không tố; `_observe` cùng PNG 2 lần -> lần 2 `duplicate_frame` True + `frame_file` None, PNG khác -> lưu shot bình thường. |
| 8 | Mọi mission player PASS phải có bằng chứng thời gian phát TĂNG giữa 2 quan sát: gate thêm `observe_playback` / `playback_status` (increasing ≥1s / frozen / unknown); `needs_playback_progress` chỉ bật cho 2 mission VOD (VOD_PLAYER_SEEK, WEBPLAYER_DIRECTED) — live stream (PLAYER_STREAMING, IPTV_EPG) không có elapsed clock có nghĩa nên ép ở đó sẽ FAIL oan; frozen -> missing `playback: ...` -> FAIL ở max_steps; unknown KHÔNG chặn PASS (giới hạn đo đã ghi rõ). Runner trích elapsed: ưu tiên dump 'elapsed / total' (lấy số nhỏ hơn), fallback min token thời gian trong cache OCR band dưới (đòi ≥2 token, 1 token lẻ -> None). Replay đọc `playback_s` từ timeline + downgrade playback-missing -> UNVERIFIED. | Mock N6: đóng băng 00:20 x10 -> FAIL ('playback: thời gian phát đứng yên 00:20 qua 10 quan sát'); tăng 20->65 -> PASS; unknown -> PASS; trích xuất dump '00:20 / 01:05:24' -> 20; OCR 2 token -> 20, 1 token -> None. Replay (đang chạy lại cuối vòng): timeline cũ không có playback_s -> unknown, không đổi recall. |
| 9 | Timeline thiếu step_id 14 — NGUYÊN NHÂN (đã tìm ra, không phải lỗ ghi log bí ẩn): trong `run_mission`, `_global_step += 1` ở đầu vòng lặp nhưng check force-fail `last_action_rule == "open_dialog"` (mở PLAYER thay vì dialog) `break` TRƯỚC `timeline.append`, nên bước quan sát PlayerActivity (step 14, ROOM_PICKER) không bao giờ được ghi, trong khi `timings.steps=79` và step sau tiếp tục từ 15. SỬA: dời check force-fail xuống SAU `timeline.append` (bước FAIL vẫn là 1 observation thật, phải có mặt trong timeline). | Mock N7 (mở rộng B9 ROOM_PICKER): timeline step_ids [1, 2] liên tục, step cuối == `_global_step`, entry cuối ghi đúng PlayerActivity. Với code cũ, entry cuối sẽ là MainActivity và step cuối vắng mặt -> test rớt. |
| 10 | (a) Audit `video_recorder.py` (dùng chung với harness cũ): thay đổi CI-T5 mục 8 (`5ee1df6`) + F67c (`c2b7bf6`) + CI-T6 mục 3 (`ce72f56`) đều CHỈ THÊM (attr `_current_remote`/`_finalize_timeout_s`, helper wait/pull-kiểm-byte, `_wait_chunk_finalized_moov`), KHÔNG đổi chữ ký `__init__(serial, out_dir, max_total_seconds)`, `start()`, `stop_and_save()` — 2 caller harness cũ (`autonomous_ai_qa.py`, `run_qa.py`) chỉ dùng 3 hàm này; 8 file harness cũ `py_compile` OK; mock B8 bao phủ `stop_and_save` (test `_dur` gốc §15.2 đã mất theo VM restart, B8 là bản kế nhiệm). KHÔNG sửa code video_recorder.py ở mục này. (b) Nhãn provider thật: `VisionClient` thêm `_detect_endpoint_host()` (provider ≠ endpoint khi chạy qua URL NIM-compatible) + `endpoint_host` trong `nim_stats()`; report thêm top-level `vision_provider` + `vision_endpoint_host`; dòng in cuối run + HTML + replay đổi từ 'NIM requests' sang 'Vision: <provider> qua <host> · requests ...'. Lưu ý: `nim_usage.provider` vốn đã đúng (CI-T5: OPENAI), chỉ nhãn hiển thị sai; số request đếm được là số gửi tới endpoint_host (limiter chỉ throttle host NIM — §8.1). | Mock N8: monkeypatch OPENAI_BASE=https://integrate.api.nvidia.com/... + OPENAI_KEY -> provider OPENAI, endpoint_host integrate.api.nvidia.com, nim_stats đủ cả 2 trường; render HTML mẫu chứa 'Vision: OPENAI qua integrate.api.nvidia.com' và không còn 'NIM requests:'. |

### 15.9. CI-T6 eye-review (run 43027661716) — tóm tắt, chi tiết ở qa-run-43027661716/VISUAL-REVIEW.md

- **Verdict PASS lần đầu (79/100, 14/17, 0 false pass theo luật gate, QA
  887s).** 5 vision calls, provider OPENAI, 0×429. Mock 33/33 + replay R7
  8/8 P0 (tự chạy lại, report đã lưu ở qa-run-43027661716/
  replay_R7_report.json — NIM hết chập chờn).
- **Sửa CI-T6 đều được kiểm bằng mắt (28/28 shot + 9 frame video):** mục 1
  hết FP "Xem ngay"; mục 2 vision check bắt được HIGH thật (tiêu đề
  WebPlayer đè đôi, step_059 — lỗi 3 vòng không bắt được); mục 4 spec
  'cola'/'kênh' khớp thực tế UI; mục 9 step_id liên tục 1–72; mục 10
  provider ghi đúng OPENAI.
- **Nhưng 3 mục chưa chạy live, đã rõ cơ chế sau review độc lập:** mục 6
  goto-player **CHẠY 4 lần nhưng sai trạng thái** (rule 0c2 không kiểm
  `has_dialog`, đuổi theo badge LIVE ở list nền sau overlay thay vì bấm
  OK trên phòng đang focus — bản đầu ghi "không kích hoạt" là sai); mục 8
  `playback_readings: []`, `playback_status: "unknown"` ở mọi mission
  player — band dưới **chưa từng được OCR**: dump WebView không có text →
  `osd_visible=False` → cả 3 detector đọc band dưới đều skip khi `osd is
  False` (`detectors.py:536/582`) → `_extract_playback_s` luôn None
  (không phải "OCR không trích được '00:20'"); mục 3 video vẫn 79% (4
  chunk — moov-wait 60s **đã chạy và thất bại**, writer không finalize;
  `_wait_for_screenrecord_exit()` trả về bị bỏ qua).
- **Findings 1 thật / 1 giả:** HIGH đè đôi tiêu đề THẬT; MEDIUM focus trap
  GIẢ (bàn phím đang mở — highlight phím đổi **⇧ (step_066) → 'z'
  (step_067) → 'q' → '▶'** — bản đầu ghi nhầm "'z' (step_066/067)"; guard
  đếm ký tự trong dump không có gì để đếm vì `ui_state` chỉ có 5 trường
  focused; mock N5(c) truyền `keyboard_open=True` bằng tay nên không
  chứng minh được hành vi live).
- **3 PASS mềm:** EPISODE_PICKER (frame step_051 không thấy dialog dù dump
  ghi "Tập 1" — lệch screenshot/dump); IPTV_EPG (frame chỉ thấy list);
  WEBPLAYER_DIRECTED — **yếu nhất: không có bằng chứng phát nào; thời gian
  KHÔNG tăng đơn điệu (00:20 → 00:00 → 00:30 → 00:20, khớp seek test) và
  step_055 = step_059 pixel-identical (cùng 1 frame đóng băng 60,3s)** —
  bản đầu ghi "tăng bằng mắt 00:00→00:20→00:30" là sai thứ tự và sai bản
  chất. PASS này chứng minh OSD + tua + tốc độ, chưa chứng minh "phát
  thật".
- **FAIL trung thực:** ROOM_PICKER (dialog đã mở step 10 nhưng driver bấm
  tiếp vào player — gốc rễ: id của MatchDetailPanel
  (`panelBlvList`, `panelSameTimeList`, `panelPlay`, `panelScore`…) không
  có trong `dialog_id_set` (`device.py:203-205`) → `has_dialog=False` suốt
  lúc panel mở; cái mở ra là match-detail panel, không phải RoomPickerDialog
  độc lập; kèm app bug loading vô hạn + spinner đè nút ▶ PHÁT ở step_012);
  PLAYER_STREAMING (A-B-A-B — luật chạy sai trạng thái, xem trên);
  NAV_RAIL (rail không mở — lỗi app).
- **Sót lỗi thật:** Schedule hàng LIVE hiện giờ kickoff thay vì tỉ số
  (18:30/18:35, còn từ T3); player native loading vô hạn + spinner đè nút;
  hàng 66 kênh không được kiểm (driver không tới); detail trận LIVE "VS"
  không tỉ số; **MỚI: nút "ÂM THANH & PHỤ ĐỀ" bị cắt mép phải khi focus ở
  player native (step_061/063, tour_160/165)**.
- **Kết luận: CHƯA SWITCH — NEEDS-CI-T7.** Tiêu chí 0 HIGH FP ✅ LẦN ĐẦU,
  nhưng eye check khớp report + reel (1/2) + video (79%) chưa đạt. Danh
  sách sửa CI-T7 (10 mục, xem VISUAL-REVIEW.md §9): (1) focus-trap +
  keyboard theo ảnh/pixel (guard dump không thấy IME; mock N5(c) phải
  dựng từ dump không có node bàn phím); (2) nối `playback_readings` vào
  nguồn thật (OCR band dưới từ ảnh/OSD pixel, không dựa `osd_visible` từ
  dump; hoặc parse từ quote vision "00:20 / 01:05:24"; gate "unknown sau
  ≥2 observation" thành UNVERIFIED); (3) nhận diện dialog: thêm id của
  MatchDetailPanel vào `dialog_id_set` (gỡ cả ROOM_PICKER lẫn
  PLAYER_STREAMING); (4) driver: cấm `goto_live_card` khi dialog/panel
  đang mở (gate rule 0c2 bằng `not has_dialog`); (5) video chunk cuối:
  xác minh process screenrecord đã chết (`pidof`) trước khi chờ moov; dừng
  quay trước giai đoạn post-processing dài để chunk cuối kết thúc bằng
  expiry 175s tự nhiên; (6) shot trùng: áp check duplicate cả ở
  `_finish_mission` (đường bypass hiện tại — 046=047, 026=037 identical);
  (7) screenshot/dump đồng bộ (chụp sau khi dump ổn định); (8) IPTV_EPG
  cần vision_confirm EPG text trong frame; (9) Schedule live-score check
  (hàng Live chỉ hiện giờ kickoff thì tố); (10) App (ghi cho fix loop):
  WebPlayer đè đôi tiêu đề; spinner đè nút + loading vô hạn; Schedule
  giờ-thay-tỉ-số; hàng 66 kênh; rail không mở; detail LIVE "VS" không tỉ
  số; **nút "ÂM THANH & PHỤ ĐỀ" bị cắt mép phải khi focus**.

### 15.10. CI-T7 — danh sách sửa (9 mục harness + mục 10 app chỉ ghi, VISUAL-REVIEW.md §9)

Bảng này ghi từng mục CI-T7 khi xong (1 mục = 1 commit trên main, Build APK
xanh từng commit, mock + replay giữ nguyên). Mock baseline trước CI-T7: 33/33.
Replay baseline trước CI-T7 (R7, run 43027661716): 8/8 P0, 0 false pass.
Baseline R8 (chạy lại bởi coordinator trên code gồm mục 1+2, artifact
run-42950738729): có vision 6/8 P0 (thiếu P0-3, P0-7 do lỗi transport vision),
0 false pass — dùng 6/8 làm baseline của vòng này, xem kết quả cuối vòng ở
§15.12.

| Mục | Sửa | Kiểm chứng |
|---|---|---|
| 1 | Nhận diện dialog: thêm 13 id của MatchDetailPanel (`panelLeague`, `panelBadge`, `panelHostName`, `panelHostIcon`, `panelScore`, `panelClock`, `panelGuestIcon`, `panelGuestName`, `panelBlvTitle`, `panelBlvList`, `panelSameTimeTitle`, `panelSameTimeList`, `panelPlay` — grep layout `dialog_match_detail.xml`, chỉ đọc) vào `dialog_id_set` (`device.py`); ngoài ra coi mọi id bắt đầu bằng `"panel"` hoặc `"blvCardRoot"` (card phòng trong panel, focus lúc panel mở — step_011 CI-T6) là dialog đang mở. An toàn: không id layout nào khác bắt đầu bằng `"panel"` (`channelCarouselPanel`/`sportOptionsPanel` đều kết thúc bằng `"Panel"`). | Mock N9 (XML dump thật): panel mở (`panelBlvList` + `blvCardRoot` focus) -> `has_dialog` True, `dialog_ids` đủ panel; `panelScore` đơn độc -> True; dialog cũ (`dialogTitle`/`btnCloseFeedback`) vẫn True; màn thường có `channelCarouselPanel` -> False. Mock 34/34 PASS. |
| 2 | Driver: cấm `goto_live_card` khi dialog/panel đang mở — gate rule 0c2 bằng `not has_dialog` (+ guard trong chính `_goto_live_card_action`, trả None khi `has_dialog`) và panel không bị dismiss bằng BACK khi mission cần player (đường vào player là OK trên phòng đang focus). | Mock N10: panel mở + badge LIVE sau overlay -> `KEY OK` rule `open_player`; `_goto_live_card_action` trực tiếp trả None khi `has_dialog`; panel đóng -> `goto_live_card` `DPAD_DOWN`; rule driver ghi vào timeline (COLD_START: 2 bước đầu `explore:down`). Mock 35/35 PASS, EXIT=0 (kiểm chứng bởi coordinator, không làm lại). |
| 3 | Focus-trap + keyboard theo ẢNH/pixel, không theo dump (`detectors.detect_keyboard_from_image` + `detect_focus_trap(..., frame_png)`): bàn phím QWERTY in-app không có node nào trong dump nên guard đếm ký tự trong dump mù. Chữ ký pixel: ≥3 dải ngang dày đặc pixel 'xám phím' (độ sáng 40–70) ở nửa dưới màn hình, cao 20–45px (theo H/540), cách đều nhau (tỉ lệ khoảng cách max/min ≤ 1.5) = 4 hàng phím QWERTY. Chỉ downscale tối đa về 960 rộng (về 480 làm mờ phím, mất tín hiệu — đã kiểm). Check ảnh chỉ chạy lazy khi sắp tố kẹt; kết quả cache theo frame_hash, ghi `keyboard_open_image` vào obs + timeline. | Mock N11: ảnh bàn phím tổng hợp (4 hàng phím xám) -> True; ảnh thường -> False; frame THẬT CI-T6: 066/067/071 (có bàn phím) -> True, 011/026/051/055 (không) -> False; dump KHÔNG có node phím + ảnh bàn phím, 3 quan sát khác nhau cùng sig + DPAD_DOWN -> KHÔNG tố, `keyboard_open_image` True; cùng dump + ảnh thường -> tố 1 MEDIUM như cũ. Kiểm trên 29 frame CI-T6: 3/3 bắt, 0 FP. Mock 37/37 PASS, EXIT=0. |
| 4 | `playback_readings` nối vào nguồn thật (`runner._extract_playback_s` + `gate.playback_monotonic` + quote vision): gốc rễ CI-T6 là dump WebView không có text -> `osd_visible=False` -> detector band dưới skip -> cache OCR trống -> luôn None. Sửa: cache trống thì OCR ÉP band dưới TRỰC TIẾP TỪ ẢNH (không qua `osd_visible`), ghi vào cache để detector dùng chung; parse thêm cặp 'elapsed / total' từ quote vision (`_playback_seconds_from_text`, dùng chung cho dump + quote). Gate: `unknown` sau ≥2 quan sát thành missing (không PASS tự do — live FAIL ở max_steps, replay downgrade UNVERIFIED); thêm kiểm tra tăng đơn điệu (lùi > 2s giữa 2 lần đọc liên tiếp -> missing), miễn lùi ngay sau tua NGƯỢC (`gate.note_seek`, chỉ DPAD_LEFT/REWIND trong player — tua TỚI DPAD_RIGHT không miễn). | Mock N6 (cập nhật luật): đóng băng 00:20 x10 -> FAIL; tăng 20->65 -> PASS; unknown x10 -> FAIL (luật mới, CI-T6 cũ cho PASS); dãy mắt đọc CI-T6 20->0->30->20 -> `playback_monotonic` False -> FAIL (status cũ `increasing` vì max-min=35s là lỗ hổng); tăng đơn điệu thật vẫn PASS; lùi ngay sau tua ngược được miễn; nhiễu OCR lùi ≤ 2s không tố. Mock N12: ảnh PIL vẽ '00:20' + '24:14' ở band dưới, dump rỗng + `osd_visible` False -> trích được 20, OCR ép ghi vào cache; ảnh đen -> None (không bịa); parse quote '00:20 / 01:05:24' -> 20, quote không có cặp giờ -> None. Mock 36/36 PASS, EXIT=0 (sau mục này). |
| 5 | Video chunk cuối (`video_recorder.py` — KHÔNG đổi chữ ký `__init__`/`start()`/`stop_and_save()`; thêm attr/method mới + sửa logic trong thân hàm `_record_loop`/`stop_and_save()` (vòng retry SIGINT, nhánh graceful), giữ kỷ luật dùng chung với harness cũ): (a) `request_graceful_stop()` — xin dừng mềm, worker để chunk hiện tại hết hạn 175s tự nhiên (moov đầy đủ) thay vì SIGINT cắt giữa chừng; runner gọi TRƯỚC giai đoạn post-processing dài (vision check cuối run), `stop_and_save()` join sau; quá hạn (175s+10s) thì SIGINT fallback. (b) Xác minh process screenrecord đã chết thật bằng `pidof` TRƯỚC khi chờ moov (`stop_and_save` + retry SIGINT tối đa 3 lần trong `_record_loop`, kết quả ghi vào `screenrecord_exited` + dict trả về + report `video_screenrecord_exited`). (c) Runner `run()`: `request_graceful_stop()` trước `_vision_overlap_checks()`, `stop_and_save()` sau. | Mock N13: (a) worker dừng mềm — chunk tự thoát (poll -> 0) thì 0 lệnh SIGINT/pkill, thread thoát, `screenrecord_exited` True; (b) `stop_and_save` dừng mềm với chunk thật 5s -> recorded 5.0s, `screenrecord_exited` True, `graceful_stop` True; (c) pidof vẫn thấy process -> `screenrecord_exited` False, xong trong 7.7s (< 20s, không treo). Mock B8 cũ (chunk cuối finalize sau 1.5s + pull cắt ngắn -> ~9s, 2 chunk; chunk hỏng -> giữ chunk đầu ~5s) và N3 (moov wait) vẫn PASS. Mock 39/39 PASS, EXIT=0 (sau mục này). Kiểm chứng live (phủ video > 95% + reel cover 2/2) còn lại cho trial trực tiếp — offline không có emulator. |
| 6 | Dedup shot trùng (`runner._save_frame` + `_finish_mission`): `_save_frame` dedup theo sha256 PNG (cùng ảnh -> trả lại path đã lưu, không ghi trùng) cho cả `_observe` lẫn `_finish_mission` và giữa các mission; `_finish_mission` ghi rõ `evidence_frame_duplicate_of` khi frame cuối trùng shot đã lưu. | Mock N14: lưu cùng PNG 2 lần -> cùng 1 path; ảnh khác -> file riêng; chạy thật 2 mission COLD_START với device trả cùng 1 frame -> shots chỉ có 1 file (`step_004_cold_sta.jpg`), mission 2 ghi `evidence_frame_duplicate_of` đúng file đó, cả 2 vẫn PASS. Mock 40/40 PASS, EXIT=0 (sau mục này). Lưu ý test: dọn sạch out_dir trước khi chạy (file sót từ lần chạy trước làm mission 1 bỏ qua lưu vì file đã tồn tại, hash không được ghi). |
| 7 | Đồng bộ screenshot/dump (`runner._observe`): dump TRƯỚC, chụp SAU (wait_stable), rồi dump kiểm chứng — (activity, focused_sig, has_dialog) phải giống dump đầu; lệch thì chụp lại (timeout 3s) + dump lại 1 lần, dùng bộ sau. Số lần retry ghi vào `timings.sync_retries` + report. Tốn thêm 1 lần dump/bước (~1-3s) nhưng screenshot và dump phải là cùng 1 trạng thái thì bằng chứng mới khớp. | Mock N15: device scripted — dump 1: màn thường, dump 2+: dialog 'Tập 1' mở -> observation ghi đúng dialog (`has_dialog` True, focused 'Tập 1'), retry đúng 1 lần, 3 lần dump; dump tĩnh -> 0 retry, không chụp lại. Mock 41/41 PASS, EXIT=0 (sau mục này). |
| 8 | IPTV_EPG cần vision_confirm EPG text trong frame (`missions.py`: `MISSION_IPTV_EPG_AND_ZAPPING_PLAYER` thêm `needs_vision=True`, `target_desc` yêu cầu thấy tên kênh + thông tin EPG/lịch phát sóng của chương trình đang phát). Không PASS cứng khi chỉ thấy list. | Mock N16: spec `needs_vision` True, `target_desc` chứa 'EPG' + 'tên kênh'; gate đủ tín hiệu rẻ (PlayerActivity + motion, 4 bước) mà chưa vision -> `VISION_PENDING` (không PASS); vision xác nhận kèm quote EPG thì PASS. Mock 42/42 PASS, EXIT=0 (sau mục này). |
| 9 | Detector điểm số trực tiếp ở Schedule (`detectors.detect_schedule_live_no_score`, chạy mọi observation, chỉ dump — không OCR): gom node theo HÀNG (tâm dọc bounds ±60px); hàng có badge LIVE + token giờ kickoff 'HH:MM' (không khoảng trắng — tỉ số app render dạng 'X : Y' có khoảng trắng) mà KHÔNG có token tỉ số -> tố HIGH (cần thấy 2 lần quan sát). Hàng 'SẮP ĐÁ' hiện giờ kickoff là đúng nên loại; chỉ chạy khi dump có ngữ cảnh lịch (id chứa 'sched'). | Mock N17: hàng LIVE 18:30 -> lần 1 ghi nhận, lần 2 tố 1 HIGH đúng '18:30'; hàng LIVE đã có tỉ số '2 : 1' không tố; hàng SẮP ĐÁ 19:00 không tố; lần 3 không tố trùng; màn không có id 'sched' không chạy. Mock 43/43 PASS, EXIT=0 (sau mục này). |
| 10 | App (CHỈ GHI vào DESIGN.md §15.11, không sửa code app). | §15.11: 7 lỗi app đã phát hiện qua các vòng (từ §15.9 + VISUAL-REVIEW.md §9), ghi cho fix loop sau. |

### 15.11. CI-T7 — lỗi app ghi cho fix loop (CHỈ GHI, không sửa code app)

Danh sách này là đầu vào cho fix loop sau, không phải sửa của vòng QA này.
Nguồn: §15.9 + VISUAL-REVIEW.md §9 (run 43027661716) và các vòng trước.

| # | Lỗi app | Bằng chứng |
|---|---|---|
| A1 | WebPlayer đè đôi tiêu đề (2 dòng tiêu đề chồng lên nhau, chữ chen nhau không đọc được) | Vision xác nhận HIGH ở step_059 CI-T6 (mục 2 CI-T6 bắt được lần đầu); lỗi tồn tại từ CI-T3+, vision check cuối run soi đúng frame cuối WebPlayer |
| A2 | Spinner loading đè nút ▶ PHÁT + loading vô hạn ở player native | Step_012 CI-T6 (ROOM_PICKER): mở player từ thẻ trận [SẮP ĐÁ] vào trạng thái 'Đang tải luồng...' vô hạn, spinner đè lên nút phát; cùng gốc với CI-T5 step_013/014 |
| A3 | Schedule: hàng LIVE hiện giờ kickoff thay vì tỉ số | Hàng LIVE hiện '18:30'/'18:35' (giờ đá) thay vì tỉ số đang diễn ra; còn từ CI-T3, mắt thấy lại ở step_030 CI-T6; nay có detector riêng (CI-T7 mục 9) để tố tự động |
| A4 | Hàng chứa quá nhiều kênh, vượt giới hạn 30 kênh/hàng (không duyệt nổi) — 2 quan sát riêng: (a) hàng "Địa Phương — 66 kênh" (CI-T3, finding thật; còn nguyên ở CI-T6, driver không tới để kiểm); (b) P0-7: 1 hàng TV360 chứa 75 kênh (run 42950738729, step_057) | Detector `row_overflow` tố khi ≥ 30 kênh/hàng |
| A5 | Rail sidebar không mở (DPAD_LEFT không mở được thanh điều hướng) | Mission NAV_RAIL FAIL ở CI-T6 (rail không mở — lỗi app, không phải driver) |
| A6 | Detail trận LIVE hiện "VS" thay vì tỉ số | Trận đang diễn ra nhưng panel chi tiết chỉ hiện 'VS', không có tỉ số (mắt thấy CI-T6); luật plausibility vẫn áp (tỉ số phi lý -> 'VS', không bịa) — lỗi ở đây là thiếu dữ liệu tỉ số thật, phải sửa plumbing dữ liệu, không được giấu bằng 'VS' |
| A7 | Nút "ÂM THANH & PHỤ ĐỀ" bị cắt ở mép phải khi focus (player native) | MỚI ở CI-T6: step_061/063, tour_160/165 — nút bị cắt cụt khi focus, chữ chạm mép phải |

### 15.12. Kết quả cuối vòng CI-T7 (offline — mock + replay, 2026-11-11)

- **Mock cuối vòng: 43/43 PASS, EXIT=0** (`python3 mock_test.py`, ~120s). Baseline
  trước CI-T7: 33/33; + N9/N10 (mục 1+2) = 35; + N11..N17 (mục 3–9) = 43.
- **Replay cuối vòng trên artifact run-42950738729** (code CI-T7 đầy đủ 9 mục):
  - Có vision (`/tmp/qa_replay_R8_final/replay_report.json`, file mới nhất
    22:13, 216.4s): **P0 recall 7/8** (bắt P0-1, P0-2, P0-4, P0-5, P0-6,
    P0-7, P0-8; chỉ thiếu P0-3), **0 false pass**, 7 vision calls (provider
    OPENAI qua integrate.api.nvidia.com), 11 requests, 0×429, mission 2 PASS
    / 3 FAIL / 11 UNVERIFIED, score 0/100. (Lần chạy trước của cùng file này:
    288.7s, 6/8 — thiếu thêm P0-7 do lỗi transport, score 2, 2/4/11, 13
    requests; file bị ghi đè bởi lần chạy cuối nên bảng này lấy số lần cuối.
    P0-7 bắt được ở lần cuối nhờ vision trên step_057.)
  - Không vision (`/tmp/qa_replay_R8_final_novision/replay_report.json`, 3.4s):
    **P0 recall 5/8** (thiếu thêm P0-8), 0 false pass, 0 vision call,
    mission 1 PASS / 3 FAIL / 13 UNVERIFIED, score 12/100.
- **So với baseline R8 trước code CI-T7** (coordinator chạy, code gồm mục 1+2):
  có vision 6/8 P0 (thiếu P0-3, P0-7), 0 false pass, 6 vision calls, 304.9s,
  14 requests, 0×429, mission 2/4/11, score 2; không vision 5/8. **Mục tiêu
  "giữ hoặc vượt 6/8" VƯỢT: P0 recall lần cuối 7/8 (baseline 6/8), bản không
  vision giữ 5/8 ở cả hai lần.**
- **Trung thực về 2 flip mission giữa 2 lần chạy (đều do vision, không phải
  code):** (a) PLAYER_STREAMING FAIL -> PASS — lần này vision-confirm trên
  frame cuối trả confirmed (lần trước không); (b) IPTV_EPG PASS -> FAIL —
  call vision-confirm MỚI của mục 8 trúng lỗi transport `Connection reset by
  peer` (giống hệt P0-3/P0-7 ở cả 2 lần chạy), report ghi `vision lỗi:
  error:[Errno 104] Connection reset by peer` ở frame step_071 — đây là lỗi
  hạ tầng, KHÔNG phải vision chối và KHÔNG phải lỗi app; lần chạy tới có thể
  flip lại. Tổng vision calls 7 (baseline 6) — đúng +1 call của mục 8.
- **P0-3 vẫn thiếu ở lần chạy cuối vì lỗi transport:** vision
  check_visual lỗi (`Connection reset by peer`), không phải detector
  hay code mới — NIM qua surrogate chập chờn theo thời điểm (đã ghi ở §15.10
  phần đầu). P0-7 (thiếu ở lần chạy trước vì cùng lỗi đó) đã bắt được ở lần
  cuối bằng vision trên step_057. Không có P0 nào bị mất do code CI-T7 (P0-4/P0-5 vẫn bắt bằng
  OCR, P0-1/P0-2/P0-6 bằng gate/detector, P0-8 bằng vision).
- **Còn lại cho trial trực tiếp (cần secret AI brain + live run, không làm
  offline được):** CI-T7 live trial — kiểm chứng (a) video phủ > 95% + reel
  cover 2/2 (mục 5: dừng mềm + pidof); (b) playback_readings đọc được từ
  ảnh thật trên WebPlayer + đơn điệu (mục 4); (c) focus-trap không còn tố oan
  khi bàn phím mở (mục 3); (d) IPTV_EPG vision-confirm EPG text thật (mục 8);
  (e) Schedule detector tố hàng LIVE thiếu tỉ số trên màn thật (mục 9);
  (f) số liệu tốc độ run (< 30 phút) + số vision call thực tế. Repo QA chưa
  có secret AI brain (NVIDIA_API_KEY / GEMINI_API_KEY / METEOR_API_KEY) nên
  preflight sẽ fail — KHÔNG dispatch trial trong vòng này.

### 15.13. CI-T7 LIVE TRIAL — eye-review (run 43083708112, 2026-11-12)

Trial trực tiếp đầu tiên của code CI-T7 (head d0c1c71 — đã sửa đường dẫn APK
sau fail sớm của run 43082620123). Workflow SUCCESS, job `qa` 40m14s.
Artifact `qa-report-realtime` 9 MB, 29 ảnh. Chi tiết mắt kiểm:
`~/workspace/kenhlive-plan/qa-run-43083708112/VISUAL-REVIEW.md` (+ thư mục
`eye/` chứa crop phóng to, khung tour, khung reel).
**Verdict: NEEDS-CI-T8 — KHÔNG switch.**

- **Số thật:** score **68**, QA **2057s (34m17s)**, **81 bước**, **10/17 PASS**,
  verdict **NEEDS_FIX**. Vision **11 call** (stuck_assist 6, confirm_target 3,
  check_visual 2), provider **OPENAI** qua integrate.api.nvidia.com,
  **23 request, 0×429**, limit 30/phút, vision latency trung bình **57,9s**/call,
  observe 721,8s, vision 637,2s, per-step p50 5,38s / p95 21,95s / mean 9,61s,
  sync_retries 0. Lưu ý (reviewer độc lập phát hiện, đã tính lại từ `observe_s`):
  p95 21,95 / mean 9,61 không khớp session (tính lại p95 = 20,01, mean = 8,91;
  p50 = 5,38 khớp) — 2 số này hoặc sai hoặc đo theo định nghĩa khác không ghi
  trong file. (Tên file step_NNN = step_id NNN−1: step_014 = step_id 13,
  step_057 = step_id 56.)
  sync_retries 0. Video ghi **1691,0s** / 2057s = **82,2%**, tour 360,07s @ 4,7×,
  graceful_stop true. Reel 12,17s, 2 entries, report tự tính covered 2/2.
  Findings **2 HIGH**. Vision lỗi **3 call** (1 timeout + 2× HTTP 503).
- **PASS (10):** COLD_START, ROOM_PICKER, DATA_ACCURACY, HOME_BILLBOARD_6_ROWS,
  SCHEDULE_EPG, IPTV_CATEGORIES, PHIM_NGUONC, EPISODE_PICKER,
  PLAYER_SETTINGS_DIALOG, SEARCH_AND_SETTINGS.
  **FAIL (7):** SPORTS_MULTI_SOURCE (A-B-A-B), PLAYER_STREAMING (A-B-A-B),
  SIDEBAR_RAIL (thiếu railPanel), IPTV_EPG (vision 2× deny), VOD_PLAYER (kẹt),
  WEBPLAYER_DIRECTED (kẹt), STRESS (kẹt).
- **Mắt kiểm PASS:** 8 PASS thật; **2 PASS mềm** — HOME_BILLBOARD (khung step_025
  không có billboard, vision hero 503, PASS dựa dump text) và EPISODE_PICKER
  (dialog có mở thật — dump tvEpisodeName + tour chớp dialog ở 292,55s — nhưng
  khung bằng chứng step_051 KHÔNG thấy dialog).
- **Mắt kiểm FAIL:** 6 FAIL thật về hành vi app; **STRESS FAIL là lỗi harness**
  (bàn phím mở, highlight di chuyển a → z → ▶, app không crash — dump không đổi
  nên detector "kẹt" nổ oan).
- **Finding #1 (HIGH) "Mất focus trong player khi OSD đang hiện" — LỖI GIẢ.**
  Crop phóng to 3× step_056/057: viền **vàng** bao nút tua lùi 10s (056) rồi
  chuyển sang nút play (057) — focus CÓ trên ảnh và DI CHUYỂN được. Dump báo
  NONE chỉ vì WebView không lộ focus ra uiautomator; session cũng ghi
  `has_focus_ring=false, ring_color=UNKNOWN` ở bước 56–59/66–69 (detector vòng
  focus của harness không thấy viền vàng). Harness tin dump hơn tin ảnh.
  **Tiêu chí "0 lỗi HIGH giả": FAIL.**
- **Finding #2 (HIGH) focus rò xuống thẻ nền khi Dialog mở — THẬT.** Crop
  step_014: thẻ nền "JPN D2 · SOCO · ● LIVE · Albirex… vs Tokush… · VS" có
  viền trắng rõ ở cạnh phải trong lúc MatchDetailPanel mở.

**Kiểm chứng 6 mục live của §15.12:**
- (a) Video phủ >95% + reel 2/2 — **KHÔNG ĐẠT.** Phủ 82,2%. Reel: report tự
  tính 2/2, nhưng **theo nội dung mỗi đoạn chỉ ~25% đúng cảnh** — seg1
  (tour 40,2–46,2s) có ~1,5s đầu ĐÚNG cảnh panel rò focus (diff 0,25 so với
  step_014), còn lại là màn Lịch; seg2 (tour 248,4–254,4s) ~4,5s "Đang tải..."
  + ~1,5s cuối là OSD placeholder (00:00/00:00 + double title) nhưng không
  thấy rõ viền vàng ở độ phân giải tour → làm bằng chứng cho finding #1 vẫn
  FAIL. (Bản đầu ghi "0/2 theo nội dung" là nói quá — reviewer độc lập đo
  lại cả đoạn, đã kiểm lại bằng output-seek.)
  Nguyên nhân: `video_t = QA_t / 4,7` giả định tour đều 4,7×, nhưng timebase
  tour **không đều** — ranh giới cảnh lệch sớm ~10–17 tour-giây so với mapping
  naive (đo bằng 3 neo: Lịch, WebPlayer, Search). Dialog chọn tập xuất hiện
  **2 lần**: đúng vị trí tour ~203,75–204,75s (≥1s, lệch ~13 tour-giây, khớp
  drift chung) + flash lạc ~0,2s ở 292,55s (lệch ~76 tour-giây nếu tính riêng
  flash; có thể dialog chưa bao giờ đóng, chớp lại lúc chuyển activity
  WebPlayer → Player ở bước 69→70). Tour ~295s có toast "Mạng chập chờn — tự
  thử lại lần 2..." (reviewer ghi nhận — ủng hộ giả thuyết embed bị chặn khi
  không có proxy).
- (b) playback_readings từ ảnh + tăng đơn điệu — **CHƯA CHỨNG MINH ĐƯỢC.** OCR tốt
  (tesseract đọc "00:00 / 00:00" từ band dưới step_057; harness đọc đúng 0,0
  ở bước 51/60) nhưng readings chỉ là singleton `[[1046.2, 0.0]]`,
  `[[1246.1, 0.0]]` — đóng băng ở 0,0 vì video không bao giờ phát (placeholder
  xám + "Đang tải..." loop; 5 khung WebPlayer 056/057/060/066/070 mean diff
  0,01–0,14 (đủ 10 cặp, grayscale 160×90)). Không phải harness đọc sai — tiền
  đề (phát thật) không xảy ra.
- (c) Focus-trap không tố oan khi bàn phím mở — **ĐẠT HẸP, mong manh.** Không có
  finding trap nào; `keyboard_open_image=True` ở đúng 5 bước [77–81]. Nhưng
  dump `keyboard_open=False` ở **cả 81 bước** (dump mù với bàn phím), detector
  ảnh trượt bước 76 (None), và detector "kẹt" vẫn không hiểu điều hướng bàn
  phím (→ STRESS FAIL oan).
- (d) IPTV_EPG vision-confirm EPG text thật — **CHƯA CHỨNG MINH ĐƯỢC.** 1 call
  timeout (khung step_042 thiếu), 2 call deny; khung chỉ thấy lưới kênh.
  FAIL trung thực; item không đạt vì điều hướng thất bại.
- (e) Schedule detector tố hàng LIVE thiếu tỉ số — **KHÔNG KIỂM ĐƯỢC.**
  `'schedule_live'` xuất hiện 0 lần trong qa_session.json; các khung Lịch chỉ
  có hàng KẾT THÚC, không có hàng LIVE nào trong cả run.
- (f) Tốc độ + vision call — **TỐC ĐỘ FAIL (2057s > 30 phút)**, budget PASS
  (11 call, 23 request ≤ 40, 0×429).

**Lỗi app mới / còn tồn tại (mắt thấy, ghi cho fix loop sau — không sửa ở đây):**
- **A1 (cũ, HIGH) VẪN CÒN:** double title WebPlayer — 5 khung đều thấy "Hoàng
  Hậu Tái Hôn / Tập 01" (trắng, trái) + "Hoàng Hậu Tái Hôn (2026) · Tập 01"
  (xám, giữa). Vision player_title 503 nên harness bỏ lỡ.
- **A8 (MỚI):** trận đã kết thúc không hiện tỉ số chung cuộc (Hong Kong vs
  Cambodia, Albirex vs Tokushima, Fujieda vs Shonan — KẾT THÚC, chỉ có giờ đá).
  A6 (LIVE hiện "VS" không tỉ số) cũng còn: China U23 vs Uzbekistan U.
- **Ngày Lịch cũ (MỚI):** "Thứ Bảy, 03/10, 37 trận" trong khi run 12/11 (lệch
  ~40 ngày); đồng hồ launcher trong video đọc 7:10 — chưa rõ do đồng hồ
  emulator hay dữ liệu API cũ, cần kiểm riêng.
- **A7 (cũ, đã sửa cách diễn đạt sau review):** hàng nút OSD native TRÀN màn
  hình — nút thứ 6 bị cắt ở mép phải, một nút bị cắt ở mép trái; riêng nút
  "ÂM THANH & PHỤ ĐỀ" KHÔNG bị cắt (viền trắng đóng kín x=739–940/960, còn
  thừa 20px, glyph "Ề" đủ nét). **A5 (cũ):** rail không mở. Nhỏ: pill IPTV
  thứ 4 chỉ còn "T"; logo đội là vòng tròn xám placeholder.
- **Run này KHÔNG có proxy VN** (annotation: "Khong co proxy VN
  (YUNA_PROXY_YAML/YUNA_SUB_URL) — chay khong qua proxy") — embed có thể bị
  chặn geo khi không proxy; F63 chỉ kiểm được khi có proxy hoặc trên máy thật.

**Bằng chứng thiếu:** `step_035_sidebar_.jpg` (SIDEBAR_RAIL) và
`step_042_iptv_epg.jpg` (unverified IPTV_EPG) **không có trong shots/** (29
file); `step_051_phim_epi.jpg` có file nhưng không thấy dialog.
`findings[].evidence.video_t` ghi **thời gian QA** (1181.7 / 203.1), không phải
thời gian tour — tên trường gây nhầm với `defect_reel_entries[].video_t`
(43.2 / 251.4, thời gian tour).

**Đối chiếu switchover (§15):** QA <30 phút FAIL (2057s); 0 PASS giả — 0 tuyệt
đối nhưng 2 PASS mềm thiếu bằng chứng mắt; WebPlayer tới đích + vision thấy OSD
CHƯA (tới activity, OSD thấy bằng mắt, vision 503, phát không chạy); 0×429
≤40 PASS (23, 0×429); frame bằng chứng FAIL (step_035, step_042 thiếu); reel
khớp báo cáo FAIL (mỗi đoạn chỉ ~25% đúng cảnh theo nội dung); 0 HIGH giả FAIL (finding #1
giả); mắt khớp báo cáo MỘT PHẦN.

**Danh sách sửa CI-T8 (harness):**
1. Detector focus trong WebPlayer phải đọc ẢNH (tìm viền vàng/vòng focus trên
   OSD), không tin dump NONE — dump mù bên trong WebView (finding #1 giả).
2. Timebase tour không đều: ghi timestamp QA theo từng chunk (hoặc nhúng QA
   t vào video), tính video_t từ map đó thay vì /4,7 đều; verify reel theo
   NỘI DUNG (frame-match với shot trích dẫn), không chỉ theo timestamp; reel
   phải tránh cắt trúng khoảng loading (tour 248–252) và phải verify viền vàng
   bằng ảnh, không chỉ scene-match.
3. Frame bằng chứng thiếu phải FAIL ồn ào (step_035/step_042 class); đồng bộ
   shot/dump ở `_finish_mission` (step_051 không thấy dialog dù dialog đã mở).
4. Tốc độ 2057s → <1800s: vision latency 57,9s/call là nút thắt (11 call =
   637,2s); giảm call hoặc đổi endpoint nhanh hơn.
5. Vision endpoint: 3/11 call lỗi (2×503 + 1 timeout, 27%) — retry 1 lần khi
   503/timeout rồi mới ghi UNVERIFIED, hoặc fallback provider.
6. Detector "kẹt" phải coi điều hướng bàn phím là đổi trạng thái
   (`keyboard_open_image` True + highlight di chuyển) — STRESS không được FAIL
   oan khi đang gõ bàn phím.
7. Schedule detector: nếu run không có hàng LIVE, ghi item (e) là UNTESTED
   (không im lặng); thêm mission directed chờ hàng LIVE thật.
8. WebPlayer phát thật (F63): trial sau cần proxy VN (YUNA secrets) hoặc máy
   thật — embed 00:00/00:00 trong emulator không proxy không chứng minh được gì.
9. Per-step p95/mean trong report không khớp session — ghi rõ định nghĩa đo
   hoặc sửa cách tính (p50 = 5,38 khớp; p95 tính lại 20,01 vs report 21,95;
   mean tính lại 8,91 vs report 9,61).

### 15.14. CI-T8 — danh sách sửa đã làm (2026-11-12, fix loop Evelyn duyệt)

Mỗi mục = 1 commit riêng trên main repo QA (lệnh "tất cả làm việc trên
main"). Không sửa code app, không sửa workflow. Mock + replay kiểm sau mỗi
cụm fix; reviewer độc lập kiểm lại trước khi dispatch trial.

1. **Focus WebPlayer đọc ẢNH** (commit `7faff57`): `device.py` thêm
   `detect_focus_ring_anywhere(png)` — quét band OSD (0,850–1920,1080) tìm
   viền vàng/trắng (connected components, hollow, perimeter ≥ 0,45); ~39ms.
   `detectors.detect_player_focus_loss` trả [] khi `image_focus_ring` True;
   `runner._observe` gọi khi ở player mà dump không có focus, ghi
   `image_focus_ring`/`image_focus_box` vào ui_state + timeline. Mock N18
   `IMAGE_FOCUS_RING_OK`: viền vàng + viền trắng tìm được, khối đặc không
   bị nhận nhầm.
2. **Timebase tour theo chunk + verify reel bằng nội dung** (commit
   `6c26559`): `video_recorder.py` ghi wall-clock từng chunk (`_chunk_times`),
   `stop_and_save` dựng `chunk_map` (qa_start/end + raw_start/end theo thời
   lượng thật file norm, trước bước dọn file tạm) và `qa_to_tour_t(qa_t,
   chunk_map, speed_factor)` (nội suy trong chunk, kẹp ở khoảng trống +
   `in_gap`). `judge.build_defect_reel(..., chunk_map=...)` dùng map (ghi
   `timebase`/`in_gap` từng entry) rồi verify nội dung: trích 5 frame quanh
   `video_t` (±6s), pixel-diff với shot trích dẫn, dời tâm cắt về vị trí
   khớp nhất (ngưỡng 1,5%: cùng cảnh ~0,25–1,15, khác cảnh > 2) — đoạn
   loading không khớp shot nên tự bị tránh. `runner.finish()` truyền
   chunk_map + ghi `video_timebase`/`video_chunk_map` và số đoạn khớp nội
   dung vào `defect_reel_coverage`. Mock N19 `CHUNK_MAP_OK` +
   `REEL_CONTENT_OK` (tour đỏ 0–6s/xanh 6–12s, shot đỏ ở video_t=9 → dời về
   3s, content_verified True; shot xanh lá → False).
3. **Đồng bộ frame bằng chứng + FAIL ồn ào** (commit `006f6de`):
   `_observe` viết lại evidence frame của finding sang path đã lưu thật khi
   `_save_frame` dedup trả path cũ; `_finish_mission` viết lại evidence
   frame khi dedup + dùng KHUNG DIALOG ĐÃ THẤY (param `dialog_obs`, ghi ở
   `run_mission` khi `has_dialog` lần đầu) làm evidence cho mission cần
   dialog; frame bằng chứng thiếu trên đĩa → FAIL ồn ào (flag
   `evidence_frame_missing`, lý do "BẰNG CHỨNG THIẾU...") — chỉ lật PASS
   thành FAIL, UNVERIFIED giữ nguyên. Mock N20 `EVIDENCE_SYNC_OK`.
4. **Tốc độ** (commit `588ec3c`, cùng mục 5 phần retry): driver kẹt lần 1
   thử thoát cục bộ `DPAD_DOWN` (`stuck:local_unstick`, ~9s) trước khi tốn
   vision-assist; vision `_chat` timeout 30s → 60s (nemotron 120B +
   max_tokens 5000 cần ~45–55s, timeout cũ cắt call thành công rồi thử lại
   lãng phí); `wait_stable` 8s → 6s. Tiết kiệm kỳ vọng ~250s (cần trial đo
   lại — mục tiêu 2057s → <1800s). Mock N21 `LOCAL_UNSTICK_OK`.
5. **Vision retry 1 lần + fallback provider** (commit `588ec3c` phần retry,
   `3a1bf0e` phần fallback): `_post` tổng 2 lần gửi (1 gốc + retry 1) cho
   503/timeout/đóng kết nối; `VisionClient._chat` tách `_chat_once` +
   `_attempt` (đếm call/latency riêng từng lần gửi); primary lỗi →
   `_pick_fallback()` — provider đầu tiên đã cấu hình VÀ khác host primary
   (OPENAI qua integrate.api.nvidia.com không fallback sang NVIDIA_NIM vì
   cùng host); ghi `fallback_provider`/`fallback_used` vào `nim_stats()` +
   `report["vision_fallback"]`. **Ở CI chỉ có 1 provider nên fallback là
   no-op — ghi rõ, không giả vờ có.** Mock N21b `VISION_RETRY_ONCE_OK` +
   N22 `VISION_FALLBACK_OK` (stub: primary KILO 503 → fallback OPENAI trả
   kết quả, 2 call; không fallback → (None, error), 1 call).
6. **Bàn phím mở = trạng thái đổi** (commit `a804d75`): `_observe` tính
   `detect_keyboard_from_image(png)` mỗi bước (~50ms) → `ui_state` +
   `detector_ctx["keyboard_open_image"]`; `Driver.note_state` reset streak
   kẹt khi `keyboard_open` (dump) hoặc `keyboard_open_image` (ảnh);
   `detect_focus_trap` dùng ctx có sẵn thay vì chỉ tính lazy ở điểm sắp tố.
   Mock N23 `KEYBOARD_STUCK_OK`.
7. **Schedule LIVE** (commit `687eab2`, sửa ở `11a99ba`): `detect_schedule_live_no_score`
   ghi `ctx["schedule_live_seen"]` + đếm `schedule_live_rows` mỗi khi thấy
   hàng LIVE (có tỉ số hay không); mission mới
   `MISSION_SCHEDULE_LIVE_DIRECTED` (tab 1, `requires_live_row=True`,
   max_steps 8, required_texts `["live"]` — badge LIVE, không dùng
   "trực tiếp" vì text nav có sẵn ở mọi tab) — tổng **18 mission**;
   `run_mission` đổi FAIL/None **và cả PASS** thành `UNVERIFIED` khi mission
   cần hàng LIVE mà run không có hàng nào (PASS trên text nav mà không thấy
   hàng LIVE thì mission chưa kiểm được gì); `finish()` ghi
   `report["schedule_live_seen"]` + entry UNTESTED vào `unverified` khi cả
   run không có hàng LIVE. Mock N24 `SCHEDULE_LIVE_OK`.
8. **F63 / proxy VN — KHÔNG CÓ SECRET, trial chạy không proxy.**
   Kiểm `gh secret list` repo QA (chỉ tên): có APP_CHECKOUT_KEY,
   IOS_CHECKOUT_KEY, NVIDIA_API_KEY; **không có YUNA_PROXY_YAML,
   YUNA_SUB_URL, GEMINI_API_KEY, METEOR_API_KEY**. Trial CI-T8 chạy không
   proxy VN như CI-T7 — F63 (WebPlayer phát thật) vẫn không chứng minh
   được trong emulator; cần proxy hoặc máy thật. Hạn chế này phải ghi rõ
   trong báo cáo trial, không được ghi F63 PASS.
9. **Định nghĩa per-step** (commit `11a99ba`, cùng sửa mục 7):
   `finish()` ghi `timings["per_step_definition"]` (wall time cả bước =
   observe + gate + hành động + chờ ổn định) + `observe_p50_s`/
   `observe_p95_s`/`observe_mean_s` tính từ timeline `observe_s` để 2 dãy
   số tự khớp; `per_step_*` giữ nguyên. Mock N25 `TIMINGS_DEFINITION_OK`.

- **Mock: XANH, exit 0, 53 marker `_OK`** (43 gốc + 10 mới: N18, N19×2,
  N20, N21, N21b, N22, N23, N24, N25) — chạy lại toàn bộ sau cụm fix cuối
  (2026-11-12, `/tmp/mock_all3.log`).
- **Replay offline R9 trên artifact run-42950738729** (code CI-T8 đầy đủ,
  2026-11-12):
  - Có vision (`/tmp/qa_replay_R9_final/replay_report.json`, 154,4s):
    **P0 recall 8/8** (bắt hết P0-1..P0-8, không thiếu cái nào), **0 false
    pass**, 7 vision calls (provider NVIDIA_NIM qua integrate.api.nvidia.com
    — surrogate, cùng endpoint/model nemotron với OPENAI ở R8, chỉ khác
    nhãn), 7 requests, 0×429, mission 2 PASS / 3 FAIL / 11 UNVERIFIED,
    score 0/100 (điểm THẬT của build cũ — 8 P0 đã xác minh phạt > 100 →
    clamp 0, không phải lỗi harness, như R8).
  - Không vision (`/tmp/qa_replay_R9_novision/replay_report.json`, 3,2s):
    **P0 recall 5/8** (P0-1, P0-2, P0-4, P0-5, P0-6), 0 false pass,
    mission 1 PASS / 3 FAIL / 13 UNVERIFIED, score 12/100.
  - **So với R8 (7/8 có vision, 5/8 không vision): VƯỢT — P0-3 (thiếu ở
    R8 do lỗi transport `Connection reset by peer`) đã bắt được ở R9.**
    Không có P0 nào bị mất do code CI-T8. Lưu ý: recall replay dao động
    theo lỗi hạ tầng vision từng thời điểm (R8 chạy 2 lần đã cho 6/8 rồi
    7/8), 8/8 lần này không có nghĩa P0-3 đã "chắc chắn" — trial trực
    tiếp mới là thước đo thật.
- **Reviewer độc lập:** ĐÃ KIỂM (2026-11-12) — đọc code từng commit +
  chạy mock: **9/9 mục OK, không có lỗi chặn**. Mock của reviewer: exit 0,
  53 marker `_OK` (chạy 157s). Reviewer tìm 2 lỗi nhỏ, đã sửa trước trial:
  (1) chunk_map sai khi `_concat_norm` hỏng và chỉ giữ chunk dài nhất —
  đã sửa ở commit `f9cbfdf` (trim map về chunk được giữ, tách thành method
  `_build_chunk_map` để test được; mock N26 `CHUNK_MAP_TRIM_OK`); (2)
  docstring `detect_keyboard_from_image` còn ghi "chỉ gọi lazy" — đã sửa
  (gọi mỗi bước từ CI-T8 mục 6). Mock sau fix: **exit 0, 54 marker `_OK`**
  (53 + N26), `/tmp/mock_final.log`. Lưu ý của reviewer: tiết kiệm ~250s
  của mục 4 là ước tính — trial phải đo lại; recall replay dao động theo
  lỗi hạ tầng vision (8/8 lần này không có nghĩa P0-3 đã "chắc chắn").
- **Trial CI-T8:** ĐÃ DISPATCH + CHẠY XONG — run **43127423731**
  (workflow QA-Realtime-Trial, main@923a9ed, dispatch 2026-11-12 00:27:33Z,
  job `qa` 32m36s, **workflow SUCCESS**). Chưa kiểm chứng nội dung
  (verdict/điểm/số PASS/tốc độ QA) — cần coordinator riêng kiểm chứng
  (video + từng ảnh + report) trước khi kết luận; **không áp dụng
  switchover** trong vòng này.

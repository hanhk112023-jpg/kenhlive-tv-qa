# Đánh giá trực quan (Visual Review) — QA run 42520284499 (FULL #2)

**Nhánh:** `redesign/netflix` · **Commit:** `309926e` (gồm QA-fix 2 cho D19/D18/D8/D12) · **Chế độ:** FULL
**Kết quả job:** xem `qa_session_summary.md` · **Thời gian chạy:** 2820,6 s (~47 phút) · **Điểm:** 66/100
**Steps:** 127 · **Tabs (theo summary):** 4/7 (Lịch Thi Đấu 0, Tìm Kiếm 0, Cài Đặt 0 — chưa duyệt) · **Findings:** 4 (2 HIGH trùng nhau + 2 LOW)
**Video:** `full_qa_tour.mp4` — 45 MB, **359,8 s** cho phiên 2820,6 s (xem §3)

**Phạm vi bài đánh giá này:** đã đọc trực tiếp **20 ảnh** — các step
`001`, `002`, `005`, `007`, `015`, `022`, `025`, `026`, `029`, `030`, `031`,
`036`, `040`, `053`, `063`, `114`, `115`, `127`; cả hai ảnh mẫu trình phát;
**6 frame video** (mỗi 60 s, `vf_001`–`vf_006`); **3 crop phóng to**
(nav/clock step_007, clock step_127, góc trái-trên step_036);
`qa_report.json` + `qa_session.json` (toàn bộ timeline 127 bước + thoughts
của AI), `qa_session_summary.md`, plan Task 11 Step 5, và báo cáo QA-fix 2
(`task-11-qafix-2.md`). Đã đối chiếu sha256 ảnh mission với step shot.
Không suy đoán nội dung ngoài những gì nhìn thấy trong ảnh/timeline.

**Quy ước timeline** (như các lần trước): focus ghi ở step N là trạng thái
**TRƯỚC** action của step N; action ở step N gây ra focus ở step N+1.
Tọa độ focus trong timeline là không gian 1920×1080; ảnh chụp là 960×540
(chia đôi tọa độ).

---

## 0. Kết luận trước: lần chạy này kiểm chứng được rất ít

Đây là điểm khác biệt lớn nhất so với full run #1 — và phải nói trước khi
đọc bất kỳ phán quyết nào dưới đây:

- **AI chỉ vào PlayerActivity 6 bước (steps 25–30) rồi không bao giờ quay
  lại.** Sau step 30, toàn bộ 97 bước còn lại (steps 31–127) đều ở
  MainActivity, loanh quanh trên **cùng một màn hình Home/Thể thao**
  (focus chỉ đảo giữa `heroPlay` ↔ `heroDetails` ↔ `cardRoot`).
- **"Kho Phim 115 thao tác" trong summary là sai.** Tab detector ghi tab 5
  cho gần như mọi bước, nhưng nội dung trên màn hình là Home Hub + hàng Thể
  thao, không phải tab Kho Phim. AI không bấm OK lên bất kỳ `nav_*` nào
  trong steps 31–127 và không mở tab Lịch trình / Tìm kiếm / Cài đặt /
  IPTV nào cả.
- Hệ quả: **D19, D18, D12, WebPlayer, IPTV player, VOD player, tab Tìm
  kiếm/Cài đặt — tất cả đều KHÔNG được kiểm chứng trong lần chạy này**,
  dù đó chính là các mục QA-fix 2 cần re-check. Xem §4.
- Ngược lại, những gì lần chạy này **làm được tốt**: hero Thể thao lúc nghỉ
  (D8), RoomPicker, film detail (1 lần), và cú lỗi ExoPlayer thoáng qua
  steps 27–29 — đều có ảnh/timeline rõ ràng.

---

## 1. Từng ảnh mission (01–17) — giá trị bằng chứng ~0, trùng lặp gần hết

Đối chiếu sha256: **16/17 ảnh mission trùng step shot** (mission 06 là ảnh
duy nhất không trùng — player Thể thao). Ba mission 12/13/14 dùng **chung
một ảnh** (cùng một frame màn hình Home). Chỉ liệt kê những ảnh có nội dung
riêng hoặc đáng chú ý:

- **01** ≡ `step_001`: dialog THÔNG BÁO, **ĐÃ HIỂU / ĐÓNG focus, viền trắng,
  nút đỏ** — R1 vẫn sửa xong. Dòng cuối thân dialog ("…nhận file cập nhật
  mới nhất.") lần này **hiện đầy đủ**, không còn hơi cắt như run #1.
- **02** ≡ `step_005`/`006`/`042`, **03** ≡ `step_013`/`014`,
  **04** ≡ `step_016`/`018`/`019`, **05** ≡ `step_022`/`023`,
  **07** ≡ `step_040`, **08** ≡ `step_046`/`108`, **09** ≡ `step_053`,
  **10** ≡ `step_063`, **15** ≡ `step_112`/`117`,
  **16** ≡ `step_044`/`106`/`109`/`113`/`118`/`119`/`120`/`122`/`123` —
  tất cả đều là **màn hình Home/Thể thao**, không phải mục tiêu mission
  ghi trên tên (IPTV, Lịch trình, Settings…).
- **06** (duy nhất không trùng): player Thể thao, OSD hiện, video đang phát
  (tương đương `step_025`/`026`).
- **11** ≡ 14 step shot (`step_056`/`059`/`062`/`066`/`068`/`070`/`074`/
  `077`/`080`/`083`/`086`/`088`/`090`/`093`/`097`/`100`): **màn hình Home**,
  không phải player IPTV như tên mission "IPTV EPG & zapping" gợi ý.
- **12/13/14** ≡ cùng một frame (`step_057`/`058`/`060`/`067`/`071`/`072`/
  `075`/`078`/`081`/`084`/`091`/`094`/`095`/`098`/`101`): màn hình Home,
  focus `heroDetails` — mission "episode picker", "VOD seek", "player
  settings" nhưng ảnh không chứa picker, player hay dialog nào.

---

## 2. Phán quyết 4 findings (trong `qa_report.json`)

| # | Finding (step) | Phán quyết | Bằng chứng |
|---|---|---|---|
| 1 | [Step 5] [LOW] UI_JANK: 82 frames bị bỏ lỡ khi cold start | **KHÔNG XÁC MINH ĐƯỢC BẰNG MẮT — logcat-only, LOW, không ưu tiên** | Không có ảnh nào cho thấy giật/lag: `step_001` dialog hiện đầy đủ, `step_002`/`005` nội dung đã nạp đủ (hàng SẮP DIỄN RA + PHIM ĐANG THỊNH HÀNH). 82 frames bỏ lỡ trên emulator lúc cold start là con số logcat, không có biểu hiện nhìn thấy. Giữ LOW, không cần sửa riêng. |
| 2 | [Step 22] [LOW] Tên giải đấu hiển thị dạng mã thay vì tên tiếng Việt đầy đủ | **REAL — nhưng chỉ một nửa câu chuyện** | Đúng trên mọi thẻ trận: `step_007`/`022`/`031` cho thấy `SPA D1`, `POR D1`, `HOL D1`, `BRA D2`, `ARG D1`. Nhưng dữ liệu **không nhất quán**: cùng một màn hình, có thẻ ghi tên đầy đủ (`Serie A`, `Ligue 1` — `step_007`), và **RoomPicker ghi tên đầy đủ** (`step_015`: "TSG Hoffenheim vs Schalke / Bundesliga · 1 phòng live"). Nghĩa là mapping tên giải **đã tồn tại trong app** nhưng chưa được áp lên thẻ trận. LOW, sửa bằng cách dùng cùng nguồn tên như dialog RoomPicker. |
| 3 | [Step 28] [HIGH] ExoPlayer lỗi sau khi nhấn A/Đỏ chuyển Aspect Ratio | **ENVIRONMENTAL + KHÔNG CÓ BẰNG CHỨNG HÌNH ẢNH — không phải regression của aspectBtn** | Xem phân tích chi tiết dưới. |
| 4 | [Step 29] [HIGH] Cùng lỗi ExoPlayer (khi nhấn A/Đỏ) | **TRÙNG LẶP của #3 — cùng một sự kiện thoáng qua, đã tự khôi phục; bị trừ điểm 2 lần** | Xem phân tích chi tiết dưới. |

### Findings #3/#4 — phân tích timeline steps 25–30

Dòng thời gian (giờ wall-clock suy từ `created_at 20:33:40` + `time_offset_sec`):

| Step | t (s) | Action | Trạng thái phát | Screenshot |
|---|---|---|---|---|
| 25 | 546 | WAIT 2s | `is_playing: false`, motion 0.00 | `step_025` — video đang phát, OSD Thể thao hiện đầy đủ |
| 26 | 687 | MENU | `is_playing: true`, motion **7.54%** | `step_026` — OSD y hệt step_025, video khác frame (đang chạy) |
| 27 | 823 | **A** (Đỏ, Aspect Ratio) | `is_playing: false`, motion 0.00 | **null — KHÔNG CÓ ẢNH** |
| 28 | 977 | B (Vàng) | `is_playing: false`, motion 0.00 | **null — KHÔNG CÓ ẢNH** |
| 29 | 1126 | COMPLETE_MISSION | `is_playing: true`, motion **29.96%** | `step_029` — video phát bình thường, OSD đầy đủ, **không có dialog lỗi nào** |
| 30 | 1263 | SWITCH_TAB 6 | `is_playing: true`, motion 15.95% | `step_030` — video vẫn phát (close-up cầu thủ, khác frame step_029) |

Bốn lý do khiến #3/#4 không đứng được như "HIGH regression của aspectBtn":

1. **Không có bằng chứng hình ảnh nào về lỗi.** Hai step mang finding
   (27, 28) đều có `screenshot: null` — harness không chụp được đúng hai
   frame quan trọng nhất. Ảnh duy nhất sau sự kiện (`step_029`, `step_030`)
   cho thấy video phát khỏe, OSD nguyên vẹn, không có dialog "Lỗi Phát
   Luồng" nào. Trong run #1, lỗi codec tương tự **có** dialog lỗi chụp được
   (step_088); lần này không có.
2. **Nhân quả với phím A không chứng minh được.** Phím A bấm ở t=823 s
   (≈20:47:23); logcat `PLAYER_ERR: ExoPlaybackException` ghi ở
   **20:48:19.559** (≈t=879 s) — **~56 giây sau** phím A, giữa một khoảng
   trống 154 s không có action nào (step 27 → step 28). Lỗi có thể xảy ra
   bất cứ lúc nào trong khoảng trống đó; gán cho phím A là suy diễn
   post-hoc từ logcat.
3. **Không thấy aspect thay đổi.** So `step_026` với `step_029`: cùng một
   khung hình sân bóng, cùng OSD, không có thay đổi letterbox/crop nào
   nhìn thấy, không có toast/nhãn nào báo chế độ aspect mới. Không thể
   xác nhận phím A đã làm gì trên màn hình — kể cả có đổi aspect hay không.
4. **Đã tự khôi phục hoàn toàn, và đây là mẫu cũ trên emulator x86.**
   Chính detail của finding #4 cũng ghi: "Video tạm dừng (motion 0%) sau
   khi nhấn A, sau đó **tự khôi phục và phát lại (motion 29.96%)**".
   `MediaCodec CodecException` + `ExoPlaybackException` thoáng qua là mẫu
   đã thấy ở run #1 (step_088 `ERROR_CODE_DECODING_FAILED`, tự phát lại ở
   step_089) — cùng emulator x86, cùng tính chất tự hồi phục. Không có dấu
   hiệu nào cho thấy aspect-cycle control mới (Task 9) gây ra lỗi này:
   lỗi không đi kèm crash, không kẹt OSD, không cần reload thủ công.

**Kết luận #3/#4:** một sự kiện codec thoáng qua trên emulator, tự hồi phục
trong cùng một mission, bị ghi thành 2 HIGH. Xếp loại đúng: **LOW /
environmental, 1 sự kiện duy nhất**. Không chặn review, không cần sửa
aspectBtn theo hướng này (nếu muốn củng cố thì chỉ cần cơ chế
auto-recovery đã có — nó đã hoạt động: video tự phát lại).

### Điểm 66/100 — đọc thế nào (xem thêm §8)

66 = 100 − 15 (#3) − 15 (#4) − 2 (#1) − 2 (#2) theo thang của judge. Khử
#3/#4 về 1 sự kiện LOW/environmental thì thang judge cho **~96/100**.
Nhưng như run #1, thang judge không chấm các lỗi thật thấy trên màn hình
(§5–§6) và không phản ánh bao phủ (§0).

---

## 3. Video `full_qa_tour.mp4`

| Frame video | Nội dung thấy được |
|---|---|
| 0 s (`vf_001`) | Hero Thể thao Atletico vs Barcelona + thẻ CF Estrela focus (tương đương step_007–010, session t≈130–230 s) — **không phải cold start** |
| 60 s (`vf_002`) | Player Thể thao, OSD hiện, video đang phát (steps 25–26) |
| 120 s (`vf_003`) | Player Thể thao, frame khác — **video chuyển động thật giữa vf_002→vf_003** (vị trí cầu thủ/bóng đổi) |
| 180 s (`vf_004`) | Home đang cuộn: ĐANG PHÁT TRỰC TIẾP + SẮP DIỄN RA, thẻ CA Central Cordoba focus; **chữ "[OK] XEM NGAY / [MENU] CHỌN PHÒNG" của hero hiện mờ xuyên qua nav** (ghost 10%, xem §4 D8) |
| 240 s (`vf_005`) | Home, ĐANG PHÁT TRỰC TIẾP (tương đương step_031) |
| 300 s (`vf_006`) | Hero Thể thao lúc nghỉ, clock 03:33 + ngày đầy đủ, sạch (tương đương step_127 nhưng ở trạng thái nghỉ) |

**Kết luận video: vẫn chưa phải full tour 1x — lần thứ ba liên tiếp.**
File dài **359,8 s** (ffprobe xác nhận, 1280×720, 32 fps, 45 MB) cho phiên
2820,6 s → **nén ~7,8x**. `concat.txt` **có** (16 chunk). Video bao phủ
session t≈130 s → t≈2715 s: **thiếu ~2 phút đầu** (cold start, dialog
THÔNG BÁO, finding #1) và **thiếu ~100 s cuối**. `qa_timelapse.mp4` 36,1 s
(timelapse 10x). **Kỳ vọng "full-length video" của Task 11 Step 5 KHÔNG
đạt** — cùng lỗi recorder như quick run (468,7 s / 3967 s) và full run #1
(480,6 s / 4152,6 s, ~8,6x); không cải thiện dù đã thêm ffmpeg vào QA deps.
Thứ tự chunk trong video cũng không đơn điệu theo session (vf_004 ≈
session t≈1500 s nhưng vf_005 ≈ session t≈1310 s), nên không dùng được để
đối chiếu thời gian thực.

---

## 4. Re-check 4 mục QA-fix 2 (commit 309926e)

| Mục | Fix 2 định sửa | Verdict trên màn hình | Bằng chứng |
|---|---|---|---|
| **D19** dialog cài đặt — focus tới được ĐÓNG | `nextFocusDownId = android.R.id.button2` cho chip hàng cuối + `nextFocusUpId` từ ĐÓNG về chip seek (`PlayerActivity.kt`) | **NOT OBSERVED — không kiểm chứng được lần này** | Xem dưới |
| **D18** episode picker nền đặc | `EpisodePickerDialog.kt:451` transparent → `R.drawable.bg_dialog` | **NOT OBSERVED — không kiểm chứng được lần này** | Xem dưới |
| **D8** hero Thể thao lúc nghỉ | 56dp top margin cho hero item (`SportAdapter.kt`) | **FIXED lúc nghỉ; PARTLY khi cuộn (ghost + D22 mới)** | Xem dưới |
| **D12** VOD bar — Speed/Lock | Không đổi code (wiring đã đúng, cần test RIGHT-walk) | **NOT OBSERVED — không kiểm chứng được lần này** | Xem dưới |

### D19 — NOT OBSERVED
Dialog "Cài đặt trình phát" **không mở lần nào trong cả phiên**. Mission 15
tên "player settings dialog" chạy 18 bước (steps 94–111) nhưng toàn bộ đều
ở MainActivity với focus `heroPlay`/`heroDetails`/`cardRoot` — AI không vào
player, không bấm TÙY CHỌN, không có ảnh dialog nào trong 142 screenshot.
Fix code (explicit focus chain) vẫn chưa có bằng chứng runtime. Cần một lần
test chủ đích: mở dialog trong player VOD, bấm DOWN từ chip seek tới ĐÓNG
(chính transition mà full run #1 chưa bao giờ thử).

### D18 — NOT OBSERVED
Episode picker **không mở lần nào trong cả phiên** — cả hai đường:
- Từ màn hình chi tiết phim: AI mở được **duy nhất 1 màn hình chi tiết**
  (`step_036`, phim "Cuộc Chiến Ẩm Thực") rồi bấm OK ngay lên nút
  `btnHeroBackHome` ("Về trang chủ") ở step_36, **không bao giờ bấm
  CHỌN TẬP**. Mission 13 "episode picker" (steps 75–83) toàn bộ là màn
  hình Home.
- Từ trong player: player VOD không mở lần nào (xem D12).
Fix một dòng (`bg_dialog`) vẫn chưa có bằng chứng runtime. Cần test chủ
đích: mở CHỌN TẬP từ màn hình chi tiết và xác nhận không còn chữ/nút chi
tiết xuyên qua lưới tập.

### D8 — FIXED lúc nghỉ, PARTLY khi cuộn
- **Lúc nghỉ: FIXED, rõ ràng.** `step_007`/`022`/`127`, `vf_001`/`vf_006`:
  hero Thể thao bắt đầu dưới nav; hàng badge ("● TRỰC TIẾP • SPA D1 •
  👁 434,9K") nằm **dưới** hàng nav, không còn đè lên KENHLIVE /
  TRANG CHỦ / TRUYỀN HÌNH như run #1. Tiêu đề, subtitle, 2 nút
  [OK] XEM NGAY / [MENU] CHỌN PHÒNG, clock "03:35/03:38" + ngày — tất cả
  sạch, đủ trong hero 216dp. Đúng như QA-fix 2 tính toán (badge 16→72dp).
  Đánh đổi đã báo trước có thật: có một dải nền #141414 phẳng 56dp phía
  trên hero lúc nghỉ — nhìn như khoảng trống, nhưng cùng màu nền app nên
  không chói.
- **Khi cuộn: vẫn lỗi (dạng ghost đã biết + D22 mới).** `vf_004`: chữ
  "[OK] XEM NGAY / [MENU] CHỌN PHÒNG" của hero hiện mờ **xuyên qua nav**,
  đè lên nhãn nav — đúng ghost 10% của token `kl3_nav_solid` #E6141414 mà
  QA-fix 2 đã đo và để lại cho Evelyn quyết (không đổi code). `step_005`:
  vệt màu mờ sau nhãn nav khi cuộn. Và **D22** (mới, xem §5): đồng hồ/ngày
  của hero bị cắt nửa khi ở trạng thái cuộn (`step_127`).

### D12 — NOT OBSERVED
Player VOD (native hay web) **không mở lần nào**. Timeline activities:
MainActivity 121 + PlayerActivity 6 (toàn bộ là player Thể thao steps
25–30), **WebPlayerActivity 0** — lần thứ ba liên tiếp (quick run, full
run #1, full run #2). Mission 14 "VOD player seek & resume" (steps
84–93) toàn bộ là màn hình Home. Hàng nút VOD, Speed, Lock — không có ảnh
nào. Test RIGHT-walk mà QA-fix 2 yêu cầu (focus Settings → RIGHT ×2 tới
Speed → RIGHT tới Lock) vẫn chưa được thực hiện.

---

## 5. Khiếm khuyết mới trong lần chạy này (D22–D23)

| # | Mức | Vấn đề | Bằng chứng |
|---|---|---|---|
| **D22** | MEDIUM-LOW | **Đồng hồ/ngày của hero bị cắt nửa khi màn hình ở trạng thái cuộn — dòng ngày không đọc được.** Ở `step_127`, cụm "03:33" + "Thứ Hai, 09/11/2026" trượt lên vùng nav: hộp giờ "03:33" còn nguyên nhưng dòng ngày "Thứ Hai, 09/11/2026" chỉ còn **nửa dưới của chữ** (nửa trên bị cắt ngang đúng mép nav), "01/10 ÂL · Ất Tỵ" đỏ phía dưới còn đủ. Cùng một hero ở trạng thái nghỉ thì sạch (`step_007`, `vf_006` — ngày đầy đủ). Đây là biến thể mới của họ D8: hero trượt dưới nav khi cuộn, và lần này phần tử bị ảnh hưởng là cụm clock/date chứ không phải badge hay nút. Cơ chế chính xác (clock có phải con của hero đang cuộn hay không) chưa rõ từ ảnh tĩnh — cần kiểm tra ở trạng thái cuộn, không suy đoán thêm. | `step_127`, crop `crop_127_clock.png` (đối chiếu `step_007` / `crop_007_clock.png`, `vf_006`) |
| **D23** | MEDIUM-LOW | **Nút quay lại hình tròn trên màn hình chi tiết phim đè lên logo KENHLIVE và bị nav cắt nửa.** Ở `step_036` (màn hình chi tiết "Cuộc Chiến Ẩm Thực"), nút tròn `btnHeroBackHome` ("Về trang chủ", focus ở step_36 là `[45,45][155,155]`) nằm đúng lên chữ KENHLIVE — vòng tròn trắng đè lên chữ K, nửa trên vòng tròn bị khuất sau nav. Dưới nav, chữ bìa mờ "…ĐIỆN ẢNH ĐẶC SẮC" vẫn lộ qua (N11). Ngoài nút này, màn hình chi tiết sạch: tiêu đề, mô tả, 4 nút XEM NGAY/CHỌN TẬP/LƯU PHIM/PHIM KHÁC, chip DANH MỤC, hàng "Phim Mới Cập Nhật · 120 phim" đều rõ. | `step_036`, crop `crop_036_topleft.png` |

### Quan sát thêm (N-series, không phải defect UI trực tiếp)

- **N8 — Tỉ số/lượt xem phi thực tế, vẫn còn.** `step_022`: thẻ
  "FC Utr… **4:12** NEC Ni…" — 4:12 không phải tỉ số bóng đá hợp lệ;
  `vf_001` cùng thẻ ghi "3:1…" (số liệu đổi giữa các lần chụp). Lượt xem
  cùng trận Atletico nhảy 433,9K → 434,9K → 437,0K (`step_007`/`022`/
  `015`) trong vài phút. Dữ liệu nguồn, không phải UI — nhưng người xem
  thấy ngay vì tỉ số app và tỉ số trên luồng đối chiếu nhau trong cùng một
  khung hình (luồng ghi 0-0, Hiệp 1: 7' ở `step_025`/`026`).
- **N15 — Đồng hồ hero không đơn điệu theo thời gian phiên.** Cùng một
  cụm clock/date ghi 03:35 (`step_007`, session t=132 s), 03:38
  (`step_015`/`022`, t=297–389 s), rồi **03:33** (`step_127`, t=2715 s;
  `vf_006`). Không tăng theo thời gian thực — nguồn giờ của hero không
  phải đồng hồ thiết bị đang chạy, hoặc giá trị được cache/rebind theo
  hero. Chỉ là quan sát lạ, chưa rõ nguyên nhân, cần xem nguồn dữ liệu —
  không xếp là defect UI.
- **N9 — Phòng 0 lượt xem: không re-check được.** RoomPicker chỉ mở từ
  Thể thao lần này (`step_015`: A BỆU 34,4K xem; `step_024`: phòng 5 LỬA
  Lv.4) — không có lần mở từ Lịch trình để đối chiếu như run #1.
- **N11 — Chữ bìa/cover lộ qua nav, vẫn còn.** Chữ mờ "…ĐIỆN ẢNH ĐẶC SẮC"
  lộ qua nav trên màn hình chi tiết (`step_036`); vệt chữ hero lộ qua nav
  khi cuộn (`step_005`, `vf_004`); chữ "…KÊNH GIẢI TRÍ…" ló ở mép trên
  (`step_040`/`063`). Cùng gốc rễ D8 (nav 90% đục).
- **N12 — Đồ họa của luồng đè lên OSD của app, vẫn còn.** Logo
  "SUTBONGTV" của luồng đè lên tiêu đề OSD Thể thao phía trên-phải
  (`step_025`/`026`/`029`, `vf_002`/`vf_003`); banner quảng cáo "TẢI NGAY
  APP BUFA / http://bufa.chat" chạy dọc mép dưới, sát seekbar
  (`step_025`/`026`/`029`/`030`); score bug của luồng ("BEN 0") đè góc
  trên-trái OSD (`step_025`). Cosmetic, khó sửa triệt để.
- **N16 — Tên đội/trạng thái cắt ngắn trên thẻ trận, vẫn còn (thiết kế,
  cần Evelyn quyết).** "Atletic…", "FC Bar…", "CF Estr…", "NEC Ni…",
  "Goias …", "Ponte …" (`step_005`/`007`/`022`/`031`); nhãn BLV
  "Đang trự…" (`step_005`/`031`); tên kênh "360 Bundesli…",
  "360 C1 Châu …" (`step_114`). Thẻ trận rộng ~330dp chứa 2 đội + logo +
  badge nên tên luôn bị cắt — như run #1 đã ghi, đây là thiết kế, không
  phải bug render.
- **N17 — Ảnh mission trùng lặp / sai mục tiêu, nặng hơn run #1.**
  16/17 ảnh mission trùng step shot (sha256, xem §1); 3 mission 12/13/14
  dùng chung đúng một frame; ảnh 11 (mission "IPTV EPG & zapping") là màn
  hình Home. Ảnh mission gần như không còn giá trị kiểm chứng riêng.

---

## 6. Trạng thái D1–D21 (so với full run #1, 42511640281)

| Defect cũ | Trạng thái lần này | Bằng chứng |
|---|---|---|
| **D1** — chữ bìa banner đè lên chữ UI | **ĐÃ SỬA (giữ nguyên).** Hero Thể thao lúc nghỉ sạch hoàn toàn (tiêu đề/nút/clock không còn chữ bìa đè); màn hình chi tiết phim sạch (`step_036`). Chỉ còn N11 (chữ bìa lộ qua nav, không đè lên chữ UI). | `step_007`/`022`/`036`, `vf_001`/`006` |
| **D2** — hàng SẮP DIỄN RA trống | **ĐÃ SỬA (giữ nguyên).** Hàng có nội dung đầy đủ (`step_002`/`005`/`031`: Ceara 05:15, Goias 05:15, CA Central Cordoba 05:30 + "Còn 1h 41p"). | `step_002`/`005`/`031` |
| **D3** — nhãn stat portal card cắt nửa ở fold | **ĐÃ SỬA (giữ nguyên, portal đã bỏ).** Không còn portal card trong bất kỳ ảnh nào. | toàn bộ |
| **D4** — focus trên kênh IPTV mờ | **KHÔNG KIỂM CHỨNG ĐƯỢC lần thứ ba liên tiếp.** Tab IPTV không mở; chỉ có hàng "KÊNH TRUYỀN HÌNH NỔI BẬT" trên Home (`step_114`: 6 thẻ kênh 360 Anime/Bundesliga/C1/C2/C3/Công Thương, thẻ focus "360 Công Th…" có viền trắng rõ — nhưng đó là hàng Home, không phải lưới kênh IPTV). | `step_114`, timeline steps 53–69 |
| **D5** — hàng cuối lưới IPTV cắt nửa | **KHÔNG KIỂM CHỨNG ĐƯỢC lần thứ ba liên tiếp.** Cùng lý do D4. (Hàng kênh trên Home ở `step_114`/`115` thì bị cắt nửa ở fold — nhưng đó là trạng thái cuộn bình thường của một hàng, không phải lưới IPTV.) | `step_114`/`115` |
| **D6/D10** — pill xám "0" | **ĐÃ SỬA (giữ nguyên).** Không còn pill "0" ở bất kỳ thẻ nào; pill hợp lệ "Hiệp 1: 4'" (`step_022`), "Còn 1h 41p" (`step_002`/`005`). | `step_007`/`022`/`031`, `vf_001` |
| **D7** — OSD clipping | **KHÔNG KIỂM CHỨNG ĐƯỢC lần này.** Player VOD không mở (D12); player Thể thao không có nhãn nào bị cắt giữa từ. Phụ đề trên OSD bar: vẫn chưa có ảnh nào có phụ đề + OSD cùng lúc. | steps 25–30 |
| **D8** | **FIXED lúc nghỉ; PARTLY khi cuộn.** Xem §4. Ghost 10% + D22 mới. | `step_007`/`022`/`127`, `vf_004`/`006` |
| **D9** — clock/date đè nav | **FIXED lúc nghỉ (giữ nguyên).** Clock/date nằm dưới nav khi hero hiện đầy đủ (`step_007`/`022`, `vf_006`). **Biến thể mới khi cuộn: D22** (ngày bị cắt nửa, `step_127`). | `step_007`/`022`/`127` |
| **D11** — episode picker focus | **KHÔNG KIỂM CHỨNG ĐƯỢC lần này.** Picker không mở (xem D18). Run #1 đã xác nhận sửa xong (chức năng). | steps 75–83 |
| **D12** | **NOT OBSERVED.** Xem §4. | — |
| **D13** — dialog cài đặt cắt chip + cắt dòng cuối | **KHÔNG KIỂM CHỨNG ĐƯỢC lần này.** Dialog không mở (xem D19). | — |
| **D14** — OSD Thể thao không focus được | **CHƯA SỬA (giữ nguyên).** Focus NONE suốt steps 25–30; không nút OSD nào có viền trắng trong `step_025`/`026`/`029`/`030`, `vf_002`/`vf_003`; MENU ở step_26 không làm thay đổi gì nhìn thấy (OSD đã hiện sẵn). Khác với VOD ở run #1 (focus thấy rõ trên nút). | `step_025`/`026`/`029`/`030` |
| **D15** — BACK không thống nhất | **KHÔNG KIỂM CHỨNG ĐƯỢC lần này.** Chỉ 2 lần BACK trong cả phiên, cả hai đều đóng RoomPicker trong MainActivity (steps 15, 17 — focus về đúng thẻ trận). Không có lần BACK nào trong player: AI rời player bằng SWITCH_TAB (step_30 → step_31 về MainActivity, hoạt động). Quy tắc 2-BACK trong player chưa được thử lại. | steps 15/17/30/31 |
| **D16** — ô nhập tìm kiếm không khung | **KHÔNG KIỂM CHỨNG ĐƯỢC lần thứ ba liên tiếp.** Tab Tìm kiếm 0 thao tác. | timeline |
| **D17** — TRANG CHỦ thiếu gạch chân đỏ + chấm đỏ bí ẩn | **ĐỔI DẠNG / CẢI THIỆN MỘT PHẦN.** Gạch chân đỏ **giờ thấy rõ trên TRANG CHỦ** ngay cả khi hero đang hiện (`step_007`/`022`/`031`/`040`/`053`/`063`/`114`/`127`, `vf_001`/`004`/`005`/`006`) — khác run #1 (không thấy trên Home Hub khi hero hiện). Lý do khớp: hero đã đẩy xuống 56dp nên không còn che gạch chân. Gạch chân cũng thấy trên KHO PHIM ở màn hình chi tiết (`step_036`). **Chấm đỏ sau "TRANG CHỦ" thì vẫn còn trong mọi ảnh, kể cả khi tab khác đang được chọn** (`step_036` KHO PHIM đang chọn mà chấm đỏ vẫn sau TRANG CHỦ) — vẫn chưa rõ là gì, cần đáp án thiết kế. | `step_007`/`022`/`031`/`036`, crop nav |
| **D18** | **NOT OBSERVED.** Xem §4. | — |
| **D19** | **NOT OBSERVED.** Xem §4. | — |
| **D20** — WebPlayerActivity 0 lần | **VẪN 0 — lần thứ ba liên tiếp.** Activities: MainActivity 121, PlayerActivity 6, WebPlayerActivity 0. Mission 13 "WebPlayerActivity" vẫn "pass" nhưng VOD không mở lần nào. Web seek bar, web Speed gate (`playbackRate` probe), web brightness — **vẫn chưa được kiểm chứng ở cả ba lần chạy**. | activity counter, steps 84–93 |
| **D21** — lưới kênh IPTV không xuất hiện | **VẪN KHÔNG XUẤT HIỆN — lần thứ ba liên tiếp** (dạng nhẹ hơn: lần này có hàng kênh IPTV trên Home, `step_114`, nhưng không phải tab IPTV). Mission 9/10 "IPTV categories & favorites / EPG & zapping" pass trên giấy nhưng ảnh chụp là màn hình Home. | steps 53–69, `step_114` |

**Đã xác nhận sửa xong trong lần này (so với full run #1):** D8 lúc nghỉ,
D17-gạch-chân (giờ thấy trên TRANG CHỦ cả khi hero hiện), R1 (giữ nguyên),
D1/D2/D6-D10 (giữ nguyên).
**Đã xác nhận còn:** D8 khi cuộn (ghost 10% + D22), D14, D17-chấm-đỏ.
**Mới:** D22 (ngày hero cắt nửa khi cuộn), D23 (nút back chi tiết phim đè
logo).
**Chưa có kết luận (cần mission ép đường test):** D19, D18, D12, D11, D13,
D7-phụ-đề, D15-trong-player, D4/D5, D16, D20, gate seek Thể thao, EPG
bar/Mini-Guide IPTV, UP lên nav từ hàng đầu các tab ngoài Home.

---

## 7. Đối chiếu checklist Task 11 Step 5

- **Bảng màu KL6.5: ĐẠT.** Nền #141414, card #242424, chữ trắng/xám, đỏ
  #E50914 chỉ dùng cho logo KENHLIVE, badge LIVE/TRỰC TIẾP, nút chính
  ([OK] XEM NGAY, ĐÃ HIỂU / ĐÓNG). Không còn cam KL5/cyan cũ, không
  gradient, không glow. Badge SOCO (xanh lá) / COLA là badge nguồn dữ liệu.
- **Top nav — gạch chân đỏ tab đang chọn: ĐẠT (cải thiện so với run #1).**
  Thấy trên TRANG CHỦ ở mọi trạng thái đã chụp (`step_007`/`022`/`031`/
  `040`/`053`/`063`/`114`/`127`) và trên KHO PHIM ở màn hình chi tiết
  (`step_036`). Chấm đỏ sau TRANG CHỦ vẫn chưa rõ (D17).
  Nav chuyển đặc khi cuộn hẳn nhưng ghost 10% còn (D8, `vf_004`).
- **Billboard: ĐẠT khi hiện đầy đủ** (`step_007`/`022`, `vf_001`/`006`
  sạch), **lỗi khi cuộn** (ghost `vf_004`, D22 `step_127`). Ảnh bìa vẫn
  chứa chữ quảng cáo mờ (N11).
- **Các hàng: ĐẠT.** Hàng live/upcoming/phim đều có nội dung, không hàng
  trống; tên giải (dạng mã, finding #2), tỉ số, lượt xem, số phòng đọc rõ.
  Tên đội trên thẻ trận bị cắt ngắn — thiết kế, cần Evelyn quyết (N16).
- **6-per-row: ĐẠT với poster phim.** Poster phim 6/hàng, tiêu đề 2 dòng
  đọc được (`step_002`/`040`/`053`/`063`/`114`: "Mục Thần Ký 2024",
  "Thần Tài Đậu Chiêm Long 2026"…). Thẻ trận rộng ~330dp, ~2,7 thẻ/hàng —
  không áp 137dp cho thẻ trận, như build hiện tại.
- **Top-bar reachability: ĐẠT MỘT PHẦN, có tiến bộ về bằng chứng.**
  Focus **nhìn thấy** lên nav: viền trắng quanh TRANG CHỦ ở `step_031`
  (sau UP từ hàng đầu) và nhiều bước sau (`step_037`/`056`/`062`/`066`/
  `068`/`070`/`074`/`077`/`080`/`083`/`086`/`088`/`090`/`093`/`097`/`100`
  — focus `heroPlay`/`heroDetails` với viền quanh nav). Nhưng AI không bao
  giờ bấm OK lên một mục nav nào, nên **chuyển tab bằng D-pad vẫn chưa
  được chứng minh**; 2 lần SWITCH_TAB của harness (steps 6, 30) thì hoạt
  động. Từ hàng đầu các tab ngoài Home, UP lên nav vẫn chưa được thử.
- **OSD Thể thao vs mẫu sport: ĐẠT VỀ CƠ BẢN, trừ focus và gate.**
  Score pill góc trên-trái ✓ ("Hiệp 1: 7' · CFE 0 - 0 BEN",
  `step_025`/`026`/`029`/`030`), TUA ±30S ✓ (nút chữ, không phải icon
  tròn như mẫu), seekbar trắng + knob ✓ (00:00, knob trắng rõ),
  "Về trực tiếp" ✓ (nút góc dưới-phải, có chấm đỏ trước chữ),
  2 hàng nút KL6.5 (Chọn BLV/Đổi luồng/KÊNH TIẾNG/ĐA MÀN HÌNH/PIP/
  TÙY CHỌN) ✓. So với mẫu sport: mẫu có icon tròn ↺30 / ⏸ / ↻30 giữa
  màn hình; app dùng nút chữ TUA -30S / PHÁT / TUA +30S — khác hình thức,
  cùng chức năng. **Nhưng:** không nút OSD nào focus được (D14); thanh
  live đứng ở 00:00, nhãn phải "00:06" khó hiểu; phần buffered xám nhạt
  không phân biệt được trên ảnh tĩnh (track tối + quảng cáo luồng đè lên).
  **Gate hỗ trợ vẫn chưa xác minh được:** AI không bấm LEFT/RIGHT ở
  player Thể thao trong cả ba lần chạy, nên không biết ±30S có tua thật
  trên luồng live không.
- **OSD IPTV vs mẫu: KHÔNG KIỂM CHỨNG ĐƯỢC.** Player IPTV không mở lần
  nào. Mini-Guide và EPG bar không xuất hiện trong bất kỳ ảnh nào. Hàng
  kênh IPTV trên Home (`step_114`) không phải player.
- **OSD VOD vs mẫu vod: KHÔNG KIỂM CHỨNG ĐƯỢC.** Player VOD không mở
  lần nào (native hay web). Seekbar, episodes, brightness slider,
  Speed/Lock — không có ảnh nào. Gate web Speed: không áp dụng được
  (D20, WebPlayer 0 lần).
- **Thanh player lúc nghỉ và lúc focus: CHỈ KIỂM CHỨNG ĐƯỢC 1 MẶT.**
  - Live (Thể thao): knob trắng thấy rõ lúc OSD hiện (`step_025`/`026`/
    `029`, `vf_002`/`vf_003`); phần đã phát/buffered không phân biệt được;
    chấm đỏ LIVE ở đầu phải: **có** — chấm đỏ trước nút "Về trực tiếp"
    (`step_025`/`026`); nhãn "00:06" khó hiểu. OSD **không bao giờ ẩn**
    trong steps 25–30 (AI không bấm BACK/OK để ẩn), nên trạng thái nghỉ
    (video trần) của player Thể thao chưa thấy lần này — khác run #1
    (BACK 1 ẩn OSD).
  - VOD/IPTV: không có ảnh.
- **BACK: KHÔNG KIỂM CHỨNG ĐƯỢC trong player.** Chỉ 2 lần BACK, đều đóng
  RoomPicker (steps 15, 17). Không có lần BACK nào trong player; AI rời
  player bằng SWITCH_TAB (step_30). Quy tắc 2-BACK của run #1 chưa được
  thử lại.
- **Phụ đề: chưa kiểm chứng được vị trí trên OSD bar.** Không ảnh nào có
  phụ đề + OSD bar cùng lúc.
- **R1: ĐÃ SỬA (giữ nguyên).** `step_001`: ĐÃ HIỂU / ĐÓNG focus, viền
  trắng; dòng cuối dialog lần này hiện đầy đủ.
- **Dialog cài đặt thống nhất: KHÔNG KIỂM CHỨNG ĐƯỢC.** Dialog không mở
  (D19 NOT OBSERVED); D13 cũng vậy.

---

## 8. Điểm 66/100 — có công bằng không?

**Không công bằng nếu hiểu là "chất lượng build".** 66/100 = 100 − 15
(finding #3) − 15 (finding #4, trùng #3) − 2 (#1) − 2 (#2). Hai HIGH là
**một sự kiện codec thoáng qua trên emulator, đã tự khôi phục, không có
bằng chứng hình ảnh, nhân quả với phím A không chứng minh được** (§2) —
khử artifact thì thang của judge cho **~96/100**, và finding #2 (LOW, REAL)
là điểm trừ thật duy nhất trong 4 findings.
**Nhưng 66/100 cũng không nên được đọc là "app gần hoàn hảo":** thang của
judge không chấm các lỗi thật thấy trên màn hình — D8 khi cuộn (ghost +
D22), D14, D17-chấm-đỏ, D23 — và không phản ánh các khoảng chưa test, lần
này **lớn hơn hẳn run #1**: D19/D18/D12/D11/D13/D7/D15/D4/D5/D16/D20, gate
seek Thể thao, EPG bar/Mini-Guide IPTV, phụ đề trên OSD bar, chuyển tab
bằng D-pad. Chất lượng cảm nhận trên những gì **đã chụp được**: tốt hơn
run #1 ở hero/nav (D8 lúc nghỉ, D17 gạch chân), còn 2 lỗi MEDIUM-LOW mới
(D22, D23) + các lỗi cũ D14/D8-cuộn/D17-chấm-đỏ; phần lớn câu hỏi QA-fix 2
đặt ra **vẫn chưa có câu trả lời** vì AI không đi tới các màn hình đó.

---

## 9. Vấn đề của harness (không phải lỗi app, nhưng quyết định lần chạy sau)

1. **AI kẹt trên một màn hình sau step 30 — bao phủ sụp đổ.** 97/127 bước
   (steps 31–127) chỉ đảo focus `heroPlay` ↔ `heroDetails` ↔ `cardRoot`
   trên màn hình Home/Thể thao, với cùng một mẫu phím UP/RIGHT/DOWN/LEFT
   lặp lại. AI không bấm OK lên nav, không mở tab, không vào player lần
   nữa, không mở dialog nào. Hệ quả trực tiếp: D19/D18/D12/D20 và 3 tab
   không được test — **không phải vì app chặn, mà vì AI không đi tới**.
   Mission sau nên ép: OK lên `nav_*` để chuyển tab thật (thay vì
   SWITCH_TAB của harness), ép mở player VOD + dialog cài đặt + episode
   picker, và ép BACK thoát dialog/player trước khi chuyển mission.
2. **Mission viết cho layout cũ, vẫn chưa cập nhật theo KL6.5** (như run
   #1 §9.1). Mission Home Hub vẫn đòi portal cards + logo Canva 3D (đã xóa
   ở Task 4); mission Sidebar Rail vẫn đòi left rail (đã xóa ở Task 3);
   mission IPTV/Schedule/Search/Settings đòi màn hình mà AI không mở.
   Lần này judge **không** ghi finding oan cho portal/rail (tiến bộ so với
   run #1), nhưng các mission đó vẫn "pass" trên giấy trong khi không test
   gì — xem #3.
3. **"Pass" lỏng lẻo + tab detector sai.** Chỉ **5/16 mission** kết thúc
   bằng COMPLETE_MISSION (steps 5, 13, 18, 22, 29); 11 mission còn lại
   kết thúc giữa chừng (SWITCH_TAB/timeout) nhưng vẫn tính pass, checks
   16/16. Summary ghi "Kho Phim 115 thao tác" trong khi AI ở màn hình
   Home/Thể thao; "Trực Tiếp 1 thao tác" dù AI ở màn hình Thể thao steps
   6–22; "Truyền Hình 1 thao tác" dù tab IPTV không mở (chỉ là focus
   `cardIptvRoot` trên hàng Home ở step_114); "Cổng Chọn 3 thao tác"
   trong khi Home Hub là màn hình AI ở gần như cả phiên.
4. **Video vẫn nén ~7,8x, thiếu đầu + cuối phiên (§3)** — lỗi recorder
   chưa được sửa dù đã thêm ffmpeg vào deps (lần thứ ba liên tiếp).
5. **Ảnh mission trùng lặp, nặng hơn run #1:** 16/17 trùng step shot
   (run #1: 12/17); 3 mission dùng chung một frame (§1, N17).
6. **Harness không chụp được đúng frame quan trọng nhất:** steps 27 và 28
   — hai step mang finding HIGH — đều `screenshot: null`. Finding HIGH
   mà không có ảnh thì không thể adjudicate bằng mắt; chỉ còn logcat +
   motion delta.
7. **Detector focus vẫn sai (như run #1 N14).** Timeline báo
   `has_focus_ring: False` ở steps 3–5 trong khi ảnh cho thấy viền trắng
   rõ quanh thẻ focus; `focused_view: NONE` ở steps 25–30 trong khi OSD
   đang hiện; và nhãn `heroPlay`/`heroDetails` gắn với focus trên nav
   (`step_031`: viền trắng quanh TRANG CHỦ nhưng timeline ghi
   `heroPlay#[208,0][654,97]`). Detector không đáng tin làm căn cứ chấm
   điểm hay đếm tab.

---

## 10. Sửa trước khi trình Evelyn / lần chạy sau? — Khuyến nghị

### Sửa ngay (nhỏ, sửa xong ảnh sẽ sạch hơn)

1. **D22 (MEDIUM-LOW) — cụm clock/date của hero khi cuộn.** Ngày "Thứ
   Hai, 09/11/2026" bị cắt nửa khi trượt dưới nav (`step_127`). Kiểm tra
   vị trí/clip của cụm clock trong trạng thái cuộn (giữ nó dưới nav hoặc
   cho nav che hẳn khi cuộn, thay vì cắt nửa chữ). Kiểm chứng bằng một ảnh
   hero ở trạng thái cuộn giữa chừng.
2. **D23 (MEDIUM-LOW) — nút back màn hình chi tiết phim đè logo.**
   Dời `btnHeroBackHome` khỏi vùng logo KENHLIVE (xuống dưới nav hoặc sang
   vị trí không chồng logo); kiểm chứng bằng một ảnh màn hình chi tiết.
3. **Finding #2 (LOW, REAL) — tên giải đấu dạng mã.** Dùng cùng nguồn tên
   đầy đủ như RoomPicker ("Bundesliga") cho thẻ trận: `POR D1` → tên đầy
   đủ, `HOL D1` → tên đầy đủ, `SPA D1` → tên đầy đủ… (mapping đã có sẵn
   một phần: `Serie A`, `Ligue 1` đã hiện đầy đủ trên thẻ).
4. **D8 ghost khi cuộn (đã để cho Evelyn ở fix 2, nhắc lại):** chấp nhận
   ghost mờ 10% của token `#E6141414`, hoặc đổi `kl3_nav_solid` thành
   `#FF141414` đục hoàn toàn (một token, giết ghost mọi nơi, lệch spec
   KL6.5 tr.3). `vf_004` là bằng chứng rõ nhất để Evelyn xem.

### Để Evelyn duyệt (quyết định thiết kế / điều tra thêm, không chặn review)

- **D17** — chấm đỏ sau "TRANG CHỦ" là gì (xuất hiện cả khi KHO PHIM đang
  được chọn, `step_036`)? Gạch chân đỏ thì nay đã thấy — chỉ còn chấm đỏ
  chưa có đáp án.
- **D14** — OSD Thể thao không focus được: thiết kế (OSD tự hiện, phím tác
  động trực tiếp) hay thiếu focus? VOD ở run #1 thì focus được, nên không
  đồng nhất — cần đáp án trước khi quyết sửa hay giữ.
- **N8** — dữ liệu (tỉ số 4:12, lượt xem nhảy 433,9K→437,0K): vấn đề phía
  nguồn dữ liệu, cần đối chiếu field nguồn trước khi sửa UI.
- **N15** — đồng hồ hero không đơn điệu (03:35→03:38→03:33): cần xem
  nguồn giờ của hero.

### Không cần full run lại để xác nhận D19/D18/D12 — cần test chủ đích

Full run #2 chứng minh AI tự do sẽ không đi tới các màn hình này. Thay vì
chạy lại full run và hy vọng, làm **một phiên test chủ đích ngắn** (hoặc
mission ép đường): (a) mở dialog cài đặt trong player VOD → DOWN từ chip
seek tới ĐÓNG (D19) → OK đóng; (b) mở CHỌN TẬP từ màn hình chi tiết phim
(D18) và từ trong player; (c) VOD bar: focus Settings → RIGHT ×2 tới Speed
→ RIGHT tới Lock (D12); (d) mở WebPlayer thật (D20); (e) mở tab IPTV +
lưới kênh (D4/D5); (f) mở tab Tìm kiếm/Cài đặt (D16); (g) LEFT/RIGHT ở
player Thể thao để kiểm tra gate ±30S; (h) BACK trong player (D15).
**Ưu tiên sửa mission map (§9.1–9.2) trước khi chạy lại, nếu không full run
sau sẽ lặp lại đúng mẫu này: AI loanh quanh Home và mọi mission vẫn "pass".**

### Không merge

Đây là full run #2. Branch `redesign/netflix` (head `309926e`) vẫn chờ
Evelyn duyệt APK + ảnh QA trước khi merge vào `main` — không merge, không
push thêm từ bài đánh giá này.

---

## 11. Tóm tắt: đã sửa xong vs run #1 / còn lại cho Evelyn

**Đã xác nhận sửa xong so với full run #1 (42511640281):** D8 lúc nghỉ
(badge row sạch khỏi nav), D17-gạch-chân (giờ thấy trên TRANG CHỦ cả khi
hero hiện), R1 (giữ nguyên), D1/D2/D6-D10 (giữ nguyên).
**Còn lại, thấy rõ trên màn hình:** D8 khi cuộn (ghost 10% + D22 mới),
D14, D17-chấm-đỏ, **mới:** D22 (ngày hero cắt nửa khi cuộn), D23 (nút
back chi tiết phim đè logo).
**Chưa có kết luận (cần test chủ đích, không phải full run lại):** D19,
D18, D12, D11, D13, D7-phụ-đề, D15-trong-player, D4/D5, D16, D20,
gate seek Thể thao, EPG bar/Mini-Guide IPTV, chuyển tab bằng D-pad.
**Điểm số:** 66/100 của judge gồm 2 HIGH trùng nhau cho 1 sự kiện codec
thoáng qua đã tự hồi phục (environmental, §2) + 2 LOW (1 logcat-only, 1
REAL là tên giải dạng mã); khử artifact thì thang judge cho ~96/100 —
nhưng thang đó không chấm các lỗi thật liệt kê trên, và lần này bao phủ
thực tế hẹp hơn run #1 rất nhiều (AI kẹt trên màn hình Home sau step 30).
Chất lượng trên những gì đã chụp được tốt hơn run #1; nhưng **QA-fix 2
chưa được kiểm chứng runtime ở cả 4 mục** — D19/D18/D12 là NOT OBSERVED,
chỉ D8 lúc nghỉ là FIXED có bằng chứng.

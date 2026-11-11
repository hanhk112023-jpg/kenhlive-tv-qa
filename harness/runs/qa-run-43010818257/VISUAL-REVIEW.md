# CI-T5 Eye Review — run 43010818257 (main @bd6186d, full 17 missions)

QA 843s (14m03s), 79 bước, 12/17 PASS, 0 UNVERIFIED, điểm 65/100, verdict
NEEDS_FIX. NIM 8 requests, 0×429, provider OPENAI (vision 8 calls:
confirm_target 4, stuck_assist 2, check_visual 2; 71.6s, latency TB 8.9s).
Video 700.5s ghi được / 843s chạy (83%, 4 chunk) → tour 175.2s @4x.
Reel 12.83s. Timelapse 17.6s. Observe 410s, per-step p50 3.7s / p95 18.5s /
mean 4.87s, `ocr_skipped_frames` 0.
Đã xem: cả 32 shot trong `shots/` + 5 frame video (tour t=5/90/170,
reel t=2/9/12) + 2 crop phóng to (step_010 "Xem ngay", step_063 title)
+ `qa_report.json` + `qa_session.json` (timeline 79 entries) +
chạy lại `realtime/mock_test.py` độc lập: EXIT=0, 24/24 `_OK`, không
Traceback/AssertionError.

## 1. Sửa CI-T5 — kiểm chứng bằng mắt

| # | Sửa CI-T5 | Kết quả mắt |
|---|---|---|
| 1 | Fake-score theo môn | ✅ **CHẠY ĐÚNG.** Không còn FP tỉ số bóng rổ: 79:52 (step_004) → 81:56 (step_026/029, đang tick), 5:7, 4:4, 1:6 → 1:7 (Vissel tick) — tỉ số bóng rổ thật không bị tố. Bóng đá 4:1, 5:0, 0:0 bình thường. |
| 2 | Motion fallback pixel_diff + UNKNOWN không tính kẹt | ✅ **CHẠY ĐÚNG.** VOD_PLAYER (CI-T4 FAIL oan) nay PASS — phim phát thật, native player tới 02:08 (tour_170). Không còn FAIL kẹt oan do motion None. |
| 3 | Driver chỉ mở thẻ LIVE | ⚠️ **MỘT NỬA.** PLAYER_STREAMING không còn kẹt A-B-A-B (fail bằng lý do khác — vision không xác nhận, xem §4). NHƯNG step_015 (ROOM_PICKER) vẫn mở thẻ [SẮP ĐÁ] INTERF 19:00 → player "Đang tải luồng…" vô hạn + tiêu đề "null · VIE - CHI" (xem §6). Luật LIVE-only chưa bao phủ ROOM_PICKER. |
| 4 | Cuộn lên đầu (UP ×8) đầu mission list | ✅ **CHẠY ĐÚNG.** DATA_ACCURACY + SCHEDULE_EPG đều PASS (CI-T4 FAIL 'hôm nay'): header "Hôm nay" hiện rõ ở step_016/018/031/032, tỉ số thật 4:4/1:6/5:7. |
| 5 | Gate: motion chỉ tính ở đúng activity | ⚠️ **KHÔNG KIỂM ĐƯỢC ĐẦY ĐỦ.** IPTV_EPG PASS nhưng vẫn "mềm" (xem §3): step_051 player đang loading, không thấy EPG thật trong frame; bằng chứng motion không đọc được từ ảnh. Không có PASS oan kiểu cũ, nhưng tiêu chí gắn activity chưa được chứng minh bằng mắt. |
| 6 | Hero OCR mỗi 2 lần due + đo fallback | ✅ **TỐC ĐỘ ĐẠT.** QA 1534s → 843s (−45%), observe p50 3.7s (CI-T4: dump p90 21.5s). Detect không còn là nút thắt. |
| 7 | Vision check hero + title player (2 call/run) | ❌ **CHẠY NHƯNG BỎ SÓT ĐÚNG LỖI NÓ CẦN BẮT.** 2 call `check_visual` không sinh finding nào, trong khi tiêu đề WebPlayer đè đôi HIỆN RÕ ở step_063/066/067 (xem §6.1, đã phóng to crop). Hero clock đè phụ đề thì KHÔNG tái hiện ở T5 (tour_005 sạch — xem §6.3). |
| 8 | Giữ chunk cuối đang quay dở | ⚠️ **MỘT NỬA.** Chunk cuối đã finalize + kéo về, NHƯNG normalize vẫn loại vì `moov atom not found` → video vẫn 83% (T4: 80%). Hệ quả: reel entry 3 (video_t 177.6s) VƯỢT tour 175.2s → đoạn 3 chỉ còn ~0.8s (xem §5). |
| 9 | Đi tới view đích theo id + phân biệt OK-dialog/player | ✅ **CHẠY ĐÚNG.** EPISODE_PICKER PASS (CI-T4 FAIL): dialog CHỌN TẬP mở đúng, đủ Tập 1–8 + PHÁT/LƯU PHIM/ĐÓNG (step_059). ROOM_PICKER FAIL với đúng lý do "OK mở PLAYER thay vì dialog đích" — fail trung thực, không PASS oan. |
| 10 | LONG_PRESS cho IPTV favorites | ⚠️ **KHÔNG KIỂM ĐƯỢC LIVE.** Mock PASS, nhưng không mission nào trong run bấm long-press thật (IPTV_CATEGORIES FAIL ở bước tìm text 'tv360' trước khi tới favorites). |
| 11 | Vision retry lỗi transport (ngoài danh sách) | ✅ Replay R6 giữ 8/8 P0 sau fix; CI-T5 NIM 8 requests, retries 0, 0×429 — không kích hoạt lỗi transport lần này, không đếm sai. |

## 2. Findings — 1 thật / 1 giả / 1 chưa xác nhận (precision 1/3, CI-T4 là 1/2)

1. **`66 kênh` (step_049) — THẬT.** Header "Địa Phương — 66 kênh" thấy rõ
   góc dưới phải (reel_009 cũng khớp). Cùng lỗi từ CI-T3/CI-T4, vẫn còn.
2. **`Chữ 'Xem' đè lên 'ngay' (chồng 93%)` (step_010) — FALSE POSITIVE,
   loại MỚI.** Crop phóng to 3× cho thấy pill đỏ ghi "Xem ngay" sạch,
   trắng trên đỏ, không chồng chữ nào. Detector tách 1 text thành 2 box
   ("Xem" trong "ngay") rồi tố chồng nhau. Đây là HIGH giả thứ 3 liên tiếp
   theo vòng: CI-T3 tố đồng hồ, CI-T4 tố tỉ số bóng rổ, CI-T5 tố 1 chữ
   bị tách đôi. Tiêu chí "0 HIGH FP" CHƯA ĐẠT.
3. **`Nghi vấn kẹt Focus` (step_075) — CHƯA XÁC NHẬN, gần như giả.**
   Step_075 và step_076 là 2 file JPEG có sha256 GIỐNG HỆT nhau
   (1 lần quan sát bị chụp trùng), và tới step_081 focus ĐÃ di chuyển
   (phím 'z' → phím '▶' trên bàn phím). Bàn phím đang mở, focus trên
   phím là trạng thái hợp lệ; detector nổ chỉ vì 1 lần quan sát không
   đổi. Không tính là lỗi app thật.

## 3. 12 PASS — đều thật (0 false pass), 1 PASS "mềm" cần ghi nhận

- Thật chắc: COLD_START (004, Home sạch, tỉ số thật 79:52), DATA_ACCURACY
  (016/018, "Hôm nay" + tỉ số thật), HOME_BILLBOARD (026/029, ĐANG PHÁT
  37 trận, tỉ số tick 79:52→81:56), SCHEDULE_EPG (031/032), PHIM_NGUONC
  (055, hero phim thật, đủ nút PHÁT/CHỌN TẬP/LƯU PHIM), EPISODE_PICKER
  (059, dialog Tập 1–8 thật), VOD_PLAYER (061→063, native loading rồi
  phát; tour_170: 02:08/1:03:15 đang chạy thật), WEBPLAYER_DIRECTED
  (066/067, WebPlayer OSD + seekbar 00:20 + TỐC ĐỘ 1X), PLAYER_SETTINGS_DIALOG
  (071, dialog Cài Đặt sạch, 01:49/1:03:35), SEARCH_AND_SETTINGS (075/076,
  43 kết quả), STRESS (081, app còn foreground, focus di chuyển được).
- IPTV_EPG PASS — **mềm**: player mở được thật (VTV Cần Thơ #05,
  tour_090; 360 Hoa Ngữ #37, step_051) nhưng frame step_051 chỉ thấy
  "Đang tải luồng…", không thấy nội dung EPG/Mini-Guide nào; step_052
  đã quay về list (player tự thoát). PASS về đích "mở được player" là
  thật, bằng chứng EPG thì không đủ.

## 4. 5 FAIL — phân loại

| Mission | Lý do | Mắt thấy gì | Loại |
|---|---|---|---|
| SPORTS_MULTI_SOURCE | thiếu text 'socolive' (8 bước) | Tab Trực tiếp hiển thị tốt, tỉ số thật; hero subtitle ghi "BLV [ColaTV] BLV ROCKSTAR" (tour_005), card chỉ ghi nhãn "COLA"/"SOCO" — text 'socolive' có thể không tồn tại trên màn hình | Harness (spec): mục tiêu text không khớp thực tế |
| ROOM_PICKER | "OK mở PLAYER thay vì dialog đích" | Step_015: player mở cho trận INTERF [SẮP ĐÁ] 19:00, "Đang tải luồng…" + tiêu đề "null · VIE - CHI" — fail đúng lý do (mục 9 chạy đúng), nhưng driver vẫn mở thẻ SẮP ĐÁ (mục 3 chưa bao phủ mission này) | Harness (phạm vi mục 3) + app (null title, loading vô hạn — xem §6) |
| PLAYER_STREAMING | vision 2 lần không xác nhận 'PlayerActivity đang phát video bóng đá thật' | Step_021/024: driver vẫn ở MainActivity (tab Trực tiếp), CHƯA BAO GIỜ vào player — vision từ chối đúng | Harness: driver không vào được player (cần luật goto-player như mục 9) |
| NAV_RAIL | thiếu view railPanel (7 bước) | Step_036/039: DPAD_LEFT đưa focus về nav_home, rail không mở lần nào — lỗi app còn từ KL8 audit | App (rail không mở) |
| IPTV_CATEGORIES | thiếu text 'tv360' (10 bước) | Tab IPTV hiển thị tốt, EPG thật (step_041: VTV Cần Thơ đúng logo VTV — P0-8 ✅; step_046: 360 Bundesliga/C1/C2). Nhưng 'tv360' chỉ tồn tại dạng ẢNH logo + chip bị cắt còn "T" — không có text 'tv360' trong dump | Harness (spec): mục tiêu text không tồn tại dạng text |

## 5. Tốc độ + video — nhanh hơn, video vẫn thiếu

- QA 843s (14m03s): nhanh hơn T4 (1534s) 45%, nhanh hơn T3 (1019s),
  dưới mục tiêu 30 phút với biên lớn. Observe 410s (p50 3.7s, p95 18.5s).
- Video: 700.5/843s = 83% (T4: 80%). Tour 175.2s @4x xem được đủ
  (tour_005 hero sạch, tour_090 Zapper, tour_170 native đang phát 02:08).
- Reel 12.83s: entry 1 (video_t 18.3) + entry 2 (100.7) khớp đúng nội
  dung (reel_002 = step_010, reel_009 = step_049). **Entry 3
  (video_t 177.6s) VƯỢT tour 175.2s** → đoạn 3 chỉ còn 0.6s
  (177.6−3=174.6, tour hết ở 175.2; reviewer trích reel t=12.5s thấy
  thoáng màn Tìm kiếm + bàn phím — đoạn 3 CÓ tồn tại nhưng không đủ 6s);
  reel_012 (t=12s) vẫn là frame IPTV của entry 2. Reel liệt kê 3
  finding nhưng chỉ 2 đoạn xem được trọn — tiêu chí "reel khớp report"
  CHỈ ĐẠT MỘT NỬA. Gốc rễ vẫn là chunk cuối mất (mục 8).
- Shot trùng lặp: 3 cặp JPEG sha256 giống hệt nhau (011=012, 055=056,
  075=076) + 063/066/067 cùng 1 frame video đứng yên 00:20 + 031≈032.
  Runner chụp trùng quan sát không đổi — phí bước, không phải lỗi app.

## 6. Lỗi app thật bị bỏ sót (không có trong findings)

1. **WebPlayer: tiêu đề đè đôi — CÒN NGUYÊN từ CI-T3/CI-T4, và vision
   check (mục 7) ĐÃ BỎ SÓT.** Step_063/066/067 + crop phóng to 2×:
   dòng 1 "Tình Yêu Trong Vỏ Bọc / Tình Yêu Ngụy Trang" bị dòng 2
   "Tình Yêu Ngụy Trang (2026) · Tập 01" đè lên cùng baseline, chữ
   chồng nhau không đọc được. Player native thì tiêu đề 1 dòng sạch
   (step_061, tour_170). Đây là lỗi HIGH thật mà harness 3 vòng liên
   tiếp không bắt được bằng detector nào.
2. **Player native: tiêu đề "null · VIE - CHI" (step_015).** Tên đội
   hiển thị literal "null" — lỗi dữ liệu/hiển thị thật, mới thấy lần đầu
   (trận INTERF [SẮP ĐÁ] 19:00). Kèm theo: trận chưa đá mở player
   → "Đang tải luồng…" vô hạn (cũng gặp ở step_051 IPTV: VTV Cần Thơ /
   360 Hoa Ngữ loading rồi player tự thoát về list ở step_052). App nên
   báo "chưa bắt đầu" / lỗi luồng rõ ràng thay vì loading rồi thoát lặng.
3. **Hero: giờ đè phụ đề — KHÔNG TÁI HIỆN ở T5.** Tour_005 (tour t=5s)
   hero sạch: đồng hồ "18:22" góc phải, ngày "Thứ Tư, 11/11/2026" bên
   dưới, phụ đề "Trực tiếp • Giải bóng rổ nam Hàn Quốc • BLV [ColaTV]…"
   bên trái — không chồng nhau. Vision check cũng sạch. Có thể đã hết
   hoặc tùy trạng thái hero; cần TV thật kiểm lại, không kết luận đã sửa.
4. **Hàng "Địa Phương — 66 kênh"** (finding thật, §2.1) + **rail không
   mở bằng DPAD_LEFT** (§4) — còn nguyên.
5. Ghi nhận, không tính finding: chip danh mục IPTV thứ 4 chỉ hiện "T"
   (step_041/046/049/052 — hàng chip cuộn ngang, chip "TV360" bị cắt ở
   mép); poster phim "Cheat-Granting Mage" có chữ tiếng Anh cháy sẵn
   trong ảnh (không phải lỗi app).

## 7. Điểm số

65/100 = 100 − 2×12 (2 HIGH) − 5 (1 MEDIUM) − round(5/17×20)=6.
Số học đúng. Nếu bỏ HIGH giả "Xem ngay": 77/100. Nếu bỏ thêm MEDIUM
chưa xác nhận: 82/100. Dù bỏ cả 2 FP, verdict vẫn NEEDS_FIX
(5 mission FAIL + 1 HIGH thật 66 kênh).

## 8. Kết luận cho switch-over

**CHƯA SWITCH ĐƯỢC (NEEDS-CI-T6).** Tiêu chí SWITCHOVER.md:
- Tốc độ <30p ✅ (QA 14m03s) · 0 false pass ✅ · WebPlayer ✅ ·
  NIM ✅ (8 req, 0×429) · frame evidence ✅ (17/17 mission đều có
  frame trên đĩa) · reel ⚠️ MỘT NỬA (2/3 đoạn xem được; entry 3
  vượt tour)
- **0 HIGH false-positive ❌** (1 HIGH giả: "Xem ngay")
- **Eye check khớp report ❌** (WebPlayer đè đôi tiêu đề còn nguyên
  mà không có trong findings; vision check bỏ sót đúng lỗi nó cần bắt)

## 9. Danh sách sửa CI-T6 (đề xuất)

1. **Text-overlap detector:** chỉ tố khi 2 box là 2 text KHÁC NHAU từ
   2 phần tử khác nhau — bỏ qua khi 1 box là chuỗi con của box kia
   ("Xem" trong "ngay") hoặc 2 box cùng 1 dòng OCR. Thêm regression
   test bằng frame step_010.
2. **Vision check hero/title:** debug vì sao 2 call check_visual trả
   sạch dù tiêu đề đè đôi hiện rõ — kiểm tra crop có đúng vùng title
   không, prompt có hỏi rõ "có 2 dòng tiêu đề chồng nhau không" không.
   Thêm regression test bằng frame step_063 (phải tố được).
3. **Video chunk cuối (moov):** chờ finalize tới khi ffprobe thấy moov
   (không chỉ size ổn định 2 lần đọc); hoặc giữ quay tới khi moov ghi
   xong mới dừng. Mục tiêu độ phủ >95%.
4. **Reel:** bỏ/kẹp entry có video_t vượt độ dài tour; báo rõ "reel
   cover x/3 finding" trong report; hoặc dựng reel từ chunk thô để
   finding cuối vẫn có đoạn xem được.
5. **Spec IPTV_CATEGORIES + SPORTS_MULTI_SOURCE:** kiểm tra text mục
   tiêu có tồn tại thật không ('tv360' chỉ là ảnh logo; 'socolive' chỉ
   có "COLA"/"SOCO" + "BLV [ColaTV]") — đổi mục tiêu sang tín hiệu
   kiểm chứng được, hoặc ghi rõ mission không PASS được bằng text.
6. **Mở rộng luật LIVE-only (mục 3) sang ROOM_PICKER** và mọi mission
   mở player; SẮP ĐÁ không được mở player.
7. **PLAYER_STREAMING:** thêm luật goto-player bằng id như mục 9
   (mở thẻ LIVE rồi xác nhận player), thay vì lang thang ở list.
8. **Focus-trap detector:** chỉ nổ khi focus đứng yên ≥2 quan sát
   KHÁC NHAU và không có bàn phím đang mở; 1 lần chụp trùng không
   tính.
9. **Shot trùng lặp:** bỏ qua/không lưu shot khi hash frame không đổi
   so với quan sát trước (tiết kiệm bước + dung lượng).
10. **App (không phải harness — ghi cho fix loop):** WebPlayer đè đôi
    tiêu đề; title "null · VIE - CHI"; trận chưa đá mở player loading
    vô hạn rồi tự thoát; rail không mở bằng DPAD_LEFT; hàng 66 kênh.

## 10. Bổ sung sau review độc lập (reviewer tự kiểm từ file gốc, coordinator tự crop xác nhận lại)

- **CI-T6 mục 1 trong §9 SAI cách diễn đạt — đã sửa trong DESIGN.md §15.7.**
  Guard chuỗi con như viết ban đầu không bắt được case "Xem"/"ngay"
  (`"Xem" in "ngay"` = False, đã kiểm bằng code). Guard đúng: box nhỏ
  ≥~90% nằm trong box lớn + cùng baseline/dòng OCR, và/hoặc gộp các box
  cùng 1 dòng OCR thành 1 cụm trước khi so chồng. Gốc rễ: `ocr.py
  read_boxes` (PSM 11) không khử trùng.
- **WEBPLAYER_DIRECTED PASS yếu — phim có thể chưa hề phát.**
  Step_063/066/067 đều đóng băng đúng 00:20/01:05:24 với overlay nút ▶
  lớn (trạng thái paused), qua 3 quan sát thời gian phát không nhích.
  PASS chỉ dựa trên "OSD + seekbar 00:20 + TỐC ĐỘ 1X". Đối chiếu: VOD
  native có bằng chứng 02:08 đang chạy thật (tour t=170s). CI-T6 phải
  yêu cầu bằng chứng thời gian phát tăng giữa 2 quan sát cho mọi mission
  player PASS.
- **Logo player SAI — MỚI, đã xác nhận bằng crop 4×.** Kênh 37 "360 Hoa
  Ngữ": ở list logo là "TV360" (step_049/052), nhưng trong player header
  (step_051) logo đọc rõ là **"BOX MOVIE"** (trắng/tím trên nền đen).
  Lỗi logo sai họ P0-8, harness không bắt.
- **Spinner loading đè nút ▶ PHÁT — MỚI, đã xác nhận bằng crop 3×.**
  Step_015: spinner nằm đè lên viền trên của nút PHÁT, text "Đang tải
  luồng…" đè lên viền dưới của nút — 3 lớp chồng nhau ở trạng thái
  loading của player.
- **"Về trực tiếp" kề "TRỰC TIẾP" — KHÔNG phải lỗi.** Crop 2× step_015
  cho thấy có khe hở giữa pill và chữ, chỉ là khoảng cách hẹp.
- **Timeline thiếu step_id 14.** `qa_session.json`: 79 entry, step_id
  1–80 thiếu đúng số 14 (đã kiểm bằng code). `timings.steps=79` khớp số
  entry nên là lỗ ghi log, chưa rõ nguyên nhân — cần điều tra.
- **Nhãn provider gây nhầm.** `nim_usage.provider` trong report là
  "OPENAI", không phải NVIDIA NIM — "NIM 8 requests" là tên bucket
  trong report; ghi rõ provider khi đối chiếu quota.
- **Lưu ý switch:** `video_recorder.py` dùng chung với harness cũ — thay
  đổi CI-T5 ở file này có thể ảnh hưởng đường cũ, kiểm trước switch.


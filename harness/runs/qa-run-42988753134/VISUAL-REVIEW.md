# Eye-review — CI-T3 main run 42988753134 (2026-11-11)

Run: QA-Realtime-Trial trên main@aec0695 (KL8 + fix loop 2 F62–F67 + QA realtime).
Workflow 08:39:20 → 09:01:16 UTC (~22 phút). QA 1019s (16m59s), 90 bước.
Report: 10/17 PASS, 0 UNVERIFIED, điểm 32/100, verdict NEEDS_FIX (trung thực).
NIM 5 requests / 30-phút, 0×429. Vision 4 calls (confirm_target), latency TB 22.5s.
Video: 904s ghi được (6 chunk chuẩn hóa) → tăng tốc 4x thành 226s (đủ cả run, tua nhanh).
Độ phủ video 904/1019s = 89%. Build APK merge 42988749595 SUCCESS.

Đã xem: video (5 frame trích: v_5/v_50/v_110/v_170/v_220) + defect reel (3 frame)
+ TẤT CẢ 28 ảnh shots/ + 6 frame reel. Không tin điểm số, chỉ tin mắt.

## Kết luận nhanh
- **0 false pass.** Cả 10 PASS đều có bằng chứng thật, đã kiểm bằng mắt.
- **Findings: 1 thật / 4 giả** (5 HIGH của harness). Tỉ lệ false positive 80%.
- **Bỏ sót 3 lỗi app thật** (mắt thấy, harness không báo).
- **Video đủ cả run** (lần đầu tiên kể từ khi làm QA mới) nhưng là bản tua 4x;
  **defect reel SAI thời gian** (dùng giờ thật cắt vào video 4x — 3/5 đoạn rơi
  ngoài file, 2 đoạn còn lại lệch nội dung). Lỗi harness, phải sửa.
- **6 frame bằng chứng của mission FAIL còn thiếu** (chỉ PASS được lưu đủ).

## Từng finding của harness (5 HIGH)
| # | Finding | Mắt thấy | Kết luận |
|---|---|---|---|
| 1 | Chữ đè chữ top nav: 'LPđPfUHPBIHUALI' vs 'đ114áI' (93%), step_022 | Step_022: hero NBL, tiêu đề "National Basketball League (Australia)" bị cắt trái, không có chữ nào đè nhau. 'LPđPfUHPBIHUALI' là OCR đọc nhầm chữ tiêu đề hero (chữ lớn, nền tối). Không có overlap thật. | **GIẢ** — OCR hallucinate chuỗi rác dài, qua được guard `_plausible_text` (đủ chữ cái). |
| 2 | Tỉ số phi lý '15 : 11', step_003 | Step_003: hero Philippines 0:0, card VS — KHÔNG thấy '15 : 11' đâu. Giá trị này xuất hiện ở step_027 trên card thứ 3 ("South... 15 : 11") — là **đồng hồ trận đấu** (phút:giây), tăng dần 15:11 → 17:23 (step_036) → 20:25 (step_063). | **GIẢ** — đồng hồ, không phải tỉ số; frame trích dẫn không chứa giá trị bị tố. |
| 3 | Tỉ số phi lý '17 : 23', step_027 | Step_027: card thứ 3 ghi '15 : 11', không phải '17 : 23'. '17 : 23' là đồng hồ của card khác (ngoài màn hình) hoặc ở bước sau (step_036 mới thấy 17:23). | **GIẢ** — đồng hồ; frame trích dẫn sai giá trị. |
| 4 | Tỉ số phi lý '23 : 28', step_063 | Step_063: card thứ 3 ghi '20 : 25' (đồng hồ đã chạy tiếp). | **GIẢ** — đồng hồ; frame trích dẫn sai giá trị. |
| 5 | Hàng '66 kênh' quá tải, step_048 | Step_048: đúng có header "Địa Phương — 66 kênh". Hàng chứa 66 kênh, vượt ngưỡng 30 của luật P0-7. | **THẬT** (cùng họ với P0-7 cũ, nay là hàng Địa Phương). |

Nguyên nhân chung #2/#3/#4: detector tỉ số đọc cả node ngoài màn hình (dump không
lọc bounds) + không phân biệt đồng hồ trận đấu (MM:SS, tăng theo thời gian) với
tỉ số. Cách sửa: chỉ tố giá trị (a) có bounds trong viewport và (b) ổn định
qua 2 lần thấy (đồng hồ đổi mỗi lần, tỉ số giả đứng yên).

## Lỗi app thật mà harness BỎ SÓT (mắt thấy)
1. **Hero Sports: đồng hồ "15:44"/"15:45" đè lên dòng phụ đề hero**
   (step_006, step_016 — ổn định, không phải thoáng qua): "BLV [ColaTV] BLV
   MONSTER · Tín hiệu HD" bị chữ giờ đè lên "MONSTER/POCARI". Harness không soi
   vùng hero (OCR chỉ band nav + band dưới; vision không check hero).
2. **Schedule: 2/4 hàng LIVE hiện giờ đá (15:00) thay vì tỉ số** (step_021,
   step_031, step_033 — ổn định qua 3 bước): Maldives U17 vs Hong Kong U17 và
   Mongolia U17 vs Yemen U17 có pill Live nhưng cột trái ghi 15:00 (giờ đá),
   trong khi Guam 0:8 và Cambodia 0:0 hiện tỉ số thật. Thiếu dữ liệu tỉ số
   trên Schedule (họ F62).
3. **WebPlayer: tiêu đề phim bị đè đôi** (step_073/076/077): "Pháp Sư Gian Lận
   Bị Sa Thải Tận Hưởng Cuộc Sống Thứ Hai" in chồng lên "(2026) · Tập 01" —
   hai lớp tiêu đề chồng nhau ở đầu màn hình WebPlayer.
4. (Nghi vấn, chưa kết luận) Hero NBL: tiêu đề "National Basketball
   League (Australia)" bị cắt trái + card hero cũng cắt ("ational Basket...") —
   thấy ở step_022 và video v_50 (cùng thời điểm). Có thể là rail cuộn ngang
   làm tiêu đề trôi khỏi màn hình; cần xem video chuyển động mới kết luận.

## Đã xác minh là SỬA ĐÚNG trên main (fix loop 2)
- **P0-8 logo**: VTV Cần Thơ hiện logo VTV đúng (step_041), không còn ANTV.
- **F62 Home**: card ĐANG PHÁT hiện tỉ số thật 0:0 sau khi load (step_004, 027,
  036). Lúc mới mở vẫn thấy VS vài giây đầu (step_003, 011) — data load chậm,
  không phải mất hẳn.
- **F63 WebPlayer OSD**: mở được, seek +10s chạy (00:10 → 00:20, toast
  "Tua tới 10s", step_073→076), hiện "TỐC ĐỘ 1X", video phát thật
  (motion 28.23/12.30/7.68). Đây là lần đầu WebPlayer được xác minh đầy đủ.
- **Settings dialog** (step_081): sạch, đủ mục, nút ĐÓNG rõ.
- **Search** (step_085/091): sạch, 37 kết quả, LIVE đúng.
- **IPTV EPG thật** (step_051): Vietnam Today HD, CHINA LINK 15:30-16:00,
  lịch phát sóng hôm nay đầy đủ.
- **Navigation reset chạy**: 10/17 PASS (từ 4/17 ở CI-T2); các mission trước
  FAIL vì kẹt PlayerActivity nay PASS (HOME_BILLBOARD, SCHEDULE, PHIM_NGUONC,
  SEARCH, DATA_ACCURACY). Không còn mission nào FAIL chỉ vì "missing MainActivity".

## 7 mission FAIL — phân tích thật
- SPORTS_MULTI (socolive text): không tìm thấy text 'socolive' trong 8 bước.
  Cần xem dump: có thể tên nguồn đã đổi hoặc nằm ngoài viewport.
- SPORTS_ROOM_PICKER (no dialog): agent bấm OK lên card phòng → vào thẳng
  PlayerActivity (step_14/17) thay vì mở dialog chọn phòng BLV. Driver chưa
  phân biệt "mở dialog" với "mở player".
- PLAYER_STREAMING (vision 2 lần từ chối): player mở 2 lần (step_23/25) nhưng
  đều đang "Đang tải luồng..." lúc vision check (motion 0.00). Tuy nhiên reel
  cho thấy trận bóng rổ NBL ĐÃ PHÁT thật trong run (scoreboard 15-13,
  "Hiệp 1: 15'") — stream không chết, mission chỉ check quá sớm / không chờ
  video lên. Motion PlayerActivity = 0.00 ở cả 11 bước lấy mẫu — tín hiệu
  motion trên native player không đáng tin (lấy mẫu thưa).
- SIDEBAR_RAIL (railPanel): view railPanel không xuất hiện trong 7 bước.
- IPTV_CATEGORIES (tv360 text): không thấy 'tv360' trong 10 bước (grid hiện
  tên kênh, không có chữ TV360 trừ logo).
- IPTV_EPG (motion): player Vietnam Today HD vẫn "Đang tải luồng..."
  (step_056) trong cả 7 bước; trial run cùng mission PASS 3 bước — flaky
  (mạng/emulator), không phải lỗi app xác định.
- EPISODE_PICKER (no dialog): focus nhảy qua lại btnHeroBackHome ↔ heroPlay
  (step_60-68), màn hình không đổi qua 3 bước (step_060/061/066 giống hệt
  nhau) mà detector kẹt không kích hoạt (luân phiên A-B-A-B không tính là
  "không đổi"). Driver không xuống được nút CHỌN TẬP để mở dialog.

## Lỗi harness cần sửa (đợt sau — CI-T4)
1. **Defect reel sai 4x**: `judge.build_defect_reel` dùng `video_t` (giờ thật)
   cắt trực tiếp vào `full_qa_tour.mp4` đã tăng tốc 4x. 3/5 đoạn bắt đầu ngoài
   file 226s → rỗng; 2 đoạn còn lại lệch nội dung (reel 18.6s thay vì 30s).
   Sửa: truyền hệ số tốc độ (hoặc `recorded_seconds` vs duration cuối) vào
   judge, chia `video_t` cho hệ số; ghi hệ số vào report.
2. **Fake-score nhận nhầm đồng hồ trận đấu** (3 FP trên): chỉ tố khi giá trị
   có bounds trong viewport VÀ ổn định qua 2 lần quan sát (đồng hồ đổi liên
   tục, tỉ số giả đứng yên).
3. **Frame bằng chứng của mission FAIL còn thiếu** (6 cái: step_012/018/040/
   050/057/069): `_finish_mission` chỉ lưu frame khi PASS. Sửa: lưu frame
   cuối cho MỌI outcome khi evidence trích dẫn nó.
4. **Detector kẹt không bắt được luân phiên A-B-A-B** (EPISODE_PICKER): streak
   "không đổi" reset khi focus đổi dù màn hình không đổi. Sửa: tính kẹt theo
   hash ảnh/dump thay vì chỉ focused_sig, hoặc đếm số lần quay lại cùng một
   focus trong N bước.
5. **OCR overlap: chuỗi rác dài qua guard** (finding #1): `_plausible_text`
   chỉ đếm chữ cái — 'LPđPfUHPBIHUALI' qua. Cần thêm guard: tỉ lệ nguyên âm
   / từ trong từ điển / loại box nằm trên ảnh hero (không phải chữ UI).
6. **Motion native player không đáng tin**: player mission nên chờ motion rõ
   (poll tới 10s) trước khi gọi vision xác nhận "đang phát", thay vì kết luận
   ngay trên frame đang tải.

## Tốc độ
- QA 1019s (17 phút), cả workflow ~22 phút — **DƯỚI mục tiêu 30 phút** ✅.
- Observe: p50 3.65s (CI-T2: 13.46s), p95 23.03s, mean 5.94s.
  Breakdown: wait p50 1.21s (tổng 121s) / **dump p50 1.60s, p90 5.01s, max
  29.14s, tổng 321.7s (60% thời gian observe)** / detect p50 0.05s (tổng 55.8s).
  Nút thắt tiếp theo là **uiautomator dump** (đặc biệt trên player, max 29s) —
  muốn nhanh hơn nữa phải giảm số lần dump hoặc dump nhẹ hơn (không thêm bước).
- Vision: 4 calls, 90.0s tổng (đã sửa đúng — CI-T2 báo sai 7.7s).
- So baseline: cũ 74m26s → CI-T2 37m57s QA → **CI-T3 16m59s QA**.

## Run đối chứng (trial 42988508129, build cũ fix loop 1)
10/17 PASS, điểm 20, QA 1014s, 93 bước, NIM 5, 0×429, 6 findings (1 overlap
giống hệt + 3 tỉ số '9 : 6' kiểu đồng hồ + 2 hàng 106/66 kênh). IPTV_EPG PASS
3 bước nhưng VOD_PLAYER FAIL kẹt — ngược với main → motion/kẹt vẫn flaky,
không phụ thuộc build. Khác biệt đáng kể duy nhất: main PASS VOD_PLAYER +
IPTV_EPG FAIL; trial ngược lại. Cùng 10/17 cho thấy harness ổn định qua 2
build, còn lại là flaky theo thời điểm.

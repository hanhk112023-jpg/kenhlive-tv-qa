# KL8 Task 12 — Visual Review (by eye, không tin điểm judge)

- **QA run:** 42950738729, workflow QA-Suite, branch `redesign/apple-kl8`, HEAD `996c3d5`
- **Kết luận run:** SUCCESS, 1h14m26s (03:08 → 04:31 UTC, 10:08 → 11:31 VN), trong timeout 150 phút
- **Artifact:** `~/workspace/kenhlive-plan/qa-run-42950738729/` (11 MB; lần tải đầu lỗi timeout mạng, tải lại OK)
- **Phiên:** QA-SESS-20261111-031222-3ccd6e, 136 bước, 121 lần bấm D-pad, 0 crash
- **Judge claim:** 88/100, 17/17 checks pass, 3 findings (2 MEDIUM, 1 LOW)
- **Eye-verdict của tôi: ~70/100 — judge bị lạm phát.** 2 trong 17 check là **false pass** (xem P0-1, P0-2 dưới đây).
  Lịch sử: Evelyn đã dặn không tin điểm judge (98/100 thực chất ~70/100) — lần này cũng vậy.

## Phương pháp xem

- Xem full-size cả **18 mission shot** (`01`–`18`).
- Xem toàn bộ **136 step shot** qua 9 contact sheet 4×4 (mỗi ảnh 480×270, có nhãn số step).
- Xem **video** `full_qa_tour.mp4` qua 15 khung hình trích (timelapse 175s, 1 khung/12s) — nội dung video trùng với step shot, không có gì thêm.
- Đối chiếu từng phát hiện với `qa_session.json` timeline (136 entry, có `ui_state`/`focused_view`/`activity` từng bước) và `qa_report.json`.
- Không dùng điểm judge để kết luận bất cứ mục nào.

## P0 — chặn, phải vào vòng fix 1

### P0-1. Mission WebPlayer có định hướng KHÔNG HỀ chạm tới WebPlayer (check judge báo pass là SAI)
- Steps 96–102 (MISSION_WEBPLAYER_DIRECTED_REAL_FILM): activity vẫn là
  `PlayerActivity` (native) ở steps 96–101, rồi về `MainActivity` ở step 102
  (`COMPLETE_MISSION`). **Không có bước nào mở `WebPlayerActivity`, không có
  WebView, không có embed phim thật, không test phát/tạm dừng/tua/tốc độ web.**
- Agent tự kết thúc mission sau khi đóng dialog lỗi native (step 101 QUAY LẠI),
  thought ở step 102 tự nhận "đã hoàn thành việc kiểm tra WebPlayer" trong khi
  chưa mở nó lần nào.
- Đây là lần thứ 4 liên tiếp QA 0 bước WebPlayer (3 run Netflix trước đó cũng vậy).
- Nguyên nhân (suy từ timeline): `LAUNCH_VOD_PLAYER_DIRECTED` (step 115) mở
  **native player**, không mở web player; F44 deep-link `open=webplayer` chưa
  được làm (prep commit Task 12 không gồm nó). Mission có định hướng nhưng
  không có đường nào tới được WebPlayer.
- Fix: làm F44 (deep-link mở WebPlayer trực tiếp với 1 embed phim thật) HOẶC
  một entry có định hướng khác tới `WebPlayerActivity`; rồi chạy lại RIÊNG
  mission này để chứng minh web play/pause/seek/speed + probe F47
  (set-and-read-back). **Không có bằng chứng này thì Task 12 chưa đóng được.**

### P0-2. Mission Home Hub kiểm tra Tab 6 không còn tồn tại (check judge báo pass là SAI)
- Steps 32–41: `SWITCH_TAB(6)` thất bại 4 lần; tab rơi về index 5 (Kho Phim);
  agent lang thang nav rồi bỏ cuộc. Shot 07 (mission) giống hệt shot 02 (home).
- Lý do: Task 4 đã xóa Hub portal cards — Tab 6 Home Hub không còn tồn tại.
  Mission này lỗi thời, không phải lỗi app.
- Fix: bỏ/thay mission này bằng kiểm tra Home = billboard 60% + 6 hàng
  (đã thấy đúng ở shot 02), và sửa QA script để không tính pass khi không tới
  được tab đích.

### P0-3. Tiêu đề hero IPTV đè lên top nav (chữ chồng chữ)
- **Bằng chứng:** `step_065_mission_.jpg` = mission shot 10 (full-size đã xem):
  "VTV4 HD" đè lên "TRANG CHỦ / TRỰC TIẾP", "ĐÀI TRUYỀN HÌNH VIỆT NAM (VTV)"
  đè lên "TÌM KIẾM / CÀI ĐẶT". Nav trên màn IPTV gần như không đọc được.
- Khung hero kênh (VTV1/VTV10/VTV2/VTV3, steps 61–64) cũng đặt tiêu đề sát
  mép trên; riêng step 065/075 là chồng hẳn.
- Fix: hero IPTV phải có top inset/scrim để tiêu đề không leo lên vùng nav.

### P0-4. Nút "Về trực tiếp" ở player Thể thao bị cắt chữ
- **Bằng chứng:** `step_026_mission_.jpg` (full-size) + mission shot 06:
  hàng dưới chỉ hiện "TRỰC…" rồi bị cắt ở mép phải, "TÙY CHỌN" đè lên sau.
  Hàng dưới quá chật — đây đúng là lỗi đã thấy ở Netflix Fix 5 ("chữ TRỰC TIẾP
  bị cắt mép"), Task 9 chưa sửa dứt.
- Fix: cân lại hàng dưới Sport (bớt/chia nút, cho "Về trực tiếp" đủ chỗ).

### P0-5. Phụ đề VOD đè lên seekbar + hàng nút khi OSD đang hiện
- **Bằng chứng:** `step_091_mission_.jpg` (full-size): câu "Đâu óc bà đâu chỉ
  biết mỗi…" nằm NGAY TRÊN thanh seekbar (03:07 —○— 21:06), phần dưới bị
  hàng nút che. Shot 14 (mission): "Mình đang mặc bộ đồ…" cũng chồng lên
  hàng nút TẬP TIẾP / DANH SÁCH TẬP.
- Đây là họ F46 (anchor chưa tính OSD) nhưng ở mặt VOD, không chỉ mặt TV.
- Fix: khi OSD hiện, neo phụ đề lên trên seekbar + hàng nút (tính cả
  `tvBottomBar` ở mặt TV như F46 đã ghi).

### P0-6. Mất focus sau khi bấm BACK trong player IPTV
- **Bằng chứng:** `step_059_mission_.jpg` (full-size): sau BACK, thanh dưới
  hiện đủ 6 nút (Kênh trước / Kênh kế / EPG / Yêu thích / Tỉ lệ 16:9 / Cài đặt)
  nhưng KHÔNG nút nào có viền focus; timeline `ui_state.focused_view = NONE`.
  Đúng finding MEDIUM của judge (step 59) — lần này judge đúng.
- Fix: khi OSD ẩn/hiện lại sau BACK, trả focus về 1 control hợp lý
  (vd nút EPG hoặc nút đang dừng), không để NONE.

### P0-7. F21 tái hiện trên dữ liệu live: 1 hàng TV360 chứa 75 kênh
- **Bằng chứng:** steps 057/060/075–079, mission 10/12: header "TV360 — 75 kênh";
  hàng VTV (~11 kênh) rồi tới TV360 khổng lồ. Không thấy hàng HTV/VTC,
  VTVcab/SCTV, Địa phương ở phía trên.
- Fix theo ledger: đưa nhánh tên đài lên trước nhánh URL `tv360://` trong
  `rowTitleFor`, kèm unit test với dữ liệu fallback (86 kênh → nhiều hơn 2 hàng).

### P0-8. Logo kênh sai: card #05 hiện "ANTV" cho kênh VTV Cần Thơ
- **Bằng chứng:** steps 057/060/075–079, mission 12 (full-size step_057):
  ô logo ghi "ANTV" nhưng tên kênh là "VTV Cần Thơ". Các card #06 VTV1 HD,
  #07 VTV10 đúng logo. Lỗi nhất quán qua nhiều shot → không phải glitch
  viewholder nhất thời.
- Fix: kiểm tra mapping logo/fallback text của `ChannelBadge` cho kênh này.

## P1 — nên sửa ở vòng fix 1 nếu còn sức, hoặc vòng 2

### P1-1. DPAD_LEFT không mở được sidebar rail (lỗi cũ từ main, Task 3 chưa sửa)
- Steps 39–44, 48–54: DPAD_LEFT 2+ lần chỉ di chuyển focus trong tab, rail
  không mở; agent phải đi lên nav rồi DPAD_RIGHT lần lượt qua từng mục.
  Nếu KL8 cố tình bỏ rail (chỉ dùng top nav) thì đây không phải lỗi app mà
  là mission lỗi thời — cần quyết dứt khoát, giống P0-2.

### P1-2. Đồng hồ ngày/giờ trên Home đè lên nav
- Shots 02/07, steps 39–44: "10:12" đè lên "TÌM KIẾM", "CÀI ĐẶT" bị cắt ở
  mép phải. Chỉ xuất hiện ở màn Home (màn Cài đặt không có đồng hồ, nav sạch).
- Fix: chừa chỗ cho cụm đồng hồ hoặc dời nó khỏi vùng nav.

### P1-3. Dialog THÔNG BÁO lúc cold start: bấm OK 3 lần không đóng, chỉ BACK mới đóng
- Steps 1–3: OK không có tác dụng, focus = NONE khi dialog mở; step 4 (BACK)
  mới đóng được. Dialog không có nút đóng nhìn thấy được.
- Fix: cho dialog nút đóng hoạt động + focus ban đầu rõ ràng.

### P1-4. Tiêu đề Mini-Guide bị cắt: "Danh Sá…"
- `step_073_mission_.jpg`: header list kênh hiện "Danh Sá…" (chữ bị cắt ở mép
  panel). Nhỏ nhưng thấy rõ ở full-size.
- Nội dung Mini-Guide thì tốt: 6 hàng (03–08), logo + tên + EPG time,
  LIVE badge, preview video bên phải.

### P1-5. Native VOD lỗi giải mã lặp lại, nuốt ~20 bước QA
- Steps 99–101, 108–114, 116–122: `ERROR_CODE_DECODING_FAILED` lặp lại sau khi
  đã phát tới 14:15; thử lại (THỬ LẠI) rồi lỗi tiếp; mở lại tập từ đầu (00:03)
  rồi lỗi ngay. Judge cho là giới hạn emulator x86 (thiếu codec) — chấp nhận
  được về mặt nguyên nhân, nhưng: (a) nó chặn mission settings-dialog sau
  step 103, (b) chưa có bằng chứng nào trên máy thật. Cần xác nhận trên máy
  thật/TV thật trước khi kết luận "không phải lỗi app".

## P2 — hỏi Evelyn / quyết ở Task 12, không phải fix code ngay

- **Trận live không hiện tỉ số ở đâu cả (card, detail, schedule đều "VS"):**
  tất cả trận đang đá đều chỉ hiện VS, kể cả NBA 09:00. Nếu thiết kế là "tỉ số
  chỉ trong player" thì ổn; nếu card/detail phải có tỉ số live thì đây là
  thiếu dữ liệu/API. Cần Evelyn/coordinator xác nhận kỳ vọng.
- **Tên giải đấu tiếng Anh "AFC U17"** (finding MEDIUM của judge, step 23,
  RoomPicker "AFC U17 · 6 phòng live"): dữ liệu API trả về như vậy. Dịch tên
  giải ra tiếng Việt là việc mapping dữ liệu — hỏi Evelyn có làm hay chấp nhận
  giữ nguyên.
- **R7 — giữ row Mini-Guide 70dp, không thu về 48dp (khuyến nghị của tôi):**
  step_073 cho thấy 6 hàng vừa khung, đọc rõ; 8 hàng chỉ đạt được bằng cách
  thu nhỏ focus target — không đáng. "8 kênh = window" (R7) đã có scroll.
- **R8 — bar VOD 8 nút CHẤP NHẬN (đã kiểm bằng mắt):** steps 107–108 cho thấy
  bar scroll được, "TỐC ĐỘ 1X" hiện ra, "TUA -10S" cuộn khỏi. Đúng như R8 mô tả.
- **F45 chưa test được:** run chỉ mở tập 1 (không phải tập cuối) nên không thấy
  flash "Tập tiếp" lúc cold-open. Cần test riêng mở thẳng tập cuối.
- **F47 chưa test được:** WebPlayer chưa từng mở nên probe Speed web chưa được kiểm.
- **Resume ("TIẾP TỤC XEM") chưa test:** hàng "TIẾP TỤC XEM / 1 phim" có hiện
  (shots 15, 102, 115, 123) nhưng agent không bấm vào bao giờ; lần mở lại tập
  sau lỗi (step 116) bắt đầu từ 00:03 chứ không resume 14:15 (nhưng đó là bấm
  PHÁT ở hero, chưa chắc là đường resume). Cần 1 test resume đích danh.

## Những gì đã tốt (xác nhận bằng mắt)

- Home: hero 60% + ĐANG PHÁT + TRẬN SẮP DIỄN RA sạch; focus viền trắng rõ;
  countdown pill "Còn 4h 44p"; **0 tỉ số ảo ở mọi màn** (tất cả đều VS, luật
  plausibility giữ vững); "Mới Cập Nhật" đã thay "Thịnh hành" (pill ở shot 15).
- RoomPicker: 5–6 phòng BLV (ZIZOU, KENCHU, BLV Củ Cải, TẠ BIÊN GIỚI, …),
  badge SOCO, dialog sạch.
- Player Thể thao: video thật phát được (PHI–IND), motion rõ, pause/play
  hoạt động, toast "Đang kết nối lại luồng trực tiếp (Lần 3/3)…" (shot 06 là
  lúc reconnect, sau đó phát lại được ở steps 26–31).
- IPTV: lưới kênh + strip EPG có chương trình thật theo giờ; zap đổi kênh
  được (01/05/06/11), thông tin EPG trên player đúng; Mini-Guide hoạt động.
- Phim: detail đầy đủ (poster, thể loại, đạo diễn/diễn viên, tóm tắt),
  EpisodePicker Tập 1–6, nút PHÁT / LƯU PHIM / ĐÓNG.
- VOD native: phát được, seek chạy (01:31 → 03:07 → 05:04 → 08:33 → 14:15),
  TUA ±10s, nút TỐC ĐỘ 1X, dialog Cài đặt thống nhất 5 mục, còn lại 16:12
  (nhãn phải = thời gian còn lại, đúng Q3).
- Tìm kiếm: gộp 3 loại (trận + kênh), placeholder "Tìm trận đấu, kênh, phim,
  BLV…", trạng thái 0 kết quả trung thực ("0 kết quả cho 'uefa'").
- Cài đặt: sạch; Liên hệ & Báo lỗi mở đúng dialog Telegram QR.
- Chaos D-pad (steps 131–136): không crash, không đơ, app vẫn ở màn Cài đặt.
  (Số liệu RAM: không có con số trong artifact — "memory audit pass" của
  judge là claim chưa kiểm chứng được bằng mắt.)

## Trạng thái follow-up F21–F48 sau run này

| Mục | Trạng thái sau QA |
|---|---|
| F21 (TV360 75 kênh) | **Tái hiện, P0-7** |
| F22 (channelSub Home) | Không kết luận được từ ảnh (cần soi code ở vòng fix) |
| F23 (CW card thumbUrl) | Không có ảnh hàng CW nào — chưa test |
| F24/F45 (gate "Tập tiếp") | F24 xong ở Task 11; F45 chưa test (chưa mở tập cuối) |
| F26 ("Hot/Đặc Sắc") | Nhãn "ĐIỆN ẢNH ĐẶC SẮC" vẫn hiện ở hero detail phim — P2 |
| F27 (2 drawable chết) | Việc code, không xem được bằng mắt |
| F30 (search_idle) | Không thấy chuỗi cũ trong ảnh search — có thể đã xong, soi code ở vòng fix |
| F35/F38/F39/F40/F41 | Không kết luận được từ ảnh tĩnh |
| F36 (màu thanh gesture) | Chỉ có trên điện thoại — run TV không cover |
| F42/R8 (bar VOD 8 nút) | **Đã kiểm bằng mắt: chấp nhận, bar scroll được** |
| F43/R9 (không dialog resume chặn) | Không thấy dialog chặn nào — phù hợp R9; nhưng resume đích danh chưa test |
| F44 (deep-link open=webplayer) | **Chưa làm — là gốc của P0-1, cần quyết** |
| F46 (phụ đề + tvBottomBar) | Mở rộng: P0-5 (mặt VOD cũng bị) |
| F47 (probe Speed web) | Chưa test được (không có WebPlayer) |
| F48 (dialog audio/sub) | Dialog "Kênh âm thanh / Phụ đề" có mở được (step 94–95 focus vào mục này) nhưng nội dung numbering chưa soi kỹ — để vòng fix |

## Đề xuất vòng fix 1 (tối đa 3 vòng theo PLAN)

1. F44 + sửa mission WebPlayer có định hướng (P0-1) — rồi chạy lại riêng mission này.
2. P0-3 (hero IPTV đè nav) + P0-4 ("Về trực tiếp" bị cắt) + P0-5 (phụ đề đè seekbar) — 3 lỗi nhìn thấy rõ nhất.
3. P0-6 (mất focus sau BACK) + P0-7 (F21) + P0-8 (logo ANTV sai).
4. P1-1/P1-2/P1-3: quyết dứt khoát rail có còn không; sửa đồng hồ Home; sửa dialog THÔNG BÁO.
5. Dọn mission lỗi thời (P0-2) để lần QA sau không còn false pass.

## Kết luận

**Task 12 chưa đóng được.** Run SUCCESS về mặt kỹ thuật nhưng bằng chứng trực
quan cho thấy 2 check pass giả (WebPlayer chưa từng mở, Home Hub không tồn
tại), cộng 6 lỗi P0 nhìn thấy rõ. Cần 1 vòng fix + 1 lần chạy lại có định hướng
(ít nhất mission WebPlayer + các màn đã sửa) rồi mới báo cáo cuối cho Evelyn.
Không merge gì.

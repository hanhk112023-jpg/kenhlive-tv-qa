# Đánh giá trực quan (Visual Review) — QA run 42504300280 (quick)

**Nhánh:** `redesign/netflix` · **Commit:** `c4e14f8` · **Chế độ:** quick
**Kết quả job:** xem `qa_session_summary.md` · **Thời gian chạy:** 3967 s (~66 phút) · **Điểm:** 75/100
**Steps:** 128 · **Tabs:** 6/7 (Trực Tiếp 0 thao tác — chưa duyệt) · **Findings:** 3 (2 MEDIUM + 1 HIGH)
**Video:** `full_qa_tour.mp4` — 72 MB, **468,7 s** cho phiên 3967 s (xem §3)

**Phạm vi bài đánh giá này:** đã đọc trực tiếp **17/17 ảnh mission** (`01`–`17`),
**~40 ảnh step** (`step_001`–`005`, `007`, `009`, `012`, `015`–`017`, `025`–`028`,
`030`–`033`, `037`, `039`, `041`–`044`, `047`, `052`, `055`, `061`–`062`, `067`–`068`,
`070`, `072`–`073`, `078`–`079`, `082`–`084`, `086`–`090`, `093`–`094`, `104`, `106`,
`112`, `114`–`115`, `118`, `121`),
**8 frame video** (mỗi 60 s), `qa_report.json` (toàn bộ timeline 128 bước),
`qa_session.json`, `qa_session_summary.md`, cả hai ảnh mẫu trình phát
(`player-sample-vod.jpg`, `player-sample-sport.jpg`) và plan Task 11 Step 5.
Đã đo pixel để kiểm chứng viền focus (xem §4). Không suy đoán nội dung ngoài
những gì nhìn thấy trong ảnh/timeline.

**Quy ước timeline** (như lần trước): focus ghi ở step N là trạng thái **TRƯỚC**
action của step N; action ở step N gây ra focus ở step N+1.

---

## 1. Từng ảnh mission (01–17)

### 01 — `01_cold_start.jpg` — Cold start, dialog THÔNG BÁO
Dialog **THÔNG BÁO** (nhóm Telegram @kenhlivetv, QR code). Nút **ĐÃ HIỂU / ĐÓNG**
(đỏ) có **viền trắng rõ ràng** — focus đã rơi đúng vào nút đóng. **R1 đã sửa xong —
xác nhận.** Phía sau dialog là home hub (hàng ĐANG PHÁT TRỰC TIẾP, hàng
GIẢI ĐẤU HÀNG ĐẦU: "Ligue 1 · 4 đang phát", "HOL D1 · 1 đang phát").
Tồn tại nhỏ: dòng cuối thân dialog ("…nhật mới nhất.") vẫn bị cắt nửa dòng ở
mép dưới vùng cuộn — giống hệt lần chạy FPT (D9 cũ, mức cosmetic).

### 02 — `02_mission_cold_start.jpg` — TRÙNG step_005/step_006
Home hub đã cuộn: hero Manchester United vs Aston Villa (tiêu đề đè lên top nav —
xem D8), hàng ĐANG PHÁT với thẻ Freiburg focus (viền trắng). Mission shot này
không chụp cold start mà là trạng thái cuối mission (quirk của harness, như lần trước).

### 03 — `03_mission_sports_multi_source.jpg` — Tab Thể thao, thẻ Le Mans focus
Hàng **Socolive TV · Trực Tiếp & Lịch Đấu (10 trận)**: thẻ **Le Mans 4:7 AS Monaco
có viền trắng rõ** (đang focus). **D10:** thẻ Villarreal vs Getafe có **pill xám "0"**
bên trái badge LIVE. Tỉ số **4:7** không hợp lý cho bóng đá (xem N8). Tiêu đề hero
đè lên top nav (D8); đồng hồ 00:23 + ngày đè lên TÌM KIẾM/CÀI ĐẶT (D9).

### 04 — `04_mission_sports_room_picker.jpg` — TRÙNG step_014/step_018
Dialog chọn phòng Le Mans vs AS Monaco (BOSS / XUÂN SON / KINH VÂN, SOCO).
Hàng phòng đầu có gạch chân trắng (focus, xem §2).

### 05 — `05_mission_sports_data_accuracy.jpg` — TRÙNG step_023
Hero Man Utd vs Aston Villa, nút [OK] XEM NGAY focus (viền trắng). D8/D9 vẫn thấy.

### 06 — `06_mission_player_streaming_and_controls.jpg` — Player toàn màn hình, OSD đã ẩn
Trận Man Utd vs Aston Villa, khung hình cầu thủ thật, score bug của luồng
**"MUN 2-3 AVL / Last 5 penalties McGinn"** — đối chiếu: tỉ số của app là 8-5/8-6
(xem N8). Logo SUTONGTV + chữ Trung "O古独播" của luồng ở góc phải. Không có OSD.

### 07 — `07_mission_home_hub_3_cards_and_canva_logos.jpg` — TRÙNG step_041
Home hub đã cuộn: hàng SẮP DIỄN RA (RC Celta 00:30 Levante, Villarreal 00:30
Getafe, Vitoria 01:00 FC Porto) + hàng **PHIM ĐANG THỊNH HÀNH với 6 poster**
(Mục Thần Ký 2024, Bắt Đầu Với Chí Tôn Đan Điền 2025, Xa Ngoài Kia Nơi Loài Tôm…
2022, Thần Tài Đậu Chiêm Long 2026, Thái Cổ Thần Tôn 2026, Quý Phi Được Nước Lấn
Tới 2026). 6 poster/một hàng, tiêu đề đọc được — **câu hỏi 6-per-row: với poster
phim thì ĐẠT** (xem §7). Top nav ở trạng thái đã cuộn thì nền đen đặc, chữ đọc rõ.

### 08 — `08_mission_schedule_epg_and_fixture_tap.jpg` — TRÙNG step_047–051
Tab Lịch trình: các thẻ trận full-width, tên đội đầy đủ ("Manchester United vs
Aston Villa", "SC Freiburg vs 1. FC Union Berlin"), giờ đỏ 23:30/23:15, badge Live,
tên giải, avatar phòng + "+8"/"+2". **N3 (tên đội ngắt giữa từ) ở lần chạy FPT đã
hết — tên không còn bị ngắt giữa từ.** Thẻ SC Freiburg focus (viền trắng).

### 09 — `09_mission_sidebar_rail_full_traversal.jpg` — TRÙNG step_052–054
Giống 08, focus đã lên thẻ đầu (Man Utd vs Aston Villa, viền trắng).
**UP từ hàng đầu lên top nav chưa bao giờ được thử trong lần chạy này** (xem §7).

### 10 — `10_mission_iptv_categories_and_favorites.jpg` — TRÙNG step_064
Màn hình IPTV: hero VTV6 (nền đen, không có video preview), nút XEM TOÀN MÀN HÌNH,
chip lọc, lưới kênh. Xem chi tiết ở step_061/062 (§2).

### 11 — `11_mission_iptv_epg_and_zapping_player.jpg` — Player IPTV đang tải
**VTV1 HD, "KÊNH 6 · Đang chiếu: Góc nhìn văn hóa"**, giữa màn hình là
**"Đang tải luồng…"** (spinner) trên nền đen. Không thấy Mini-Guide hay EPG bar.
Trạng thái cuối mission là đang tải, không phải đang phát.

### 12 — `12_mission_phim_nguonc_and_categories.jpg` — TRÙNG step_076
Màn hình Kho Phim: hero "Mục Thần Ký" (xem step_072/073).

### 13 — `13_mission_phim_episode_picker_and_favorite.jpg` — TRÙNG step_085
Giống step_084: hero phim, nút XEM NGAY focus (viền trắng), **"✓ ĐÃ LƯU"**,
hàng **BỘ PHIM ĐÃ LƯU (1)** mới xuất hiện. Không thấy hộp chọn tập nào —
mission "episode picker" kết thúc ở màn hình chi tiết, không phải ở dialog.

### 14 — `14_mission_vod_player_seek_and_resume.jpg` — TRÙNG step_094/095
Màn hình chi tiết phim sau khi thoát player: **"✓ ĐÃ LƯU (TẬP 01 · 10:50/19:18)"**,
hàng **TIẾP TỤC XEM (1 phim)** mới xuất hiện — **lưu tiến độ xem hoạt động**,
thời gian khớp với lúc thoát player (10:47 ở step_093).

### 15 — `15_mission_player_settings_dialog.jpg` — Khung hình video + phụ đề
Title card của phim Mục Thần Ký (chữ Trung trên nền đen) với phụ đề
**"(Mục Thần Ký)"** ở gần mép dưới. Đây là khung hình video, không phải dialog
cài đặt — mission shot lại không chụp đúng mục tiêu (quirk harness). Phụ đề ở
mép dưới khi không có OSD — bình thường, không đè lên seekbar vì không có seekbar
nào hiện.

### 16 — `16_mission_search_and_settings_feedback.jpg` — TRÙNG step_120/122/123
Màn hình Cài đặt: các hàng "Chất lượng hình — Cao nhất (nét)", "Chế độ âm thanh —
Tự động (Hay)", "Liên hệ & Báo lỗi", "Xóa bộ nhớ đệm ảnh", "Phiên bản 0.1.12".
Sạch, đọc rõ (xem step_118).

### 17 — `17_mission_dpad_chaos_stress_and_recovery.jpg` — TRÙNG step_128
Màn hình Cài đặt sau stress test, focus ở hàng cuối (viền trắng), app không crash,
không màn hình đen — recovery tốt.

---

## 2. Ảnh step — bằng chứng cho các finding

### step_001 — Dialog THÔNG BÁO, R1 đã sửa
Giống ảnh 01: **ĐÃ HIỂU / ĐÓNG có viền trắng rõ**, focus đúng nút đóng.
Timeline: `btnCloseFeedback#[575,960][888,1048]`, ring=True/WHITE — lần này
detector và pixels khớp nhau.

### step_002 — Home billboard, heroPlay focus (D8)
Hero Man Utd vs Aston Villa: **[OK] XEM NGAY có viền trắng rõ** (timeline
ring=True). Nhưng **tiêu đề billboard "Manchester United VS Aston Villa" nằm
cùng hàng với top nav**: chữ trắng đè lên logo đỏ "KENHLIVE" ("KENH[Manches]ter
United"), đè lên "TRANG CHỦ", chữ "VS" đỏ đè lên "TRUYỀN HÌNH", "Aston Villa"
+ logo đè lên "KHO PHIM". Crop phóng to `crop_002_topnav.png` (đã kiểm tra)
cho thấy rõ sự chồng lấn — xem D8.

### step_003 / step_004 / step_005 — Bằng chứng finding #1 và #2 là ARTIFACT
- **step_003:** thẻ Man Utd vs Aston Villa **có viền trắng hình chữ nhật rõ
  ràng bao quanh toàn bộ thẻ**, khác hẳn 2 thẻ bên cạnh (không viền). Crop
  `crop_003_card.png` cho thấy viền trắng ~2px (2dp) sắc nét.
- **step_004:** thẻ Inter vs Como **có viền trắng tương tự**.
- **step_005:** thẻ SC Freiburg vs 1. FC Union **có viền trắng tương tự**.
- Đo pixel (quét dòng y=330 tìm pixel sáng >200): step_002 không có pixel sáng
  nào (chưa focus thẻ); step_003 có viền ở x=39/373; step_004 ở x=367/701;
  step_005 ở x=586/920 — đúng vị trí mép trái/phải của thẻ đang focus.
  Thẻ focus còn hơi lớn hơn thẻ thường (mép trái x=41 so với x=48 khi chưa
  focus — khớp scale ~1.05–1.06x theo KL6.5).
- **Kết luận: detector báo `has_focus_ring: False` nhưng pixels cho thấy viền
  trắng 2dp + scale-up đúng chuẩn KL6.5. Finding #1 và #2 là lỗi detector,
  không phải lỗi app.**

### step_007 / step_008 — UP từ thẻ lên billboard, vòng ORANGE
Focus rơi vào toàn bộ vùng billboard `view#[96,0][1824,648]`, detector báo
**viền ORANGE**. Trong ảnh không thấy rõ viền cam quanh billboard — không xác
minh được bằng mắt. Billboards lúc này hiện đầy đủ: badge "● TRỰC TIẾP",
"Ngoại Hạng Anh", "👁 930,5K", tiêu đề + logo đội, nút XEM NGAY / CHỌN PHÒNG,
đồng hồ **00:22** + ngày **"Thứ Hai, 09/11/2026"** + **"01/10 ÂL · Ất Tỵ"** đè
lên "TÌM KIẾM/CÀI ĐẶT" (D9). Ảnh bìa có chữ quảng cáo mờ
"BÓNG ĐÁ ĐỈNH CAO CÙNG" sau lớp scrim (N11).

### step_009 — Nav focus rõ
**KHO PHIM có viền trắng rõ** (đang focus). UP từ thẻ đã lên được top nav sau
3 lần UP (thẻ → billboard → nav) — xem §7.

### step_012 / step_032 — Tab Thể thao, thẻ focus + pill "0" (D10)
Hàng Socolive TV (10 trận): thẻ Freiburg **4:1** focus (viền trắng rõ).
**Thẻ Inter vs Como có pill xám "0" ở góc trái, cạnh badge LIVE** (step_012);
step_032 thẻ Inter focus vẫn có pill "0" (tỉ số lúc này đã thành 2:0).
Thẻ Freiburg thì pill xám hiển thị "HT" (hợp lệ). D6 chưa sửa ở layout này.

### step_015 / step_016 / step_017 — Dialog chọn phòng (RoomPicker)
Dialog "Le Mans vs AS Monaco — Ligue 1 · 3 phòng live": BOSS (Lv.1) 26,4K,
XUÂN SON (Lv.3) 26,4K, KINH VÂN (Lv.1) 26,2K, badge SOCO.
Focus thể hiện bằng **gạch chân trắng dưới hàng phòng đang focus** (không phải
viền hộp): step_015 gạch dưới BOSS, step_016 gạch dưới XUÂN SON (nhưng vẫn còn
một gạch mờ dưới BOSS — xem N17). BACK đóng dialog, focus về lại thẻ trận
(step_018) — vòng đời dialog tốt.

### step_025–030 — Player Thể thao (Sport OSD)
OSD hiện đầy đủ trong cả 6 ảnh: hàng trên **"◀ QUAY LẠI"** + pill tỉ số
**"HT · MAN 8 - 5 AST"** + tiêu đề phải "THỂ THAO · Manchester United vs
Aston Villa · TẠ BIÊN GIỚI / NGOẠI HẠNG ANH · TRỰC TIẾP · 8 - 5 · HT";
hàng nút "Chọn BLV / Đổi luồng / KÊNH TIẾNG / DA MÀN HÌNH / PIP / TÙY CHỌN";
giữa màn hình **TUA -30S / ▶ PHÁT / TUA +30S**; dưới cùng seekbar **00:00** +
knob trắng ở đầu trái + chấm đỏ LIVE ở đầu phải + nút **"Về trực tiếp"**.
Video phát thật (motion_delta 25.41 / 41.48 / 11.67 / 10.48).
**Không nút OSD nào có viền trắng trong cả 6 ảnh** (timeline focus NONE suốt).
MENU (step 25) không mở Server Picker; A (26) / B (27) không có thay đổi nhìn
thấy; DPAD_DOWN (28) / OK (29) không tạo focus. BACK lần 1 (step 30) chỉ ẩn
OSD (step_031 còn ở PlayerActivity, video trần); BACK lần 2 (step 31) mới thoát
về MainActivity (step_032) — xem D14, D15.
Lưu ý: chữ của luồng (quảng cáo BUFA "TẢI NGAY APP BUFA / http://bufa.chat",
"ZALO +63 960 584 8581") đè lên vùng seekbar/nhãn giờ của app (N12);
logo SUTONGTV của luồng đè lên cuối tiêu đề app.

### step_033 / step_037 — Billboard đầy đủ + thẻ focus
Billboard không cuộn: tiêu đề + phụ đề + 2 nút đều sạch, [OK] XEM NGAY focus
(viền trắng). D9 (đồng hồ/ngày đè nav) và N11 (chữ bìa) vẫn thấy.
step_037: thẻ Man Utd focus, **viền trắng rõ** (timeline lại báo ring=False —
thêm một mẫu detector sai).

### step_039 / step_041 — Hàng SẮP DIỄN RA có nội dung + 6 poster phim (D2 đã sửa)
Hàng upcoming: "RC Ce… 00:30 Levante", "Villarr… 00:30 Getafe",
"Vitoria… 01:00 FC Porto" + pill "Còn 7p" + avatar phòng. **D2 đã sửa — hàng
không còn trống.** Hàng PHIM ĐANG THỊNH HÀNH: 6 poster + tiêu đề 2 dòng đọc
được; poster đầu focus (viền trắng, step_039). Tên đội trên thẻ trận vẫn bị
cắt ngắn ("RC Ce…", "Villarr…") — xem §7.

### step_042 / step_047 / step_052 — Tab Lịch trình
Thẻ trận full-width, tên đội đầy đủ, không ngắt giữa từ (N3 đã hết).
**"LỊCH TRÌNH" có gạch chân đỏ** (tab đang chọn — xác nhận). Thẻ đầu focus
(viền trắng, step_052). LEFT từ thẻ full-width không di chuyển focus (steps
47–50: 4 lần LEFT, focus đứng yên ở `schedCard#[44,317]`) — đúng vì thẻ đã
rộng toàn màn hình, không có phần tử bên trái; **UP từ hàng đầu lên nav thì
chưa được thử** (AI chỉ UP từ hàng 2 lên hàng 1 rồi dừng).

### step_043 — Dialog chọn phòng từ Lịch trình
Dialog Man Utd vs Aston Villa (12 phòng live): A MÂN, CR Bưởi, BLV MESSI,
RICKHANTER, BLV COCA — **tất cả "0 lượt xem · LIVE"**, trong khi hero báo
trận này 930,5K xem (xem N9). Gạch chân trắng dưới hàng A MÂN (focus).

### step_044 — Player Thể thao từ Lịch trình
Pill tỉ số lúc này là **"MAN 8 - 6 AST"** (đã đổi từ 8-5). TUA ±30S + PHÁT +
seekbar 00:00 + "Về trực tiếp" như cũ. BACK lần 1 → còn ở player (step_045),
BACK lần 2 → về MainActivity (step_046).

### step_055 — Tab IPTV, hero ANTV HD
Hero: **"ANTV HD / Đang phát: [00:30 - 01:00] 113 online"** + thanh tiến trình
đỏ mỏng + "Tiếp theo: [01:00] Phim truyện: 12h00 - Cuộc chiến thừa kế -
Tập 59/88". Nút **XEM TOÀN MÀN HÌNH** (đỏ), "+ YÊU THÍCH", "NGUỒN M3U".
**Hero không có video preview — nền đen.** Chip lọc: "Tất cả" (trắng, đang
chọn), "Yêu thích", "VTV", "HTV", "Thể thao", **"Phim tru…" — chip "Phim
truyện" bị cắt ở mép ô tìm kiếm** (hàng chip chưa cuộn; khi cuộn thì hiện đủ —
xem step_061). Nhóm "Thể thao": VTV6, 360 Bundesli…, 360 C1 Châu… (tên kênh
cắt ngắn "…"). **"TRUYỀN HÌNH" có gạch chân đỏ** (tab đang chọn).

### step_061 / step_062 — Lưới kênh IPTV, D4 đã sửa
**step_061: thẻ VTV6 có viền trắng rõ ràng** (focus `cardIptvRoot`) — **D4 đã
sửa**, khác hẳn lần chạy FPT (focus mờ/không thấy). Hero lúc này là VTV6
("Đang phát trực tiếp từ Đài Truyền hình Quốc gia", hint "Bấm [OK] để xem toàn
màn hình · Bấm [Lên/Xuống] để duyệt kênh"). Chip "Tất cả" lúc này bị cắt nửa
ở mép trái (hàng chip đã cuộn theo focus — edge-peek bình thường).
**step_062:** sau LONG_PRESS OK, nhóm mới **"Kênh yêu thích"** xuất hiện với
VTV6 — thêm yêu thích hoạt động. Hàng "Phim truyện" ở dưới bị cắt nửa ở mép
màn hình (chỉ thấy nửa trên thẻ) — D5 **chưa xác minh được** (AI không cuộn
tới cuối danh sách để kiểm tra padding 105dp).

### step_067 / step_068 — Player IPTV đang tải
**VTV9 HD, "KÊNH 17 · Đang chiếu: Alo Doctor"**, OSD trên gồm QUAY LẠI /
KÊNH / Đổi nguồn / PIP / TÙY CHỌN, giữa màn hình **"Đang tải luồng…"**
(spinner) trên nền đen. Bấm phím số 1 rồi 5 (zapping) — sau ~85 s (steps
67–69) vẫn đang tải, chưa có hình. Toast dưới: "Tự chuyển sang kênh VTV9 HD…".
Không thấy Mini-Guide hay EPG bar.

### step_070 — Player IPTV đã phát (VTV Cần Thơ)
Video phát thật (phim Hàn Quốc). OSD trên: QUAY LẠI / KÊNH / Đổi nguồn / PIP /
TÙY CHỌN; phải trên: **"VTV Cần Thơ / KÊNH 5"** — chữ "KÊNH 5" đè lên logo
"Cần Thơ" của luồng (N12). Dưới trái: **"CUỘC ĐỜI THỨ HAI / 00:51"** (tên
chương trình + thời gian đã phát). **Không có thanh EPG** (không có thanh tiến
trình mỏng, không có Mini-Guide) trong bất kỳ ảnh player IPTV nào.

### step_072 / step_073 — Màn hình Kho Phim (hero phim)
Hero Netflix-style: tiêu đề lớn **"Mục Thần Ký"**, "2024", pill "Phiêu Lưu ·
Viễn Tưởng", mô tả 2 dòng (cắt "…"), nút **▶ XEM NGAY** (đỏ), **CHỌN TẬP**,
**+ LƯU PHIM**, **PHIM KHÁC**. Dưới: chip DANH MỤC ("Tất Cả" trắng đang chọn,
"Lịch Sử Xem", "Tìm Kiếm", "Mới Cập Nhật", "Phim Bộ", "Phim Lẻ", "Anime & …"
— chip cuối cắt ở mép phải) + hàng "Phim Mới Cập Nhật (120 phim)".
**"KHO PHIM" có gạch chân đỏ.** step_072: TRANG CHỦ focus (viền trắng rõ quanh
chữ). step_073: focus sang CHỌN TẬP — crop phóng to cho thấy **CHỌN TẬP có
viền trắng rõ** dù timeline báo ring=False (thêm một mẫu detector sai).
Lưu ý: sau lưng top nav có chữ mờ "…ĐIỆN ẢNH ĐẶC SẮC" lộ qua nav bán trong
(crop_094, xem N11-biến thể).

### step_078–082 — EpisodePickerDialog (finding HIGH — THẬT)
Cả 5 ảnh **giống hệt nhau (cùng sha256)**: màn hình chi tiết phim Mục Thần Ký
(backdrop lớn, poster trái, "2024", "Trọn bộ", "Không có mô tả chi tiết."
— dòng này đè lên mép dưới poster), đoạn mô tả, và ở **mép dưới cùng chỉ ló
một dòng "CHỌN SERVER & TẬP PHIM"** bị cắt nửa. Không có danh sách tập/server
nào hiện ra; không có phần tử nào focus được. Timeline: focus NONE suốt
steps 78–82 (~70 s), qua WAIT + DPAD_DOWN + OK + DPAD_UP đều không đổi.
BACK ở step 82 đóng được (step_083 về lại màn hình chi tiết, focus
`btnHeroBackHome`). Xem phán quyết §4.

### step_083 / step_084 / step_086 — Sau khi đóng dialog
Nút LƯU PHIM đã thành **"✓ ĐÃ LƯU"** (OK ở step 80 khi focus NONE có lẽ đã
kích hoạt lưu — hoặc đã lưu từ trước), hàng **BỘ PHIM ĐÃ LƯU (1)** xuất hiện.
step_084: XEM NGAY focus, **viền trắng rõ** (timeline lại báo ring=False).

### step_087–089 / step_093 — Player VOD (OSD phim)
OSD VOD hiện đầy đủ: trên giữa tiêu đề **"PHIM TRUYỆN · Mục Thần Ký · Tập 01"**
+ "Tập 01"; trái có icon bánh răng + **thanh trượt dọc độ sáng** (knob trắng);
giữa **TUA -10S / ▶ PHÁT / TUA +10S** (nút chữ nhật, không phải icon tròn
như mẫu); dưới seekbar **đỏ + knob trắng** với giờ trái/phải; hàng nút dưới:
PHÁT, TUA -10S, TUA +10S, TẬP TRƯỚC, TẬP TIẾP, CHỌN TẬP,
**ÂM THANH & PHỤ ĐỀ** (focus, viền trắng), **"TỐ…"** — nút cuối bị cắt nửa
nhãn ở mép phải (xem D12).
Giờ seekbar nhất quán: 01:35/17:43, 03:55/15:22, 05:41/13:36, 10:47/08:30 —
**giờ phải là thời gian CÒN LẠI** (cộng lại luôn ≈ 19:17–19:18) — đúng mẫu
(remaining-time label), không phải lỗi. **SKIP INTRO không xuất hiện** (đúng
— GONE theo mặc định vì không có dữ liệu). **Không có nút Speed (1x)/Lock
đọc được; "TỐ…" nhiều khả năng là "TỐC ĐỘ" bị cắt.**
Timeline báo focus NONE ở steps 87–89/93 nhưng ảnh cho thấy viền trắng rõ
trên ÂM THANH & PHỤ ĐỀ (step_087/089/093) và CHỌN TẬP (step_088, frame video
f_005) — detector mù với nút OSD (xem §9).

### step_090 / step_092 — Dialog "Cài đặt trình phát" (VOD)
Dialog 4 nhóm: Hình ảnh ("Tự động ✓" focus viền trắng, "Cao nhất (nét)",
"Ổn định (mượt)"), Âm thanh ("Chuẩn", "Bass mạnh", "Rõ tiếng BLV",
"Ban đêm (êm)", **"Tự động (Hay)" bị cắt ở mép phải dialog**), Tỉ lệ khung
hình ("16:9 Chuẩn (Fit)", "Lấp đầy (Fill) ✓", "Điện ảnh (Zoom)",
"Cố định (Fixed)"), Bước tua ("10s ✓", "20s", "30s"). Nút ĐÓNG đỏ dưới phải.
OK ở step 91 mở lại dialog thay vì toggle Play/Pause (step_092) — OK trên OSD
mở dialog cài đặt chứ không tạm dừng/phát.

### step_094 — Về lại màn hình phim, resume đã lưu
**"✓ ĐÃ LƯU (TẬP 01 · 10:50/19:18)"** + hàng **TIẾP TỤC XEM (1 phim)** —
resume hoạt động, thời gian khớp lúc thoát player.

### step_104 — Dialog lỗi phát luồng
**"Lỗi Phát Luồng Video / Stream lỗi: ERROR_CODE_DECODING_FAILED"** với nút
**THỬ LẠI** (focus, viền trắng), QUAY LẠI, BÁO LỖI + "Báo lỗi kênh qua nhóm
Telegram: @kenhlivetv". Phụ đề "(Hạ lưu sông chảy, bên ngoài Đại Khu)" ở mép
dưới màn hình — không đè seekbar (không có OSD lúc lỗi). Lỗi codec trên
emulator x86 — theo plan là môi trường, mức LOW. THỬ LẠI thành công (step_105
phát lại, motion 12.3).

### step_106 / step_112 — Dialog cài đặt (player native)
Giống step_090 — **dialog cài đặt thống nhất ở cả hai player** (VOD + native).
step_112: AI đã chọn "Cao nhất (nét) ✓" ("Đang chọn: Cao nhất (nét)").
**Dòng "Đang chọn: 10s" vẫn bị cắt nửa ở mép dưới dialog** ngay cả khi đã
cuộn tới nút ĐÓNG (step_112) — xem D13. Chip "Tự động (Hay)" vẫn bị cắt ở
mép phải.

### step_114–116 — Tab Tìm kiếm
**"TÌM KIẾM" có gạch chân đỏ.** Chip gợi ý: Phim Mới, Hoạt Hình, Ngoại Hạng
Anh, Bundesliga, SPA D1, Serie A, "TUR D1" (cắt ở mép phải). "23 trận đang
live". "Xu hướng tìm kiếm": One Piece / Conan / Ao no Hako ("Gợi ý nhanh").
Kết quả: **"Manchester United vs Aston Villa / CR Bưởi +11 BLV · 888,9K ·
12 phòng"** + badge [LIVE], "Inter Milan vs Como / CÔNG CHẤT +5 BLV · 217,4K ·
6 phòng" — tên đội đầy đủ, đọc rõ. **Ô nhập tìm kiếm không thấy khung/placeholder**
nào trên màn hình (bounds `searchInput#[96,24][1720,116]` trùng vùng top nav);
truy vấn chỉ lộ qua bàn phím ("uefa"/"UEFA") và dòng "0 kết quả cho 'uefa'"
(step_115). Bàn phím ảo render tốt, phím "q" focus (viền trắng).

### step_118 / step_121 — Tab Cài đặt + dialog THÔNG BÁO
Cài đặt sạch, đọc rõ: "Chất lượng hình — Cao nhất (nét) ›" (focus, viền
trắng quanh cả hàng), "Chế độ âm thanh — Tự động (Hay) ›", mục "Ứng dụng",
"Liên hệ & Báo lỗi — Nhóm Telegram: @kenhlivetv ›", "Xóa bộ nhớ đệm ảnh",
"Phiên bản — 0.1.12". **"CÀI ĐẶT" có gạch chân đỏ.**
step_121: mở dialog THÔNG BÁO từ "Liên hệ & Báo lỗi" — ĐÃ HIỂU / ĐÓNG focus
(viền trắng), thân dialog lại cắt nửa dòng cuối như step_001.

---

## 3. Video `full_qa_tour.mp4`

| Frame video | Nội dung thấy được |
|---|---|
| 0 s (`f_001`) | Dialog chọn phòng Le Mans (tương đương step_015, session t≈244 s) — **không phải cold start** |
| 60 s (`f_002`) | Player Thể thao, OSD Man Utd HT 8-5 (steps 25–30) |
| 120 s (`f_003`) | Home hub đã cuộn: SẮP DIỄN RA + PHIM ĐANG THỊNH HÀNH (steps 32–41) |
| 180 s (`f_004`) | **Player IPTV ANTV HD đang phát** ("KÊNH 1 · Đang chiếu: 113 online", timer 00:49) — trạng thái này không có trong ảnh step |
| 240 s (`f_005`) | Player VOD 03:26/15:51, focus CHỌN TẬP (viền trắng) |
| 300 s (`f_006`) | Màn hình phim "ĐÃ LƯU (TẬP 01 · 10:50/19:18)" (step_094) |
| 360 s (`f_007`) | Player VOD 15:57/03:20, OSD hiện nhưng **không nút nào focus** |
| 420 s (`f_008`) | Tab Tìm kiếm (step_114) |

**Kết luận video: tốt hơn hẳn lần chạy FPT nhưng vẫn chưa phải full tour 1x.**
File dài **468,7 s** (ffprobe xác nhận, 1280×720, 72 MB) cho phiên 3967 s.
`concat.txt` **có** trong artifact (22 chunk) — bản sửa merge đã phát huy tác
dụng (lần FPT chỉ còn chunk 1, 174,9 s, không có concat.txt). Nhưng video bao
phủ session t≈244 s → t≈3635 s với tốc độ nén **~8x** (mỗi 60 s video ≈ 450–550 s
phiên): **thiếu ~4 phút đầu** (cold start, dialog, hero, findings #1–2) và
**thiếu ~5,5 phút cuối** (Cài đặt steps 118–122 + chaos 123–128). Không dùng
được để kiểm chứng chuyển động/phát lại ở tốc độ thực. `qa_timelapse.mp4` 46,9 s
(timelapse 10x theo summary).

---

## 4. Phán quyết 3 findings (trong `qa_report.json`)

| # | Finding (step) | Phán quyết | Bằng chứng |
|---|---|---|---|
| 1 | [Step 3] [MEDIUM] Viền focus không chuẩn trên cardRoot đầu tiên | **PHÓNG ĐẠI / DETECTOR ARTIFACT — không phải lỗi app** | Ảnh step_003: thẻ Man Utd có **viền trắng 2dp rõ ràng + scale ~1.05x** (đo pixel: viền sáng ở x=39/373; thẻ focus rộng hơn thẻ thường). Judge chỉ dựa vào flag `has_focus_ring: False`, không nhìn pixels. |
| 2 | [Step 4] [MEDIUM] Viền focus không chuẩn trên card trận ĐANG PHÁT | **PHÓNG ĐẠI / DETECTOR ARTIFACT — cùng nguyên nhân với #1** | Ảnh step_004: thẻ Inter vs Como có **viền trắng rõ tương tự** (pixel sáng x=367/701). step_005, 012, 032, 037 lặp lại mẫu này: viền thấy rõ, flag báo False. |
| 3 | [Step 82] [HIGH] EpisodePickerDialog không trap focus — focus NONE khi mở | **THẬT — HIGH là xứng đáng về mặt hiệu quả** | 5 ảnh liên tiếp step_078–082 **giống hệt nhau (cùng sha256)**: chỉ ló dòng "CHỌN SERVER & TẬP PHIM" ở mép dưới, không có nội dung dialog nào hiện ra, focus NONE suốt ~70 s qua WAIT + DPAD_DOWN + OK + DPAD_UP. Người dùng không thể chọn tập/server bằng remote. Cơ chế có vẻ là **bottom sheet mở nhưng nội dung nằm dưới fold + không set focus ban đầu**, chứ không hẳn "dialog không trap focus" như judge diễn đạt — nhưng hậu quả giống nhau: dialog không dùng được. BACK vẫn đóng được (step_083). |

**Tóm lại: 3 findings thực chất chỉ là 1 vấn đề thật (D11) + 2 lần detector báo
sai cùng một lỗi. Điểm 75/100 bị trừ oan 10 điểm cho 2 artifact.**

---

## 5. Khiếm khuyết mới trong lần chạy này (D8–D17)

| # | Mức | Vấn đề | Bằng chứng |
|---|---|---|---|
| **D8** | MEDIUM | **Tiêu đề billboard trượt lên dưới top nav trong suốt và đè lên logo + nhãn nav.** Khi trang cuộn, tiêu đề "Manchester United VS Aston Villa" (kèm logo đội) nằm cùng hàng với top nav: đè lên "KENHLIVE", "TRANG CHỦ", "TRUYỀN HÌNH", "KHO PHIM". KL6.5 yêu cầu nav chuyển sang nền đặc #E6141414 khi cuộn — ở trạng thái cuộn dở này nav vẫn trong suốt. Khi cuộn hẳn qua billboard thì nav đặc lại (step_041) nên lỗi chỉ xuất hiện ở vùng chuyển tiếp — nhưng đó lại là vùng người dùng thấy nhiều nhất. | step_002/003/004/005, step_012, step_032, `03_mission_sports_multi_source.jpg`; crop phóng to `crop_002_topnav.png` |
| **D9** | MEDIUM-LOW | **Đồng hồ + ngày đè lên nav TÌM KIẾM/CÀI ĐẶT.** Khi billboard hiện đầy đủ, cụm "00:22" + "Thứ Hai, 09/11/2026" + "01/10 ÂL · Ất Tỵ" ở góc phải đè lên nhãn "TÌM KIẾM" (bị pill đồng hồ che) và "CÀI ĐẶT" (bị chữ ngày đỏ che). | step_007/009/012/032/033/037, `03_mission_sports_multi_source.jpg` |
| **D10** | MEDIUM-LOW | **Pill xám "0" vẫn còn trên thẻ trận ở tab Thể thao (D6 chưa sửa ở layout này).** Thẻ Inter vs Como và Villarreal vs Getafe có pill xám "0" ở vị trí mà thẻ khác hiển thị "HT" — field phút/trạng thái render giá trị thiếu thành "0". Bản sửa `validKickoff` ở Task 5 có vẻ chỉ áp cho thẻ ở hàng home, chưa áp cho thẻ ở tab Thể thao. | step_012, step_032, `03_mission_sports_multi_source.jpg` |
| **D11** | **HIGH** | **EpisodePickerDialog mở dưới fold, không có focus ban đầu, D-pad chết.** Xem §4 finding #3. | step_078–082 (5 ảnh giống hệt nhau) |
| **D12** | MEDIUM-LOW | **Hàng nút OSD VOD tràn màn hình: nút Speed bị cắt còn "TỐ", nút Lock không thấy.** Hàng 8 nút (PHÁT, TUA -10S, TUA +10S, TẬP TRƯỚC, TẬP TIẾP, CHỌN TẬP, ÂM THANH & PHỤ ĐỀ, TỐ…) — nút cuối chỉ ló "TỐ" ở mép phải trong mọi ảnh; Lock (KHÓA) không xuất hiện trong bất kỳ ảnh nào. Hàng có cuộn theo focus hay không thì lần chạy này không thử (focus chưa bao giờ tới nút cuối). Thuộc họ D7 (OSD clipping). | step_087/088/089/093, frame video f_005/f_007; crop `crop_087_vodbar.png` |
| **D13** | LOW | **Dialog "Cài đặt trình phát": chip "Tự động (Hay)" bị cắt ở mép phải; dòng "Đang chọn: 10s" bị cắt nửa ở mép dưới.** Cả hai đều còn nguyên sau khi AI cuộn tới nút ĐÓNG (step_112) — ScrollView thiếu padding dưới; hàng chip Âm thanh thiếu chỗ cho chip thứ 5. Dialog vẫn dùng được (cuộn được) nên chỉ là cosmetic. | step_090/106/112 |
| **D14** | MEDIUM-LOW | **OSD Thể thao không cho thấy focus nào trên nút điều khiển; MENU/A/B/OK không có phản hồi nhìn thấy.** OSD hiện đầy đủ trong 6 ảnh steps 25–30 nhưng không nút nào có viền trắng; MENU không mở Server Picker, A/B không đổi gì nhìn thấy, OK không tạm dừng (motion vẫn 10.48 ở step_30). Lưu ý: timeline NONE ở player là không đáng tin (VOD cũng báo NONE dù ảnh có viền trắng), nhưng ở đây **chính ảnh chụp** cũng không có viền — khác với VOD. Có thể OSD Thể thao tự hiện mà không nhận focus, hoặc focus nằm trên playerView. | step_025/026/027/028/030 |
| **D15** | LOW | **BACK không thống nhất giữa hai player.** Từ trạng thái OSD đang hiện: VOD thoát ngay sau **1 BACK** (step_93 → step_94 MainActivity); Thể thao và IPTV cần **2 BACK** (BACK 1 ẩn OSD, BACK 2 thoát — steps 30–31, 44–45). KL6.5 nói BACK 3 cấp thống nhất — VOD đang bỏ qua cấp "ẩn OSD". | step_030/031, step_044/045, step_093 |
| **D16** | LOW-MEDIUM | **Ô nhập tìm kiếm không có khung/placeholder nhìn thấy trên tab Tìm kiếm.** Vùng `searchInput#[96,24][1720,116]` trùng vùng top nav; trên ảnh chỉ thấy chip gợi ý + kết quả, không thấy ô nhập. Truy vấn chỉ lộ qua bàn phím và dòng "0 kết quả cho 'uefa'". Gõ phím vẫn hoạt động. | step_114/115/116 |
| **D17** | LOW | **TRANG CHỦ không có gạch chân đỏ khi được chọn (các tab khác đều có); thay vào đó có một chấm đỏ nhỏ sau nhãn trong mọi ảnh.** Gạch chân đỏ xác nhận ở KHO PHIM (step_072), LỊCH TRÌNH (step_042), TRUYỀN HÌNH (step_055), TÌM KIẾM (step_114), CÀI ĐẶT (step_118). Ở TRANG CHỦ (step_041, crop phóng to) không thấy gạch chân — chỉ có chấm đỏ sau chữ, xuất hiện cả khi TRANG CHỦ không được chọn (step_055/061/072). Chưa rõ chấm đỏ là badge "live" hay chỉ báo chọn bị vẽ sai — cần đối chiếu thiết kế. | step_041 (crop `crop_041_topnav.png`), step_002/007/009/012/032/055/061/072 |

### Quan sát thêm (N8–N17, không phải defect UI trực tiếp)

- **N8 — Tỉ số trực tiếp không hợp lý, vẫn còn.** App báo "MAN 8 - 5 AST"
  (steps 25–30) rồi "MAN 8 - 6 AST" (step_044), "Le Mans 4:7 AS Monaco"
  (ảnh 03); trong khi **chính score bug của luồng ghi "MUN 2-3 AVL"**
  (step_031, ảnh 06). Dữ liệu tỉ số của nguồn sai so với luồng thật — vấn đề
  dữ liệu, không phải UI.
- **N9 — Số lượt xem phòng = 0.** Dialog chọn phòng mở từ Lịch trình:
  tất cả các phòng "0 lượt xem · LIVE" (step_043), trong khi cùng trận đó mở
  từ Home thì phòng có 26,4K/26,2K xem (step_015). Dữ liệu không nhất quán
  giữa hai đường mở.
- **N10 — "Đang chiếu: 113 online".** Player IPTV ANTV HD hiển thị
  "KÊNH 1 · Đang chiếu: 113 online" (frame f_004) — số người xem đang được
  dùng làm tên chương trình. Lỗi map field dữ liệu EPG.
- **N11 — Ảnh bìa billboard vẫn chứa chữ quảng cáo.** "BÓNG ĐÁ ĐỈNH CAO CÙNG"
  mờ sau lớp scrim (step_007/033/037); chữ mờ "…ĐIỆN ẢNH ĐẶC SẮC" lộ qua
  nav bán trong trên màn hình phim (step_072–094, crop_094). Scrim đã đủ mạnh
  để chữ bìa không đè lên tiêu đề/nút — nhưng quy tắc "clean-cover" (không
  dùng ảnh có chữ) chưa được áp triệt để.
- **N12 — Đồ họa của luồng đè lên OSD của app.** Quảng cáo BUFA
  ("TẢI NGAY APP BUFA", số Zalo) đè lên vùng seekbar/nhãn giờ Thể thao
  (step_025–030); logo SUTONGTV đè lên cuối tiêu đề Thể thao; logo "Cần Thơ"
  của luồng đè lên "KÊNH 5" ở player IPTV (step_070). Đây là bản chất của việc
  phủ OSD lên luồng bên thứ ba có chữ chạy sẵn — cosmetic, khó sửa triệt để.
- **N13 — Ảnh mission trùng lặp / sai mục tiêu (quirk harness, như lần trước).**
  02≡step_005/006, 04≡step_014/018, 05≡step_023, 07≡step_041, 08≡step_047–051,
  09≡step_052–054, 10≡step_064, 12≡step_076, 13≡step_085, 14≡step_094/095,
  16≡step_120/122/123, 17≡step_128; ảnh 06/11/15 là khung hình video thay vì
  màn hình mission. Giá trị bằng chứng của mission shot thấp — phải dựa vào
  step shot.
- **N14 — Detector focus không đáng tin (vấn đề harness nghiêm trọng nhất).**
  Flag `has_focus_ring: False` xuất hiện ở ít nhất 8 ảnh mà viền trắng nhìn
  thấy rõ bằng mắt (step_003/004/005/012/032/037/073/084); `focused_view:
  NONE` ở 23/128 bước, trong đó có các bước VOD mà ảnh cho thấy nút đang
  focus có viền trắng (step_087–089/093). Chính lỗi này đã sinh ra findings
  #1–2. **Không nên dùng flag focus của harness làm căn cứ chấm điểm khi
  chưa sửa detector.**
- **N15 — Chỉ 5/16 mission được COMPLETE_MISSION** (Cold Start step_5,
  Room Picker step_18, VOD Seek step_94, Search & Settings step_122, Chaos
  step_128); 11 mission còn lại kết thúc bằng SWITCH_TAB giữa chừng. Tab
  detector vẫn sai: summary ghi "Kho Phim 66 thao tác" trong khi phần lớn
  phiên AI ở Home/Thể thao/Lịch trình theo ảnh (tab 0 Trực Tiếp ghi 0 thao
  tác nhưng AI đã ở màn hình Thể thao steps 12–22 — detector suy tab từ nav
  focus nên kẹt).
- **N16 — ERROR_CODE_DECODING_FAILED xuất hiện 1 lần** (step_104, dialog
  "Lỗi Phát Luồng Video"), THỬ LẠI thành công ngay (step_105 phát lại).
  Lỗi codec emulator x86 — theo plan mức LOW, không phải defect app.
  `qa_session.json` nhắc mã này 4 lần, `ExoPlaybackException` 0 lần.
- **N17 — Focus của hàng phòng là gạch chân, không phải viền hộp.**
  RoomPicker dùng gạch chân trắng dưới hàng đang focus (step_015–017); ở
  step_016 vẫn còn một gạch mờ dưới hàng trước đó (BOSS) — có thể là divider
  hoặc focus cũ chưa xóa. Nhìn được nhưng nhẹ hơn chuẩn KL6.5 (viền 2dp +
  scale). Cosmetic.

---

## 6. Trạng thái D1–D7 (từ lần chạy FPT 42489380818)

| Defect cũ | Trạng thái lần này | Bằng chứng |
|---|---|---|
| **D1** — chữ bìa banner đè lên chữ UI | **ĐỔI DẠNG, chưa hết hẳn.** Dạng cũ ("BLV TAP / KINH NGHIỆM / LÀ ĐẲNG CẤP" đè lên tiêu đề/nút) đã hết — hero có scrim, tiêu đề/phụ đề/nút sạch khi chưa cuộn (step_007/033). Nhưng cùng khu vực sinh ra 2 dạng mới: D8 (tiêu đề trượt dưới nav trong suốt) và D9 (đồng hồ/ngày đè nav), + chữ bìa vẫn còn mờ sau scrim (N11). | step_002–005, 007, 012, 032, 033, 037; ảnh 03 |
| **D2** — hàng SẮP DIỄN RA trống | **ĐÃ SỬA.** Hàng có nội dung đầy đủ (3 thẻ upcoming + giờ + avatar phòng). | step_039/041, ảnh 07 |
| **D3** — nhãn stat portal card bị cắt nửa ở fold | **ĐÃ SỬA** (portal cards đã bỏ). Không còn portal card trong bất kỳ ảnh nào; các hàng dùng chiều cao đo được, hàng phim hiện đầy đủ. | step_039/041 |
| **D4** — focus trên kênh IPTV mờ | **ĐÃ SỬA.** Thẻ VTV6 focus có viền trắng rõ. | step_061 |
| **D5** — hàng cuối lưới IPTV bị cắt nửa | **CHƯA XÁC MINH ĐƯỢC.** Hàng dưới cùng vẫn cắt nửa ở mép màn hình (step_061/062) nhưng đó là peek khi cuộn bình thường; AI không cuộn tới cuối danh sách để kiểm tra padding 105dp. | step_061/062 |
| **D6** — pill xám "0" trên thẻ trận | **CHƯA SỬA** (ở tab Thể thao) — xem D10. Hàng home không còn thấy pill "0" (thẻ home hiện "HT"/league pill), nhưng thẻ tab Thể thao vẫn có. | step_012, step_032, ảnh 03 |
| **D7** — OSD clipping (nhãn nút "TẬP TRƯ…", phụ đề đè seekbar) | **ĐÃ SỬA MỘT PHẦN.** Nhãn nút VOD không còn bị cắt giữa từ kiểu "TẬP TRƯ…" — nhưng hàng nút tràn màn hình cắt mất nhãn Speed ("TỐ", D12). Dialog cài đặt có clipping riêng (D13). Phụ đề đè seekbar: **chưa kiểm chứng được** — không có ảnh nào chụp phụ đề cùng lúc với OSD bar hiện (phụ đề chỉ thấy khi OSD ẩn: step_104, ảnh 15). | step_087–093, step_090/106/112, step_104, ảnh 15 |

**Đã xác nhận sửa xong trong lần này:** R1 (dialog focus ĐÃ HIỂU — step_001,
step_121), D2, D3, D4, N3 (tên đội không ngắt giữa từ — step_042/047).
**Đã xác nhận còn:** D6 (dạng D10), D1 (dạng D8/D9), D7 (dạng D12/D13).
**Chưa xác minh được:** D5, nửa phụ đề của D7.

---

## 7. Đối chiếu checklist Task 11 Step 5

- **Bảng màu KL6.5: ĐẠT.** Nền #141414, card #242424, chữ trắng/xám, đỏ #E50914
  chỉ dùng cho logo KENHLIVE, badge LIVE/TRỰC TIẾP, nút chính ([OK] XEM NGAY,
  ĐÃ HIỂU / ĐÓNG). Không còn cam KL5/cyan cũ, không gradient, không glow.
  Badge SOCO (xanh lá) là badge nguồn dữ liệu.
- **Top nav — gạch chân đỏ tab đang chọn: ĐẠT MỘT PHẦN.** Có ở KHO PHIM,
  LỊCH TRÌNH, TRUYỀN HÌNH, TÌM KIẾM, CÀI ĐẶT; **không có ở TRANG CHỦ** (D17).
  Nav chuyển đặc khi cuộn hẳn (step_041) nhưng không chuyển ở vùng chuyển tiếp
  (D8); đồng hồ/ngày đè nav (D9).
- **Billboard: ĐẠT khi chưa cuộn** (ảnh sạch, không va chạm chữ — step_007/033),
  **lỗi khi cuộn** (D8/D9). Ảnh bìa vẫn chứa chữ quảng cáo mờ (N11).
- **Các hàng: ĐẠT.** Hàng live/upcoming/phim đều có nội dung, không hàng trống;
  tên giải, tỉ số, lượt xem, số phòng đọc rõ. Tên đội trên thẻ trận bị cắt ngắn
  ("Manch…", "SC Frei…", "RC Ce…") do mỗi thẻ chứa 2 đội + logo + badge.
- **6-per-row: câu hỏi đã có đáp án — match card KHÔNG phải 6-per-row.**
  Thẻ trận rộng ~326dp (bounds 652px/1920), ~2,7 thẻ hiện mỗi hàng; lo ngại
  137dp không áp cho thẻ trận như build hiện tại. **Poster phim mới là 6/hàng**
  (~137dp) và **đọc được** (step_039/041: poster + tiêu đề 2 dòng rõ).
  Điểm legibility còn lại của thẻ trận là tên đội cắt ngắn — đó là thiết kế
  (2 tên/hàng trong 1 thẻ), cần Evelyn quyết có đổi layout không, không phải
  lỗi kỹ thuật.
- **Top-bar reachability: ĐẠT MỘT PHẦN.** Từ hàng đầu Home, UP lên được nav
  sau 3 lần UP (thẻ → billboard → nav, steps 6–9); billboard nhận focus với
  viền detector báo ORANGE (không thấy rõ viền trên ảnh). Từ hàng đầu của
  Lịch trình/IPTV/Phim/Tìm kiếm/Cài đặt, **UP lên nav chưa được thử lần nào**
  trong phiên này (AI không bấm UP từ hàng đầu các tab đó) — chưa xác minh được.
  LEFT từ thẻ Lịch trình full-width không đi đâu là đúng (không có phần tử
  bên trái).
- **OSD Thể thao vs mẫu sport: ĐẠT VỀ CƠ BẢN.** Score pill góc trên-trái ✓
  ("HT · MAN 8 - 5 AST"), TUA ±30S ✓ (nút chữ, không phải icon tròn như mẫu),
  seekbar trắng + knob ✓, chấm đỏ LIVE ở đầu phải ✓, nút "Về trực tiếp" ✓.
  Thêm 2 hàng nút KL6.5 (Chọn BLV/Đổi luồng/KÊNH TIẾNG/DA MÀN HÌNH/PIP/
  TÙY CHỌN) không có trong mẫu — chấp nhận được (nhiều tính năng hơn mẫu).
  **Gate hỗ trợ chưa xác minh được:** TUA ±30S hiện trên luồng live trong khi
  seekbar đứng ở 00:00 (steps 25–30); AI không bấm phím tua nào ở player Thể
  thao nên không biết luồng có seekable không — **cần test trực tiếp ở full run**
  (bấm LEFT/RIGHT ở player Thể thao và đối chiếu `isCurrentWindowSeekable`).
- **OSD IPTV vs mẫu: CHƯA THẤY ĐỦ.** Top bar ✓ (QUAY LẠI/KÊNH/Đổi nguồn/PIP/
  TÙY CHỌN), tên kênh + "Đang chiếu" ✓. **Mini-Guide và EPG bar không xuất
  hiện trong bất kỳ ảnh nào** (steps 067/068/070, ảnh 11, frame f_004) — nhưng
  AI cũng không bấm OK/DOWN để gọi OSD dưới trong player IPTV nên chưa kết
  luận được là thiếu hay chỉ chưa gọi. Hero IPTV có thanh tiến trình đỏ mỏng
  (step_055); player chỉ có nhãn "00:51"/"00:49" (thời gian đã phát), không có
  thanh EPG.
- **OSD VOD vs mẫu vod: ĐẠT VỀ CƠ BẢN, trừ cuối hàng nút.** Tiêu đề giữa ✓,
  thanh trượt dọc độ sáng ✓ (icon bánh răng + knob trắng), seekbar đỏ + knob ✓,
  nhãn thời gian còn lại ✓ (cộng lại luôn ≈19:17–19:18), TẬP TRƯỚC/TIẾP ✓,
  CHỌN TẬP ✓, ÂM THANH & PHỤ ĐỀ ✓. SKIP INTRO vắng mặt là đúng (GONE mặc
  định). **Speed bị cắt còn "TỐ", Lock không thấy (D12).** Gate web Speed:
  **không áp dụng được — WebPlayerActivity không mở lần nào trong cả phiên**
  (activities chỉ có MainActivity 90 + PlayerActivity 38; "WebPlayerActivity"
  trong `qa_session.json` chỉ xuất hiện trong text mô tả mission). VOD lần này
  chạy trên PlayerActivity (native), không phải WebPlayer.
- **Thanh player lúc nghỉ và lúc focus: ĐẠT MỘT PHẦN.**
  - VOD: knob trắng thấy rõ cả lúc nghỉ lẫn lúc focus (step_087–089/093,
    f_005/f_007); phần đã phát đỏ rõ; phần chưa phát xám vừa — **không phân
    biệt được đoạn buffered xám nhạt riêng** trên ảnh tĩnh; nhãn giờ đọc rõ,
    không nhảy (tổng luôn 19:17–19:18).
  - Live (Thể thao): chấm đỏ LIVE ở đầu phải ✓; knob trắng ở 00:00 — vị trí
    00:00 trên luồng live là lạ (xem gate ở trên); phần buffered không phân
    biệt được (track tối, bị chữ quảng cáo của luồng đè lên).
  - EPG (IPTV): thanh mỏng không knob **không quan sát được** (xem trên).
- **BACK: không thống nhất (D15).** Thể thao/IPTV: 2 BACK (ẩn OSD → thoát);
  VOD: 1 BACK (thoát ngay). Dialog nào cũng đóng bằng BACK (RoomPicker,
  EpisodePicker, Settings) và focus về đúng chỗ.
- **Phụ đề: chưa kiểm chứng được vị trí trên OSD bar.** Không ảnh nào có phụ
  đề + OSD bar cùng lúc. Phụ đề thấy ở mép dưới khi OSD ẩn (step_104, ảnh 15)
  — bình thường.
- **R1: ĐÃ SỬA** (step_001, step_121).
- **Dialog cài đặt thống nhất: ĐẠT.** Cùng một dialog 4 nhóm ở cả VOD
  (step_090) và player native (step_106/112), chọn chip cập nhật được
  ("Cao nhất (nét) ✓", "Đang chọn: …" đổi theo).

---

## 8. Điểm 75/100 — có công bằng không?

**Không công bằng nếu hiểu là "chất lượng build".** 75/100 = 100 − 5 (finding #1)
− 5 (finding #2) − 15 (finding #3, HIGH). Hai finding MEDIUM là **lỗi detector
thuần túy** (pixels chứng minh ngược lại — §4). Chỉ còn 1 vấn đề thật trong 3
findings → **điểm đã khử artifact ≈ 85/100** (100 − 15 cho D11).
So với lần FPT 55/100: lần đó 9 findings nhưng thực chất ~3 vấn đề (điểm khử
trùng lặp ~85–90); lần này 3 findings nhưng thực chất 1 vấn đề — cùng một mức
chất lượng cảm nhận (~85), điểm số khác nhau chỉ vì cách đếm.
**Nhưng 75/100 cũng không nên bị bỏ qua:** D11 là HIGH thật và chặn cả một tính
năng (chọn tập phim); D8/D9/D10/D12 là các lỗi nhìn thấy được mà judge không
ghi (judge chỉ ghi 3 findings — nó bỏ sót các lỗi trực quan rõ ràng nhất trên
màn hình chính). Và ngược lại, điểm số không phản ánh các khoảng chưa test:
WebPlayer (0 bước), EPG bar/Mini-Guide IPTV, gate seek Thể thao, UP lên nav từ
hàng đầu các tab ngoài Home — những chỗ này chưa có điểm nào cả, tốt hay xấu
đều chưa biết.

---

## 9. Vấn đề của harness (không phải lỗi app, nhưng ảnh hưởng lần chạy sau)

1. **Detector focus sai (N14):** `has_focus_ring` False dù viền trắng rõ;
   `focused_view: NONE` dù nút OSD đang focus có viền. Đây là nguyên nhân
   trực tiếp của 2/3 findings. Cần sửa detector (đọc đúng trạng thái focus
   trên cardRoot/nút OSD) trước khi tin điểm số lần chạy sau.
2. **Mission "pass" lỏng lẻo:** chỉ 5/16 mission COMPLETE_MISSION; 11 mission
   bị bỏ giữa chừng bằng SWITCH_TAB nhưng không bị tính là fail. Mission
   "VOD seek/resume" được hoàn thành (step_94) dù WebPlayer chưa từng mở.
3. **Tab detector kẹt:** summary ghi Kho Phim 66 thao tác / Home Hub 14 trong
   khi ảnh cho thấy AI chủ yếu ở Home/Thể thao/Lịch trình; tab 0 Trực Tiếp ghi
   0 thao tác dù AI đã ở màn hình Thể thao steps 12–22.
4. **Video chưa phải full tour 1x:** merge đã chạy (22 chunk, `concat.txt` có)
   nhưng kết quả nén ~8x và thiếu đầu + cuối phiên (§3). Cần kiểm tra vì sao
   recorder chỉ giữ ~469 s cho phiên 3967 s.
5. **Ảnh mission trùng lặp:** 12/17 ảnh mission trùng step shot (N13) — ảnh
   mission chụp cuối mission sau khi AI đã di chuyển, ít giá trị kiểm chứng.

---

## 10. Sửa trước full QA run? — Khuyến nghị

### Sửa ngay (nhỏ, sửa xong chạy full run sẽ sạch hơn)

1. **D11 (HIGH) — EpisodePickerDialog: set focus ban đầu + cuộn sheet vào
   tầm nhìn khi mở.** Đây là HIGH duy nhất và chặn cả tính năng chọn tập —
   bắt buộc sửa trước full run, nếu không full run sẽ ghi lại đúng finding này.
2. **D10 — pill "0":** áp cùng logic `validKickoff` (loại `"0"`/`"0'"`) cho
   layout thẻ ở tab Thể thao — thẻ hàng home đã hết pill "0", chỉ còn layout
   tab Thể thao. Sửa 1 chỗ, kiểm chứng bằng ảnh thẻ Inter/Villarreal.
3. **D12 — hàng nút VOD tràn:** rút ngắn nhãn ("TỐC ĐỘ" → nhãn ngắn hơn hoặc
   icon + chữ ngắn) hoặc cho hàng nút cuộn để lộ Speed/Lock; kiểm chứng bằng
   ảnh OSD VOD thấy đủ nút cuối.
4. **D8 + D9 — va chạm ở top nav/billboard:** cho nav chuyển nền đặc
   #E6141414 ngay khi billboard bắt đầu trượt dưới nav (hoặc thêm padding
   trên để tiêu đề không trượt lên dưới nav); dời cụm đồng hồ/ngày khỏi vùng
   TÌM KIẾM/CÀI ĐẶT. Đây là lỗi nhìn thấy trong **mọi** ảnh home — sửa trước
   full run để ảnh full run sạch.

### Để Evelyn duyệt (quyết định thiết kế / điều tra thêm, không chặn full run)

- **D17** — TRANG CHỦ thiếu gạch chân đỏ + chấm đỏ bí ẩn: cần đáp án thiết kế
  (chấm đỏ là gì?) trước khi sửa.
- **D14** — OSD Thể thao không focus được: cần xác định là thiết kế (OSD tự
  hiện, phím tác động trực tiếp) hay thiếu focus — nếu là thiết kế thì không
  sửa, chỉ cần ghi nhận.
- **D15** — BACK 1 lần (VOD) vs 2 lần (Thể thao/IPTV): thống nhất chỉ sau khi
  Evelyn chọn một hành vi (spec nói BACK 3 cấp; VOD hiện thoát ngay sau 1 lần).
- **D16** — ô tìm kiếm không khung: kiểm tra có phải thiết kế borderless
  không rồi mới thêm khung.
- **D13** — dialog cài đặt cắt chip + cắt dòng cuối: cosmetic, dialog cuộn
  được; sửa padding trong đợt polish sau.
- **N8/N9/N10** — dữ liệu (tỉ số 8-5/4:7, phòng 0 lượt xem, "Đang chiếu: 113
  online"): vấn đề phía nguồn dữ liệu, cần đối chiếu field nguồn trước khi
  sửa UI.
- **D5, nửa phụ đề của D7, gate seek Thể thao, EPG bar/Mini-Guide IPTV,
  UP lên nav từ hàng đầu các tab ngoài Home, WebPlayer** — tất cả đều
  **chưa kiểm chứng được trong quick run này**; full run cần mission ép các
  đường này (đặc biệt: mở WebPlayer thật, bấm LEFT/RIGHT ở player Thể thao,
  bấm UP từ hàng đầu mỗi tab, gọi OSD dưới ở player IPTV) thì mới có kết luận.

### Không merge

Đây là quick run. Branch `redesign/netflix` vẫn chờ full QA run + Evelyn
duyệt APK và ảnh chụp trước khi merge vào `main` (Task 11 Step 6).

# Đánh giá trực quan QA — CI run 42563696308 (Fix 5, commit 49ea066)

- **Run:** 42563696308 · **Branch:** `redesign/netflix` · **Commit:** `49ea066` (Fix 5)
- **Phiên:** `QA-SESS-20261109-045116-6b6f9e` · **Thời lượng:** 3016,5 s (~50 phút) · **Điểm judge (OPENAI):** 98/100
- **Checks:** 16/16 · **Missions:** 16/16 · **Steps:** 129 · **D-pad:** 126 lần · **Findings của judge:** 1 (LOW, step 26)
- **Độ bao phủ tab:** **2/7 (28,6%) — Kho Phim 98 thao tác, Home Hub 4, Live / Lịch / IPTV / Tìm kiếm / Cài đặt đều 0**
- **Phương pháp:** đọc trực tiếp bằng mắt từng ảnh, đối chiếu `qa_session.json` (timeline, focus, motion) và `qa_report.json`, quét pixel để đo thanh bar đỏ, phóng to crop để kiểm tra chi tiết nghi ngờ. Không tin điểm số hay kết luận của judge khi chưa có bằng chứng hình ảnh.
- **Độ phủ xem trực tiếp:** **17 ảnh mission + 35 ảnh step + 12 frame video tour + 3 crop phóng to** = **45/84 ảnh unique** trong tổng số 146 file (nhiều file trùng nhau từng pixel — xem mục B.2). 39 ảnh unique còn lại chưa mở xem từng ảnh — được mô tả theo timeline trong mục B.2, ghi rõ là chưa eyeball.
- **Lưu ý về cách đặt tên ảnh:** như run trước, ảnh mission `NN_mission_*.jpg` là ảnh **cuối mission** (sau khi AI đã BACK/chuyển tab), nên tên mission thường **không khớp** nội dung ảnh (vd: ảnh 09 mission "sidebar rail" thực ra là Home; ảnh 14 mission "VOD seek" thực ra là Home). Bằng chứng player thật nằm ở các **ảnh step**.
- **Lưu ý về độ phân giải:** ảnh chụp trong run này vẫn là **960×540**. Video tour là **1280×720** nên một số chi tiết (dialog lỗi, nav ghost) nhìn rõ hơn trong video.
- **Lưu ý về timeline focus:** `qa_session.json` ghi `focus=NONE` cho **mọi** step PlayerActivity (26–32, 104–115), nhưng ảnh chụp cho thấy viền trắng focus rõ ràng trên nút `PHÁT` (steps 26–28, 30–31), `THỬ LẠI` (steps 29, 32) và từng nút hàng VOD (steps 104–112). **Trường focus của timeline không đáng tin cho PlayerActivity** — mọi kết luận về focus dưới đây dựa trên ảnh, không dựa trên timeline.

---

## A. Ảnh mission (01–17) — mô tả bằng mắt

### 01_cold_start.jpg — Dialog Telegram lúc khởi động lạnh
Dialog `THÔNG BÁO — NHÓM THẢO LUẬN & HỖ TRỢ TRỰC TUYẾN`, QR + `Nhóm Telegram: @kenhlivetv`, 2 nút `ĐÃ HIỂU / ĐÓNG` (đỏ, focus) và `VÀO NHÓM TELEGRAM`. Sạch, không cắt chữ. Phía sau dialog mờ mờ là Home (hàng `TRẬN CẦU SẮP DIỄN RA`, poster phim).

### 02_mission_cold_start.jpg — Home, focus card Khaan (KHÔNG phải hero)
Hàng `ĐANG PHÁT TRỰC TIẾP` (đã cuộn lên): `Khaan… VS Khovd…` (focus viền trắng, `Đang trự… 255,5K xem · 5 phòng`), `Beijing… VS Chongq…` (`26,0K xem`), `Atletic… VS FC …`. Toàn `VS`, không tỉ số. Hàng `TRẬN CẦU SẮP DIỄN RA`: `Khaan… 12:00 Khovd…` (`Còn 8p`), `Fujian… 14:00 Hebei…` (`Còn 2h 8p`), `Qingda… 14:00 Wu…`. Cuối ảnh là hàng `PHIM ĐANG THỊNH HÀNH`. Chấm đỏ nhỏ sau chữ `TRANG CHỦ` trên nav vẫn còn (D17).

### 03_mission_sports_multi_source.jpg — Home, giống ảnh 02 nhưng cuộn khác
Như ảnh 02, focus vẫn ở card Khaan; card live có thêm badge `SOCO` + `● LIVE` và vạch đỏ dưới mỗi card. Không tỉ số ảo. **Ảnh 03 và 04 giống hệt nhau từng pixel.**

### 04_mission_sports_room_picker.jpg — Home (TRÙNG ảnh 03, KHÔNG phải dialog chọn phòng!)
Giống hệt ảnh 03. Mission tên "room picker" nhưng ảnh cuối mission chỉ là Home — dialog chọn phòng thật nằm ở steps 015–018 (mục B).

### 05_mission_sports_data_accuracy.jpg — Home, đã cuộn ngang sang phải
Card live: `Khaan… VS Khovd…` (`255,5K`), `Beijing… VS Chongq…` (`26,0K`), `Atletic… VS FC Bar…` (`1,0K xem` — Atletico vs Barcelona chỉ 1,0K lượt xem trong khi Khaan ở giải VĐQG Mông Cổ có 255,5K; dữ liệu feed, ghi nhận ở mục F). Toàn `VS`. Hàng sắp diễn ra focus ở card `Fujian… 14:00 Hebei…`. **Chữ `[OK] XEM NGAY` / `[MENU] CHỌN PHÒNG` của hero mờ mờ xuyên qua thanh nav trên cùng** (nav ghost D8 — thấy rõ hơn trong video, mục C).

### 06_mission_player_streaming_and_controls.jpg — Sport player, trận Fujian vs Hebei, MÀN HÌNH ĐEN + ĐANG TẢI
Ảnh Sport duy nhất trong nhóm mission: nền đen hoàn toàn (không có 1 khung hình video nào), top bar `◀ QUAY LẠI` + pill `FUJ - HEB` (không tỉ số, không phút — đúng vì trận 14:00 chưa đá), giữa màn hình nút `▶ PHÁT` (có viền trắng) đè lên spinner + chữ `Đang tải nguồn…` (chữ bị nút PHÁT che một phần), dưới cùng thanh bar `KÊNH TIẾNG | 00:00 | [vạch đỏ] ● | Về trực tiếp | TRỰC TIẾP | TÙY CHỌN | TỈ LỆ`. **Toast trắng `Mạng chập chờn: Đang tự kết nối lại luồng…` nổi giữa thanh bar dưới, che mất một phần nút `Về trực tiếp`.** Không có nút ±30s. Đây là ảnh cuối mission "player streaming" — và là bằng chứng đầu tiên rằng Sport player **không phát được gì** trong run này (xem mục B, E).

### 07_mission_home_hub_3_cards_and_canva_logos.jpg — Home, focus card Man Utd
Như ảnh 03/05 nhưng đã cuộn ngang: `Beijing… VS Chongq…` (`26,0K`), `Atletic… VS FC Bar…` (`1,0K`), `Manch… VS Aston…` (focus viền trắng, `1,0K xem`). Không có "3 card Home Hub" hay giao diện Hub riêng biệt nào — chỉ là Home cuộn ngang. Toàn `VS`.

### 08_mission_schedule_epg_and_fixture_tap.jpg — Home, hàng phim (KHÔNG phải Schedule!)
Cuộn xuống hàng `PHIM ĐANG THỊNH HÀNH`: 6 poster `Cuộc Chiến Ẩm Thực 2026`, `Mục Thần Ký 2024`, `Bắt Đầu Với Chí Tôn Đan Điền 2025`, `Xa Ngoài Kia Nơi Loài Tôm Hát 2022`, `Thần Tài Đậu Chiêm Long 2026`, `Thái Cổ Thần Tôn 2026`. Tiêu đề dài bị cắt/ngắt dòng (`Bắt Đầu Với Chí… Tôn Đan Điền`). Không có màn hình Lịch Thi Đấu nào trong ảnh này — Schedule không được mở trong cả run (0 thao tác).

### 09_mission_sidebar_rail_full_traversal.jpg — Home, focus poster phim (KHÔNG có rail!)
Giống khung 08 nhưng focus viền trắng ở poster `Cuộc Chiến Ẩm Thực`. **Không có sidebar rail nào** sau 7 lần DPAD_LEFT (steps 48–54). Rail không mở — lần thứ 3 liên tiếp (xem mục F).

### 10_mission_iptv_categories_and_favorites.jpg — Home (TRÙNG step_059, KHÔNG phải IPTV!)
Giống ảnh 03 (Home, focus card Khaan). Mission tên "IPTV" nhưng AI chưa bao giờ rời Home ở mission này. Không có màn hình IPTV nào trong cả run (0 thao tác).

### 11_mission_iptv_epg_and_zapping_player.jpg — Home (KHÔNG có player IPTV!)
Giống ảnh 10, focus vẫn card Khaan. Không có player IPTV, không có zapping — mission "zapping player" nhưng AI chỉ ở Home.

### 12_mission_phim_nguonc_and_categories.jpg — Home (KHÔNG phải Kho Phim!)
Giống ảnh 10/11. Mission tên "Kho Phim" nhưng ảnh cuối mission vẫn là Home — AI chưa vào tab Kho Phim ở mission này (tab Kho Phim chỉ được "đếm" qua các thao tác ở Home, xem mục H).

### 13_mission_phim_episode_picker_and_favorite.jpg — Hero Khaan (KHÔNG phải episode picker!)
Hero banner: `● TRỰC TIẾP · Giải VĐQG Mông Cổ`, `Khaan Khuns-Erchim FC VS Khovd Western`, `Trực tiếp · Giải VĐQG Mông Cổ · BLV Củ Cải · Tín hiệu HD`, `255,5K` lượt xem, nút `[OK] XEM NGAY` (đỏ) + `[MENU] CHỌN PHÒNG`. Hero sạch, không tỉ số. Không có dialog chọn tập nào — AI không mở episode picker trong cả run.

### 14_mission_vod_player_seek_and_resume.jpg — Home, hàng phim (KHÔNG có VOD player!)
Giống khung 08/09, focus poster `Thái Cổ Thần Tôn` (card cuối hàng phim, có viền trắng). Không có VOD player trong ảnh này — VOD player thật nằm ở steps 104–115 (mục B).

### 15_mission_player_settings_dialog.jpg — VOD OSD khi TẠM DỪNG, 02:01 / 1:10:13 (TRÙNG step_114)
`Cuộc Chiến Ẩm Thực - Tập 01`, tiêu đề căn giữa 1 dòng; thanh trượt dọc trái (độ sáng) + icon bánh răng; seek bar `02:01 / 1:10:13` (núm đỏ); hàng nút dưới đã **cuộn sang phải**: nút đầu chỉ còn một vệt xám ở mép trái, tiếp theo `TUA -10S / TUA +10S / TẬP TRƯỚC / TẬP TIẾP / CHỌN TẬP / ÂM THANH & PHỤ ĐỀ / TỐC ĐỘ` — **nút `TỐC ĐỘ` hiện đầy đủ, có khoảng thở ở mép phải**. Không có focus trắng trên nút nào trong ảnh này. Không có phụ đề. **Không có settings dialog nào** — tên mission không đúng với những gì AI đã làm (chỉ phát phim + di chuyển focus trong hàng nút).

### 16_mission_search_and_settings_feedback.jpg — Chi tiết phim, focus nav LỊCH TRÌNH
`Cuộc Chiến Ẩm Thực`, `2026 · Chính Kịch`, mô tả `The Table: K-Chef 2026…`, nút `XEM NGAY` (đỏ), `CHỌN TẬP`, `+ LƯU PHIM`, `PHIM KHÁC`; `DANH MỤC: Tất Cả / Lịch Sử Xem / Tìm Kiếm / Mới Cập Nhật / Phim Bộ / Phim Lẻ / Anime & H…`; `TIẾP TỤC XEM — 1 phim`. **2 lỗi cũ vẫn còn nguyên:** (1) nút back tròn (◀) ở góc trái **che mất chữ `C` đầu tiên của tiêu đề** (đọc thành `uộc Chiến Ẩm Thực`); (2) dòng chữ mờ `…ĐẶC SẮC` bị cắt dở phía sau thanh nav trên cùng. Focus viền trắng ở nav `LỊCH TRÌNH` trong khi tab đang chọn là `KHO PHIM` (gạch đỏ dưới KHO PHIM). **Không có màn hình Tìm kiếm hay Cài đặt nào** — mission tên "Search & Settings" nhưng AI chỉ ở chi tiết phim.

### 17_mission_dpad_chaos_stress_and_recovery.jpg — Chi tiết phim, focus nav TRUYỀN HÌNH
Giống khung 16, focus viền trắng chuyển sang nav `TRUYỀN HÌNH` (vẫn đang ở màn hình chi tiết phim, tab `KHO PHIM`). Back vẫn che chữ `C`, chữ mờ sau nav vẫn còn. App không crash sau chuỗi DPAD chaos — màn hình vẫn bình thường, focus di chuyển được.

---

## B. Ảnh step

### B.1 Đã xem trực tiếp (35 ảnh step + 17 ảnh mission)

#### MISSION_COLD_START — steps 1–5
- **step_001** (t=21s): = ảnh mission 01 (dialog Telegram, `ĐÃ HIỂU / ĐÓNG` focus đỏ). Sạch.
- **step_003** (chưa xem từng ảnh — xem B.2) / **step_005** (= ảnh mission 02): Home, focus card Khaan.

#### MISSION_SPORTS_ROOM_PICKER — steps 14–19 (dialog chọn phòng Khaan)
- **step_015** (t=275s) và **step_016** (t=285s): Dialog `Khaan Khuns-Erchim FC vs Khovd Western — Giải VĐQG Mông Cổ · 5 phòng live`: `BLV Củ Cải (Lv.7) — 62,8K lượt xem · LIVE · Điểm: 215,3K`, `TẠ BIÊN GIỚI (Lv.6) — 62,8K · Điểm: 151,3K`, `BLV ĐÓM (Lv.3) — 62,6K · Điểm: 15,2K`, `BLV RÔSI (Lv.5) — 33,6K · Điểm: 47,9K`, `SAO LA (Lv.4)` (bị cắt ở mép dưới dialog). Dialog sạch, không cắt chữ, **phòng có lượt xem thật** (khác hẳn phòng Fujian ở step_025 — xem dưới). Lần này không thấy chuỗi Trung Quốc `(最高等级)` như run trước. Focus di chuyển qua các hàng phòng (step_017 focus ở hàng `BLV ĐÓM`).
- **step_017** (t=295s): = dialog trên, focus ở hàng `BLV ĐÓM (Lv.3)`.
- **step_019** (chưa xem — xem B.2): BACK đóng dialog.

#### MISSION_PLAYER_STREAMING_AND_CONTROLS — steps 24–32 (Sport player — 7 step duy nhất)
- **step_024** (t=398s): = ảnh mission 05 (Home, focus card `Fujian… 14:00 Hebei…` ở hàng sắp diễn ra). Lưu ý: trận này **chưa bắt đầu** (14:00, lúc đó ~11:58, `Còn 2h 8p`).
- **step_025** (t=414s): Dialog chọn phòng `Fujian Nanan Women vs Hebei Snow Ruyi Women — CHA CFA · 2 phòng live`: `5 LỬA — 0 lượt xem · LIVE`, `PEANUT — 0 lượt xem · LIVE`. Cả 2 phòng đều `0 lượt xem` — nhưng trận chưa đá nên 0 là hợp lý (không có card lượt xem nào để đối chiếu, khác trường hợp Piratas run trước). Dialog sạch.
- **step_026** (t=472s) — **STEP CỦA FINDING DUY NHẤT**: Sport OSD, **màn hình đen hoàn toàn** (không video). Top: `◀ QUAY LẠI` + pill `FUJ - HEB` (không tỉ số, không phút — đúng vì trận chưa đá). Giữa: nút `▶ PHÁT` **có viền trắng focus rõ** đè lên spinner + chữ `Đang tải nguồn…` (chữ bị nút che một phần). Dưới: `KÊNH TIẾNG | 00:00 | [vạch đỏ] ● | Về trực tiếp | TRỰC TIẾP | TÙY CHỌN | TỈ LỆ`. **Có vạch đỏ** — xem đo pixel ở mục D, Fix 5 item 5. Không có nút ±30s. Motion 0.00%, không phát.
- **step_027** (t=529s): Giống hệt step_026 nhưng spinner/chữ tải đã mất — vẫn màn hình đen, `PHÁT` vẫn focus trắng, vạch đỏ vẫn đó. Video vẫn không phát. (= step_028, cùng sha256.)
- **step_028** (t=584s): Giống hệt step_027 (AI bấm MENU — **không có tác dụng gì nhìn thấy được**, không mở Server Picker hay menu nào).
- **step_029** (t=640s): **Dialog lỗi** `Lỗi Phát Luồng Video` — `Mạng lỗi — … vào lại sau`, 3 nút `THỬ LẠI` (viền trắng) / `QUAY LẠI` / `BÁO LỖI`, dòng `Báo lỗi kênh qua nhóm Telegram: @kenhlivetv`. **LỖI MỚI: nút `▶ PHÁT` ở giữa màn hình vẫn hiện ĐÈ LÊN dialog, che mất giữa tiêu đề (`Lỗi [PHÁT] Video`) và che một phần dòng `Mạng lỗi…`** (xem crop ở mục B.3). Dialog vẫn dùng được nhưng thông báo bị che. Vạch đỏ dưới vẫn hiện. (= step_032, cùng sha256.)
- **step_030** (t=702s): Quay lại trạng thái đang tải (`Đang tải nguồn…`, `PHÁT` focus) sau khi AI bấm `THỬ LẠI` — tức retry đã chạy nhưng vẫn chưa có video. (= step_031, cùng sha256.)
- **step_031** (t=761s): Giống hệt step_030 (AI bấm MENU — lại không có tác dụng). Timeline ghi `motion=0.56, is_playing=True` — nhưng ảnh là màn hình đen + spinner tải, **không phải video đang phát** (xem mục E: AI/judge đã đọc sai motion của spinner thành "phát thành công").
- **step_032** (t=815s): **Dialog lỗi lại hiện** (giống hệt step_029, `THỬ LẠI` focus) — sau BACK của AI. Tức là sau retry, lỗi quay lại. Đây là ảnh Sport cuối cùng; step_033 AI đã về Home.

#### MISSION_HOME_HUB / SCHEDULE / RAIL — steps 33–54 (toàn Home)
- **step_043** (t=1041s): **Hero banner đầy đủ lần đầu trong run**: `● TRỰC TIẾP · Giải VĐQG Mông Cổ`, `Khaan Khuns-Erchim FC VS Khovd Western`, `Trực tiếp · Giải VĐQG Mông Cổ · BLV Củ Cải · Tín hiệu HD`, `255,5K` lượt xem, `[OK] XEM NGAY` (đỏ) + `[MENU] CHỌN PHÒNG`, đồng hồ góc phải `11:51 · Thứ Hai, 09/11/2026 · 01/10 ÂL · Ất Tỵ`. Hero sạch, không tỉ số. (Xác nhận giờ phiên ~11:51 VN — trận Fujian 14:00 còn ~2h nữa mới đá.)
- **step_044** (t=1051s): Home, focus card `Qingda… 14:00 Wuhan…` (hàng sắp diễn ra). Live: Beijing `26,0K`, Atletico `1,0K`, Man Utd `1,0K`.
- **step_050** (t=1134s): Home, focus card `Khaan… 12:00 Khovd…` (hàng sắp diễn ra), hàng `PHIM ĐANG THỊNH HÀNH` phía dưới. Đây là nhóm step "rail traversal" (48–54: DPAD_LEFT ×7) — **focus chỉ di chuyển trong lưới card, không có rail nào mở**.
- **step_085** (t=1793s): = hero như step_043 (11:51, Khaan). Thuộc mission "episode picker" — nhưng AI vẫn đang ở Home, chưa vào chi tiết phim.
- **step_090** (t=1864s): Home, focus card `Beijing… VS Chongq…` (`26,0K`). Nav ghost `[OK] XEM NGAY` xuyên qua nav thấy rõ.
- **step_097** (t=1958s): Home đã cuộn, focus card `Fujian… 14:00 Hebei…`. Thuộc mission "player settings dialog" — vẫn là Home.
- **step_098** (t=1971s): Home, focus card Beijing; góc phải trên có pill `● LIVE` đỏ ló ra sau nav (bị nav che một phần) — một dạng khác của nav ghost.

#### MISSION_PHIM / VOD — steps 101–115 (VOD player — 12 step duy nhất)
- **step_101** (t=2015s): Home, hàng `PHIM ĐANG THỊNH HÀNH` + hàng `KÊNH TRUYỀN HÌNH NỔI BẬT` (`360 Anime`, `360 Bundesli…`, `360 C1 Châu…`, `360 C2 Châu…`, `360 C3 Châu…`, `360 Công Th…`, đều có badge `LIVE`). Đây là lần duy nhất trong run thấy tên kênh IPTV — nhưng chỉ là một hàng trên Home, không phải tab IPTV. Focus ở poster `Thái Cổ Thần Tôn`.
- **step_102** (t=2026s): Chi tiết phim `Cuộc Chiến Ẩm Thực` — back tròn focus trắng (viền quanh nút back), tiêu đề đọc thành `uộc Chiến Ẩm Thực` (chữ `C` bị nút back che), chữ mờ `…ĐẶC SẮC` sau nav. `XEM NGAY` đỏ, `CHỌN TẬP`, `+ LƯU PHIM`, `PHIM KHÁC`; `Phim Mới Cập Nhật — 120 phim`.
- **step_103** (t=2038s): Giống step_102 nhưng focus chuyển sang `XEM NGAY` (viền trắng). Chuẩn bị vào VOD player.
- **step_104** (t=2160s): **VOD player đã vào (PlayerActivity, native)** — `Cuộc Chiến Ẩm Thực - Tập 01`, cảnh đêm (loa phóng thanh trên cây). OSD mở: tiêu đề căn giữa 1 dòng; thanh trượt dọc trái + bánh răng; seek bar `01:49 / 1:10:25` (tiến trình đỏ + núm đỏ); hàng nút `PHÁT` (**viền trắng, hiện đầy đủ, có khoảng thở**) `/ TUA -10S / TUA +10S / TẬP TRƯỚC / TẬP TIẾP / CHỌN TẬP / ÂM THANH & PHỤ [bị cắt ở mép phải]`. **Không có phụ đề trong ảnh này.** Không có nút PIP. Không thấy `SKIP INTRO`, không thấy nút `Lock`.
- **step_105** (t=2219s): VOD tạm dừng `02:01 / 1:10:13`, cảnh bếp (khung hình đã đổi — video đã phát được từ 01:49 lên 02:01 rồi dừng). `PHÁT` focus trắng, đầy đủ. Hàng nút vẫn như step_104, nút cuối `ÂM THANH & PHỤ` bị cắt ở mép phải. Không phụ đề.
- **step_106** (t=2277s): Giống step_105, focus chuyển sang `TUA -10S` (viền trắng). Thời gian đứng yên `02:01 / 1:10:13`. Không phụ đề.
- **step_107** (t=2334s): Focus `TUA +10S`. Thời gian vẫn `02:01`. Không phụ đề.
- **step_108** (t=2391s): Focus `TẬP TRƯỚC`. Thời gian vẫn `02:01`. Không phụ đề.
- **step_109** (t=2451s): Focus `TẬP TIẾP`. Thời gian vẫn `02:01`. Không phụ đề.
- **step_110** (t=2507s): Focus `CHỌN TẬP`. Thời gian vẫn `02:01`. Không phụ đề.
- **step_111** (t=2564s): Focus `ÂM THANH & PHỤ ĐỀ` — nút này vẫn bị cắt ở mép phải (`ÂM THANH & PHỤ` + một vệt `I`), hàng nút **chưa cuộn**. Thời gian vẫn `02:01`. Không phụ đề.
- **step_112** (t=2652s): **HÀNG NÚT ĐÃ CUỘN SANG PHẢI** — nút đầu `PHÁT` giờ chỉ còn một vệt xám ở mép trái, các nút `TUA -10S / TUA +10S / TẬP TRƯỚC / TẬP TIẾP / CHỌN TẬP / ÂM THANH & PHỤ ĐỀ / TỐC ĐỘ` hiện ra, **nút `TỐC ĐỘ` hiện đầy đủ và có viền trắng focus**. Lần đầu tiên trong mọi run QA thấy nút Speed hiện đầy đủ + được focus trên màn hình. Thời gian vẫn `02:01 / 1:10:13`. Không phụ đề.
- **step_113** (t=2714s): Focus rời khỏi hàng nút (AI bấm DPAD_UP — không còn viền trắng trên nút nào; núm seek trông to/đỏ hơn, có thể focus đã lên seek bar). Hàng nút **vẫn giữ trạng thái đã cuộn** (PHÁT là vệt ở mép trái, `TỐC ĐỘ` đầy đủ). Thời gian vẫn `02:01`. Không phụ đề.
- **step_114** (t=2775s): = ảnh mission 15. Giống step_113 (AI bấm BACK lần 1 — OSD vẫn mở, ảnh không đổi). Thời gian vẫn `02:01`. Không phụ đề.
- **step_115** (t=2794s): OSD đã tắt — toàn màn hình video (cảnh bếp, không OSD, không phụ đề). BACK lần 2 mới thoát OSD (xác nhận thoát player cần 2 lần BACK như run trước).

#### Cuối phiên — steps 116–129
- **step_116** (t=2815s): Chi tiết phim (giống ảnh mission 16): back focus trắng, `uộc Chiến Ẩm Thực`, `TIẾP TỤC XEM — 1 phim` (resume đã ghi nhận sau khi xem VOD). Chữ mờ sau nav vẫn còn.

### B.2 Chưa xem trực tiếp từng ảnh (39 ảnh unique còn lại — mô tả theo timeline)

Các ảnh dưới đây **không được mở xem bằng mắt**; nội dung suy ra từ `qa_session.json` (activity, focus node, thời gian) và từ các ảnh trùng pixel đã xem.

- **step_002** (t=35s): MainActivity, focus ở vùng `Phim đang trending` (đang cuộn Home sau khi đóng dialog Telegram). **step_003, step_004** (t=56–71s): Home, focus qua card `Khaan 12:00` (2 ảnh giống hệt nhau).
- **step_007, step_008** (t=143–155s): Home, focus qua card `Beijing Guoan vs Chongqing` / `Khaan` (di chuyển ngang hàng live).
- **step_009, step_010** (t=168–180s): Home, focus qua `heroPlay`/`heroDetails` (2 cặp ảnh giống hệt nhau từng cặp).
- **step_018** (t=304s): dialog chọn phòng Khaan, focus hàng phòng thứ 4. **step_019** (t=313s): BACK đóng dialog.
- **step_021, step_022, step_023** (t=368–388s): Home, focus qua `Beijing`, `Atletico Madrid vs FC Barcelona`, `Qingdao 14:00` (di chuyển trong lưới Home).
- **step_036, step_037, step_038, step_040, step_041** (t=881–1029s): Home sau khi BACK khỏi Sport player — focus qua card `Fujian 14:00`, `Khaan 12:00`, `Beijing`, `Atletico`; 2 lần `SWITCH_TAB 6` (Home Hub) ở steps 33–34 nhưng màn hình vẫn là Home (theo thought của AI: "SWITCH_TAB(6) đã thất bại 2 lần").
- **step_045, step_047, step_049, step_051, step_052** (t=1069–1163s): Home, DPAD qua các card (Man Utd, Qingdao, Khaan, Beijing) — nhóm "Schedule" và "rail" nhưng thực chất chỉ là di chuyển focus trong lưới Home; **không có màn hình Schedule hay rail nào**.
- **step_056, step_057** (t=1219–1238s): Home, DPAD_UP qua card Khaan (nhóm "IPTV" nhưng vẫn ở Home).
- **step_066** (t=1423s): Home, BACK (nhóm "IPTV zapping" — vẫn ở Home, không mở player IPTV).
- **step_084** (t=1771s): Home, focus card Beijing (nhóm "episode picker" — vẫn ở Home).
- **step_087, step_088, step_089** (t=1827–1864s): Home, DPAD qua các card (Qingdao, Atletico, Beijing) — nhóm "VOD seek" nhưng vẫn ở Home.
- **step_093, step_094, step_095** (t=1904–1930s): Home, DPAD_LEFT qua các card phim (`view#[1244,463]`, `view#[946,463]`, `view#[648,463]` — vùng poster phim).
- **step_098** đã xem ở B.1. **step_100** (t=2002s): Home, focus `cardIptvRoot` (một card kênh IPTV trong hàng `KÊNH TRUYỀN HÌNH NỔI BẬT` trên Home — không phải tab IPTV).
- **step_117** (t=2843s): Chi tiết phim, focus `XEM NGAY` (giống step_103). **step_121, step_123** (t=2890–2912s): Chi tiết phim, focus qua nav `nav_live` / `nav_phim` (di chuyển trên nav trong khi đang ở chi tiết phim). **step_125, step_126** (t=2937–2947s): Chi tiết phim, focus qua nav `nav_search` / `nav_settings` (AI chỉ di chuyển focus trên nav, **không hề mở tab Tìm kiếm hay Cài đặt**).

### B.3 Crop phóng to (bằng chứng chi tiết)

- **Crop thanh bar dưới Sport** (`/tmp/crop_sport_bar.png`, từ step_026, phóng 2×): vạch đỏ rõ ràng, dày ~6px; đồng thời thấy **chữ `● TRỰC TIẾP` bị nút `TÙY CHỌN` lấn vào** — mép phải của chữ bị nút che (xem mục F.2).
- **Crop dialog lỗi Sport** (`/tmp/crop_sport_err.png`, từ step_029, phóng 2×): nút `▶ PHÁT` đè lên giữa dialog — tiêu đề đọc thành `Lỗi [PHÁT] Video`, dòng `Mạng lỗi — … vào lại sau` bị che đoạn giữa. 3 nút `THỬ LẠI / QUAY LẠI / BÁO LỖI` phía dưới vẫn đầy đủ, `THỬ LẠI` có viền trắng.
- **Crop hàng nút VOD step_112** (`/tmp/crop_vod_row112.png`, phóng 2×): hàng đã cuộn phải — nút đầu chỉ còn vệt xám ở mép trái, `TỐC ĐỘ` hiện đầy đủ với viền trắng focus.

---

## C. Video

### full_qa_tour.mp4 — TIMELAPSE ~8× TOÀN PHIÊN (khác hẳn run trước)
- `full_qa_tour.mp4`: **367,7 s**, 1280×720, H.264, 6,2 MB. Phiên thực 3016,5 s → video bằng **12,2% thời lượng thực**, tỉ lệ nén ≈ **8,2×**.
- Đối chiếu 12 frame trích (mỗi 30s) với timeline step:
  - **f_001 (video 0s):** Home, focus card Beijing (`26,0K`) — đầu phiên.
  - **f_002 (30s):** Home, focus card Qingdao 14:00.
  - **f_003 (60s):** **Sport player, dialog lỗi `Lỗi Phát Luồng Video`** (khớp steps 29/32, t≈640–815s) — ở 720p thấy rất rõ nút `PHÁT` đè lên dialog và chữ `TRỰC TIẾP` bị nút `TÙY CHỌN` lấn.
  - **f_004 (90s):** Home, focus card Fujian 14:00; **nav ghost thấy rất rõ**: chữ `[OK] XEM NGAY` / `[MENU] CHỌN PHÒNG` xuyên qua thanh nav.
  - **f_005 (120s):** Home, hàng phim, focus card Qingdao.
  - **f_006 (150s):** Home, hàng live (Khaan `255,5K`, Beijing `26,0K`).
  - **f_007 (180s):** Home, focus card Khaan; nav ghost lại thấy rõ.
  - **f_008 (210s):** Home, focus card Atletico (`1,0K`).
  - **f_009 (240s):** **VOD OSD ở `00:34 / 1:11:40`** — một khoảnh khắc **không có trong ảnh step nào** (step đầu tiên của VOD là 01:49): cảnh đêm, `PHÁT` focus trắng, hàng nút `PHÁT / TUA -10S / TUA +10S / TẬP TRƯỚC / TẬP TIẾP / CHỌN TẬP / ÂM THANH & PHỤ [cắt]`. **Không có phụ đề.** 00:34 + 1:11:40 = 1:12:14 (lại là thời gian còn lại — xem mục D, item 3).
  - **f_010 (270s):** VOD `02:01 / 1:10:13`, focus `TUA +10S` (= step_107). Không phụ đề.
  - **f_011 (300s):** VOD `02:01 / 1:10:13`, focus `ÂM THANH & PHỤ ĐỀ` (= step_111). Không phụ đề.
  - **f_012 (330s):** Chi tiết phim, nút back được focus (viền trắng), tiêu đề `uộc Chiến Ẩm Thực`, `TIẾP TỤC XEM — 1 phim` (≈ steps 116+).
- **Kết luận video:** khác run trước (tour chỉ là chunk cuối), tour lần này **là timelapse toàn phiên** — từ Home đầu phiên, qua Sport lỗi, tới VOD và chi tiết phim cuối phiên. Nó xác nhận thêm 2 điều: (1) VOD đã phát được từ ~00:00 tới 02:01 (frame f_009 ở 00:34 là bằng chứng duy nhất cho thấy video từng chạy trước khi dừng ở 02:01); (2) **không có phụ đề trong bất kỳ frame nào của video** — kể cả khi OSD đang mở (f_009, f_010, f_011). Tour không quay lại được room picker, dialog Telegram hay hero (chỉ lướt qua Home).
- `qa_timelapse.mp4`: 36,9 s — chỉ xem lướt, không trích frame chi tiết (tỉ lệ nén ~80×, giá trị kiểm chứng thấp).
- Không còn file chunk mp4 thô trong run này (chỉ có `full_qa_tour.mp4` + `qa_timelapse.mp4` + `concat.txt` trỏ tới các chunk trên máy CI, không có trong artifact).

---

## D. Verdict từng fix (nghiêm ngặt, kèm bằng chứng)

### Fix 5 — item 1: Phụ đề neo trên seek bar (setBottomPaddingFraction) — ⚪ **NOT SEEN — KHÔNG KIỂM ĐƯỢC**
- **Không có phụ đề trong bất kỳ ảnh VOD OSD nào của run này** (steps 104–114: 11 ảnh OSD, 0 phụ đề) và không có phụ đề trong bất kỳ frame video nào (f_009 ở 00:34, f_010/f_011 ở 02:01 — đều không có phụ đề). Video dừng ở 02:01 trong ~9 phút thời gian thực (steps 105–114, t=2219–2775s) ở 2 cảnh không có thoại (cảnh đêm, cảnh bếp).
- Vì không có phụ đề nào xuất hiện cùng lúc với OSD mở, **không thể đo khoảng cách** giữa đáy phụ đề và seek bar, không thể kết luận Fix 5 đã sửa được lỗi đè seek bar (steps 101/112 run trước) hay chưa, và cũng **không thể kiểm cảnh báo double-lift** (phụ đề bay cao ~65–80dp).
- Đây là lỗi của **bao phủ kiểm thử**, không phải bằng chứng fix sai: để kiểm item này cần một VOD có phụ đề hiện lên trong lúc OSD mở — run này không tạo ra được khoảnh khắc đó. **Không được ghi "đã sửa" cho item 1.**

### Fix 5 — item 2: Hàng nút VOD — "TẠM DỪNG" đầy đủ + cuộn tới Speed — ⚠️ **PARTIAL**
- **"TẠM DỪNG" hiện đầy đủ khi đang phát: NOT SEEN.** Trong cả run, nút đầu hàng nút **lúc nào cũng là `PHÁT`** (video tạm dừng) — không có ảnh nào chụp được trạng thái đang phát với OSD mở (video chỉ chạy từ 00:34 tới 02:01 trong lúc OSD đóng/tạm dừng, rồi đứng yên). Vì vậy không thể kiểm `minWidth="144dp"` có sửa được hiện tượng "TẠM DỪNG" bị cắt ở mép trái (steps 108/111/112 run trước) hay không.
- **Nút `PHÁT` khi tạm dừng: ĐẦY ĐỦ.** Steps 104–105: `PHÁT` hiện đầy đủ, có viền trắng focus, có khoảng thở 2 bên — không bị cắt như "TẠM DỪNG" ở run trước. (Lưu ý: `PHÁT` ngắn hơn `TẠM DỪNG` nên đây chỉ là bằng chứng yếu cho minWidth.)
- **Cuộn tới Speed: ✅ CONFIRMED — lần đầu tiên trong mọi run QA.** Step_112: sau 7 lần DPAD_RIGHT, hàng nút đã cuộn sang phải, **`TỐC ĐỘ` hiện đầy đủ với viền trắng focus** (crop phóng to xác nhận); steps 113–114 hàng giữ nguyên trạng thái đã cuộn. Khi hàng ở vị trí trái nhất (steps 104–111), nút cuối `ÂM THANH & PHỤ ĐỀ` vẫn bị cắt ở mép phải — đúng như kỳ vọng "hàng cuộn được, nút cuối chỉ hiện đủ sau khi cuộn phải". Khi cuộn hết phải, nút đầu `PHÁT` trở thành một vệt xám ở mép trái — đó là hành vi cuộn bình thường, không phải lỗi mới.
- Kết luận: nửa "Speed tới được" đã xong; nửa "TẠM DỪNG không bị cắt khi phát" vẫn chưa có bằng chứng trên màn hình.

### Fix 5 — item 3: Nhãn phải seek bar VOD = thời gian CÒN LẠI (by design) — ✅ **CONFIRMED, không hành động**
- Kiểm chứng bằng số (vị trí + số phải = 01:12:14 hằng số): step_104 `01:49 + 1:10:25`, steps 105–114 `02:01 + 1:10:13`, video f_009 `00:34 + 1:11:40`. **Nhãn phải vẫn hiển thị thời gian còn lại**, đúng thiết kế đã xác nhận (plan lines 77/116/644 + mẫu VOD "21:23"). Đây KHÔNG phải bug — là quyết định sản phẩm để Evelyn chọn (muốn tổng thời lượng thì đổi).

### Fix 5 — item 4: Pill Sport — phút khi vào phòng live + mã đội LEO/DEP — ⚠️ **PARTIAL (mã đội ✅, phút NOT SEEN)**
- **Mã đội: ✅ CONFIRMED không còn trùng.** Pill `FUJ - HEB` ở mọi ảnh Sport (steps 26–32, ảnh 06, video f_003) — 2 mã khác nhau, đọc được, không còn hiện tượng `CLU - CLU` như run trước. (Trận này không phải Club León/Guadalajara nên trường hợp `LEO`/`DEP` cụ thể chưa được kiểm trực tiếp — chỉ kiểm được "không còn gán cùng một mã cho 2 đội".)
- **Phút khi vào phòng live: NOT SEEN.** Trận duy nhất được vào player là Fujian vs Hebei Women, **trận chưa bắt đầu** (14:00, vào lúc ~12:00) — không có phút nào để hiển thị, pill không phút là đúng. Không có trận live nào được vào player trong run này (Khaan 12:00 đang live nhưng AI chỉ mở room picker rồi BACK ra, steps 14–19). Vì vậy fallback `meta.matchTimeMs` cho live-room entry **chưa được kiểm trên màn hình**.
- **Tỉ số:** pill không tỉ số — đúng trong trường hợp này (trận chưa đá, không có tỉ số; không có bug đài nào để đối chiếu vì màn hình đen, không có video).

### Fix 5 — item 5: Bar live Sport đỏ 100% — ✅ **CONFIRMED (có vạch đỏ — với 1 lưu ý về độ rộng)**
- **Bằng chứng pixel (quét step_026, ảnh 960×540):** dải pixel đỏ liên tục **x ≈ 258–469, y ≈ 513–518** — tức **rộng ~211px, dày ~6px**, màu RGB ≈ (205, 20, 26) (đỏ #E50914 sau nén JPEG), **lấp đầy ~100% chiều rộng của widget SeekBar**. Cộng thêm chấm đỏ `●` live ở x ≈ 502–509 cùng hàng. Vạch đỏ này xuất hiện **giống hệt nhau ở cả 7 ảnh Sport** (steps 26–32) và trong video f_003 (720p). Run trước: quét pixel không thấy vạch đỏ nào — nay đã có.
- **Lưu ý (không làm mất kết luận CONFIRMED):** widget SeekBar chỉ chiếm ~240px trong hàng dưới vì hàng dưới quá chật (KÊNH TIẾNG, 00:00, Về trực tiếp, TRỰC TIẾP, TÙY CHỌN, TỈ LỆ chen nhau) — nên trên màn hình vạch đỏ đọc thành "một đoạn đỏ ngắn", không phải "vạch đỏ full-width toàn màn hình" như mẫu Sport. Đây là giới hạn bố cục hàng dưới, không phải lỗi của riêng Fix 5.
- **Không có núm (thumb) trên vạch** — đúng với bar live không seek được.

### Fix 5 — item 6: Nút ±30s ẩn khi không seek được — ✅ **CONFIRMED (chiều ẩn); chiều hiện NOT SEEN**
- Không có nút ±30s nào trong bất kỳ ảnh Sport OSD nào (steps 26–32) — đúng gate (stream không seek được / trận chưa bắt đầu). Không có trường hợp nút ±30s xuất hiện sai trên stream live không seek được.
- Chiều ngược lại (nút ±30s **hiện** trên stream seek được) **không được kiểm** — không có stream Sport nào seek được trong run này (Sport duy nhất còn không phát được video).

### Fix 1 — Tỉ số ảo + fmtViewers M — ✅ **CONFIRMED (tỉ số); M tier vẫn NOT SEEN**
- Không có tỉ số bóng đá nào vượt quy tắc trong tất cả ảnh đã xem. Mọi card live, hero, room picker đều hiện `VS` (ảnh 01–17, steps 003–116). Không thấy tỉ số `2:8`/`4:12`/`13:8` nào.
- Định dạng `M` (`6,8M`) **vẫn chưa kiểm được**: lượt xem cao nhất trong run là `255,5K` (Khaan) — không có lượt xem nào ≥ 1M xuất hiện. Bóng rổ không được kiểm (không có trận NBA nào được mở).

### Fix 2 — Sport Player OSD gọn (back + pill, focus rõ, bar dưới rõ) — ✅ **CONFIRMED, với 2 vết mới (xem F)**
- Mọi ảnh Sport OSD (steps 26–32, ảnh 06): top bar chỉ còn `◀ QUAY LẠI` + pill; **focus viền trắng rõ trên `PHÁT`** (và trên `THỬ LẠI` khi dialog lỗi hiện); bar dưới đọc được (`KÊNH TIẾNG | 00:00 | [vạch đỏ] | Về trực tiếp | ● TRỰC TIẾP | TÙY CHỌN | TỈ LỆ`); **`Về trực tiếp` hiện ở cả 7 ảnh** — nhất quán, không còn lúc có lúc không như run trước.
- Vết mới: (1) nút `PHÁT` ở giữa đè lên dialog lỗi (mục F.1); (2) hàng dưới quá chật, chữ `TRỰC TIẾP` bị nút `TÙY CHỌN` lấn (mục F.2).

### Fix 3 — VOD Player OSD — ✅ **CONFIRMED (native); WebPlayer NOT SEEN (lần 3)**
- Native VOD (steps 104–114): tiêu đề 1 dòng căn giữa ✅; không có nút PIP ✅; thanh trượt dọc trái + bánh răng ✅; seek bar đầy đủ ✅; focus trắng rõ trên từng nút hàng dưới ✅.
- Vẫn chưa đạt mẫu `player-sample-vod.jpg`: không có cụm pause/±10s ở giữa màn hình; không thấy `SKIP INTRO`; không thấy nút `Lock` (không có điểm nào trong phim để kiểm SKIP INTRO trong run này).
- **WebPlayerActivity: KHÔNG TỚI — lần thứ 3 liên tiếp** (xem mục H). Không có settings dialog nào được mở (mission 15 chỉ phát phim + di chuyển focus).

### Fix 4 (đối chiếu nhanh)
| Fix 4 | Trạng thái run này |
|---|---|
| 4a — Hàng nút VOD hiện đầy đủ (dọc) + cuộn được (ngang) | ✅ **TIẾN BỘ RÕ**: chiều dọc đầy đủ ở mọi ảnh VOD OSD; chiều ngang nay **cuộn được tới Speed** (step_112) — hơn run trước |
| 4b — Phụ đề neo trên seek bar | ⚪ **NOT SEEN** — không có phụ đề nào trong run (xem Fix 5 item 1) |
| 4c — Nút Speed tới được | ✅ **CONFIRMED** — step_112 `TỐC ĐỘ` đầy đủ + focus |
| 4d — Pill Sport hiện phút | ⚪ **NOT SEEN** — không vào trận live nào (xem Fix 5 item 4) |
| 4e — Bar live Sport fallback | ✅ **ĐÃ ĐƯỢC FIX 5 THAY THẾ VÀ XÁC NHẬN** — vạch đỏ hiện (xem Fix 5 item 5) |

---

## E. Chấm finding duy nhất của judge (step 26, ExoPlaybackException)

| Finding (judge) | Phán quyết | Bằng chứng |
|---|---|---|
| LOW step 26: `ExoPlaybackException` khi phát trận Fujian Nanan Women vs Hebei Snow Ruyi Women từ phòng `5 LỬA`; màn hình hiện nút `PHÁT` và `Đang tải nguồn…` nhưng video không chuyển động (Motion 0.00%); "có thể là giới hạn emulator x86 thiếu codec" | **THẬT — nhưng mô tả thiếu và giả thuyết nguyên nhân chưa vững** | **step_026 đúng như mô tả:** màn hình đen, `PHÁT` focus, `Đang tải nguồn…`, motion 0.00%. **Nhưng judge chỉ kể một nửa câu chuyện:** dialog lỗi `Lỗi Phát Luồng Video` còn xuất hiện ở **step_029 và step_032** (2 lần hiện dialog, cùng 1 lần lỗi kéo dài), và **playback KHÔNG BAO GIỜ hồi phục** trong run này. |

**Phân tích chi tiết:**
- **Diễn biến thật (steps 26–32, t=472–815s):** tải (26) → vẫn đen (27) → MENU không tác dụng (28) → **dialog lỗi** (29) → bấm `THỬ LẠI` → tải lại (30) → MENU không tác dụng (31) → **dialog lỗi lại** (32) → BACK về Home. 7 step, **0 khung hình video nào** được phát.
- **"Đã phát thành công" ở step 31 là đọc sai.** Thought của AI ở step 31 viết: "Video đã bắt đầu phát thành công (Motion delta: 0.56%)". Nhưng **step_031 giống hệt step_030 từng pixel** (màn hình đen + spinner `Đang tải nguồn…`). Motion 0.56% gần như chắc chắn là **spinner loading đang quay**, không phải video. Sau "thành công" đó, step_032 lại hiện dialog lỗi — playback chưa từng hồi phục. Judge không phát hiện ra mâu thuẫn này.
- **Nguyên nhân: giả thuyết "emulator thiếu codec" chưa vững — có giải thích khớp hơn.** Trận Fujian vs Hebei Women **khởi tranh 14:00**, AI mở phòng lúc ~12:00 (`Còn 2h 8p`). Rất có thể **nguồn live chưa có gì để phát** (trận chưa bắt đầu) — lỗi là "chưa có luồng", không phải "codec không giải mã được". App hiển thị lỗi chung chung `Lỗi Phát Luồng Video / Mạng lỗi` cho một trận chưa đá — thông báo gây hiểu lầm (đáng lẽ phải là "trận chưa bắt đầu"). Không thể kết luận chắc chắn từ ảnh (cần kiểm log nguồn hoặc thử lại sau 14:00), nhưng mốc thời gian ủng hộ giả thuyết này hơn giả thuyết codec.
- **Stream failure hay app failure?** Lỗi gốc nằm ở **nguồn phát** (không có luồng / luồng lỗi), không phải crash app. Nhưng có **2 lỗi thuộc về app** đi kèm: (1) thông báo lỗi sai bản chất (trận chưa đá → báo "mạng lỗi"); (2) nút `PHÁT` ở giữa che mất nội dung dialog lỗi (mục F.1).
- **Không có lỗi phát nào khác trong run:** VOD phát tốt, **0 lần decoding failed** (run trước có 4 lần) — đây là cải thiện thật. Judge lần này không bỏ sót thêm lỗi phát nào (khác run trước).

---

## F. Các lỗi khác nhìn thấy bằng mắt (ngoài finding)

### F.1 Lỗi mới trong run này
1. **(MỚI) Nút `▶ PHÁT` ở giữa đè lên dialog lỗi Sport, che nội dung dialog** — steps 29, 32; video f_003 (720p thấy rõ nhất). Tiêu đề `Lỗi Phát Luồng Video` bị che đoạn giữa, dòng `Mạng lỗi — … vào lại sau` bị che một phần. Dialog vẫn dùng được (`THỬ LẠI` có focus trắng) nhưng người dùng không đọc được hết thông báo lỗi. Chỉ xảy ra ở Sport player (VOD không có nút giữa nổi nên dialog VOD run trước không bị).
2. **(MỚI) Hàng dưới Sport OSD quá chật: chữ `● TRỰC TIẾP` bị nút `TÙY CHỌN` lấn/che mép phải** — steps 26–32, crop phóng to xác nhận. Nút `TỈ LỆ` cũng sát mép phải màn hình. Hệ quả của việc nhồi 7 thành phần (KÊNH TIẾNG, 00:00, seek bar, Về trực tiếp, TRỰC TIẾP, TÙY CHỌN, TỈ LỆ) vào một hàng — cũng là lý do vạch đỏ chỉ dài ~211px (mục D, item 5).
3. **(MỚI, nhỏ) Toast `Mạng chập chờn: Đang tự kết nối lại luồng…` che giữa thanh bar dưới** — ảnh mission 06 (che một phần nút `Về trực tiếp`). Thoáng qua, tự mất, nhưng nó đè lên đúng vùng điều khiển.
4. **(MỚI) Phím MENU trong Sport player không có tác dụng gì nhìn thấy được** — steps 28, 31 (bấm MENU, ảnh không đổi, không mở Server Picker/menu nào). Không rõ là gate cố ý hay phím chết (AI ở step 31 còn định dùng MENU để mở Server Picker — không mở được).

### F.2 Lỗi cũ từ run trước — đối chiếu
| Lỗi run trước | Trạng thái run này |
|---|---|
| Rail không mở | ❌ **VẪN CÒN — lần thứ 3 liên tiếp.** Steps 48–54: DPAD_LEFT ×7 chỉ di chuyển focus trong lưới card, không có rail nào. AI tự ghi trong thought: "DPAD_LEFT không mở được Sidebar Rail" (step 4) và "SWITCH_TAB(6) đã thất bại 2 lần" (mission Home Hub). **Check 8 "Sidebar Rail" vẫn PASS, không finding nào** — judge bỏ sót dù chính AI đã ghi nhận lỗi. |
| Chi tiết phim: back che chữ `C` của tiêu đề | ❌ **VẪN CÒN** — mọi ảnh chi tiết phim (16, 17, 102, 103, 116; video f_012: khi back được focus thì tiêu đề đọc thành `uộc Chiến Ẩm Thực`) |
| Chữ mờ `…ĐẶC SẮC` bị cắt sau thanh nav ở chi tiết phim | ❌ **VẪN CÒN** — mọi ảnh chi tiết phim |
| Nav ghost (D8): chữ hero xuyên qua nav | ❌ **VẪN CÒN, thấy rõ hơn ở 720p** — `[OK] XEM NGAY` / `[MENU] CHỌN PHÒNG` xuyên qua nav ở steps 005, 044, 090, 098; video f_002/f_004/f_007/f_008. Chấm đỏ sau `TRANG CHỦ` vẫn còn (mọi ảnh Home). |
| Decoding errors ×4 lần (VOD) | ✅ **ĐÃ HẾT trong run này** — 0 lần (VOD chỉ phát 2 phút rồi tạm dừng, nên mẫu nhỏ — nhưng không có lần nào) |
| VOD nhãn phải = thời gian còn lại | 🔍 **ĐÃ XÁC NHẬN LÀ THIẾT KẾ** (xem D, item 3) — không còn tính là lỗi |
| Phòng `0 lượt xem` vs card `121,9K` | ⚪ **KHÔNG TÁI HIỆN** — phòng Khaan có lượt xem thật (62,8K, steps 015–017); phòng Fujian 0 lượt xem nhưng trận chưa đá nên 0 là hợp lý. Không có mẫu tương đương run trước để đối chiếu. |
| Schedule hàng đầu bị cắt | ⚪ **KHÔNG KIỂM ĐƯỢC** — tab Lịch 0 thao tác, không vào Schedule lần nào (run trước đã hết, run này không xác nhận lại được) |
| IPTV chữ đè lên logo ANTV | ⚪ **KHÔNG KIỂM ĐƯỢC** — tab IPTV 0 thao tác, player IPTV không mở lần nào |
| Pill tỉ số lag so với bug đài | ⚪ **KHÔNG KIỂM ĐƯỢC** — Sport không phát được video nên không có bug đài để đối chiếu |
| Thoát player cần 2 lần BACK | ❌ **VẪN CÒN** — VOD: BACK lần 1 (step_114) OSD vẫn mở, BACK lần 2 (step_115) mới tắt OSD |
| Dialog chọn tập: pill tập đè lên mô tả | ⚪ **KHÔNG KIỂM ĐƯỢC** — AI không mở dialog chọn tập lần nào trong run này |
| Nút `Về trực tiếp` lúc có lúc không (Sport) | ✅ **ĐÃ HẾT** — hiện ở cả 7 ảnh Sport (steps 26–32), nhất quán |

### F.3 Vấn đề khác thấy bằng mắt
5. **AI "đi lạc" ~2000s trên Home:** từ step 33 (t=833s) tới step 100 (t=2002s), AI chỉ di chuyển focus trong lưới Home — 10/16 mission mang tên Schedule/IPTV/Phim/Settings nhưng không rời Home. Đây là vấn đề của **phiên kiểm thử**, không phải lỗi app — nhưng nó làm cho hầu hết check "PASS" trở nên rỗng (xem mục G).
6. **Không có lần seek/tua nào thật sự xảy ra ở VOD:** mission 14 tên "VOD seek & resume" nhưng vị trí phim chỉ tăng 01:49 → 02:01 rồi đứng yên ~9 phút (AI tạm dừng rồi chỉ di chuyển focus). Resume thì có (`TIẾP TỤC XEM — 1 phim` ở steps 102/116), seek thì **không được kiểm**.
7. **Lượt xem theo feed khó tin:** Atletico vs Barcelona chỉ `1,0K` trong khi Khaan (VĐQG Mông Cổ) `255,5K` (ảnh 05, 07; steps 044, 090). Dữ liệu feed — ghi nhận, không trừ điểm app.
8. **Focus ở nav `LỊCH TRÌNH`/`TRUYỀN HÌNH` trong khi đang ở màn hình chi tiết phim** (ảnh 16, 17; steps 121–129) — focus di chuyển được nhưng vị trí ban đầu khó hiểu; AI chỉ lướt nav chứ không mở tab nào.

---

## G. Điểm 98/100 — có công bằng không?

**Không công bằng — 98/100 quá cao so với những gì thực sự được kiểm chứng trên màn hình.** Phân tích:

- **Phiên này kiểm được ít hơn run trước, không phải nhiều hơn:** Sport player không phát được 1 khung hình nào (7/7 step màn hình đen); không vào trận live nào; WebPlayer lần thứ 3 không tới; 5/7 tab 0 thao tác; 10/16 mission không rời Home; không seek, không mở episode picker, không gõ tìm kiếm, không vào Cài đặt, không mở player IPTV. Điểm 98 dựa trên một phiên mà AI dành ~2/3 thời gian đi lạc trên Home.
- **Judge bỏ sót lỗi thật — lần này còn có bằng chứng là chính AI đã ghi nhận:** rail không mở (AI viết rõ "DPAD_LEFT không mở được Sidebar Rail", "SWITCH_TAB(6) đã thất bại 2 lần") nhưng check 8 vẫn PASS, không finding. AI viết "Video đã bắt đầu phát thành công" ở step 31 trong khi ảnh là màn hình đen — judge không phát hiện mâu thuẫn.
- **Nhiều check "pass" trên danh nghĩa tên mission chứ không phải nội dung thực:** check 13 "WebPlayer" pass trong khi activity chỉ có MainActivity + PlayerActivity; check 15 "Settings Dialog" pass trong khi không có settings dialog nào; check 10 "Zapping Player" pass trong khi player IPTV chưa bao giờ mở; check 16 "Tìm kiếm & Cài đặt" pass trong khi Cài đặt chưa bao giờ vào; check 7 "Schedule EPG" pass trong khi Schedule 0 thao tác.
- **Nhưng 98 không phải hoàn toàn vô căn cứ:** Fix 1 giữ vững (không tỉ số ảo); Fix 2 giữ vững (OSD gọn, focus rõ); Speed lần đầu tới được + focus được; vạch đỏ Sport lần đầu hiện; 0 decoding error (run trước 4 lần); Home/hero/room picker/chi tiết phim/resume đều sạch; không crash sau chaos.

**Ước tính sau khi khử artifact (de-artifacted): ~70/100 (khoảng 68–72)** — tương đương run trước (~70), nhưng thành phần khác nhau. Cách tính (xuất phát 100):
- Rail không mở, lần thứ 3, judge tự ghi nhận rồi vẫn PASS: −6
- Sport player không phát được 1 khung hình nào + báo lỗi sai bản chất (trận chưa đá → "mạng lỗi") + nút PHÁT che dialog: −6
- WebPlayer lần thứ 3 không tới, check 13 PASS giả: −5
- Bao phủ: 5/7 tab 0 thao tác, 10/16 mission không rời Home, không seek thật, không episode picker/search/settings: −5
- Fix 5 item 1 (phụ đề) + nửa "TẠM DỪNG" của item 2 + phút pill (item 4) **không kiểm được trên màn hình**: −3 (trừ vào độ tin cậy của điểm, không khẳng định fix sai)
- Lỗi cũ lặp lại: back che `C` + chữ mờ sau nav + nav ghost: −3
- Hàng dưới Sport quá chật (TRỰC TIẾP bị che) + MENU chết trong Sport player: −2
- Thoát player 2 lần BACK: −0 (ghi nhận, không trừ thêm — đã tính trong bao phủ)
- Tổng: −30 → **~70/100**. Khoảng 68–72 tùy trọng số cho Sport đen màn hình (một phần do AI chọn trận chưa đá — nếu tính đó là lỗi chọn mẫu của AI thì điểm app cao hơn ~2–3 điểm, khoảng 72–73).

---

## H. Trả lời trực tiếp các câu hỏi về bao phủ

| Câu hỏi | Trả lời | Bằng chứng |
|---|---|---|
| **WebPlayerActivity đã tới chưa?** | ❌ **KHÔNG — 0 step.** | Activity trong cả 129 step chỉ có `MainActivity` (110) và `PlayerActivity` (19). Không có `WebPlayerActivity` lần nào. Check 13 "Trình Phát Web (WebPlayerActivity)" PASS trên mission VOD_PLAYER_SEEK_AND_RESUME mà 10 step của nó (86–95) toàn là MainActivity ở Home. **Lần thứ 3 liên tiếp WebPlayer không được mở.** Từ "WebPlayer" xuất hiện 11 lần trong `qa_report.json` — toàn là tên mission/check, không phải activity thật. |
| **Sport player đã tới chưa? (steps nào?)** | ⚠️ **CÓ — nhưng chỉ 7 step, và không phát được gì.** Steps **26–32** (PlayerActivity), trận Fujian Nanan Women vs Hebei Snow Ruyi Women, phòng `5 LỬA`. Cả 7 ảnh đều màn hình đen: tải → lỗi → retry → lỗi. **Không có trận live nào được vào player** (Khaan đang live nhưng AI chỉ mở room picker steps 14–19 rồi BACK ra). Không có session Sport nào khác. | steps 26–32; ảnh 06; video f_003 |
| **VOD player đã tới chưa? (steps nào?)** | ✅ **CÓ — 12 step, native only.** Steps **104–115** (PlayerActivity), phim `Cuộc Chiến Ẩm Thực - Tập 01`. Phát được 00:00 → 02:01 rồi tạm dừng; OSD mở ở steps 104–114; thoát bằng 2 lần BACK (114–115). **Không có phụ đề trong bất kỳ shot nào; không có trạng thái `TẠM DỪNG` nào; không có lần seek nào.** | steps 104–115; ảnh 15; video f_009/f_010/f_011 |
| **Fix 5 items nào KHÔNG thể kiểm trên màn hình?** | **Item 1 (phụ đề): hoàn toàn không kiểm được** — 0 phụ đề trong mọi ảnh OSD + mọi frame video. **Item 4 (phút pill khi vào phòng live): không kiểm được** — không vào trận live nào. **Item 2 (nửa "TẠM DỪNG" đầy đủ khi phát): không kiểm được** — không có OSD nào ở trạng thái đang phát. **Item 6 (chiều hiện ±30s trên stream seek được): không kiểm được** — không có stream seek được nào. Chỉ **item 3 (remaining time), item 5 (vạch đỏ), item 6 (chiều ẩn) và nửa "Speed" của item 2** là có bằng chứng trực tiếp. | Xem mục D |

---

## Kết luận ngắn

- **Xác nhận được trên màn hình:** vạch đỏ Sport (item 5) ✅; nút Speed hiện đầy đủ + focus được lần đầu tiên (item 2 một nửa) ✅; pill `FUJ - HEB` không trùng mã ✅; ±30s ẩn đúng gate ✅; nhãn phải VOD vẫn là thời gian còn lại (by design) ✅; không tỉ số ảo ✅; 0 decoding error (run trước 4 lần) ✅.
- **Không kiểm được (do AI không tạo ra được màn hình cần thiết — KHÔNG được ghi là "đã sửa"):** phụ đề vs seek bar (item 1) ❓; `TẠM DỪNG` đầy đủ khi phát ❓; phút pill khi vào phòng live (item 4) ❓; WebPlayer (lần 3) ❓.
- **Lỗi mới đáng chú ý nhất:** nút `PHÁT` ở giữa đè lên dialog lỗi Sport, che nội dung dialog (steps 29/32); hàng dưới Sport quá chật làm chữ `TRỰC TIẾP` bị nút `TÙY CHỌN` lấn; Sport player không phát được 1 khung hình nào vì AI mở trận chưa đá mà app báo thành "mạng lỗi".
- **Lỗi cũ dai dẳng nhất:** rail không mở — lần thứ 3 liên tiếp, và lần này chính AI đã ghi nhận trong thought nhưng judge vẫn cho PASS.
- **Điểm thật: ~70/100 (68–72), không phải 98/100.** Run này tiến bộ ở VOD (Speed, vạch đỏ, hết decoding error) nhưng thụt lùi ở bao phủ kiểm thử (Sport đen màn hình, không trận live, WebPlayer lần 3 vắng mặt).

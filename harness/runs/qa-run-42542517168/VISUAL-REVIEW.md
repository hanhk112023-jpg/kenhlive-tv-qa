# Đánh giá trực quan QA — CI run 42542517168 (QA QUICK, score-player fix wave)

- **Run:** 42542517168 · **Branch:** `redesign/netflix` · **Commit:** `36f9a7d` (trên nền `f60214b`, gồm 3 fix: `7a55f9b` + `ed27eae` + `36f9a7d`)
- **Phiên:** `QA-SESS-20261109-005615-5a8fc2` · **Thời lượng:** 3823 s · **Điểm judge (OPENAI/nemotron):** 64/100
- **Checks:** 16/16 · **Missions:** 16/16 · **Steps:** 127 (cả 127 đều do OPENAI chấm) · **Findings của judge:** 12 (4 MEDIUM + 8 LOW)
- **Video:** `full_qa_tour.mp4` 14,9 MB, 456,2 s, 1280×720 · `qa_timelapse.mp4` 47,4 s · `concat.txt` liệt kê 21 chunk
- **Phương pháp:** đọc trực tiếp bằng mắt từng ảnh, đối chiếu với `qa_session.json` (timeline, focus, motion) và `qa_report.json` (findings). Không tin điểm số hay kết luận của judge khi chưa có bằng chứng hình ảnh.
- **Độ phủ xem trực tiếp:** **90 hình** — 17 ảnh mission + 1 ảnh BEFORE (run 42520284499 shot 06) + 1 ảnh mẫu VOD + **61 ảnh step** + **9 frame video**. 65 ảnh step còn lại chưa xem trực tiếp từng ảnh — được mô tả theo timeline trong mục C (ghi rõ là chưa eyeball).
- **Lưu ý quan trọng về cách đặt tên ảnh:** ảnh mission `NN_mission_*.jpg` là ảnh **cuối mission** (sau khi AI đã BACK/chuyển tab), nên tên mission thường **không khớp** nội dung ảnh (vd: ảnh 06 mission player thực ra là màn hình Tìm kiếm; ảnh 14 mission VOD thực ra là màn hình chi tiết phim). Bằng chứng player thật nằm ở các **ảnh step**, không phải ảnh mission.

---

## A. Ảnh mission (01–17) + ảnh đối chiếu

### 01_cold_start.jpg — Dialog Telegram lúc khởi động lạnh
Màn hình chính bị che bởi dialog `THÔNG BÁO — NHÓM THẢO LUẬN & HỖ TRỢ TRỰC TUYẾN`, QR + `Nhóm Telegram: @kenhlivetv`, 2 nút `ĐÃ HIỂU / ĐÓNG` (đỏ, focus) và `VÀO NHÓM TELEGRAM`. Dialog sạch, không cắt chữ, focus rõ. Phía sau mờ là Home với các card `VS`. Không lỗi. (Focus theo timeline: `btnCloseFeedback`, có focus ring trắng.)

### 02_mission_cold_start.jpg — Home sau khi đóng dialog (TRÙNG step_005)
Ảnh này **giống hệt step_005** (cùng sha256). Home: 3 card live đầu `Queret… VS Puebla`, `Deport… VS Millona…`, `Detroit… VS Los…` — live nhưng **không hiện tỉ số, chỉ VS**; lượt xem `303,3K / 145,7K / 127,0K` (không có `6844,4K`, không có pill `0` xám). Hàng `TRẬN CẦU SẮP DIỄN RA`: `Pirata… 08:00 Cancu…`, `Milwa… 08:00 Bosto…`, `Alianza 08:15 Lla…`. Hàng `PHIM ĐANG THỊNH HÀNH` ở cuối bị cắt nửa dưới (cuộn dọc — bình thường). Palette KL6.5 đúng (#141414, đỏ #E50914). Không thấy tỉ số ảo.

### 03_mission_sports_multi_source.jpg — Hero + rail Socolive
Hero: `Queretaro FC 3 : 5 Puebla` (đỏ, rõ) — tỉ số bóng đá hợp lý (mỗi bên ≤ 9, tổng 8). `Trực tiếp · MEX D1 · BLV COCA · Tín hiệu HD`, `302,9K` xem, ngày `Thứ Hai, 09/11/2026 07:57`. Rail `Socolive TV`: card focus `CS Her… VS Inter d…` (VS, không tỉ số), `Univers… VS Moque…` (VS), `66,6K / 53,1K / 25,6K xem`. **Không có tỉ số ảo.** Việc card live hiện `VS` thay vì tỉ số chính là Fix 1 đang hoạt động (xem thêm step_006–012).

### 04_mission_sports_room_picker.jpg — Lịch thi đấu (Schedule)
Danh sách lịch: `06:10 Deportes Tolima vs Millonarios`, `07:00 Queretaro FC vs Puebla`, `07:30 CS Herediano vs Inter de San Carlos`, `08:00 Piratas FC vs Cancun FC` — **không hiện tỉ số** (chỉ giờ + pill `Live`/`Có phòng`). **Lỗi thấy rõ: hàng đầu tiên (Detroit Pistons vs Los Angeles Lakers) bị cắt nửa trên, chìm dưới thanh nav trên cùng** — chữ chỉ còn nửa dưới, focus ring trắng ôm một card bị che. Lỗi này lặp lại ở mọi ảnh Schedule (08, 09, 19–22, 52). Một vài avatar BLV là vòng tròn xám trống (đang load — ở ảnh 09 sau đó đã load đủ).

### 05_mission_sports_data_accuracy.jpg — IPTV ANTV HD (KHÔNG phải màn hình tỉ số)
Ảnh cuối mission 5 thực ra là tab **Truyền hình**: hero `ANTV HD — Đang phát: [08:00 - 08:45] Thời sự VTV Tiếp sóng`, nút `XEM TOÀN MÀN HÌNH` (focus đỏ), `+ YÊU THÍCH`, `NGUỒN M3U`; lưới kênh `VTV6`, `360 Bundesli…`, `360 C1 Châu …`… Không có tỉ số trong ảnh này. Tên mission gây hiểu lầm — mission 5 kết thúc ở tab IPTV sau `SWITCH_TAB 2`.

### 06_mission_player_streaming_and_controls.jpg — TÌM KIẾM (không phải player!)
Ảnh cuối mission 6 là màn hình **Tìm kiếm** (tab `TÌM KIẾM` đang chọn): chip `Phim Mới / Hoạt Hình / MEX D1 / COL D1 / Bóng Rổ NBA / MEX D2 / CRC D1`, `22 trận đang live`, `Xu hướng tìm kiếm: One Piece, Conan, Ao no Hako`, kết quả `Queretaro FC vs Puebla — BLV COCA +4 BLV · 302,6K · 5 phòng`, `Deportes Tolima vs Millonarios — 146,0K`. **Không có player trong ảnh này.** Bằng chứng Sport OSD thật nằm ở **step_044** (mục B). Đây là điểm mù của cách đặt tên ảnh mission — ai chỉ xem ảnh mission sẽ kết luận sai là "không thấy player".

### 06 BEFORE — run 42520284499, shot 06 (ảnh đối chiếu, trước fix)
Trận CF Estrela Amadora vs Benfica: hàng nút trên cùng **6 nút** (`QUAY LẠI`, `Chọn BLV`, `Đổi luồng`, `KÊNH TIẾNG`, `ĐA MÀN HÌNH`, `PIP`, `TÙY CHỌN` — thực tế 7 ô kể cả QUAY LẠI), tiêu đề trùng lặp 3 lần (`Hiệp 1: 7' · CFE 0 - 0 BEN` + `THỂ THAO · CF Estrela Amadora SAD vs Benfica · 5 LỰA` + `POR D1 · TRỰC TIẾP · 0 - 0 · Hiệp 1: 7`), giữa màn hình `TUA -30S / PHÁT / TUA +30S` **không có focus** (không viền trắng), thanh bar dưới gần như tàng hình trên nền quảng cáo `BUFA`. Đây là baseline để so sánh với step_044.

### 07_mission_home_hub_3_cards_and_canva_logos.jpg — Home (ĐANG PHÁT + SẮP DIỄN RA)
3 card live đầu đều `VS` (`Queret… VS Puebla`, `Deport… VS Millona…`, `Detroit… VS Los…`), lượt xem `303,3K / 145,7K / 127,0K`. Hàng dưới: `Pirata… 08:00 Cancu…` (`Còn 3p`), `Milwa… 08:00 Bosto…`, `Alianza 08:15 Lla…`. **Không tỉ số ảo, không `6844,4K`.** Logo đội hiển thị đủ (không còn logo đỏ hình chữ nhật như run trước). Card đầu bị focus trắng nhưng tên đội bị cắt (`Queret…`) do card tràn — bình thường với rail ngang.

### 08_mission_schedule_epg_and_fixture_tap.jpg — Schedule (TRÙNG step_052)
Giống hệt step_052: hàng đầu Detroit vs Lakers **bị cắt nửa trên dưới nav**, các hàng sau đầy đủ, không tỉ số. Focus ring trắng quanh hàng đầu bị che. (Xem chi tiết ở step_052.)

### 09_mission_sidebar_rail_full_traversal.jpg — Schedule, rail KHÔNG xuất hiện (TRÙNG step_052)
Giống hệt step_052 và ảnh 08. **Không có sidebar rail nào trên màn hình** sau 5 lần DPAD_LEFT (steps 47–52) — đây là bằng chứng hình ảnh cho finding step 52. Xem step_052.

### 10_mission_iptv_categories_and_favorites.jpg — Dialog M3U + bàn phím (TRÙNG step_061/062)
Dialog `DANH SÁCH PHÁT M3U TÙY CHÍNH`, ô `edtM3uUrl` có focus (viền trắng), nút `Xóa link`, phía dưới **2 nút `ĐÓNG` và `LƯU & NẠP KÊNH` bị cắt nửa** ở mép dưới dialog, bàn phím mềm mở che nửa dưới màn hình. Đây là bằng chứng cho finding M3U trap — xem step_061/062/064/065.

### 11_mission_iptv_epg_and_zapping_player.jpg — IPTV đang tải (ANTV HD)
Màn hình đen, hộp `Đang tải luồng…` với icon xoay ở giữa; top bar IPTV `QUAY LẠI / KÊNH / Đổi nguồn / PIP / TÙY CHỌN`, góc phải `ANTV HD — KÊNH 1 · Đang chiếu: Thời sự VTV Tiếp sóng`. Đây là trạng thái chuyển kênh (zapping) — không phải màn hình lỗi đứng yên; step_070 sau đó cho thấy ANTV đã phát được.

### 12_mission_phim_nguonc_and_categories.jpg — Chi tiết phim (TRÙNG step_075)
`Cuộc Chiến Ẩm Thực`, `2026 · Chính Kịch`, mô tả `The Table: K-Chef 2026…`, nút `XEM NGAY` (focus viền trắng), `CHỌN TẬP`, `+ LƯU PHIM`, `PHIM KHÁC`; `DANH MỤC: Tất Cả / Lịch Sử Xem / Tìm Kiếm / Mới Cập Nhật / Phim Bộ / Phim Lẻ / Anime & H…` (pill cuối bị cắt ở mép phải — cuộn ngang, bình thường); `Phim Mới Cập Nhật — 120 phim`. **2 lỗi lặp lại trên mọi ảnh chi tiết phim:** (1) nút back tròn (◀) ở góc trái **che mất chữ `C` đầu tiên của tiêu đề `Cuộc…`**; (2) có dòng chữ mờ `…ĐẶC SẮC` bị cắt dở phía sau thanh nav trên cùng.

### 13_mission_phim_episode_picker_and_favorite.jpg — Chi tiết phim sau khi lưu
Giống khung 12 nhưng nút đã thành `✓ ĐÃ LƯU`, hàng dưới đổi thành `BỘ PHIM ĐÃ LƯU (1) — 1 phim`. Chức năng lưu phim hoạt động. Vẫn còn 2 lỗi như ảnh 12 (back che chữ `C`, chữ mờ sau nav).

### 14_mission_vod_player_seek_and_resume.jpg — Chi tiết phim (KHÔNG phải VOD player)
Ảnh cuối mission 14 là màn hình chi tiết phim, nút `✓ ĐÃ LƯU (TẬP 01 · 03:31/01:12:14)` — tức resume đã lưu được vị trí 03:31. **Không có VOD player trong ảnh này.** VOD player thật nằm ở steps 85–93 (mục B). Lưu ý: tổng thời lượng ở đây là `01:12:14`, nhưng trong player lúc thì `1:11:37`, lúc `1:08:43`, `1:03:48`, `59:20`, `49:27` — tổng thời lượng của cùng một tập **nhảy lung tung theo từng lần phát** (xem mục B).

### 15_mission_player_settings_dialog.jpg — Lỗi decoding lần 3 (TRÙNG step_112)
Giống hệt step_112: dialog `Lỗi Phát Luồng Video — Stream lỗi: ERROR_CODE_DECODING_FAILED`, `22:47 / 49:27`, hàng nút dưới **bị cắt nửa dưới ở mép màn hình**. **Không có settings dialog nào** trong mission 15 — tên mission không đúng với những gì AI đã làm (chỉ phát lại phim và gặp lỗi).

### 16_mission_search_and_settings_feedback.jpg — Chi tiết phim, focus pill Hàn Quốc
Giống khung 14, focus viền trắng ở pill `Hàn Quốc` trong hàng `DANH MỤC`. Vẫn còn lỗi back che chữ `C` và chữ mờ sau nav. Mission 16 tên là Search & Settings nhưng các step 113–121 chủ yếu vẫn ở màn hình chi tiết phim (chỉ lướt pill thể loại).

### 17_mission_dpad_chaos_stress_and_recovery.jpg — Chi tiết phim, focus pill Mới Cập Nhật
Giống khung 16, focus chuyển sang pill `Mới Cập Nhật`. App không crash sau chuỗi DPAD chaos (steps 122–127) — màn hình vẫn bình thường, focus di chuyển được. Đạt mục đích stress test ở mức bề mặt.

---

## B. Ảnh step đã xem trực tiếp (61 ảnh)

### MISSION_COLD_START — steps 1–4
- **step_002** (t=40s): Home sau khi đóng dialog Telegram. 3 card live `VS`, lượt xem `303,3K / 145,7K / 127,0K`; hàng `TRẬN CẦU SẮP DIỄN RA` + `PHIM ĐANG THỊNH HÀNH`. Màn hình đang cuộn xuống nên hero banner không thấy trong khung. Không tỉ số ảo, không `6844,4K`. Palette đúng.

### MISSION_SPORTS_MULTI_SOURCE — steps 5–12
- **step_005** (t=79s): như ảnh 02 (card `VS`, `303,3K / 145,7K / 127,0K`). Card đầu có focus trắng.
- **step_006** (t=93s): Hero `Queretaro FC 3 : 5 Puebla` + card dưới cũng `3 : 5` (hero và card **đồng nhất** — cùng một nguồn tỉ số). Card `Deport… VS Millona…` + pill xám `Hiệp 2: 72'` (hiện phút nhưng ẩn tỉ số — đúng quy tắc plausibility: tỉ số bị ẩn thì hiện `VS`, phút vẫn giữ). Card NBA `Detro… 81 : 88 Los A…` — **bóng rổ hiện tỉ số lớn bình thường, không bị ẩn sai**. Lượt xem `302,9K / 145,9K / 127,2K`. Không tỉ số ảo.
- **step_007** (t=103s): như step_006, focus chuyển sang card Deportes (`VS` + `Hiệp 2: 72'`). `3:5` và `81:88` vẫn đúng.
- **step_008** (t=113s): như step_006/007, focus ở card NBA `81 : 88`. Hero `3:5` không đổi.
- **step_009** (t=124s): rail cuộn tiếp — `Detro… 81 : 88 Los A…`, `Piratas… VS Cancun…`, `Alianza VS Llanero…`. Toàn `VS` hoặc `81:88`. Không tỉ số ảo.
- **step_010** (t=135s): như trên; hero `3:5` ổn định. Lượt xem `119,9K / 66,6K`.
- **step_011** (t=145s): `Alianza VS Llanero…`, `CS Her… VS Inter d…`, `Univers… VS Moque…` — toàn `VS`. Lượt xem `66,6K / 53,1K`.
- **step_012** (t=157s): cuối rail — `CS Her… VS Inter d…`, `Univers… VS Moque… (Trực tiếp (08:30) · 25,6K xem)`. Không tỉ số nào khác ngoài hero `3:5`. **Kết luận rail thể thao: không có tỉ số bóng đá nào vượt quy tắc (mỗi bên ≤ 9, tổng ≤ 12) trong cả 8 step.**

### MISSION_SPORTS_ROOM_PICKER — steps 13–18
- **step_014** (t=180s): Dialog chọn phòng `CS Herediano vs Inter de San Carlos — CRC D1 · 2 phòng live`: `BLV HUCK (Lv.1) — 26,9K lượt xem · LIVE · Điểm: 1,0K` và `ASHAHI (Lv.1) — 26,2K lượt xem · LIVE · Điểm: 1,1K`, pill `SOCO`. Dialog sạch, không cắt, không lỗi. (Focus theo timeline đang ở container dialog, chưa thấy viền focus rõ trên hàng phòng ở ảnh này.)
- **step_015** (t=191s): như step_014, focus đã xuống hàng `ASHAHI` (timeline: focus ring = True). Dialog hoạt động bình thường.

### MISSION_SPORTS_DATA_ACCURACY — steps 19–22
- **step_019** (t=239s): Schedule — hàng đầu Detroit **bị cắt nửa trên dưới nav** (lỗi lặp lại, xem ảnh 04). Các hàng sau không có tỉ số.
- **step_020** (t=249s): như trên, focus ring trắng chuyển xuống hàng `06:10 Deportes Tolima vs Millonarios`. Hàng đầu vẫn bị cắt.
- **step_021** (t=259s): focus xuống hàng `07:00 Queretaro FC vs Puebla`. Hàng đầu vẫn bị cắt.
- **step_022** (t=269s): focus xuống hàng `07:30 CS Herediano vs Inter de San Carlos`. Hàng đầu vẫn bị cắt. **Cả 4 ảnh: lịch không hiện tỉ số trận nào — không có gì để sai, nhưng cũng có nghĩa mission "data accuracy" không kiểm được tỉ số ở màn hình này.**

### MISSION_PLAYER_STREAMING_AND_CONTROLS — steps 23–30 (IPTV, KHÔNG phải Sport!)
- **step_024** (t=320s): PlayerActivity — nhưng là **IPTV ANTV HD**, không phải thể thao. Top bar: `◀ QUAY LẠI` + hàng 4 nút `KÊNH / Đổi nguồn / PIP / TÙY CHỌN`; góc phải `TRUYỀN HÌNH · ANTV HD — KÊNH 1 · Đang chiếu: Thời sự VTV Tiếp sóng`. **Chữ `Đang chiếu: Thời sự VTV Tiếp sóng` đè lên logo đỏ ANTV của stream** (chữ trắng trên nền logo đỏ, khó đọc). Không có nút pause/play ở giữa, không có thanh bar dưới — chỉ có đồng hồ `08:00` góc dưới phải. Focus theo timeline là `playerView` toàn màn hình, không focus ring. Video đang phát (motion 24,82%).
- **step_025** (t=364s): như step_024, khung hình khác (em bé áo vàng). Vẫn 4 nút trên, không bar dưới, chữ đè logo ANTV.
- **step_026** (t=413s): như trên, khung hình 2 y tá. Đồng hồ `08:01`.
- **step_027** (t=455s): như trên, khung hình biên bản làm việc. Đồng hồ `08:02`. Top bar vẫn hiện sau nhiều giây — OSD IPTV không tự ẩn trong các ảnh này (hoặc AI bấm phím giữ OSD hiện).
- **step_028** (t=490s): như trên, khung hình giấy khai sinh. Đồng hồ `08:03`.
- **step_029** (t=522s): OSD đã tự ẩn — chỉ còn video (chân người ngồi ghế) + logo `ANTV HD` + đồng hồ `08:03`. Đây là trạng thái xem thường (không OSD), bình thường.
- **Nhận xét chung steps 24–29:** mission tên "player streaming" nhưng AI mở **IPTV** (bấm `btnHeroWatchFullscreen` ở tab IPTV), không mở trận thể thao nào. OSD IPTV vẫn là dạng cũ (4 nút trên, không có center control, không có bottom bar) — **Fix 2 (Sport OSD) không áp dụng cho IPTV**, đúng phạm vi, nhưng lỗi chữ đè logo ANTV thì vẫn còn đó.

### MISSION_HOME_HUB_3_CARDS_AND_CANVA_LOGOS — steps 31–40 (thực tế: Search + Settings)
- **step_031** (t=548s): = ảnh mission 06 (Tìm kiếm, `22 trận đang live`, `302,6K`). Xem ảnh 06.
- **step_033** (t=600s): Tìm kiếm với từ khóa gõ sai thành `uefaq` (AI gõ `uefa` rồi thêm `q`), `0 kết quả cho "uefaq"`, bàn phím mở với gợi ý `UEFA / UEFA q / UEFA quick`. Empty state hiển thị đúng, không crash. (Timeline: step 31 TEXT `uefa`, step 32 ENTER, step 33 `SWITCH_TAB 4` — chữ `q` thừa nhiều khả năng do AI chạm gợi ý bàn phím.)
- **step_036** (t=635s): Màn hình **Cài đặt** — `Chất lượng hình: Tự động`, `Chế độ âm thanh: Tự động (Hay)`, `Liên hệ & Báo lỗi — Nhóm Telegram: @kenhlivetv` (focus viền trắng), `Xóa bộ nhớ đệm ảnh`, `Phiên bản 0.1.12`. Sạch, đúng palette, không lỗi. (Mission tên "Home Hub" nhưng AI lại đi vào Cài đặt — mission 6 thực tế không hề hiện "hub 3 card" nào.)

### MISSION_SCHEDULE_EPG_AND_FIXTURE_TAP — steps 41–46
- **step_043** (t=728s): Dialog chọn phòng `Detroit Pistons vs Los Angeles Lakers — Bóng Rổ NBA · 4 phòng live`: `BRIAN`, `CHAN SENA`, `BLV HENRY`, `ZERO` — cả 4 đều `0 lượt xem · LIVE`. **Mâu thuẫn dữ liệu: card trận này ngoài Home hiện `127,0K xem`, nhưng cả 4 phòng đều `0 lượt xem`.** Dialog thì sạch, không cắt.
- **step_044** (t=855s) — **ẢNH QUAN TRỌNG NHẤT CỦA RUN NÀY (Sport OSD sau Fix 2):** Trận NBA Detroit vs Lakers đang phát. Top bar **chỉ còn `◀ QUAY LẠI` + pill `DET 92 - 94 LOS`** — không còn hàng 6 nút. Pill là ô bo tròn nền tối, chữ trắng, gọn, ở góc trái trên. Giữa màn hình `TUA -30S / ▶ PHÁT / TUA +30S`, nút **PHÁT có viền trắng rõ ràng — focus nhìn thấy được (D14 đã sửa)**. Scrim trên tối dần, chữ đọc được. Thanh bar dưới **nhìn rõ trên nền kính tối**: `KÊNH TIẾNG | 00:00 | thanh trượt có núm trắng | ● Về trực tiếp | 00:06 | TÙY CHỌN | TỈ LỆ`. **So với BEFORE: khác một trời một vực — hết hàng nút, hết tiêu đề trùng, có focus, bar dưới rõ.** Tuy nhiên có 3 điểm trừ: (1) pill **không có phút/hiệp** (`DET 92 - 94 LOS` — không thấy `4TH 6:26`); (2) **pill lệch với bug tỉ số trong chính stream**: bug của đài hiện `LAL 95 - 94 DET, 4TH 6:26` trong khi pill app hiện `DET 92 - 94 LOS` — DET lệch 2 điểm (92 vs 94), LOS/LAL lệch 1 điểm (94 vs 95); trên cùng một màn hình có 2 tỉ số khác nhau; (3) bar dưới hiện `00:00 / 00:06` cho một trận live — thanh "seekable" với tổng chỉ 6 giây, trong khi theo luật support-gate thì live không seek được phải fallback sang bar đỏ 100% (ở đây lại là bar trắng có núm như VOD).
- **step_045** (t=929s): OSD tự ẩn — toàn cảnh sân bóng rổ, chỉ còn logo `SUTBONGTV` và banner `BUFA` của stream. Video đang phát (motion 23,09%). Bình thường.

### MISSION_SIDEBAR_RAIL_FULL_TRAVERSAL — steps 47–52
- **step_052** (t=1008s): = ảnh mission 08/09. Schedule, focus vẫn ở `schedCard` Detroit đầu tiên. **Không có sidebar rail.** Timeline: steps 47–51 bấm DPAD_LEFT 5 lần, focus không nhúc nhích khỏi `schedCard#[44,0][1876,200]` (có focus ring). Kết luận finding step 52 là **THẬT**. Lưu ý: focus đang ở card full-width, không rõ có phải "mép trái" theo đúng nghĩa spec hay không, nhưng sau 5 lần LEFT mà rail không mở thì hành vi đã sai so với thiết kế. Hàng đầu vẫn bị cắt nửa trên dưới nav (lỗi Schedule lặp lại).

### MISSION_IPTV_CATEGORIES_AND_FAVORITES — steps 53–62
- **step_058** (t=1139s): Dialog M3U vừa mở, bàn phím mềm đã hiện che nửa dưới màn hình; ô URL có focus; nút `Xóa link` đã bị bàn phím che mất một phần. Đây là lúc bắt đầu kẹt.
- **step_061** (t=1175s): Dialog M3U + bàn phím. Ô `edtM3uUrl` có focus (viền trắng, con trỏ ở đầu text). 2 nút `ĐÓNG` và `LƯU & NẠP KÊNH` **chỉ còn nửa trên**, bị cắt ở mép dưới dialog. Timeline: step 61 AI bấm DPAD_RIGHT (không phải DOWN như judge ghi), focus vẫn ở `edtM3uUrl`.
- **step_062** (t=1189s): gần như giống hệt step_061 (chỉ khác vị trí phím gợi ý trên bàn phím). Focus vẫn `edtM3uUrl`. Judge đếm đây là 1 finding riêng — thực chất là cùng 1 trạng thái với step_061.
- **step_064** (t=1210s): sau BACK (step 63) + DPAD_RIGHT, **bàn phím đã tắt** — dialog hiện đầy đủ: `Xóa link`, `ĐÓNG`, `LƯU & NẠP KÊNH` (đỏ) đều nhìn rõ, không cắt. Chứng tỏ **nguyên nhân kẹt là bàn phím mềm đang mở** (che nút + giữ focus ở ô nhập), không phải `nextFocusDown` như judge đoán.
- **step_065** (t=1219s): như step_064, nút `ĐÓNG` có viền trắng (focus đã tới được nút). Timeline: step 65 OK ở `btnM3uClose` — dialog đóng được. **Kết luận: trap là THẬT nhưng có điều kiện (chỉ khi bàn phím mở) và thoát được bằng BACK; judge đếm 3 lần cho 1 nguyên nhân.**

### MISSION_IPTV_EPG_AND_ZAPPING_PLAYER — steps 63–69
- **step_069** (t=1267s): PlayerActivity IPTV `VTV8 HD — KÊNH 16 · Đang chiếu: Phim truyện: Sóng gió nơi thị thành - Tập 20`. Màn hình đen, hộp `Đang tải luồng…` + icon xoay ở giữa. Top bar 4 nút như thường lệ. Motion chỉ 0,54%. Đây là khoảnh khắc finding LOW step 69 — **đúng là có lúc đen + loading**, nhưng xem step_070 sẽ rõ nó chỉ là thoáng qua.
- **step_070** (t=1315s): đã tự failover sang **ANTV HD đang phát** (người đàn ông mặc quân phục, đồng hồ `08:16`, motion 3,58%). Top bar vẫn 4 nút, chữ vẫn đè logo ANTV. **Kết luận: step 69 là trạng thái chuyển kênh thoáng qua, tự hồi phục sau ~48s — không phải "video không phát được" như một lỗi đứng yên.**
- **step_071** (t=1368s): ANTV HD đang phát tiếp (motion 1,31%), OSD đã ẩn. Bình thường.

### MISSION_PHIM_NGUONC_AND_CATEGORIES — steps 70–74
- **step_073** (t=1406s): Chi tiết phim `Cuộc Chiến Ẩm Thực`, focus viền trắng ở nav `TRANG CHỦ` trên top bar trong khi tab đang chọn là `KHO PHIM` (gạch đỏ dưới KHO PHIM) — focus đang ở nav trái, không phải lỗi nghiêm trọng nhưng nhìn hơi lạ. Vẫn còn lỗi back che chữ `C` và chữ mờ sau nav.
- **step_075** (t=1434s): = ảnh mission 12. `XEM NGAY` có focus viền trắng. Xem ảnh 12.

### MISSION_PHIM_EPISODE_PICKER_AND_FAVORITE — steps 75–83
- **step_083** (t=1529s): Chi tiết phim sau khi lưu — nút `✓ ĐÃ LƯU`, hàng `BỘ PHIM ĐÃ LƯU (1)`. Back che chữ `C`, chữ mờ sau nav vẫn còn. (Các step 76–82 là dialog chọn tập — chưa xem trực tiếp, xem mục C.)

### MISSION_VOD_PLAYER_SEEK_AND_RESUME — steps 84–93 (NATIVE player, KHÔNG phải WebPlayer)
- **step_085** (t=1610s): **VOD player đã vào được (PlayerActivity, native)** — `Cuộc Chiến Ẩm Thực - Tập 01`. Nhưng video lỗi: dialog `Lỗi Phát Luồng Video — Stream lỗi: ERROR_CODE_DECODING_FAILED`, nút `THỬ LẠI` (có viền trắng = focus), `QUAY LẠI`, `BÁO LỖI`, dòng `Báo lỗi kênh qua nhóm Telegram: @kenhlivetv`. Phía sau là khung hình phim bị đứng. OSD VOD nhìn được: trên `◀ QUAY LẠI` + tiêu đề **căn giữa, chỉ 1 dòng, không trùng**; trái có **thanh trượt dọc (độ sáng) + icon bánh răng** — giống mẫu VOD; dưới `00:36 | thanh seek núm đỏ | 1:11:37`; hàng nút dưới `PHÁT / TUA -10S / TUA +10S / TẬP TRƯỚC / TẬP TIẾP / CHỌN TẬP / ÂM THANH & PHỤ ĐỀ / TỐ…` — **nút cuối bị cắt ở mép phải, chỉ còn `TỐ`** (nhiều khả năng là `TỐC ĐỘ`). **Không có nút PIP** — tốt. **Không có cụm pause/play ±10s ở giữa màn hình** (khác mẫu: mẫu có nút pause lớn giữa + 2 vòng ±10) — giữa màn hình đang bị dialog lỗi che nên chưa kết luận được ở ảnh này, nhưng ở step_092 (không dialog) cũng không có cụm giữa — xem dưới.
- **step_086** (t=1676s): gần như giống hệt step_085 (cùng dialog, cùng khung hình đứng, `00:36 / 1:11:37`), chỉ khác: viền trắng ở `THỬ LẠI` đã mất (focus theo timeline = NONE). Đây là **cùng 1 sự kiện lỗi**, judge đếm thành finding riêng — trùng lặp.
- **step_087** (t=1732s): giống hệt step_086 (chỉ khác núm seek hơi đỏ hơn). Cùng 1 sự kiện, đếm lần 3.
- **step_088** (t=1788s): giống hệt step_087. Cùng 1 sự kiện, đếm lần 4 (judge không liệt kê step_088 trong summary nhưng nó cũng là dialog lỗi — judge liệt kê 86, 87, 88 trong findings JSON; xem mục E).
- **step_089** (t=1871s): video **đã phát lại được** (cảnh tay áo trắng trên sàn gỗ tối, không OSD, motion 8,78%). Tức sau khi bấm THỬ LẠI (step 88 OK), video chạy lại — lỗi decoding không phải lỗi chết.
- **step_090** (t=1916s): video đang phát (cảnh sân vườn ban đêm, motion 5,81%). Không OSD.
- **step_091** (t=1967s): video đang phát (cận mặt người nằm trên cỏ, motion 2,89%). Không OSD.
- **step_092** (t=2029s): OSD VOD hiện lại, **không còn dialog lỗi**: trên `QUAY LẠI` + tiêu đề căn giữa 1 dòng; thanh trượt dọc trái; dưới `03:31 | seek núm đỏ | 1:08:43`; hàng nút `PHÁT` (**có viền trắng = focus thấy rõ**) `TUA -10S / TUA +10S / TẬP TRƯỚC / TẬP TIẾP / CHỌN TẬP / ÂM THANH & PHỤ ĐỀ / TỐ…` (lại cắt ở `TỐ`). **Giữa màn hình trống — không có cụm pause ±10s như mẫu VOD.** Lưu ý: tổng thời lượng đã đổi từ `1:11:37` (step 85) thành `1:08:43` (step 92) cho cùng một tập — đổi server sau khi retry. Không thấy `SKIP INTRO`, không thấy nút `Lock`, không thấy `Next Ep` riêng (chỉ có `TẬP TIẾP`).
- **step_093** (t=2055s): video đang phát, phụ đề tiếng Việt `Chưa đến lúc đâu.` hiển thị đẹp ở cuối màn hình. Phụ đề hoạt động. Không OSD.
- **step_094** (t=2073s): về lại chi tiết phim, `✓ ĐÃ LƯU (TẬP 01 · 03:31/01:12:14)` — resume đã ghi nhận 03:31. Nhưng tổng `01:12:14` này lại khác với `1:11:37` và `1:08:43` trong player — **3 con số tổng khác nhau cho cùng 1 tập**.

### MISSION_PLAYER_SETTINGS_DIALOG — steps 94–111 (KHÔNG có settings dialog nào)
- **step_096** (t=2197s): lỗi decoding **lần 2**: dialog `ERROR_CODE_DECODING_FAILED` ở `03:51 / 1:08:23`, nút `THỬ LẠI` có viền trắng. Hàng nút dưới lúc này **hiện đầy đủ** (không bị cắt dọc), chỉ cắt phải ở `TỐ`.
- **step_097** (t=2256s): giống step_096 (cùng dialog, `03:51 / 1:08:23`), viền trắng ở `THỬ LẠI` đã mất. Cùng sự kiện lần 2, judge đếm riêng.
- **step_098** (t=2320s): giống step_096/097, `04:13 / 1:08:00` — vị trí đã chạy thêm 22 giây trong lúc dialog lỗi vẫn hiện (tổng lại giảm tiếp). `THỬ LẠI` có viền trắng. Hàng nút dưới vẫn đầy đủ.
- **step_099** (t=2377s): giống step_098, `04:13 / 1:08:00`, không viền trắng. Cùng sự kiện lần 2.
- **step_100** (t=2410s): video **phát lại được** (cảnh rừng tối, motion blur, motion 3,47%). Không OSD.
- **step_102** (t=2647s): lỗi decoding **lần 3**: dialog ở `08:26 / 1:03:48`, `THỬ LẠI` có viền trắng. **Hàng nút dưới bây giờ bị cắt nửa dưới ở mép màn hình** (chữ `TẠM DỪNG TUA -10S…` nằm sát mép dưới, nửa dưới của nút bị mất) — khác với step_096/098 (đầy đủ). Tổng thời lượng lại đổi: `1:03:48`.
- **step_107** (t=3159s): OSD VOD khi đang phát (`TẠM DỪNG` — video đang chạy), `16:48 / 55:26`. **2 lỗi:** (1) hàng nút dưới **bị cắt nửa dưới** như step_102; (2) **phụ đề `ai không chịu nghe thì bị` đè lên đúng vị trí thanh seek bar** — chữ phụ đề nằm ngay trên vạch seek, va chạm với OSD. Bấm MENU ở step này không mở dialog nào (không thấy settings dialog).
- **step_108** (t=3256s): video đang phát (tin nhắn tiếng Hàn trong phim — nội dung của phim, không phải UI), `18:20 / 53:53`. Hàng nút dưới vẫn bị cắt nửa dưới, nút đầu `TẠM DỪNG`. Tổng thời lượng lại đổi (`53:53`).
- **step_110** (t=3457s): video đang phát (người phụ nữ áo vest), `21:44 / 50:30`. Hàng nút dưới vẫn bị cắt nửa dưới.
- **step_111** (t=3535s): lỗi decoding **lần 4**: dialog ở `22:47 / 49:27`, `THỬ LẠI` có viền trắng, hàng nút dưới bị cắt nửa dưới. **Không có settings dialog nào trong cả mission 15** (steps 94–111) — AI chỉ phát lại phim, bấm MENU/OK lung tung rồi gặp lỗi.
- **Quy luật rút ra từ steps 85–112:** hàng nút dưới **đầy đủ khi video tạm dừng** (nút đầu là `PHÁT`: steps 85, 92, 96, 98) và **bị cắt nửa dưới khi video đang phát** (nút đầu là `TẠM DỪNG`: steps 102, 107, 108, 110, 111, 112). Đây là lỗi layout phụ thuộc trạng thái phát/dừng, không phải lỗi chụp ảnh.

### MISSION_SEARCH_AND_SETTINGS_FEEDBACK — steps 112–121
- **step_112** (t=3600s): = ảnh mission 15. Lỗi decoding lần 4 ở `22:47 / 49:27`, hàng nút dưới bị cắt nửa dưới + cắt phải ở `T`. (Judge liệt kê step_112 là 1 trong 7 finding decoding — nhưng step_102 và step_111 cũng là dialog lỗi mà judge không liệt kê; ngược lại step_098 cũng là dialog lỗi mà judge bỏ qua. Việc đếm của judge không nhất quán.)
- **step_113** (t=3613s): về lại chi tiết phim, `XEM NGAY` focus, `✓ ĐÃ LƯU (TẬP 01 · 03:31/01:12:14)`. Back che chữ `C`, chữ mờ sau nav vẫn còn.

### MISSION_DPAD_CHAOS_STRESS_AND_RECOVERY — steps 122–127
- (Chưa xem trực tiếp các step 122–127; ảnh mission 17 cho thấy màn hình cuối vẫn là chi tiết phim, focus ở pill `Mới Cập Nhật`, app không crash — xem mục C.)

---

## C. Ảnh step chưa xem trực tiếp từng ảnh (65 ảnh — mô tả theo timeline)

Các ảnh dưới đây **không được mở xem bằng mắt**; nội dung suy ra từ `qa_session.json` (activity, focus node, motion, thời gian). Ghi rõ để không giả vờ đã xem.

- **step_001** (t=18s): MainActivity, dialog Telegram, focus `btnCloseFeedback` (có focus ring trắng). = trạng thái ảnh 01.
- **step_003** (t=56s): MainActivity, focus `cardRoot` Piratas FC vs Cancun FC 08:00 (không ring). Home đang cuộn.
- **step_004** (t=69s): focus `cardRoot` Queretaro FC vs Puebla, TRỰC TIẾP. Kết thúc mission cold start.
- **step_013** (t=168s): OK trên card CS Herediano — mở dialog chọn phòng (dẫn tới step_014).
- **step_016–018** (t=200–221s): đóng/mở lại dialog chọn phòng rồi `SWITCH_TAB 1` sang Lịch. Không có player.
- **step_023** (t=285s): OK trên `btnHeroWatchFullscreen` ở tab IPTV — mở player IPTV (dẫn tới step_024). **Đây là lý do mission "player" mở IPTV chứ không mở thể thao.**
- **step_030** (t=536s): `SWITCH_TAB 3` (Tìm kiếm) sau khi BACK khỏi player — giải thích vì sao ảnh mission 06 là màn hình Tìm kiếm.
- **step_032** (t=589s): ENTER sau khi gõ `uefa` ở ô tìm kiếm.
- **step_034–035** (t=614–624s): DPAD_DOWN trong màn hình Cài đặt (focus các `view` full-width, có ring).
- **step_037–038** (t=650–662s): DPAD_DOWN tiếp + `SWITCH_TAB 6` (Home Hub).
- **step_039–040** (t=679–693s): DPAD_DOWN: focus `heroPlay` rồi `cardRoot` Queretaro. Kết thúc mission 6.
- **step_041–042** (t=703–713s): `SWITCH_TAB 1` + OK trên `schedCard` Detroit Pistons vs Lakers — mở dialog chọn phòng NBA (dẫn tới step_043/044).
- **step_046** (t=944s): COMPLETE mission Schedule, focus `schedCard` Detroit.
- **step_047–051** (t=951–996s): 5 lần DPAD_LEFT liên tiếp, focus **đứng yên** ở `schedCard` Detroit (có ring) — tiền đề của finding step 52.
- **step_053** (t=1015s): `SWITCH_TAB 2` (IPTV).
- **step_054** (t=1027s): LONG_PRESS OK trên `cardIptvRoot` (yêu thích kênh).
- **step_055–057** (t=1038–1127s): DPAD_RIGHT qua `btnHeroWatchFullscreen` → `btnHeroFavorite` → OK trên `btnIptvAddM3u` (mở dialog M3U).
- **step_059–060** (t=1150–1164s): DPAD_DOWN ×2 ở `edtM3uUrl` (focus không đổi) — **2 lần DOWN đầu tiên của trap M3U** (cùng với step_058).
- **step_063** (t=1198s): BACK trong dialog M3U (focus vẫn `edtM3uUrl`) — nhiều khả năng chính phím này đã tắt bàn phím, mở đường cho step_064/065 thoát trap.
- **step_066–068** (t=1230–1254s): DPAD_LEFT ×2 rồi OK trên `btnHeroWatchFullscreen` — mở lại player IPTV (dẫn tới step_069).
- **step_072** (t=1384s): `SWITCH_TAB 5` (Kho Phim).
- **step_074** (t=1416s): DPAD_DOWN, focus `btnHeroBackHome` (nút back tròn ở chi tiết phim — khớp với lỗi back che chữ `C`).
- **step_076–082** (t=1448–1513s): dialog chọn tập: focus qua `btnHeroEpisodes` → `dialogBtnClose` → `btnFilmPlay` → `dialogBtnFavorite` (`ĐÃ LƯU`) → đóng dialog. Chức năng chọn tập/lưu phim chạy được (không xem ảnh nên không xác nhận được dialog chọn tập có bị cắt hay không).
- **step_084** (t=1541s): OK trên `btnHeroPlay` — mở VOD player (dẫn tới step_085).
- **step_095** (t=2083s): OK trên `btnHeroPlay` — mở lại VOD player lần 2 (dẫn tới step_096, mission 15).
- **step_101** (t=2507s): DPAD_LEFT trong player, motion 1,87% (video đang phát sau lỗi lần 2).
- **step_103–106** (t=2771–3064s): DPAD_DOWN / DPAD_LEFT / OK trong player, motion 9–17% (video đang phát, không OSD trong các ảnh này theo timeline — focus NONE).
- **step_109** (t=3355s): DPAD_DOWN trong player, motion 5,11%.
- **step_114–121** (t=3625–3714s): lướt pill thể loại ở chi tiết phim: `btnHeroEpisodes` → `btnHeroFavorite` (`ĐÃ LƯU (TẬP 01 · 03:31/01:12:14)`) → `btnHeroNext` (`PHIM KHÁC`) → các `tvFilterTitle` (`Anime & Hoạt Hình`, `Hàn Quốc`…). Ảnh mission 16/17 khớp với đoạn này.
- **step_122–127** (t=3726–3782s): DPAD_LEFT ×5 + DPAD_RIGHT ×1 qua các pill thể loại (`Hàn Quốc` → `Anime & Hoạt Hình` → `Phim Lẻ` → `Phim Bộ` → `Mới Cập Nhật` → `Tìm Kiếm`), focus di chuyển được, có ring — app hồi phục sau chaos, không crash.

---

## D. Video — 9 frame trích bằng ffmpeg

`full_qa_tour.mp4`: 456,2 s, 1280×720, H.264, 14,9 MB. Phiên thực 3823 s → video chỉ bằng **11,9% thời lượng thực**. Nhưng đối chiếu thời điểm: frame 102s ≈ step 44 (t=855s), frame 240s ≈ step 89–91 (t≈1870–1970s), frame 450s ≈ step 116 (t=3657s) → tỉ lệ nén khá đều **~8,1–8,4×**. Kết luận: đây là **bản tua nhanh ~8× bao phủ gần như toàn bộ phiên (từ launcher tới ~step 116–121)**, không phải bản ghi realtime đầy đủ, cũng không phải chỉ quay đoạn đầu. `qa_timelapse.mp4` 47,4 s ≈ ~80×, chỉ xem lướt được bố cục.

- **frame_0s:** Màn hình chính Android TV launcher (chưa vào app): `Search movies, TV, and more`, `Apps`, `Add app to favori…`, đồng hồ `12:56`. 720p.
- **frame_90s:** Schedule — hàng đầu Detroit **bị cắt nửa trên dưới nav** (lỗi lặp lại), focus ring trắng quanh hàng bị che.
- **frame_102s:** **Sport OSD (Fix 2) trong video** — `◀ QUAY LẠI` + pill `DET 92 - 94 LOS`, giữa `TUA -30S / ▶ PHÁT (viền trắng = focus) / TUA +30S`, dưới `KÊNH TIẾNG | 00:00 | núm trắng | Về trực tiếp | 00:06 | TÙY CHỌN | TỈ LỆ`. Bug tỉ số trong stream lúc này: `LAL 95 - 92 DET, 4TH 6:36` — pill app (`DET 92`, `LOS 94`) lệch với bug đài (`DET 92` khớp, `LAL 95` vs `LOS 94` lệch 1 điểm). Khẳng định lại từ step_044: pill và bug đài không đồng bộ.
- **frame_120s:** Schedule (như frame_90s), hàng đầu vẫn bị cắt.
- **frame_190s:** VOD OSD khi tạm dừng — `00:07 / 1:12:07`, nút `PHÁT` có viền trắng, hàng nút dưới **hiện đầy đủ** (chỉ cắt phải ở `TỐ`). Tổng thời lượng lại là một con số mới: `1:12:07` (trước đó đã thấy 1:11:37, 1:08:43, 1:08:23, 1:08:00, 1:03:48…). Trong khung hình phim có đồng hồ đếm ngược `02:59:59` của chính show truyền hình (không phải UI app).
- **frame_240s:** VOD đang phát (cảnh bàn tay trên cỏ), không OSD. Trên đầu khung hình có **dòng quảng cáo cờ bạc chèn sẵn trong nguồn phim**: `Bộ phim này do : 9922.com tài trợ… Nổ Hũ, Game Bài, Bắn Cá, Sòng Bài, Thể Thao. Rút tiền 24/7…` — đây là nội dung của stream lậu, không phải UI của app, nhưng nó hiện trên màn hình người dùng.
- **frame_300s:** VOD OSD khi đang phát — `05:05 / 1:07:09`, nút `TẠM DỪNG` có viền trắng, **hàng nút dưới bị cắt nửa dưới ở mép màn hình** (khẳng định lỗi này không phải artifact của ảnh chụp — nó có trong cả video). Tổng thời lượng lại đổi: `1:07:09`.
- **frame_360s:** VOD OSD khi đang phát — `12:54 / 59:20`, hàng nút dưới **bị cắt nửa dưới** (như frame_300s). Tổng thời lượng lại đổi: `59:20`.
- **frame_450s:** Chi tiết phim, focus viền trắng ở `PHIM KHÁC`, `✓ ĐÃ LƯU (TẬP 01 · 03:31/01:12:14)`. Back che chữ `C` của `Cuộc…`, chữ mờ `…ĐẶC SẮC` sau nav vẫn thấy.

**Kết luận video:** bản tour nén ~8×, bao phủ gần hết phiên, đủ để xác nhận Sport OSD và VOD OSD bằng chuyển động; không thay thế được bản ghi realtime (không xem được thao tác D-pad chi tiết, không nghe được âm thanh, 720p mờ hơn ảnh chụp 1920×1080). Timelapse 47s chỉ có giá trị xem lướt.

---

## E. Kết luận (verdict)

### E1. Ba fix — kiểm chứng trên màn hình

| Fix | Kết quả | Bằng chứng chính |
|---|---|---|
| **Fix 1 — Tỉ số ảo** | ✅ **XÁC NHẬN ĐÃ SỬA (trên màn hình)** | Không có tỉ số bóng đá nào vượt quy tắc (mỗi bên ≤ 9, tổng ≤ 12) trong tất cả ảnh đã xem. Hero `Queretaro 3:5 Puebla` (step_006–012, ảnh 03). Card live hiện `VS` thay vì tỉ số (ảnh 02, 03, 07; steps 005–012). Card Deportes live: `VS` + pill `Hiệp 2: 72'` — ẩn tỉ số nhưng giữ phút (step_006/007). Bóng rổ hiện đúng: `Detroit 81:88 Los Angeles` (step_006–009), pill Sport `DET 92 - 94 LOS` (step_044). Không thấy `6844,4K` ở đâu — lượt xem toàn dạng K (`302,9K`, `303,3K`, `127,0K`…). Không thấy pill `0` xám. **Không thấy tỉ số `2:8`** trong run này (không kiểm được trường hợp này). **Chưa kiểm được 2 điểm:** (a) định dạng `M` (`6,8M`) — không có lượt xem nào ≥ 1M xuất hiện trong phiên nên không có mẫu để xem; (b) tỉ số pill Sport lệch với bug đài trong stream (xem E4). |
| **Fix 2 — Sport Player OSD** | ✅ **XÁC NHẬN ĐÃ SỬA (trên màn hình)** — nhưng bằng chứng nằm ở **step_044** (mission Schedule), KHÔNG phải ảnh mission 06 (ảnh đó là màn hình Tìm kiếm) | step_044 + video frame_102s: top bar chỉ còn `QUAY LẠI` + pill `DET 92 - 94 LOS` (không còn hàng 6–7 nút); pill gọn, nền tối, góc trái trên; scrim trên đọc được; **focus viền trắng rõ trên nút `▶ PHÁT` giữa màn hình (D14 đã hết)**; bar dưới rõ trên nền kính (`KÊNH TIẾNG | 00:00 | núm trắng | Về trực tiếp | 00:06 | TÙY CHỌN | TỈ LỆ`). Đối chiếu BEFORE (run 42520284499 shot 06): 6 nút + tiêu đề trùng 3 lần + không focus + bar tàng hình — tất cả đã hết. **Còn tồn tại:** pill không có phút/hiệp; bar live `00:00/00:06` (6 giây) thay vì fallback bar đỏ 100% theo luật support-gate; pill lệch 1–2 điểm so với bug đài (xem E4). |
| **Fix 3 — VOD Player** | ⚠️ **MỘT NỬA: native VOD đã vào được và audit được; WebPlayer CHƯA BAO GIỜ tới** | **Đã tới:** mission 14 steps 84–93 — PlayerActivity (native) `Cuộc Chiến Ẩm Thực - Tập 01`, video phát được (steps 89–91, 93 có phụ đề `Chưa đến lúc đâu.`). Audit OSD native vs mẫu `player-sample-vod.jpg`: tiêu đề 1 dòng căn giữa, không trùng ✅; không có nút PIP ✅; thanh trượt dọc trái ✅; seek bar đầy đủ `00:36 → 1:11:37` / `03:31 → 1:08:43` ✅; focus thấy rõ trên `PHÁT` (step_092) và `THỬ LẠI` (steps 85, 96, 98, 102, 111) ✅. **Chưa đạt mẫu:** không có cụm pause/±10s ở giữa màn hình (giữa trống; pause chỉ có ở hàng nút dưới); không thấy `SKIP INTRO`; không thấy nút `Lock`; không thấy `Speed`/`Next Ep` dạng mẫu — hàng nút dưới là `PHÁT / TUA -10S / TUA +10S / TẬP TRƯỚC / TẬP TIẾP / CHỌN TẬP / ÂM THANH & PHỤ ĐỀ / TỐ…` (nút cuối bị cắt). **Chưa tới:** trong 127 step, activity chỉ có `MainActivity` và `PlayerActivity` — **không có `WebPlayerActivity` lần nào**. Mission 14 tên "WebPlayer" nhưng AI mở native player bằng `btnHeroPlay`. Gate Speed bằng JS probe, EPG bar/Mini-Guide, subtitle anchor (trừ 1 bằng chứng ở step_107) vẫn **chưa được kiểm trên màn hình**. |

### E2. Chấm 12 finding của judge (từng cái một)

| # | Finding (judge) | Phán quyết | Bằng chứng |
|---|---|---|---|
| 1 | MEDIUM step 52: Sidebar Rail không mở bằng DPAD_LEFT từ mép trái | **THẬT** | Steps 47–52: DPAD_LEFT ×5, focus đứng yên ở `schedCard` Detroit, ảnh step_052 + ảnh mission 09 không có rail. |
| 2 | MEDIUM (deep probe): kẹt focus ở `edtM3uUrl` khi DPAD_DOWN | **THẬT, nhưng là 1 nguyên nhân đếm 3 lần** (gộp với #3, #4) | Steps 58–61: DOWN ×3 + RIGHT, focus không rời `edtM3uUrl`; ảnh step_058/061/062: bàn phím mở che nút. |
| 3 | MEDIUM step 61: kẹt focus ở `edtM3uUrl`, không xuống được nút | **THẬT (trùng #2)** | Ảnh step_061: nút `ĐÓNG`/`LƯU & NẠP KÊNH` bị cắt nửa ở mép dialog. Judge ghi sai: step 61 AI bấm DPAD_RIGHT, các lần DOWN là steps 58–60. |
| 4 | MEDIUM step 62: kẹt focus ở `edtM3uUrl` (y hệt #3) | **THẬT (trùng #2, #3)** | Ảnh step_062 gần như giống hệt step_061. 3 finding = 1 trap. **Nguyên nhân đúng là bàn phím mềm** (step_064 sau khi tắt bàn phím thì nút hiện đủ, step_065 focus tới được `ĐÓNG` và đóng dialog) — không phải `nextFocusDown` như judge đoán. Mức MEDIUM là hợp lý cho trap, nhưng ×3 là đếm trùng. |
| 5 | LOW step 69: IPTV không phát, kẹt ở `Đang tải nguồn...` | **ĐÚNG LÚC ĐÓ, PHÓNG ĐẠI thành lỗi** | Step_069: VTV8 HD đen + `Đang tải luồng…` là thật. Nhưng step_070 (48s sau) đã tự failover sang ANTV HD đang phát (motion 3,58%), step_071 phát tiếp. Đây là zapping/failover thoáng qua, tự hồi phục — không phải lỗi đứng yên. LOW là đúng mức, câu chữ "không phát được" là quá. |
| 6 | LOW step 86: ERROR_CODE_DECODING_FAILED | **THẬT, nhưng là 1 trong 4 lần xuất hiện của cùng 1 lỗi** | Steps 85–88: cùng 1 dialog ở `00:36/1:11:37`, khung hình đứng yên. |
| 7 | LOW step 87: như trên | **THẬT (trùng #6)** | Giống hệt step_086. |
| 8 | LOW step 88: như trên | **THẬT (trùng #6)** | Giống hệt step_086/087. |
| 9 | LOW step 96: ERROR_CODE_DECODING_FAILED | **THẬT — lần xuất hiện thứ 2** | Steps 96–99: dialog ở `03:51–04:13 / 1:08:xx`, khung hình khác sự kiện #6. |
| 10 | LOW step 97: như trên | **THẬT (trùng #9)** | Giống step_096. |
| 11 | LOW step 99: như trên | **THẬT (trùng #9)** | Giống step_096–098 (judge bỏ qua step_098 cũng là dialog lỗi — đếm không nhất quán). |
| 12 | LOW step 112: ERROR_CODE_DECODING_FAILED | **THẬT — nhưng còn 2 lần xuất hiện khác judge không liệt kê** | Step_112: dialog ở `22:47/49:27`. Judge bỏ qua step_102 (lần 3, `08:26/1:03:48`) và step_111 (cùng lần 4). Tổng cộng dialog lỗi xuất hiện ở **11 step, thuộc 4 lần riêng biệt** (A: 85–88, B: 96–99, C: 102, D: 111–112), lần nào video cũng phát lại được sau đó (steps 89–91, 100–101, 103–110). Nhiều khả năng là codec emulator x86 (như chính judge ghi) — nhưng **tái diễn 4 lần trong 1 phiên trên cùng 1 tập phim** thì không thể gọi là "1 lỗi môi trường" cho xong; cần kiểm trên thiết bị thật. Mức LOW cho từng lần là hợp lý, nhưng pattern tổng thể đáng chú ý hơn điểm số thể hiện. |

**Tóm tắt đếm trùng:** 12 finding của judge thực chất chỉ còn **5 vấn đề riêng biệt**: (1) rail không mở, (2) trap M3U do bàn phím, (3) IPTV loading thoáng qua, (4) decoding failed tái diễn, (5) — không được judge đếm — hàng nút dưới VOD bị cắt (xem E4). Trong đó 10/12 finding là đếm trùng của 2 nguyên nhân (M3U ×3, decoding ×7).

### E3. Điểm 64/100 — có công bằng không?

**Không công bằng nếu hiểu là điểm chất lượng build; có thể hiểu nếu hiểu là điểm QA nghiêm khắc có trừ trùng lặp.** Phân tích:

- **Điểm trừ bị phình to do đếm trùng:** 10/12 finding là trùng lặp. Nếu gộp về 5 vấn đề riêng biệt thì số lỗi thực ít hơn một nửa.
- **Judge chấm 16/16 checks và 16/16 missions đều PASS**, video phát được ở hầu hết các step player (motion 2,89–29,83%), 3 fix thì 2 fix xác nhận trên màn hình, fix thứ 3 một nửa — bức tranh tổng thể tốt hơn con số 64.
- **Nhưng 64 không phải vô căn cứ:** rail không mở (MEDIUM thật), trap M3U (MEDIUM thật), decoding tái diễn 4 lần, VOD bottom-row bị cắt, Schedule bị cắt hàng đầu, pill lệch tỉ số với bug đài — đó đều là lỗi thật, người dùng sẽ gặp.
- **Ước tính sau khi khử artifact (de-artifacted): ~78–82/100.** Cách tính: xuất phát 100, trừ rail (MEDIUM, −5), trap M3U (MEDIUM, −5), decoding tái diễn (môi trường + tái diễn, −4), VOD bottom-row cắt + subtitle va chạm (mới, −3), Schedule cắt hàng đầu + Phim detail back che tiêu đề (mới, −3), pill lệch bug đài + tổng thời lượng VOD nhảy số (−2). Phần còn lại (điều hướng, focus, palette, phát video, lưu phim, tìm kiếm, cài đặt) chạy tốt. Con số này là ước tính của người review, không phải điểm đo được.

### E4. Các lỗi khác nhìn thấy bằng mắt (ngoài 12 finding)

1. **(MỚI, đáng sửa) Hàng nút dưới của VOD OSD bị cắt nửa dưới khi video đang phát** — steps 102, 107, 108, 110, 111, 112 + video frames 300s, 360s. Khi tạm dừng (nút đầu `PHÁT`) thì hiện đầy đủ (steps 85, 92, 96, 98 + frame 190s). Quy luật theo trạng thái phát/dừng, rất có thể là bug layout.
2. **(MỚI) Nút cuối hàng dưới VOD luôn bị cắt ở mép phải** — chỉ còn `TỐ` (steps 85–88, 92, 96–99, 102, 107, 108, 110–112) hoặc `T` (step_112). Hàng 8 nút không vừa 1920px; nút Tốc độ gần như không bấm được.
3. **(MỚI) Phụ đề đè lên thanh seek khi OSD VOD mở** — step_107: `ai không chịu nghe thì bị` nằm đúng trên vạch seek bar. (Subtitle anchor chưa đúng khi OSD hiện — đúng thứ mà review run trước nói là "chưa được kiểm chứng", giờ đã thấy bằng chứng.)
4. **(MỚI) Tổng thời lượng VOD nhảy lung tung** — cùng tập `Cuộc Chiến Ẩm Thực - Tập 01`: `1:11:37 → 1:08:43 → 1:08:23 → 1:08:00 → 1:03:48 → 59:20 → 55:26 → 53:53 → 50:30 → 49:27 → 1:12:07 → 1:07:09` (12 giá trị khác nhau), trong khi chip resume ghi `01:12:14`. Nhiều khả năng mỗi lần retry đổi server và server trả duration khác — resume/seek dựa trên con số này sẽ không đáng tin.
5. **(MỚI) Pill tỉ số Sport lệch với bug tỉ số trong stream** — step_044: pill `DET 92 - 94 LOS` vs bug đài `LAL 95 - 94 DET`; video frame_102s: pill `DET 92 - 94 LOS` vs bug `LAL 95 - 92 DET` (4TH 6:36). Pill lấy từ API (trễ), bug đài là live — trên cùng màn hình có 2 tỉ số khác nhau. Fix 1 sửa "tỉ số ảo" nhưng chưa sửa "tỉ số không đồng bộ".
6. **(MỚI) Hàng đầu Schedule luôn bị cắt nửa trên dưới thanh nav** — ảnh 04, 08, 09, 19, 20, 21, 22, 52 + video frames 90s, 120s. Card focus đầu tiên lúc nào cũng chỉ thấy nửa dưới.
7. **(MỚI) Chi tiết phim: nút back tròn che chữ `C` của tiêu đề `Cuộc…`, và dòng chữ mờ `…ĐẶC SẮC` bị cắt sau thanh nav** — ảnh 12, 13, 14, 16, 17, 73, 75, 83, 94, 113 + video frame_450s. Lặp lại ở mọi ảnh chi tiết phim.
8. **(MỚI) Phòng NBA hiện `0 lượt xem` trong khi card trận hiện `127,0K xem`** — step_043 (4 phòng BRIAN/CHAN SENA/BLV HENRY/ZERO đều `0 lượt xem · LIVE`). Số người xem ở 2 chỗ không khớp nhau.
9. **IPTV OSD: chữ `Đang chiếu: …` đè lên logo ANTV của stream** — steps 24–28, 70 (logo đỏ ANTV nằm đúng dưới dòng chữ trắng). Không có bottom bar và không có center control ở OSD IPTV (ngoài phạm vi Fix 2, nhưng vẫn là điểm trừ nhìn thấy).
10. **Tên mission không khớp việc AI thực sự làm** — mission 6 "Home Hub 3 cards" thực tế đi Search (`uefaq`) + Cài đặt; mission 14 "WebPlayer" mở native player; mission 15 "Player Settings Dialog" không mở settings dialog nào; mission 16 "Search & Settings" chủ yếu lướt pill phim. Checks/missions vẫn PASS 16/16 nên verdict mission là lỏng — điểm 64 của judge không phản ánh sự lỏng này, nhưng người đọc báo cáo cần biết: **WebPlayer, EPG bar/Mini-Guide, Sport ±30s seek gate vẫn chưa được kiểm trên màn hình**.
11. **Quảng cáo cờ bạc chèn trong nguồn phim** — video frame_240s: `9922.com… Nổ Hũ, Game Bài…` là nội dung của stream, không phải UI app. Không tính là lỗi app, nhưng người dùng sẽ thấy nó.
12. **Nhỏ:** lượt xem `302,6K` (step_031) vs `302,9K` (hero) cho cùng trận cùng lúc — số live thay đổi theo thời gian, bình thường, không tính là lỗi. Avatar BLV dạng vòng tròn xám trống lúc mới load (ảnh 04) rồi load đủ sau (ảnh 09) — bình thường.

### E5. Tóm tắt verdict cuối

- **Fix 1 (tỉ số ảo): CÓ trên màn hình.** Không còn tỉ số bóng đá ảo; `VS` hiện đúng chỗ; bóng rổ `81:88` và `92-94` hiện đúng.
- **Fix 2 (Sport OSD): CÓ trên màn hình** (step_044 + video frame_102s, không phải ảnh mission 06). Hết hàng 6 nút, hết tiêu đề trùng, có focus trắng trên PHÁT, bar dưới rõ. Còn: pill thiếu phút/hiệp, bar live `00:00/00:06`, pill lệch bug đài 1–2 điểm.
- **Fix 3 (VOD): MỘT NỬA.** Native VOD vào được, phát được, OSD gọn hơn mẫu ở vài điểm nhưng thiếu cụm giữa, thiếu SKIP INTRO/Lock, hàng nút dưới bị cắt phải + cắt nửa dưới khi đang phát, phụ đề đè seek bar, tổng thời lượng nhảy số. **WebPlayerActivity chưa tới lần nào — phần web của Fix 3 chưa được kiểm chứng.**
- **12 finding: 5 vấn đề thật, 10/12 là đếm trùng.** Nặng nhất và thật nhất: rail không mở (step 52), trap M3U do bàn phím (steps 58–62), decoding failed tái diễn 4 lần (11 step).
- **Video: bản tua nhanh ~8× bao phủ gần hết phiên** (456,2s / 3823s), đủ để xác nhận Sport OSD và VOD OSD bằng chuyển động; không phải bản ghi realtime đầy đủ.
- **Điểm 64/100: khắc nghiệt so với chất lượng build thực; ước tính sau khử artifact ~78–82/100.** Merge vẫn cần cân nhắc 5 vấn đề thật + các lỗi mới ở E4, đặc biệt rail, trap M3U, và hàng nút VOD bị cắt khi đang phát.

---

*Người review: subagent visual review · Ngày: 2026-11-09 · Nguồn: `~/workspace/kenhlive-plan/qa-run-42542517168/` (`qa_report.json`, `qa_session.json`, `shots/`, `full_qa_tour.mp4`), ảnh BEFORE `~/workspace/kenhlive-plan/qa-run-42520284499/shots/06_mission_player_streaming_and_controls.jpg`, mẫu VOD `~/workspace/kenhlive-plan/player-sample-vod.jpg`. Frame video trích ra `/tmp/qa42542517168/frame_{0,90,102,120,190,240,300,360,450}.jpg` (thư mục tạm, không phải deliverable).*

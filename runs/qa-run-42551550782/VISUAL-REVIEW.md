# Đánh giá trực quan QA — CI run 42551550782 (Fix 4, commit 1707d87)

- **Run:** 42551550782 · **Branch:** `redesign/netflix` · **Commit:** `1707d87` (Fix 4)
- **Phiên:** `QA-SESS-20261109-023734-e72c3f` · **Thời lượng:** 4669,5 s · **Điểm judge (OPENAI):** 98/100
- **Checks:** 16/16 · **Missions:** 16/16 · **Steps:** 129 · **Findings của judge:** 1 (LOW, step 103)
- **Phương pháp:** đọc trực tiếp bằng mắt từng ảnh, đối chiếu với `qa_session.json` (timeline, focus, motion) và `qa_report.json`. Không tin điểm số hay kết luận của judge khi chưa có bằng chứng hình ảnh.
- **Độ phủ xem trực tiếp:** **17 ảnh mission + 61 ảnh step + 9 frame video tour + 3 frame đầu video phụ + 2 ảnh mẫu + 4 ảnh crop phóng to** (pill, thanh bar Sport, phụ đề/hàng nút VOD). **68 ảnh step còn lại chưa xem trực tiếp từng ảnh** — được mô tả theo timeline trong mục B.2, ghi rõ là chưa eyeball.
- **Lưu ý về cách đặt tên ảnh:** ảnh mission `NN_mission_*.jpg` là ảnh **cuối mission** (sau khi AI đã BACK/chuyển tab), nên tên mission thường **không khớp** nội dung ảnh (vd: ảnh 02 mission cold start thực ra là Sport player; ảnh 14 mission VOD thực ra là màn hình chi tiết phim). Bằng chứng player thật nằm ở các **ảnh step**, không phải ảnh mission.
- **Lưu ý về độ phân giải:** ảnh chụp trong run này là **960×540** (không phải 1920×1080 như run trước) — chi tiết nhỏ (vạch bar 2–3px) có thể bị mờ, nhưng mọi kết luận dưới đây đều dựa trên chi tiết nhìn thấy rõ ở độ phân giải này, và đã phóng to crop để kiểm tra những điểm nghi ngờ.

---

## A. Ảnh mission (01–17) — mô tả bằng mắt

### 01_cold_start.jpg — Home, hero Albirex Niigata VS Tokushima Vortis
Home sau khởi động lạnh (không còn dialog Telegram trong ảnh này — dialog đã đóng ở step_001). Hero: `Albirex Niigata VS Tokushima Vortis`, `Trực tiếp · JPN D2 · BLV ĐÓM · Tín hiệu HD`, `242,3K` xem, ngày `Thứ Hai, 09/11/2026 09:37`. Nút `[OK] XEM NGAY` (focus đỏ) và `[MENU] CHỌN PHÒNG`. Hàng `ĐANG PHÁT TRỰC TIẾP`: 3 card live đều `VS` (không tỉ số). Palette KL6.5 đúng. Không tỉ số ảo.

### 02_mission_cold_start.jpg — Sport player, trận Club Leon vs Guadalajara (KHÔNG phải Home!)
Ảnh cuối mission cold start thực ra là **Sport OSD đã mở**: sân bóng, pill `CLU - CLU` (xem phân tích ở mục B — 2 đội cùng mã CLU, không tỉ số, không phút), giữa màn hình chỉ có nút `▶ PHÁT` (viền trắng = focus), dưới `KÊNH TIẾNG | 00:00 | ● TRỰC TIẾP | TÙY CHỌN | TỈ LỆ`. Không có nút ±30s, không thấy vạch seek bar hay tổng thời gian. Bug của đài trong stream hiện quảng cáo `JAMAICA vs MEXICO`. Đây là bằng chứng đầu tiên cho thấy pill Sport có vấn đề (mục F).

### 03_mission_sports_multi_source.jpg — Home, rail thể thao
3 card live đầu đều `VS` (`Club Le… VS Club D…`, `Alianza VS Llanero…`, `Piratas… VS Cancun…`), lượt xem `374,3K / 166,9K / 121,9K`. Hàng `TRẬN CẦU SẮP DIỄN RA`: `Khaan… 12:00 Khovd…` (`Còn 2h 22p`), `Fujian… 14:00 Hebei…`, `Qingda… 14:00 Wu…`. Không tỉ số ảo, không có lượt xem ≥ 1M nên **không kiểm được định dạng `M` (`6,8M`)** trong ảnh này (và trong cả run — xem mục D, Fix 1).

### 04_mission_sports_room_picker.jpg — Dialog chọn phòng Club Leon (6 phòng)
Dialog `Club Leon vs Club Deportivo Guadalajara — MEX D1 · 6 phòng live`: `ZIZOU (最高等级) — 67,6K lượt xem · LIVE · Điểm: 272,7K`, `BLV COCA (Lv.5) — 66,7K`, `RICKHANTER (Lv.4) — 65,5K`, `BLV CUỘI (Lv.2) — 64,6K`. Dialog sạch, không cắt. 2 ghi chú: (1) chữ Trung Quốc `(最高等级)` (= "cấp cao nhất") hiện nguyên văn trong giao diện tiếng Việt — chuỗi chưa dịch; (2) các phòng ở đây **có** lượt xem thật (khác hẳn step_044, xem mục F).

### 05_mission_sports_data_accuracy.jpg — Home (giống ảnh 03, đã cuộn)
Như ảnh 03: card live toàn `VS`, lượt xem `374,3K / 166,9K / 121,9K`, trận sắp diễn ra `Khaan 12:00`, `Fujian 14:00`, `Qingda 14:00`. Không có tỉ số nào để sai — mission "data accuracy" không kiểm được tỉ số ở màn hình này, chỉ kiểm được "không hiện tỉ số ảo".

### 06_mission_player_streaming_and_controls.jpg — Sport player, trận Club Leon (TRÙNG nội dung step_006/031/032)
Giống ảnh 02: pill `CLU - CLU`, chỉ có nút `▶ PHÁT` ở giữa, dưới `KÊNH TIẾNG | 00:00 | ● TRỰC TIẾP | TÙY CHỌN | TỈ LỆ`. Không ±30s, không vạch bar. (Tên mission là "player streaming" nhưng ảnh này đúng là player — khác run trước, khi ảnh 06 là màn hình Tìm kiếm.)

### 07_mission_home_hub_3_cards_and_canva_logos.jpg — Home (TRÙNG step_042)
Như ảnh 03/05, focus viền trắng ở card trận sắp diễn ra `Khaan… 12:00 Khovd…`. Card live toàn `VS`. Logo đội hiển thị đủ.

### 08_mission_schedule_epg_and_fixture_tap.jpg — Sport player, trận Piratas vs Cancun (KHÔNG phải Schedule!)
Ảnh cuối mission Schedule thực ra là **Sport OSD**: pill `Hiệp 2: 90+' · PIR - CAN` — **có phút hiệp 2** (bằng chứng Fix 4d, xem mục D), vẫn không có tỉ số (bug đài trong stream hiện `PIR 1 - 1 CAN, MARCADOR GLOBAL 2-2`). Giữa màn hình chỉ có `▶ PHÁT` (viền trắng). Dưới `KÊNH TIẾNG | 00:00 | Về trực tiếp | ● TRỰC TIẾP | TÙY CHỌN | TỈ LỆ` — ở ảnh này nút `Về trực tiếp` CÓ hiện (trong khi ảnh 02/06 thì không — xem mục F).

### 09_mission_sidebar_rail_full_traversal.jpg — Schedule, hàng đầu ĐÃ ĐẦY ĐỦ (TRÙNG step_043/051/052/054)
Danh sách lịch: hàng đầu `08:00 Piratas FC vs Cancun FC` (focus viền trắng) **hiện đầy đủ, không bị cắt nửa trên dưới nav** — lỗi "hàng đầu Schedule bị cắt" của run trước **đã hết trong ảnh này**. Các hàng sau: `Milwaukee Bucks vs Boston Celtics` (NBA), `Alianza vs Llaneros FC`, `Universitario vs Moquehua`, `Club Leon vs Guadalajara`. Không tỉ số. Góc phải trên có một badge nhỏ bị cắt ở mép (`26 trận` — chỉ thấy một phần, không đọc được hết). **Không có sidebar rail nào** sau các lần DPAD_LEFT (xem step_051–054, mục F).

### 10_mission_iptv_categories_and_favorites.jpg — IPTV, hero VTV6, mục Yêu thích (TRÙNG step_062/065)
Hero `VTV6 — Đang phát trực tiếp từ Đài Truyền hình Quốc gia`, nút `XEM TOÀN MÀN HÌNH` (đỏ), `✓ YÊU THÍCH`, `NGUỒN M3U`; logo box phải trên hiện `VTV` (đúng mạng VTV). Pill thể loại `Tất cả / Yêu thích (đang chọn) / VTV / HTV / Thể thao / Phim tru…` (pill cuối bị cắt ở mép phải — cuộn ngang, bình thường). Mục `Kênh yêu thích`: card `VTV6 — Việt Nam` (focus viền trắng). Sạch, không lỗi. **Không có dialog M3U nào trong ảnh này** (AI không mở M3U trong run này — xem mục F).

### 11_mission_iptv_epg_and_zapping_player.jpg — IPTV VTV6 (gần như TRÙNG ảnh 10)
Giống ảnh 10, chỉ khác focus chuyển sang pill `Tất cả`. **Không có player IPTV nào** — mission tên "zapping player" nhưng AI chưa bao giờ mở player IPTV trong run này (xem mục B, steps 65–71).

### 12_mission_phim_nguonc_and_categories.jpg — Chi tiết phim (TRÙNG step_075/087)
`Cuộc Chiến Ẩm Thực`, `2026 · Chính Kịch`, mô tả `The Table: K-Chef 2026…`, nút `XEM NGAY` (focus viền trắng), `CHỌN TẬP`, `+ LƯU PHIM`, `PHIM KHÁC`; `DANH MỤC: Tất Cả / Lịch Sử Xem / Tìm Kiếm / Mới Cập Nhật / Phim Bộ / Phim Lẻ / Anime & H…`; `Phim Mới Cập Nhật — 120 phim`. **2 lỗi cũ vẫn còn nguyên:** (1) nút back tròn (◀) ở góc trái **che mất chữ `C` đầu tiên của tiêu đề `Cuộc…`**; (2) dòng chữ mờ `…ĐẶC SẮC` bị cắt dở phía sau thanh nav trên cùng.

### 13_mission_phim_episode_picker_and_favorite.jpg — Chi tiết phim, focus CHỌN TẬP (TRÙNG step_078)
Giống khung 12 nhưng focus chuyển sang nút `CHỌN TẬP`. Nút vẫn là `+ LƯU PHIM` (chưa lưu). Vẫn còn lỗi back che chữ `C` và chữ mờ sau nav.

### 14_mission_vod_player_seek_and_resume.jpg — Chi tiết phim, có hàng TIẾP TỤC XEM (TRÙNG step_095/116)
Giống khung 12/13 nhưng hàng dưới đổi thành `TIẾP TỤC XEM — 1 phim` (resume đã ghi nhận sau khi xem VOD). **Không có VOD player trong ảnh này.** VOD player thật nằm ở steps 88–93, 97–113 (mục B).

### 15_mission_player_settings_dialog.jpg — VOD OSD khi TẠM DỪNG (TRÙNG step_113/114)
`Cuộc Chiến Ẩm Thực - Tập 01`, tiêu đề căn giữa 1 dòng; thanh trượt dọc trái (độ sáng) + icon bánh răng; seek bar `26:31 / 45:43` (núm đỏ); hàng nút dưới `PHÁT (focus viền trắng) / TUA -10S / TUA +10S / TẬP TRƯỚC / TẬP TIẾP / CHỌN TẬP / ÂM THANH & PHỤ ĐỀ / TỐ…` — **hàng nút hiện đầy đủ theo chiều dọc** (không bị cắt nửa dưới như run trước khi tạm dừng), nhưng **nút cuối vẫn chỉ còn `TỐ`** (cắt ở mép phải). **Không có settings dialog nào** trong mission này — tên mission không đúng với những gì AI đã làm (chỉ phát phim, không mở dialog cài đặt).

### 16_mission_search_and_settings_feedback.jpg — Tìm kiếm
Tab `TÌM KIẾM` đang chọn: chip `Phim Mới / Hoạt Hình / MEX D1 / Bóng Rổ NBA / Ngoại Hạng Anh / La Liga / Ligu…`, `24 trận đang live`, `Xu hướng tìm kiếm: One Piece, Conan, Ao no Hako`, kết quả `Club Leon vs Club Deportivo Guadalajara — BLV TAP +5 BLV · 380,5K · 6 phòng`, `Los Angeles Clippers vs New Orleans Pelicans — BRIAN +1 BLV · 56,0K · 2 phòng`. Sạch, không lỗi. **Không có màn hình Cài đặt nào** — mission tên "Search & Settings" nhưng AI chỉ vào Tìm kiếm, không vào Cài đặt.

### 17_mission_dpad_chaos_stress_and_recovery.jpg — Tìm kiếm, focus chip La Liga
Giống khung 16, focus viền trắng chuyển sang chip `La Liga`. App không crash sau chuỗi DPAD chaos — màn hình vẫn bình thường, focus di chuyển được.

---

## B. Ảnh step

### B.1 Đã xem trực tiếp (61 ảnh)

#### MISSION_COLD_START — steps 1–5
- **step_001** (t=25s): Dialog Telegram lúc khởi động lạnh — `THÔNG BÁO — NHÓM THẢO LUẬN & HỖ TRỢ TRỰC TUYẾN`, QR + `Nhóm Telegram: @kenhlivetv`, 2 nút `ĐÃ HIỂU / ĐÓNG` (đỏ, focus) và `VÀO NHÓM TELEGRAM`. Sạch, không cắt chữ. (Giải thích vì sao ảnh mission 01 không còn dialog: dialog đã đóng ở step này.)
- **step_003** (t=60s): Home đã cuộn xuống — card live toàn `VS` (`374,3K / 166,9K / 121,9K`), hàng `TRẬN CẦU SẮP DIỄN RA` + `PHIM ĐANG THỊNH HÀNH` ở cuối. Không tỉ số ảo.
- **step_005** (t=83s): Dialog chọn phòng Club Leon (xem ảnh mission 04 — cùng nội dung, 6 phòng, phòng đầu `BLV TAP (最高等级) — 75,6K lượt xem`).

#### MISSION_SPORTS_MULTI_SOURCE — steps 6–13 (Sport player)
- **step_006** (t=192s): Sport OSD trận Club Leon. Pill `CLU - CLU` (không tỉ số, không phút). Giữa chỉ có `▶ PHÁT` (viền trắng). Dưới `KÊNH TIẾNG | 00:00 | ● TRỰC TIẾP | TÙY CHỌN | TỈ LỆ` — **không có nút `Về trực tiếp`, không có vạch seek bar, không có tổng thời gian**. Không có ±30s.
- **step_007** (t=256s): Như step_006, nhưng dưới **CÓ nút `Về trực tiếp`** (`KÊNH TIẾNG | 00:00 | Về trực tiếp | ● TRỰC TIẾP | TÙY CHỌN | TỈ LỆ`). Cùng một trận, cùng một OSD, nút `Về trực tiếp` lúc có lúc không (xem mục F).
- **step_008** (t=272s): OSD đã tự ẩn — toàn màn hình video. Bug tỉ số **của đài** hiện rõ: `LIGA BBVA MX | LEO 0 - 0 GDL | 29:44`. Đây là bằng chứng then chốt: trận đang ở phút 29:44, tỉ số 0-0 (hoàn toàn hợp lệ), vậy mà pill app (`CLU - CLU`) không hiện cả tỉ số lẫn phút, lại còn gán cùng một mã `CLU` cho 2 đội khác nhau (đài dùng `LEO` / `GDL`). Dưới cùng là banner quảng cáo cờ bạc `BUFA` chèn trong stream (nội dung của nguồn phát, không phải UI app).
- **step_031** (t=991s): Sport OSD trận Club Leon, pill `CLU - CLU` (vẫn không phút, không tỉ số), không có `Về trực tiếp`. **step_032** (t=1103s): giống hệt, pill `CLU - CLU`.

#### MISSION_PLAYER_STREAMING_AND_CONTROLS — steps 27–31 (Sport player, trận Piratas)
- **step_027** (t=679s): Sport OSD trận Piratas vs Cancun. Pill `PIR - CAN` — **không có phút** (dù trận đã đá từ 08:00). Bug đài: `PIR 1 - 1 CAN, MARCADOR GLOBAL 2-2`. Pill ẩn tỉ số 1-1 (hợp lệ) và không hiện phút. Dưới: `KÊNH TIẾNG | 00:00 | ● TRỰC TIẾP | TÙY CHỌN | TỈ LỆ` (không `Về trực tiếp`).
- **step_028** (t=749s): Như step_027, nhưng dưới **CÓ `Về trực tiếp`**. Pill vẫn `PIR - CAN` không phút.
- **step_030** (t=887s): OSD Sport + **một rail "đổi trận" hiện đè lên nửa dưới màn hình**: 3 card live `Club Le… VS Club D…` (`375,4K`), `Alianza VS Llanero…` (`167,1K`), `Los An… VS New…` (`54,6K`) — card đầu có viền trắng (focus). Đây là kết quả sau khi AI bấm MENU (step_028) rồi DPAD_DOWN + OK — nhiều khả năng là panel TÙY CHỌN/đổi trận. Card đọc được, không lỗi hiển thị; toàn `VS` (đúng Fix 1).

#### MISSION_SCHEDULE_EPG_AND_FIXTURE_TAP — steps 42–47
- **step_042** (t=1275s): = ảnh mission 07 (Home, focus card `Khaan 12:00`).
- **step_043** (t=1289s): = ảnh mission 09. Schedule, hàng đầu **đầy đủ, không bị cắt**; focus viền trắng ở `Piratas FC vs Cancun FC`.
- **step_044** (t=1300s): Dialog chọn phòng `Piratas FC vs Cancun FC — MEX D2 · 4 phòng live`: `BLV ENZO`, `BLV YONE`, `BLV VIP`, `BLV TOMIA` — **cả 4 đều `0 lượt xem · LIVE`**. Mâu thuẫn dữ liệu: card trận này ngoài Home hiện `121,9K xem`, nhưng cả 4 phòng đều `0 lượt xem` (lỗi đã thấy ở run trước với phòng NBA, nay lặp lại với phòng bóng đá). Dialog thì sạch, không cắt.
- **step_045** (t=1406s): Sport OSD trận Piratas. Pill **`Hiệp 2: 90+' · PIR - CAN`** — **có phút** (lần đầu thấy phút trên pill trong run này). Vẫn không có tỉ số (bug đài: `PIR 1 - 1 CAN`). Dưới: `KÊNH TIẾNG | 00:00 | Về trực tiếp | ● TRỰC TIẾP | TÙY CHỌN | TỈ LỆ`. Giữa chỉ có `▶ PHÁT` (viền trắng).
- **step_046** (t=1514s): Giống step_045, pill `Hiệp 2: 90+' · PIR - CAN`, bug đài `PIR 1 - 1 CAN`.
- **step_047** (t=1586s) và **step_048** (t=1635s): 2 ảnh **giống hệt nhau** (cùng sha256) — pill `Hiệp 2: 90+' · PIR - CAN`, `Về trực tiếp` hiện. OSD đứng yên giữa 2 step.
- **step_050** (t=1728s): OSD đã ẩn sau 2 lần BACK — toàn màn hình video, banner `BUFA` ở dưới. Bình thường.

#### MISSION_SIDEBAR_RAIL_FULL_TRAVERSAL — steps 51–54 (rail KHÔNG mở)
- **step_051, 052, 054** (t=1739–1782s): cả 3 ảnh **giống hệt nhau** (cùng sha256) — Schedule, focus đứng yên ở card `Piratas FC vs Cancun FC`, **không có sidebar rail nào**. Timeline: steps 51–54 là 4 lần DPAD_LEFT liên tiếp, focus không nhúc nhích khỏi `schedCard` Piratas (có focus ring). **Finding rail của run trước vẫn còn nguyên — và judge run này KHÔNG liệt kê nó** (xem mục E, G).

#### MISSION_IPTV_CATEGORIES_AND_FAVORITES — steps 56, 62
- **step_056** (t=1814s): IPTV hero `ANTV HD — Đang phát: [09:45 - 10:10] An ninh văn hóa 20 - Khi hội nhóm mạng xã hội dẫn lố…`, có thanh tiến trình EPG đỏ, `Tiếp theo: [10:10] Phim truyện: 45 - Phi hổ ngoại truyện - Tập 30/40`, nút `XEM TOÀN MÀN HÌNH` (focus đỏ), `+ YÊU THÍCH`, `NGUỒN M3U`; logo box `ANTV`. Lưới kênh dưới: `VTV6`, `360 Bundesli…`, `360 C1 Châu…`… Sạch, EPG đầy đủ. (So với run trước: hero ANTV lần này có EPG + nút đầy đủ, không còn cảnh "chữ đè logo" vì đây là màn hình hero, không phải player.)
- **step_062** (t=1918s): = ảnh mission 10. Hero `VTV6`, `✓ YÊU THÍCH`, mục `Kênh yêu thích` có card `VTV6` (focus). Chức năng yêu thích kênh hoạt động.

#### MISSION_IPTV_EPG_AND_ZAPPING_PLAYER — steps 65, 69, 70, 71 (KHÔNG có player IPTV)
- **step_065** (t=1962s): = ảnh mission 10 (IPTV VTV6, focus card `VTV6` ở mục Yêu thích).
- **step_069** (t=2025s): vẫn màn hình IPTV VTV6, focus chuyển sang ô `Tìm kênh TV...` (có viền trắng + con trỏ đỏ).
- **step_070** (t=2052s): ô tìm kiếm đã mở **bàn phím mềm** che nửa dưới màn hình (bàn phím QWERTY đầy đủ, nút tìm kiếm). Không kẹt — step_071 BACK đã tắt bàn phím, về lại màn hình IPTV bình thường.
- **step_071** (t=2062s): IPTV VTV6, bàn phím đã tắt, focus ở ô tìm kiếm. **Kết luận: cả mission "zapping player" (steps 65–71) AI không hề mở player IPTV** — chỉ loanh quanh ở màn hình hero + ô tìm kiếm. Lỗi "chữ đè logo ANTV" của run trước **không kiểm lại được** trong run này.

#### MISSION_PHIM — steps 73–87
- **step_073** (t=2089s): Chi tiết phim, focus viền trắng ở nav `TRANG CHỦ` trong khi tab đang chọn là `KHO PHIM` (gạch đỏ dưới KHO PHIM) — focus đang ở nav trái, nhìn hơi lạ nhưng không phải lỗi nghiêm trọng. Back che chữ `C`, chữ mờ sau nav vẫn còn.
- **step_075** (t=2114s): = ảnh mission 12. `XEM NGAY` focus viền trắng.
- **step_078** (t=2147s): = ảnh mission 13. Focus ở `CHỌN TẬP`.
- **step_084** (t=2218s): **Dialog chọn tập** — `Cuộc Chiến Ẩm Thực / Final Table`, chip `2026 / Trọn bộ`, các pill `Tập 1 … Tập 5` một hàng, `Tập 6` rớt xuống hàng dưới (đè lên poster), dòng `Không có mô tả chi tiết.` **chạy xuyên dưới hàng pill tập** (chữ bị pill che một phần), nút `LƯU PHIM / PHÁT (đỏ) / ĐÓNG (focus viền trắng)`. Dialog dùng được nhưng bố cục lộn xộn: pill tập đè lên mô tả. Không hiện thời lượng từng tập.
- **step_087** (t=2261s): = ảnh mission 12 (`XEM NGAY` focus, chuẩn bị vào VOD player).

#### MISSION_VOD_PLAYER_SEEK_AND_RESUME — steps 88–95 (native player)
- **step_088** (t=2375s): **VOD player đã vào (PlayerActivity, native)** — `Cuộc Chiến Ẩm Thực - Tập 01`. OSD tạm dừng: tiêu đề căn giữa 1 dòng; thanh trượt dọc trái + bánh răng; seek bar `01:42 / 1:10:32` (tiến trình đỏ + núm); hàng nút `PHÁT (focus viền trắng) / TUA -10S / TUA +10S / TẬP TRƯỚC / TẬP TIẾP / CHỌN TẬP / ÂM THANH & PHỤ ĐỀ / TỐ…` — **hàng nút hiện đầy đủ theo chiều dọc** (không bị cắt nửa dưới), nhưng **nút cuối vẫn chỉ còn `TỐ`**. Không có nút PIP. Không có cụm pause/±10s ở giữa màn hình (khác mẫu VOD), không thấy `SKIP INTRO`, không thấy nút `Lock`.
- **step_089** (t=2476s): `03:23 / 1:08:51` — "tổng" đã giảm từ `1:10:32` xuống `1:08:51` (xem chẩn đoán ở mục F: đây là thời gian còn lại, không phải tổng).
- **step_090** (t=2571s): `05:01 / 1:07:13`, focus chuyển sang `TUA -10S` (viền trắng). Hàng nút vẫn đầy đủ chiều dọc, nút cuối `TỐ`.
- **step_091** (t=2653s): **Lỗi decoding lần 1** — dialog `Lỗi Phát Luồng Video — Stream lỗi: ERROR_CODE_DECODING_FAILED`, nút `THỬ LẠI` (focus viền trắng), `QUAY LẠI`, `BÁO LỖI`, dòng `Báo lỗi kênh qua nhóm Telegram: @kenhlivetv`. Ở `06:01 / 1:06:13`. **Judge KHÔNG liệt kê step này.**
- **step_092** (t=2764s): Đã phát lại được (cảnh người nằm, không dialog), OSD `07:40 / 1:04:34`. Hồi phục sau lỗi lần 1.
- **step_093** (t=2819s): **Lỗi decoding lần 2** — dialog như trên, `THỬ LẠI` focus, khung hình khác (bánh sandwich). **Judge KHÔNG liệt kê.**
- **step_095** (t=2849s): = ảnh mission 14. Về lại chi tiết phim, hàng `TIẾP TỤC XEM — 1 phim`. Resume hoạt động.

#### MISSION_PLAYER_SETTINGS_DIALOG — steps 97–113 (VOD, KHÔNG có settings dialog)
- **step_097** (t=2979s): VOD OSD tạm dừng `10:18 / 1:01:56`, `PHÁT` focus. Hàng nút đầy đủ chiều dọc, nút cuối `TỐ`.
- **step_098** (t=3106s): `12:28 / 59:46` — "tổng" xuống dưới 1 giờ.
- **step_099** (t=3180s): **Lỗi decoding lần 3** — dialog ở `13:37 / 58:37`, `THỬ LẠI` focus. **Judge KHÔNG liệt kê.**
- **step_100** (t=3282s): Đã phát lại được — nhưng khung hình là **quảng cáo cờ bạc `9922.com` chèn trong nguồn phim** (`BIG WIN 812.46`, thần tài, tiền vàng). Nội dung của stream lậu, không phải UI app, nhưng nó hiện trên màn hình người dùng. `15:04 / 57:10`.
- **step_101** (t=3381s): `16:45 / 55:29`. **Phụ đề `Ông ta chỉ chịu các đầu bếp theo mình` đè lên đúng vị trí thanh seek bar** — xem crop phóng to ở mục C: chữ phụ đề to, nằm xuyên qua vạch seek (vạch đỏ + núm đi xuyên qua chữ), nửa dưới của phụ đề bị hàng nút dưới che mất. **Fix 4b THẤT BẠI trên màn hình** (xem mục D).
- **step_102** (t=3502s): `18:43 / 53:31`, không phụ đề. Hàng nút đầy đủ chiều dọc.
- **step_103** (t=3567s): **Lỗi decoding lần 4** — dialog ở `19:10 / 53:04`, `THỬ LẠI` focus viền trắng. Đây là finding DUY NHẤT judge liệt kê — dialog đúng như judge mô tả (3 nút `THỬ LẠI / QUAY LẠI / BÁO LỖI`).
- **step_104, 105, 106** (t=3635–3749s): **Cùng một dialog lỗi, cùng một khung hình đứng yên `19:10 / 53:04`** — step_105 và step_106 có **cùng sha256** (ảnh giống hệt nhau). AI bấm DPAD_DOWN ×3 rồi OK mà dialog vẫn còn đó; ở step_104–106 nút `THỬ LẠI` **mất viền trắng** (focus NONE theo timeline — focus đã rời khỏi dialog mà dialog không đóng). Đây là cùng 1 lần lỗi với step_103 (không phải 4 lần riêng).
- **step_107** (t=3866s): Đã phát lại được — toàn màn hình video, không OSD, không phụ đề. Hồi phục sau lỗi lần 4.
- **step_108** (t=3969s): **ẢNH QUAN TRỌNG NHẤT CHO FIX 4a — VOD khi ĐANG PHÁT** (nút đầu là `TẠM DỪNG`, focus viền trắng), `22:38 / 49:35`. Hàng nút **hiện đầy đủ theo chiều dọc** (không bị cắt nửa dưới như run trước) — NHƯNG: **nút đầu `TẠM DỪNG` bị cắt ở mép trái** (chữ `T` mất một nửa, viền focus cũng bị cắt — xem crop phóng to), và **nút cuối chỉ còn `T`** ở mép phải. Khi phát, hàng nút bị đẩy sang phải: cắt cả 2 đầu. Nút Speed vẫn không nhìn thấy, không tới được.
- **step_109** (t=4040s) và **step_110** (t=4101s): 2 ảnh **giống hệt nhau** (cùng sha256) — tạm dừng `22:47 / 49:27`, `PHÁT` focus, hàng nút đầy đủ chiều dọc, nút cuối `TỐ`.
- **step_111** (t=4204s): Đang phát lần 2 — `TẠM DỪNG` focus, `24:22 / 47:52`, **nút đầu lại bị cắt trái, nút cuối chỉ còn `T`** (khẳng định lại quy luật ở step_108, không phải ảnh chụp lỗi 1 lần).
- **step_112** (t=4324s): Đang phát, `TẠM DỪNG` focus, `26:23 / 45:51`. **Phụ đề lại đè lên seek bar** — dòng `Ta gọi hồ lớn về mạng lên` nằm ngay trên vạch seek, nửa dưới bị hàng nút che (bằng chứng thứ 2 cho Fix 4b).
- **step_113** (t=4402s) và **step_114** (t=4460s): 2 ảnh **giống hệt nhau** (= ảnh mission 15) — tạm dừng `26:31 / 45:43`, `PHÁT` focus. BACK ở step_114 chưa thoát khỏi player (ảnh không đổi); phải tới step_115 (BACK lần 2) mới về được màn hình chính (theo timeline).

#### MISSION_SEARCH_AND_SETTINGS + CHAOS — steps 116, 124, 129
- **step_116** (t=4492s): = ảnh mission 14 (chi tiết phim, `TIẾP TỤC XEM — 1 phim`).
- **step_124** (t=4595s): Tìm kiếm — `24 trận đang live`, chip thể loại, kết quả `Club Leon vs Guadalajara — BLV TAP +5 BLV · 380,5K · 6 phòng`, `Clippers vs Pelicans — BRIAN +1 BLV · 56,0K · 2 phòng`. Sạch.
- **step_129** (t=4660s): Cuối phiên — Tìm kiếm, focus viền trắng ở chip `Ngoại Hạng Anh`. App ổn định sau chaos, không crash.

### B.2 Chưa xem trực tiếp từng ảnh (68 ảnh — mô tả theo timeline)

Các ảnh dưới đây **không được mở xem bằng mắt**; nội dung suy ra từ `qa_session.json` (activity, focus node, motion, thời gian).

- **step_002** (t=44s): MainActivity, focus ở vùng `Phim đang trending` (đang cuộn Home sau khi đóng dialog).
- **step_004** (t=71s): OK trên card `Club Leon vs Guadalajara, TRỰC TIẾP` — mở dialog chọn phòng (dẫn tới step_005).
- **step_009–013** (t=286–354s): BACK khỏi player (2 lần, có dialog `Ở LẠI`), `SWITCH_TAB 0`, DPAD qua `heroPlay`/`heroDetails` trên Home. Không có player mới.
- **step_014–019** (t=354–460s): DPAD_DOWN qua các card Home rồi BACK; mở lại dialog chọn phòng Club Leon (steps 16–19 là dialog, focus qua các hàng phòng).
- **step_020–026** (t=460–553s): BACK, DPAD qua rail thể thao (`Alianza`, `Piratas`), DPAD_UP/DOWN, OK trên card Piratas — mở player trận Piratas (dẫn tới step_027).
- **step_029** (t=824s): PlayerActivity trận Piratas, DPAD_DOWN sau khi bấm MENU (dẫn tới overlay đổi trận ở step_030).
- **step_033** (t=1156s): PlayerActivity trận Club Leon, BACK (dẫn tới dialog `Ở LẠI` ở step_034).
- **step_034–041** (t=1170–1263s): dialog `Ở LẠI`, BACK về Home, DPAD_LEFT ×6 qua rail (focus qua `Piratas` → `Alianza` → `Club Leon` → `Khaan 12:00`), `SWITCH_TAB 6` (Home Hub). Không có màn hình Hub riêng biệt nào được mở (chỉ chuyển tab).
- **step_049** (t=1707s): PlayerActivity trận Piratas, BACK (OSD vẫn hiện ở step_048, tắt ở step_050).
- **step_053** (t=1770s): DPAD_LEFT thứ 3 ở Schedule, focus vẫn `schedCard` Piratas (tiền đề rail).
- **step_055** (t=1796s): `SWITCH_TAB 2` (IPTV).
- **step_057–061** (t=1827–1882s): IPTV: DPAD qua `btnHeroWatchFullscreen`/`Yêu thích`, OK, DPAD_LEFT/DOWN — di chuyển trong màn hình hero IPTV, không mở player, không mở M3U.
- **step_063–064** (t=1936–1947s): DPAD_DOWN rồi OK ở IPTV (focus `Yêu thích`/`btnHeroWatchFullscreen`) — vẫn ở màn hình hero.
- **step_066–068** (t=1980–2002s): DPAD_UP qua các pill IPTV (`Yêu thích` → `Tìm kênh TV...` → `Tất cả`) — di chuyển lên ô tìm kiếm (dẫn tới step_069/070).
- **step_072** (t=2075s): `SWITCH_TAB 5` (Kho Phim).
- **step_074** (t=2101s): DPAD_DOWN, focus `Về trang chủ` (nút back tròn ở chi tiết phim — khớp với lỗi back che chữ `C`).
- **step_076–077** (t=2125–2136s): DPAD_UP/RIGHT ở chi tiết phim, focus qua `XEM NGAY` → `CHỌN TẬP`.
- **step_079–083** (t=2162–2207s): dialog chọn tập: focus qua `Tập 1` → `Tập 5`, rồi DPAD_LEFT về `ĐÓNG`. (Không xem ảnh nên không xác nhận được pill tập có bị cắt ở các step này không — chỉ có step_084 đã xem.)
- **step_085–086** (t=2238–2251s): BACK đóng dialog chọn tập, DPAD_LEFT về `XEM NGAY` (dẫn tới step_087/088 mở VOD player).
- **step_094** (t=2835s): MainActivity, BACK khỏi player lần 2 sau lỗi lần 2 (về chi tiết phim).
- **step_096** (t=2857s): OK trên `XEM NGAY` — mở lại VOD player lần 2 (dẫn tới step_097, mission 15).
- **step_115** (t=4474s): PlayerActivity, BACK lần 2 — thoát player về MainActivity (step_116).
- **step_117–123** (t=4503–4583s): ở chi tiết phim rồi đi lên nav: focus qua `CHỌN TẬP` → `Về trang chủ` → `nav_live` → `nav_iptv` → `nav_phim` → `nav_schedule` → `nav_search`, OK mở Tìm kiếm.
- **step_125–128** (t=4606–4651s): Tìm kiếm: DPAD qua các chip `Phim Mới` → `Hoạt Hình` → `MEX D1` → `Bóng Rổ NBA` → `Ngoại Hạng Anh` (focus di chuyển được, có ring — app hồi phục sau chaos).

---

## C. Video

### full_qa_tour.mp4 — CHỈ LÀ ĐOẠN CUỐI PHIÊN, không phải tour toàn phiên
- `full_qa_tour.mp4`: **180,9 s**, 1280×720, H.264, 2,1 MB. Phiên thực 4669,5 s → video chỉ bằng **3,9% thời lượng thực**.
- Phát hiện quan trọng: **thời lượng của `full_qa_tour.mp4` (180,887 s) trùng khớp từng mili-giây với `chunk_26.mp4` (180,887 s)** — tức file "tour" thực chất **là chunk cuối cùng của bản ghi**, không phải bản tua nhanh toàn phiên. Đối chiếu khung hình: frame đầu tiên của tour (t=0s) đã là VOD tạm dừng `26:31 / 45:43` (= step_113/114, t≈4402s); frame cuối (t≈160s) là màn hình Tìm kiếm với focus ở nav `LỊCH TRÌNH` (= steps 119–122). **Tour chỉ bao phủ khoảng t≈4490–4669 s — 3 phút cuối của phiên 78 phút.** Nó KHÔNG hề quay lại Sport player, chuỗi lỗi decoding, Schedule, IPTV hay cold start.
- 9 frame trích (mỗi 20s):
  - **f_001 (t=0s), f_002 (t=20s), f_003 (t=40s):** cùng một khung VOD tạm dừng `26:31 / 45:43` (= step_113) — video đứng yên ở frame này trong ~60s đầu (do video đang phát lại đoạn pause, hoặc do chunk ghi lại trạng thái đứng yên).
  - **f_004 (t=60s):** VOD đang phát toàn màn hình, **không OSD**, phụ đề `Chúng ta sẽ cho thấy` nằm **đúng vị trí chuẩn ở mép dưới màn hình** (không bị che). Đây là đối chứng quan trọng: khi OSD tắt thì phụ đề nằm đúng chỗ; chỉ khi OSD mở thì phụ đề mới bị đè lên seek bar (steps 101, 112).
  - **f_005 (t=80s):** Chi tiết phim, `XEM NGAY` focus, hàng `TIẾP TỤC XEM — 1 phim`. Back che chữ `C` của `Cuộc…` thấy rõ.
  - **f_006 (t=100s):** Chi tiết phim, **nút back tròn đang được focus** (viền trắng quanh vòng tròn) — lúc này tiêu đề đọc thành `uộc Chiến Ẩm Thực` vì chữ `C` bị nút back che hoàn toàn.
  - **f_007 (t=120s):** Chi tiết phim (khung giống f_005).
  - **f_008 (t=140s):** Chi tiết phim, focus ở nav `TRUYỀN HÌNH` (viền trắng) trong khi tab đang chọn là `KHO PHIM`.
  - **f_009 (t=160s):** Chi tiết phim, focus ở nav `LỊCH TRÌNH`.
- **Kết luận video:** tour không dùng được để xác nhận Sport OSD hay VOD OSD "trong chuyển động" — nó chỉ quay lại 3 phút cuối (VOD tạm dừng + chi tiết phim + Tìm kiếm). Muốn xem lại toàn phiên phải nối các chunk 01–26 theo `concat.txt` (mỗi chunk ~175s, tổng ≈ 4550s). **chunk_27.mp4 bị hỏng** (`moov atom not found`, ffprobe không đọc được — file 351KB, có thể là phần ghi dở cuối phiên).

### qa_timelapse.mp4 (18,5 s) và raw_full.mp4 (18,3 s)
- `qa_timelapse.mp4`: frame đầu tiên cũng là VOD `26:31 / 45:43` — tức timelapse cũng chỉ tua nhanh **đoạn cuối** (chunk_26), không phải timelapse toàn phiên. Giá trị xem lướt gần như bằng 0.
- `raw_full.mp4`: frame đầu tiên là **launcher Android TV** (`Search movies, TV, and more`, `Apps`, đồng hồ `2:37`) — tức file này ghi từ đầu phiên (giống frame đầu chunk_01), nhưng chỉ dài 18,3s nên cũng không bao quát được gì.

---

## D. Verdict từng fix (nghiêm ngặt, kèm bằng chứng)

| Fix | Kết quả | Bằng chứng |
|---|---|---|
| **Fix 1 — Tỉ số ảo** | ✅ **XÁC NHẬN (trên màn hình)** | Không có tỉ số bóng đá nào vượt quy tắc (mỗi bên ≤ 9, tổng ≤ 12) trong tất cả ảnh đã xem. Mọi card live đều hiện `VS` (ảnh 01, 03, 05, 07; steps 003, 042; step_030). Hero `Albirex VS Tokushima` (ảnh 01). Không thấy tỉ số `2:8`/`4:12`/`13:8` nào. **Chưa kiểm được:** (a) định dạng `M` (`6,8M`) — lượt xem cao nhất thấy trong run là `380,5K` (step_124/129), không có lượt xem nào ≥ 1M xuất hiện nên không có mẫu để xem; (b) bóng rổ không được kiểm (không có trận NBA nào được mở — chỉ thấy tên trên Search). **Lưu ý:** pill Sport ẩn cả tỉ số HỢP LỆ (0-0, 1-1) — xem mục F, không tính là lỗi Fix 1 nhưng là vấn đề dữ liệu riêng. |
| **Fix 2 — Sport Player OSD** | ✅ **XÁC NHẬN (vẫn đúng trên màn hình)** | Mọi ảnh Sport OSD (steps 006, 007, 027, 028, 031, 032, 045–048; ảnh 02, 06, 08): top bar chỉ còn `◀ QUAY LẠI` + pill (không còn hàng 6–7 nút); scrim trên đọc được; **focus viền trắng rõ trên nút `▶ PHÁT` giữa màn hình**; bar dưới rõ trên nền kính (`KÊNH TIẾNG | 00:00 | ● TRỰC TIẾP | TÙY CHỌN | TỈ LỆ`). **Thay đổi so với run trước:** run trước (step_044) giữa màn hình có `TUA -30S / PHÁT / TUA +30S`; run này **không còn nút ±30s nào** trong bất kỳ ảnh Sport OSD nào — chỉ có `▶ PHÁT` đứng một mình. Nếu đây là support-gate cố ý ẩn (cửa sổ seek < 30s) thì là đúng thiết kế; nếu không thì là regression — cần xác nhận từ code, không kết luận được từ ảnh. |
| **Fix 3 — VOD Player** | ⚠️ **MỘT NỬA: native VOD giữ nguyên, WebPlayer CHƯA BAO GIỜ tới (lần thứ 2 liên tiếp)** | **Đã tới:** VOD native steps 88–93, 97–113 — tiêu đề 1 dòng căn giữa ✅; không có nút PIP ✅; thanh trượt dọc trái ✅; seek bar đầy đủ ✅; focus thấy rõ trên `PHÁT`/`TẠM DỪNG`/`THỬ LẠI` ✅. **Chưa đạt mẫu `player-sample-vod.jpg`:** không có cụm pause/±10s ở giữa màn hình; không thấy `SKIP INTRO`; không thấy nút `Lock`; hàng nút dưới là `PHÁT / TUA -10S / TUA +10S / TẬP TRƯỚC / TẬP TIẾP / CHỌN TẬP / ÂM THANH & PHỤ ĐỀ / TỐ…` (không giống mẫu `Speed (1x) / Lock / Episodes / Audio & Subtitles / Next Ep.`). **Chưa tới:** trong 129 step, activity chỉ có `MainActivity` (88) và `PlayerActivity` (41) — **không có `WebPlayerActivity` lần nào**. Check 13 tên "Trình Phát Web (WebPlayerActivity)" nhưng 10 step của nó (86–95) toàn mở **native player bằng `XEM NGAY`**. Gate Speed bằng JS probe, EPG bar/Mini-Guide, subtitle anchor (trừ 2 bằng chứng ở steps 101/112) vẫn **chưa được kiểm trên màn hình**. Không có settings dialog nào được mở (mission 15 chỉ phát lại phim). |
| **Fix 4a — Hàng nút dưới VOD hiện đầy đủ khi tạm dừng VÀ khi phát** | ⚠️ **MỘT NỬA: chiều dọc đã sửa, chiều ngang vẫn hỏng** | **Chiều dọc — ĐÃ SỬA:** hàng nút hiện đầy đủ theo chiều dọc ở cả 2 trạng thái: tạm dừng (steps 088–090, 092, 097, 098, 102, 109, 110, 113; ảnh 15) và đang phát (steps 108, 111, 112) — không còn cảnh "cắt nửa dưới" như run trước. Margin 8dp có tác dụng. **Chiều ngang — CHƯA SỬA:** nút cuối **lúc nào cũng chỉ còn `TỐ` khi tạm dừng và `T` khi đang phát** (mọi ảnh VOD OSD); tệ hơn, **khi đang phát nút ĐẦU `TẠM DỪNG` còn bị cắt ở mép trái** (steps 108, 111, 112 — crop phóng to cho thấy chữ `T` mất một nửa, viền focus cũng bị cắt). Hàng nút bị đẩy sang phải khi nút đầu đổi từ `PHÁT` sang `TẠM DỪNG` — đúng cơ chế đã mô tả trong Fix 4 (rộng thêm ~21px), nhưng việc "hàng cuộn được" **không thể hiện trên màn hình**: không có ảnh nào cho thấy hàng đã cuộn hay nút Speed hiện đầy đủ. |
| **Fix 4b — Phụ đề neo trên seek bar khi OSD mở** | ❌ **KHÔNG XÁC NHẬN — bằng chứng trên màn hình cho thấy vẫn hỏng** | **step_101:** phụ đề `Ông ta chỉ chịu các đầu bếp theo mình` nằm xuyên qua vạch seek bar (vạch đỏ + núm đi xuyên qua chữ), nửa dưới bị hàng nút che (crop phóng to `/tmp/vodbot_step_101_mission_.png`). **step_112:** phụ đề `Ta gọi hồ lớn về mạng lên` cũng nằm ngay trên vạch seek, nửa dưới bị hàng nút che. Phụ đề KHÔNG nằm rõ trên seek bar khi OSD mở — nó vẫn ở vị trí cũ, va chạm với seek bar + hàng nút. Đối chứng: video frame f_004 (OSD tắt) phụ đề nằm đúng ở mép dưới. Kết luận: `anchorSubtitles()` 148dp **không có tác dụng nhìn thấy được** trong 2 lần phụ đề xuất hiện cùng OSD mở. |
| **Fix 4c — Nút Speed tới được (phần cuộn của 4a)** | ❌ **KHÔNG THẤY (NOT SEEN)** | Không có ảnh nào trong run cho thấy nút Speed/Tốc độ hiện đầy đủ hay được focus. Mọi ảnh VOD OSD đều chỉ thấy `TỐ` (tạm dừng) hoặc `T` (đang phát) ở mép phải. Không có step nào di chuyển focus tới cuối hàng nút (focus xa nhất về phải trong các ảnh VOD là `TUA -10S` ở step_090). |
| **Fix 4d — Pill Sport hiện phút/hiệp khi feed không có đồng hồ** | ⚠️ **MỘT NỬA: có phút ở 1 trận, không có ở trận còn lại** | **Có phút:** trận Piratas vs Cancun — pill `Hiệp 2: 90+' · PIR - CAN` (steps 045, 046, 047, 048; ảnh 08). **Không có phút:** trận Club Leon vs Guadalajara — pill `CLU - CLU` ở MỌI ảnh (steps 006, 007, 031, 032; ảnh 02, 06), dù bug đài ở step_008 chứng minh trận đang ở phút **29:44**. Cùng một cơ chế fallback mà 1 trận có, 1 trận không — không nhất quán. **Thêm 2 vấn đề pill:** (1) mã đội trùng nhau `CLU - CLU` cho 2 đội khác nhau (đài dùng `LEO`/`GDL`); (2) pill ẩn tỉ số ngay cả khi tỉ số hợp lệ (`PIR 1-1`, `LEO 0-0` — đều mỗi bên ≤ 9, tổng ≤ 12). Bóng rổ: không có trận NBA nào được mở nên **không kiểm** (và theo hướng dẫn thì cũng không được tính là lỗi nếu pill NBA không có phút). |
| **Fix 4e — Bar live Sport fallback sang bar đỏ 100% khi cửa sổ seek < 30s** | ⚠️ **MỘT NỬA: bar seek 6s đã hết, nhưng không thấy bar đỏ** | **Đã hết:** không còn thấy thanh seek trắng `00:00 / 00:06` có núm như run trước (step_044 cũ) trong bất kỳ ảnh Sport OSD nào — chỉ còn `00:00` và `● TRỰC TIẾP` (+ `Về trực tiếp` lúc có lúc không). **Chưa thấy bar đỏ:** đã phóng to crop thanh bar dưới của steps 006/027/045/046 và quét pixel đỏ — không có vạch đỏ ngang full-width nào; pixel đỏ ở đó là chữ quảng cáo `BUFA` của stream phía sau lớp kính. Có thể bar đỏ quá mỏng để thấy ở 960×540, nhưng bar trắng cũ thì thấy rõ ở cùng độ phân giải, nên kết luận: **không xác nhận được bar đỏ 100% hiển thị trên màn hình**. |

---

## E. Chấm finding duy nhất của judge (step 103)

| Finding (judge) | Phán quyết | Bằng chứng |
|---|---|---|
| LOW step 103: `ERROR_CODE_DECODING_FAILED` khi phát video native trên PlayerActivity; "có thể là giới hạn emulator x86"; dialog hiển thị đúng 3 tùy chọn `THỬ LẠI / QUAY LẠI / BÁO LỖI` | **THẬT — nhưng judge đếm thiếu: đây chỉ là 1 trong 4 lần xuất hiện** | **step_103 đúng như mô tả:** dialog `Lỗi Phát Luồng Video — Stream lỗi: ERROR_CODE_DECODING_FAILED`, `THỬ LẠI` có viền trắng (focus), `19:10 / 53:04`. **Nhưng cùng dialog còn xuất hiện ở:** **step_091** (lần 1, `06:01 / 1:06:13`), **step_093** (lần 2, khung hình khác), **step_099** (lần 3, `13:37 / 58:37`), và **steps 104–106** (cùng lần 4 với step_103, khung hình đứng yên `19:10 / 53:04`). Tổng cộng **7 ảnh step có dialog lỗi, thuộc 4 lần riêng biệt**. |

**Phân tích pattern:**
- **Hồi phục sau mọi lần:** lần 1 → step_092 phát lại được; lần 2 → AI BACK về chi tiết phim rồi mở lại, step_097 phát được; lần 3 → step_100 phát lại được (OK trên `THỬ LẠI` ở step_099); lần 4 → step_107/108 phát lại được (OK ở step_106). Không lần nào làm chết app hay kẹt vĩnh viễn.
- **Tần suất:** lỗi tái diễn đều đặn trong suốt 26 phút xem VOD (từ 06:01 đến 19:10 vị trí phim), trung bình ~4–5 phút/lần. Đây là **pattern, không phải sự cố 1 lần**.
- **Môi trường hay app?** Giả thuyết emulator x86 thiếu codec là hợp lý một phần (lỗi chỉ xảy ra với VOD phim, không xảy ra với Sport player trong cùng phiên — các step Sport 6–8, 27–33, 45–50 đều phát tốt). Nhưng **4 lần trên cùng 1 tập phim trong 1 phiên** thì không thể gọi là "1 lỗi môi trường" cho xong — cần kiểm trên thiết bị thật trước khi kết luận. Mức LOW cho từng lần là hợp lý, nhưng pattern tổng thể đáng chú ý hơn điểm số thể hiện.
- **Điểm trừ thêm cho judge:** ở steps 104–106, sau khi bấm DPAD_DOWN ×3, focus **rời khỏi dialog** (mất viền trắng ở `THỬ LẠI`) mà dialog vẫn hiện — AI phải bấm OK "mù" ở step_106 mới thoát. Đây là một khiếm khuyết focus nhỏ trong dialog lỗi mà judge không nhắc tới.
- **Kết luận:** finding là THẬT, mô tả đúng, nhưng **đếm thiếu 3/4 lần xuất hiện**. Nếu tính đúng thì run này có 4 lần decoding failed, không phải 1.

---

## F. Các lỗi khác nhìn thấy bằng mắt (ngoài finding)

### F.1 Lỗi mới / lỗi Fix 4 chưa sửa xong
1. **(MỚI, từ Fix 4a) Hàng nút VOD khi đang phát bị cắt cả 2 đầu** — steps 108, 111, 112: nút đầu `TẠM DỪNG` cắt trái, nút cuối chỉ còn `T`. Khi tạm dừng thì nút đầu hiện đủ, nút cuối `TỐ`. Hàng nút vẫn không vừa màn hình ở cả 2 trạng thái; nút Speed không bao giờ hiện đầy đủ.
2. **(MỚI, từ Fix 4b) Phụ đề đè lên seek bar khi OSD VOD mở** — steps 101, 112 (xem mục D, Fix 4b). Lỗi đã thấy ở run trước (step_107 cũ) vẫn còn nguyên.
3. **(MỚI, chẩn đoán chính xác) Nhãn "tổng thời lượng" VOD thực ra là thời gian CÒN LẠI** — kiểm chứng bằng số: ở mọi ảnh VOD OSD, **vị trí + số bên phải = 01:12:14 không đổi**: `01:42+1:10:32`, `03:23+1:08:51`, `05:01+1:07:13`, `06:01+1:06:13`, `07:40+1:04:34`, `10:18+1:01:56`, `12:28+59:46`, `13:37+58:37`, `15:04+57:10`, `16:45+55:29`, `18:43+53:31`, `19:10+53:04`, `22:38+49:35`, `22:47+49:27`, `24:22+47:52`, `26:23+45:51`, `26:31+45:43` (chênh 1s do làm tròn ở 22:38). Tổng thật của tập là `01:12:14` (khớp chip resume `03:31/01:12:14` ở run trước). Đây KHÔNG phải "tổng thời lượng nhảy lung tung do đổi server" như run trước đoán — mà là **nhãn bên phải đang hiển thị thời gian còn lại** (hoặc duration đang bị tính bằng `tổng − vị trí`). Resume/seek dựa trên con số này sẽ sai.
4. **(MỚI) Pill Sport: mã đội trùng `CLU - CLU`, phút không nhất quán, ẩn tỉ số hợp lệ** — xem mục D, Fix 4d. Đặc biệt: bug đài ở step_008 cho thấy `LEO 0-0 GDL 29:44` trong khi pill app chỉ có `CLU - CLU` (không tỉ số, không phút) — trên cùng màn hình, 2 nguồn thông tin mâu thuẫn nhau về cùng một trận.

### F.2 Lỗi cũ từ run trước — đối chiếu
| Lỗi run trước | Trạng thái run này |
|---|---|
| Schedule hàng đầu bị cắt nửa trên dưới nav | ✅ **ĐÃ HẾT** — step_043/051/052/054 + ảnh 09: hàng đầu hiện đầy đủ |
| Chi tiết phim: back che chữ `C` của tiêu đề | ❌ **VẪN CÒN** — mọi ảnh chi tiết phim (12, 13, 14, 16, 17; steps 073, 075, 078, 087, 095, 116) + video f_005/f_006 (khi back được focus thì tiêu đề đọc thành `uộc Chiến Ẩm Thực`) |
| Chữ mờ `…ĐẶC SẮC` bị cắt sau thanh nav ở chi tiết phim | ❌ **VẪN CÒN** — mọi ảnh chi tiết phim |
| M3U keyboard trap | ⚪ **KHÔNG KIỂM ĐƯỢC** — AI không mở dialog M3U lần nào trong run này (steps 55–71 không có M3U) |
| Rail không mở | ❌ **VẪN CÒN** — steps 51–54, focus đứng yên, ảnh giống hệt nhau; **judge không liệt kê** |
| Decoding errors ×4 lần | ❌ **VẪN CÒN, vẫn 4 lần** — steps 91, 93, 99, 103–106 (judge chỉ liệt kê 1) |
| VOD tổng thời lượng nhảy 12 giá trị | 🔍 **ĐÃ CHẨN ĐOÁN ĐƯỢC GỐC** — không phải nhảy lung tung: số bên phải là thời gian còn lại (vị trí + số phải = 01:12:14 hằng số). Vẫn là lỗi hiển thị, nhưng nguyên nhân đã rõ |
| Phòng NBA `0 lượt xem` vs card `127,0K` | ❌ **VẪN CÒN, nay ở bóng đá** — step_044: 4 phòng Piratas đều `0 lượt xem` vs card `121,9K xem`. Ngược lại step_005: phòng Club Leon có lượt xem thật (75,6K…) — lỗi theo từng trận, không phải toàn bộ |
| IPTV chữ đè lên logo ANTV | ⚪ **KHÔNG KIỂM ĐƯỢC** — player IPTV không được mở lần nào trong run này |
| Pill tỉ số lag so với bug đài | ❌ **VẪN CÒN, dạng mới** — pill không hiện tỉ số trong khi bug đài hiện `PIR 1-1` / `LEO 0-0` (xem F.1.4) |

### F.3 Lỗi/vấn đề khác thấy bằng mắt
5. **Nút `Về trực tiếp` ở Sport OSD lúc có lúc không** — có ở steps 007, 028, 030, 045–048; không có ở steps 006, 027, 031, 032. Cùng một trận, cùng một OSD, không thấy quy luật. (Có thể phụ thuộc thời điểm mở OSD — không kết luận được từ ảnh.)
6. **Không còn nút ±30s ở Sport OSD** — xem mục D, Fix 2. So với run trước (có `TUA -30S / PHÁT / TUA +30S` ở step_044 cũ) thì đây là thay đổi nhìn thấy được; cần xác nhận có phải gate cố ý không.
7. **Dialog chọn tập bố cục lộn xộn** — step_084: pill `Tập 6` rớt hàng đè lên poster; dòng `Không có mô tả chi tiết.` chạy xuyên dưới hàng pill tập (bị che một phần).
8. **Chuỗi Trung Quốc chưa dịch trong room picker** — `(最高等级)` sau tên BLV (steps 005, ảnh 04). Nhỏ nhưng lộ trên giao diện tiếng Việt.
9. **Quảng cáo cờ bạc chèn trong stream** — step_100: quảng cáo `9922.com BIG WIN 812.46` toàn màn hình trong lúc xem phim; step_008/050: banner `BUFA` dưới stream thể thao. Đây là nội dung của nguồn phát lậu, không phải lỗi UI của app — nhưng người dùng vẫn nhìn thấy nó, nên ghi nhận (không trừ điểm app).
10. **Focus ở nav `TRANG CHỦ` trong khi tab đang chọn là `KHO PHIM`** — step_073, video f_008 (focus ở `TRUYỀN HÌNH`/`LỊCH TRÌNH` trong khi đang ở màn hình chi tiết phim). Focus di chuyển được nhưng vị trí ban đầu khó hiểu.
11. **Thoát player cần 2 lần BACK** — steps 113→114 (ảnh không đổi sau BACK lần 1), 114→115 mới thoát; tương tự steps 32→33→34 ở Sport player có dialog `Ở LẠI` xen giữa. Không phải lỗi, nhưng đáng ghi nhận (run trước D15 cũng ghi BACK VOD thành 2 lần bấm).

---

## G. Điểm 98/100 — có công bằng không?

**Không công bằng — 98/100 quá cao so với những gì nhìn thấy trên màn hình.** Phân tích:

- **Judge bỏ sót lỗi thật:** rail không mở (MEDIUM, đã xác nhận bằng ảnh ở run trước và lặp lại ở run này) không được liệt kê; 3/4 lần decoding failed không được liệt kê; hàng nút VOD cắt 2 đầu khi phát, phụ đề đè seek bar, pill `CLU - CLU` + phút không nhất quán, nhãn thời lượng còn lại — tất cả đều không có trong findings.
- **Judge chấm 16/16 checks và 16/16 missions đều PASS**, nhưng nhiều check "pass" trên danh nghĩa mission tên gọi chứ không phải nội dung thực: check 13 "WebPlayer" pass trong khi WebPlayer chưa bao giờ được mở; check 15 "Settings Dialog" pass trong khi không có settings dialog nào; check 10 "Zapping Player" pass trong khi player IPTV chưa bao giờ được mở; check 16 "Tìm kiếm & Cài đặt" pass trong khi Cài đặt chưa bao giờ được vào.
- **Điểm mù bao phủ:** Live 0 thao tác, Search 0 thao tác gõ (chỉ lướt chip), Settings 0, IPTV chỉ 1 thao tác, Schedule chỉ 1 — 66/129 step dồn vào Kho Phim. Điểm 98 dựa trên một phiên lệch hẳn về Phim.
- **Nhưng 98 không phải hoàn toàn vô căn cứ:** Fix 1 và Fix 2 giữ vững trên màn hình; Schedule đã sửa được hàng đầu; video phát được ở hầu hết các step player; không crash sau chaos; điều hướng, focus, palette, tìm kiếm, yêu thích kênh, chọn tập, resume đều chạy tốt.

**Ước tính sau khi khử artifact (de-artifacted): ~70/100 (khoảng 68–72).** Cách tính (xuất phát 100):
- Rail không mở (MEDIUM, lặp lại 2 run, judge bỏ sót): −6
- Decoding failed tái diễn 4 lần / 1 phiên VOD (pattern, cần kiểm thiết bị thật): −6
- Hàng nút VOD khi phát cắt 2 đầu, Speed không tới được (Fix 4a chưa xong): −5
- Phụ đề đè seek bar khi OSD mở (Fix 4b thất bại, 2 bằng chứng): −4
- Pill Sport: phút không nhất quán + mã đội trùng + ẩn tỉ số hợp lệ (Fix 4d một nửa): −4
- Nhãn thời lượng VOD hiển thị thời gian còn lại thay vì tổng: −3
- Phòng 0 lượt xem vs card 121,9K: −2
- Chi tiết phim: back che chữ `C` + chữ mờ sau nav (lặp lại nhiều run): −2
- Tổng trừ: −32 → **~68**, làm tròn lên **~70** vì phần còn lại (điều hướng, phát video, focus, palette, resume, tìm kiếm, EPG IPTV) chạy tốt và 2/4 fix chính đã xác nhận.
- Con số này là ước tính của người review, không phải điểm đo được. Điểm mù (WebPlayer, M3U, IPTV player, Settings chưa được kiểm lại) không trừ vào điểm chất lượng nhưng làm giảm độ tin cậy của bất kỳ điểm số nào cho run này.

---

## H. Trả lời thẳng các câu hỏi kiểm chứng

- **WebPlayerActivity có được tới không? KHÔNG.** Timeline 129 step chỉ có 2 activity: `MainActivity` (88 step) và `PlayerActivity` (41 step). Check 13 "Trình Phát Web (WebPlayerActivity), Tua D-pad JS & Hàng Tiếp Tục Xem" (10 step, steps 86–95) thực tế mở **native PlayerActivity bằng nút `XEM NGAY`** (step_088). Không có bước nào mở WebView/WebPlayer, không có tua JS nào được kiểm. Đây là lần thứ 2 liên tiếp mission tên "WebPlayer" nhưng AI mở native player.
- **Sport player có được tới không? CÓ** — steps 6, 7, 8 (Club Leon), 27, 28, 30, 31, 32, 33 (Piratas + Club Leon), 45, 46, 47, 48, 49, 50 (Piratas). Tất cả đều là `PlayerActivity` với OSD Sport (back + pill, nút PHÁT giữa, bar dưới).
- **VOD player có được tới không? CÓ** — steps 88–93 và 97–113, `PlayerActivity` native, phim `Cuộc Chiến Ẩm Thực - Tập 01`. Trạng thái tạm dừng (nút `PHÁT`) thấy ở steps 88–90, 92, 97, 98, 102, 109, 110, 113, 114; trạng thái đang phát (nút `TẠM DỪNG`) thấy ở steps 108, 111, 112; dialog lỗi decoding thấy ở steps 91, 93, 99, 103–106.
- **IPTV player có được tới không? KHÔNG** — AI chỉ ở màn hình hero IPTV (steps 56–71), không bấm `XEM TOÀN MÀN HÌNH` lần nào.
- **Màn hình Cài đặt có được tới không? KHÔNG** — 0 thao tác ở tab Settings trong cả phiên.
- **Dialog M3U có được mở không? KHÔNG** — nên trap M3U của run trước không kiểm lại được.
- **Dialog cài đặt player (mission 15) có được mở không? KHÔNG** — mission 15 (steps 96–113) chỉ phát lại phim và gặp lỗi decoding; không có settings dialog nào trong bất kỳ ảnh nào.

# Đánh giá trực quan — QA run 42470778044 (KenhLive TV, main 9d37546)

- **Run:** CI 42470778044 (QA-Suite, quick) · **Commit:** `9d37546` trên main · **App:** KenhLive TV 0.1.12 (162)
- **Phiên:** `QA-SESS-20261108-102947-455fd4` · **Thời lượng phiên:** 1686,6s · **Điểm QA tự động:** 0/100 (16/16 check đều pass — điểm 0 đến hoàn toàn từ 20 finding Focus Loss HIGH)
- **Phạm vi đã xem:** 17 ảnh mission (`01`–`17`), 12 frame video (`vf_5s`–`vf_165s`, video 170s), 20 ảnh step tương ứng với 20 finding Focus Loss (`step_001`–`018`, `step_039`–`040`), và 4 ảnh step khu vực player (`step_025`–`028`). **Tổng cộng 53 ảnh/frame đã xem trực tiếp.**
- **Phương pháp:** chỉ ghi những gì nhìn thấy được trong ảnh. Không suy đoán mã nguồn, không đo mã hex từ ảnh nén (mã màu chính xác vẫn do `scripts/kl5_audit.py` 16/16 làm chuẩn).

---

## Phần 1 — 17 ảnh mission

### 01_cold_start.jpg — Màn hình chính, dialog THÔNG BÁO che giữa
- Màn hình home "ĐANG PHÁT" phía sau bị làm mờ, phía trước là dialog **THÔNG BÁO** (nhóm Telegram @kenhlivetv, mã QR).
- **Focus: KHÔNG thấy dấu focus nào** — không có viền trắng, không có nút nào nổi bật trong dialog.
- **Lỗi thấy được:**
  - Nội dung dialog tràn khỏi hộp: dòng cuối "…hoặc nhận file cập nhật **mới nhất**" bị cắt ngang ở mép dưới dialog.
  - Dialog không có nút đóng/OK nào nhìn thấy được — người dùng chỉ có thể bấm BACK (không có gợi ý trên màn hình).

### 02_mission_cold_start.jpg — Giống 01 (dialog vẫn mở)
- Y hệt 01, chỉ khác đồng hồ 17:29 → 17:30 và xuất hiện toast hệ thống **"Wi-Fi has no internet access"** góc trên phải.
- Focus: không thấy. Đây là bằng chứng mạng emulator lúc này chưa có internet (liên quan đến các lỗi tải nội dung ở ảnh 10, 12–14).
- Lỗi: như 01 (chữ dialog bị cắt, không có nút đóng).

### 03_mission_sports_multi_source.jpg — Giống 01/02 (dialog vẫn mở)
- Y hệt 01/02 (17:32). Dialog vẫn che màn hình sau nhiều lần bấm D-pad.
- Focus: không thấy. D-pad không làm thay đổi gì trên màn hình.

### 04_mission_sports_room_picker.jpg — Home ĐANG PHÁT, dialog đã tắt
- Dialog đã biến mất. Màn hình home: 3 thẻ trận (JPN D2, badge SOCO xanh ngọc, badge **LIVE đỏ**), nav dưới chỉ chữ: CÀI ĐẶT / BÁO LỖI TELEGRAM / LỊCH THI ĐẤU / TÌM KIẾM.
- **Focus: CÓ, nhưng nằm trên một ô trống** — hình chữ nhật viền trắng ở hàng dưới, bên trái, bên trong hoàn toàn trống (không chữ, không icon). Đây là thẻ Sports của HomeHub theo timeline (`cardSports`), nhưng render ra ô trống.
- **Lỗi thấy được:** 3 ô chữ nhật tối bên dưới hàng ĐANG PHÁT đều trống nội dung (không nhãn, không logo). Thẻ trận thứ 3 bị cắt ở mép phải (bình thường với cuộn ngang — không tính là lỗi).
- Không thấy cam #FF6500 hay cyan. Nền than ấm, badge LIVE đỏ, chữ "VS" vàng đồng.

### 05_mission_sports_data_accuracy.jpg — Lịch thi đấu, focus rõ
- Danh sách trận "Thứ Bảy, 03/10", 37 trận. **Focus rõ: viền trắng quanh hàng "Fujieda MYFC vs Shonan Bellmare".**
- **Lỗi thấy được:** các vòng tròn logo đội bóng hiển thị thành vòng tròn xám trống (logo không tải được); các trận "KẾT THÚC" không hiện tỉ số, chỉ có vòng tròn xám + "+2".
- Bố cục sạch, chữ tương phản tốt, không cam/cyan.

### 06_mission_player_streaming_and_controls.jpg — Home ĐANG PHÁT (sau khi thoát player)
- Giống 04: **focus vẫn nằm trên ô trống có viền trắng** ở hàng dưới bên trái; 3 ô dưới đều trống nội dung.
- Lỗi: như 04 (thẻ HomeHub trống).

### 07_mission_home_hub_3_cards_and_canva_logos.jpg — Home, focus ở nav TÌM KIẾM
- **Focus rõ: viền oval trắng quanh chữ "TÌM KIẾM"** ở nav dưới. Đây là minh chứng focus của nav hoạt động đúng thiết kế (text-only + pill outline).
- **Lỗi thấy được:** 3 ô HomeHub bên trên vẫn trống hoàn toàn (không có logo Canva nào như tên mission kỳ vọng).
- Không cam/cyan; badge LIVE đỏ, SOCO xanh ngọc (badge nguồn, không phải chrome UI).

### 08_mission_schedule_epg_and_fixture_tap.jpg — Lịch thi đấu, focus rõ
- **Focus rõ: viền trắng quanh hàng "Albirex Niigata vs Tokushima Vortis".**
- Lỗi: như 05 — logo đội là vòng tròn xám trống, trận KẾT THÚC không có tỉ số.

### 09_mission_sidebar_rail_full_traversal.jpg — Lịch thi đấu đã cuộn xuống, focus rõ
- **Focus rõ: viền trắng quanh hàng cuối "Matsumoto Yamaga FC vs Gainare Tottori".**
- Lỗi: như 05/08 (logo xám trống). Không có lỗi bố cục khác.

### 10_mission_iptv_categories_and_favorites.jpg — MÀN HÌNH ĐEN HOÀN TOÀN
- **Ảnh đen 100%, không có bất kỳ UI, chữ hay dấu focus nào.** Đây là màn hình chết (dead/blank screen) ở mission IPTV categories & favorites.
- Đây là lỗi thật, nghiêm trọng: người dùng bấm vào IPTV mà màn hình đen xì.
- Không thể xác định nguyên nhân từ ảnh (có thể activity IPTV render lỗi, surface đen, hoặc app kẹt sau lần bấm trước).

### 11_mission_iptv_epg_and_zapping_player.jpg — IPTV EPG, focus mờ
- Màn hình IPTV render được: hero "VTV2 HD", badge **TRỰC TIẾP đỏ** + FHD, chương trình đang phát / tiếp theo, lưới kênh VTV1–VTV4 HD phía dưới, pills thể loại (Yêu Thích, VTV đang chọn, TV360, HTV/VTC), ô tìm kênh, nút THÊM M3U.
...[truncated 15820 chars]- **Focus: MỜ/KHÔNG RÕ** — chỉ thấy một đường trắng dọc mỏng ở x≈40% màn hình (mép trái của thẻ đang focus, thẻ VTV1 HD), không thấy rõ thẻ nào đang được focus, không thấy thẻ phóng to.
- **Lỗi thấy được:** vùng hero trên cùng trống đen (không có ảnh nền/backdrop); hàng chữ cuối lưới kênh bị cắt ở mép dưới màn hình ("17:15 - Phim truyền…", "17:25 - Sao check: No…").
- Không cam/cyan. Ô logo "VTV 2" màu xanh lá là logo kênh (nội dung), không phải màu UI.

### 12_mission_phim_nguonc_and_categories.jpg — Lỗi tải kho phim
- Màn hình lỗi: **"Không thể tải kho phim / Kiểm tra kết nối mạng hoặc thử lại sau"**, nút **THỬ LẠI** đỏ có viền trắng.
- **Focus: CÓ** — nút THỬ LẠI có viền trắng rõ, đúng chuẩn focus (nút đỏ = primary action theo KL5).
- **Lỗi:** kho phim không tải được (lỗi mạng — khớp với toast "Wi-Fi has no internet access" ở step_002). Mission "kho phim + thể loại" thực tế chưa hề vào được kho phim.

### 13_mission_phim_episode_picker_and_favorite.jpg — Y hệt 12
- Ảnh giống hệt 12 (cùng sha256). Vẫn là màn hình lỗi "Không thể tải kho phim", nút THỬ LẠI có viền trắng.
- **Lỗi:** Episode Picker chưa bao giờ mở được — mission này không được test thật về mặt hình ảnh.

### 14_mission_vod_player_seek_and_resume.jpg — Y hệt 12/13
- Ảnh giống hệt 12/13 (cùng sha256). Vẫn màn hình lỗi kho phim.
- **Lỗi:** VOD player (seek/resume) chưa bao giờ mở được — mission này không được test thật về mặt hình ảnh.

### 15_mission_player_settings_dialog.jpg — Home ĐANG PHÁT, focus ở nav
- Giống 07: **focus rõ trên "TÌM KIẾM"** (viền oval trắng). 3 ô HomeHub bên dưới vẫn trống.
- Lưu ý: tên mission là "player settings dialog" nhưng ảnh cuối mission là màn hình home (sau DOUBLE_BACK) — dialog cài đặt player không xuất hiện trong ảnh này.
- Lỗi: như 07 (thẻ HomeHub trống).

### 16_mission_search_and_settings_feedback.jpg — Cài đặt, focus rõ
- Màn hình Cài đặt: mục "Hình ảnh & âm thanh" (Chất lượng hình: Tự động; Chế độ âm thanh: Tự động (Hay)), mục "Ứng dụng" (Liên hệ & Báo lỗi — Nhóm Telegram: @kenhlivetv; Xóa bộ nhớ đệm ảnh; Phiên bản 0.1.12).
- **Focus rõ: viền trắng quanh hàng "Chất lượng hình".**
- Bố cục sạch, tương phản tốt. Tiêu đề mục có vạch vàng đồng nhỏ bên trái (accent brass theo KL5). Không cam/cyan, không gradient, không glow.

### 17_mission_dpad_chaos_stress_and_recovery.jpg — Y hệt 16
- Ảnh giống hệt 16 (cùng sha256): vẫn màn hình Cài đặt, focus ở "Chất lượng hình".
- **Nhận xét:** sau chuỗi D-pad chaos, app vẫn ở màn hình Cài đặt và giữ focus ổn định — không crash, không mất focus (đây là bằng chứng recovery tốt).
- Lỗi: không có lỗi mới; chỉ lưu ý mission "chaos stress" kết thúc ở cùng một màn hình với mission 16 (không có gì khác để xem).

---

## Phần 2 — 12 frame video (`full_qa_tour.mp4`, 170s, 1280×720)

| Frame | Đồng hồ trong video | Nội dung |
|---|---|---|
| vf_5s | 17:29 | Dialog THÔNG BÁO |
| vf_15s | 17:29 | Dialog THÔNG BÁO |
| vf_30s | 17:30 | Dialog THÔNG BÁO |
| vf_45s | 17:30 | Dialog THÔNG BÁO |
| vf_60s | 17:30 | Dialog THÔNG BÁO |
| vf_75s | 17:31 | Dialog THÔNG BÁO |
| vf_90s | 17:31 | Dialog THÔNG BÁO |
| vf_105s | 17:31 | Dialog THÔNG BÁO |
| vf_120s | 17:31 | Dialog THÔNG BÁO |
| vf_135s | 17:31 | Dialog THÔNG BÁO |
| vf_150s | 17:32 | Dialog THÔNG BÁO |
| vf_165s | 17:32 | Dialog THÔNG BÁO |

- **Cả 12 frame đều là cùng một màn hình: dialog THÔNG BÁO Telegram che giữa màn hình home ĐANG PHÁT.** Đồng hồ chạy 17:29 → 17:32 nên video là bản ghi thật (không phải ảnh tĩnh bị kẹt), nhưng **màn hình không hề thay đổi trong suốt 170 giây**.
- **Không có frame nào đen/trống, không có spinner loading, focus không xuất hiện ở bất kỳ frame nào.**
- **Giới hạn quan trọng:** video chỉ dài 170s trong khi phiên QA dài 1686,6s (~28 phút). Video chỉ bao phủ ~3 phút đầu (cold start, lúc dialog còn mở) — **đây không phải video toàn bộ phiên** như tên file gợi ý. Mọi màn hình sau 17:32 (lịch, IPTV, phim, cài đặt, player) đều không có trong video.
- Khuyết điểm thấy trong mọi frame: chữ dialog bị cắt ở dòng cuối ("mới nhất"), không có nút đóng nào nhìn thấy.

---

## Phần 3 — Phán quyết 20 finding "Mất dấu focus (Focus Loss) HIGH"

### Cơ sở đối chiếu
- `qa_report.json`: 20 findings, tất cả cùng một issue, chi tiết ghi "Sau các phím […], không có view nào giữ focus". `qa_session_summary.md` liệt kê các bước 1–18, 39, 40.
- `decisions_timeline` trong `qa_report.json` ghi trường `focused` cho từng bước: từ bước global 19 trở đi detector báo đúng view đang focus (`cardSports#…`, `schedCard#…`, `cardRoot#…`, `backBtn#…`) — tức **detector không hỏng**.
- Map bước global → mission: 1–5 = COLD_START, 6–13 = SPORTS_MULTI_SOURCE, 14–19 = ROOM_PICKER, 20–23 = DATA_ACCURACY, 24–31 = PLAYER_STREAMING, 32–41 = HOME_HUB. Vậy bước 39–40 = HOME_HUB bước 8–9 (WAIT 2.0 rồi DOUBLE_BACK, sau khi ENTER vào thẻ Phim).

### Kết quả từng nhóm

**Bước 1–18: ĐÚNG (lỗi thật, không phải artifact) — 18/18**
- Ảnh `step_001`–`step_018` đều cho thấy cùng một màn hình: dialog THÔNG BÁO, **không có bất kỳ dấu focus nào** (không viền trắng, không nút nổi bật).
- D-pad bấm liên tục (DOWN, RIGHT, UP…) nhưng màn hình không thay đổi gì ngoài đồng hồ — người dùng thật sự không điều khiển được gì.
- Nguyên nhân gốc: dialog không có view focusable nào nhìn thấy được và không có nút đóng; QA agent không bấm BACK trong 18 bước này nên dialog kẹt.
- Lưu ý: đây là **một lỗi duy nhất lặp lại 18 lần**, không phải 18 lỗi khác nhau.

**Bước 39–40: ĐÚNG (lỗi thật, không phải artifact) — 2/2**
- Ảnh `step_039`, `step_040` đều là màn hình lỗi "Không thể tải kho phim". Nút THỬ LẠI lúc này **không có viền trắng** — so sánh trực tiếp: cùng một nút trong ảnh mission 12–14 CÓ viền trắng rõ ràng. Tức tại thời điểm bước 39–40 focus thật sự chưa được gán cho nút này (màn hình lỗi vừa hiện, focus chưa kịp hạ cánh hoặc không được gán).
- Đây là lỗi thật nhưng nhỏ và có thể tự hết (focus xuất hiện ở ảnh mission cuối 12–14).

**Kết luận phần 3:** **20/20 finding đều được ảnh hỗ trợ — không có finding nào là artifact của detector.** Detector báo đúng: nó báo NONE đúng những lúc trên màn hình không có dấu focus, và báo đúng view cụ thể ở mọi bước còn lại (19–38, 41–127). Tuy nhiên, 20 finding này chỉ là **2 gốc lỗi** (dialog kẹt + màn hình lỗi phim chưa gán focus), không phải lỗi focus hệ thống của bản redesign. Điểm 0/100 là hệ quả của cách tính điểm (mỗi finding HIGH trừ nặng), trong khi 16/16 mission check đều pass.

---

## Phần 4 — Kiểm tra riêng bản redesign (KL5 / FPT-style)

- **Bảng màu KL5: ĐÚNG trên màn hình.** Nền than ấm xuyên suốt; đỏ chỉ dùng cho badge LIVE / TRỰC TIẾP, nút chính XEM NGAY / THỬ LẠI và dấu chấm đỏ ở logo. Không thấy cam #FF6500 cũ, không thấy cyan #22D3EE cũ ở bất cứ đâu. "VS" và số lượt xem màu vàng đồng (brass) — đúng vai trò accent phụ. Badge SOCO (xanh ngọc) và COLA (đỏ hồng) là badge nhận diện nguồn phát (nội dung), không phải màu chrome UI. Vạch tiêu đề mục Cài đặt màu vàng đồng (brass). (Lưu ý: mã hex chính xác không đo được từ ảnh JPEG nén — phần này vẫn do audit token 16/16 làm chuẩn.)
- **Bo góc 4dp, không gradient, không glow: ĐÚNG.** Thẻ bo góc nhẹ, focus chỉ là viền trắng 1dp, không thấy phát sáng hay gradient.
- **Nav chỉ chữ: ĐÚNG.** CÀI ĐẶT / BÁO LỖI TELEGRAM / LỊCH THI ĐẤU / TÌM KIẾM — không icon; focus là viền oval trắng (ảnh 07, 15).
- **Player OSD kiểu FPT: ĐÚNG MỘT PHẦN (đã xác nhận qua step_025–028).** `step_027` cho thấy video bóng đá đang phát thật, OSD top-bar đúng địa lý FPT: nút **QUAY LẠI** dạng pill viền trắng ở góc trên-trái (đang focus), tiêu đề trận đấu + "TRỰC TIẾP 1-0" ở góc trên-phải; bên trái có nút PIP và TÙY CHỌN. **Chưa xác nhận được:** hàng điều khiển dưới (seekbar, play/pause, badge LIVE, dãy nút tròn) — không xuất hiện trong bất kỳ ảnh nào đã xem (có thể OSD tự ẩn sau vài giây; không kết luận là thiếu hay đủ).
- **Hero banner:** `step_025` có hero trận đấu với ảnh sân vận động thật, nút XEM NGAY đỏ, "[MENU] ĐỔI LUỒNG" — render tốt.
- **Focus 1.13x/500ms:** không đo được hệ số scale từ ảnh tĩnh; chỉ xác nhận được viền trắng xuất hiện rõ trên thẻ/hàng/nav khi focus (ảnh 05, 07, 08, 09, 15, 16, 17, step_025–027).

---

## Phần 5 — Danh sách lỗi thật (xếp theo mức độ)

| # | Mức | Lỗi | Bằng chứng |
|---|---|---|---|
| R1 | HIGH | **Dialog THÔNG BÁO kẹt ở cold start:** không có view focusable, không có nút đóng, D-pad vô hiệu trong 18 bước / ~3–4 phút đầu. Đây là gốc của 18/20 finding Focus Loss. | step_001–018, ảnh 01–03, video vf_5s–165s |
| R2 | HIGH | **Màn hình đen hoàn toàn ở mission IPTV categories & favorites** — không UI, không focus. | 10_mission_iptv_categories_and_favorites.jpg |
| R3 | MEDIUM-HIGH | **Kho phim NguonC không tải được** — 3 mission phim (11, 12, 13) đều kết thúc ở cùng màn hình lỗi; Episode Picker và VOD player chưa hề được test thật về mặt hình ảnh dù check báo pass. Khả năng cao do mạng emulator (toast "Wi-Fi has no internet access" ở step_002), không hẳn lỗi UI — nhưng cần chạy lại khi mạng ổn. | 12/13/14_mission_*.jpg, step_039–040 |
| R4 | MEDIUM | **3 thẻ HomeHub (Sports/IPTV/Phim) render trống** — không nhãn, không icon/logo; người dùng không phân biệt được thẻ nào nếu không nhớ vị trí focus. Khả năng cao logo Canva chưa tải được do mạng (xem R3), nhưng trên màn hình thực tế chúng đang trống. Cần xác nhận lại khi mạng ổn. | 04, 06, 07, 15_mission_*.jpg |
| R5 | LOW-MEDIUM | **Logo đội bóng ở hàng lịch thi đấu thành vòng tròn xám trống; trận KẾT THÚC không hiện tỉ số.** Cùng họ nguyên nhân mạng như R3/R4, hoặc logo chưa được cache. | 05, 08, 09_mission_*.jpg |
| R6 | LOW | **IPTV EPG: focus mờ** (chỉ thấy một đường trắng dọc), hero trống đen, hàng cuối lưới kênh bị cắt ở mép dưới. | 11_mission_iptv_epg_and_zapping_player.jpg |
| R7 | LOW | **Chữ dialog THÔNG BÁO bị cắt** ở dòng cuối ("mới nhất") — dialog cao hơn nội dung cho phép. | 01–03, mọi frame video |
| R8 | INFO | Thẻ trận thứ 3 ở hàng ĐANG PHÁT bị cắt ở mép phải; chữ tên đội/gải đấu bị cắt ở mép thẻ khi cuộn ngang (step_026) — đây là hành vi cuộn ngang bình thường, không tính là lỗi. | 04, 06, step_026 |

**Không phải lỗi (đã kiểm chứng):** focus hoạt động đúng trên màn hình thường (lịch, nav, cài đặt, thẻ trận, player) — ảnh 05, 07, 08, 09, 15, 16, 17, step_025–027; player phát video thật (step_027); sau D-pad chaos app không crash và giữ focus (ảnh 17); không còn cam #FF6500/cyan cũ, không gradient/glow.

---

## Kết luận

- **Đã xem: 53 ảnh/frame** (17 mission + 12 frame video + 24 ảnh step bổ sung).
- **Lỗi thật đáng kể nhất:** dialog THÔNG BÁO kẹt không focus ở cold start (R1 — gốc của 18/20 finding), màn hình đen ở mission IPTV (R2), và kho phim không tải được khiến 3 mission phim chưa được test thật (R3). Thêm 3 thẻ HomeHub trống (R4) và logo đội xám trống (R5) — cả hai nhóm sau nhiều khả năng liên quan đến mạng emulator lúc chạy (toast "Wi-Fi has no internet access" ở step_002), cần chạy lại khi mạng ổn để kết luận dứt khoát.
- **Verdict Focus Loss: 20/20 finding đều đúng, không phải artifact.** Detector hoạt động chính xác (báo đúng view focus ở các bước còn lại). Nhưng 20 finding chỉ là 2 gốc lỗi, không phải lỗi focus hệ thống — điểm QA 0/100 gây hiểu lầm vì 16/16 mission check đều pass.
- **Verdict redesign:** trên màn hình, KL5 thể hiện đúng — nền than ấm, đỏ chỉ cho LIVE/nút chính, nav chỉ chữ, focus viền trắng, không còn cam/cyan, không gradient/glow; player OSD top-bar đúng kiểu FPT và phát video thật. Hàng điều khiển dưới của player chưa được quan sát trong bộ ảnh này nên chưa kết luận được.

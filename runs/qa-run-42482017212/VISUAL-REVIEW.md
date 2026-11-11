# Đánh giá trực quan — QA run 42482017212 (KenhLive TV, nhánh redesign/fpt-home-landing)

- **Run:** CI 42482017212 (QA-Suite, quick) · **Commit:** `5a78191` trên nhánh `redesign/fpt-home-landing` · **App:** KenhLive TV 0.1.12 (162)
- **Phiên:** `QA-SESS-20261108-125322-64d2ac` · **Thời lượng phiên:** 3714,7s · **Điểm QA tự động:** 94/100 (13/16 check, 13/16 mission)
- **PHIÊN BỊ CẮT NGANG:** job bị GitHub hủy ở bước 94/128 do hết `timeout-minutes: 90` — đây là phiên **chưa hoàn chỉnh**. 3 mission không chạy (PlayerActivity native, Tìm kiếm + Cài đặt, Chaos stress). Tab bao phủ chỉ 4/7 (Trực Tiếp / Tìm Kiếm / Cài Đặt có 0 thao tác).
- **KHÔNG CÓ VIDEO trong artifact này** (recorder không kịp hoàn thành do job bị hủy) — không có file `full_qa_tour.mp4`. Mọi nhận xét dưới đây chỉ dựa trên ảnh chụp.
- **Phạm vi đã xem trực tiếp: 20 ảnh** — 14 ảnh mission (`01`–`14`) + 6 ảnh step (`step_001`, `step_033`, `step_035`, `step_064`, `step_065`, `step_089`). Đối chiếu thêm `qa_report.json`, `qa_session_summary.md` và `qa_session.json` (timeline 94 bước, tất cả dùng OPENAI/nemotron).
- **Phương pháp:** chỉ ghi những gì nhìn thấy được trong ảnh. Không suy đoán mã nguồn, không đo mã hex từ ảnh JPEG nén (màu chính xác vẫn do `scripts/kl5_audit.py` 20/20 làm chuẩn).

---

## Phần 1 — 14 ảnh mission

### 01_cold_start.jpg — Dialog THÔNG BÁO + rail trái đã hiện (R1: ĐÃ SỬA)
- Màn hình chính phía sau bị làm mờ, phía trước là dialog **THÔNG BÁO** (nhóm Telegram @kenhlivetv, mã QR).
- **Rail trái HIỆN RÕ lần đầu:** TRANG CHỦ (có chấm đỏ live), TRUYỀN HÌNH, KHO PHIM, LỊCH TRÌNH, TÌM KIẾM, CÀI ĐẶT — chỉ chữ, dọc bên trái.
- **Focus: CÓ, rõ ràng** — viền trắng quanh nút **ĐÃ HIỂU / ĐÓNG** (nút đỏ, đã focus). Nút **VÀO NHÓM TELEGRAM** cũng thấy được bên phải.
- **Lỗi thấy được:** dòng cuối của thân dialog ("Cảm ơn bạn đã luôn đồng…") vẫn bị cắt nửa chữ ở mép dưới vùng thân — thân dialog đã bọc trong ScrollView nên cuộn được, nhưng ở trạng thái nghỉ trông vẫn bị cắt (xem D9). Phía sau dialog, chữ quảng cáo trên ảnh bìa banner ("V TAP", "HIỆM", "LUỒNG") lấp ló — xem D1.

### 02_mission_cold_start.jpg — Màn hình chính mới: rail + banner hero + ĐANG PHÁT
- Dialog đã tắt. Rail trái đầy đủ 6 mục, TRANG CHỦ có chấm đỏ.
- **Banner hero:** ảnh nền Chelsea + badge **TRỰC TIẾP** đỏ, "Serie A", mắt xem 377,9K, "Napoli VS Lazio", "Trực tiếp · Serie A · BLV TAP · Tín hiệu HD", nút đỏ **[OK] XEM NGAY**, "[MENU] ĐỔI LUỒNG". Ngày "Chủ Nhật, 08/11/2026" góc trên phải.
- **Focus: CÓ** — viền trắng quanh thẻ trận thứ 2 (HOL D1, SC Hee… vs Feyeno…).
- **Lỗi thấy được (D1):** ảnh bìa banner chứa chữ quảng cáo lớn ("BLV TAP", "KINH NGHIỆM", "LÀ ĐẲNG CẤP") đè/vướng vào chữ của banner: chữ "BLV TAP" đỏ to nằm sau ngày tháng, "KINH NGHIỆM" bị cắt ở mép phải, chữ "P" và "HI…" lẻ loi ở mép phải banner. Banner trông rối vì chữ trên ảnh bìa va chạm chữ giao diện.
- Hàng **ĐANG PHÁT**: 2 thẻ trận đầy đủ (logo đội, badge SOCO xanh ngọc, badge LIVE đỏ, "Đang trự…", "377,9K xem", "6 phòng"); thẻ thứ 3 bị cắt ở mép phải (cuộn ngang bình thường).

### 03_mission_sports_multi_source.jpg — Home cuộn, focus trên thẻ Napoli 1:1
- Rail: TRANG CHỦ có vạch đỏ bên trái (đang chọn) + chấm đỏ.
- Banner (cuộn lên một phần) vẫn vướng chữ bìa "KINH NGHIỆM / LÀ ĐẲNG CẤP" (D1).
- Mục mới: tiêu đề hàng **"Socolive TV · Trực Tiếp & Lịch Đấu"** (chấm xanh lá), "8 trận" bên phải.
- **Focus: CÓ, rõ** — viền trắng quanh thẻ Napoli 1:1 Lazio (Serie A, LIVE). Thẻ hiển thị tỉ số thật "1 : 1", logo đội đầy đủ. Thẻ 2: SC Hee… 9 : 6 Feyeno… (HOL D1, pill "Hiệp 2: 82'", LIVE).
- **Quan sát (D6):** thẻ Napoli có pill xám chỉ ghi **"0"** (trong khi ảnh 02 cùng thẻ ghi "SOCO") — pill thông tin có vẻ xoay vòng giữa badge nguồn và phút thi đấu, và khi không có dữ liệu phút thì hiện "0". Cần xác nhận từ dữ liệu.

### 04_mission_sports_room_picker.jpg — Giống 03, focus vẫn trên thẻ Napoli
- Y hệt 03 (chỉ khác pill thẻ 2 đổi "Hiệp 2: 82'" → "SOCO" — xác nhận pill xoay vòng giữa nguồn và phút trận đấu).
- Focus rõ trên thẻ Napoli 1:1. Không lỗi mới. D1 (chữ bìa banner) vẫn hiện.

### 05_mission_sports_data_accuracy.jpg — Hàng ĐANG PHÁT cuộn ngang, tỉ số thật
- Focus trên thẻ VIE D1 "The Co… 0 : 4 Thanh…" (pill "Hiệp 1: 41'", LIVE, "56,7K xem", "2 phòng"). Thẻ trái: "…g Anh" vs Liverpool (SOCO, LIVE, "62,0K xem"); thẻ phải: RUS D1 "Krylya… VS …".
- Tỉ số, logo đội, số người xem đều hiển thị thật. D1 vẫn hiện ở banner phía trên. Không lỗi mới ngoài D6 (pill "0" ở thẻ Napoli không còn trong khung hình này).

### 06_mission_player_streaming_and_controls.jpg — Dialog "Tùy Chọn Phát" trong player
- Dialog cài đặt player mở trên nền trận bóng đang phát (sân cỏ xanh, logo "TBONGTV", banner quảng cáo "BUFA" của luồng phát — nội dung của luồng, không phải của app).
- Các mục: **Chất lượng** (đang focus — nền xám nổi), "Tỉ lệ: 16:9 Chuẩn (Fit)", "Âm thanh: Tự động (Hay)", "Khuếch đại âm lượng: Tắt", "Kênh âm thanh (Ngôn ngữ)", "Hẹn giờ tắt (Chưa đặt)", "Thông số kỹ thuật (Stats)", "Đổi nguồn phát (Socolive)". Nút **ĐÓNG** chữ đỏ góc dưới phải.
- Chữ rõ, bố cục sạch, focus thấy được. Không lỗi trong dialog này.

### 07_mission_home_hub_3_cards_and_canva_logos.jpg — R4: 3 thẻ portal ĐÃ CÓ CHỮ (nhưng đáy cắt ở fold)
- Home cuộn xuống. Trên: 2 thẻ ĐANG PHÁT. Tiêu đề **SẮP DIỄN RA**.
- **3 thẻ portal render ĐẦY ĐỦ CHỮ (R4 đã sửa):** THỂ THAO (badge TRỰC TIẾP đỏ, "Trực tiếp bóng đá …", "NHẤN OK →", số lớn **4**, "NHÀ ĐÀI"); TRUYỀN HÌNH ("M3U TÙY CHỈNH", "Kênh VTV, HTV, VT…", "NHẤN OK →", **150+**, "KÊNH HD"); PHIM TRUYỆN ("4K FHD", "Hơn 33.000+ phim…", "NHẤN OK →", **33K+**, "PHIM & BỘ").
- **Lỗi thấy được (D3):** nhãn stat ở đáy thẻ ("NHÀ ĐÀI" / "KÊNH HD" / "PHIM & BỘ") nằm đúng mép dưới màn hình và bị cắt nửa chữ — thẻ kéo dài qua fold, nội dung dưới fold phải cuộn mới thấy. Không phải thẻ trống nữa, nhưng khung hình nghỉ trông như bị cắt dở.
- **Lỗi thấy được (D2):** ngay dưới tiêu đề **SẮP DIỄN RA** là 3 thẻ portal — KHÔNG CÓ hàng trận sắp đá nào ở giữa. Hàng trận sắp đá (rvUpcoming) trống vào lúc này (mọi trận trong dữ liệu đều đã bắt đầu) nên chỉ còn tiêu đề trơ trọi, đọc như thể 3 thẻ portal chính là nội dung của "SẮP DIỄN RA".
- Nền: ảnh bìa hero (huy hiệu Chelsea + chữ "KINH NGHIỆM")透 qua sau các mục — chữ bìa vẫn lấp ló sau tiêu đề mục (D1, mức nhẹ).

### 08_mission_schedule_epg_and_fixture_tap.jpg — Player đang tải luồng (mission lịch nhưng ảnh cuối là player)
- Màn hình đen với hộp "Đang tải luồng…" + spinner. Top bar: pill **◀ QUAY LẠI** có viền trắng (focus), "THỂ THAO · Napoli vs Lazio · TẠ BIÊN GIỚI", "SERIE A · TRỰC TIẾP · 1 - 1 · 0". Nút PIP / TÙY CHỌN bên trái.
- **Quan sát (D8):** chuỗi tỉ số "1 - 1 · 0" có đuôi "· 0" lạ — như một giá trị thừa (phút? thẻ?) không rõ nghĩa.
- Ảnh cuối mission là player đang tải (sau khi bấm vào trận ở lịch) — tên mission không khớp trạng thái cuối, nhưng đó là cách agent kết thúc mission, không phải lỗi app.

### 09_mission_sidebar_rail_full_traversal.jpg — Danh sách lịch, rail hoạt động đúng
- Rail trái: **TRANG CHỦ có viền trắng (focus)**, LỊCH TRÌNH có vạch đỏ (đang chọn). Điều hướng rail ↔ nội dung hoạt động.
- Danh sách trận theo giờ: 18:30 Napoli vs Lazio (Live), 18:15 SC Heerenve… (HOL D1), 19:15 The Cong-Viettel vs Thanh Hoa (VIE D1), 19:30 CSKA Moscow vs Zenit Petersburg (VTBUL), 20:00 Elche CF vs Real Betis (SPA D1). Mỗi hàng: giờ đỏ, badge Live, tên đội, giải đấu, avatar BLV (+2).
- Logo đội, chữ, tương phản đều tốt. Không lỗi thấy được. ("The Cong-Viettel" là tên đội từ dữ liệu.)

### 10_mission_iptv_categories_and_favorites.jpg — IPTV: hero trống, focus rõ, hàng cuối cắt
- Rail: TRUYỀN HÌNH có vạch đỏ (đang chọn). Hero: "ĐÀI TRUYỀN HÌNH VIỆT NAM (VTV)", badge TRỰC TIẾP đỏ + pill FHD, tiêu đề lớn **"VTV Cần Thơ"**, "Đang phát trực tiếp từ Đài Truyền hình Quốc gia", gợi ý phím. Logo **VTV** nền hồng đậm bên phải.
- **Focus: CÓ, rõ** — viền trắng quanh pill **Yêu Thích**. Các pill: VTV, ô "Tìm kênh TV…", nút THÊM M3U.
- Lưới kênh: VTV Cần Thơ, VTV1 HD, VTV10, VTV2 HD, VTV3 HD + "Việt Nam" + giờ chương trình.
- **Lỗi thấy được:** (a) hero trống đen, không có ảnh nền/backdrop ở trạng thái tĩnh (xem ảnh 12: khi phát thì có ảnh); (b) hàng lưới kênh cuối bị cắt nửa ở mép dưới màn hình (D5).

### 11_mission_iptv_epg_and_zapping_player.jpg — IPTV player ĐANG PHÁT video thật
- Video đang phát thật (ANTV HD, phim truyền hình — nữ diễn viên áo blazer xanh). Top bar: pill **◀ QUAY LẠI** viền trắng (focus), "KÊNH 1 · Đang chiếu: Phim truyện: 7h00 - Thập cửu muội - Tập 14/30", "ANTV HD" góc trên phải. Nút KÊNH / PIP / TÙY CHỌN bên trái. Góc dưới phải có đồng hồ "20 : 30".
- Không có hàng điều khiển dưới (OSD đã tự ẩn — bình thường khi đang phát).
- **Quan sát (D8):** dòng tiêu đề chương trình dài chạy sát dưới nhãn "ANTV HD", suýt chạm nhau ở góc trên phải. Nhẹ.

### 12_mission_phim_nguonc_and_categories.jpg — IPTV hero CÓ ảnh nền khi đang phát (tên mission là phim nhưng ảnh cuối là IPTV)
- Giống ảnh 10 nhưng hero giờ có ảnh nền video thật (khung hình kênh VTV Cần Thơ, logo "CầnThơ 1" góc trên phải) — hero "trống" ở ảnh 10 chỉ là trạng thái tĩnh trước khi phát.
- Rail: TRUYỀN HÌNH đang chọn; **focus đang ở CÀI ĐẶT** (viền trắng quanh mục cuối rail) — agent đã di chuyển focus xuống cuối rail.
- Hàng lưới kênh cuối vẫn cắt ở mép dưới (D5).
- Lưu ý: tên mission là kho phim nhưng ảnh cuối mission là màn hình IPTV (agent kết thúc ở đó); kho phim thật sự có chạy hay không xem ở ảnh 13/14.

### 13_mission_phim_episode_picker_and_favorite.jpg — Kho phim: hero phim thật, thư viện đã tải (R3 đã hết)
- Rail: KHO PHIM có vạch đỏ (đang chọn). Hero phim **"Mục Thần Ký"** 2024, "Phiêu Lưu · Viễn Tưởng", poster thật (nhân vật huyền huyễn), "NỔI BẬT · Tác phẩm điện ảnh nổi bật hôm nay", "K ĐIỆN ẢNH ĐẶC SẮC", mô tả (cắt "…" — bình thường), nút **▶ XEM NGAY** đỏ, "CHỌN TẬP", "+ LƯU PHIM" (viền pill), "PHIM" bên phải.
- Dưới: DANH MỤC — pill **"Tất Cả"** nền vàng cam (đang chọn), "Lịch Sử Xem", "Tìm Kiếm", "Mới Cập Nhật", "Phim Bộ". Mục **"Phim Mới Cập Nhật — 120 phim"**.
- **Kho phim tải được với poster thật** — lỗi R3 (không tải được kho phim) của lượt trước đã hết.
- **Quan sát:** trong ảnh này KHÔNG thấy rõ viền focus trắng trên phần tử nào (có thể focus đang ở phần tử dưới fold, hoặc ở nút XEM NGAY mà không thấy viền). Xem D10.
- Pill "Tất Cả" màu vàng cam — có thể là brass KL5 (#C9A227), không đo được mã hex từ JPEG nên không kết luận.

### 14_mission_vod_player_seek_and_resume.jpg — Kho phim, mục TIẾP TỤC XEM (VOD seek/resume đã chạy)
- Giống ảnh 13 (cùng hero "Mục Thần Ký"). **Focus: CÓ, rõ** — viền trắng quanh **TRANG CHỦ** trên rail; KHO PHIM có vạch đỏ.
- Mục dưới đổi thành **"TIẾP TỤC XEM — 1 phim"** — hàng tiếp tục xem có dữ liệu (VOD seek/resume đã được agent chạy ở mission này, khớp tên mission).
- Không lỗi mới ngoài D10 (focus trên hero phim không rõ ở ảnh 13).

---

## Phần 2 — 6 ảnh step đã đối chiếu

### step_001_mission_.jpg — Dialog lúc mở app (R1, khớp ảnh 01)
- Y hệt ảnh 01. Timeline ghi focus `btnCloseFeedback` — khớp với viền trắng thấy trên nút ĐÃ HIỂU / ĐÓNG trong ảnh. **R1 xác nhận ở cả ảnh và detector.**

### step_033_mission_.jpg — Banner, focus trên XEM NGAY (D1 rõ nhất)
- Focus viền trắng quanh nút **[OK] XEM NGAY** (đỏ). Timeline ghi focus `heroPlay` — khớp.
- D1 thấy rõ nhất ở đây: đồng hồ "20:09" đè lên chữ "BLV TAP" đỏ to; ngày "Chủ Nhật, 08/11/2026" đè lên chữ bìa; "KINH NGHIỆM" / "LÀ ĐẲNG CẤP" sau chữ banner; ký tự "P" và "HI…" lẻ loi ở mép phải banner.
- Hàng ĐANG PHÁT bên dưới đầy đủ 2 thẻ + thẻ thứ 3 cắt mép phải (bình thường).

### step_035_mission_.jpg — Portal, focus trên thẻ THỂ THAO (R4 + D2 + D3)
- Focus viền trắng quanh thẻ **THỂ THAO**; timeline ghi focus `cardSports` — khớp.
- Xác nhận lại: tiêu đề SẮP DIỄN RA nằm ngay trên 3 thẻ portal, không có hàng trận nào ở giữa (D2). Nhãn stat "NHÀ ĐÀI" / "KÊNH HD" / "PHIM & BỘ" cắt nửa ở mép dưới (D3). Thẻ portal có đủ chữ, số, badge (R4).

### step_064_mission_.jpg — IPTV, focus trên pill Yêu Thích
- Y hệt ảnh 10. Timeline ghi focus `groupTitle` — khớp viền trắng trên pill Yêu Thích. Hero trống ở trạng thái tĩnh; hàng lưới cuối cắt mép dưới (D5).

### step_065_mission_.jpg — IPTV, focus sang lưới kênh (D4)
- Timeline ghi focus `cardIptvRoot` (thẻ kênh VTV Cần Thơ). Trên ảnh, viền focus của thẻ kênh **rất mờ — chỉ một đường trắng mỏng ở mép trên thẻ**, yếu hẳn so với viền trắng đậm trên thẻ trận/rail. Pill Yêu Thích đã mất viền. Đây là lỗi hiển thị focus của lưới kênh IPTV (cùng họ với R6 lượt trước).

### step_089_mission_.jpg — Dialog lỗi giải mã (finding LOW duy nhất — ĐÚNG)
- Player VOD ("PHIM TRUYỆN · Mục Thần Ký · Tập 01") hiện dialog **"Lỗi Phát Luồng Video / Stream lỗi: ERROR_CODE_DECODING_FAILED"** với 3 nút THỬ LẠI (đang focus — nền tối nổi), QUAY LẠI, BÁO LỖI. Top bar "◀ QUAY LẠI", nút PIP. Hàng điều khiển dưới hiện đủ: seekbar 01:06 / 19:18, PHÁT | **TUA -10S (viền trắng)** | TUA +10S | TẬP TRƯ… | TẬP TIẾP | DANH SÁ… | CÀI ĐẶT.
- Timeline ghi focus NONE (player dùng focus tự vẽ, không dùng focus Android — đã biết từ lượt trước), nhưng ảnh cho thấy viền trắng trên TUA -10S và highlight trên THỬ LẠI. Dialog hiển thị đúng, đủ nút.
- **Finding LOW của AI là chính xác:** lỗi giải mã trên emulator x86 (thiếu codec), không phải lỗi app. Nhưng lưu ý D7: nhãn nút OSD vẫn bị cắt ("TẬP TRƯ…", "DANH SÁ…") và phụ đề đè lên seekbar — đây là lỗi cũ từ lượt trước, nằm trong đợt "sửa chung sau", chưa sửa ở nhánh này.

---

## Phần 3 — Xác minh sửa R1 / R4

| Lỗi cũ | Kết quả ở lượt này | Bằng chứng |
|---|---|---|
| R1 — Dialog THÔNG BÁO kẹt: không nút đóng thấy được, không focus, D-pad vô hiệu | **ĐÃ SỬA** | Ảnh 01 + step_001: cả 2 nút thấy được, viền trắng trên ĐÃ HIỂU / ĐÓNG, timeline step 1 focus `btnCloseFeedback`. Agent đóng dialog và đi tiếp (step 2 focus `heroPlay`). |
| R4 — 3 thẻ portal render trống | **ĐÃ SỬA** | Ảnh 07 + step_035: 3 thẻ có đủ badge, tiêu đề, mô tả 1 dòng, "NHẤN OK →", số stat lớn. Timeline step 35–37 focus `cardSports` → `cardIptv` → `cardPhim` lần lượt. |
| R3 — Kho phim không tải được | **Đã hết (do mạng)** | Ảnh 13/14: poster thật, 120 phim mới cập nhật, hàng TIẾP TỤC XEM có 1 phim. |
| R2 — Màn hình đen IPTV | **Không tái hiện** | Ảnh 10/12: IPTV render đầy đủ (hero, pill, lưới kênh). R2 vẫn ngoài phạm vi nhánh này, cần chẩn đoán riêng — nhưng 2 lượt QA liên tiếp đều không tái hiện. |

---

## Phần 4 — Màn hình chính kiểu FPT: verdict

**Kết cấu ĐÚNG như thiết kế:** rail trái hiện rõ (6 mục chỉ chữ, vạch đỏ khi chọn, chấm đỏ live ở TRANG CHỦ, viền trắng khi focus); banner hero toàn chiều rộng với trận tâm điểm + nút XEM NGAY đỏ; nền full-screen (ảnh bìa hero + scrim); các hàng ĐANG PHÁT / SẮP DIỄN RA / portal xếp dọc và cuộn được; dialog và portal đã sửa. Focus di chuyển được rail ↔ nội dung (timeline: DPAD_RIGHT từ `cardPhim` sang `nav_live`; DPAD_DOWN từ banner `heroPlay` xuống `cardRoot`; rail traversal ở mission 09 và step 47–53).

**Bảng màu KL5 ĐÚNG trên màn hình:** nền than ấm, đỏ chỉ ở badge LIVE / TRỰC TIẾP, nút XEM NGAY, nút ĐÃ HIỂU và vạch chọn rail; nav chỉ chữ; focus viền trắng; không thấy cam #FF6500 / cyan cũ, không gradient/glow trong chrome UI. (Badge SOCO xanh ngọc, logo VTV hồng đậm, pill "Tất Cả" vàng cam là màu của nội dung/nguồn — không phải chrome UI.)

**Chưa giống FPT hẳn ở cảm giác:** banner hero là điểm khác biệt lớn nhất còn lại — FPT dùng banner quảng cáo sạch với tiêu đề rõ, còn ở đây ảnh bìa chứa chữ quảng cáo lớn va chạm chữ giao diện (D1). Phần còn lại (rail + hàng + thẻ) đã rất gần cấu trúc FPT.

---

## Phần 5 — Các lỗi thật AI bỏ sót (AI chỉ báo 1 finding LOW)

| # | Mức | Lỗi | Bằng chứng |
|---|---|---|---|
| D1 | MEDIUM-LOW | **Chữ trên ảnh bìa banner va chạm chữ giao diện:** ảnh bìa hero chứa chữ quảng cáo lớn ("BLV TAP / KINH NGHIỆM / LÀ ĐẲNG CẤP") đè lên tiêu đề trận, dòng "Trực tiếp · Serie A · BLV TAP" và đồng hồ/ngày ("20:09" đè lên "BLV TAP"); chữ bìa còn bị cắt ở mép phải banner ("P", "HI…"). Scrim chưa đủ mạnh để làm mờ chữ bìa. | 02, 03, 04, 05, step_033; 01/step_001 (sau dialog) |
| D2 | LOW-MEDIUM | **Mục SẮP DIỄN RA chỉ có tiêu đề, không có trận nào:** hàng trận sắp đá trống vào lúc chạy (mọi trận đã bắt đầu) nên tiêu đề nằm ngay trên 3 thẻ portal, đọc như thể portal thuộc về "SẮP DIỄN RA". Thiếu trạng thái trống hoặc ẩn mục khi không có dữ liệu. | 07, step_035 |
| D3 | LOW | **Nhãn stat đáy thẻ portal cắt nửa ở fold:** ở vị trí cuộn nghỉ, "NHÀ ĐÀI" / "KÊNH HD" / "PHIM & BỘ" nằm đúng mép dưới màn hình, cắt nửa chữ. Cuộn xuống thì thấy đủ — chỉ là khung hình nghỉ trông dở. | 07, step_035 |
| D4 | LOW | **Focus trên thẻ kênh IPTV rất mờ:** chỉ một đường trắng mỏng ở mép trên thẻ (step_065), yếu hẳn so với viền focus đậm ở thẻ trận/rail. Cùng họ với R6 lượt trước. | step_065 (so với step_064) |
| D5 | LOW | **Hàng lưới kênh IPTV cuối cắt nửa ở mép dưới** trong mọi ảnh IPTV; hero trống đen ở trạng thái tĩnh (có ảnh khi đang phát — ảnh 12). | 10, 12, step_064, step_065 |
| D6 | LOW (cần xác nhận) | **Pill xám chỉ ghi "0" trên thẻ Napoli–Lazio** (ảnh 03–05) trong khi cùng thẻ ở ảnh 02 ghi "SOCO" — pill xoay vòng giữa badge nguồn và phút thi đấu, có vẻ render phút thiếu dữ liệu thành "0". | 03, 04, 05 (so với 02) |
| D7 | LOW (đã biết, chưa sửa) | **Nhãn nút OSD player vẫn bị cắt** ("TẬP TRƯ…", "DANH SÁ…") và phụ đề đè lên seekbar. Lỗi cũ từ lượt trước, nằm trong đợt "sửa chung sau" — ghi lại để khỏi tưởng là mới. | step_089 |
| D8 | INFO | Chuỗi tỉ số player có đuôi lạ "1 - 1 · 0" (ảnh 08); tiêu đề chương trình IPTV chạy sát dưới nhãn kênh ở góc trên phải (ảnh 11). | 08, 11 |
| D9 | INFO | Dòng cuối thân dialog THÔNG BÁO vẫn cắt nửa chữ ở trạng thái nghỉ ("Cảm ơn bạn đã luôn đồng…") — ScrollView cuộn được nên không kẹt, chỉ là mỹ quan. | 01, step_001 |
| D10 | INFO (cần kiểm tra) | Ảnh 13 (kho phim) không thấy rõ viền focus trên phần tử nào — có thể focus đang ở dưới fold hoặc ở XEM NGAY mà không thấy viền. Ảnh 14 thì focus rõ trên rail TRANG CHỦ. Cần kiểm tra focus trên hero phim ở lượt QA đầy đủ sau. | 13 (so với 14) |

**Không phải lỗi (đã kiểm chứng):** rail hiện và điều hướng được; banner hiển thị trận tâm điểm thật + XEM NGAY focus được; ĐANG PHÁT có tỉ số/logo/số người xem thật; lịch thi đấu đầy đủ giờ + Live + BLV; IPTV phát video thật (ảnh 11); kho phim có poster thật; dialog lỗi giải mã hiển thị đúng 3 nút; player OSD đủ hàng điều khiển dưới; dialog THÔNG BÁO đóng được và focus hạ cánh đúng.

---

## Phần 6 — Verdict về finding duy nhất và điểm 94/100

- **Finding LOW (ERROR_CODE_DECODING_FAILED) là chính xác và đã được AI đánh giá đúng mức:** đây là giới hạn codec của emulator x86, dialog lỗi hiển thị đúng với đủ 3 nút, không phải lỗi app. Không có gì để sửa trong app cho finding này.
- **Điểm 94/100 là công bằng cho một PHIÊN CHƯA HOÀN CHỈNH** — nhưng nó đo "không crash, không mất focus, luồng chạy được", không đo độ sạch về mặt hình ảnh. AI bỏ sót D1–D6 (đều ở mức polish, không chặn), và 3/16 mission chưa chạy chút nào. Nói "94/100" mà không kèm chú thích sẽ gây hiểu lầm là giao diện đã sạch — thực tế màn hình chính mới vẫn còn D1 (banner rối chữ) là điểm nhìn thấy ngay khi mở app.
- **Nemotron lần này đáng tin hơn lượt trước:** không còn finding phóng đại nào (0 finding HIGH/MEDIUM); nó mô tả đúng màn hình và tự hạ mức finding xuống LOW khi nhận ra giới hạn môi trường. Nhưng nó vẫn mù trước các lỗi mỹ quan (chữ va chạm, mục trống, focus mờ, cắt ở fold) — những thứ chỉ mắt người soi ảnh mới thấy.

---

## Phần 7 — Lượt QA đầy đủ sau nên kiểm tra

(Lượt rerun 42489380818 đã chạy với timeout 150 phút; nếu nó chạy hết 128 bước thì kiểm tra những mục này trên bộ ảnh của nó.)

1. **D1 — banner:** chữ bìa còn va chạm chữ giao diện không (đặc biệt với các trận/ảnh bìa khác nhau, không chỉ BLV TAP).
2. **D2 — SẮP DIỄN RA:** khi có trận sắp đá thì hàng fixture có hiện không; khi trống thì tiêu đề có bị ẩn hoặc có dòng trạng thái trống không.
3. **D3/D5 — fold:** vị trí cuộn nghỉ có còn cắt nhãn stat portal và hàng lưới IPTV cuối không.
4. **D4 — focus lưới kênh IPTV:** viền focus trên thẻ kênh đã rõ như thẻ trận chưa.
5. **D6 — pill "0":** pill thông tin trên thẻ trận còn hiện "0" khi thiếu phút không.
6. **D10 — focus hero phim:** focus trên màn hình kho phim có thấy rõ không.
7. **Bao phủ còn thiếu ở phiên này:** tab Trực Tiếp (0 thao tác), Tìm Kiếm (0), Cài Đặt (0); mission PlayerActivity native (0 bước); mission Chaos stress (0 bước). Cần chạy đủ để xác nhận các màn đó trên nhánh mới.
8. **Video:** phiên này KHÔNG có video (job bị hủy trước khi recorder hoàn thành). Lượt sau (timeout 150 phút) cần xác nhận video full tour có đủ dài không — đây cũng là lần kiểm tra đầu tiên của bản sửa `video_recorder.py` (commit 15a986a).
9. **R2 (màn hình đen IPTV):** 2 lượt liên tiếp không tái hiện — nếu lượt đầy đủ sau cũng không tái hiện thì có thể hạ mức ưu tiên chẩn đoán riêng.

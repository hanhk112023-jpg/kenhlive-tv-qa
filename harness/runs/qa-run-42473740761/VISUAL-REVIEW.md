# Đánh giá trực quan — QA run 42473740761 (KenhLive TV, main 07814ff)

- **Run:** CI 42473740761 (QA-Suite, quick) · **Commit:** `07814ff` trên main · **App:** KenhLive TV 0.1.12 (162)
- **Phiên:** `QA-SESS-20261108-110758-ba8bce` · **Thời lượng phiên:** 3827,5s (~64 phút, dài gấp ~2,3 lần lượt trước vì mỗi bước đều gọi model AI) · **Điểm QA tự động:** 0/100 (16/16 check đều pass — điểm 0 đến hoàn toàn từ 27 finding)
- **Điểm khác biệt lớn nhất so với lượt trước (42470778044):** AI Brain lần này chạy thật — `qa_session.json` ghi `ai_cognition.provider = OPENAI` trên **cả 128/128 bước** (lượt trước là `LOCAL_REFLEX` 127/127). Preflight đã trả về full model id `nvidia/nemotron-3.5-super-vl-120b-a12b`.
- **Phạm vi đã xem:** 17 ảnh mission (`01`–`17`), 12 frame video (`vf_001s`–`vf_012s`, 1 frame/15s), 19 ảnh step tương ứng với các finding (`step_009, 011, 020, 029, 069, 087–090, 093, 094, 097, 098, 100, 102, 106, 108, 110, 112`). **Tổng cộng 48 ảnh/frame đã xem trực tiếp.**
- **Phương pháp:** chỉ ghi những gì nhìn thấy được trong ảnh, đối chiếu với `ui_state` trong timeline (`focused_view`, `has_focus_ring`, `focus_ring_color`) và hành động đã bấm ở mỗi bước. Không suy đoán mã nguồn, không đo mã hex từ ảnh nén (mã màu chính xác vẫn do `scripts/kl5_audit.py` làm chuẩn).
- **Lưu ý về video:** `full_qa_tour.mp4` chỉ dài 175s (chunk 1) dù `concat.txt` liệt kê 22 chunk (~64 phút). Lượt này bắt đầu TRƯỚC khi sửa `video_recorder.py` (commit 15a986a), nên lỗi ghép video cũ vẫn xảy ra và 21 chunk sau đã bị xóa — video chỉ bao phủ ~3 phút đầu, KHÔNG phải toàn bộ phiên.

---

## Phần 1 — 17 ảnh mission

### 01_cold_start.jpg — Dialog THÔNG BÁO, y hệt lượt trước
- Màn hình home "ĐANG PHÁT" phía sau bị làm mờ, dialog THÔNG BÁO che giữa.
- **Focus: KHÔNG thấy dấu focus nào.** Chữ cuối "…hoặc nhận file cập nhật **mới nhất**" vẫn bị cắt ngang ở mép dưới dialog; không thấy nút đóng/OK nào.
- Đây là R1 của lượt trước, **chưa được sửa trên main** (bản sửa nằm trong nhánh FPT-home đang làm dở).

### 02_mission_cold_start.jpg — Hero + hàng Socolive, focus rõ
- Hero trận SC Heerenveen vs Feyenoord (HOL D1, BLV TOMIA, 323,8K xem), nút đỏ **[OK] XEM NGAY** + [MENU] ĐỔI LUỒNG. Dưới là hàng "Socolive TV · Trực Tiếp & Lịch Đấu".
- **Focus: CÓ, rõ** — viền trắng quanh thẻ Napoli vs Lazio 0 : 0.
- **Ghi nhận:** chữ lớn trên ảnh cover hero ("KHĂN RA RUNG / VÙNG TAY RA GÓC") đè lên vùng tiêu đề trận, nhìn rối — đó là chữ có sẵn trong ảnh cover, va chạm với tiêu đề đè lên trên (xem R6).

### 03_mission_sports_multi_source.jpg — Socolive + ColaTV, focus rõ
- Hai hàng: Socolive TV (Napoli 0 : 0 Lazio, Caykur 2 : 0 Erzuru…, Krylya… vs FC…) và ColaTV (Rizespor 5 : 2 Erzuru…, "Giao hữu Quốc tế" 19:00 · 10/11).
- **Focus: CÓ, rõ** — viền trắng quanh thẻ "Giao hữu Quốc tế" (COLA).
- Tên đội bị cắt ngắn trên thẻ nhỏ ("Vi…", "Th…", "Lên só…"), tỉ số cập nhật theo thời gian thực (Caykur 2 : 0 → 5 : 2 ở ảnh sau).

### 04_mission_sports_room_picker.jpg — Giống 03
- Cùng màn hình, tỉ số đã đổi (Caykur 5 : 2). Focus vẫn ở thẻ "Giao hữu Quốc tế".
- Không có dialog chọn phòng nào xuất hiện trong ảnh cuối mission này.

### 05_mission_sports_data_accuracy.jpg — Focus rõ, logo đội đã tải được
- **Focus: CÓ, rõ** — viền trắng quanh thẻ RUS D1 (Krylya… vs FC Ore…).
- Khác lượt trước: logo đội phần lớn đã tải (logo Napoli, Lazio, Caykur có màu thật), không còn vòng tròn xám trống. Tỉ số trực tiếp cập nhật (Rizespor 6 : 2).
- Tên giải: "Serie A", "TUR D1", "RUS D1" xen với "Giải Ngoại hạng…" (tiếng Việt) — xem phán quyết finding tiếng Anh ở Phần 3.

### 06_mission_player_streaming_and_controls.jpg — Màn hình chờ "Đang tải lịch thi đấu…"
- Màn hình đen + spinner + chữ "Đang tải lịch thi đấu…". Không có UI, không có focus.
- Ảnh cuối mission player nhưng lại là màn hình chờ lịch đấu — player đã thoát (hoặc chưa mở được) và app đang tải lại lịch. Đây là trạng thái chuyển tiếp, không kết luận được là kẹt hay chỉ đang tải (xem step_029 ở Phần 3).

### 07_mission_home_hub_3_cards_and_canva_logos.jpg — Lịch đấu, focus rõ (không phải Hub)
- Danh sách lịch: Crystal Palace vs Liverpool, Ipswich Town vs Bournemouth AFC, Sunderland vs Chelsea, Man Utd vs Aston Villa, Genoa vs AC Milan.
- **Focus: CÓ, rõ** — viền trắng quanh hàng "Genoa vs AC Milan".
- Logo đội đã tải (logo thật, có màu). Tên giải "Ngoại Hạng Anh" (tiếng Việt) và "Serie A". Tên đội dài xuống 2 dòng ("Ipswich Town vs Bournemouth AFC", "Manchester United vs Aston Villa") — chấp nhận được.
- Lưu ý: tên mission là "home hub 3 cards" nhưng ảnh cuối là màn hình lịch đấu (agent đã rời Hub) — không thấy 3 thẻ portal trong ảnh này.

### 08_mission_schedule_epg_and_fixture_tap.jpg — Dialog chọn phòng BLV
- Dialog "Angers SCO vs OGC Nice — Ligue 1 · 2 phòng live", 2 hàng: BLV RYO (SOCO) và VINFAST (SOCO, có dấu ">").
- **Focus: KHÔNG rõ** — không thấy viền trắng trên hàng nào trong dialog; hàng "23:15 Angers SCO vs OGC Nice" phía dưới (nền) thì có viền trắng. Dialog có thể đang không giữ focus hiển thị, hoặc focus đang ở hàng nền. Ghi nhận là KHÔNG RÕ (xem thêm ở R6).

### 09_mission_sidebar_rail_full_traversal.jpg — Lịch đấu, focus rõ
- Danh sách lịch (Monza vs Atalanta, FC Köln vs Bayer 04 Leverkusen, SC Freiburg vs 1. FC Union Berlin, Stade Rennais FC vs LOSC Lille, Angers SCO vs OGC Nice).
- **Focus: CÓ, rõ** — viền trắng quanh hàng "Angers SCO vs OGC Nice" (23:15) ở cuối.
- Tên giải "Serie A", "Bundesliga", "Ligue 1" — đều là tên riêng gốc (Ý/Đức/Pháp). Không thấy rail/sidebar trong ảnh.

### 10_mission_iptv_categories_and_favorites.jpg — IPTV render được, KHÔNG còn màn hình đen
- Dialog "DANH SÁCH PHÁT M3U TÙY CHỈNH" với ô nhập link (đang focus — viền trắng + con trỏ), chữ "Xóa link" đỏ, bàn phím ảo mở (phím "q" nền trắng = đang focus).
- Phía sau: "VTV Cần Thơ — Đang phát trực tiếp", ô "VTV" màu hồng đậm.
- **Kết luận quan trọng:** R2 của lượt trước (màn hình đen hoàn toàn ở mission IPTV) **KHÔNG tái hiện** ở lượt này — IPTV render được, dialog + bàn phím hoạt động, focus thấy rõ trên ô nhập.

### 11_mission_iptv_epg_and_zapping_player.jpg — Player IPTV đang tải, nút QUAY LẠI có viền
- PlayerActivity: top bar pill "◀ QUAY LẠI" **có viền trắng**, tiêu đề "TRUYỀN HÌNH · VTV1 HD / KÊNH 6 · Đang chiếu: Hài quan Việt Nam", nút "KÊNH / PIP / TÙY CHỌN" bên trái. Giữa màn hình: "Đang tải luồng…" + spinner, vùng video đen (luồng chưa tải xong).
- Viền trắng trên pill QUAY LẠI: không phân biệt được đây là viền mặc định của nút hay viền focus — xem phân tích ở Phần 3 (nhóm PlayerActivity).

### 12_mission_phim_nguonc_and_categories.jpg — Kho phim ĐÃ TẢI ĐƯỢC
- Hero phim "Cuộc Chiến Ẩm Thực" (2026, Chính Kịch) với ảnh nền thật (cảnh bếp), mô tả tiếng Việt, nút đỏ "▶ XEM NGAY", "CHỌN TẬP", "LƯU PHIM", "PHIM KHÁC".
- Hàng DANH MỤC: "Tất Cả" (đang chọn, viền vàng đồng), Lịch Sử Xem, Tìm Kiếm, Mới Cập Nhật, Phim Bộ, Phim Lẻ, Anime &…; "Phim Mới Cập Nhật — 120 phim".
- **Kết luận:** R3 của lượt trước (kho phim không tải được) **đã hết** — mạng emulator lần này hoạt động, kho phim tải đủ nội dung.
- **Focus: KHÔNG rõ** — không thấy viền trắng trên nút XEM NGAY hay thẻ nào; viền vàng đồng trên "Tất Cả" là trạng thái đang chọn (selected), không phải focus.

### 13_mission_phim_episode_picker_and_favorite.jpg — ĐÃ LƯU (1), focus ở nút back
- Giống 12 nhưng nút "LƯU PHIM" đã thành "✓ ĐÃ LƯU"; dưới có hàng "BỘ PHIM ĐÃ LƯU (1)".
- **Focus: CÓ** — nút back "<" góc trên-trái có vòng tròn trắng bao quanh (focus ring).
- Không thấy dialog chọn tập nào trong ảnh cuối mission này (episode picker có thể đã mở ở bước giữa — không kiểm chứng được từ ảnh cuối).

### 14_mission_vod_player_seek_and_resume.jpg — ĐÃ LƯU (TẬP 01 · 12:16/01:12:14)
- Giống 13 nhưng "✓ ĐÃ LƯU (TẬP 01 · 12:16/01:12:14)" và hàng "TIẾP TỤC XEM — 1 phim".
- **Kết luận:** tua + lưu vị trí xem (resume) **hoạt động thật** — VOD đã phát tới 12:16 và vị trí được lưu. Focus ở nút back (vòng tròn trắng) như ảnh 13.

### 15_mission_player_settings_dialog.jpg — Player VOD đang phát thật + HÀNG ĐIỀU KHIỂN DƯỚI ĐÃ XUẤT HIỆN
- Video thật đang phát (cảnh phim Hàn, phụ đề "Trưởng phòng Seon Jeong Won"). Top bar: "◀ QUAY LẠI" (chữ thường, không pill), "PHIM TRUYỆN · Cuộc Chiến Ẩm Thực · Tập 01", "PIP".
- **Hàng điều khiển dưới (lần đầu quan sát được):** seekbar 24:37 / 1:12:14 + dãy nút PHÁT | TUA -10S | TUA +10S | TẬP TRƯ… | TẬP TIẾP | DANH SÁ… | **CÀI ĐẶT (có viền trắng — đang focus)**.
- **Ghi nhận:** nhãn 2 nút bị cắt ("TẬP TRƯ…", "DANH SÁ…"); phụ đề đè lên vùng seekbar; đoạn đã phát trên seekbar có màu hồng/magenta nhạt (cần đối chiếu token KL5 — xem R6).

### 16_mission_search_and_settings_feedback.jpg — Tìm kiếm phim, poster thật, focus không rõ
- Ô tìm kiếm "Tìm phim, anime, diễn viên (VD: One Piece, Conan, Lật Mặt…)", nút đỏ TÌM KIẾM, "✕ ĐÓNG"; thịnh hành: One Piece, Conan, Ao no Hako, Dan Da Dan, Doraemon, Drago…
- "Phim & Anime Thịnh Hành Được Tìm Kiếm Nhiều Nhất" với 5 poster thật (Cuộc Chiến Ẩm Thực, Lời Nói Dối Hoàn Hảo, Vỗ Về Trái Tim, Upin & Ipin (Phần 19), Mười Ba Kiểu Tình Yêu).
- **Focus: KHÔNG thấy** — không có viền trắng trên poster hay nút nào.
- Lưu ý: đây là màn tìm kiếm trong tab Phim; theo bảng bao phủ, Tab 3 (Tìm Kiếm) và Tab 4 (Cài Đặt) có 0 thao tác trong phiên này — xem ghi chú bao phủ ở Phần 5.

### 17_mission_dpad_chaos_stress_and_recovery.jpg — Giống 16, focus ở "Dragon Ball"
- Cùng màn tìm kiếm; pill "Dragon Ball" có viền trắng (đang focus). Sau chuỗi D-pad chaos, app vẫn ở màn tìm kiếm và giữ focus ổn định — không crash.
- Đây là bằng chứng recovery tốt (giống lượt trước).

---

## Phần 2 — 12 frame video (`full_qa_tour.mp4`, 175s, 1280×720)

| Frame | Nội dung |
|---|---|
| vf_001s | Dialog THÔNG BÁO (giống ảnh 01) |
| vf_005s | Hero + hàng Socolive, focus ở thẻ Napoli vs Lazio |
| vf_009s | Hero + hàng Socolive/ColaTV, focus ở thẻ Caykur 2 : 0 |
| vf_012s | Hàng Socolive + ColaTV, focus ở thẻ Rizespor 5 : 2 |

- **Cả 12 frame đều nằm trong ~3 phút đầu** (cold start → hàng thể thao). Dialog đã được đóng trong khoảng 15s–60s (vf_001s còn dialog, vf_005s đã hết) — khác lượt trước (dialog kẹt suốt video).
- **Focus thấy rõ và di chuyển được** trong các frame sau dialog (viền trắng đổi thẻ theo từng frame).
- **Giới hạn:** video chỉ là chunk 1 trong 22 chunk (`concat.txt` liệt kê chunk_01–chunk_22, ~64 phút). Lỗi ghép video cũ (trước commit 15a986a) khiến 21 chunk sau bị mất — đây KHÔNG phải video toàn phiên.

---

## Phần 3 — Phán quyết từng nhóm finding (27 finding)

### Nhóm A — 2 LOW "viền focus không chuẩn nhưng hiển thị WHITE" (bước 9, 11): ARTIFACT
- `step_009`: thẻ TUR D1 (Caykur 2 : 0) có **viền trắng rõ ràng**. `step_011`: thẻ ColaTV "Giải Ngoại hạng… / FC Cop… 0 : 0 Brondby" có **viền trắng rõ ràng**.
- Detector báo màu viền "không chuẩn" nhưng ảnh cho thấy viền trắng đúng chuẩn KL5. 2 LOW này là lỗi đọc của detector, không phải lỗi UI.

### Nhóm B — 1 MEDIUM "tên giải đấu tiếng Anh" (bước 20): ARTIFACT (phán xét quá chặt)
- `step_020` cho thấy tên giải là hỗn hợp: "Serie A", "TUR D1", "HOL D1" xen với "Giải Ngoại hạng…", "Giao hữu Quốc tế" (tiếng Việt).
- "Serie A" là tiếng Ý, "Ligue 1" tiếng Pháp, "Bundesliga" tiếng Đức — **tên riêng chính thức của giải**, truyền thông Việt Nam cũng gọi như vậy, không có bản dịch tiếng Việt tương đương. "HOL D1 / TUR D1 / RUS D1" là mã viết tắt từ nguồn dữ liệu.
- Ghi nhận nhỏ (không phải defect): cách đặt tên không nhất quán giữa các nguồn (có giải tiếng Việt, có giải mã tắt). Không nên sửa "Serie A" thành tiếng Việt.

### Nhóm C — 1 MEDIUM "mất focus sau khi nhấn BACK" (bước 29): THẬT (có sắc thái)
- Timeline: bước 28 focus đang ở `backBtn` (viền WHITE); bước 29 sau 1 lần BACK: `FOCUS: NONE`, OSD biến mất, **vẫn ở PlayerActivity**, video bóng đá phát toàn màn hình không OSD (`step_029`).
- Agent phải dùng SWITCH_TAB (bước 30) để thoát về MainActivity. Vậy: **BACK đơn không thoát player** — nó chỉ ẩn OSD và làm mất focus, người dùng không còn dấu hiệu nào trên màn hình.
- Sắc thái: đây có thể là thiết kế 2 nấc (BACK ẩn OSD → BACK nữa mới thoát; bằng chứng: bước 93 và 106 dùng DOUBLE_BACK thì thoát được). Dù là thiết kế hay lỗi, việc BACK làm mất focus mà không để lại dấu hiệu nào là một khoảng trống trải nghiệm thật.

### Nhóm D — 2 MEDIUM "kẹt focus tại iptvGroupList khi bấm DPAD_UP" (bước 68–69): THẬT
- Timeline: bước 68 (DPAD_UP) và 69 (DPAD_DOWN) focus đều đứng yên ở `iptvGroupList#[112,748][986,832]`, `has_ring: False`, không di chuyển lên Hero Preview. `step_069` cho thấy màn hình IPTV EPG (VTV Cần Thơ, lưới kênh VTV1/VTV2/VTV3 HD) **không có viền focus nào nhìn thấy được**.
- Sắc thái: không phải kẹt hoàn toàn — bước 70 bấm OK thì focus chuyển sang `cardIptvRoot` (VTV1 HD). Vấn đề thật là: (1) DPAD_UP/DOWN không rời được khỏi group list; (2) focus đang ở đâu cũng không nhìn thấy được. Gợi ý sửa của AI (kiểm tra `nextFocus`/thứ tự focus trong layout) là hợp lý.

### Nhóm E — 16 HIGH "mất focus trong PlayerActivity" (bước 87–94, 102–109, 112): PHẦN LỚN LÀ PHÓNG ĐẠI — quan sát detector đúng, kết luận về ảnh hưởng sai
- **Phần đúng:** timeline ghi `FOCUS: NONE` nhất quán ở mọi bước trong PlayerActivity, và không có view Android nào giữ focus. Điều này có vẻ đúng ở tầng Android — player dường như tự vẽ trạng thái chọn (custom selection) thay vì dùng focus của hệ thống.
- **Phần sai (bằng chứng từ ảnh):** viền trắng **di chuyển được giữa các nút OSD** qua các bước: bước 87 → CÀI ĐẶT; 88 → QUAY LẠI (pill); 89/90 → PIP; 102/108/112 → CÀI ĐẶT. Video phát và tua được: 01:36 → 03:11 → 05:01 → 06:46 → 12:16 (lưu resume) → 14:00 → 21:30 → 24:29. OSD tự ẩn khi không thao tác (bước 93, 106: video toàn màn hình, không OSD — hành vi bình thường). Thoát được bằng DOUBLE_BACK (93→94, 106→107: quay về MainActivity, focus về `btnHeroPlay`).
- Vậy các kết luận "không thể thao tác D-pad tua thời gian", "không thể thoát bằng BACK" **không đúng với những gì ảnh cho thấy**. Mức HIGH cho cả 16 finding là không justified. Vấn đề thật nằm ở tầng triển khai (player không dùng Android focus — cần dev xác nhận) với ảnh hưởng tới người dùng thấp, vì chỉ báo chọn vẫn di chuyển và hoạt động được. Xếp lại tối đa MEDIUM/LOW cho khoảng trống triển khai này, không phải 16 lỗi HIGH.
- Lưu ý: ảnh 11 (mission IPTV player) cho thấy pill QUAY LẠI có viền trắng trong khi detector báo NONE — cùng một hiện tượng: viền trắng trên OSD không đồng nhất với Android focus.

### Nhóm F — 4 MEDIUM "mất focus trong dialog lỗi PlayerActivity" (bước 97–100): PHẦN LỚN LÀ PHÓNG ĐẠI
- Dialog "Lỗi Phát Luồng Video / Stream lỗi: ERROR_CODE_DECODING_FAILED" với 3 nút THỬ LẠI / QUAY LẠI / BÁO LỖI. Viền chọn **di chuyển được giữa các nút**: bước 97 → THỬ LẠI (viền trắng); 98 → THỬ LẠI (nền đậm, trạng thái đã chọn); 100 → QUAY LẠI (viền trắng); 110 → QUAY LẠI (viền trắng).
- Phát lại **hồi phục được sau lỗi**: 12:32 (lỗi) → 14:00 → 21:30 → 24:29 đang phát. Tức nút THỬ LẠI/QUAY LẠI hoạt động được qua D-pad.
- Chính finding 18 cũng tự thừa nhận "nút QUAY LẠI có vẻ có viền focused" — AI đã thấy mâu thuẫn giữa detector (FOCUS: NONE) và ảnh nhưng vẫn ghi defect. Kết luận: giống nhóm E — detector đúng ở tầng Android, kết luận "không thể thao tác D-pad" sai theo ảnh.

### Nhóm G — 1 LOW "ERROR_CODE_DECODING_FAILED trên emulator x86" (bước 110): LỖI CÓ THẬT, NHƯNG NGUYÊN NHÂN CHƯA CHỨNG MINH ĐƯỢC
- Dialog lỗi xuất hiện **2 lần** trong phiên: ~12:32 (bước 97–100) và ~22:50 (bước 110). Đây là lỗi phát thật, không phải artifact.
- Tuy nhiên chi tiết finding ghi "thiếu codec HEVC/H.264 trên emulator x86" là **không khớp với ảnh**: cùng một luồng đã phát được ~11 phút trước lần lỗi đầu (01:36 → 12:32) và ~8 phút nữa trước lần lỗi hai (14:00 → 22:50) — giải mã H.264 rõ ràng hoạt động. Lỗi mang tính từng đoạn (segment hỏng hoặc decoder vấp ở đoạn đổi tham số) chứ không phải thiếu codec hoàn toàn.
- Nguyên nhân (đoạn stream hỏng hay decoder emulator) **không xác định được từ ảnh** — cần kiểm tra trên thiết bị thật. Không phải lỗi logic của app: app xử lý đúng (hiện dialog lỗi rõ ràng + nút THỬ LẠI, và phát lại được sau đó).

### Tổng kết Phần 3
| Nhóm | Số lượng | Phán quyết |
|---|---|---|
| A. Viền focus LOW (bước 9, 11) | 2 | ARTIFACT — viền trắng thấy rõ trong ảnh |
| B. Tên giải tiếng Anh (bước 20) | 1 | ARTIFACT — "Serie A/Ligue 1/Bundesliga" là tên riêng |
| C. Mất focus sau BACK (bước 29) | 1 | THẬT — BACK đơn ẩn OSD + mất focus, phải DOUBLE_BACK/SWITCH_TAB mới thoát |
| D. Kẹt focus IPTV (bước 68–69) | 2 | THẬT — UP/DOWN không rời group list, không thấy viền focus |
| E. Mất focus PlayerActivity HIGH | 16 | PHÓNG ĐẠI — FOCUS: NONE có thể đúng ở tầng Android, nhưng viền chọn vẫn di chuyển, tua/phát/thoát đều hoạt động |
| F. Mất focus dialog lỗi | 4 | PHÓNG ĐẠI — viền chọn di chuyển giữa các nút, phát lại hồi phục được |
| G. ERROR_CODE_DECODING_FAILED | 1 | LỖI THẬT, nguyên nhân CHƯA RÕ (không phải thiếu codec hoàn toàn) |

**Điểm 0/100 lại gây hiểu lầm** như lượt trước: 16/16 check pass, và 27 finding gộp lại chỉ còn ~4 vấn đề thật (C, D, E-phần-triển-khai, G), trong đó không có lỗi nào khiến player không dùng được.

---

## Phần 4 — Kiểm tra riêng bản redesign (KL5 / FPT-style)

- **Bảng màu KL5: ĐÚNG trên màn hình.** Nền than ấm xuyên suốt; đỏ chỉ dùng cho badge LIVE / TRỰC TIẾP, nút XEM NGAY, nút TÌM KIẾM; nav chỉ chữ; focus viền trắng. Không thấy cam #FF6500 cũ, không thấy cyan cũ. Viền vàng đồng trên pill "Tất Cả" là trạng thái đang chọn (brass), không phải cam cũ. Badge SOCO (xanh ngọc) và COLA (đỏ hồng) là badge nhận diện nguồn phát (nội dung), không phải màu chrome UI.
- **Hàng điều khiển dưới của player: ĐÃ XUẤT HIỆN LẦN ĐẦU** (lượt trước không quan sát được). Ảnh 15 + step_087–112 cho thấy đầy đủ: seekbar có thời gian 2 đầu + dãy nút PHÁT | TUA -10S | TUA +10S | TẬP TRƯ… | TẬP TIẾP | DANH SÁ… | CÀI ĐẶT. Top bar đúng kiểu FPT (QUAY LẠI trái, tiêu đề phải, PIP/TÙY CHỌN). Video phát thật, phụ đề tiếng Việt hiển thị.
- **Bo góc 4dp, không gradient/glow: ĐÚNG.** Thẻ bo góc nhẹ, focus chỉ là viền trắng 1dp.
- **Focus 1.13x/500ms:** không đo được hệ số scale từ ảnh tĩnh; viền trắng xuất hiện rõ khi focus trên thẻ/hàng/nút (ảnh 02–05, 07, 09, 13–15, 17, step_087–112).
- **Hero banner:** ảnh 02 cho thấy hero trận tâm điểm với ảnh nền thật, nút XEM NGAY đỏ, "[MENU] ĐỔI LUỒNG" — render tốt, ngoại trừ chữ trong ảnh cover va chạm với tiêu đề đè lên (xem R6).

---

## Phần 5 — Danh sách lỗi thật (xếp theo mức độ)

| # | Mức | Lỗi | Bằng chứng |
|---|---|---|---|
| R1 | HIGH (cũ, chưa sửa) | **Dialog THÔNG BÁO kẹt ở cold start:** chữ bị cắt, không thấy nút đóng/focus (bản sửa nằm trong nhánh FPT-home, chưa lên main) | 01, vf_001s |
| R2 | MEDIUM (mới) | **BACK đơn trong PlayerActivity chỉ ẩn OSD + làm mất focus, không thoát** — người dùng không còn dấu hiệu nào trên màn hình; phải DOUBLE_BACK hoặc SWITCH_TAB mới thoát | step_028→029→030; step_093, 106 |
| R3 | MEDIUM (mới) | **Kẹt focus ở IPTV EPG:** DPAD_UP/DOWN không rời khỏi `iptvGroupList`, không thấy viền focus trên màn hình IPTV | step_068–069, ảnh 11 |
| R4 | MEDIUM (mới, tầng triển khai) | **PlayerActivity không dùng Android focus (FOCUS: NONE ở mọi bước)** — player tự vẽ trạng thái chọn. Người dùng vẫn thao tác được (viền chọn di chuyển, tua/thoát hoạt động) nên ảnh hưởng thấp, nhưng cần dev xác nhận và gán initial focus cho OSD | step_087–112 |
| R5 | LOW (mới) | **Lỗi giải mã ERROR_CODE_DECODING_FAILED xuất hiện 2 lần giữa lúc phát** (12:32, 22:50); nguyên nhân chưa rõ (đoạn stream hay decoder emulator) — cần kiểm tra trên thiết bị thật | step_097–100, 110 |
| R6 | LOW | **Lặt vặt UI:** nhãn nút OSD bị cắt ("TẬP TRƯ…", "DANH SÁ…"); phụ đề đè lên seekbar; chữ trong ảnh cover hero va chạm tiêu đề trận; tên đội cắt ngắn trên thẻ nhỏ ("Vi…", "S.S.C…"); số lượt xem lạ ("9558,9K xem"); dialog chọn phòng (ảnh 08) không thấy rõ focus | ảnh 15, 02, 03, 08; step_011 |

**Đã hết so với lượt trước (42470778044):** màn hình đen mission IPTV (ảnh 10 render được + dialog M3U + bàn phím); kho phim không tải được (ảnh 12–14 tải đủ, poster thật); logo đội xám trống (ảnh 05/07/09 logo thật đã tải); 3 thẻ HomeHub trống (không quan sát được trong lượt này — ảnh 07 là màn lịch đấu, không thấy Hub; không kết luận); VOD seek/resume (ảnh 14: resume 12:16 đã lưu).

**Ghi chú bao phủ:** phiên này chỉ bao phủ **5/7 tab** — Tab 3 (Tìm Kiếm) và Tab 4 (Cài Đặt) có 0 thao tác, dù 16/16 mission vẫn báo pass. Lượt trước bao phủ 7/7. Đây là điểm yếu của phiên này, không phải của app.

**Không phải lỗi (đã kiểm chứng):** viền focus trắng hoạt động đúng trên màn hình thường (ảnh 02–05, 07, 09, 13–15, 17, step_087–112); player phát video thật và tua/thoát được; dialog lỗi có nút chọn di chuyển được; sau D-pad chaos app không crash và giữ focus (ảnh 17); không còn cam/cyan cũ, không gradient/glow.

---

## Kết luận

- **Đã xem: 48 ảnh/frame** (17 mission + 12 frame video + 19 ảnh step).
- **Nemotron lần này có đáng tin không? Đáng tin một nửa.** Nó chạy thật (OPENAI 128/128 bước), mô tả đúng những gì trên màn hình, trích đúng dữ liệu detector (FOCUS: NONE, tên view, tọa độ), và thậm chí tự nhận ra mâu thuẫn ở finding 18. Nhưng nó **tin detector hơn tin ảnh**: khi detector báo FOCUS: NONE, nó kết luận "không thể thao tác" dù ảnh cho thấy viền chọn di chuyển, video tua được và thoát được — tạo ra 16 finding HIGH + 4 MEDIUM phóng đại cho một player thực ra vẫn dùng được. Nó cũng ghi 2 LOW sai hẳn (viền trắng nhìn thấy rõ) và 1 MEDIUM quá chặt (tên giải là tên riêng). **Kết luận: dùng nemotron để mô tả màn hình và đọc detector thì tốt; nhưng mức độ nghiêm trọng (severity) và kết luận về ảnh hưởng thì phải có người kiểm chứng lại bằng ảnh — không nên tin điểm 0/100 theo nghĩa đen.**
- **Verdict chung:** phiên này thực ra **khỏe hơn lượt trước** (kho phim tải được, IPTV không đen, VOD seek/resume hoạt động, hàng điều khiển dưới của player đã xuất hiện và hoạt động) nhưng điểm vẫn 0/100 vì cách tính điểm và cách AI phóng đại nhóm focus của player. Vấn đề thật cần sửa: BACK đơn trong player (R2), kẹt focus IPTV (R3), gán Android focus cho OSD (R4), và dialog THÔNG BÁO cũ (R1 — đang sửa trong nhánh FPT-home).

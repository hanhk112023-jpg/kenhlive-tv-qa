# Đánh giá trực quan (Visual Review) — QA run 42489380818

**Nhánh:** `redesign/fpt-home-landing` · **Commit:** `0c53f9c` (timeout QA 150 phút)
**Kết quả job:** SUCCESS · **Thời gian chạy:** 3168 s (~53 phút) · **Điểm:** 55/100
**Checks:** 16/16 · **Missions:** 16/16 · **Findings:** 9 (tất cả MEDIUM, không có HIGH)
**Steps:** 129 (128 OPENAI/nemotron + 1 LOCAL_REFLEX tại step 63)
**Video:** `full_qa_tour.mp4` — 5,3 MB, **chỉ 174,9 s** (xem §6)

**Phạm vi bài đánh giá này:** đã đọc trực tiếp **17/17 ảnh mission** (`01`–`17`),
**11 ảnh step** (`step_027`, `step_030`, `step_035`, `step_062`, `step_063`, `step_073`,
`step_082`, `step_087`, `step_089`, `step_095`, `step_104`),
**4 frame video** (0 s, 60 s, 120 s, 170 s),
`qa_report.json`, `qa_session_summary.md` và toàn bộ `qa_session.json` (129 bước timeline).
Không suy đoán nội dung ngoài những gì nhìn thấy trong ảnh/timeline.

---

## 1. Từng ảnh mission (01–17)

### 01 — `01_cold_start.jpg` — Cold start, dialog THÔNG BÁO
Màn hình khởi động lạnh: dialog **THÔNG BÁO** (nhóm Telegram @kenhlivetv, QR code) phủ giữa màn hình.
Nút **ĐÃ HIỂU / ĐÓNG** (đỏ) có **viền trắng rõ ràng** — focus đã rơi đúng vào nút đóng.
Nút VÀO NHÓM TELEGRAM bên cạnh cũng hiển thị đầy đủ. Phía sau dialog mờ đi là rail trái
(TRANG CHỦ, TRUYỀN HÌNH, KHO PHIM, LỊCH TRÌNH, TÌM KIẾM, CÀI ĐẶT) và hero bên phải
(có badge LIVE). **R1 (dialog kẹt focus ở lần chạy 42470778044) đã sửa xong — xác nhận.**
Tồn tại nhỏ: dòng cuối thân dialog ("Cảm ơn bạn đã luôn đồng…") vẫn bị cắt nửa dòng ở mép dưới
của vùng cuộn — giống hệt lần chạy trước (D9 cũ, mức cosmetic).

### 02 — `02_mission_cold_start.jpg` — Player đang phát trực tiếp
Ảnh kết thúc mission cold start **không phải màn hình chính mà là PlayerActivity đang phát
trận Sunderland vs Chelsea** (Ngoại Hạng Anh, BLV TAP, logo SUTONGTV): video phát thật,
cầu thủ đang di chuyển. Top bar: nút **◀ QUAY LẠI** có viền trắng (đang focus), **PIP**,
**TÙY CHỌN** bên trái; tiêu đề "THỂ THAO · Sunderland vs Chelsea · BLV TAP" + badge
"NGOẠI HẠNG ANH" bên phải. **Không thấy hàng điều khiển dưới (seekbar/nút bấm)** — OSD dưới
đã tự ẩn, chỉ còn top bar. Lưu ý: nút QUAY LẠI đè lên score bug của luồng ("SUN…CHE" lấp ló
sau nút) — va chạm giữa OSD của app và đồ họa của luồng, mức cosmetic.
Nhận xét về mission shot: mission cold start kết thúc trong player vì AI đã bấm OK trên hero
— ảnh mission không phản ánh màn hình "cold start" mà là trạng thái cuối mission.

### 03 — `03_mission_sports_multi_source.jpg` — Home Hub, rail focus TRUYỀN HÌNH
Màn hình chính FPT-style: rail trái hiện rõ, mục **TRUYỀN HÌNH có viền trắng** (đang focus).
Hero banner: Sunderland vs Chelsea, badge TRỰC TIẾP, "Ngoại Hạng Anh", 454,3K lượt xem,
nút **[OK] XEM NGAY** đỏ, **[MENU] ĐỔI LUỒNG**. Dưới banner là hàng **ĐANG PHÁT** với
2 thẻ trận (Ngoại Hạng Anh / SOCO / LIVE).
**D1 CÒN NGUYÊN:** ảnh bìa của banner chứa chữ quảng cáo lớn "BLV TAP" / "KINH NGHIỆM" /
"LÀ ĐẲNG CẤP" đè lên chữ UI — đồng hồ "21:34" và ngày "Chủ Nhật, 08/11/2026" bị chữ bìa
che một phần, chữ bìa bị cắt ở mép phải. Logo "KENHLIVE TV / CỔNG GIẢI TRÍ TRỰC TUYẾN"
hiện ở đầu banner.

### 04 — `04_mission_sports_room_picker.jpg` — Dialog chọn phòng (Sunderland vs Chelsea)
Dialog "Sunderland vs Chelsea — Ngoại Hạng Anh · 6 phòng live": các phòng BLV TAP (最高等级),
ZIZOU (最高等级), TẠ BIÊN GIỚI (Lv.6), BLV Cù Cải (Lv.7) kèm lượt xem, badge SOCO xanh lá.
Dialog render sạch, nền charcoal ấm. Lưu ý: tên phòng chứa chữ Trung "(最高等级)" — dữ liệu
nguồn Socolive, không phải lỗi UI của app. Không thấy rõ viền focus trên hàng phòng nào
(hàng đầu tiên không có viền trắng phân biệt được). Dialog bị cắt ở dưới (phòng thứ 5
lấp ló) — danh sách cuộn được, bình thường.

### 05 — `05_mission_sports_data_accuracy.jpg` — Home Hub cuộn xuống, thẻ trận focus
Home hub đã cuộn xuống: hero Sunderland vs Chelsea ở trên (D1 vẫn thấy — chữ bìa
"KINH NGHIỆM / LÀ ĐẲNG CẤP" che mất một phần số lượt xem "442,8K"), dưới là hàng
**"Socolive TV · Trực Tiếp & Lịch Đấu"** (10 trận) với các thẻ trận có viền trắng rõ
trên thẻ giữa **"Ipswic… 0:3 Bourne…"** (đang focus). Logo đội tải được (Ipswich,
Bournemouth, Brentford), tỉ số thật (Brentford 3:2, Ipswich 0:3). **Điểm lạ:** thẻ
"Elche CF **8:5**" — tỉ số không hợp lý cho bóng đá (xem N1, §8).
Hàng cuộn ngang, thẻ bị cắt ở mép trái/phải theo kiểu edge-peek (by design).

### 06 — `06_mission_player_streaming_and_controls.jpg` — TRÙNG 05
**File này giống hệt 05 (cùng sha256).** Ảnh mission của "player streaming" không hề
chụp player — nó là ảnh màn hình chính, trùng với ảnh mission 05. Đây là quirk của harness
(ảnh mission chụp ở cuối mission, sau khi AI đã quay về home), không phải lỗi app —
nhưng làm giảm giá trị bằng chứng của mission shot. Trạng thái player thực tế trong
mission này phải xem ở step shot (step_027, step_030 — xem §2).

### 07 — `07_mission_home_hub_3_cards_and_canva_logos.jpg` — Home Hub, rail focus KHO PHIM
Rail trái: **KHO PHIM có viền trắng** (đang focus). Hero Sunderland vs Chelsea, D1 vẫn còn
(chữ bìa "BLV TAP" đè lên đồng hồ "21:45" và ngày). Hàng ĐANG PHÁT: 2 thẻ
"Sunder… VS Chelsea" (454,3K xem, 6 phòng) và "Crystal… VS Liverpool" (392,4K xem, 6 phòng).
**Lưu ý:** logo Sunderland trên thẻ trận hiển thị như một **hình chữ nhật đỏ** (không phải
huy hiệu đội) trong khi logo Chelsea/Crystal Palace/Liverpool tải bình thường — giống hệt
ảnh 035 (xem N2, §8). Tên đội bị cắt ngắn "Sunder…", "Crystal…" là bình thường theo chiều
rộng thẻ. **Không thấy hàng portal (THỂ THAO / TRUYỀN HÌNH / PHIM TRUYỆN) trong ảnh này**
— nó nằm dưới fold, AI không cuộn tới (xem D3, §7).

### 08 — `08_mission_schedule_epg_and_fixture_tap.jpg` — Dialog chọn phòng (Brighton vs Brentford)
Dialog phòng cho trận Brighton Hove Albion vs Brentford ("Ngoại Hạng Anh · 6 phòng live"):
TYPN, BLV TOMIA, HẢI THANH, A MÂN — **tất cả đều "0 lượt xem · LIVE"** (hợp lý cho trận
ít người xem hơn, hoặc số liệu chưa tải). Phía sau dialog là màn hình Lịch thi đấu với
các thẻ trận và avatar phòng (+2). Không thấy viền focus rõ trên hàng phòng nào.

### 09 — `09_mission_sidebar_rail_full_traversal.jpg` — Tab Lịch trình, rail focus CÀI ĐẶT
Màn hình Lịch trình: danh sách trận 21:00, tất cả badge "Live" đỏ, tên đội + giải đấu
("Ngoại Hạng Anh", "Serie A"), avatar các phòng + "+2". **Rail: mục CÀI ĐẶT có viền trắng
rõ ràng** — rail traversal hoạt động, focus trên rail nhìn thấy được.
**Khiếm khuyết mới (N3):** tên đội bị ngắt giữa từ — "Brig ht…", "Crys tal…", "Ips wi…",
"Sun de…" — cột tên đội quá hẹp nên text wrap giữa từ (riêng "Genoa vs AC Milan" hiển
thị đủ vì ngắn hơn). Mức LOW, chỉ ở tab Lịch trình.

### 10 — `10_mission_iptv_categories_and_favorites.jpg` — Lại dialog chọn phòng
Ảnh mission IPTV **không chụp màn hình IPTV** — lại là dialog chọn phòng Sunderland vs
Chelsea (BLV TAP giờ là 100,4K lượt xem — số liệu thay đổi theo thời gian nên đây là
ảnh chụp sau, không phải file trùng; khác với cặp 05/06). Màn hình IPTV thực tế phải xem
ở step_062 (§2). Mission shot này không có giá trị kiểm chứng IPTV.

### 11 — `11_mission_iptv_epg_and_zapping_player.jpg` — Home Hub, heroPlay focus
Hero Sunderland vs Chelsea, nút **[OK] XEM NGAY có viền trắng rõ** (focus heroPlay nhìn
thấy được). D1 vẫn còn (chữ bìa che số lượt xem "445,7K"). Hàng Socolive: thẻ
"Crystal… **2:8** Liverpo…" và "Bright… 0:0 Brentf…".
**D6 CÒN NGUYÊN:** trên thẻ Brighton vs Brentford, ở vị trí badge SOCO là một **pill xám
hiển thị "0"** (cạnh badge LIVE) — chip thông tin xoay vòng đang render giá trị thiếu
thành "0". Thẻ Crystal Palace thì có badge SOCO xanh bình thường.

### 12 — `12_mission_phim_nguonc_and_categories.jpg` — TRÙNG 11
**File giống hệt 11 (cùng sha256).** Ảnh mission "Phim NguonC" không hề có nội dung phim
nào — là ảnh home hub trùng với mission 11. Phim (poster, danh mục NguonC) không xuất hiện
trong bất kỳ ảnh mission nào của lần chạy này (xem §9).

### 13 — `13_mission_phim_episode_picker_and_favorite.jpg` — Home Hub, hero đã xoay trận khác
Hero giờ là **Real Sociedad vs Rayo Vallecano** (SPA D1, BLV A BỆU, 116,3K) — hero tự
xoay sang trận khác (auto-rotate hoạt động). [OK] XEM NGAY có viền trắng. Dưới là thẻ
"Sunder… 3:2 Chelsea" và "Crystal… 2:8 Liverpo…". Mission "episode picker" kết thúc ở
home hub — không thấy hộp chọn tập hay nội dung phim nào.

### 14 — `14_mission_vod_player_seek_and_resume.jpg` — Lại dialog chọn phòng
Dialog phòng Sunderland vs Chelsea (BLV TAP 80,5K — số lượt xem dao động theo thời gian:
97,8K → 100,4K → 80,5K qua các ảnh, là dữ liệu live bình thường). Mission "VOD seek/resume"
không có ảnh nào chụp WebPlayer — **WebPlayerActivity không mở lần nào trong cả phiên**
(0 bước trong timeline, xem §9).

### 15 — `15_mission_player_settings_dialog.jpg` — Dialog chọn phòng (Genoa vs AC Milan)
Dialog phòng cho Genoa vs AC Milan (Serie A, 4 phòng live): BLV GIÓ (Lv.3) 26,8K,
BLV RYO (Lv.2) 26,3K, BLV VIP (Lv.4) 26,3K, BLV CHIVAS (Lv.3) 26,2K. Mission "player
settings dialog" không có ảnh nào chụp dialog cài đặt trong player — player chỉ xuất hiện
ở các step 97/106/111 trong timeline.

### 16 — `16_mission_search_and_settings_feedback.jpg` — Home Hub, D1 nặng nhất
Hero Genoa vs AC Milan với ảnh bìa là **poster quảng cáo cá cược** "CHƠI KÈO CÙNG BLV GIÓ /
PHÂN TÍCH CHUẨN – SOI KÈO ĐỈNH – CHIẾN THẮNG! / ĐỒNG HÀNH CÙNG BLV GIÓ / CHINH PHỤC MỌI
KÈO ĐẤU!" — chữ bìa chiếm gần hết banner, đè lên đồng hồ "22:15", ngày "Chủ Nhật,
08/11/2026", "30/09 ÂL · Át Tỵ" và che một phần số lượt xem "105,8K". Đây là ví dụ D1
tệ nhất trong lần chạy. [OK] XEM NGAY có viền trắng. **Không thấy màn hình Tìm kiếm hay
Cài đặt nào** — mission search/settings kết thúc ở home hub.

### 17 — `17_mission_dpad_chaos_stress_and_recovery.jpg` — Home Hub, thẻ trận focus
Hero Genoa vs AC Milan (D1). Hàng Socolive: thẻ **"Real S… 0:0 Rayo V…" có viền trắng**
(đang focus), badge SPA D1, "Hiệp 2: 60'", LIVE — và **lại pill xám "0"** (D6).
Các thẻ khác: "1:10 Bourn…" (Ipswich 1:10 Bournemouth) và "FC Köln 2:7" — tỉ số không
hợp lý cho bóng đá (xem N1, §8). Sau stress test, app vẫn ở home hub, không crash,
không màn hình đen — recovery tốt.

---

## 2. Ảnh step — bằng chứng cho các finding

### step_027 — Player đang phát (Ipswich vs Bournemouth, phòng CURRY)
PlayerActivity: trận Ipswich vs Bournemouth, tỉ số 0-3, "Hiệp 1: 34'". Khung hình là
đồ họa chuyển cảnh/replay của Premier League (logo sư tử quét ngang) — không phải
khung hình đứng hay lỗi. Top bar: **◀ QUAY LẠI focus (viền trắng)**, PIP, TÙY CHỌN;
tiêu đề "THỂ THAO · Ipswich Town vs Bournemouth AFC · CURRY / NGOẠI HẠNG ANH · TRỰC TIẾP
· 0 - 3 · Hiệp 1: 34'". Không có hàng điều khiển dưới (OSD dưới tự ẩn).
Timeline step 27: `is_playing: true, motion_delta: 6.86` — video đang phát.

### step_030 — Player đang phát, bóng lăn thật (Ipswich vs Bournemouth)
Cùng trận, khung hình khác: cầu thủ dàn đội hình, bóng đang lăn, tỉ số 0-3, Hiệp 1: 34'.
**Video phát bình thường, có chuyển động thật.** Timeline: `is_playing: true,
motion_delta: 6.7`. Đây là bằng chứng gần nhất cho finding "motion 0.00%" ở step 31
(xem §4, finding #2).

### step_026 và step_031 — KHÔNG CÓ ẢNH
Hai bước ghi defect phát video (step 26 ExoPlaybackException, step 31 motion 0.00%)
**đều không có file ảnh** (harness không chụp ở bước WAIT / bước ghi defect).
Mọi kết luận về 2 finding này chỉ dựa vào timeline + logcat + ảnh step lân cận,
không có ảnh trực tiếp tại thời điểm defect — xem phán quyết ở §4.

### step_035 — Home Hub, heroPlay focus rõ
Hero Sunderland vs Chelsea, **[OK] XEM NGAY viền trắng rõ**. ĐANG PHÁT: "Sunder… VS
Chelsea" (logo Sunderland lại là **hình chữ nhật đỏ**, xem N2), "Crystal… VS Liverpool".
D1 vẫn còn. Focus trên heroPlay nhìn thấy được, không có vấn đề gì ở trạng thái chưa cuộn.

### step_062 — Màn hình IPTV thật (duy nhất thấy rõ IPTV)
Tab Truyền hình render tốt: hero là **video live đang phát** (VTV Cần Thơ, "ĐÀI TRUYỀN
HÌNH VIỆT NAM (VTV)", badge TRỰC TIẾP đỏ + FHD, "Đang phát trực tiếp từ Đài Truyền
hình Quốc gia", hướng dẫn "Bấm [OK] để xem toàn màn hình · Bấm [Lên/Xuống] để duyệt kênh"),
tile logo VTV hồng, chip lọc "Yêu Thích" / "VTV" (đang chọn) / ô "Tìm kênh TV…" /
nút "THÊM M3U". Dưới là lưới kênh: VTV Cần Thơ, VTV1 HD, VTV10, VTV2 HD, VTV3 HD
kèm "Việt Nam" và giờ chương trình ("21:40 · Đi cùng…", "21:45 · 360 độ…").
**D4 CÒN:** timeline nói focus là `cardIptvRoot#[530,852][1046,1080]` (thẻ ở hàng dưới,
đã bị cắt nửa ở mép màn hình) nhưng **không thấy viền focus nào trên thẻ kênh** —
trong khi mục TRANG CHỦ trên rail lại có viền trắng (đây là chỉ báo tab đang chọn,
không phải focus). Focus trên lưới kênh IPTV vẫn mờ/không phân biệt được.
**D5 CÒN:** hàng kênh cuối bị **cắt ngang giữa thẻ** ở mép dưới màn hình (chữ
"VTV Cần Thơ / Việt Nam" bị cắt dở). IPTV hero lần này KHÔNG trống (có video live),
khác với lần chạy trước.

### step_063 — Về lại Home Hub sau IPTV
Hero Sunderland vs Chelsea, [OK] XEM NGAY focus, D1, hàng Socolive "12 trận",
thẻ "0:0 Brentf…" **lại có pill xám "0"** (D6), thẻ "Elche… **13:8** Real B…" (N1),
"SPA D1 / Hiệp 2: 91' / LIVE".

### step_073 — Home Hub (mission Phim)
Giống hệt ảnh 11/12 (cùng sha256). Hero Sunderland vs Chelsea, XEM NGAY focus,
thẻ "Crystal… 2:8 Liverpo…" + pill "0" trên thẻ Brighton. Mission Phim nhưng màn hình
là home hub — không có poster phim.

### step_082 — Home Hub đã cuộn sâu (bằng chứng focus-trap #1)
Trang đã cuộn qua hero: hàng "Socolive TV · Trực Tiếp & Lịch Đấu" ở trên (bị cắt nửa)
và hàng **"ColaTV · Trực Tiếp & Lịch Đấu" (90 trận)** ở dưới. Thẻ "Sunder… 3:2 Chelsea"
**có viền trắng rõ** (focus cardRoot). Timeline step 82: focus
`cardRoot#[511,57][1226,477]` sau 2 lần DPAD_LEFT không đổi focus — khớp với ảnh
(focus vẫn ở thẻ trên cùng). Số lượt xem "6844,4K xem" (6,8 triệu) và "2641,6K xem"
trên hàng ColaTV là không hợp lý (xem N1). Tỉ số "2:8", "1:8" lại xuất hiện.

### step_087 và step_089 — GIỐNG HỆT NHAU (bằng chứng focus-trap)
**Hai file giống hệt nhau (cùng sha256)** dù giữa chúng có 2 lần bấm DPAD_LEFT
(step 87 và 88). Màn hình: hero **Genoa vs AC Milan** (Serie A, BLV GIÓ, 105,2K),
nút **[OK] XEM NGAY có viền trắng** (focus heroPlay), rail trái không có mục nào
được focus. Dưới là hàng Socolive ("Sunder… 3:2 Chelsea", "Crystal… 2:8 Liverpo…").
**Đây là bằng chứng trực quan mạnh nhất: DPAD_LEFT từ heroPlay không làm gì cả —
màn hình không thay đổi, focus không sang rail.** D1 vẫn còn (chữ bìa "BLV GIÓ"
che số lượt xem).

### step_095 — Hero Genoa, focus mơ hồ kép
Hero Genoa vs AC Milan, [OK] XEM NGAY và thẻ "Sunder… 3:2 Chelsea" bên dưới đều
có vẻ có viền trắng — timeline nói focus là heroPlay nhưng ảnh cho thấy cả thẻ trận
cũng có viền. Có thể do thời điểm chụp ảnh và thời điểm đọc focus lệch nhau
(harness chụp sau khi action OK đã xử lý). Viền focus trên heroPlay ở ảnh này
không rõ bằng step_087 — ghi nhận là không nhất quán, không kết luận thêm.

### step_104 — Trạng thái y hệt step_095 (bằng chứng focus-trap)
Màn hình giống step_095: hero Genoa vs AC Milan, XEM NGAY, hàng Socolive.
Timeline step 104 ghi defect focus-trap tại heroPlay#[680,316][1126,413] sau nhiều
lần DPAD_LEFT. Ảnh xác nhận màn hình không đổi so với step_095 — LEFT vẫn không
đưa focus sang rail.

---

## 3. Video `full_qa_tour.mp4`

| Frame | Nội dung thấy được |
|---|---|
| 0 s (`f002`) | **Màn hình đen hoàn toàn** (app đang khởi động) |
| 60 s (`f060`) | Home hub hero Sunderland vs Chelsea, [OK] XEM NGAY focus (viền trắng), D1 rõ |
| 120 s (`f120`) | Dialog chọn phòng Sunderland vs Chelsea (BLV TAP 94,6K, ZIZOU 82,8K…) |
| 170 s (`f170`) | Player đang phát Sunderland vs Chelsea full-screen (OSD top bar, QUAY LẠI focus) |

**Kết luận video: video chỉ dài 174,9 s (ffprobe xác nhận) và chỉ bao phủ ~3 phút đầu
phiên — cold start → dialog → home hero → room picker → lần đầu vào player.
Không có video cho 50 phút còn lại của phiên (3168 s). Video toàn phiên KHÔNG tồn tại,
dù bản sửa video_recorder (merge chunk bằng re-encode + genpts, fallback chunk dài nhất)
đã có trong commit 15a986a. Không có file `concat.txt` trong artifact.
Nguyên nhân đã được xác định từ job log (Astra kiểm tra): CI không cài ffmpeg/ffprobe
(`qa-suite.yml` chỉ cài tesseract + pillow) nên mọi chunk đều probe 0.0 s ở bước dừng,
code fallback về chunk 1. Cần sửa: cài ffmpeg trong CI deps + hardening recorder
(nếu thiếu ffprobe thì fallback, không im lặng trả về chunk 1).**

---

## 4. Phán quyết 9 findings (trong `qa_report.json`)

Timeline dùng quy ước: **focus ghi ở step N là trạng thái TRƯỚC action của step N**;
action ở step N gây ra focus ở step N+1 (kiểm chứng: step 9 LEFT từ heroPlay →
step 10 focus nav_settings).

| # | Finding (step) | Phán quyết | Bằng chứng |
|---|---|---|---|
| 1 | ExoPlaybackException, "Đang tải lại…" (step 26) | **THẬT, nhưng nhất thời và đã tự hồi phục** — mức ảnh hưởng LOW-MEDIUM, không phải MEDIUM nặng | Logcat có `PLAYER_ERR: ExoPlaybackException` (trận Ipswich vs Bournemouth, phòng CURRY). Nhưng player đang phát ở step 27 (motion 6.86) và step 30 (motion 6.7, ảnh step_030 bóng lăn thật). Không có ảnh step_026 nên câu "màn hình hiển thị 'Đang tải lại…'" **không xác minh được**. Cùng họ với ERROR_CODE_DECODING_FAILED ở lần chạy 42473740761 — vấn đề độ tin cậy luồng/server, không phải UI. |
| 2 | Motion delta 0.00%, khung hình đứng (step 31) | **PHÓNG ĐẠI / KHÔNG XÁC MINH ĐƯỢC** | Không có ảnh step_031. Ảnh gần nhất step_030 (t=905 s) cho thấy video đang phát bình thường; step 32 AI đã về home (OK trên backBtn). Chỉ số motion 0.0 + `is_playing: false` có thể là lúc stream đệm/tạm dừng hoặc khung hình tĩnh của chương trình (ví dụ đồ họa chuyển cảnh ở step_027). AI viết "Screenshot thấy trận… đang phát (tỉ số 0-3)" nhưng không tồn tại screenshot step 31 — nhiều khả năng nó đã dùng lại ảnh step_030. Không đủ bằng chứng kết luận "đứng hình". |
| 3 | Focus trap tại cardRoot#[511,57] khi DPAD_LEFT (step 82) | **THẬT một phần — là cùng 1 root cause với #4–#9** | Timeline: step 80 LEFT → step 81 focus không đổi; step 81 LEFT → step 82 focus không đổi (cardRoot Sunderland). Ảnh step_082: focus vẫn ở thẻ trên cùng. Nhưng đây KHÔNG phải kẹt hoàn toàn: step 82 UP → step 83 focus đã di chuyển (sang cardRoot khác rồi lên heroPlay ở step 84–85). LEFT từ thẻ ở cột trái cùng không đi đâu là hành vi đúng (đã ở biên trái) — trừ khi nó phải sang rail. |
| 4 | Focus trap tại heroPlay#[680,294] khi DPAD_LEFT (step 89) | **THẬT** | step_087 ≡ step_089 (cùng sha256): 2 lần LEFT, màn hình không đổi, focus vẫn trên [OK] XEM NGAY, rail không được focus. |
| 5 | Focus trap tại cardRoot khi DPAD_LEFT (step 82, bản ghi trùng) | **TRÙNG LẶP của #3** — cùng step, cùng root cause, harness ghi 2 lần (1 "Deep Probe" + 1 "Tab 0 Sidebar"). | Như #3. |
| 6 | Focus trap tại heroPlay#[680,316] khi DPAD_LEFT (step 95) | **THẬT** | Timeline: step 87/88 LEFT → không đổi; step 92 LEFT → focus nhảy xuống cardRoot (chứ không sang rail); step 94 LEFT → không đổi. Ảnh step_095: màn hình không đổi. |
| 7 | Focus trap tại heroPlay khi DPAD_LEFT/DPAD_UP (step 95, bản ghi trùng) | **TRÙNG LẶP của #6** — cùng step, ghi 2 lần. | Như #6. |
| 8 | Focus trap tại heroPlay khi DPAD_LEFT (step 104) | **THẬT** | Timeline: step 100/101 LEFT từ heroPlay → không đổi (step 101→102 LEFT nhảy xuống cardRoot thay vì sang rail); step 104 ghi defect. Ảnh step_104: màn hình y hệt step_095. |
| 9 | (finding thứ 9 trong file — heroPlay/cardRoot, Deep Probe) | **TRÙNG LẶP** — 9 findings gồm 7 bản ghi về cùng 1 root cause focus-trap (các step 82/89/95/104, mỗi step bị ghi 1–2 lần dưới 2 area khác nhau). | Xem §5. |

**Tóm lại: 9 findings thực chất chỉ là ~3 vấn đề: (1) heroPlay LEFT không sang rail
(THẬT, 1 root cause bị đếm 7 lần); (2) ExoPlaybackException nhất thời (THẬT, nhẹ);
(3) motion 0.00% (KHÔNG XÁC MINH ĐƯỢC).**

---

## 5. Phán quyết quan trọng nhất: heroPlay có kẹt focus không?

**Kết luận: CÓ, nhưng hẹp và có điều kiện — không phải "kẹt toàn bộ", mà là
"đường LEFT từ heroPlay sang rail bị hỏng khi trang đã cuộn".**

Bằng chứng ủng hộ (THẬT):
- **6+ lần DPAD_LEFT từ heroPlay ở vị trí y≈294–316 (trạng thái đã cuộn) không lần nào
  sang được rail:** step 85→86, 87→88, 88→89, 92→93, 94→95, 100→101, 101→102.
  Hai cặp ảnh giống hệt nhau (step_087 ≡ step_089; trạng thái step_095 ≡ step_104)
  chứng minh phím LEFT không có tác dụng nhìn thấy được.
- Khi LEFT "có tác dụng", focus **nhảy xuống-thẳng thẻ trận bên dưới-trái**
  (`cardRoot#[511,626][1226,1046]`, step 85→86, 92→93, 101→102) thay vì sang
  `nav_phim#[0,272][440,392]` — dù tọa độ Y chồng chéo (heroPlay Y 316–413,
  nav_phim Y 272–392) như chính finding đã chỉ ra. FocusFinder đang chọn sai ứng viên.
- Rail vẫn hiển thị đầy đủ trong mọi ảnh — không phải rail bị ẩn.

Bằng chứng giới hạn (KHÔNG phải kẹt toàn bộ):
- **LEFT từ heroPlay VẪN sang được rail khi trang chưa cuộn:** step 9 LEFT từ
  `heroPlay#[680,691][1126,788]` → step 10 focus `nav_settings#[0,680][440,800]`.
  Sau đó rail traversal UP/DOWN hoạt động hoàn hảo (step 10–15:
  nav_settings → nav_search → nav_schedule → nav_phim → nav_iptv → nav_live;
  và step 50–55 tương tự). **Rail ↔ content không hỏng hoàn toàn.**
- **LEFT từ các phần tử khác sang được rail:** step 49 LEFT từ
  `schedCard#[470,0][1890,222]` → step 50 `nav_live`. Step 55 RIGHT từ nav_settings
  → schedCard (chiều ngược lại cũng hoạt động).
- **UP/DOWN từ heroPlay vẫn di chuyển focus** (sang các thẻ trận, step 83–85, 90–94),
  và OK vẫn mở được nội dung. Người dùng không bị khóa cứng — họ vẫn xem được trận,
  chỉ không sang được rail bằng một phím LEFT từ hero khi đã cuộn.
- Cách vượt qua (workaround): cuộn về đầu trang rồi LEFT (y=691 thì được), hoặc
  xuống thẻ trận rồi LEFT (từ cardRoot, LEFT đôi khi vẫn không đổi — step 102→103
  LEFT từ cardRoot cũng không đổi; nhưng từ schedCard thì được). Không nhất quán,
  nhưng không phải đường cụt tuyệt đối.

Sai sót trong cách AI diễn đạt (nhưng không làm sai kết luận chính):
- AI ghi "Tab 0 Trực tiếp" — thực tế màn hình là **Home Hub** (hero + hàng Đang phát),
  không phải tab 0. AI cũng đòi focus phải sang "nav_phim/KHO PHIM" — đúng hướng
  (nav_phim là mục rail chồng Y với heroPlay) nhưng tên tab sai.
- AI gọi là "trap" cả khi focus **đã di chuyển** (nhảy xuống thẻ trận) — đó là
  "đi sai hướng", không phải "kẹt". Nhưng vì đích đến mong đợi (rail) không bao giờ
  đạt được, gọi là trap vẫn chấp nhận được ở mức MEDIUM.

**Mức độ: 1 defect thật, MEDIUM là hợp lý. Nhưng harness đã đếm nó 7 lần
(7/9 findings) — đó mới là lý do điểm rơi mạnh, xem §10.**

---

## 6. Kết luận video

**Video toàn phiên KHÔNG tồn tại.** File `full_qa_tour.mp4` dài 174,9 s, chỉ là chunk 1
(~3 phút đầu: màn đen → home hero → room picker → player đầu tiên). Không có
`concat.txt` trong artifact. Bản sửa video_recorder ở commit 15a986a (merge re-encode +
genpts, fallback chunk dài nhất) **không phát huy tác dụng trong lần chạy này** vì CI
không cài ffmpeg/ffprobe — mọi chunk probe 0.0 s nên code fallback về chunk 1
(nguyên nhân đã xác định từ job log). **Hậu quả: 50 phút còn lại của phiên không có
video để đối chiếu — mọi kết luận sau phút thứ 3 chỉ dựa vào ảnh tĩnh + timeline.**

---

## 7. Trạng thái D1–D7 (từ lần chạy 42482017212)

| Defect cũ | Trạng thái lần này | Bằng chứng |
|---|---|---|
| **D1** — chữ bìa banner đè lên chữ UI | **CÒN NGUYÊN, thậm chí tệ hơn** | Mọi ảnh hero: 03, 05/06, 07, 11/12, 13, 16, 17, step_035/063/073/087/089/095/104, frame video 60 s. Tệ nhất ở ảnh 16 (poster "CHƠI KÈO CÙNG BLV GIÓ" chiếm hết banner, đè cả đồng hồ và ngày). Nguyên nhân: ảnh bìa do nguồn cấp (Socolive) chứa sẵn chữ quảng cáo — app hiển thị nguyên bìa mà không có lớp che (scrim) đủ mạnh hay cắt chữ. |
| **D2** — hàng SẮP DIỄN RA trống | **KHÔNG XÁC MINH ĐƯỢC** | Hàng SẮP DIỄN RA không xuất hiện trong bất kỳ ảnh nào của lần chạy này (AI không cuộn tới). Không kết luận được đã sửa hay chưa. |
| **D3** — nhãn stat của portal card bị cắt nửa ở fold | **KHÔNG XÁC MINH ĐƯỢC** | Hàng portal (THỂ THAO / TRUYỀN HÌNH / PHIM TRUYỆN) không xuất hiện trong bất kỳ ảnh nào của lần chạy này — AI không cuộn tới vị trí đó. Bản sửa R4 (chiều cao cố định) chưa được kiểm chứng bằng hình ảnh. |
| **D4** — focus trên kênh IPTV mờ | **CÒN** | step_062: thẻ kênh đang focus không có viền nhìn thấy được; viền trắng trên rail (TRANG CHỦ) dễ gây nhầm với focus. |
| **D5** — hàng cuối lưới IPTV bị cắt nửa | **CÒN** | step_062: hàng kênh dưới cùng bị cắt ngang giữa thẻ ở mép màn hình. |
| **D6** — pill xám "0" trên thẻ trận | **CÒN** | Ảnh 11/12, step_063, ảnh 17: pill xám "0" ở vị trí badge SOCO trên thẻ Brighton vs Brentford và thẻ SPA D1. Chip xoay vòng render giá trị thiếu thành "0" — cần sửa như plan KL6.5 đã ghi (mở rộng `validKickoff` để loại "0"/"0'"). |
| **D7** — OSD clipping (nhãn nút "TẬP TRƯ…", phụ đề đè seekbar) | **KHÔNG XÁC MINH ĐƯỢC** | Hàng điều khiển dưới của player không xuất hiện trong bất kỳ ảnh nào (OSD dưới tự ẩn; chỉ top bar được chụp: ảnh 02, step_027, step_030, frame 170 s). Mission player-settings cũng không chụp được dialog. D7 vẫn mở, chưa kiểm chứng. |

---

## 8. Khiếm khuyết mới phát hiện trong lần chạy này

- **N1 — Tỉ số trực tiếp không hợp lý cho bóng đá (data accuracy).** Nhiều thẻ trận
  hiển thị tỉ số không thể là bóng đá: "Crystal Palace **2:8** Liverpool"
  (ảnh 11/12, 13, 16, 17, step_082/095/104), "Elche **13:8** Real Betis" (step_063),
  "Elche **8:5**" (ảnh 05/06), "Ipswich **1:10** Bournemouth" (ảnh 17),
  "Ipswich **1:8** Bournemouth" (step_082), "FC Köln **2:7**" (ảnh 17).
  Tỉ số thay đổi theo thời gian (Elche 8:5 → 13:8) nên là dữ liệu live, không phải
  ảnh tĩnh lỗi — nhiều khả năng field "score" của nguồn Socolive/ColaTV bị trộn
  với môn khác hoặc là chỉ số khác (cần đối chiếu với nguồn). Tương tự, số lượt xem
  "6844,4K xem" (6,8 triệu) và "2641,6K xem" trên hàng ColaTV (step_082) là không
  hợp lý. **Mức: MEDIUM-LOW về độ tin cậy dữ liệu** — không phải lỗi UI nhưng làm
  giảm niềm tin vào màn hình chính. (Lưu ý: "Sunderland 3:2 Chelsea" và "Ipswich 0:3
  Bournemouth" thì hợp lý và khớp với tỉ số trong player.)
- **N2 — Logo Sunderland hiển thị thành hình chữ nhật đỏ.** Trên thẻ trận ở ảnh 07
  và step_035, logo Sunderland là một khối đỏ (placeholder lỗi) trong khi logo
  Chelsea/Crystal Palace/Liverpool tải bình thường. Có thể URL logo đội này lỗi
  hoặc Coil fallback hiển thị sai. Mức LOW.
- **N3 — Tên đội ngắt giữa từ ở tab Lịch trình.** "Brig ht…", "Crys tal…",
  "Ips wi…", "Sun de…" (ảnh 09) — cột tên quá hẹp, text wrap giữa từ. Mức LOW.
- **N4 — Tên phòng chứa chữ Trung.** "(最高等级)" trong tên phòng BLV TAP/ZIZOU
  (ảnh 04, 10, 14) — dữ liệu nguồn, cosmetic.
- **N5 — Ảnh mission trùng lặp / sai mục tiêu.** 05 ≡ 06 và 11 ≡ 12 (cùng sha256);
  ảnh 10/14/15 là dialog chọn phòng thay vì màn hình mission (IPTV/VOD/settings);
  ảnh 02 là player thay vì cold start. Harness chụp ảnh cuối mission sau khi AI đã
  di chuyển — làm giảm giá trị bằng chứng của mission shot.
- **N6 — OSD top bar đè lên score bug của luồng.** "IPS…BOU" lấp ló sau nút
  "◀ QUAY LẠI" (step_027, frame 170 s, ảnh 02) — va chạm giữa OSD app và đồ họa
  của luồng. Cosmetic.
- **N7 — Vấn đề độ tin cậy của harness (không phải lỗi app).** Xem §9.

---

## 9. Vì sao 102/129 bước "ở tab Phim"? AI có bị kẹt ở tab phim không?

**Không — con số 102 là sai số đo, và AI thực ra bị kẹt ở Home Hub.**

- **Tab detector bị kẹt, không phải AI bị kẹt.** Detector báo "Kho Phim: 102 actions,
  Home Hub: 2, còn lại 0" — nhưng tất cả ảnh step/mission đều cho thấy AI ở **Home Hub**
  (hero + hàng Đang phát) và PlayerActivity. Detector dường như suy tab từ nav item
  được focus/OK gần nhất (nav_phim được focus ở step 13, 42–43) rồi không cập nhật
  nữa, vì AI hiếm khi bấm OK trên nav item. Bằng chứng: step 87–104 detector báo
  "Kho Phim" nhưng ảnh là home hub rõ ràng.
- **AI bị kẹt ở Home Hub theo nghĩa khác — và đó là hệ quả của chính defect heroPlay:**
  từ step 72 đến step 123, AI lặp đi lặp lại vòng `heroPlay ↔ cardRoot` bằng UP/DOWN/LEFT
  (step 72–76: 5 bước liền chỉ ở heroPlay#[680,294]; step 80–104: thăm dò LEFT liên tục;
  step 114–123 mission Search/Settings: cũng chỉ xoay quanh heroPlay/cardRoot).
  Nó không bao giờ tới được màn hình Tìm kiếm, Cài đặt, hay nội dung phim — vì đường
  LEFT từ hero sang rail hỏng, và AI không thử cách khác (xuống thẻ trận rồi LEFT,
  cuộn về đầu rồi LEFT, hay dùng SWITCH_TAB). Một người dùng thật có thể sẽ tự tìm ra
  workaround, nhưng AI thì không — nên **blast radius của defect heroPlay lớn hơn
  một nút bấm: nó làm AI mất khả năng tới 5/7 tab bằng D-pad trong phần lớn phiên.**
- **Mức độ bao phủ thực tế (theo timeline + ảnh, không theo detector):**
  Home Hub (rất nhiều), PlayerActivity (11 bước: 4–7, 26–31, 97, 106, 111),
  Lịch trình (step 45–49, 56–60 — schedCard), IPTV (chỉ step 61–62, rất ngắn).
  **Không bao giờ mở:** WebPlayerActivity (0 bước — mission VOD seek/resume chưa hề
  test web player), màn hình Tìm kiếm, màn hình Cài đặt, nội dung phim NguonC
  (không có poster phim nào trong bất kỳ ảnh nào; mission Phim 72–76 chỉ ở heroPlay).
  Focus từng xuất hiện chỉ gồm: btnCloseFeedback, heroPlay, view#…, backBtn, button2,
  nav_*, cardRoot, schedCard, cardIptvRoot — không có phần tử UI nào của Search/Settings/Phim.
- **Hệ quả cho "16/16 missions passed":** các mission VOD seek/resume, Search &
  Settings, Phim episode picker được chấm "pass" dù màn hình mục tiêu chưa bao giờ
  xuất hiện. Verdict mission của harness là **đánh giá lỏng (lenient)** — không dùng
  được làm bằng chứng bao phủ. Chỉ số trung thực nhất là tab coverage (2/7) — và
  ngay cả nó cũng bị detector làm méo.

---

## 10. Điểm 55/100 — có công bằng không? So với 94/100 ở lần chạy trước

**Không công bằng nếu hiểu là "chất lượng build". Công bằng nếu hiểu là phép tính
của harness. 55/100 phản ánh cách chấm, không phản ánh app tệ đi.**

- **Lần chạy trước (42482017212) 94/100 là điểm của phiên DỞ DANG** — bị hủy ở step
  94/128 do timeout 90 phút, trước khi deep-probe focus và các mission cuối chạy.
  Nó chỉ có 1 finding LOW (decoding error). 94/100 không phải "app đạt 94" mà là
  "trong 94 bước đầu, AI chỉ tìm ra 1 lỗi nhẹ".
- **Lần chạy này chạy đủ 129 bước** nên deep-probe (mission 12–15) mới có cơ hội
  phát hiện defect heroPlay — và nó **đếm cùng 1 defect 7 lần** (mỗi mission/probe
  ghi 1–2 finding cho cùng một root cause). 9 MEDIUM × 5 điểm = −45 → 55/100.
  App không tệ đi giữa 2 lần chạy (cùng commit dòng FPT-home, chỉ khác timeout);
  **phần thăm dò sâu hơn + đếm trùng mới làm điểm rơi.**
- **Điểm đã khử trùng lặp (ước tính, không phải điểm chính thức):** chỉ còn
  ~3 vấn đề thật (heroPlay LEFT, ExoPlaybackException nhất thời, motion 0.0
  chưa xác minh) → khoảng **85–90/100** nếu mỗi root cause chỉ trừ một lần
  (100 − 5 heroPlay − 5 playback − 0~5 motion). Con số này gần với cảm nhận trực
  quan hơn: build chạy ổn định trên các đường đã đi qua (home, lịch trình, IPTV
  ngắn, player thể thao), một defect điều hướng thật, một lỗi luồng nhất thời.
- **Nhưng 55/100 cũng không nên bị bỏ qua hoàn toàn:** nó phơi bày 2 vấn đề thật
  của harness và sản phẩm — (a) defect heroPlay có blast radius lớn (làm AI mất
  khả năng tới 5/7 tab, §9); (b) mission verdict 16/16 là lỏng lẻo, che giấu việc
  Search/Settings/Phim/WebPlayer chưa được test. Điểm số thì phóng đại, nhưng
  hướng sửa thì đúng.

---

## 11. Kiểm tra bảng màu KL5

**ĐẠT.** Nền charcoal ấm (#141210) xuyên suốt mọi màn hình; đỏ #C1272D chỉ dùng cho
badge LIVE/TRỰC TIẾP và nút chính ([OK] XEM NGAY, ĐÃ HIỂU / ĐÓNG); nav rail chỉ có
chữ (text-only, không icon); viền focus trắng rõ ràng trên rail, hero button và thẻ
trận (ngoại trừ lưới IPTV — D4). Không còn cam/cyan cũ, không gradient, không glow.
Badge SOCO (xanh lá) và COLA (đỏ) là badge của nguồn dữ liệu, không phải màu chủ đạo
của app. Dialog chọn phòng và dialog THÔNG BÁO đúng tông KL5.

---

## 12. Follow-up nên kiểm tra (cho lần chạy sau / đợt sửa chung)

1. **Ưu tiên 1 — sửa đường LEFT từ heroPlay sang rail khi đã cuộn** (1 root cause,
   7 findings). Kiểm tra `nextFocusLeft` của heroPlay hoặc `dispatchKeyEvent` safety
   net trong MainActivity: vì sao FocusFinder tìm được nav_settings khi heroPlay ở
   y=691 mà không tìm được nav_phim khi heroPlay ở y=316. Test tay: cuộn hub xuống
   → focus heroPlay → LEFT phải sang rail; lặp lại ở nhiều vị trí cuộn.
2. **D1 — ảnh bìa banner chứa chữ quảng cáo.** Cần scrim mạnh hơn ở vùng chữ UI,
   hoặc ưu tiên dùng ảnh bìa sạch (không chữ) cho hero; ít nhất che được đồng hồ/
   ngày/lượt xem. Kiểm chứng bằng ảnh hero Genoa (poster "CHƠI KÈO") và Sunderland.
3. **D6 — pill "0".** Mở rộng `validKickoff` trong MatchCardsAdapter.bindLive để
   loại "0"/"0'" (đã ghi trong plan KL6.5) — kiểm chứng trên thẻ Brighton vs Brentford.
4. **N1 — tỉ số không hợp lý (2:8, 13:8, 1:10, 2:7) và lượt xem 6844,4K.**
   Đối chiếu field score/viewers của nguồn Socolive/ColaTV với dữ liệu thật trước
   khi sửa UI — có thể là trộn môn thể thao hoặc sai field.
5. **D4/D5 — IPTV:** focus trên lưới kênh phải có viền thấy được; hàng cuối không
   bị cắt nửa (padding/scroll). Kiểm chứng bằng ảnh step_062 tương đương.
6. **D2/D3/D7 — chưa kiểm chứng được trong lần này:** cần bước QA chủ động cuộn
   tới hàng SẮP DIỄN RA + portal cards, và mở OSD dưới trong player để thấy hàng
   nút (seekbar, tập, cài đặt) — nếu không, 3 defect này vẫn mở.
7. **Harness — video:** cài ffmpeg/ffprobe trong `qa-suite.yml` (Install deps)
   và hardening `video_recorder.py` (thiếu ffprobe thì báo rõ, không im lặng
   fallback chunk 1). Nếu không, mọi lần chạy sau vẫn mất video toàn phiên.
8. **Harness — khử trùng lặp findings:** cùng một root cause (cùng view + cùng
   phím) không nên trừ điểm nhiều lần; và mission không nên "pass" khi màn hình
   mục tiêu (Search/Settings/Phim/WebPlayer) chưa từng xuất hiện — cần gate
   theo activity/fragment thực tế, không chỉ theo phán đoán của AI.
9. **Harness — tab detector:** đang báo sai (kẹt ở "Phim" trong khi AI ở Home Hub);
   cần sửa cách xác định tab đang hoạt động trước khi dùng coverage 2/7 làm căn cứ.
10. **Kiểm chứng player OSD dưới + WebPlayer:** lần chạy này chưa hề thấy hàng
    điều khiển dưới và chưa mở WebPlayer lần nào — đợt QA sau cần mission ép mở
    WebPlayer (phim VOD) và giữ OSD dưới hiện đủ lâu để chụp ảnh.

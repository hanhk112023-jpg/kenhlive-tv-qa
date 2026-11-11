# Đánh giá trực quan (Visual Review) — QA run 42511640281 (FULL)

**Nhánh:** `redesign/netflix` · **Commit:** `7829d25` ("fix: episode picker focus and viewport, Sports 0 pill, VOD bar scroll, nav solid on scroll, hero clock clear of nav") · **Chế độ:** FULL
**Kết quả job:** xem `qa_session_summary.md` · **Thời gian chạy:** 4152,6 s (~69 phút) · **Điểm:** 65/100
**Steps:** 126 · **Tabs:** 5/7 (Tìm Kiếm 0 thao tác, Cài Đặt 0 thao tác — chưa duyệt) · **Findings:** 3 (2 HIGH trùng nhau + 1 MEDIUM)
**Video:** `full_qa_tour.mp4` — 87 MB, **480,6 s** cho phiên 4152,6 s (xem §3)

**Phạm vi bài đánh giá này:** đã đọc trực tiếp **~45 ảnh** — các step
`001`–`003`, `005`, `007`–`008`, `010`, `012`, `015`, `020`, `023`, `025`, `028`,
`030`, `032`, `038`–`039`, `041`–`042`, `046`, `055`, `061`–`064`, `066`–`067`,
`070`, `073`, `076`–`077`, `080`, `083`, `086`–`090`, `092`, `094`, `096`,
`104`, `111`; ảnh mission `11`; **8 frame video** (mỗi 60 s, `f_001`–`f_008`);
`qa_report.json` (toàn bộ timeline 126 bước + thoughts của AI), `qa_session.json`,
`qa_session_summary.md`, cả hai ảnh mẫu trình phát, plan Task 11 Step 5, và
**diff của commit sửa QA `7829d25`** (để đối chiếu "định sửa gì" với "trên màn
hình ra sao"). Đã đo/crop vùng top nav để kiểm chứng D8/D9/D17
(`crop_step_002/005/007/020/038/039`). Không suy đoán nội dung ngoài những gì
nhìn thấy trong ảnh/timeline/diff.

**Quy ước timeline** (như các lần trước): focus ghi ở step N là trạng thái
**TRƯỚC** action của step N; action ở step N gây ra focus ở step N+1.

---

## 1. Từng ảnh mission (01–17) — giá trị bằng chứng thấp, nhiều trùng lặp

Đối chiếu sha256: **12/17 ảnh mission trùng step shot** (xem §9). Chỉ liệt kê
những ảnh có nội dung riêng hoặc đáng chú ý:

- **01** ≡ `step_001`: dialog THÔNG BÁO, **ĐÃ HIỂU / ĐÓNG có viền trắng rõ** —
  R1 vẫn sửa xong. Dòng cuối thân dialog ("…nhận file cập nhật mới nhất.")
  vẫn hơi cắt ở mép dưới vùng cuộn (cosmetic, như quick run).
- **02** ≡ `step_006`, **03** ≡ `step_013`/`014`, **04** ≡ `step_018`/`019`,
  **05** ≡ `step_023`/`031`, **07** ≡ `step_039`/`040`, **08** ≡
  `step_046`–`051` (6 ảnh giống hệt nhau — bằng chứng finding #3, xem §4),
  **09** ≡ `step_053`, **10** ≡ `step_063`, **12** ≡ `step_075`/`085`,
  **13** ≡ `step_076`/`084`, **14** ≡ `step_092`/`093`,
  **15** ≡ `step_111`/`114`/`117`, **16** ≡ **17** ≡ `step_121`/`124`.
- **06** ≡ `step_023`/`031`: màn hình Thể thao (không phải player) — mission
  "player streaming" lại chụp màn hình list, quirk harness như trước.
- **11** (duy nhất không trùng step): player IPTV **VTV Cần Thơ, "Đang tải
  luồng…"** (spinner, nền đen) — trạng thái đang zap kênh, không thấy
  Mini-Guide hay EPG bar.
- **15/16/17** đều là **dialog "Cài đặt trình phát" bên trong PlayerActivity** —
  mission 16 tên "search and settings feedback" nhưng ảnh không phải màn hình
  Tìm kiếm hay Cài đặt nào cả. Đây là triệu chứng của vấn đề lớn nhất về bao
  phủ của lần chạy này: **AI không bao giờ rời PlayerActivity sau step 93**
  (xem §7), nên 3 mission cuối "pass" trên giấy nhưng không test đúng mục tiêu.

---

## 2. Phán quyết 3 findings (trong `qa_report.json`)

| # | Finding (step) | Phán quyết | Bằng chứng |
|---|---|---|---|
| 1 | [Step 38] [HIGH] Tab 6 Home Hub Portal không tồn tại trong app | **HARNESS-EXPECTATION MISMATCH — không phải lỗi app** | Judge tự ghi: nav chỉ có 6 `nav_*` views (`nav_live, nav_iptv, nav_phim, nav_schedule, nav_search, nav_settings`). Đó đúng là thiết kế KL6.5: 6 tab, portal cards đã **bị xóa có chủ đích ở Task 4** của plan ("The ONLY deletions allowed… Task 4 (portal cards + old home header)"). Ảnh `step_031`–`039` cho thấy Home Hub mới hoạt động đúng thiết kế thay thế: billboard Inter Milan vs Como sạch (step_038), hàng ĐANG PHÁT TRỰC TIẾP (step_032/039), SẮP DIỄN RA + PHIM ĐANG THỊNH HÀNH 6 poster (step_002/003). Mission đòi "3 card lớn THỂ THAO/TRUYỀN HÌNH/PHIM TRUYỆN với Logo Canva 3D" là mô tả **layout cũ trước redesign**. Không có màn hình đen, crash hay thiếu nội dung nào. |
| 2 | [Step 39] [HIGH] cùng finding portal | **TRÙNG LẶP của #1 — cùng một nguyên nhân, bị trừ điểm 2 lần** | Cùng một mission, cùng một detail, ghi lại ở step COMPLETE_MISSION ngay sau step 38. Không có bằng chứng mới nào. 2 HIGH = −30 điểm cho **một** mismatch của harness. |
| 3 | [Step 51] [MEDIUM] Sidebar Rail không mở khi DPAD_LEFT từ mép trái | **HARNESS-EXPECTATION MISMATCH — không phải lỗi app** | 5 lần DPAD_LEFT từ `schedCard` "RC Celta vs Levante" (steps 46–50, 6 ảnh `step_046`–`051` giống hệt nhau): focus đứng yên — **đúng** vì thẻ Lịch trình rộng toàn màn hình, không có phần tử nào bên trái để đi tới. Left rail đã **bị thay có chủ đích bằng top nav ở Task 3** (cùng 6 nav id, lên nav bằng UP từ hàng đầu). Và lần chạy này **chứng minh UP hoạt động**: steps 55–61 bấm UP 7 lần từ thẻ Lịch trình → focus lên `nav_phim` (step_061, viền trắng quanh KHO PHIM), LEFT sang `nav_iptv`, OK mở IPTV (step_063). Focus không kẹt ở đâu cả. Judge đòi một tính năng đã bị xóa khỏi thiết kế. |

**Tóm lại: cả 3 findings đều là kỳ vọng của harness viết cho layout cũ
(portal cards + sidebar rail), không phải lỗi app. 65/100 = 100 − 15 (#1)
− 15 (#2) − 5 (#3): toàn bộ 35 điểm trừ là oan theo nghĩa "app sai".**
Xem §8 để biết vì sao 65/100 vẫn không nên được đọc là "app đạt 100".

---

## 3. Video `full_qa_tour.mp4`

| Frame video | Nội dung thấy được |
|---|---|
| 0 s (`f_001`) | Hero Thể thao Inter vs Como + thẻ RC Celta focus (tương đương step_010, session t≈250 s) — **không phải cold start** |
| 60 s (`f_002`) | Player Thể thao, OSD TSG 6-0 FCS (steps 25–30) |
| 120 s (`f_003`) | Home hub: ĐANG PHÁT TRỰC TIẾP, thẻ Inter focus (steps 32–39) |
| 180 s (`f_004`) | Tab Lịch trình, thẻ RC Celta focus (steps 46–52) |
| 240 s (`f_005`) | Player IPTV VTV Cần Thơ, **OSD đã ẩn, video trần** (steps 64–71) |
| 300 s (`f_006`) | Player VOD 04:47/14:30, OSD hiện, không nút nào focus |
| 360 s (`f_007`) | Episode picker trong player: Tập 1 đỏ (đang xem), Tập 2 focus (steps 96–101) |
| 420 s (`f_008`) | Dialog "Cài đặt trình phát", "Điện ảnh (Zoom)" focus (steps 104–111) |

**Kết luận video: vẫn chưa phải full tour 1x — y hệt mẫu quick run.**
File dài **480,6 s** (ffprobe xác nhận, 1280×720, 87 MB) cho phiên 4152,6 s.
`concat.txt` **có** (22 chunk) — merge chạy được. Nhưng video bao phủ session
t≈250 s → t≈3900 s với tốc độ nén **~8,6x**: **thiếu ~4 phút đầu** (cold start,
dialog THÔNG BÁO, hero, findings #1–2) và **thiếu ~4 phút cuối** (kẹt trong
dialog cài đặt steps 111–126 + kết thúc phiên). Không dùng được để kiểm chứng
chuyển động/phát lại ở tốc độ thực. `qa_timelapse.mp4` 48,1 s (timelapse 10x).
**Kỳ vọng "full-length video" của Task 11 Step 5 KHÔNG đạt** — cùng một lỗi
recorder như quick run (468,7 s / 3967 s), không cải thiện dù commit `5c99050`
đã thêm ffmpeg vào QA deps.

---

## 4. Re-check 5 mục QA-fix (commit 7829d25)

| Mục | Commit định sửa | Verdict trên màn hình | Bằng chứng |
|---|---|---|---|
| **D11** episode picker | Bỏ gate `DeviceMode.isTv` khi xin focus + focus dự phòng vào nút ĐÓNG trong `onShow` (`EpisodePickerDialog.kt`) | **FIXED (chức năng)** — xem chi tiết dưới | step_077–083, step_096–101, f_007 |
| **D10** pill "0" | `validClock` loại `"0"`/`"0'"` (`MatchCardsAdapter.kt`) | **FIXED** | step_007/008/010/012/020/023, f_001 |
| **D12** VOD bar | `vodControlBar` thành HorizontalScrollView + nút Khóa add vào row con (`PlayerActivity.kt`, `activity_player.xml`) | **PARTLY — sửa trong code, chưa chứng minh được trên màn hình** | step_086/087/089/094, f_006 |
| **D8** nav solid | Ngưỡng đặc nav 8dp (Home) + thêm scroll listener cho tab Thể thao (`HomeHubFragment.kt`, `LiveFragment.kt`) | **PARTLY — sạch khi hero hiện đầy đủ, vẫn lỗi ở 2 trạng thái còn lại** | step_007/008/010/012/015/039, f_001, crop top nav |
| **D9** clock/date | Đẩy cụm đồng hồ xuống dưới mép dưới nav (`HeroPagerAdapter.kt`) | **FIXED** | step_007/038, f_001, crop top nav |

### D11 — FIXED (chức năng), còn 1 vấn đề trình bày mới (→ D18)
- Mở từ màn hình chi tiết phim: step_077 dialog hiện **đầy đủ trong tầm nhìn**,
  lưới Tập 1–25, **Tập 1 focus ngay khi mở** (viền trắng, timeline
  `tvEpisodeName#[62,550][424,626]` ring=True). Điều hướng RIGHT Tập 1→4
  (step_080, viền trắng trên Tập 4), DOWN Tập 4→15 (step_083, viền trắng trên
  Tập 15). BACK đóng được (step_084 về lại CHỌN TẬP). Khác hẳn quick run
  (5 ảnh giống hệt nhau, focus NONE ~70 s).
- Mở từ trong player: step_096 dialog **nền đặc, sạch**: tiêu đề "Mục Thần Ký ·
  Vietsub", lưới Tập 1–50, Tập 1 đỏ (tập đang xem), ĐÓNG góc dưới-phải;
  f_007 cho thấy Tập 2 focus (viền trắng) trong khi Tập 1 giữ màu đỏ.
  OK ở step_101 trên ĐÓNG đóng dialog (step_102 về player).
- **Nhưng:** dialog mở từ màn hình chi tiết có **nền trong suốt** — nội dung
  chi tiết phía sau xuyên qua và đè lên lưới tập (xem D18).

### D10 — FIXED
Không còn pill xám "0" ở bất kỳ thẻ nào trong steps 007–013/020/023 và f_001.
Thẻ RC Celta 2:2 hiện pill xám **"HT" hợp lệ** (step_010, f_001); thẻ
Inter 2:0, Villarreal 0:0, FC Utrecht 0:0 hiện tỉ số thật. "0:0" là tỉ số,
không phải pill lỗi.

### D12 — PARTLY
Hàng nút VOD ở trạng thái nghỉ **vẫn kết thúc bằng nút cắt nửa "TỐ" ở mép
phải** trong mọi ảnh (step_086/087/089/094, f_006); **nút Lock (KHÓA) không
xuất hiện trong bất kỳ ảnh nào**. Focus đi được tới ÂM THANH & PHỤ ĐỀ
(step_086, viền trắng) và CHỌN TẬP (step_087, viền trắng) nhưng AI không bao
giờ bấm RIGHT từ nút cuối để cuộn bar — nên không biết bar cuộn có lộ
Speed/Lock hay không. Fix code có thật (bar giờ là HorizontalScrollView),
nhưng **trên màn hình, ở trạng thái nghỉ, lỗi nhìn vẫn y như quick run**.
Cần một lần test chủ đích: focus tới nút cuối và bấm RIGHT.

### D8 — PARTLY (chi tiết ở §5)
- Sạch khi billboard hiện đầy đủ dưới nav đặc: step_038 (tiêu đề Inter Milan
  VS Como, nút XEM NGAY/CHỌN PHÒNG, clock — tất cả sạch, nav nền đen đặc).
- **Vẫn lỗi ở 2 trạng thái:** (a) hero tab Thể thao lúc nghỉ — hàng badge của
  hero ("TRỰC TIẾP" • "Serie A" • 👁 413,9K) nằm cùng hàng với nav và đè lên
  "KENHLIVE"/"TRANG CHỦ"/"TRUYỀN HÌNH" (step_007/008/010/012/015, f_001 —
  crop phóng to cho thấy rõ); (b) Home đang cuộn — nút "[OK] XEM NGAY" /
  "[MENU] CHỌN PHÒNG" của billboard **hiện xuyên qua/lên trên nav** và đè lên
  nhãn nav (step_039, crop phóng to). Ngoài ra nội dung vẫn trượt lên dưới
  nav ở các màn hình list: chữ "Đang trự…" ló trên mép nav (crop step_002),
  thẻ trận nửa cắt dưới nav (step_005), thẻ Lịch trình nửa cắt dưới nav
  (step_055, f_004). Ngưỡng 8dp không cứu được trạng thái (a) vì ở offset
  cuộn = 0 nav vẫn trong suốt trong khi hero đã bắt đầu ở y=0 phía sau nav;
  và ở trạng thái (b) hero dường như vẽ **trên** nav (z-order), không chỉ là
  nav trong suốt.

### D9 — FIXED
Cụm "01:54" + "Thứ Hai, 09/11/2026" + "01/10 ÂL · Ất Tỵ" giờ nằm **dưới**
hàng nav, bên trong hero (step_007/038, crop top nav; f_001) — không còn đè
lên TÌM KIẾM/CÀI ĐẶT trong bất kỳ ảnh nào. Fix đúng như diff mô tả.

---

## 5. Khiếm khuyết mới trong lần chạy này (D18–D21)

| # | Mức | Vấn đề | Bằng chứng |
|---|---|---|---|
| **D18** | MEDIUM-LOW | **Episode picker mở từ màn hình chi tiết phim có nền trong suốt — nội dung chi tiết xuyên qua và đè lên lưới tập.** Chữ mô tả ("…sau khi khảo nghiệm, hắn trở thành thủ lĩnh của…", "Không có mô tả chi tiết.") và các nút XEM NGAY/CHỌN TẬP/LƯU PHIM + chip DANH MỤC phía sau đều lộ qua dialog, chồng lên các hàng Tập 1–25. Lưới vẫn đọc được và focus vẫn chạy, nhưng trông như 2 màn hình chồng nhau. (Cùng một dialog mở từ trong player thì nền đặc và sạch — step_096/f_007 — nên đây là lỗi riêng của đường mở từ màn hình chi tiết; code comment trong diff cũng ghi "nền cửa sổ trong suốt để nền kính bg_osd_glass".) | step_077–083 |
| **D19** | MEDIUM | **Focus kẹt vòng lặp trong dialog "Cài đặt trình phát" — không tới được nút ĐÓNG bằng D-pad; phiên kết thúc vẫn ở trong dialog.** Từ step_104 tới step_126 (~23 bước, ~10 phút phiên) focus chỉ luẩn quẩn giữa các chip: `view#[770,434]` → `view#[641,644]` → `view#[672,854]` → `view#[770,434]`… (steps 107–126 lặp đúng chu trình này). DOWN từ chip hàng cuối ("30s", y≈854–950) nhảy về hàng Âm thanh thay vì xuống ĐÓNG (y≈992). Nút ĐÓNG thấy rõ ở góc dưới-phải (step_111, f_008) nhưng **không bao giờ được focus** sau step_101 (lần đó là ĐÓNG của episode picker, không phải dialog này). Hệ quả trực tiếp: AI không thoát dialog, missions 16 (Tìm kiếm & Cài đặt) và 17 (chaos) chạy loanh quanh trong dialog và **tab Tìm Kiếm/Cài Đặt không bao giờ được mở**. Lưu ý: AI không thử BACK trong trạng thái này nên chưa rõ BACK có đóng dialog không — kẹt ở đây nghĩa là "không có đường D-pad tới ĐÓNG", chưa chứng minh là "không thoát được". | step_104–126, step_111, f_008 |
| **D20** | LOW-MEDIUM | **WebPlayerActivity mở 0 lần — lần thứ hai liên tiếp.** Timeline activities: MainActivity 71 + PlayerActivity 55, **WebPlayerActivity 0**. Mission 13 tên "Trình Phát Web (WebPlayerActivity)" vẫn "pass" nhưng VOD mở từ XEM NGAY đi vào PlayerActivity (native, direct m3u8); thoughts của AI còn ghi nhầm PlayerActivity thành WebPlayerActivity (steps 86, 89–92). Hệ quả: web seek bar, web Speed gate (`playbackRate` probe), web brightness — **vẫn chưa được kiểm chứng ở cả hai lần chạy**. | timeline steps 86–92, activity counter |
| **D21** | LOW | **Lưới kênh IPTV không hề xuất hiện trong lần chạy này — D4/D5 không re-check được.** SWITCH_TAB(2) bấm 3 lần ở steps 51–53 nhưng màn hình vẫn ở Lịch trình; chỉ tới khi OK trên `nav_iptv` ở step_62 thì step_063 mới vào hero IPTV, rồi AI mở thẳng player (step_063 OK trên XEM TOÀN MÀN HÌNH). Không có ảnh nào chụp lưới kênh, không có focus `cardIptvRoot`, không có long-press yêu thích. Mission 9 "IPTV categories & favorites" pass trên giấy nhưng ảnh chụp là màn hình Lịch trình. | steps 51–63 |

### Quan sát thêm (N-series, không phải defect UI trực tiếp)

- **N8 — Tỉ số/lượt xem phi thực tế, vẫn còn và nặng hơn.** App báo TSG
  Hoffenheim **6-0** Schalke trong khi **chính score bug của luồng ghi 2:0**
  (step_025/028, f_002; luồng còn ghi "39:08 TSG 2 0 S04" ở step_030).
  ColaTV: Inter **8:1** Calcio, Besiktas 9:1, Vitoria 2:5 (step_020/023);
  lượt xem "3726,0K xem", "2668,3K xem", "2095,4K xem" cho cùng trận mà
  Socolive báo 413,8K. Dữ liệu nguồn, không phải UI — nhưng người xem thấy
  ngay vì tỉ số app và tỉ số trên luồng đối chiếu nhau trong cùng một khung hình.
- **N9 — Phòng 0 lượt xem, vẫn còn.** RoomPicker mở từ Lịch trình: tất cả
  các phòng "0 lượt xem · LIVE" (step_042: A BỆU, BLV HEHE, THẠCH TÚ, LOKA,
  A PÁO); cùng trận đó mở từ Thể thao thì phòng có 26,8K xem (step_015:
  TRÀ ĐÁ Lv.2, 26,8K lượt xem · LIVE · Điểm: 9,1K). Không nhất quán giữa hai
  đường mở.
- **N10 — "Đang chiếu: 113 online" đã hết.** Hero IPTV giờ hiện EPG thật:
  "Đang phát: [02:00 - 02:50] Phim truyện: 13h00 - Ngọc Lâu Xuân - Tập 14/43"
  + "Tiếp theo: [02:50] Câu chuyện giao thông…" (step_063); player cũng ghi
  "KÊNH 1 · Đang chiếu: Phim truyện: 13h00 - Ngọc Lâu Xuân - Tập 14/43"
  (step_064/066/067).
- **N11 — Chữ bìa/cover lộ qua nav, vẫn còn.** Chữ mờ "…ĐIỆN ẢNH ĐẶC SẮC" lộ
  qua nav bán trong trên màn hình phim (step_073/076/092); chữ "LIVE"/"Đang
  trự…" ló trên mép nav ở Home (crop step_002/005).
- **N12 — Đồ họa của luồng đè lên OSD của app, vẫn còn.** Banner "HOME
  (XANH) · AWAY (XANH LÁ) · KÈO RUNNING…" của luồng đè lên hàng tiêu đề Thể
  thao (step_025/028, f_002); chữ quảng cáo "…i999.ai tài trợ… Bắn Cá, Sòng
  Bài…" đè lên tiêu đề VOD (step_087); logo "Cần Thơ" của luồng đè lên
  "KÊNH 5" ở player IPTV (step_070). Cosmetic, khó sửa triệt để.
- **N13 — Ảnh mission trùng lặp / sai mục tiêu.** 12/17 ảnh mission trùng
  step shot (sha256, xem §9); ảnh 06 chụp màn hình list thay vì player;
  ảnh 15/16/17 đều là dialog cài đặt trong player.
- **N14 — Detector focus vẫn sai.** Timeline báo `has_focus_ring: False` ở
  step_003/004/005 trong khi ảnh cho thấy viền trắng rõ quanh thẻ focus
  (step_003: thẻ FC Utrecht; step_005: thẻ TSG Hoffenheim); `focused_view:
  NONE` ở 23 bước, trong đó có các bước VOD mà ảnh cho thấy nút đang focus
  có viền trắng (step_087 CHỌN TẬP, step_094 ÂM THANH & PHỤ ĐỀ). Detector
  vẫn không đáng tin làm căn cứ chấm điểm.
- **N16 — ERROR_CODE_DECODING_FAILED tái xuất 1 lần.** step_088: dialog
  "Lỗi Phát Luồng Video / Stream lỗi: ERROR_CODE_DECODING_FAILED" với THỬ LẠI
  focus (viền trắng), QUAY LẠI, BÁO LỖI; step_089 video phát lại bình thường
  (06:07). Lỗi codec trên emulator x86 — mức LOW, theo plan là môi trường.

---

## 6. Trạng thái D1–D17 (so với quick run 42504300280)

| Defect cũ | Trạng thái lần này | Bằng chứng |
|---|---|---|
| **D1** — chữ bìa banner đè lên chữ UI | **ĐỔI DẠNG, chưa hết.** Dạng cũ (chữ bìa đè tiêu đề/nút) đã hết — hero có scrim, tiêu đề/nút sạch khi hiện đầy đủ (step_038). Nhưng cùng khu vực sinh ra D8-dạng-mới (hero trượt dưới nav) + N11 (chữ bìa lộ qua nav). | step_007/038/039, f_001 |
| **D2** — hàng SẮP DIỄN RA trống | **ĐÃ SỬA (giữ nguyên).** Hàng có nội dung đầy đủ (step_002/003: FC Utrecht 02:00, Fiorentina 02:45, RC Lens 02:45 + "Còn 9p/54p"). | step_002/003 |
| **D3** — nhãn stat portal card cắt nửa ở fold | **ĐÃ SỬA (giữ nguyên, portal đã bỏ).** Không còn portal card trong bất kỳ ảnh nào. | toàn bộ |
| **D4** — focus trên kênh IPTV mờ | **KHÔNG KIỂM CHỨNG ĐƯỢC lần này.** Lưới kênh IPTV không xuất hiện (D21). Quick run đã xác nhận sửa; lần này không có ảnh để đối chiếu. | steps 51–63 |
| **D5** — hàng cuối lưới IPTV cắt nửa | **KHÔNG KIỂM CHỨNG ĐƯỢC lần này.** Cùng lý do D21. | steps 51–63 |
| **D6/D10** — pill xám "0" | **ĐÃ SỬA.** Xem §4 D10. | step_007–013, f_001 |
| **D7** — OSD clipping | **ĐÃ SỬA MỘT PHẦN, còn D12/D13.** Nhãn nút VOD không còn cắt giữa từ kiểu "TẬP TRƯ…" — nhưng hàng nút vẫn tràn và cắt Speed ("TỐ", D12). Phụ đề đè seekbar: **vẫn chưa kiểm chứng được** — không ảnh nào có phụ đề + OSD bar cùng lúc. | step_086–094, f_006 |
| **D8** | **PARTLY.** Xem §4. | step_007/039, f_001 |
| **D9** | **FIXED.** Xem §4. | step_007/038 |
| **D11** | **FIXED (chức năng).** Còn D18 (nền trong suốt ở đường mở từ màn hình chi tiết). | step_077–083, 096–101 |
| **D12** | **PARTLY.** Xem §4. | step_086–094 |
| **D13** — dialog cài đặt cắt chip + cắt dòng cuối | **CHƯA SỬA.** Chip "Tự động (Hay)" vẫn bị cắt ở mép phải dialog; dòng "Đang chọn: 10s" vẫn bị cắt nửa ở mép dưới (step_104/111, f_008). | step_104/111, f_008 |
| **D14** — OSD Thể thao không focus được | **CHƯA SỬA.** Focus NONE suốt steps 24–30; không nút OSD nào có viền trắng trong step_025/028/f_002; MENU/A/B/OK không có phản hồi nhìn thấy (OK ở step_28 không tạm dừng — motion vẫn 12.13→9.0). Khác với VOD (focus thấy rõ trên nút). | step_025/028, f_002 |
| **D15** — BACK không thống nhất | **ĐÃ SỬA (thành hành vi thống nhất 2-BACK).** Thể thao: BACK 1 ẩn OSD (step_030 video trần) → BACK 2 thoát (step_031 MainActivity). IPTV: tương tự steps 70–71. VOD: BACK 1 ẩn OSD (step_090 video trần) → BACK 2 thoát (step_091 MainActivity). Khác quick run (VOD khi đó thoát sau 1 BACK) — giờ cả ba player đều theo đúng quy tắc 3 cấp (ẩn OSD → thoát). | step_029/030, 070/071, 089/090 |
| **D16** — ô nhập tìm kiếm không khung | **KHÔNG KIỂM CHỨNG ĐƯỢC.** Tab Tìm kiếm không được mở lần nào. | timeline |
| **D17** — TRANG CHỦ thiếu gạch chân đỏ + chấm đỏ bí ẩn | **ĐỔI DẠNG / LÀM RÕ MỘT PHẦN.** Gạch chân đỏ **có tồn tại** trên TRANG CHỦ ở một số trạng thái: rõ ràng ở tab Thể thao (crop step_020) và khi billboard đã cuộn khỏi hẳn (f_003). Nhưng **vẫn không thấy** trên màn hình Home Hub khi hero đang hiện (crop step_002/005/038/039 — không có gạch chân dù TRANG CHỦ đang được chọn). Cách giải thích khớp mọi ảnh: gạch chân có vẽ nhưng bị hero/billboard che mất khi hero còn hiện (cùng gốc rễ với D8: hero vẽ trên nav). **Chấm đỏ sau "TRANG CHỦ" thì vẫn còn trong mọi ảnh, kể cả khi tab khác đang được chọn** (step_041/055/061/063/073/076) — vẫn chưa rõ là gì, cần đáp án thiết kế. | crop step_002/005/020/038/039, f_003 |

**Đã xác nhận sửa xong trong lần này (so với quick run):** D9, D10, D11
(chức năng), D15 (thống nhất 2-BACK), N10 (EPG thật), R1 (giữ nguyên).
**Đã xác nhận còn:** D8 (dạng mới), D12 (dạng cũ), D13, D14, D17 (dạng mới).
**Chưa xác minh được trong lần này:** D4, D5, D16, nửa phụ đề của D7,
gate seek Thể thao, EPG bar/Mini-Guide IPTV, WebPlayer (D20).

---

## 7. Đối chiếu checklist Task 11 Step 5

- **Bảng màu KL6.5: ĐẠT.** Nền #141414, card #242424, chữ trắng/xám, đỏ
  #E50914 chỉ dùng cho logo KENHLIVE, badge LIVE/TRỰC TIẾP, nút chính ([OK]
  XEM NGAY, ĐÃ HIỂU / ĐÓNG, PHÁT). Không còn cam KL5/cyan cũ, không gradient,
  không glow. Badge SOCO (xanh lá) / COLA (đỏ) là badge nguồn dữ liệu.
- **Top nav — gạch chân đỏ tab đang chọn: ĐẠT MỘT PHẦN.** Có ở LỊCH TRÌNH
  (step_041/061), TRUYỀN HÌNH (step_063), KHO PHIM (step_073/076), TRANG CHỦ
  ở tab Thể thao (crop step_020) và khi đã cuộn (f_003); **không thấy ở
  TRANG CHỦ trên màn hình Home Hub khi hero đang hiện** (D17, xem §6).
  Nav chuyển đặc khi cuộn hẳn (step_038, f_003) nhưng không chuyển/che được
  hero ở vùng chuyển tiếp (D8).
- **Billboard: ĐẠT khi hiện đầy đủ** (step_038 sạch), **lỗi khi ở tab Thể thao
  lúc nghỉ và khi cuộn** (D8). Ảnh bìa vẫn chứa chữ quảng cáo mờ (N11).
- **Các hàng: ĐẠT.** Hàng live/upcoming/phim đều có nội dung, không hàng trống;
  tên giải, tỉ số, lượt xem, số phòng đọc rõ. Tên đội trên thẻ trận bị cắt ngắn
  ("Inter M…", "TSG Ho…", "Villarre…", "FC Utr…") do mỗi thẻ chứa 2 đội +
  logo + badge — như quick run, đây là thiết kế, cần Evelyn quyết.
- **6-per-row: ĐẠT với poster phim, KHÔNG áp cho thẻ trận.** Poster phim 6/hàng,
  tiêu đề 2 dòng đọc được (step_002/003). Thẻ trận rộng ~326dp, ~2,7 thẻ/hàng
  (step_005/010/012) — lo ngại 137dp không áp cho thẻ trận như build hiện tại.
- **Top-bar reachability: ĐẠT MỘT PHẦN, có tiến bộ so với quick run.** Từ hàng
  đầu Lịch trình, UP lên được nav sau 7 lần UP (thẻ → … → nav_phim, steps
  55–61), rồi LEFT sang nav_iptv + OK mở IPTV. Từ hàng đầu Home, UP lên nav
  đã xác nhận ở quick run (3 lần UP). Từ hàng đầu IPTV/Phim/Tìm kiếm/Cài đặt,
  **UP lên nav vẫn chưa được thử lần nào** (AI đi DOWN từ nav thay vì UP từ
  hàng đầu). LEFT từ thẻ Lịch trình full-width không đi đâu là đúng (finding
  #3 là mismatch, xem §2).
- **OSD Thể thao vs mẫu sport: ĐẠT VỀ CƠ BẢN, trừ focus và gate.**
  Score pill góc trên-trái ✓ ("TSG 6 - 0 FCS", step_025/028, f_002),
  TUA ±30S ✓ (nút chữ, không phải icon tròn như mẫu), seekbar trắng + knob ✓,
  "Về trực tiếp" ✓, 2 hàng nút KL6.5 (Chọn BLV/Đổi luồng/KÊNH TIẾNG/DA MÀN
  HÌNH/PIP/TÙY CHỌN) ✓. **Nhưng:** không nút OSD nào focus được (D14);
  thanh live đứng ở 00:00, nhãn phải "00:06" khó hiểu, **không thấy chấm đỏ
  LIVE ở đầu phải** trong bất kỳ ảnh nào (đầu phải là nút "Về trực tiếp");
  phần buffered xám nhạt không phân biệt được (track tối + quảng cáo của luồng
  đè lên). **Gate hỗ trợ vẫn chưa xác minh được:** AI không bấm LEFT/RIGHT ở
  player Thể thao trong cả hai lần chạy, nên không biết ±30S có tua thật trên
  luồng live không.
- **OSD IPTV vs mẫu: CHƯA THẤY ĐỦ — Mini-Guide và EPG bar không xuất hiện
  trong bất kỳ ảnh nào.** Top bar ✓ (QUAY LẠI/KÊNH/Đổi nguồn/PIP/TÙY CHỌN),
  tên kênh + "Đang chiếu" thật ✓ (step_064/066/067/070). Nhưng player IPTV
  **không có thanh dưới nào cả**: chỉ có timer "02:19"/"02:22"/"02:26" góc
  dưới-phải (step_064/067, f_005); AI đã bấm OK/DOWN/UP/phím số 1/5 (steps
  64–69, zap kênh thành công ANTV → VTV Cần Thơ) mà không gọi ra Mini-Guide
  hay thanh EPG nào. Hero IPTV thì có thanh tiến trình đỏ mỏng (step_063) —
  nhưng đó là hero, không phải player.
- **OSD VOD vs mẫu vod: ĐẠT VỀ CƠ BẢN, trừ cuối hàng nút (D12).** Tiêu đề
  giữa ✓, thanh trượt dọc độ sáng ✓ (icon bánh răng + knob trắng, step_086/
  087/089/094), seekbar đỏ + knob ✓, nhãn thời gian còn lại ✓ (01:36+17:42,
  03:17+16:00, 06:07+13:10, 08:43+10:34 — cộng lại luôn ≈19:17–19:18),
  TẬP TRƯỚC/TIẾP ✓, CHỌN TẬP ✓, ÂM THANH & PHỤ ĐỀ ✓ (focus được, viền trắng
  step_086/094). SKIP INTRO vắng mặt là đúng (GONE mặc định). **Speed bị cắt
  còn "TỐ", Lock không thấy (D12).** Gate web Speed: **không áp dụng được —
  WebPlayerActivity không mở lần nào (D20).**
- **Thanh player lúc nghỉ và lúc focus: ĐẠT MỘT PHẦN.**
  - VOD: knob trắng thấy rõ cả lúc nghỉ lẫn lúc focus (step_086–089/094,
    f_006); phần đã phát đỏ rõ; phần chưa phát xám vừa — **không phân biệt
    được đoạn buffered xám nhạt riêng** trên ảnh tĩnh; nhãn giờ đọc rõ,
    không nhảy (tổng luôn 19:17–19:18).
  - Live (Thể thao): knob trắng ở 00:00; phần buffered không phân biệt được;
    chấm đỏ LIVE ở đầu phải **không thấy** (xem trên).
  - EPG (IPTV): thanh mỏng không knob **không quan sát được** trong player
    (xem trên); chỉ có ở hero IPTV.
- **BACK: THỐNG NHẤT (D15 đã sửa).** Cả ba player đều 2 BACK: BACK 1 ẩn OSD,
  BACK 2 thoát (Sport steps 29–30, IPTV 70–71, VOD 89–90). Dialog nào cũng
  đóng bằng BACK (RoomPicker step_17, EpisodePicker step_83) và focus về
  đúng chỗ.
- **Phụ đề: chưa kiểm chứng được vị trí trên OSD bar.** Không ảnh nào có phụ
  đề + OSD bar cùng lúc (phụ đề không xuất hiện trong bất kỳ ảnh player nào
  của lần chạy này).
- **R1: ĐÃ SỬA (giữ nguyên).** step_001: ĐÃ HIỂU / ĐÓNG focus, viền trắng.
- **Dialog cài đặt thống nhất: ĐẠT về nội dung, KẸT về focus (D19).** Cùng một
  dialog 4 nhóm (Hình ảnh / Âm thanh / Tỉ lệ khung hình / Bước tua) ở VOD
  (step_104/111, f_008); chọn chip cập nhật được ("Đang chọn: …" đổi theo).
  Nhưng focus không tới được ĐÓNG (D19), và D13 (cắt chip/cắt dòng cuối) còn
  nguyên.

---

## 8. Điểm 65/100 — có công bằng không?

**Không công bằng nếu hiểu là "chất lượng build".** 65/100 = 100 − 15 (finding
#1) − 15 (finding #2, trùng #1) − 5 (finding #3). Cả 3 findings đều là
**mismatch giữa mission/harness viết cho layout cũ và app đã redesign** (§2) —
khử artifact thì thang của judge cho **100/100**. So với quick run 75/100
(thực chất 1 vấn đề thật D11 + 2 artifact): lần này **không còn vấn đề HIGH
thật nào trong 3 findings** — D11 đã sửa, D10 đã sửa, D9 đã sửa.
**Nhưng 65/100 cũng không nên được đọc là "app hoàn hảo":** thang của judge
không chấm các lỗi thật thấy trên màn hình — D8 (PARTLY), D12 (PARTLY), D18,
D19, D13, D14, D17-chấm-đỏ — và không phản ánh các khoảng chưa test:
WebPlayer (0 lần mở, cả hai lần chạy), EPG bar/Mini-Guide IPTV, gate seek Thể
thao, UP lên nav từ hàng đầu các tab ngoài Home/Lịch trình, tab Tìm kiếm và
Cài đặt (0 thao tác — lần này AI kẹt trong dialog cài đặt nên không tới được),
phụ đề trên OSD bar. Chất lượng cảm nhận: **tốt hơn quick run** (3 fix lớn đã
vào), còn lại chủ yếu là các lỗi MEDIUM-LOW trở xuống + 1 lỗi MEDIUM (D19)
mới lộ ra do AI kẹt trong dialog.

---

## 9. Vấn đề của harness (không phải lỗi app, nhưng ảnh hưởng lần chạy sau)

1. **Mission viết cho layout cũ, chưa cập nhật theo KL6.5.** Mission Home Hub
   đòi portal cards + logo Canva 3D (đã xóa ở Task 4); mission Sidebar Rail
   đòi left rail (đã xóa ở Task 3). Đây là nguyên nhân trực tiếp của cả 3
   findings và toàn bộ 35 điểm trừ. **Cần cập nhật mission map trước lần chạy
   sau, nếu không full run sau sẽ ghi lại đúng 3 findings này.**
2. **Detector focus vẫn sai (N14):** `has_focus_ring: False` dù viền trắng rõ
   (step_003/004/005); `focused_view: NONE` dù nút OSD đang focus có viền
   (step_087/094).
3. **Mission "pass" lỏng lẻo + tab detector sai:** chỉ 4/16 mission
   COMPLETE_MISSION (Sports step_13, Room Picker step_18, VOD Seek step_92,
   và 1 lần ở step_39); 12 mission còn lại kết thúc bằng SWITCH_TAB giữa
   chừng nhưng vẫn tính pass. Summary ghi "Kho Phim 58 thao tác" trong khi
   phần lớn phiên AI ở Home/Thể thao/Lịch trình/player; tab 0 Trực Tiếp ghi
   1 thao tác dù AI đã ở màn hình Thể thao steps 6–22; "Cổng Chọn (Home Hub)
   4 thao tác" trong khi Home Hub là màn hình mở đầu.
4. **Video vẫn nén ~8,6x, thiếu đầu + cuối phiên (§3)** — lỗi recorder chưa
   được sửa dù đã thêm ffmpeg vào deps.
5. **Ảnh mission trùng lặp:** 12/17 ảnh mission trùng step shot (sha256):
   02≡step_006; 03≡step_013/014; 04≡step_018/019; 05≡step_023/031;
   07≡step_039/040; 08≡step_046–051; 09≡step_053; 10≡step_063;
   12≡step_075/085; 13≡step_076/084; 14≡step_092/093;
   15≡step_111/114/117; 16≡17≡step_121/124. Ảnh mission chụp cuối mission
   sau khi AI đã di chuyển, ít giá trị kiểm chứng.
6. **AI kẹt trong dialog làm lệch bao phủ:** sau step_93 AI không rời
   PlayerActivity; missions 15–17 chạy trong dialog cài đặt; Search/Settings
   0 thao tác. Một phần là lỗi app (D19), một phần là AI không thử BACK để
   thoát dialog — mission sau nên ép BACK/đóng dialog trước khi chuyển mission.

---

## 10. Sửa trước khi trình Evelyn / lần chạy sau? — Khuyến nghị

### Sửa ngay (nhỏ, sửa xong ảnh sẽ sạch hơn — không cần thêm full run để xác nhận D8/D12/D18/D19 nếu sửa đúng chỗ)

1. **D19 (MEDIUM) — dialog "Cài đặt trình phát": cho focus tới được nút ĐÓNG.**
   Kiểm tra `nextFocusDown` từ hàng "Bước tua" xuống ĐÓNG (hoặc thứ tự focus
   của dialog); kiểm chứng bằng một lần bấm DOWN từ chip "30s" tới ĐÓNG.
   Đây là lỗi duy nhất ở mức MEDIUM trong lần chạy này và là nguyên nhân
   trực tiếp khiến 2 tab không được test.
2. **D18 (MEDIUM-LOW) — episode picker từ màn hình chi tiết: cho dialog nền
   đặc** như bản trong player (step_096/f_007) — nền trong suốt hiện tại làm
   chữ mô tả/nút phía sau đè lên lưới tập.
3. **D8 (MEDIUM-LOW) — hero/nav:** hero tab Thể thao không được bắt đầu ở y=0
   sau nav trong suốt (đẩy hero xuống dưới nav như Home step_038, hoặc cho
   nav đặc ngay cả ở offset 0 khi hero hiện); kiểm tra z-order ở trạng thái
   Home đang cuộn (nút billboard không được vẽ lên trên nav). Đây là lỗi nhìn
   thấy trong **mọi** ảnh hero Thể thao + Home cuộn.
4. **D12 (MEDIUM-LOW) — hàng nút VOD tràn:** rút ngắn nhãn ("TỐC ĐỘ" → nhãn
   ngắn hơn) hoặc thu hẹp các nút để Speed + Lock hiện đủ ở trạng thái nghỉ;
   kiểm chứng bằng ảnh OSD VOD thấy đủ nút cuối (và bấm RIGHT tới Lock để
   chứng minh bar cuộn hoạt động, nếu giữ thiết kế cuộn).

### Để Evelyn duyệt (quyết định thiết kế / điều tra thêm, không chặn review)

- **D17** — chấm đỏ sau "TRANG CHỦ" là gì (xuất hiện cả khi tab khác được
  chọn)? Và gạch chân TRANG CHỦ bị hero che ở màn hình Home — sửa cùng D8
  hay chấp nhận?
- **D14** — OSD Thể thao không focus được: cần xác định là thiết kế (OSD tự
  hiện, phím tác động trực tiếp) hay thiếu focus — nếu là thiết kế thì không
  sửa, chỉ cần ghi nhận. (VOD thì focus được, nên không đồng nhất.)
- **D13** — dialog cài đặt cắt chip "Tự động (Hay)" + cắt dòng "Đang chọn:
  10s": cosmetic, dialog vẫn dùng được; sửa padding trong đợt polish sau.
- **N8/N9** — dữ liệu (tỉ số 6-0 vs luồng 2:0, 8:1, lượt xem 3726,0K, phòng
  0 lượt xem từ Lịch trình): vấn đề phía nguồn dữ liệu, cần đối chiếu field
  nguồn trước khi sửa UI.
- **D20/D21, D4/D5/D16, gate seek Thể thao, EPG bar/Mini-Guide IPTV, phụ đề
  trên OSD bar, UP lên nav từ hàng đầu các tab ngoài Home/Lịch trình** — tất
  cả đều **chưa kiểm chứng được trong lần chạy này**; cần mission ép các đường
  này (đặc biệt: mở WebPlayer thật, bấm LEFT/RIGHT ở player Thể thao, bấm UP
  từ hàng đầu mỗi tab, gọi OSD dưới ở player IPTV, mở tab Tìm kiếm/Cài đặt
  thật) thì mới có kết luận. **Ưu tiên sửa mission map (§9.1) trước khi chạy
  lại, nếu không sẽ lặp lại 3 findings oan.**

### Không merge

Đây là full run. Branch `redesign/netflix` (head `7829d25`) vẫn chờ Evelyn
duyệt APK + ảnh QA trước khi merge vào `main` — không merge, không push thêm
từ bài đánh giá này.

---

## 11. Tóm tắt: đã sửa xong vs quick run / còn lại cho Evelyn

**Đã xác nhận sửa xong so với quick run (42504300280):** D9 (clock/date),
D10 (pill "0"), D11 (episode picker — chức năng), D15 (BACK thống nhất 2 lần),
N10 (EPG thật trên hero/player IPTV), R1 (giữ nguyên).
**Còn lại, thấy rõ trên màn hình:** D8 (PARTLY — hero Thể thao + Home cuộn),
D12 (PARTLY — Speed "TỐ" + Lock chưa thấy), D13, D14, D17 (chấm đỏ),
**mới:** D18 (episode picker nền trong suốt), D19 (kẹt focus trong dialog cài
đặt — MEDIUM, chặn bao phủ 2 tab).
**Chưa có kết luận (cần mission ép đường test):** WebPlayer, EPG bar/Mini-Guide
IPTV, gate seek Thể thao, D4/D5, D16, phụ đề trên OSD bar, UP lên nav từ hàng
đầu các tab ngoài Home/Lịch trình.
**Điểm số:** 65/100 của judge là toàn bộ do 3 harness-mismatch (2 HIGH trùng
nhau + 1 MEDIUM); khử artifact thì thang judge cho 100/100 — nhưng thang đó
không chấm các lỗi thật liệt kê trên. Chất lượng cảm nhận tốt hơn quick run,
còn 1 lỗi MEDIUM (D19) + 5 lỗi MEDIUM-LOW trở xuống cần sửa trước khi trình
Evelyn là sạch nhất; phần còn lại là quyết định thiết kế (D17, D14) và các
đường test chưa bao phủ (D20/D21).

# KL8 Task 12 — Visual Review, Fix Loop 1 Re-run (by eye, không tin điểm judge)

- **QA run:** 42963719447, workflow QA-Suite, branch `redesign/apple-kl8`, HEAD `c4de57e`
- **Kết luận run:** SUCCESS, 1h29m44s (05:08:04 → 06:37:48 UTC, 12:08 → 13:37 VN), trong timeout 150 phút
- **Artifact:** `~/workspace/kenhlive-plan/qa-run-42963719447/` (11 MB, tải 1 lần OK)
- **Phiên:** QA-SESS-20261111-051218-ca4ef7, 140 bước, 122 lần bấm D-pad, 0 crash
- **Judge claim:** 78/100, 17/17 checks pass, 17/17 missions, 5 findings (4 MEDIUM, 1 LOW)
- **Eye-verdict của tôi: ~72/100 — judge vẫn bị lạm phát, nhưng ít hơn run trước.**
  Run này sửa thật được nhiều P0 nhìn thấy rõ (hero IPTV, hàng IPTV, logo VTV Cần Thơ,
  tỉ số live trên card/lịch/detail, dialog THÔNG BÁO, đồng hồ Home, WebPlayer chạm được
  lần đầu tiên). Nhưng 2 điểm lớn nhất của vòng fix 1 vẫn chưa xong: **(a) tab Home
  không hề hiện tỉ số live ở đâu cả (hero + card ĐANG PHÁT vẫn VS, kiểm 2 thời điểm
  cách nhau ~8 phút); (b) mission WebPlayer chứng minh được reach + phát thật, nhưng
  OSD KL8 không hề hiện, nút Speed không được test, tua không chứng minh được — agent
  tự bịa các chi tiết này trong thought, judge tính pass.** Thêm 1 lỗi mới nhỏ nhưng
  rõ: badge "0" vô nghĩa trên card live NBA.

## Phương pháp xem

- Xem full-size **17 mission shot** (`01`–`05`, `07`–`18`; shot `06` mission
  player-streaming KHÔNG có file).
- Xem toàn bộ **139/140 step shot** qua 9 contact sheet 4×4 (mỗi ảnh 480×270, có nhãn
  số step). **Thiếu `step_043_mission_.jpg`** — đúng bước judge flag (focus NONE),
  chỉ còn thought + timeline làm chứng.
- Xem thêm full-size riêng: `step_007` (card NBA + badge "0"), `step_024` (lưới IPTV),
  `step_038` (KÊNH NỔI BẬT), `step_047` (detail panel), `step_065` (player IPTV),
  `step_073/074/075` (Apple Pills), `step_092` (error box native), `step_098/103`
  (WebPlayer OSD), `step_107` (player native).
- Xem **video** `full_qa_tour.mp4` qua 14 khung trích — video chỉ cover ~17 phút đầu
  (cold start → tab Thể thao), không có thêm gì ngoài step shot, không có cảnh player.
- Đối chiếu từng phát hiện với `qa_session.json` timeline (140 entry, có
  `ui_state`/`focused_view`/`activity` từng bước) và `qa_report.json`.
- Không dùng điểm judge để kết luận bất cứ mục nào. Đọc code khi cần giải thích một
  pixel (ChannelBadge, MatchCardsAdapter, HeroPagerAdapter — chỉ đọc, không sửa).

## Evidence checklist (vòng fix 1)

### 1. WebPlayer (P0-1/F44) — SỬA MỘT NỬA: reach + phát thật ✅, Speed/tua ❌ chưa chứng minh
- **Reach: FIXED, lần đầu tiên trong 5 run.** Steps 94–105 activity là
  `.phim.WebPlayerActivity`, không bounce về native (force_web giữ trong mission).
  Phim embed THẬT "Pháp Sư Gian Lận Bị Sa Thái Tận Hưởng Cuộc Sống Thứ Hai (2026) -
  Tập 01". VERIFY_STREAM pass thật: motion delta 19,83% → 22,19% → 33,79% → 44,49%,
  khung hình đổi liên tục, thời gian chạy 05:52 → 09:02. Mission shot 15 full-screen
  video thật. `step_094`–`step_105`.
- **Play/pause: OK.** OK ở step 97/100/105 toggle pause/play (nút play giữa màn hình
  hiện/mất, motion 0% ↔ >10%).
- **Seek: KHÔNG chứng minh được.** Vị trí ở step 098 là 05:52, ở step 100 vẫn 05:52
  (sau DPAD_RIGHT + DPAD_LEFT lúc pause), ở step 103 là 09:02 — đúng bằng thời gian
  phát tự nhiên giữa các bước, không tách được tác dụng của phím tua. Thought agent
  tự bịa số ("00:02 / 24:14" ở step 99, "00:52" ở step 100) trong khi ảnh chụp vẫn
  05:52 — bằng chứng agent hallucinate.
- **Speed (F47): KHÔNG TEST ĐƯỢC — OSD KL8 không hề hiện.** `step_098` và
  `step_103` full-size chỉ thấy điều khiển của **chính embed** (title bar, nút play
  giữa, thanh -10/+10, volume, 05:52/24:14, bánh răng ⚙️, PiP, fullscreen).
  **Không có nút "TỐC ĐỘ 1X", không có "TẬP TIẾP", không có "DANH SÁCH TẬP"** ở bất
  kỳ step 94–105 nào. DPAD_DOWN 2 lần (steps 95–96) + 1 lần (101) không mở được OSD
  KL8 (focus NONE, không focusable view). Agent vẫn viết trong thought "OSD đã hiển
  thị đầy đủ… TỐC ĐỘ 1X… probe playbackRate pass", rồi ở step 104 tự thú nhận bằng
  cách gọi bánh răng của embed là "nút TỐC ĐỘ 1X (biểu tượng bánh răng ⚙️)". OK ở
  step 105 chỉ toggle play/pause, không đổi tốc độ, không có menu tốc độ nào hiện.
  Kết luận: probe F47 chưa biết pass hay fail; nút Speed chưa từng hiện. Theo luật
  mission ("không có nút thì ghi nhận là đúng gate") thì đây không phải lỗi app —
  nhưng **"đã test Speed" là claim sai**, judge tính pass cho check WebPlayer là lạm phát.
- **Hardsub:** phụ đề tiếng Việt trong các shot WebPlayer (vd `step_103`: "Cứ kệ cho
  họ đấm tôi một phát xem nào." đè lên seekbar) vẫn là hardsub cháy trong khung hình
  — KHÔNG flag, theo non-defect (a).

### 2. Home (P0-2) — FIXED (mission mới), 1 điểm chưa đủ bằng chứng
- Mission mới `MISSION_HOME_BILLBOARD_6_ROWS` chạy đúng: SWITCH_TAB(6) mở Trang Chủ,
  không còn mission Tab 6 Hub portal cũ. Billboard hero đo được 1920×648 ≈ 60% chiều
  cao 1080px (agent tự đo, khớp ảnh `step_033`–`step_034`).
- **Hàng: chỉ thấy 4/6.** ĐANG PHÁT (3 card) → TRẬN SẮP DIỄN RA (3 card AFC U17) →
  PHIM MỚI CẬP NHẬT (29 phim, `step_036`) → KÊNH NỔI BẬT (12 kênh, `step_037`–`039`).
  Agent dừng ở hàng 4, không cuộn tiếp — 2 hàng còn lại (nếu có) chưa được thấy trong
  run này. Không kết luận là thiếu hàng, chỉ là chưa đủ bằng chứng cho "6 hàng".

### 3. IPTV hero (P0-3) — FIXED, có bằng chứng bắt buộc
- `11_mission_iptv_epg_and_zapping_player.jpg` (và steps 54–64): với strip EPG
  "LỊCH PHÁT SÓNG HÔM NAY" đang hiện, hero "VTV10 / Thể thao / 12:30 - 13:00" nằm
  hẳn dưới nav, nav đọc rõ, **nút "XEM KÊNH" hiện ĐẦY ĐỦ** (focus, viền trắng).
  `step_056` (VTV1 HD "Talk VietNam…") và `step_024` (VTV Cần Thơ) tương tự. Slack
  ~1–21dp đã đủ.

### 4. Sport bottom row (P0-4) — UNCONFIRMED (không test được trong run này)
- Player Thể thao chỉ được mở đúng 1 bước (step 43, từ RoomPicker TOP 01) rồi agent
  bấm OK và rời ngay (step 44 đã về MainActivity). **Không có screenshot step 43**
  (file thiếu), video timelapse không cover đoạn này. Không có ảnh nào của bottom row
  sport ("Về trực tiếp" / "TRỰC TIẾP") trong cả run. Không thể kết luận fix đúng hay
  sai — cần mission có định hướng tới player sport và chụp OSD.

### 5. VOD subtitles (P0-5/F46) — UNCONFIRMED (không có cue text-track thật nào)
- Toàn bộ phụ đề thấy trong run (WebPlayer steps 85–87, 94–105; native steps
  107/116/122) đều là hardsub của cùng stream phim embed — KHÔNG flag theo
  non-defect (a). `step_107` full-size: không có cue nào đè seekbar.
- **Không có track text nào được load** (dialog "Âm thanh & Phụ đề" mở được ở steps
  124–129 nhưng không thấy track phụ đề thật nào) nên anchor F46 cho cue thật vẫn
  chưa được kiểm trên máy. Giữ nguyên trạng thái "fix đã làm, chưa có bằng chứng".

### 6. IPTV player BACK (P0-6) — UNCONFIRMED trực tiếp, gián tiếp ổn
- Không có lần bấm BACK nào trong lúc ở trong player IPTV ở run này (các lần thoát
  player đều bằng OK trên QUAY LẠI hoặc SWITCH_TAB). Scenario gốc (BACK → OSD hiện
  lại trong player, focus NONE) không tái hiện.
- Gián tiếp: focus luôn hiện hữu ở player IPTV (`step_065`: QUAY LẠI có viền trắng;
  `step_067/069`: backBtn); sau khi thoát về lưới (steps 66/68) focus nằm trên card
  kênh, không NONE. Sau BACK ở native VOD (step 92 → 93, step 130 → 131) focus về
  MainActivity trên 1 view, không NONE. Phù hợp fix, nhưng **không phải bằng chứng
  trực tiếp cho P0-6**.

### 7. TV360 rows (P0-7/F21) — FIXED, 1 điểm chưa đủ bằng chứng
- Không còn hàng TV360 75 kênh. Lưới IPTV: #05 VTV Cần Thơ, #06 VTV1 HD, #07 VTV10,
  #08 VTV2 HD (kèm EPG từng kênh), header **"HTV / VTC — 19 kênh"** ngay dưới
  (`step_024`, `step_054`–`055`). Pills nhóm: VTV / HTV / VTC / VTVcab / SCTV /
  Thể Thao / Phim truyện / Giải trí (`step_059`–`063`).
- **HTV7 chưa thấy:** nội dung hàng HTV/VTC chưa bao giờ được cuộn vào khung hình
  (chỉ thấy header). Không xác nhận được HTV7 có trong hàng đó không.

### 8. Logos (P0-8/F58/F59) — FIXED phần nhìn thấy; VTVcab chỉ có bằng chứng code
- **VTV Cần Thơ → "VTV": FIXED.** `step_024` full-size: card #05 logo "VTV"
  (trước đây "ANTV"). Home rail: #01 ANTV HD → "ANTV" ✓, #02 QPVN HD → "QPVN" ✓,
  #03 SCTV2 → "SCTV2" ✓ (`step_038`). Player IPTV: VTV10 logo màu đúng
  (`step_065`), VTV1/VTV2 đúng (`step_024`).
- **VTVcab → "VTVCAB": chỉ có bằng chứng code, không có ảnh.** Nhánh VTVCAB đứng
  trước nhánh VTV trong `ChannelBadge.kt:52` (fix F59 đã vào code), nhưng không card
  VTVcab nào hiện trong run (pill "VTVcab / SCTV" được focus ở step 60 nhưng lưới
  dưới không đổi). Chưa xác nhận bằng mắt.
- **Mới (liên quan F59): SCTV6 (Fim360) hiện badge "TV360".** `step_038`/`07_mission`:
  card #04 "SCTV6 (Fim360)" mang badge "TV360". Đọc code: `ChannelBadge.kt:63`
  `n.contains("360") -> "TV360"` — tên "FIM360" trúng nhánh này. Nhãn "TV360"
  (dịch vụ Viettel) cho kênh Fim360 là sai họ đài, cùng lớp lỗi với F59. Nhỏ nhưng
  rõ, cho vòng 2 (thêm nhánh SCTV trước nhánh "360", hoặc chỉ khớp "TV360").

### 9. Live scores (Q9/R10 — ưu tiên cao nhất) — SỬA ĐƯỢC 3/4 MẶT, MẶT QUAN TRỌNG NHẤT VẪN HỎNG
- **Card trận live: FIXED, tỉ số thật.** `03_mission_sports_multi_source.jpg` +
  `step_007` full-size: SAC–ORL **90 : 101**, POR–OKC **54 : 54**, SAC–ORL
  **87 : 96**, LIVE badge, tên giải "Bóng Rổ NBA". Tên đội trên card vẫn ellipsize
  ("Portl…", "Oklah…") do card hẹp — hình học card, không phải lỗi dữ liệu.
- **Hero: VẪN HỎNG — hero không hiện tỉ số.** Hero POR–OKC hiện **"VS"** ở cả 2
  thời điểm: cold start 12:12 (`02_mission_cold_start`, steps 2–6) và Home mission
  ~12:20 (`step_033`–`034`), trong khi cùng lúc đó tab Thể thao hiện 54:54 → 59:59
  → 64:61. Code hero (`HeroPagerAdapter.kt:206-222`) đã đọc `g.hostScore`, nhưng
  **dữ liệu feed vào tab Home không mang điểm** — cả hero lẫn card ĐANG PHÁT đều VS,
  trong khi cùng adapter đó ở tab Thể thao hiện điểm. Đây là lỗi plumbing của Home,
  không phải lỗi render. **Đây là item loop-2 số 1.**
- **Card ĐANG PHÁT trên Home: VẪN HỎNG (cùng gốc với hero).** Cả 3 card ĐANG PHÁT
  hiện VS ở steps 2–6 và 33–35, trong khi tab Thể thao/Lịch hiện điểm thật.
  (Lưu ý: ở cold start, card Home hiện "SOCO" provider chip, không có badge "0" —
  xem N2 dưới — chứng tỏ Home dùng data instance khác với tab Thể thao.)
- **Detail panel: FIXED.** `step_042`: RoomPicker POR–OKC **64 : 61** với tên đầy
  đủ 2 đội. `step_015`–`016`: SAC–ORL 87:96 full names.
- **Player pill (trong player): UNCONFIRMED.** Không có ảnh pill tỉ số trong
  PlayerActivity (player sport chỉ mở 1 bước, không screenshot).
- **Lịch live row: FIXED.** `04_mission_...` + `step_041`/`step_044`: hàng live
  "59 : 59" đỏ + badge Live + tên đầy đủ "Portland Trail Blazers vs Oklahoma City
  Thunder" thay cho giờ đá; các trận sắp đá hiện giờ (16:30, 21:00, 14:30) đúng.
- **Negative controls:** không có tỉ số ảo nào trong 140 bước (0 score >9, 0 score
  bịa). Trận SOCO-only vẫn VS đúng kỳ vọng loop-2: Juarez–Chivas VS (`step_017`–`018`),
  các trận AFC U17/JLC sắp đá hiện giờ, không điểm. **"2:8 vẫn hiện" và "tỉ số phi
  lý → VS": KHÔNG được test** — mission data-accuracy (steps 20–23) tìm trận KẾT
  THÚC nhưng không có trận nào đã xong trong list (1 live + 3 sắp đá), không có dữ
  liệu phi lý nào xuất hiện để gate chặn. Chỉ kết luận "không bịa điểm", không kết
  luận "gate phi lý hoạt động".

### 10. P1s — 2/3 FIXED, 1 UNCONFIRMED
- **P1-2 đồng hồ Home: FIXED.** Nav sạch ở mọi shot Home: "CÀI ĐẶT" hiện đầy đủ,
  đồng hồ "12:12 / Thứ Tư, 11/11/2026" nằm dưới nav, đè lên vùng trống của hero
  (`02_mission_cold_start`). Không còn chồng "TÌM KIẾM"/"CÀI ĐẶT" như run trước.
- **P1-3 dialog THÔNG BÁO: FIXED.** `01_cold_start`: dialog sạch, 2 nút
  "ĐÃ HIỂU / ĐÓNG" (focus, viền trắng đỏ) + "VÀO NHÓM TELEGRAM" đều nhìn rõ, QR rõ.
  Step 1 bấm OK → step 2 dialog đóng ngay, **đóng ở lần bấm đầu** (run trước cần 3
  lần OK + BACK).
- **P1-4 Mini-Guide "Danh Sách Kênh": UNCONFIRMED.** Mini-Guide không được mở lần
  nào trong run (không có mention nào trong 140 thought). Không thể kết luận.

### 11. F45 ("Tập tiếp" flash khi cold-open tập cuối) — UNTESTABLE (lần 2)
- Agent chỉ duyệt Tập 1–5 trong EpisodePicker (steps 77–81), đóng dialog ở step 82,
  không mở thẳng tập cuối (Tập 6) lần nào. Cần test đích danh ngoài QA suite.

### 12. Harness — CHẠY SẠCH, nhưng 2 chỗ judge lạm phát
- Autonomous suite chạy thật: `run_qa.py` → `AutonomousQASuite`, 17 mission mới
  (gồm `MISSION_HOME_BILLBOARD_6_ROWS`, `MISSION_WEBPLAYER_DIRECTED_REAL_FILM`),
  140 bước, 7/7 tab, `auto_failovers_observed: 0`, 0 lần nhắc "fallback" trong JSON.
  Không mission nào tự complete mà chưa tới đích theo kiểu run trước (P0-2 đã dọn).
- **Nhưng 2 check pass là lạm phát:**
  - Check WebPlayer (12 bước) pass trong khi Speed/tua không chứng minh được (mục 1).
  - Check "Trình Phát Native…, Toàn Bộ Chức Năng" (19 bước) pass trong khi native
    VOD **không phát được lần nào ra hồn trên emulator**: step 92 lỗi
    `ERROR_CODE_PARSING_CONTAINER_UNSUPPORTED`, steps 108–119 lỗi
    `ERROR_CODE_DECODING_FAILED` lặp lại (THỬ LẠI → phát được vài giây → lỗi lại).
    19 bước đó thực chất chỉ chứng minh được **dialog Cài đặt** (steps 124–129 mở
    và điều hướng tốt). Đây là giới hạn codec emulator — non-defect (c) — nhưng
    "Toàn Bộ Chức Năng" là over-claim; cần xác nhận native playback trên máy thật.
  - Tương tự: check "Trình Phát Video ExoPlayer, Server Picker & Phím Tắt TV
    (A/B/Menu)" (8 bước, steps 24–31) pass trong khi agent chỉ bấm DPAD/OK trên
    player IPTV — không bấm A/B/Menu, không mở Server Picker.

## Findings mới trong run này (ngoài checklist)

### N1 (P0, loop 2 — quan trọng nhất). Home không mang tỉ số live
- Xem mục 9: hero + card ĐANG PHÁT trên Home luôn VS (12:12 và 12:20), tab Thể
  thao/Lịch/Detail cùng thời điểm hiện điểm thật. `HeroPagerAdapter` đã đọc điểm
  nhưng data feed Home không có điểm. Cần sửa plumbing data của Home (hoặc Home
  refresh/enrich như tab Thể thao), rồi chụp lại hero + card Home có điểm.

### N2 (P1). Badge "0" vô nghĩa trên card live NBA (tab Thể thao)
- `step_007` full-size: card POR–OKC và SAC–ORL có 1 pill xám nhỏ ghi **"0"** ngay
  trước pill LIVE, và chip nguồn (SOCO) bị ẩn. Đọc code `MatchCardsAdapter.kt:406-413`:
  đó là `cardTimeBadge` hiện `g.liveClock` — liveClock = "0" (NBA không có phút thi
  đấu, nguồn trả "0"), `validClock` chỉ loại blank/"null" nên "0" lọt qua, rồi code
  ẩn provider để nhường chỗ. Nhánh upcoming đã chặn `kickoff != "0"` (dòng ~431),
  nhánh live thì không. Fix 1 dòng: coi liveClock "0"/"0'" là invalid như kickoff.
  Lưu ý: card Home cùng trận không có badge "0" (liveClock blank ở đó) — lại là bằng
  chứng Home dùng data khác.

### N3 (P1). Focus NONE khi video load xong ở trạng thái pause (judge đúng)
- Step 43 (PlayerActivity, sport, video đã load, đang pause, nút PHÁT giữa màn
  hình): `focused_view = NONE`, thought agent tự ghi nhận "không auto-focus vào nút
  phát". Tái hiện ở native VOD: steps 107–113 focus NONE 6 bước liền sau khi error
  box hiện (108), tới step 114 focus mới rơi vào btnPlayerBack, step 115
  btnPlayerRetry (THỬ LẠI). Người dùng bấm remote 6 lần "mù" trước khi thấy focus.
  (Chụp step 92 thì THỬ LẠI có viền trắng dù dump ghi NONE — dump và mắt lệch nhau
  ở điểm này; nhưng 108–113 thì cả dump lẫn ảnh đều không có focus.)
  Liên quan F54 (allowlist restore focus thiếu 3 nút error-box). Fix: default focus
  vào nút phát khi player pause sau load + focus mặc định vào THỬ LẠI khi error box
  mở.

### N4 (P2/minor). Judge sai về Apple Pills — focus ring CÓ, chỉ mỏng
- 3 finding MEDIUM của judge (steps 73/74/75: "Focus border không hiển thị") là
  **sai khi xem bằng mắt**: `step_074` "Lịch Sử Xem" có viền trắng mỏng rõ,
  `step_075` "Tìm Kiếm" tương tự; `step_073` "Tất Cả" trắng đặc là trạng thái
  *selected* (đã trắng từ steps 71–72 trước khi focus tới), không phải focus.
  Hạ xuống minor: ring của pill mỏng hơn hẳn viền focus chuẩn ở nav/card (10-foot
  khó phân biệt focus với selected). Nên làm dày/đậm theo DESIGN-SYSTEM §8.

### N5 (P2/minor). Nav trên không có scrim — nội dung cuộn lên chồng chữ nav
- `03_mission_sports_multi_source`: header "Hiệp hội Bóng rổ Quốc gia" khi cuộn lên
  đè lên chữ nav TRANG CHỦ/TRỰC TIẾP. `step_047`: header "Hôm nay" nửa hiện nửa
  mất trong vùng nav sau dialog. `14_mission_...`: tiêu đề detail phim lấp ló sau
  nav. Nav trong suốt, không nền đặc → bất kỳ nội dung nào cuộn tới mép trên cũng
  va chữ nav. Nên thêm scrim/nền cho top nav (giống hero IPTV đã có top inset).

### N6 (P2/minor). Nút "Tự động (Hay)" bị cắt ở mép phải dialog Cài đặt
- `16_mission_player_settings_dialog` + steps 125–129: hàng Âm thanh có 5 nút, nút
  cuối "Tự động (Hay)" bị cắt ở mép panel (chỉ thấy "Tự động (Hay) •"). Hàng quá
  rộng so với dialog; cần thu nút hoặc cho cuộn ngang.

### N7 (harness, minor). Thiếu bằng chứng + nhãn cũ
- Thiếu `step_043_mission_.jpg` (đúng bước judge flag) và mission shot `06`
  (player-streaming). Tab 6 trong `tabs_coverage` vẫn ghi tên cũ "Cổng Chọn
  (Home Hub)" dù tab đã là Trang Chủ. Video timelapse chỉ cover ~17 phút đầu của
  run 89 phút. Không ảnh hưởng kết luận, nhưng lần sau nên đủ shot.

## Những gì đã tốt (xác nhận bằng mắt)

- **WebPlayer chạm được lần đầu sau 5 run** (F44 deep-link hoạt động): embed thật,
  phát thật, ở lại WebView cả mission, không bounce native.
- **IPTV sạch:** hero + XEM KÊNH + EPG strip đúng (P0-3), hàng VTV/HTV-VTC đúng
  (P0-7), logo VTV Cần Thơ đúng (P0-8), zap đổi kênh được (VTV Cần Thơ → VTV1 →
  VTV10 → VTV3), EPG trên player đúng giờ, toast "Tự chuyển luồng dự phòng" rõ ràng,
  bottom bar 6 nút đủ và không cắt ("Kênh trước / Kênh kế / EPG / Yêu thích /
  Tỉ lệ Fill / Cài đặt", `step_065`).
- **Tỉ số live có thật lần đầu tiên:** card 54:54 / 87:96 / 90:99 / 90:101, detail
  64:61, lịch 59:59 — 0 tỉ số ảo, 0 điểm bịa trong 140 bước.
- **Dialog THÔNG BÁO + đồng hồ Home** sửa dứt (mục 10).
- **Settings dialog native đầy đủ và điều hướng tốt** (Hình ảnh/Âm thanh/Tỉ lệ/Bước
  tua + ĐÓNG, focus rõ từng mục, steps 124–129; `16_mission_...`).
- **Tìm kiếm + Cài đặt sạch:** search "bóng đá" ra trận live có league/phòng,
  search phim ra 4 kết quả có poster/năm; Cài đặt không crash sau chaos D-pad
  (steps 135–140).
- **TIẾP TỤC XEM (1 phim)** xuất hiện sau phiên WebPlayer (`step_088`–`091`,
  `step_131`) — resume row hoạt động.
- **Native player bar:** TUA ±10S / TẬP TIẾP / DANH SÁCH TẬP / ÂM THANH & PHỤ ĐỀ /
  TỐC ĐỘ 1X đủ, nút focus có viền trắng rõ, nhãn phải = thời gian còn lại 22:28
  đúng Q3 (`step_107`). Bar cuộn được theo R8 (nút thứ 6 lấp ló mép phải là đúng
  thiết kế scroll, không phải lỗi).

## Đề xuất vòng fix 2 (ưu tiên)

1. **N1 — Home mang tỉ số live (P0):** hero + card ĐANG PHÁT phải hiện cùng điểm
   với tab Thể thao. Đây là hạng mục Evelyn dặn ưu tiên cao nhất; chưa xong thì
   Task 12 chưa đóng được.
2. **WebPlayer OSD + Speed (P0-1 phần còn lại, F47):** làm cho DPAD_DOWN mở được
   OSD KL8 trong WebPlayer (hiện tại 3 lần bấm không mở), rồi test Speed bằng cách
   bấm nút "TỐC ĐỘ 1X" thật và đọc lại nhãn; tua phải đọc lại vị trí sau khi tua
   (read-back), không tin thought agent. Sửa mission để fail nếu không thấy OSD.
3. **N2 — badge "0":** chặn liveClock "0"/"0'" ở nhánh live (`MatchCardsAdapter`),
   mirror guard của kickoff.
4. **N3 — focus mặc định:** player pause sau load focus vào nút phát; error box mở
   focus vào THỬ LẠI (kèm F54: thêm 3 nút error-box vào allowlist).
5. **Các mục chưa test được cần mission có định hướng riêng (không trông chờ agent
   tự đi tới):** P0-4 bottom row sport ("Về trực tiếp"), P0-6 BACK trong player
   IPTV, P1-4 Mini-Guide "Danh Sách Kênh", F45 mở thẳng tập cuối. Nếu QA suite
   không tới được các state này thì ghi rõ là manual test, đừng để check pass trên
   danh nghĩa.
6. **Minor (gộp 1 đợt):** N4 ring pill dày lên; N5 scrim top nav; N6 dialog Cài đặt
   (nút âm thanh thứ 5); N7 SCTV6 badge (nhánh SCTV trước "360"); label tab 6
   ("Trang Chủ"); đảm bảo đủ step screenshot + mission shot.
7. **Native VOD trên máy thật:** playback/seek/resume native chưa từng chứng minh
   được trên emulator (lỗi codec lặp lại) — cần 1 lần chạy/chụp trên TV thật trước
   khi kết luận "không phải lỗi app" (nối tiếp P1-5 run trước).

## Kết luận

**Task 12 vẫn chưa đóng được.** Vòng fix 1 sửa thật được phần lớn P0 nhìn thấy
(P0-2, P0-3, P0-7, P0-8, P1-2, P1-3, tỉ số trên card/lịch/detail, WebPlayer reach),
nhưng **2 hạng mục lớn nhất còn dở**: tỉ số live chưa lên tab Home (hero + card),
và mission WebPlayer chưa chứng minh được Speed/tua (agent bịa OSD). Cộng thêm lỗi
mới badge "0", focus NONE sau load/error, và 4 mục (P0-4, P0-6, P1-4, F45) vẫn
chưa được test lần nào sau 2 run. Cần vòng fix 2 + chạy lại có định hướng (ít nhất
hero Home có điểm + WebPlayer OSD/Speed + các state chưa tới được), rồi mới báo
cáo cuối cho Evelyn. Không merge gì.

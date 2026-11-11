# CI-T4 Eye Review — run 42993141273 (main @767cb7e, full 17 missions)

QA 1534s (25m34s), 95 bước, 8/17 PASS, 0 UNVERIFIED, điểm 65/100, verdict
NEEDS_FIX. NIM 5 requests, 0×429, provider OPENAI. Video 1225s ghi được /
1534s chạy (80%, 7 chunk) → tour 306s @4x. Reel 12.3s (2×6s).
Đã xem: cả 33 shot trong `shots/` + 3 frame video (v_53/v_60/v_67) + 2 frame
reel (r_3/r_9) + `qa_report.json` + timeline + log `/tmp/cit4.log`.

## 1. Sửa CI-T4 — kiểm chứng bằng mắt (tất cả đều chạy đúng)

| # | Sửa CI-T4 | Kết quả mắt |
|---|---|---|
| 1 | Reel chia `video_t` cho speed_factor | ✅ **ĐÃ SỬA.** Reel 12.3s = 2 đoạn × 6s, không đoạn nào rỗng. r_3 (tour 20.9s) đúng frame hero bóng rổ 54:71 = finding 1; r_9 (tour 148.4s) đúng tab IPTV lúc finding 2. Report ghi `video_speed_factor: 4.0`, entries có `video_t` đã chia. (Cắt `-c copy` có thể lệch vài giây so với frame trích dẫn — chấp nhận được cho reel.) |
| 2 | Fake-score: lọc bounds + ổn định 2 lần | ✅ **FP đồng hồ BIẾN MẤT.** Không còn finding nào tố đồng hồ MM:SS (CI-T3 có 3). Không finding OCR rác nào. |
| 3 | Dump lọc node ngoài viewport | ✅ Không còn gate PASS nhờ text offscreen (xem §3 — giờ FAIL trung thực khi header cuộn khỏi màn hình). |
| 4 | Frame evidence cho mọi outcome | ✅ **ĐÃ SỬA.** Tất cả 17 frame evidence mission + 2 frame finding đều tồn tại trên đĩa (CI-T3 thiếu 6/7 frame FAIL). |
| 5 | Kẹt A-B-A-B | ✅ **BẮT ĐƯỢC.** PLAYER_STREAMING FAIL đúng với lý do "luân phiên qua lại cùng trạng thái" (timeline: MainActivity ↔ PlayerActivity, bước 22–25). |
| 6 | Guard OCR chuỗi rác | ✅ Không còn finding kiểu 'LPđPfUHPBIHUALI'. |
| 7 | Motion poll 10s + `motion_delta: null` | ⚠️ Một nửa: timeline ghi đúng 17 lần `null` (chưa đo được) thay vì 0.00. Nhưng VOD vẫn FAIL oan (xem §4). |
| 8 | Stress gate kiểm foreground | ✅ STRESS PASS thật: app còn foreground ở tab Tìm kiếm sau chuỗi phím chaos (step_096). |
| 9 | Đếm NIM | ✅ `requests_used: 5` = đúng 5 vision calls (4 stuck_assist + 1 confirm), `retries: 0`, `provider: OPENAI`. |
| 10 | Band hero OCR | ⚠️ Đã chạy (detect tổng 396.9s — xem §5) nhưng **không bắt được** lỗi hero giờ đè phụ đề (step_006/016) — tesseract gộp 2 lớp chữ chồng thành 1 box, cùng giới hạn như P0-3. |

## 2. Findings — 1 thật / 1 giả (precision 1/2, CI-T3 là 1/5)

1. **`54 : 71` (step_012) — FALSE POSITIVE, loại mới.** Đây là tỉ số bóng rổ
   THẬT, đang chạy: giải "Liên đoàn Bóng rổ Quốc gia Úc" (NBL), South East
   Melbourne vs Illawarra Hawks, tick 54:69 (t=27, step_004) → 54:71 (t=79–139,
   step_011/012/016). Luật plausibility (một đội > 9 → giả) là luật BÓNG ĐÁ,
   không áp được cho bóng rổ. **Bằng chứng ngược:** subtitle hero ghi rõ
   "Liên đoàn Bóng rổ Quốc gia Úc" (step_016) và header row "Liên đoàn Bóng rổ
   Quốc gia Úc" (step_011) — ngữ cảnh môn thể thao CÓ trong dump, detector
   không dùng. Lưu ý mở: cùng cặp đấu này hiện 0:0 ở frame video v_60
   (~t=240) — có thể do lệch thời gian video 4x, hoặc dữ liệu 2 nguồn
   (COLA vs GIỜ VÀNG) không khớp nhau; chưa kết luận, cần app kiểm tra.
2. **`66 kênh` (step_052) — THẬT.** Header "Địa Phương — 66 kênh" thấy rõ ở
   góc dưới phải. Cùng lớp với P0-7 (CI-T3 cũng bắt). Điểm sẽ là 77 thay vì
   65 nếu bỏ FP #1 (100 − 12 − round(9/17×20) = 77).

## 3. 8 PASS — đều thật (0 false pass), 2 PASS "mềm" cần ghi nhận

- Thật chắc: COLD_START (004, Home sạch, tỉ số thật), HOME_BILLBOARD (031),
  PHIM_NGUONC (060), WEBPLAYER_DIRECTED (082, phim phát 03:17/24:14, OSD
  hiện), PLAYER_SETTINGS_DIALOG (086, dialog Cài Đặt sạch, 02:06/22:07),
  SEARCH_AND_SETTINGS (090, 39 kết quả), STRESS (096, app còn foreground).
- IPTV_EPG PASS — **mềm**: player mở được thật (Vietnam Today HD, EPG
  NEWSLINE 16:00–16:30 thật, step_056/057) nhưng bằng chứng motion
  (md 24.68) đo được ở MainActivity SAU khi player tự thoát, không phải
  trong player. Gate đếm `motion_seen` ở bất kỳ observation nào, không gắn
  với activity đích. PASS về đích là thật, bằng chứng motion thì không đúng
  chỗ.

## 4. 9 FAIL — phân loại

| Mission | Lý do | Mắt thấy gì | Loại |
|---|---|---|---|
| SPORTS_MULTI_SOURCE | thiếu text 'socolive' (8 bước) | Tab Trực tiếp hiển thị tốt, tỉ số thật 0:4/0:0/0:9; không có hàng nào ghi 'socolive' trong 8 bước (driver chỉ đi DOWN/RIGHT trong 2 hàng đầu) | Harness: driver không tìm đủ sâu |
| SPORTS_ROOM_PICKER | không thấy dialog (6 bước) | OK trên thẻ trận mở PLAYER (step_018: SOU 54-71 ILL, "Đang tải luồng...") chứ không mở dialog chọn phòng | Harness (nợ P2): không phân biệt OK-mở-dialog vs OK-mở-player |
| SPORTS_DATA_ACCURACY | thiếu text 'hôm nay' (4 bước) | Tab Lịch đấu hiển thị TỐT, tỉ số thật 0:0/0:9/0:4 (step_021/022) — nhưng header "Hôm nay" đã cuộn khỏi màn hình trước observation đầu tiên. CI-T3 PASS được là nhờ dump cũ chứa text offscreen (đúng lỗ reviewer chỉ ra) — CI-T4 FAIL mới là trung thực | Harness: cần cuộn lên đầu trước khi gate đọc text header |
| PLAYER_STREAMING | kẹt A-B-A-B (4 bước) | Driver mở thẻ [SẮP ĐÁ] ĐTQ Việt Nam 19:00 (chưa đá!) → player "Đang tải luồng..." vô hạn → player tự thoát → mở lại → dao động. Thêm nữa: ở bước 23, `wake_osd` bấm OK khi focus NONE; sau đó player thoát (có thể do OK đó, hoặc stream lỗi tự thoát). App cũng có lỗi: trận chưa bắt đầu phải hiện "chưa bắt đầu", không phải loading vô hạn | Harness (chọn sai mục tiêu LIVE) + app (loading vô hạn cho trận chưa đá) |
| SCHEDULE_EPG | thiếu text 'hôm nay' (6 bước) | Như DATA_ACCURACY (step_036/037: danh sách thật, header cuộn mất) | Harness (như trên) |
| SIDEBAR_RAIL | thiếu view railPanel (7 bước) | DPAD_LEFT đưa focus về nav_home (step_041/044), rail không mở lần nào — lỗi app còn tồn tại từ KL8 audit (rail không mở bằng DPAD_LEFT) | App (rail không mở) |
| IPTV_CATEGORIES | thiếu text 'tv360' (10 bước) | Tab IPTV hiển thị tốt, EPG thật (step_054: NEWSLINE 16:00–16:30; step_046: VTV Cần Thơ đúng logo VTV — P0-8 đã sửa ✅). 'tv360' chỉ có ở header row (đã cuộn mất) — badge "TV360" trên card là ẢNH logo, không phải text dump | Harness (như 'hôm nay') |
| EPISODE_PICKER | không thấy dialog (9 bước) | Nút CHỌN TẬP có ngay trên màn hình (step_061/066) nhưng driver đi lạc về Home (focus btnHeroBackHome ↔ heroPlay) thay vì tới nút đó | Harness: không có luật đi tới view đích theo id |
| VOD_PLAYER_SEEK_AND_RESUME | kẹt cấp 2 (9 bước) | **FALSE-NEGATIVE của harness.** Phim THỰC SỰ PHÁT (step_078: frame anime, nút ⏸ hiện, OSD đầy đủ) nhưng motion đo được là None/0.00 ở cả 9 bước (watcher đói mẫu trong lúc dump WebPlayer 26.6s) → no-change streak nổ trong khi video đang chạy. Đây là lỗi đo motion, không phải lỗi app | Harness: stuck không được nổ trong player khi motion là UNKNOWN (None); cần fallback pixel_diff giữa 2 frame quan sát liên tiếp |

## 5. Tốc độ — vẫn < 30 phút nhưng CHẬM LẠI (1019s → 1534s QA)

Breakdown observe (95 bước, tổng 1018.9s): wait 141.0s (p50 0.00) /
**dump 443.4s (p50 1.64, p90 21.51, max 27.85)** /
**detect 396.9s (p50 0.05, p90 7.83, max 73.35)**.
- Detect tăng 55.8s (CI-T3) → 396.9s: band hero OCR mới là chính — bước 45
  detect 64.0s, bước 48 detect 73.4s (tab IPTV, frame đông). Chưa tương xứng
  (không bắt thêm lỗi hero nào).
- Dump vẫn là nút thắt lớn nhất: 21–27s mỗi lần dump trên PlayerActivity /
  WebPlayerActivity (uiautomator dump cây WebView khổng lồ).
- Video: 1225s ghi / 1534s chạy = 80% — chunk cuối (~300s, SEARCH + STRESS)
  mất khi dừng quay (như chunk_13 ở CI-T2). Tour 306s @4x vẫn xem được.

## 6. Lỗi app thật bị bỏ sót (không có trong findings)

1. **Hero: giờ đè phụ đề** (step_006: "16:17" đè "Thứ Tư, 11/11/2026" +
   dòng phụ đề hero; step_016: "16:18" tương tự) — lỗi từ CI-T3 vẫn còn,
   hero band OCR không bắt được (tesseract gộp lớp chữ chồng). Cần vision
   check hero.
2. **WebPlayer: tiêu đề đè đôi** (step_071/078/082: "Pháp Sư Gian Lận Bị Sa
   Thải Tận Hưởng Cuộc Sống Thứ Hai (2026) · Tập 01" đè lên "Tập 01" + dòng
   text khác) — từ CI-T3 vẫn còn, detector bỏ qua vì frame player không soi
   band hero/nav. Cần vision check vùng title player.
3. **Hero title cắt trái** (step_006/011/012/016, v_60: ".iên đoàn Bóng…",
   "ational Basketball League") — chưa kết luận chắc (có thể là trạng thái
   cuộn của carousel), cần xem chuyển động trong video; không tính là
   finding chắc.
4. **Player tự thoát khi stream không tải được** (basketball 54:71, ĐTQ
   19:00, Vietnam Today HD đều "Đang tải luồng..." rồi activity tự finish)
   — app nên báo trạng thái rõ (chưa bắt đầu / lỗi luồng) thay vì loading
   vô hạn rồi thoát lặng lẽ.
5. **Phụ đề cứng (hardsub) đè hàng điều khiển WebPlayer** (step_078: "Đi
   thôi!" nửa chìm dưới thanh điều khiển; step_076 tương tự) — là phụ đề
   cháy trong video, app không neo được; ghi nhận, không tính finding
   (không phân biệt được hardsub với cue text-track).

## 7. Điểm số

65/100 = 100 − 2×12 (findings) − round(9/17×20)=11. Số học đúng. Nếu bỏ FP
bóng rổ: 77/100 — vẫn NEEDS_FIX (7 mission FAIL + 1 HIGH thật).

## 8. Kết luận cho switch-over

**CHƯA SWITCH ĐƯỢC (NEEDS-CI-T5).** Tiêu chí SWITCHOVER.md:
- Tốc độ <30p ✅ (QA 25m34s) · 0 false pass ✅ · WebPlayer ✅ · NIM ✅
  (5 req, 0×429) · frame evidence ✅ (17/17 + 2/2) · reel ✅ (12.3s)
- **0 HIGH false-positive ❌** (1 FP: tỉ số bóng rổ 54:71)
- **Eye check khớp report ❌** (3 lỗi thật bị sót: hero giờ đè phụ đề,
  WebPlayer đè đôi tiêu đề; + 1 false-negative VOD)

## 9. Danh sách sửa CI-T5 (đề xuất)

1. **Fake-score theo môn:** chỉ áp luật plausibility bóng đá khi ngữ cảnh
   là bóng đá (text lân cận có "Bóng đá"/AFC/SAFF/V-League...); nếu có
   "Bóng rổ"/Basketball/NBL/NBA → bỏ qua nhánh implausible (nhánh giờ-đội-lốt-tỉ-số
   giữ nguyên, không phụ thuộc môn).
2. **Motion fallback:** pixel_diff giữa 2 frame quan sát liên tiếp (rẻ,
   ~ms); trong player, motion UNKNOWN (None) thì KHÔNG tính streak kẹt.
3. **Driver chọn mục tiêu LIVE:** mission player chỉ mở thẻ có badge LIVE /
   không mở thẻ [SẮP ĐÁ]; trong WebPlayer đã mở mà chưa phát thì bấm Play
   (OK) thay vì chỉ WAIT.
4. **Driver cuộn lên đầu** (UP ×N) đầu mission list để header ('hôm nay',
   'tv360') hiện trước khi gate đọc — hoặc spec chấp nhận text trong
   viewport.
5. **Gate: motion phải gắn activity đích** — `motion_seen` chỉ tính khi đo
   được trong lúc đang ở `required_activity`.
6. **Tốc độ:** hero band OCR giảm chi phí (độ phân giải thấp hơn hoặc mỗi
   2 lần OCR-due mới soi hero 1 lần); đo vì sao dump player 21–27s
   (`--compressed` luôn? bỏ dump khi chỉ cần activity?).
7. **Vision check hero + title player** (1 call mỗi run, crop vùng hero /
   title) cho 2 lỗi sót #1 #2.
8. **Video:** giữ chunk cuối đang quay dở khi dừng (độ phủ 80% → >95%).
9. **Driver đi tới view đích theo id** (CHỌN TẬP, roomList...) thay vì
   explore mù; phân biệt OK-mở-dialog vs OK-mở-player (ROOM_PICKER).
10. Nợ cũ còn lại: LONG_PRESS cho IPTV favorites (chưa từng kiểm tra thật).

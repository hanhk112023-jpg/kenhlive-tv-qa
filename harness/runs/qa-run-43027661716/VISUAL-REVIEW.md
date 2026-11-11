# CI-T6 Eye Review — run 43027661716 (main @ba1e55b, full 17 missions)

QA 887s (14m47s), job 19m32s, 72 bước, 14/17 PASS, 0 UNVERIFIED, điểm 79/100, verdict
**PASS (lần đầu PASS)**. Vision 5 calls (confirm_target 2, stuck_assist 1,
check_visual 2; 93.2s, latency TB 18.6s), provider OPENAI (endpoint
integrate.api.nvidia.com), 5 requests, 0 retry, 0×429. Video 702.8s ghi được /
887s chạy (79%, 4 chunk) → tour 175.77s @4x. Reel 12.03s, cover 1/2.
Observe 419.35s, per-step p50 3.95s / p95 17.2s / mean 5.82s,
`ocr_skipped_frames` 0.
Đã xem: cả 28 shot trong `shots/` + 9 frame video (tour t=5/60/90/95/100/160/
165/172/175, reel t=2/9) + `qa_report.json` + `qa_session.json` (timeline
72 entry, step_id 1–72 không thiếu) + chạy lại `mock_test.py` độc lập (33/33)
và replay R7 (8/8 P0, 0 false pass — xem §1).

## 1. Sửa CI-T6 — kiểm chứng bằng mắt

| # | Sửa CI-T6 | Kết quả mắt |
|---|---|---|
| 1 | Khử trùng OCR text-overlap | ✅ **CHẠY ĐÚNG.** Không còn FP "Xem ngay": pill "Xem ngay" ở step_006/008/016/036 sạch, 1 pill duy nhất, không bị tố. "Xem ngay" không còn trong findings. |
| 2 | Vision check hero/title (frame cuối + hỏi rõ đè đôi + log frame) | ✅ **CHẠY ĐÚNG — LẦN ĐẦU BẮT ĐƯỢC.** 2 call `check_visual`: hero not_found (đúng — tour_005 sạch), player_title tố được tiêu đề đè đôi ở step_059 (HIGH thật, xem §2.1). Prompt mới quote đủ 2 dòng. |
| 3 | Chờ moov khi finalize video + kẹp reel vượt tour | ⚠️ **MỘT NỬA.** Reel đã kẹp đúng (entry 2 clamped, report ghi rõ "1/2 finding (1 đoạn bị kẹp do vượt tour)") — nhưng video vẫn chỉ 79% (702.8/887s, 4 chunk trong concat.txt; chunk cuối vẫn mất). Mục tiêu >95% CHƯA ĐẠT. Xem §5. |
| 4 | Spec `socolive`→`cola`, `tv360`→`kênh` | ✅ **CHẠY ĐÚNG.** SPORTS_MULTI_SOURCE PASS (UI ghi "COLA" thật, step_006/008); IPTV_CATEGORIES PASS (text 'kênh' có thật). Không còn FAIL vì text không tồn tại. |
| 5 | Luật LIVE-only cho mọi mission + nhận diện [SẮP ĐÁ] | ⚠️ **KHÔNG KIỂM ĐƯỢC ĐẦY ĐỦ.** Không mission nào mở thẻ [SẮP ĐÁ] trong run này (không có case SẮP ĐÁ để chứng minh). ROOM_PICKER vẫn mở thẻ LIVE rồi vào player loading (xem §4). |
| 6 | PLAYER_STREAMING goto-player bằng id/bounds | ❌ **CHẠY SAI TRẠNG THÁI (sửa sau review độc lập: bản đầu ghi "không kích hoạt" là SAI).** CI log cho thấy luật chạy 4 lần (`DPAD_UP [goto_live_card]` ×4, `OK [open_player]` ×3) — nhưng rule 0c2 (`driver.py`) không có nhánh "dialog đang mở" và không kiểm `has_dialog`: khi detail panel đã mở (không được nhận là dialog, xem §4), luật đuổi theo badge LIVE ở list nền sau overlay ("Trận cùng giờ") thay vì bấm OK trên phòng đang focus. Driver dao động dialog↔list (A-B-A-B) suốt 8 bước, không bao giờ vào player. Mission FAIL trung thực, nhưng lỗi là luật chạy sai trạng thái, không phải không chạy. |
| 7 | Focus-trap chỉ tính quan sát khác nhau + bỏ shot trùng | ⚠️ **MỘT NỬA.** Step_id đã liên tục (72 entry, 1–72 không thiếu — mục 9 ✅). Nhưng: (a) shot trùng vẫn được lưu (step_046 = step_047 byte-identical; step_066 ≈ step_067 cùng nội dung; **thêm sau review độc lập: step_026 = step_037 byte-identical** — trùng xuyên mission mà bản đầu bỏ sót) dù `duplicate_frame: True` đã được đánh dấu — flag có, file vẫn lưu, vì `_finish_mission` (`runner.py` ~640–644) lưu ảnh cuối mission **vô điều kiện, không check duplicate** (đường bypass); dedup chỉ bắt trùng liên tiếp, không bắt trùng xuyên mission. Timeline chỉ link 15 screenshot trong khi 28 file tồn tại. (b) focus-trap vẫn nổ FP (xem §2.2). |
| 8 | Mission player PASS cần thời gian phát tăng | ❌ **CHƯA CÓ HIỆU LỰC TRONG RECORD.** Code `gate.py` có `playback_readings` (mục 8) nhưng mọi mission player đều `playback_status: "unknown"`, `playback_readings: []` — không có reading nào được ghi live. Bằng chứng thời gian phát tăng chỉ thấy bằng mắt (WebPlayer 00:00→00:20→00:30 ở reel; native 01:13→01:53), không có trong report. Xem §3. |
| 9 | Timeline thiếu step_id 14 | ✅ **CHẠY ĐÚNG.** 72 entry, step_id 1–72 liên tục, không thiếu số nào. |
| 10 | Audit video_recorder + nhãn provider thật | ✅ **CHẠY ĐÚNG.** Report ghi rõ `provider: OPENAI`, `endpoint_host: integrate.api.nvidia.com`, không còn ghi nhầm "NIM". `video_recorder.py` chỉ đổi ở mục 3 (moov); chữ ký hàm không đổi. |

Replay R7 (tự chạy lại, code CI-T6, artifact 42950738729): **8/8 P0, 0 false pass,
6 vision calls (NVIDIA_NIM), 0×429, 142.4s** — NIM đã hết chập chờn, con số
6–7/8 của implementer đúng là lỗi transport (`Connection reset by peer`),
không phải hồi quy. Mock tự chạy lại: 33/33 `_OK`, exit 0.

## 2. Findings — 1 thật / 1 giả (precision 1/2, CI-T5 là 1/3)

1. **`Tiêu đề player đè đôi` (step_059) — THẬT, HIGH.** Vision xác nhận chữ
   chồng: "Tình Yêu Trong Vỏ Bọc / Tình Yêu Ngụy Trang" đè lên "Tình Yêu
   Ngụy Trang (2026) · Tập 01". Mắt kiểm: đúng, 2 dòng chồng nhau không đọc
   được (step_055/056/059 đều thấy). Đây là lỗi HIGH thật mà harness 3 vòng
   (T3/T4/T5) không bắt được — vision check mục 2 nay đã bắt được. Reel
   entry 1 khớp đúng nội dung (reel t=2s: OSD 00:30, tiêu đề đè đôi thấy rõ).
2. **`Nghi vấn kẹt Focus` (step_067) — FALSE POSITIVE, MEDIUM, cùng họ với
   T5.** Chi tiết: "DPAD_DOWN liên tiếp nhưng tiêu điểm giữ nguyên tại
   'searchInput#...'". Nhưng bằng chứng ảnh cho thấy: (a) bàn phím đang MỞ
   (item 7 yêu cầu không nổ khi có bàn phím — guard không nhận ra bàn phím
   vì dump không bao giờ lộ IME); (b) phím highlight trên bàn phím CÓ đổi:
   **⇧ (step_066) → 'z' (step_067)** → 'q' (tour t=172s/175s, reel t=9s) →
   '▶' (step_071, STRESS). *(Sửa sau review độc lập: bản đầu ghi nhầm
   "'z' (step_066/067)" — crop phóng to step_066 cho thấy phím trắng là ⇧
   shift, không phải 'z'.)* Focus trong bàn phím di chuyển được; "kẹt tại
   searchInput" chỉ là focused_view trong dump không phản ánh highlight
   của IME. Guard bàn phím của mục 7 (đếm ≥8 text 1 ký tự trong dump) không
   có gì để đếm: `ui_state` lưu ở step 66 chỉ có 5 trường (focused_view/
   text/bounds/ring) — không có danh sách text, không có node bàn phím nào;
   mock N5(c) chỉ chứng minh detector vì test truyền `keyboard_open=True`
   bằng tay, không chứng minh được hành vi live. Reel entry 2 (t=9s) cũng
   cho thấy bàn phím với 'q' đang highlight — đoạn reel không chứng minh
   được finding. FP loại này đã 2 vòng liên tiếp.

## 3. 14 PASS — đều thật (0 false pass), 3 PASS "mềm" cần ghi nhận

- Thật chắc: COLD_START (004, Home sạch), SPORTS_MULTI_SOURCE (006/008, tỉ
  số thật 5:3/0:0, "COLA"), DATA_ACCURACY (015/030, "Hôm nay" + dữ liệu
  thật), HOME_BILLBOARD (026/027, phim mới 12 phim sạch), SCHEDULE_EPG
  (030), PHIM_NGUONC (046/047, detail sạch, đủ nút PHÁT/CHỌN TẬP/LƯU
  PHIM), PLAYER_SETTINGS_DIALOG (061/063, dialog Cài Đặt sạch + native
  phát thật 01:13→01:53, nhãn phải là thời gian còn lại 1:04:10→1:03:31
  đúng thiết kế KL8), SEARCH_AND_SETTINGS (066/067/073, 37 kết quả),
  STRESS (071/073, app còn foreground, focus đã di chuyển).
- IPTV_EPG PASS — **mềm**: player mở được thật (step 42 activity
  PlayerActivity) nhưng frame step_044 chỉ thấy lại list IPTV (VTV Cần Thơ
  #05), không thấy nội dung EPG/Mini-Guide nào trong ảnh. Giống T5.
- EPISODE_PICKER PASS — **mềm**: frame trích dẫn step_051 KHÔNG thấy dialog
  chọn tập (chỉ thấy detail page, nút CHỌN TẬP được focus); dump cùng bước
  ghi `dialog_seen: true`, focus `tvEpisodeName "Tập 1"` tại [386,696]–
  [612,772] — vùng đó trong ảnh là khoảng đen trống, không có dialog.
  Screenshot/dump lệch nhau (có thể dialog mở sau khi chụp, do animation).
  PASS này yếu hơn T5 (dialog Tập 1–8 thấy rõ trong frame).
- WEBPLAYER_DIRECTED PASS — **mềm về bằng chứng phát, yếu hơn bản đầu ghi.**
  WebPlayer tới đích thật, OSD mở, seekbar 00:20, TỐC ĐỘ 1X — nhưng KHÔNG
  có bằng chứng phát tự nhiên nào: *(sửa sau review độc lập: bản đầu ghi
  "thời gian tăng bằng mắt 00:00→00:20→00:30" là SAI thứ tự và sai bản
  chất)*. Thực tế: 00:20 (step_055, t=450,7) → 00:00 (step_056, t=484,8) →
  00:30 (reel t=2s) → 00:20 (step_059, t=511) — KHÔNG tăng đơn điệu, khớp
  với seek test; hơn nữa step_055 = step_059 **pixel-identical** (mean abs
  diff 0,0017) = cùng 1 frame đóng băng suốt 60,3s. `playback_readings: []`,
  `playback_status: "unknown"` — mục 8 không ghi được reading nào (cơ chế:
  dump WebView không có text → `osd_visible=False` → cả 3 detector đọc
  band dưới đều skip → band chưa từng được OCR, xem §9 mục 2). PASS này
  chứng minh được OSD + tua + tốc độ, chưa chứng minh được "phát thật".
  Đối chiếu: native player phát thật (01:13→01:53, tour 01:36→01:56).

## 4. 3 FAIL — phân loại

| Mission | Lý do | Mắt thấy gì | Loại |
|---|---|---|---|
| SPORTS_ROOM_PICKER | "OK mở PLAYER thay vì dialog đích" | Dialog "Phòng bình luận" ĐÃ mở ở step 10 (shot step_011: TOP 01/02, focus `blvCardRoot`); driver bấm OK tiếp lên thẻ phòng → PlayerActivity ở step 11 (shot step_012: loading "Đang tải luồng…" + spinner đè nút ▶ PHÁT). Mission FAIL vì driver không dừng ở dialog, nhưng lý do ghi sai bản chất. *(Sửa sau review độc lập — gốc rễ đã chứng minh bằng app source + CI log: cái mở ra là **match-detail panel** (`LiveFragment.openGroupPicker`, layout `dialog_match_detail.xml`), KHÔNG phải RoomPickerDialog độc lập; các id của panel (`panelBlvList`, `panelSameTimeList`, `panelPlay`, `panelScore`…) **không có id nào** trong `dialog_id_set` của `device.py:203-205` → `has_dialog=False` suốt lúc panel mở → driver rule 1 tưởng dialog chưa mở, bấm OK lần nữa lên `blvCardRoot` → mở player. "Gate không latch" là diễn đạt không chính xác — gate không thể latch cái dump không báo.)* | Harness (nhận diện dialog thiếu id panel + driver rule 0c2 không kiểm `has_dialog`) + app (loading vô hạn, spinner đè nút — xem §6) |
| PLAYER_STREAMING | hết 8 bước, không vào PlayerActivity | Driver dao động dialog↔list cả 8 bước (17/19/21 dialog, 18/20/22 list), kết thúc ở dialog Singapore U17 vs India U (shot step_023); không lần nào bấm OK vào phòng. Luật goto-player (mục 6) CHẠY 4 lần nhưng sai trạng thái — rule 0c2 không kiểm `has_dialog` nên đuổi badge LIVE ở list nền sau overlay thay vì bấm OK trên phòng đang focus (cùng gốc rễ với ROOM_PICKER: panel không được nhận là dialog). | Harness (mục 6 chạy sai trạng thái) |
| NAV_RAIL | thiếu view railPanel (7 bước) | DPAD_LEFT chỉ di chuyển focus trong lưới ĐANG PHÁT (step_031/036/037), rail không mở lần nào — lỗi app còn từ KL8 audit. | App (rail không mở) |

## 5. Tốc độ + video — nhanh nhất, video vẫn thiếu chunk cuối

- QA 887s (14m47s): chậm hơn T5 (843s) 44s nhưng vẫn dưới mục tiêu 30 phút
  với biên lớn; nhanh hơn T4 (1534s) và T3 (1019s). Observe 419.35s (p50
  3.95s, p95 17.2s).
- Video: 702.8/887s = 79% (T5: 83%). Tour 175.77s @4x xem được đủ phần
  lớn (tour_005 hero sạch, tour_090 IPTV, tour_160/165 native 01:36→01:56
  đang phát thật). `concat.txt` chỉ có 4 chunk norm_01–04 — chunk cuối
  (~184s cuối run, gồm SEARCH cuối + STRESS) vẫn mất dù đã có chờ moov
  (mục 3). *(Sửa sau review độc lập: moov-wait 60s ĐÃ chạy và THẤT BẠI —
  CI log ghi `"Chunk cuối qa_rec_05.mp4: KHÔNG có moov sau 5 lần pull thử"`
  + `"CHƯA chắc có moov sau 60s"`; normalize: `"moov atom not found"` →
  chunk_05 rớt. Không phải timeout chờ chưa đủ — writer không finalize.
  Lỗ thiết kế: `_wait_for_screenrecord_exit()` được gọi nhưng giá trị trả
  về bị bỏ qua, `stop_and_save` không xác minh process screenrecord đã
  chết trước khi chờ moov.)* Tour t=170s có 1 frame đen thoáng qua (nối
  chunk) — không nghiêm trọng nhưng thấy được.
- Reel 12.03s: entry 1 (HIGH đè đôi) khớp đúng nội dung; entry 2
  (MEDIUM focus) bị kẹp (video_t 178.3s > tour 175.77s) — đoạn 2 thực chất
  là khung hình ở tour t≈169.8–175.8, không chứa đúng thời điểm finding
  (713.3s > 702.8s ghi được). Report ghi trung thực "1/2 finding (1 đoạn
  bị kẹp do vượt tour)". Tiêu chí "reel khớp report" CHỈ ĐẠT MỘT NỬA.
- Shot trùng lặp: step_046 = step_047 byte-identical; step_066 ≈ step_067
  cùng nội dung; step_041 ≈ step_044 gần giống hệt; **thêm sau review độc
  lập: step_026 = step_037 byte-identical (trùng xuyên mission)**. Mục 7
  đánh dấu `duplicate_frame: True` nhưng file vẫn được lưu (đường bypass
  `_finish_mission`, xem §1 mục 7).

## 6. Lỗi app thật bị bỏ sót (không có trong findings)

1. **Schedule: hàng LIVE hiện giờ kickoff thay vì tỉ số — CÒN NGUYÊN từ
   T3.** Step_015/030 ("Hôm nay"): 18:30 FK Orsha vs BATE Borisov và
   18:35 China U19 vs Vietnam U19 đều gắn badge Live nhưng chỉ hiện giờ
   đá, không có tỉ số; trong khi hàng Vietnam vs Chinese Taipei hiện "4:2".
   DATA_ACCURACY PASS không kiểm điều này.
2. **Player native: "Đang tải luồng…" vô hạn + spinner đè nút ▶ PHÁT —
   CÒN NGUYÊN từ T5.** Step_012 (ROOM_PICKER → player trận ĐTQ VN 5-3,
   Hiệp 2 67', LIVE thật): spinner nằm đè lên viền trên nút PHÁT, text
   "Đang tải luồng…" đè lên viền dưới nút; thời gian 00:00, stream không
   bao giờ chạy. Trận LIVE thật mà luồng không tải được.
3. **Hàng "Địa Phương — 66 kênh" — KHÔNG ĐƯỢC KIỂM Ở T6.** Driver không
   cuộn tới hàng này trong IPTV (tour t=90s chỉ thấy hàng VTV + HTV/VTC);
   mission IPTV_CATEGORIES PASS trên text 'kênh' mà không tới được hàng
   Địa Phương. Không chứng minh đã sửa, cũng không bị tố lại.
4. **Trận LIVE không có tỉ số trong detail:** Singapore U17 vs India U
   (step_016/023) gắn "Đang trực tiếp" nhưng chỉ hiện "VS", không có tỉ
   số (cùng họ với #1).
5. **Hero giờ đè phụ đề — KHÔNG TÁI HIỆN ở T6** (tour_005 sạch, vision
   hero check not_found). Không kết luận đã sửa.
6. **Rail không mở bằng DPAD_LEFT** (§4) — còn nguyên, đã FAIL mission.
7. **MỚI (review độc lập phát hiện, coordinator đã xác minh bằng crop
   phóng to): nút "ÂM THANH & PHỤ ĐỀ" bị cắt mép phải khi focus ở player
   native** — chữ "Ề" mất một nửa, viền phải của nút ra ngoài màn hình,
   trong lúc nút đang focus (viền trắng), ở cả 4 frame: step_061, step_063,
   tour_160, tour_165. Hàng nút tràn mép phải, item đang focus không được
   cuộn vào trong — lỗi layout thật.

## 7. Điểm số

79/100 = 100 − 12 (1 HIGH) − 5 (1 MEDIUM) − round(3/17×20)=4. Số học đúng.
Nếu bỏ MEDIUM giả (focus trap): 84/100. Verdict PASS (score ≥75, pass
14/17 ≈ 82% ≥80%, không CRITICAL) — lần đầu harness cho verdict PASS.

## 8. Kết luận cho switch-over

**CHƯA SWITCH ĐƯỢC (NEEDS-CI-T7) — nhưng đã rất gần.** Đối chiếu
SWITCHOVER.md:
- Tốc độ <30p ✅ (QA 14m47s) · 0 false pass ✅ theo luật gate (14 PASS đều
  đạt điều kiện gate; nhưng WEBPLAYER_DIRECTED là PASS mềm nhất — không có
  bằng chứng phát nào, frame đóng băng 60,3s, xem §3) · WebPlayer ✅ ·
  0×429, ≤40 req ✅ (5 req, provider OPENAI ghi rõ) · frame evidence ✅
  (17/17 mission đều có frame trên đĩa) · **0 HIGH false-positive ✅ LẦN
  ĐẦU** (HIGH duy nhất là thật — tiêu đề đè đôi; MEDIUM focus-trap là giả
  nhưng không tính vào tiêu chí HIGH)
- Reel ⚠️ MỘT NỬA (1/2 đoạn xem được trọn; entry 2 kẹp) · video 79% (chưa
  >95%) · **Eye check khớp report ❌** (Schedule giờ-thay-tỉ-số, spinner
  đè nút + loading vô hạn, hàng 66 kênh không được kiểm, nút "ÂM THANH &
  PHỤ ĐỀ" bị cắt — đều không có trong findings ban đầu; ROOM_PICKER FAIL
  với lý do sai bản chất)
- Driver còn 2 lỗi: ROOM_PICKER overshoot (dialog_id_set thiếu id của
  MatchDetailPanel → `has_dialog=False` suốt lúc panel mở), PLAYER_STREAMING
  A-B-A-B (goto-player chạy 4 lần nhưng sai trạng thái — rule 0c2 không
  kiểm `has_dialog`).

## 9. Danh sách sửa CI-T7 (đề xuất)

1. **Focus-trap + keyboard:** guard bàn phím theo ảnh/pixel (dump không bao
   giờ lộ IME): nếu OCR thấy lưới phím (qwerty) hoặc shot liên tiếp giống
   hệt nhau kèm bàn phím thì không tố; hoặc so highlight phím giữa 2 shot
   (đổi phím = focus di chuyển). Regression bằng step_066 (⇧) / step_067
   ('z') + tour t=172s ('q') + step_071 ('▶'). Mock N5(c) phải dựng từ dump
   KHÔNG có node bàn phím (hiện truyền `keyboard_open=True` bằng tay nên
   không chứng minh được hành vi live).
2. **Mục 8 — nối playback_readings vào nguồn thật:** hiện
   `playback_readings: []` vì band dưới chưa từng được OCR: dump WebView
   không có text (mọi step WebPlayer chỉ có `view#[0,0][1920,1080]`) →
   `osd_visible=False` → cả 3 detector đọc band dưới đều skip khi `osd is
   False` (`detectors.py:536/582`) → `_ocr_cache[(frame_ref,
   BOTTOM_BAR_BAND)]` không bao giờ được điền → `_extract_playback_s`
   luôn None. Không phải "OCR không trích được '00:20'" — band chưa từng
   được OCR. Sửa: OCR band dưới ở player dựa trên ảnh/OSD pixel, không dựa
   trên `osd_visible` từ dump; hoặc parse elapsed từ quote vision ("00:20 /
   01:05:24"). Gate: "unknown sau ≥2 observation trong player" thành
   UNVERIFIED/soft-fail thay vì PASS miễn phí. Regression: WEBPLAYER_DIRECTED
   phải có readings tăng đơn điệu, nếu không thì không PASS.
3. **Nhận diện dialog (gốc rễ ROOM_PICKER + PLAYER_STREAMING):** thêm id của
   MatchDetailPanel (`panelBlvList`, `panelSameTimeList`, `panelPlay`,
   `panelScore`, …) vào `dialog_id_set` (`device.py:203-205`) — hoặc coi
   focus `blvCardRoot`/`panel*` là dialog đang mở. Một sửa này gỡ cả 2
   mission. Regression: ROOM_PICKER PASS với `dialog_seen=true`;
   PLAYER_STREAMING tới được PlayerActivity.
4. **Driver:** khi dialog/panel đang mở, mission cần player phải bấm OK trên
   phòng đang focus — cấm `goto_live_card` đuổi badge ở list nền sau
   overlay. Gate rule 0c2 bằng `not has_dialog` (sau khi mục 3 sửa xong).
   Log rõ mỗi bước driver chọn luật nào (CI-T6: luật đã chạy 4 lần nhưng
   sai trạng thái — phải thấy được trong log).
5. **Video chunk cuối:** gốc rễ đã xác định (CI log, xem §5): moov-wait
   60s ĐÃ chạy và thất bại — writer không finalize, nên kéo dài timeout
   không cứu được. Sửa: xác minh process screenrecord đã chết (`pidof`)
   trước khi chờ moov — không chờ 60s trên file có thể vẫn đang mở;
   cân nhắc dừng quay trước giai đoạn post-processing dài (~130s vision
   check + reel) để chunk cuối kết thúc bằng expiry 175s tự nhiên. Mục
   tiêu độ phủ >95% + reel cover 2/2.
6. **Shot trùng — bỏ hẳn, không chỉ đánh dấu:** `duplicate_frame: True` đã
   có nhưng file vẫn lưu, vì `_finish_mission` (`runner.py` ~640–644) lưu
   ảnh cuối mission vô điều kiện, không check duplicate (đường bypass);
   áp check duplicate cả ở đó; ghi mọi shot đã lưu vào timeline/report;
   cân nhắc phát hiện trùng xuyên mission (step_026 = step_037
   byte-identical; step_055 = step_059 pixel-identical).
7. **Screenshot/dump đồng bộ:** shot trích dẫn cho EPISODE_PICKER
   (step_051) không thấy dialog trong khi dump thấy — chụp sau khi dump ổn
   định (chờ animation dialog) hoặc ghi rõ evidence chỉ từ dump.
8. **IPTV_EPG evidence:** PASS mềm vì frame không thấy nội dung EPG —
   yêu cầu vision_confirm với EPG text trong frame (như WEBPLAYER) hoặc
   đánh dấu PASS mềm trong report.
9. **Schedule live-score check:** thêm detector — hàng gắn badge Live mà
   chỉ hiện giờ kickoff (không có tỉ số) thì tố (đã sót 3 vòng: T3/T4/T6
   đều thấy 18:30/18:35). Cẩn thận: chỉ tố khi trận đã bắt đầu (giờ đá <
   giờ hiện tại).
10. **App (không phải harness — ghi cho fix loop):** WebPlayer đè đôi tiêu
    đề (HIGH thật, lần đầu bắt được); spinner loading đè nút ▶ PHÁT +
    "Đang tải luồng…" vô hạn ở player native trận LIVE; Schedule hàng LIVE
    hiện giờ thay vì tỉ số; hàng "Địa Phương — 66 kênh" (chưa kiểm lại);
    rail không mở bằng DPAD_LEFT; detail trận LIVE "VS" không tỉ số;
    **MỚI: nút "ÂM THANH & PHỤ ĐỀ" bị cắt mép phải khi focus ở player
    native (step_061/063, tour_160/165).**

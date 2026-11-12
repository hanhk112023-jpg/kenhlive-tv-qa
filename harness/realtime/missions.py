#!/usr/bin/env python3
"""KenhLive Realtime QA — mission specs (mục tiêu bằng chứng, không kịch bản).

21 mission: 18 mission cũ (17 mission gốc — VOD và WebPlayer tách riêng
thành 2 mission nhưng tổng vẫn 17 vì Home Hub cũ đã bỏ — + 1 mission
CI-T8 MISSION_SCHEDULE_LIVE_DIRECTED) + 3 mission tour đủ màn sau trial 9
(DESIGN §15.23: Cài đặt storage dialog, Cài đặt Telegram QR, MultiView).
Mỗi mission khai TÍN HIỆU CẦN CÓ, không khai từng bước bấm — driver tự chọn
hành động theo trạng thái. required_texts so khớp case-insensitive trên text
của UI dump (tên hiển thị thật của app).
"""
from gate import MissionSpec

QUICK_KEEP = {
    "MISSION_COLD_START",
    "MISSION_HOME_BILLBOARD_6_ROWS",
    "MISSION_IPTV_CATEGORIES_AND_FAVORITES",
    "MISSION_PHIM_NGUONC_AND_CATEGORIES",
    "MISSION_PLAYER_SETTINGS_DIALOG",
}

ALL_MISSIONS = [
    MissionSpec(
        "MISSION_COLD_START",
        "Khởi Động Lạnh & Màn Hình Chính",
        "Mở app từ trạng thái tắt, màn hình chính nạp đủ dữ liệu, focus xuất hiện.",
        max_steps=5, min_steps=3,
        required_activity="MainActivity",
        required_texts=["trang chủ"],
        target_desc="màn hình chính KenhLive đã nạp, nav TRANG CHỦ hiển thị",
        tab=6,
    ),
    MissionSpec(
        "MISSION_SPORTS_MULTI_SOURCE",
        "Thể Thao Đa Nguồn & Cuộn Ngang Sâu",
        "Duyệt các hàng đài độc lập (ColaTV/Soco, Gà Vàng, Khán Đài). "
        "CI-T6: text mục tiêu cũ 'socolive' KHÔNG TỒN TẠI dạng text trên màn "
        "hình (chỉ có nhãn 'COLA'/'SOCO' trên card + 'BLV [ColaTV]' trong "
        "phụ đề hero, VISUAL-REVIEW CI-T5 §4) nên mission không bao giờ PASS "
        "được bằng text đó — đổi sang tín hiệu kiểm chứng được 'cola' "
        "(khớp cả 'COLA' lẫn 'ColaTV'). "
        "H3 (trial 5 run 43183031119): driver explore DOWN/RIGHT dao động "
        "A-B-A-B giữa 2 thẻ NBL/JLC (chỉ có badge 'SOCO') suốt 8 bước, không "
        "bao giờ tới hàng có 'COLA' — app CÓ hiện 'COLA' ở thẻ khác cùng "
        "tab (step_036 'Aus Champ COLA'). Giờ driver quét chéo DOWN/RIGHT "
        "theo goto_texts cho tới khi text xuất hiện trong dump (max_steps "
        "8 -> 10 để đủ chỗ quét).",
        max_steps=10, min_steps=4,
        required_activity="MainActivity",
        required_texts=["cola"],
        target_desc="hàng trận đấu của đài ColaTV hiển thị trên tab Trực tiếp",
        tab=0, goto_texts=["cola"],
    ),
    MissionSpec(
        "MISSION_SPORTS_ROOM_PICKER",
        "Hộp Thoại Chọn Phòng BLV",
        "Mở RoomPickerDialog trên thẻ trận đấu, duyệt phòng BLV, đóng bằng BACK.",
        max_steps=6, min_steps=4,
        required_activity="MainActivity",
        required_texts=["blv"],
        needs_dialog=True,
        target_desc="hộp thoại chọn phòng BLV đang mở với danh sách phòng",
        tab=0,
    ),
    MissionSpec(
        "MISSION_SPORTS_DATA_ACCURACY",
        "Chuẩn Hóa Dữ Liệu Bóng Đá GMT+7",
        "Tab Lịch đấu: tên giải, tỷ số dạng X : Y, badge KẾT THÚC, không spam.",
        max_steps=4, min_steps=3,
        required_activity="MainActivity",
        required_texts=["hôm nay"],
        target_desc="tab Lịch đấu hiển thị danh sách trận theo ngày",
        tab=1, needs_scroll_top=True,
    ),
    MissionSpec(
        "MISSION_PLAYER_STREAMING_AND_CONTROLS",
        "Trình Phát Video ExoPlayer & Phím Tắt",
        "Mở phát trận đấu, video chuyển động thật, phím tắt A/B/Menu phản hồi. "
        "CI-T9 nhóm B mục (3): CHỈ mở trận ĐANG ĐÁ (badge LIVE/TRỰC TIẾP, "
        "hoặc giờ kickoff hôm nay đã qua) — TUYỆT ĐỐI không mở trận SẮP ĐÁ/"
        "tương lai (Thử 3: mở nhầm KUW–SYR đá ngày mai 21:00 nên player "
        "'Đang tải luồng...' vô hạn). Run không có trận đang đá nào để chọn "
        "thì UNVERIFIED (chưa kiểm được), không FAIL oan.",
        max_steps=8, min_steps=4,
        required_activity="PlayerActivity",
        needs_motion=True, needs_vision=True,
        target_desc="trình phát PlayerActivity đang phát video bóng đá thật của một trận đang đá (LIVE/TRỰC TIẾP)",
        tab=0, requires_live_row=True,
    ),
    MissionSpec(
        "MISSION_HOME_BILLBOARD_6_ROWS",
        "Trang Chủ: Billboard 60% + 6 Hàng (KL8 Task 4)",
        "Tab 6 Trang Chủ: billboard ~60% + 6 hàng ĐANG PHÁT / TIẾP TỤC XEM / "
        "TRẬN SẮP DIỄN RA / MỚI CẬP NHẬT / KÊNH / GIẢI ĐẤU. Không còn portal 3 card.",
        max_steps=8, min_steps=4,
        required_activity="MainActivity",
        required_texts=["đang phát", "mới cập nhật"],
        target_desc="trang chủ với billboard hero và các hàng ĐANG PHÁT, MỚI CẬP NHẬT",
        tab=6,
    ),
    MissionSpec(
        "MISSION_SCHEDULE_EPG_AND_FIXTURE_TAP",
        "Lịch Thi Đấu EPG & Chạm Trận Đấu",
        "Tab Lịch đấu, duyệt lịch theo ngày, bấm trận kiểm tra onFixtureTap.",
        max_steps=6, min_steps=3,
        required_activity="MainActivity",
        required_texts=["hôm nay"],
        target_desc="tab Lịch đấu, bấm vào một trận đấu mở được popup/phòng",
        tab=1, needs_scroll_top=True,
    ),
    MissionSpec(
        "MISSION_SCHEDULE_LIVE_DIRECTED",
        "Lịch Trực Tiếp & Tỉ Số Trận Đang Đá",
        "CI-T8 mục 7: chờ hàng LIVE thật ở tab Lịch đấu rồi kiểm tỉ số "
        "đang diễn ra (detector (e) 'hàng LIVE chỉ hiện giờ kickoff thay "
        "vì tỉ số'). Run không có trận nào đang đá -> UNVERIFIED (chưa "
        "kiểm được), không FAIL, không im lặng.",
        max_steps=8, min_steps=3,
        required_activity="MainActivity",
        required_texts=["live"],
        target_desc="hàng trận đấu đang đá (badge TRỰC TIẾP/LIVE) hiển thị tỉ số",
        tab=1, needs_scroll_top=True, requires_live_row=True,
    ),
    MissionSpec(
        "MISSION_SIDEBAR_RAIL_FULL_TRAVERSAL",
        "Thanh Điều Hướng Sidebar Rail",
        "Mở rail bằng DPAD_LEFT, duyệt dọc các mục, đóng bằng DPAD_RIGHT.",
        max_steps=7, min_steps=3,
        required_activity="MainActivity",
        required_views=["railPanel"],
        target_desc="thanh sidebar rail đang mở với danh sách mục điều hướng",
        tab=6,
    ),
    MissionSpec(
        "MISSION_IPTV_CATEGORIES_AND_FAVORITES",
        "Truyền Hình IPTV, Lưới Kênh & Kênh Yêu Thích",
        "Tab IPTV: danh mục kênh, long-press OK lưu yêu thích, dialog M3U. "
        "CI-T6: text mục tiêu cũ 'tv360' KHÔNG TỒN TẠI dạng text trong dump "
        "(chỉ tồn tại dạng ẢNH logo + chip danh mục bị cắt còn 'T', "
        "VISUAL-REVIEW CI-T5 §4) nên mission không bao giờ PASS được bằng "
        "text đó — đổi sang tín hiệu kiểm chứng được 'kênh' (header hàng "
        "'Địa Phương — 66 kênh' và các header đếm kênh khác trên lưới).",
        max_steps=10, min_steps=4,
        required_activity="MainActivity",
        required_texts=["kênh"],
        target_desc="tab Truyền hình hiển thị lưới kênh IPTV với các hàng danh mục",
        tab=2, needs_scroll_top=True, needs_long_press=True,
    ),
    MissionSpec(
        "MISSION_IPTV_EPG_AND_ZAPPING_PLAYER",
        "Hero Preview IPTV, EPG & Nhảy Kênh",
        "Hero Preview + EPG theo giờ, mở phát toàn màn hình, gõ số nhảy kênh. "
        "CI-T7 mục 8: CI-T6 PASS mềm — frame chỉ thấy list kênh, không thấy "
        "EPG text — nên mission này bắt buộc vision_confirm (xác nhận có "
        "thấy tên kênh + thông tin EPG/lịch phát sóng trong frame), không "
        "PASS cứng khi chỉ thấy list. "
        "H4 (trial 5 run 43183031119): target cũ SAI với app thật — OSD "
        "player chỉ hiện TÊN KÊNH, KHÔNG có thông tin EPG (tên/giờ chương "
        "trình); EPG chỉ có ở thẻ lưới (step_041: 'Khám phá Việt Nam…' dưới "
        "tên kênh). Vision xác nhận đúng lúc kênh đang phát (tour t≈95s, "
        "VTV Cần Thơ, motion 10.37) nhưng driver SWITCH_TAB giết player rồi "
        "vision chạy trên khung lưới/khung tải luồng nên 2× deny oan. Giờ "
        "target vision chỉ đòi tên kênh + đang phát (đúng cái OSD hiện); "
        "EPG lấy từ thẻ lưới qua required_texts=['kênh'] — bằng chứng lưới "
        "đã thấy trong mission. Driver giữ kênh đang phát + không SWITCH_TAB "
        "trong player (xem driver.py).",
        max_steps=7, min_steps=3,
        required_activity="PlayerActivity",
        required_texts=["kênh"],
        needs_motion=True, needs_vision=True,
        target_desc="trình phát IPTV đang phát một kênh truyền hình, màn hình hiện tên kênh đang phát",
        tab=2,
    ),
    MissionSpec(
        "MISSION_PHIM_NGUONC_AND_CATEGORIES",
        "Kho Phim NguonC & Apple Pills",
        "Tab Kho Phim: hero phim + pills thể loại, focus hạ cánh đúng nút XEM NGAY.",
        max_steps=5, min_steps=3,
        required_activity="MainActivity",
        required_texts=["kho phim"],
        target_desc="tab Kho Phim với hero phim và pills thể loại",
        tab=5,
    ),
    MissionSpec(
        "MISSION_PHIM_EPISODE_PICKER_AND_FAVORITE",
        "Hộp Thoại Chọn Tập, Lưu Phim & Đổi Spotlight",
        "Nút CHỌN TẬP mở EpisodePickerDialog, LƯU PHIM, ĐỔI PHIM chuyển Spotlight.",
        max_steps=9, min_steps=4,
        required_activity="MainActivity",
        required_texts=["tập"],
        needs_dialog=True,
        target_desc="hộp thoại chọn tập phim đang mở với danh sách tập",
        tab=5, goto_texts=["CHỌN TẬP"],
    ),
    MissionSpec(
        "MISSION_VOD_PLAYER_SEEK_AND_RESUME",
        "Trình Phát Web (WebPlayerActivity), Tua JS & Tiếp Tục Xem",
        "WebPlayer bằng deep-link open=webplayer (phim embed THẬT), tua D-pad qua JS, "
        "toggle Play/Pause, thoát lưu tiến độ vào hàng Tiếp Tục Xem. "
        "H1 (trial 9 run 43217017298): OSD WebPlayer KHÔNG CÓ đồng hồ phát "
        "nên gate không đòi đọc đồng hồ (playback_no_clock) — bằng chứng phát "
        "là motion + vision; mission #14 FAIL oan ở trial 9 vì gate cũ đòi đọc "
        "đồng hồ không tồn tại.",
        max_steps=10, min_steps=4,
        required_activity="WebPlayerActivity",
        needs_motion=True, needs_vision=True, needs_playback_progress=True,
        playback_no_clock=True,
        directed_launch="LAUNCH_WEB_PLAYER",
        target_desc="WebPlayerActivity đang phát phim embed thật",
    ),
    MissionSpec(
        "MISSION_WEBPLAYER_DIRECTED_REAL_FILM",
        "WebPlayer Có Định Hướng: Phim Embed Thật, Phát/Tạm Dừng/Tua/Tốc Độ",
        "Mission có định hướng (KL8 Task 12): deep-link open=webplayer với tập embed "
        "thật TRƯỚC vòng driver; trong WebPlayer: VERIFY_STREAM (motion), OSD, tua ±, "
        "tạm dừng/phát lại, nút Tốc độ nếu hiện (probe F47). "
        "H1 (trial 9 run 43217017298): như mission VOD — OSD WebPlayer không có "
        "đồng hồ nên gate không đòi đọc (playback_no_clock).",
        max_steps=12, min_steps=4,
        required_activity="WebPlayerActivity",
        needs_motion=True, needs_vision=True, needs_playback_progress=True,
        playback_no_clock=True,
        directed_launch="LAUNCH_WEB_PLAYER",
        target_desc="WebPlayerActivity đang phát phim embed thật, OSD điều khiển hiển thị",
    ),
    MissionSpec(
        "MISSION_PLAYER_SETTINGS_DIALOG",
        "Trình Phát Native, Dialog Cài Đặt Thống Nhất",
        "PlayerActivity mặt VOD bằng deep-link open=vodplayer (tập m3u8 THẬT): mở OSD, "
        "nút Cài Đặt mở dialog thống nhất, tua/pause, phím tắt A/B/MENU.",
        max_steps=19, min_steps=4,
        required_activity="PlayerActivity",
        needs_dialog=True,
        directed_launch="LAUNCH_VOD_PLAYER",
        target_desc="dialog Cài đặt trình phát đang mở trên PlayerActivity mặt VOD",
    ),
    MissionSpec(
        "MISSION_MULTIVIEW_DIRECTED",
        "MultiView Có Định Hướng: 2/4 Ô Trận Cùng Lúc",
        "Deep-link explicit mở thẳng MultiViewActivity (tour trial 9 thiếu màn "
        "này). KHÔNG có đường D-pad: chuỗi nav 'Đa màn hình' chỉ tồn tại dạng "
        "string chết (không dùng ở MainActivity/layout), LiveFragment.openMultiView "
        "không có caller nào, đường vào duy nhất còn lại là panel TÙY CHỌN trong "
        "PlayerActivity (sportOptMulti) mà driver không mở được — nên dùng "
        "directed launch như 2 mission WebPlayer/VOD. MultiView tự nạp trận live "
        "thật (SocoliveRepository.fetchLiveRooms); run không có trận live nào thì "
        "màn hình hiện trạng thái trống trung thực ('Hiện chưa có trận đấu nào đang "
        "trực tiếp' + nút Thử lại) — mission vẫn PASS vì mục tiêu là màn hình "
        "MultiView, không phải trận live: KHÔNG ép motion để không FAIL oan trạng "
        "thái trống đúng. Bằng chứng: activity + tiêu đề 'Đa màn hình' + vision.",
        max_steps=8, min_steps=4,
        required_activity="MultiViewActivity",
        required_texts=["đa màn hình"],
        needs_vision=True,
        directed_launch="LAUNCH_MULTIVIEW",
        target_desc="màn hình Đa màn hình với 2 hoặc 4 ô trận đấu đang phát, hoặc trạng thái trống trung thực khi không có trận trực tiếp",
    ),
    MissionSpec(
        "MISSION_SEARCH_AND_SETTINGS_FEEDBACK",
        "Tìm Kiếm & Cài Đặt (Báo Lỗi Telegram QR)",
        "Tab Tìm kiếm: nhập từ khóa; Tab Cài đặt: mở 'Liên hệ & Báo lỗi', QR Telegram. "
        "CI-T9 mục 7: bắt buộc mở bàn phím ảo thật (OK trên ô tìm kiếm rồi gõ "
        "từ khóa qua adb input) — CI-T8 bàn phím không mở lần nào ở cả 95 bước "
        "nên mục 6 cũ chưa từng được kiểm.",
        max_steps=10, min_steps=4,
        required_activity="MainActivity",
        required_texts=["tìm kiếm"],
        target_desc="tab Tìm kiếm với ô nhập từ khóa đang hiển thị",
        tab=3, needs_keyboard=True,
    ),
    MissionSpec(
        "MISSION_SETTINGS_STORAGE_DIALOG",
        "Cài Đặt: Dialog Xóa Bộ Nhớ Đệm (Destructive Đỏ, D6)",
        "Tab Cài đặt (tab 4, tour trial 9 thiếu màn này): hàng 'Xóa bộ nhớ "
        "đệm ảnh' (SettingsFragment, row mở showStorageDialog) mở dialog tiêu đề "
        "'Dung lượng & nguồn dữ liệu', nút Positive 'Xóa toàn bộ bộ nhớ đệm' "
        "(đỏ, destructive — D6) + nút 'Đóng'. Text đích 'xóa toàn bộ bộ nhớ "
        "đệm' CHỈ có trên nút của dialog (danh sách Cài đặt chỉ có hàng 'Xóa "
        "bộ nhớ đệm ảnh') nên mission không PASS được khi chưa mở dialog. "
        "Trial 10 (run 43227207645, mission #19 FAIL 8 bước): goto_texts cũ "
        "'dung lượng bộ nhớ đệm' căn cứ code KHÔNG khớp nhãn thật trên màn "
        "hình — hàng thật là 'Xóa bộ nhớ đệm ảnh' (step_079/093) — nên driver "
        "fallback bấm OK lên hàng đang focus (Chất lượng hình) rồi kẹt trong "
        "dialog chọn chất lượng; đổi sang đúng nhãn thật. "
        "AN TOÀN — KHÔNG xóa thật: driver không bao giờ bấm OK khi dialog đang "
        "mở (luật open_dialog chỉ bấm khi chưa có dialog; luật dismiss để nguyên "
        "dialog đích của mission cần dialog); mission PASS ngay khi đủ bằng chứng "
        "rồi runner BACK về ở mission sau. Nút đỏ không bao giờ bị bấm.",
        max_steps=8, min_steps=4,
        required_activity="MainActivity",
        required_texts=["xóa toàn bộ bộ nhớ đệm"],
        needs_dialog=True,
        target_desc="hộp thoại dung lượng bộ nhớ đệm đang mở với nút xóa toàn bộ màu đỏ và nút Đóng",
        tab=4, goto_texts=["xóa bộ nhớ đệm ảnh"],
    ),
    MissionSpec(
        "MISSION_SETTINGS_FEEDBACK_TELEGRAM_QR",
        "Cài Đặt: Phản Hồi Telegram QR",
        "Tab Cài đặt (tab 4, tour trial 9 thiếu màn này): hàng 'Liên hệ & Báo "
        "lỗi' (value 'Nhóm Telegram: @kenhlivetv') mở FeedbackDialog với mã QR "
        "Telegram (dialog_feedback.xml). Text đích 'quét mã qr' ('Quét mã QR để "
        "vào nhóm') CHỈ có trong dialog — danh sách Cài đặt không có — nên "
        "mission không PASS được khi chưa mở dialog. AN TOÀN: dialog này mang "
        "btnCloseFeedback nên luật dismiss có thể đóng nó bằng OK trên 'ĐÃ HIỂU "
        "/ ĐÓNG' (nút đóng an toàn, focus mặc định) SAU khi bằng chứng đã ghi "
        "vào gate; nút 'VÀO NHÓM TELEGRAM' không bao giờ bị bấm nên không mở "
        "intent trình duyệt ngoài app.",
        max_steps=8, min_steps=4,
        required_activity="MainActivity",
        required_texts=["quét mã qr"],
        needs_dialog=True,
        target_desc="hộp thoại phản hồi Telegram đang mở với mã QR và nút Vào Nhóm Telegram",
        tab=4, goto_texts=["liên hệ"],
    ),
    MissionSpec(
        "MISSION_DPAD_CHAOS_STRESS_AND_RECOVERY",
        "Stress Chaos D-pad & Đo RAM PSS",
        "Nhồi phím 4 hướng liên tục: không crash, không văng app, focus tự phục hồi.",
        max_steps=6, min_steps=6, kind="stress",
        target_desc="app còn foreground sau chuỗi phím D-pad ngẫu nhiên",
    ),
]


def get_missions(quick=False, only=None):
    """Trả list MissionSpec. quick: giữ 5 mission như harness cũ."""
    ms = list(ALL_MISSIONS)
    if only:
        keep = set(only)
        ms = [m for m in ms if m.name in keep]
    if quick:
        ms = [m for m in ms if m.name in QUICK_KEEP]
        for m in ms:
            m.max_steps = min(int(m.max_steps), 4 if m.name != "MISSION_PLAYER_SETTINGS_DIALOG" else 6)
    return ms

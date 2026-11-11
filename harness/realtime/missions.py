#!/usr/bin/env python3
"""KenhLive Realtime QA — mission specs (mục tiêu bằng chứng, không kịch bản).

17 mission, cùng độ phủ với harness cũ (17 mission — VOD và WebPlayer tách
riêng thành 2 mission nhưng tổng vẫn 17 vì Home Hub cũ đã bỏ).
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
        "(khớp cả 'COLA' lẫn 'ColaTV').",
        max_steps=8, min_steps=4,
        required_activity="MainActivity",
        required_texts=["cola"],
        target_desc="hàng trận đấu của đài ColaTV hiển thị trên tab Trực tiếp",
        tab=0,
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
        "Mở phát trận đấu, video chuyển động thật, phím tắt A/B/Menu phản hồi.",
        max_steps=8, min_steps=4,
        required_activity="PlayerActivity",
        needs_motion=True, needs_vision=True,
        target_desc="trình phát PlayerActivity đang phát video bóng đá thật",
        tab=0,
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
        "PASS cứng khi chỉ thấy list.",
        max_steps=7, min_steps=3,
        required_activity="PlayerActivity",
        needs_motion=True, needs_vision=True,
        target_desc="trình phát IPTV đang phát một kênh truyền hình, màn hình hiện tên kênh và thông tin EPG/lịch phát sóng của chương trình đang phát (tên chương trình và giờ phát)",
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
        "toggle Play/Pause, thoát lưu tiến độ vào hàng Tiếp Tục Xem.",
        max_steps=10, min_steps=4,
        required_activity="WebPlayerActivity",
        needs_motion=True, needs_vision=True, needs_playback_progress=True,
        directed_launch="LAUNCH_WEB_PLAYER",
        target_desc="WebPlayerActivity đang phát phim embed thật",
    ),
    MissionSpec(
        "MISSION_WEBPLAYER_DIRECTED_REAL_FILM",
        "WebPlayer Có Định Hướng: Phim Embed Thật, Phát/Tạm Dừng/Tua/Tốc Độ",
        "Mission có định hướng (KL8 Task 12): deep-link open=webplayer với tập embed "
        "thật TRƯỚC vòng driver; trong WebPlayer: VERIFY_STREAM (motion), OSD, tua ±, "
        "tạm dừng/phát lại, nút Tốc độ nếu hiện (probe F47).",
        max_steps=12, min_steps=4,
        required_activity="WebPlayerActivity",
        needs_motion=True, needs_vision=True, needs_playback_progress=True,
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
        "MISSION_SEARCH_AND_SETTINGS_FEEDBACK",
        "Tìm Kiếm & Cài Đặt (Báo Lỗi Telegram QR)",
        "Tab Tìm kiếm: nhập từ khóa; Tab Cài đặt: mở 'Liên hệ & Báo lỗi', QR Telegram.",
        max_steps=10, min_steps=4,
        required_activity="MainActivity",
        required_texts=["tìm kiếm"],
        target_desc="tab Tìm kiếm với ô nhập từ khóa đang hiển thị",
        tab=3,
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

### 🤖 Phiên Kiểm Thử AI QA: `QA-SESS-20261109-005615-5a8fc2`
- **Phiên bản ứng dụng:** KenhLive TV `0.1.12` (code `162`)
- **Git Commit:** `36f9a7d` (redesign/netflix) | **AI Brain:** OPENAI
- **Thời gian chạy:** `3824.8s` | **Điểm QA:** **64/100**
- **Độ bao phủ Tab:** **7/7 Tabs (100.0%)**
- **Tổng số bước AI:** `127` | **Lượt bấm D-pad:** `111` | **Kiểm tra Video:** `0`
- **🎬 Video Toàn Bộ Quá Trình:** `full_qa_tour.mp4` | **⚡ Timelapse 10x:** `qa_timelapse.mp4`

#### 🗺️ Bản Đồ Bao Phủ 6 Tab Đa Năng
| Tab | Biểu Tượng | Tên Phân Hệ | Thao Tác | Trạng Thái |
|:---:|:---:|:---|:---:|:---:|
| 0 | ⚽ | Trực Tiếp (Live) | 1 | ✅ ĐÃ DUYỆT |
| 1 | 📅 | Lịch Thi Đấu (Schedule) | 2 | ✅ ĐÃ DUYỆT |
| 2 | 📺 | Truyền Hình (IPTV) | 9 | ✅ ĐÃ DUYỆT |
| 3 | 🔍 | Tìm Kiếm (Search) | 1 | ✅ ĐÃ DUYỆT |
| 4 | ⚙️ | Cài Đặt (Settings) | 1 | ✅ ĐÃ DUYỆT |
| 5 | 🎬 | Kho Phim (NguonC) | 65 | ✅ ĐÃ DUYỆT |
| 6 | 🏠 | Cổng Chọn (Home Hub) | 11 | ✅ ĐÃ DUYỆT |

#### 🎮 Thống Kê Phím Điều Khiển TV D-pad
`OK: 22`, `DPAD_UP: 2`, `DPAD_RIGHT: 22`, `DPAD_LEFT: 24`, `DPAD_DOWN: 27`, `BACK: 12`, `ENTER: 1`, `MENU: 1`

#### 🚨 Lỗi Phát Hiện Trong Phiên
- **[Bước 52]** [MEDIUM] Sidebar Rail không mở được bằng phím DPAD_LEFT từ mép trái màn hình
- **[Bước 61]** [MEDIUM] Focus bị kẹt tại edtM3uUrl trong Dialog M3U, không thể di chuyển xuống các nút điều khiển bằng DPAD_DOWN
- **[Bước 62]** [MEDIUM] Focus bị kẹt tại edtM3uUrl trong Dialog M3U, không thể di chuyển xuống các nút điều khiển bằng DPAD_DOWN
- **[Bước 69]** [LOW] Video IPTV không phát được, chỉ hiển thị 'Đang tải nguồn...' với vòng quay loading
- **[Bước 86]** [LOW] Lỗi giải mã video ERROR_CODE_DECODING_FAILED trên emulator x86
- **[Bước 87]** [LOW] Lỗi giải mã video ERROR_CODE_DECODING_FAILED trên emulator x86
- **[Bước 88]** [LOW] Lỗi giải mã video ERROR_CODE_DECODING_FAILED trên emulator x86
- **[Bước 96]** [LOW] Lỗi giải mã video ERROR_CODE_DECODING_FAILED trên emulator x86
- **[Bước 97]** [LOW] Lỗi giải mã video ERROR_CODE_DECODING_FAILED trên emulator x86
- **[Bước 99]** [LOW] Lỗi giải mã video ERROR_CODE_DECODING_FAILED trên emulator x86
- **[Bước 112]** [LOW] Lỗi giải mã video ERROR_CODE_DECODING_FAILED trên emulator x86

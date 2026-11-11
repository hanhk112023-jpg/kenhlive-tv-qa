### 🤖 Phiên Kiểm Thử AI QA: `QA-SESS-20261108-142554-3b7140`
- **Phiên bản ứng dụng:** KenhLive TV `0.1.12` (code `162`)
- **Git Commit:** `0c53f9c` (redesign/fpt-home-landing) | **AI Brain:** OPENAI
- **Thời gian chạy:** `3170.1s` | **Điểm QA:** **55/100**
- **Độ bao phủ Tab:** **2/7 Tabs (28.6%)**
- **Tổng số bước AI:** `129` | **Lượt bấm D-pad:** `121` | **Kiểm tra Video:** `0`
- **🎬 Video Toàn Bộ Quá Trình:** `full_qa_tour.mp4`

#### 🗺️ Bản Đồ Bao Phủ 6 Tab Đa Năng
| Tab | Biểu Tượng | Tên Phân Hệ | Thao Tác | Trạng Thái |
|:---:|:---:|:---|:---:|:---:|
| 0 | ⚽ | Trực Tiếp (Live) | 0 | ⚪ CHƯA DUYỆT |
| 1 | 📅 | Lịch Thi Đấu (Schedule) | 0 | ⚪ CHƯA DUYỆT |
| 2 | 📺 | Truyền Hình (IPTV) | 0 | ⚪ CHƯA DUYỆT |
| 3 | 🔍 | Tìm Kiếm (Search) | 0 | ⚪ CHƯA DUYỆT |
| 4 | ⚙️ | Cài Đặt (Settings) | 0 | ⚪ CHƯA DUYỆT |
| 5 | 🎬 | Kho Phim (NguonC) | 102 | ✅ ĐÃ DUYỆT |
| 6 | 🏠 | Cổng Chọn (Home Hub) | 2 | ✅ ĐÃ DUYỆT |

#### 🎮 Thống Kê Phím Điều Khiển TV D-pad
`OK: 27`, `BACK: 7`, `DPAD_LEFT: 26`, `DPAD_UP: 37`, `DPAD_DOWN: 16`, `DPAD_RIGHT: 8`

#### 🚨 Lỗi Phát Hiện Trong Phiên
- **[Bước 26]** [MEDIUM] Lỗi phát video ExoPlaybackException, màn hình hiển thị 'Đang tải lại...'
- **[Bước 31]** [MEDIUM] Video hiển thị nội dung nhưng Motion delta: 0.00% (khoảng khung hình không chuyển động)
- **[Bước 82]** [MEDIUM] Focus Trap tại cardRoot khi bấm DPAD_LEFT
- **[Bước 89]** [MEDIUM] Focus Trap tại heroPlay khi bấm DPAD_LEFT
- **[Bước 95]** [MEDIUM] Focus Trap tại heroPlay khi bấm DPAD_LEFT/DPAD_UP
- **[Bước 104]** [MEDIUM] Focus Trap tại heroPlay khi bấm DPAD_LEFT

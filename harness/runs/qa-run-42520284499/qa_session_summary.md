### 🤖 Phiên Kiểm Thử AI QA: `QA-SESS-20261108-203340-660934`
- **Phiên bản ứng dụng:** KenhLive TV `0.1.12` (code `162`)
- **Git Commit:** `309926e` (redesign/netflix) | **AI Brain:** OPENAI
- **Thời gian chạy:** `2820.6s` | **Điểm QA:** **66/100**
- **Độ bao phủ Tab:** **4/7 Tabs (57.1%)**
- **Tổng số bước AI:** `127` | **Lượt bấm D-pad:** `119` | **Kiểm tra Video:** `0`
- **🎬 Video Toàn Bộ Quá Trình:** `full_qa_tour.mp4` | **⚡ Timelapse 10x:** `qa_timelapse.mp4`

#### 🗺️ Bản Đồ Bao Phủ 6 Tab Đa Năng
| Tab | Biểu Tượng | Tên Phân Hệ | Thao Tác | Trạng Thái |
|:---:|:---:|:---|:---:|:---:|
| 0 | ⚽ | Trực Tiếp (Live) | 1 | ✅ ĐÃ DUYỆT |
| 1 | 📅 | Lịch Thi Đấu (Schedule) | 0 | ⚪ CHƯA DUYỆT |
| 2 | 📺 | Truyền Hình (IPTV) | 1 | ✅ ĐÃ DUYỆT |
| 3 | 🔍 | Tìm Kiếm (Search) | 0 | ⚪ CHƯA DUYỆT |
| 4 | ⚙️ | Cài Đặt (Settings) | 0 | ⚪ CHƯA DUYỆT |
| 5 | 🎬 | Kho Phim (NguonC) | 115 | ✅ ĐÃ DUYỆT |
| 6 | 🏠 | Cổng Chọn (Home Hub) | 3 | ✅ ĐÃ DUYỆT |

#### 🎮 Thống Kê Phím Điều Khiển TV D-pad
`OK: 7`, `DPAD_UP: 37`, `DPAD_RIGHT: 35`, `BACK: 2`, `DPAD_LEFT: 19`, `MENU: 1`, `A: 1`, `B: 1`, `DPAD_DOWN: 16`

#### 🚨 Lỗi Phát Hiện Trong Phiên
- **[Bước 5]** [LOW] UI_JANK: Bỏ lỡ 82 frames khi khởi động lạnh
- **[Bước 22]** [LOW] Tên giải đấu hiển thị dưới dạng mã thay vì tên tiếng Việt đầy đủ
- **[Bước 28]** [HIGH] ExoPlayer bị lỗi phát video sau khi nhấn phím A/Đỏ chuyển Aspect Ratio
- **[Bước 29]** [HIGH] ExoPlayer bị lỗi phát video khi nhấn phím A/Đỏ chuyển Aspect Ratio

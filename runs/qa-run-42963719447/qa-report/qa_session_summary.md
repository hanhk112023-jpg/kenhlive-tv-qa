### 🤖 Phiên Kiểm Thử AI QA: `QA-SESS-20261111-051218-ca4ef7`
- **Phiên bản ứng dụng:** KenhLive TV `0.1.12` (code `162`)
- **Git Commit:** `c4de57e` (redesign/apple-kl8) | **AI Brain:** OPENAI
- **Thời gian chạy:** `5122.8s` | **Điểm QA:** **78/100**
- **Độ bao phủ Tab:** **7/7 Tabs (100.0%)**
- **Tổng số bước AI:** `140` | **Lượt bấm D-pad:** `122` | **Kiểm tra Video:** `0`
- **🎬 Video Toàn Bộ Quá Trình:** `full_qa_tour.mp4`

#### 🗺️ Bản Đồ Bao Phủ 6 Tab Đa Năng
| Tab | Biểu Tượng | Tên Phân Hệ | Thao Tác | Trạng Thái |
|:---:|:---:|:---|:---:|:---:|
| 0 | ⚽ | Trực Tiếp (Live) | 17 | ✅ ĐÃ DUYỆT |
| 1 | 📅 | Lịch Thi Đấu (Schedule) | 15 | ✅ ĐÃ DUYỆT |
| 2 | 📺 | Truyền Hình (IPTV) | 17 | ✅ ĐÃ DUYỆT |
| 3 | 🔍 | Tìm Kiếm (Search) | 4 | ✅ ĐÃ DUYỆT |
| 4 | ⚙️ | Cài Đặt (Settings) | 20 | ✅ ĐÃ DUYỆT |
| 5 | 🎬 | Kho Phim (NguonC) | 20 | ✅ ĐÃ DUYỆT |
| 6 | 🏠 | Cổng Chọn (Home Hub) | 14 | ✅ ĐÃ DUYỆT |

#### 🎮 Thống Kê Phím Điều Khiển TV D-pad
`OK: 30`, `DPAD_DOWN: 37`, `DPAD_UP: 7`, `DPAD_RIGHT: 31`, `DPAD_LEFT: 11`, `BACK: 6`

#### 🚨 Lỗi Phát Hiện Trong Phiên
- **[Bước 43]** [MEDIUM] Node FOCUS là NONE khi video load xong, không có phần tử focus mặc định
- **[Bước 73]** [MEDIUM] Focus border không hiển thị trên Apple Pill 'Tất Cả'
- **[Bước 74]** [MEDIUM] Focus border không hiển thị trên Apple Pill 'Lịch Sử Xem'
- **[Bước 75]** [MEDIUM] Focus border không hiển thị trên Apple Pill 'Tìm Kiếm'
- **[Bước 92]** [LOW] Lỗi phát stream embed trên emulator x86 (ERROR_CODE_PARSING_CONTAINER_UNSUPPORTED)

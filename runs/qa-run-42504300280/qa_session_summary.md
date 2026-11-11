### 🤖 Phiên Kiểm Thử AI QA: `QA-SESS-20261108-172218-1f2dec`
- **Phiên bản ứng dụng:** KenhLive TV `0.1.12` (code `162`)
- **Git Commit:** `c4e14f8` (redesign/netflix) | **AI Brain:** OPENAI
- **Thời gian chạy:** `3967.0s` | **Điểm QA:** **75/100**
- **Độ bao phủ Tab:** **6/7 Tabs (85.7%)**
- **Tổng số bước AI:** `128` | **Lượt bấm D-pad:** `110` | **Kiểm tra Video:** `0`
- **🎬 Video Toàn Bộ Quá Trình:** `full_qa_tour.mp4` | **⚡ Timelapse 10x:** `qa_timelapse.mp4`

#### 🗺️ Bản Đồ Bao Phủ 6 Tab Đa Năng
| Tab | Biểu Tượng | Tên Phân Hệ | Thao Tác | Trạng Thái |
|:---:|:---:|:---|:---:|:---:|
| 0 | ⚽ | Trực Tiếp (Live) | 0 | ⚪ CHƯA DUYỆT |
| 1 | 📅 | Lịch Thi Đấu (Schedule) | 1 | ✅ ĐÃ DUYỆT |
| 2 | 📺 | Truyền Hình (IPTV) | 6 | ✅ ĐÃ DUYỆT |
| 3 | 🔍 | Tìm Kiếm (Search) | 1 | ✅ ĐÃ DUYỆT |
| 4 | ⚙️ | Cài Đặt (Settings) | 3 | ✅ ĐÃ DUYỆT |
| 5 | 🎬 | Kho Phim (NguonC) | 66 | ✅ ĐÃ DUYỆT |
| 6 | 🏠 | Cổng Chọn (Home Hub) | 14 | ✅ ĐÃ DUYỆT |

#### 🎮 Thống Kê Phím Điều Khiển TV D-pad
`OK: 23`, `DPAD_DOWN: 27`, `DPAD_RIGHT: 15`, `DPAD_UP: 10`, `DPAD_LEFT: 19`, `BACK: 11`, `MENU: 1`, `A: 1`, `B: 1`, `ENTER: 1`, `CHANNEL_UP: 1`

#### 🚨 Lỗi Phát Hiện Trong Phiên
- **[Bước 3]** [MEDIUM] Viền focus không chuẩn khi focus ở cardRoot đầu tiên
- **[Bước 4]** [MEDIUM] Viền focus không chuẩn trên các card trận đấu trong danh sách ĐANG PHÁT TRỰC TIẾP
- **[Bước 82]** [HIGH] Dialog không trap focus - Focus bị mất (NONE) khi mở EpisodePickerDialog

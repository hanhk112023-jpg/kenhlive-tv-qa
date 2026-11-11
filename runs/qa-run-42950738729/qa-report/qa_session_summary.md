### 🤖 Phiên Kiểm Thử AI QA: `QA-SESS-20261111-031222-3ccd6e`
- **Phiên bản ứng dụng:** KenhLive TV `0.1.12` (code `162`)
- **Git Commit:** `996c3d5` (redesign/apple-kl8) | **AI Brain:** OPENAI
- **Thời gian chạy:** `4229.5s` | **Điểm QA:** **88/100**
- **Độ bao phủ Tab:** **6/7 Tabs (85.7%)**
- **Tổng số bước AI:** `136` | **Lượt bấm D-pad:** `121` | **Kiểm tra Video:** `0`
- **🎬 Video Toàn Bộ Quá Trình:** `full_qa_tour.mp4`

#### 🗺️ Bản Đồ Bao Phủ 6 Tab Đa Năng
| Tab | Biểu Tượng | Tên Phân Hệ | Thao Tác | Trạng Thái |
|:---:|:---:|:---|:---:|:---:|
| 0 | ⚽ | Trực Tiếp (Live) | 7 | ✅ ĐÃ DUYỆT |
| 1 | 📅 | Lịch Thi Đấu (Schedule) | 0 | ⚪ CHƯA DUYỆT |
| 2 | 📺 | Truyền Hình (IPTV) | 1 | ✅ ĐÃ DUYỆT |
| 3 | 🔍 | Tìm Kiếm (Search) | 1 | ✅ ĐÃ DUYỆT |
| 4 | ⚙️ | Cài Đặt (Settings) | 16 | ✅ ĐÃ DUYỆT |
| 5 | 🎬 | Kho Phim (NguonC) | 58 | ✅ ĐÃ DUYỆT |
| 6 | 🏠 | Cổng Chọn (Home Hub) | 16 | ✅ ĐÃ DUYỆT |

#### 🎮 Thống Kê Phím Điều Khiển TV D-pad
`OK: 25`, `BACK: 10`, `DPAD_DOWN: 29`, `DPAD_UP: 10`, `DPAD_RIGHT: 31`, `MENU: 1`, `A: 1`, `B: 1`, `DPAD_LEFT: 13`

#### 🚨 Lỗi Phát Hiện Trong Phiên
- **[Bước 23]** [MEDIUM] Tên giải đấu hiển thị bằng tiếng Anh 'AFC U17' thay vì tiếng Việt
- **[Bước 59]** [MEDIUM] Mất focus sau khi nhấn BACK trong PlayerActivity
- **[Bước 121]** [LOW] ERROR_CODE_DECODING_FAILED khi phát VOD native trên emulator x86

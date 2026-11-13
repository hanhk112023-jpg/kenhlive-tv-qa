#!/bin/bash
# APK VIDEO TOUR — quay quá trình test APK mới trên Android TV emulator.
# Thiết kế riêng cho main line mới (source cũ + waves 1-3): TV boot thẳng Tab 0
# (Thể thao) với rail mở; chuyển tab bằng deep-link --ei tab để chắc chắn.
# Không proxy, không launcher phụ, không sửa hệ thống ngoài wm size/density.
set -u
OUT=/tmp/tour; mkdir -p $OUT
adb root >/dev/null 2>&1 || true; sleep 1
adb wait-for-device >/dev/null 2>&1 || true
adb shell wm size 1920x1080
adb shell wm density 320
adb shell settings put system accelerometer_rotation 0
adb shell settings put system user_rotation 0
# APK build ra tên app-universal-debug.apk (do ABI splits trong app/build.gradle),
# không phải app-debug.apk — tìm đúng file, thiếu thì dừng rõ ràng.
APK=$(ls app/app/build/outputs/apk/debug/*-universal-debug.apk 2>/dev/null || ls app/app/build/outputs/apk/debug/*-debug.apk 2>/dev/null | head -1)
if [ -z "$APK" ] || [ ! -f "$APK" ]; then
  echo "::error::khong thay APK debug"
  ls -R app/app/build/outputs/apk/debug/ 2>/dev/null || true
  exit 1
fi
echo "Cai APK: $APK"
adb install -r "$APK"
adb shell am force-stop com.kenhlive.tv; sleep 1
adb logcat -c

TL=$OUT/timeline.txt; : > $TL
T0=$(date +%s)
fg_app() { adb shell dumpsys window 2>/dev/null | grep -m1 -o 'com.kenhlive.tv/[^ ]*' || echo ''; }
mark() { echo "$(($(date +%s)-T0))s|$1|$(fg_app)" >> $TL; }
key() { adb shell input keyevent $1; }
go() { local n="$1" c="$2" w="$3"; key "$c"; sleep "$w"; mark "$n"; }
shot() { adb exec-out screencap -p > "$OUT/$1" 2>/dev/null || true; }
ensure_fg() {
  if [ -z "$(fg_app)" ]; then
    echo "$(($(date +%s)-T0))s|FG-LOST: mo lai app" >> $TL
    adb shell am start -W -n com.kenhlive.tv/.MainActivity >/dev/null 2>&1
    sleep 3
  fi
}
opentab() { local n="$1" t="$2"; mark "$n"; adb shell am start -W -n com.kenhlive.tv/.MainActivity --ei tab "$t" >/dev/null 2>&1; sleep 5; ensure_fg; }

# 1. Bắt đầu quay (giới hạn 175s)
adb shell rm -f /sdcard/tour.mp4
adb shell screenrecord --size 1280x720 --bit-rate 2500000 --time-limit 175 /sdcard/tour.mp4 &
REC_PID=$!
sleep 2

# 2. Boot: Tab 0 Thể thao, rail mở sẵn
mark "BOOT: Tab The thao, rail mo"
adb shell am start -W -n com.kenhlive.tv/.MainActivity > $OUT/am_start.log 2>&1
sleep 5
if [ -z "$(fg_app)" ]; then
  echo "$(($(date +%s)-T0))s|FAIL: app khong foreground" >> $TL
  cat $OUT/am_start.log >> $TL
  adb logcat -d -t 200 > $OUT/logcat_crash.txt 2>/dev/null || true
  shot 00_failfast.png
  adb shell "pkill -2 screenrecord 2>/dev/null || true"
  wait $REC_PID 2>/dev/null || true
  exit 1
fi
shot 01_boot_sports_rail.png

# 3. Rail: di chuyển xuống qua các mục để thấy focus ring
go "DOWN: rail -> Truyen hinh" 20 2
go "DOWN: rail -> Phim" 20 2
shot 02_rail_focus.png
go "UP: rail -> ve The thao" 19 1
go "UP: rail -> ve The thao" 19 1

# 4. Đóng rail (DPAD_RIGHT), duyệt thẻ trận Thể thao
go "RIGHT: dong rail vao noi dung" 22 3
shot 03_sports_content.png
go "DOWN: xuong hang tran" 20 2
go "RIGHT: sang the tran ben" 22 2
shot 04_sports_cards.png
go "DOWN: xuong them 1 hang" 20 2

# 5. Tab Lịch (tỉ số)
opentab "TAB 1: Lich thi dau" 1
shot 05_schedule.png
go "DOWN: duyet lich" 20 2
go "DOWN: duyet lich tiep" 20 2
shot 06_schedule_down.png

# 6. Tab Truyền hình
opentab "TAB 2: Truyen hinh" 2
shot 07_iptv.png
go "DOWN: xuong luoi kenh" 20 2
go "RIGHT: sang kenh ben" 22 2
shot 08_iptv_grid.png

# 7. Tab Phim
opentab "TAB 5: Phim" 5
shot 09_movies.png
go "DOWN: duyet kho phim" 20 2
go "RIGHT: sang phim ben" 22 2
shot 10_movies_browse.png

# 8. Hub (Tab 6) + BACK xem dialog/rail
opentab "TAB 6: Hub" 6
shot 11_hub.png
go "BACK: xem phan hoi" 4 3
shot 12_after_back.png

# 9. Dừng quay, kéo video về
sleep 2
adb logcat -d -s SportsStreamResolver:V KenhLive:V AndroidRuntime:E > $OUT/logcat.txt 2>/dev/null || true
adb shell "pkill -2 screenrecord 2>/dev/null || kill -2 \$(pidof screenrecord) 2>/dev/null || true"
wait $REC_PID 2>/dev/null || true
sleep 3
adb pull /sdcard/tour.mp4 $OUT/tour.mp4 >/dev/null 2>&1 || true

SZ=$(stat -c%s $OUT/tour.mp4 2>/dev/null || echo 0)
echo "KET-QUA tour.mp4=$SZ bytes"
[ "$SZ" -gt 100000 ] || { echo "::error::thieu video"; exit 1; }

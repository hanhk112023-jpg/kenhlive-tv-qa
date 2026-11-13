#!/bin/bash
# APK VIDEO TOUR (KHÁM PHÁ) — quay quá trình test APK bản Hydrogen trên
# Android TV emulator. KHÔNG theo kịch bản cứng: script không biết trước
# app có những tab nào, nút nào ở đâu. Nó chỉ biết các thao tác chung
# (phím DPAD, ENTER, BACK, chụp màn hình, dump UI) rồi TỰ DÒ:
#   - dump cây UI sau mỗi bước, đọc text đang focus và các text trên màn hình
#   - đi hết các mục trên rail bằng DOWN, ghi lại nhãn từng mục nó tìm thấy
#   - vào nội dung bằng RIGHT, duyệt thẻ bằng DOWN/RIGHT, ghi lại text focus
#   - mở từng tab nó đã khám phá ra (bằng ENTER trên mục rail đó), chụp + báo cáo
#   - BACK xem phản hồi, kiểm tra crash qua logcat sau mỗi bước
# Kết quả: video + ảnh từng màn hình + exploration.log ghi lại những gì nó
# thực sự thấy (màn hình trống, mất focus, crash...), không phải những gì
# mình đoán trước.
set -u
OUT=/tmp/tour; mkdir -p $OUT
adb root >/dev/null 2>&1 || true; sleep 1
adb wait-for-device >/dev/null 2>&1 || true
adb shell wm size 1920x1080
adb shell wm density 320
adb shell settings put system accelerometer_rotation 0
adb shell settings put system user_rotation 0
# APK build ra tên app-universal-debug.apk (do ABI splits trong app/build.gradle.kts),
# không phải app-debug.apk — tìm đúng file, thiếu thì dừng rõ ràng.
APK=$(ls app/build/outputs/apk/debug/*-universal-debug.apk 2>/dev/null || ls app/build/outputs/apk/debug/*-debug.apk 2>/dev/null | head -1)
if [ -z "$APK" ] || [ ! -f "$APK" ]; then
  echo "::error::khong thay APK debug"
  ls -R app/build/outputs/apk/debug/ 2>/dev/null || true
  exit 1
fi
echo "Cai APK: $APK"
adb install -r "$APK"
adb shell am force-stop com.kenhlive.tv; sleep 1
adb logcat -c

TL=$OUT/timeline.txt; : > $TL
LOG=$OUT/exploration.log; : > $LOG
T0=$(date +%s)
MAIN="com.kenhlive.tv/.ui.MainActivity"
STEP=0
fg_app() { adb shell dumpsys window 2>/dev/null | grep -m1 -o 'com.kenhlive.tv/[^ ]*' || echo ''; }
mark() { echo "$(($(date +%s)-T0))s|$1|$(fg_app)" >> $TL; }
key() { adb shell input keyevent $1; }
shot() { adb exec-out screencap -p > "$OUT/$1" 2>/dev/null || true; }

# Đọc cây UI: in ra text đang focus, số node có text, vài text đầu.
# Dùng python3 có sẵn trên runner để parse XML dump.
dump_summary() {
  local tag="$1"
  adb shell uiautomator dump /sdcard/window_dump.xml >/dev/null 2>&1 || { echo "[$tag] DUMP-FAIL" >> $LOG; return 1; }
  adb pull /sdcard/window_dump.xml "$OUT/dump_$tag.xml" >/dev/null 2>&1 || { echo "[$tag] PULL-FAIL" >> $LOG; return 1; }
  python3 - "$OUT/dump_$tag.xml" "$tag" >> $LOG 2>/dev/null <<'PYEOF' || echo "[$tag] PARSE-FAIL" >> $LOG
import sys, xml.etree.ElementTree as ET
path, tag = sys.argv[1], sys.argv[2]
try:
    root = ET.parse(path).getroot()
except Exception as e:
    print(f"[{tag}] XML-ERR {e}"); sys.exit(0)
texts, focused, focusable = [], "", 0
for n in root.iter("node"):
    t = (n.get("text") or "").strip()
    if t: texts.append(t)
    if n.get("focused") == "true": focused = t or n.get("content-desc", "")
    if n.get("focusable") == "true": focusable += 1
print(f"[{tag}] FOCUS={focused!r} TEXTS={len(texts)} FOCUSABLE={focusable}")
for t in texts[:12]: print(f"[{tag}]   - {t}")
if len(texts) < 3: print(f"[{tag}] FLAG: MAN HINH GAN NHU TRONG ({len(texts)} text)")
if any("has stopped" in t or "keeps stopping" in t for t in texts): print(f"[{tag}] FLAG: CO THE CRASH (dialog dung ung dung)")
PYEOF
}

# Một bước khám phá: ghi timeline, chụp ảnh, dump UI, kiểm tra crash.
explore() {
  local name="$1"
  STEP=$((STEP+1))
  mark "$name"
  shot "step_$(printf %02d $STEP)_$2.png"
  dump_summary "step$(printf %02d $STEP)"
  if [ -z "$(fg_app)" ]; then
    echo "[step$STEP] FLAG: APP KHONG CON FOREGROUND" >> $LOG
    adb shell am start -W -n "$MAIN" >/dev/null 2>&1; sleep 3
  fi
  if adb logcat -d -t 200 2>/dev/null | grep -q "FATAL EXCEPTION"; then
    echo "[step$STEP] FLAG: CO FATAL EXCEPTION TRONG LOGCAT" >> $LOG
    adb logcat -d -t 300 > "$OUT/logcat_crash_step$STEP.txt" 2>/dev/null || true
    adb logcat -c
  fi
}

# 1. Bắt đầu quay (giới hạn 175s)
adb shell rm -f /sdcard/tour.mp4
adb shell screenrecord --size 1280x720 --bit-rate 2500000 --time-limit 175 /sdcard/tour.mp4 &
REC_PID=$!
sleep 2

# 2. Boot: mở app, xem nó tự vào đâu
mark "BOOT"
adb shell am start -W -n "$MAIN" > $OUT/am_start.log 2>&1
sleep 5
if [ -z "$(fg_app)" ]; then
  echo "FAIL: app khong foreground" >> $LOG
  cat $OUT/am_start.log >> $LOG
  adb logcat -d -t 200 > $OUT/logcat_crash.txt 2>/dev/null || true
  shot 00_failfast.png
  adb shell "pkill -2 screenrecord 2>/dev/null || true"
  wait $REC_PID 2>/dev/null || true
  exit 1
fi
explore "BOOT: man hinh dau tien" boot

# 3. Dò rail: DOWN liên tiếp, ghi lại nhãn từng mục focus được.
# Dừng khi focus quay lại nhãn đầu (đi hết vòng) hoặc 8 lần.
echo "[rail] Bat dau do rail" >> $LOG
RAIL_LABELS=()
PREV_FOCUS=""
for i in 1 2 3 4 5 6 7 8; do
  key 20; sleep 2
  F=$(adb shell uiautomator dump /sdcard/window_dump.xml >/dev/null 2>&1 && adb pull /sdcard/window_dump.xml $OUT/rail_tmp.xml >/dev/null 2>&1 && python3 -c "import xml.etree.ElementTree as ET; r=ET.parse('$OUT/rail_tmp.xml').getroot(); print(next(( (n.get('text') or n.get('content-desc','')).strip() for n in r.iter('node') if n.get('focused')=='true'), ''))" 2>/dev/null || echo "")
  echo "[rail] DOWN $i -> FOCUS=${F!r}" >> $LOG
  if [ -n "$F" ] && [ "$F" = "$PREV_FOCUS" ]; then echo "[rail] focus lap lai, dung do" >> $LOG; break; fi
  if [ -n "$F" ]; then
    case " ${RAIL_LABELS[*]} " in *" $F "*) ;; *) RAIL_LABELS+=("$F");; esac
    PREV_FOCUS="$F"
  fi
done
echo "[rail] Cac muc tim thay: ${RAIL_LABELS[*]}" >> $LOG
explore "RAIL: sau khi do het rail" rail

# 4. Về đầu rail (UP nhiều lần), rồi RIGHT vào nội dung, duyệt thẻ.
for i in 1 2 3 4 5 6 7 8; do key 19; sleep 1; done
key 22; sleep 3
explore "NOI DUNG: sau RIGHT khoi rail" content
key 20; sleep 2; explore "NOI DUNG: DOWN 1" content_down1
key 22; sleep 2; explore "NOI DUNG: RIGHT 1" content_right1
key 20; sleep 2; explore "NOI DUNG: DOWN 2" content_down2

# 5. Mở từng tab đã khám phá: về rail (LEFT), DOWN tới đúng nhãn, ENTER.
for label in "${RAIL_LABELS[@]}"; do
  for i in 1 2 3 4 5; do key 21; sleep 1; done
  FOUND=0
  for i in 1 2 3 4 5 6 7 8; do
    F=$(adb shell uiautomator dump /sdcard/window_dump.xml >/dev/null 2>&1 && adb pull /sdcard/window_dump.xml $OUT/rail_tmp.xml >/dev/null 2>&1 && python3 -c "import xml.etree.ElementTree as ET; r=ET.parse('$OUT/rail_tmp.xml').getroot(); print(next(( (n.get('text') or n.get('content-desc','')).strip() for n in r.iter('node') if n.get('focused')=='true'), ''))" 2>/dev/null || echo "")
    if [ "$F" = "$label" ]; then FOUND=1; break; fi
    key 20; sleep 1
  done
  if [ "$FOUND" = "1" ]; then
    key 23; sleep 4
    explore "TAB: mo [$label]" "tab"
  else
    echo "[tab] KHONG TIM LAI DUOC muc [$label], bo qua" >> $LOG
  fi
done

# 6. BACK xem phản hồi
key 4; sleep 3
explore "BACK: phan hoi sau BACK" after_back

# 7. Dừng quay, kéo video về
sleep 2
adb logcat -d -s KenhLive:V AndroidRuntime:E > $OUT/logcat.txt 2>/dev/null || true
adb shell "pkill -2 screenrecord 2>/dev/null || kill -2 \$(pidof screenrecord) 2>/dev/null || true"
wait $REC_PID 2>/dev/null || true
sleep 3
adb pull /sdcard/tour.mp4 $OUT/tour.mp4 >/dev/null 2>&1 || true

SZ=$(stat -c%s $OUT/tour.mp4 2>/dev/null || echo 0)
echo "KET-QUA tour.mp4=$SZ bytes"
[ "$SZ" -gt 100000 ] || { echo "::error::thieu video"; exit 1; }

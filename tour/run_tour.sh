#!/bin/bash
# APK VIDEO TOUR (KHÁM PHÁ) — quay quá trình test APK bản chính (source cũ + waves) trên
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
# APK: lấy từ biến môi trường APK (workflow generic truyền đường dẫn tuyệt đối)
# hoặc tìm theo layout bản chính (app checkout ở path app).
if [ -n "${APK:-}" ]; then
  APK_PATH="$APK"
else
  APK_PATH=$(ls app/app/build/outputs/apk/debug/*-universal-debug.apk 2>/dev/null || ls app/app/build/outputs/apk/debug/*-debug.apk 2>/dev/null | head -1)
fi
if [ -z "$APK_PATH" ] || [ ! -f "$APK_PATH" ]; then
  echo "::error::khong thay APK debug"
  ls -R app/app/build/outputs/apk/debug/ 2>/dev/null || true
  exit 1
fi
echo "Cai APK: $APK_PATH"
adb install -r "$APK_PATH"
adb shell am force-stop com.kenhlive.tv; sleep 1
adb logcat -c

TL=$OUT/timeline.txt; : > $TL
LOG=$OUT/exploration.log; : > $LOG
T0=$(date +%s)
# Activity launcher: workflow generic dò từ manifest rồi truyền qua env MAIN;
# mặc định là bản chính.
MAIN="${MAIN:-com.kenhlive.tv/.MainActivity}"
STEP=0
fg_app() { adb shell dumpsys window 2>/dev/null | grep -m1 -o 'com.kenhlive.tv/[^ ]*' || echo ''; }
mark() { echo "$(($(date +%s)-T0))s|$1|$(fg_app)" >> $TL; }
key() { adb shell input keyevent $1; }
shot() { adb exec-out screencap -p > "$OUT/$1" 2>/dev/null || true; }

# Đọc cây UI: in ra text đang focus, số node có text, vài text đầu.
# Dùng python3 có sẵn trên runner để parse XML dump.
# Lưu ý: node focus có thể là container không có text (ví dụ mục rail) —
# khi đó lấy text của con trực tiếp đầu tiên có text.
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
def focus_text(n):
    t = (n.get("text") or "").strip()
    if t: return t
    t = (n.get("content-desc") or "").strip()
    if t: return t
    for c in n:
        t = (c.get("text") or "").strip() or (c.get("content-desc") or "").strip()
        if t: return t
    return ""
texts, focused, focusable = [], "", 0
for n in root.iter("node"):
    t = (n.get("text") or "").strip()
    if t: texts.append(t)
    if n.get("focused") == "true": focused = focus_text(n)
    if n.get("focusable") == "true": focusable += 1
print(f"[{tag}] FOCUS={focused!r} TEXTS={len(texts)} FOCUSABLE={focusable}")
for t in texts[:12]: print(f"[{tag}]   - {t}")
if len(texts) < 3: print(f"[{tag}] FLAG: MAN HINH GAN NHU TRONG ({len(texts)} text)")
if any("has stopped" in t or "keeps stopping" in t for t in texts): print(f"[{tag}] FLAG: CO THE CRASH (dialog dung ung dung)")
PYEOF
}

# Thông tin node đang focus: "text|x_min|x_max" (bounds của chính node focus).
# Dùng để phân biệt mục rail (x_max <= 520) với thẻ nội dung — boot có thể
# focus ở nội dung (hero) chứ không phải trên rail, nên dò rail mà không lọc
# bounds sẽ nhặt nhầm tiêu đề trận đấu làm nhãn tab (tour bản chính lần 1).
focused_info() {
  adb shell uiautomator dump /sdcard/window_dump.xml >/dev/null 2>&1 || { echo "|0|0"; return; }
  adb pull /sdcard/window_dump.xml $OUT/rail_tmp.xml >/dev/null 2>&1 || { echo "|0|0"; return; }
  python3 - "$OUT/rail_tmp.xml" 2>/dev/null <<'PYEOF' || echo "|0|0"
import sys, xml.etree.ElementTree as ET
root = ET.parse(sys.argv[1]).getroot()
def focus_text(n):
    t = (n.get("text") or "").strip()
    if t: return t
    t = (n.get("content-desc") or "").strip()
    if t: return t
    for c in n:
        t = (c.get("text") or "").strip() or (c.get("content-desc") or "").strip()
        if t: return t
    return ""
for n in root.iter("node"):
    if n.get("focused") == "true":
        b = n.get("bounds", "[0,0][0,0]")
        try:
            parts = [int(v) for v in b.replace("[", " ").replace("]", " ").replace(",", " ").split()]
            x1, x2 = parts[0], parts[2]
        except Exception:
            x1, x2 = 0, 0
        print(f"{focus_text(n)}|{x1}|{x2}")
        break
else:
    print("|0|0")
PYEOF
}

# Lấy text của node đang focus (kèm fallback con trực tiếp), dùng khi dò rail.
focused_text() { focused_info | cut -d'|' -f1; }

# Focus có nằm trong vùng rail không? Rail 240dp @ density 320 = 480px, chừa biên 520.
in_rail_zone() {
  local xmax="${1##*|}"
  [ -n "$xmax" ] && [ "$xmax" -gt 0 ] && [ "$xmax" -le 520 ]
}

# Đưa focus vào rail: bấm LEFT tối đa 4 lần cho tới khi focus nằm trong vùng rail.
# Trả 0 nếu vào được rail, 1 nếu không (vd: màn hình trống làm mất focus).
ensure_rail_focus() {
  local i info
  for i in 1 2 3 4; do
    info=$(focused_info)
    if in_rail_zone "$info"; then return 0; fi
    key 21; sleep 1
  done
  info=$(focused_info)
  if in_rail_zone "$info"; then return 0; fi
  echo "[rail] KHONG VAO DUOC RAIL (focus hien tai: '${info%%|*}')" >> $LOG
  return 1
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

# 2. Boot: mở app, xem nó tự vào đâu. Thử MAIN trước, nếu app không lên thì
# thử activity còn lại (.MainActivity <-> .ui.MainActivity / SplashActivity).
try_launch() {
  adb shell am start -W -n "$1" > $OUT/am_start.log 2>&1
  sleep 5
  [ -n "$(fg_app)" ]
}
if ! try_launch "$MAIN"; then
  case "$MAIN" in
    *.ui.SplashActivity) ALT="com.kenhlive.tv/.ui.MainActivity" ;;
    *.ui.MainActivity) ALT="com.kenhlive.tv/.MainActivity" ;;
    *) ALT="com.kenhlive.tv/.ui.MainActivity" ;;
  esac
  echo "MAIN $MAIN khong len, thu $ALT" >> $LOG
  if try_launch "$ALT"; then MAIN="$ALT"; fi
fi
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

# 3. Dò rail: đưa focus vào rail trước (boot có thể focus ở nội dung như hero),
# rồi DOWN liên tiếp, chỉ ghi nhãn nào có bounds trong vùng rail.
# Dừng khi focus lặp lại, rời khỏi rail, hoặc mất focus. Ghi cả mục đầu tiên
# (không bỏ qua như bản cũ chỉ ghi sau mỗi lần DOWN).
echo "[rail] Bat dau do rail" >> $LOG
RAIL_LABELS=()
PREV_FOCUS=""
if ensure_rail_focus; then
  for i in 1 2 3 4 5 6 7 8; do
    INFO=$(focused_info); F="${INFO%%|*}"
    if [ -z "$F" ]; then echo "[rail] mat focus, dung do" >> $LOG; break; fi
    if ! in_rail_zone "$INFO"; then echo "[rail] focus roi khoi rail ('$F'), dung do" >> $LOG; break; fi
    if [ "$F" = "$PREV_FOCUS" ]; then echo "[rail] focus lap lai, dung do" >> $LOG; break; fi
    echo "[rail] muc $i: '$F'" >> $LOG
    case " ${RAIL_LABELS[*]} " in *" $F "*) ;; *) RAIL_LABELS+=("$F");; esac
    PREV_FOCUS="$F"
    key 20; sleep 2
  done
else
  echo "[rail] BO QUA do rail (khong vao duoc rail)" >> $LOG
fi
echo "[rail] Cac muc tim thay: ${RAIL_LABELS[*]}" >> $LOG
explore "RAIL: sau khi do het rail" rail

# 4. Về đầu rail (UP nhiều lần), rồi RIGHT vào nội dung, duyệt thẻ.
for i in 1 2 3 4 5 6 7 8; do key 19; sleep 1; done
key 22; sleep 3
explore "NOI DUNG: sau RIGHT khoi rail" content
key 20; sleep 2; explore "NOI DUNG: DOWN 1" content_down1
key 22; sleep 2; explore "NOI DUNG: RIGHT 1" content_right1
key 20; sleep 2; explore "NOI DUNG: DOWN 2" content_down2

# 5. Mở từng tab đã khám phá: vào lại rail, DOWN tới đúng nhãn, ENTER.
for label in "${RAIL_LABELS[@]}"; do
  if ! ensure_rail_focus; then
    echo "[tab] KHONG VAO DUOC RAIL de tim [$label], bo qua" >> $LOG
    continue
  fi
  FOUND=0
  for i in 1 2 3 4 5 6 7 8; do
    INFO=$(focused_info); F="${INFO%%|*}"
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

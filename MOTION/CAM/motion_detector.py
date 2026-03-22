import cv2
import datetime
import os
import time
import shutil
import csv
import signal
import sys
import smtplib
import threading
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage

# ============================================================
#  SETTINGS  — adjust these without touching the rest
# ============================================================
CAMERA_INDEX        = 0       # 0 = default webcam; change for USB / IP cam
FRAME_WIDTH         = 640
FRAME_HEIGHT        = 480
FPS                 = 20.0

MOTION_THRESHOLD    = 25      # pixel-difference sensitivity (lower = more sensitive)
MIN_CONTOUR_AREA    = 1000    # ignore blobs smaller than this (noise filter)
MOTION_TIMEOUT      = 5       # seconds of no-motion before stopping recording
MIN_RECORD_SECS     = 10       # always record at least this long once triggered
COOLDOWN_SECS       = 30      # seconds to wait before a new event can trigger after recording stops

RETENTION_DAYS      = 7       # auto-delete folders older than this
RECORDINGS_DIR      = "recordings"
SNAPSHOTS_DIR       = "snapshots"
LOG_FILE            = "motion_log.csv"

SHOW_THRESHOLD_WIN  = True    # show the binary diff window (useful for tuning)

# ── Email settings ───────────────────────────────────────────
EMAIL_ENABLED       = True    # set False to disable alerts entirely
EMAIL_SENDER        = "sunnylostinlight@gmail.com"
EMAIL_PASSWORD      = "iigumnvzzqptinlr"   # use an App Password, not your account password
EMAIL_RECIPIENT     = "luthermaximuof@gmail.com"
EMAIL_SUBJECT       = "⚠️ Motion Detected"
SMTP_HOST           = "smtp.gmail.com"
SMTP_PORT           = 587
# ============================================================


# ── Graceful shutdown on Ctrl-C ──────────────────────────────
def shutdown(sig=None, frame=None):
    print("\n🔴 Shutting down...")
    cap.release()
    if out is not None:
        out.release()
    cv2.destroyAllWindows()
    sys.exit(0)

signal.signal(signal.SIGINT, shutdown)


# ── Email alert (runs in background thread) ──────────────────
def send_alert(snapshot_path, timestamp):
    """Send an email alert with the snapshot attached. Runs in a daemon thread."""
    try:
        msg = MIMEMultipart()
        msg["From"]    = EMAIL_SENDER
        msg["To"]      = EMAIL_RECIPIENT
        msg["Subject"] = EMAIL_SUBJECT

        body = (
            f"Motion was detected at {timestamp}.\n\n"
            f"Snapshot attached. Check your recordings folder for the full clip.\n\n"
            f"— Motion Detector"
        )
        msg.attach(MIMEText(body, "plain"))

        # Attach snapshot if it exists
        if os.path.exists(snapshot_path):
            with open(snapshot_path, "rb") as img_file:
                img = MIMEImage(img_file.read(), name=os.path.basename(snapshot_path))
                msg.attach(img)

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_SENDER, EMAIL_RECIPIENT, msg.as_string())

        print(f"📧  Alert sent to {EMAIL_RECIPIENT}")

    except Exception as e:
        print(f"⚠️  Email failed: {e}")

def send_alert_async(snapshot_path, timestamp):
    """Fire-and-forget email in a background thread so it never blocks the camera loop."""
    if not EMAIL_ENABLED:
        return
    t = threading.Thread(target=send_alert, args=(snapshot_path, timestamp), daemon=True)
    t.start()


# ── Helpers ──────────────────────────────────────────────────
def ensure_dirs():
    os.makedirs(RECORDINGS_DIR, exist_ok=True)
    os.makedirs(SNAPSHOTS_DIR, exist_ok=True)

def init_log():
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, mode="w", newline="") as f:
            csv.writer(f).writerow(["Timestamp", "Duration (s)", "Video File", "Snapshot File"])

def log_event(timestamp, duration, video_file, snapshot_file):
    with open(LOG_FILE, mode="a", newline="") as f:
        csv.writer(f).writerow([timestamp, f"{duration:.1f}", video_file, snapshot_file])

def daily_folder(base_dir):
    folder = os.path.join(base_dir, datetime.datetime.now().strftime("%Y-%m-%d"))
    os.makedirs(folder, exist_ok=True)
    return folder

def cleanup_old(base_dir, days):
    if not os.path.isdir(base_dir):
        return
    cutoff = datetime.datetime.now()
    for entry in os.listdir(base_dir):
        path = os.path.join(base_dir, entry)
        try:
            age = (cutoff - datetime.datetime.strptime(entry, "%Y-%m-%d")).days
            if age > days:
                shutil.rmtree(path)
                print(f"🗑️  Removed old folder: {path}")
        except ValueError:
            pass

def in_cooldown():
    """Return (is_cooling, seconds_remaining)."""
    if cooldown_start is None:
        return False, 0
    remaining = COOLDOWN_SECS - (time.time() - cooldown_start)
    return remaining > 0, max(0.0, remaining)

def draw_overlay(frame, motion_detected, recording, on_cooldown, cooldown_remaining, motion_count, rec_elapsed):
    h, w = frame.shape[:2]
    now_str = datetime.datetime.now().strftime("%Y-%m-%d  %H:%M:%S")

    if recording:
        color = (0, 0, 255)
        label = f"● REC  {rec_elapsed:.0f}s"
    elif on_cooldown:
        color = (0, 165, 255)
        label = f"⏳ Cooldown  {cooldown_remaining:.0f}s"
    elif motion_detected:
        color = (0, 165, 255)
        label = "⚡ Motion"
    else:
        color = (0, 200, 0)
        label = "● Monitoring"

    cv2.rectangle(frame, (0, 0), (w, 32), (0, 0, 0), -1)
    cv2.putText(frame, label,   (10, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
    cv2.putText(frame, now_str, (w - 230, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (200, 200, 200), 1)
    cv2.putText(frame, f"Events: {motion_count}",
                (10, h - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (180, 180, 180), 1)


# ── Startup ──────────────────────────────────────────────────
ensure_dirs()
init_log()
cleanup_old(RECORDINGS_DIR, RETENTION_DAYS)
cleanup_old(SNAPSHOTS_DIR,  RETENTION_DAYS)

cap = cv2.VideoCapture(CAMERA_INDEX)
cap.set(cv2.CAP_PROP_FRAME_WIDTH,  FRAME_WIDTH)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)

if not cap.isOpened():
    print("❌ Cannot open camera. Check CAMERA_INDEX in settings.")
    sys.exit(1)

bg_subtractor = cv2.createBackgroundSubtractorMOG2(
    history=500, varThreshold=MOTION_THRESHOLD, detectShadows=False
)

previous_gray  = None
recording      = False
out            = None
last_motion_ts = None
rec_start_ts   = None
rec_video_file = None
rec_snap_file  = None
rec_start_time = None
cooldown_start = None
motion_events  = 0

print("✅ Motion detector started. Press 'q' to quit.")
print(f"   Saving to   →  {RECORDINGS_DIR}/  &  {SNAPSHOTS_DIR}/")
print(f"   Log file    →  {LOG_FILE}")
print(f"   Cooldown    →  {COOLDOWN_SECS}s after each recording")
print(f"   Email alerts→  {'ON  → ' + EMAIL_RECIPIENT if EMAIL_ENABLED else 'OFF'}\n")


# ── Main loop ────────────────────────────────────────────────
while True:
    ret, frame = cap.read()
    if not ret:
        print("⚠️  Frame grab failed — retrying...")
        time.sleep(0.1)
        continue

    # ── Motion detection ──
    gray    = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray    = cv2.GaussianBlur(gray, (21, 21), 0)
    fg_mask = bg_subtractor.apply(gray)
    fg_mask = cv2.dilate(fg_mask, None, iterations=2)

    motion_detected = False
    if previous_gray is not None:
        diff     = cv2.absdiff(previous_gray, gray)
        thresh   = cv2.threshold(diff, MOTION_THRESHOLD, 255, cv2.THRESH_BINARY)[1]
        thresh   = cv2.dilate(thresh, None, iterations=2)
        combined = cv2.bitwise_or(fg_mask, thresh)
    else:
        combined = fg_mask

    contours, _ = cv2.findContours(combined, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    for cnt in contours:
        if cv2.contourArea(cnt) < MIN_CONTOUR_AREA:
            continue
        motion_detected = True
        last_motion_ts  = time.time()
        x, y, w, h = cv2.boundingRect(cnt)
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

    # ── Cooldown check ──
    on_cooldown, cooldown_remaining = in_cooldown()

    # ── Recording logic ──
    rec_elapsed = (time.time() - rec_start_time) if rec_start_time else 0.0

    if motion_detected and not recording and not on_cooldown:
        # ---- Start a new recording ----
        motion_events += 1
        ts = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

        rec_video_file = os.path.join(daily_folder(RECORDINGS_DIR), f"{ts}.avi")
        rec_snap_file  = os.path.join(daily_folder(SNAPSHOTS_DIR),  f"{ts}.jpg")

        fourcc         = cv2.VideoWriter_fourcc(*"XVID")
        out            = cv2.VideoWriter(rec_video_file, fourcc, FPS, (frame.shape[1], frame.shape[0]))
        recording      = True
        rec_start_time = time.time()
        rec_start_ts   = ts
        cooldown_start = None  # clear any previous cooldown

        cv2.imwrite(rec_snap_file, frame)
        send_alert_async(rec_snap_file, ts)   # 📧 non-blocking

        print(f"🎥  Recording started  → {rec_video_file}")
        print(f"📸  Snapshot saved     → {rec_snap_file}")

    elif recording:
        elapsed_since_motion = time.time() - (last_motion_ts or rec_start_time)
        min_met = rec_elapsed >= MIN_RECORD_SECS

        if not motion_detected and elapsed_since_motion > MOTION_TIMEOUT and min_met:
            # ---- Stop recording & begin cooldown ----
            duration       = time.time() - rec_start_time
            recording      = False
            cooldown_start = time.time()
            out.release()
            out = None
            log_event(rec_start_ts, duration, rec_video_file, rec_snap_file)
            print(f"🛑  Recording stopped  ({duration:.1f}s)")
            print(f"⏳  Cooldown started   ({COOLDOWN_SECS}s)")
            rec_start_time = None

    elif motion_detected and on_cooldown:
        # Silent in the loop — cooldown countdown is visible on screen
        pass

    if recording and out is not None:
        out.write(frame)

    # ── Overlay & display ──
    draw_overlay(frame, motion_detected, recording, on_cooldown,
                 cooldown_remaining, motion_events, rec_elapsed)
    cv2.imshow("Security Camera", frame)

    if SHOW_THRESHOLD_WIN:
        cv2.imshow("Motion Mask", combined)

    previous_gray = gray

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break


shutdown()

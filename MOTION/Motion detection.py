import cv2
import datetime
import os
import time
import shutil
import csv

# ==== SETTINGS ====
MOTION_TIMEOUT = 5        # seconds after motion ends before stopping recording
RETENTION_DAYS = 7        # keep only last X days of recordings/snapshots
FRAME_WIDTH = 640
FRAME_HEIGHT = 480
LOG_FILE = "motion_log.csv"
# ==================

# Initialize camera
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)

previous_frame = None
recording = False
out = None
last_motion_time = None

# Ensure base directories exist
os.makedirs("recordings", exist_ok=True)
os.makedirs("snapshots", exist_ok=True)

# Setup log file if not exists
if not os.path.exists(LOG_FILE):
    with open(LOG_FILE, mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["Timestamp", "Video File", "Snapshot File"])

def log_event(timestamp, video_file, snapshot_file):
    """Append motion event to log CSV."""
    with open(LOG_FILE, mode="a", newline="") as file:
        writer = csv.writer(file)
        writer.writerow([timestamp, video_file, snapshot_file])

def get_daily_folder(base_dir):
    """Return today's folder path, creating if missing."""
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    folder = os.path.join(base_dir, today)
    os.makedirs(folder, exist_ok=True)
    return folder

def cleanup_old_folders(base_dir, retention_days):
    """Delete folders older than retention_days."""
    now = datetime.datetime.now()
    for folder in os.listdir(base_dir):
        folder_path = os.path.join(base_dir, folder)
        try:
            folder_date = datetime.datetime.strptime(folder, "%Y-%m-%d")
            age = (now - folder_date).days
            if age > retention_days:
                shutil.rmtree(folder_path)
                print(f"🗑️ Deleted old folder: {folder_path}")
        except ValueError:
            continue  # skip non-date folders

# Run cleanup at start
cleanup_old_folders("recordings", RETENTION_DAYS)
cleanup_old_folders("snapshots", RETENTION_DAYS)

while True:
    ret, frame = cap.read()
    if not ret:
        print("Failed to grab frame")
        break

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (21, 21), 0)

    if previous_frame is None:
        previous_frame = gray
        continue

    frame_diff = cv2.absdiff(previous_frame, gray)
    thresh = cv2.threshold(frame_diff, 25, 255, cv2.THRESH_BINARY)[1]
    thresh = cv2.dilate(thresh, None, iterations=2)

    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    motion_detected = False

    for contour in contours:
        if cv2.contourArea(contour) < 1000:
            continue
        motion_detected = True
        last_motion_time = time.time()
        (x, y, w, h) = cv2.boundingRect(contour)
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

    # Overlay text
    status_text = "Recording..." if recording else "No Motion"
    cv2.putText(frame, status_text, (10, 20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255) if recording else (0, 255, 0), 2)
    cv2.putText(frame, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                (10, frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)

    cv2.imshow("Security Camera", frame)

    # Start recording + snapshot
    if motion_detected and not recording:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

        rec_folder = get_daily_folder("recordings")
        snap_folder = get_daily_folder("snapshots")

        video_filename = os.path.join(rec_folder, f"{timestamp}.avi")
        snapshot_filename = os.path.join(snap_folder, f"{timestamp}.jpg")

        fourcc = cv2.VideoWriter_fourcc(*"XVID")
        out = cv2.VideoWriter(video_filename, fourcc, 20.0, (frame.shape[1], frame.shape[0]))
        recording = True

        cv2.imwrite(snapshot_filename, frame)
        log_event(timestamp, video_filename, snapshot_filename)

        print(f"🎥 Recording started: {video_filename}")
        print(f"📸 Snapshot saved: {snapshot_filename}")
        print(f"📝 Logged event at {timestamp}")

    # Stop recording if timeout passed
    elif recording and last_motion_time is not None:
        if time.time() - last_motion_time > MOTION_TIMEOUT:
            recording = False
            out.release()
            out = None
            print("🛑 Recording stopped (no motion)")

    # Write frames if recording
    if recording and out is not None:
        out.write(frame)

    previous_frame = gray

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
if out is not None:
    out.release()
cv2.destroyAllWindows()

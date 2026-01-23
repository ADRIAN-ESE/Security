# motion_face_recog.py
import cv2
import datetime
import os
import time
import shutil
import csv
import numpy as np

# ========== SETTINGS ==========
MOTION_TIMEOUT = 5
RETENTION_DAYS = 7
FRAME_WIDTH = 640
FRAME_HEIGHT = 480
LOG_FILE = "motion_face_log.csv"

# Face recognition settings
KNOWN_FACES_DIR = "known_faces"   # structure: known_faces/{person_name}/{img1.jpg,...}
FACE_SNAPSHOT_DIR = "recognized_snapshots"
HAAR_CASCADE_PATH = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
LBPH_MODEL_FILE = "lbph_model.yml"
CONFIDENCE_THRESHOLD = 70  # smaller is better match for LBPH (experiment)
# ==============================

# Ensure folders exist
os.makedirs("recordings", exist_ok=True)
os.makedirs("snapshots", exist_ok=True)
os.makedirs(FACE_SNAPSHOT_DIR, exist_ok=True)
os.makedirs(KNOWN_FACES_DIR, exist_ok=True)

# init video
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)

# motion variables
previous_frame = None
recording = False
out = None
last_motion_time = None

# face detector and recognizer
face_cascade = cv2.CascadeClassifier(HAAR_CASCADE_PATH)
recognizer = cv2.face.LBPHFaceRecognizer_create()

# Setup log file if not exists
if not os.path.exists(LOG_FILE):
    with open(LOG_FILE, mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["Timestamp", "Video File", "Snapshot File", "Recognized"])

def log_event(timestamp, video_file, snapshot_file, recognized_names):
    with open(LOG_FILE, mode="a", newline="") as file:
        writer = csv.writer(file)
        writer.writerow([timestamp, video_file, snapshot_file, ";".join(recognized_names)])

def get_daily_folder(base_dir):
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    folder = os.path.join(base_dir, today)
    os.makedirs(folder, exist_ok=True)
    return folder

def cleanup_old_folders(base_dir, retention_days):
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
            continue

# Train LBPH recognizer from KNOWN_FACES_DIR
def prepare_training_data(known_dir):
    """
    Returns faces (grayscale images) and labels (ints), plus label->name mapping.
    Expects known_dir/name/*.jpg
    """
    faces = []
    labels = []
    label_map = {}
    cur_label = 0

    for person_name in sorted(os.listdir(known_dir)):
        person_path = os.path.join(known_dir, person_name)
        if not os.path.isdir(person_path):
            continue
        label_map[cur_label] = person_name
        for filename in os.listdir(person_path):
            filepath = os.path.join(person_path, filename)
            img = cv2.imread(filepath)
            if img is None:
                continue
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            # detect largest face in the image
            faces_rects = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)
            if len(faces_rects) == 0:
                continue
            # choose largest face
            x,y,w,h = max(faces_rects, key=lambda r: r[2]*r[3])
            roi = gray[y:y+h, x:x+w]
            roi_resized = cv2.resize(roi, (200, 200))
            faces.append(roi_resized)
            labels.append(cur_label)
        cur_label += 1

    return faces, labels, label_map

# Try to load existing model or train if possible
if os.path.exists(LBPH_MODEL_FILE):
    try:
        recognizer.read(LBPH_MODEL_FILE)
        # We also need label_map stored; for simplicity, store mapping file
        label_map_path = LBPH_MODEL_FILE + ".labels.npy"
        if os.path.exists(label_map_path):
            label_map = np.load(label_map_path, allow_pickle=True).item()
        else:
            label_map = {}
        print("Loaded existing LBPH model.")
    except Exception as e:
        print("Failed to load model:", e)
        label_map = {}
else:
    faces, labels, label_map = prepare_training_data(KNOWN_FACES_DIR)
    if len(faces) > 0:
        recognizer.train(faces, np.array(labels))
        recognizer.write(LBPH_MODEL_FILE)
        np.save(LBPH_MODEL_FILE + ".labels.npy", label_map)
        print(f"Trained LBPH model with {len(set(labels))} identities.")
    else:
        label_map = {}
        print("No training data found in known_faces/. Please add face images before expecting recognition.")

# Run cleanup at start
cleanup_old_folders("recordings", RETENTION_DAYS)
cleanup_old_folders("snapshots", RETENTION_DAYS)

while True:
    ret, frame = cap.read()
    if not ret:
        print("Failed to grab frame")
        break

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray_blur = cv2.GaussianBlur(gray, (21, 21), 0)

    if previous_frame is None:
        previous_frame = gray_blur
        continue

    frame_diff = cv2.absdiff(previous_frame, gray_blur)
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

    status_text = "Recording..." if recording else "No Motion"
    cv2.putText(frame, status_text, (10, 20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255) if recording else (0, 255, 0), 2)
    cv2.putText(frame, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                (10, frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)

    cv2.imshow("Security Camera", frame)

    # Start recording + snapshot + face recognition
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

        # Face detection on the snapshot and recognition
        gray_snap = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces_rects = face_cascade.detectMultiScale(gray_snap, scaleFactor=1.1, minNeighbors=5)
        recognized = []
        for (fx, fy, fw, fh) in faces_rects:
            face_roi = gray_snap[fy:fy+fh, fx:fx+fw]
            face_resized = cv2.resize(face_roi, (200,200))
            if len(label_map) > 0:
                label, conf = recognizer.predict(face_resized)
                # LBPH: smaller confidence means better match
                if conf < CONFIDENCE_THRESHOLD and label in label_map:
                    name = label_map[label]
                    recognized.append(f"{name} ({conf:.1f})")
                else:
                    recognized.append(f"Unknown ({conf:.1f})")
            else:
                recognized.append("Unknown (no model)")
            # annotate the frame (visual)
            cv2.rectangle(frame, (fx, fy), (fx+fw, fy+fh), (255, 0, 0), 2)
            cv2.putText(frame, recognized[-1], (fx, fy-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,0,0), 1)

        # Save an annotated face snapshot
        face_snapshot_name = os.path.join(FACE_SNAPSHOT_DIR, f"{timestamp}_faces.jpg")
        cv2.imwrite(face_snapshot_name, frame)

        log_event(timestamp, video_filename, snapshot_filename, recognized)

        print(f"🎥 Recording started: {video_filename}")
        print(f"📸 Snapshot saved: {snapshot_filename}")
        print(f"📌 Face snapshot saved: {face_snapshot_name}")
        print(f"📝 Logged event at {timestamp} recognized: {recognized}")

    # Stop recording if timeout passed
    elif recording and last_motion_time is not None:
        if time.time() - last_motion_time > MOTION_TIMEOUT:
            recording = False
            out.release()
            out = None
            print("🛑 Recording stopped (no motion)")

    if recording and out is not None:
        out.write(frame)

    previous_frame = gray_blur

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
if out is not None:
    out.release()
cv2.destroyAllWindows()

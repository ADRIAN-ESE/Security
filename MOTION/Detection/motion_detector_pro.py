"""
motion_detector_pro.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Multi-camera motion detector with:
  • YOLOv8 person / object detection
  • Email + SMS (Twilio) alerts with snapshot attachments
  • Automatic night-mode (CLAHE low-light enhancement)
  • Per-camera threads — all cameras run simultaneously
  • config.ini driven — never edit this file

Usage:
    python motion_detector_pro.py
    python motion_detector_pro.py --config my_config.ini
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import cv2
import datetime
import os
import time
import shutil
import csv
import signal
import sys
import argparse
import threading
import smtplib
import configparser
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage

# ── Optional dependencies ─────────────────────────────────────
try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False

try:
    from twilio.rest import Client as TwilioClient
    TWILIO_AVAILABLE = True
except ImportError:
    TWILIO_AVAILABLE = False


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  LOGGING
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler("motion_detector.log"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger(__name__)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  CONFIG
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CONFIG_FILE = "config.ini"

DEFAULT_CONFIG = {
    "cameras": {
        # Comma-separated list. Use 0,1,2 for webcams or rtsp://... URLs.
        "sources":       "0",
        "frame_width":   "640",
        "frame_height":  "480",
        "fps":           "20",
    },
    "detection": {
        "motion_threshold":        "25",    # pixel-diff sensitivity (lower=more sensitive)
        "min_contour_area":        "1000",  # ignore blobs smaller than this
        "motion_timeout":          "5",     # seconds of silence before stopping clip
        "min_record_secs":         "3",     # minimum clip length
        # YOLO
        "yolo_enabled":            "true",
        "yolo_model":              "yolov8n.pt",       # n=nano(fastest) s/m/l/x=larger
        "yolo_confidence":         "0.45",
        "yolo_targets":            "person,car,dog",   # only alert for these classes
        # Night mode
        "night_mode_auto":         "true",
        "night_brightness_threshold": "60",            # mean brightness below this = night
    },
    "storage": {
        "recordings_dir":     "recordings",
        "snapshots_dir":      "snapshots",
        "log_file":           "motion_log.csv",
        "retention_days":     "7",
        "show_threshold_win": "false",
    },
    "alerts": {
        "alert_cooldown_secs": "60",   # min gap between alerts per camera
        # Email
        "email_enabled":   "false",
        "email_host":      "smtp.gmail.com",
        "email_port":      "587",
        "email_user":      "",         # your Gmail address
        "email_password":  "",         # Gmail App Password (not your login password)
        "email_to":        "",         # recipient address
        # SMS (Twilio)
        "sms_enabled":     "false",
        "twilio_sid":      "",
        "twilio_token":    "",
        "twilio_from":     "",         # your Twilio phone number  e.g. +15551234567
        "sms_to":          "",         # destination phone number  e.g. +447911123456
    },
}


def load_config(path=CONFIG_FILE):
    cfg = configparser.ConfigParser()
    for section, values in DEFAULT_CONFIG.items():
        cfg[section] = values

    if os.path.exists(path):
        cfg.read(path)
        log.info(f"Config loaded from {path}")
    else:
        with open(path, "w") as f:
            cfg.write(f)
        log.info(f"Default config written to {path} — edit it to enable alerts.")
    return cfg


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  STORAGE HELPERS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def ensure_dirs(cfg):
    os.makedirs(cfg["storage"]["recordings_dir"], exist_ok=True)
    os.makedirs(cfg["storage"]["snapshots_dir"],  exist_ok=True)


def init_csv(cfg):
    path = cfg["storage"]["log_file"]
    if not os.path.exists(path):
        with open(path, "w", newline="") as f:
            csv.writer(f).writerow([
                "Timestamp", "Camera", "Duration (s)",
                "Objects Detected", "Video File", "Snapshot File",
            ])


def append_csv(cfg, ts, cam_id, duration, objects, video, snapshot):
    with open(cfg["storage"]["log_file"], "a", newline="") as f:
        csv.writer(f).writerow([
            ts, cam_id, f"{duration:.1f}",
            ", ".join(objects) if objects else "motion only",
            video, snapshot,
        ])


def daily_folder(base_dir):
    folder = os.path.join(base_dir, datetime.datetime.now().strftime("%Y-%m-%d"))
    os.makedirs(folder, exist_ok=True)
    return folder


def cleanup_old(base_dir, days):
    if not os.path.isdir(base_dir):
        return
    now = datetime.datetime.now()
    for entry in os.listdir(base_dir):
        path = os.path.join(base_dir, entry)
        try:
            age = (now - datetime.datetime.strptime(entry, "%Y-%m-%d")).days
            if age > days:
                shutil.rmtree(path)
                log.info(f"Deleted old folder: {path}")
        except ValueError:
            pass


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  NIGHT MODE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
_clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))


def is_dark(gray_frame, threshold):
    return float(gray_frame.mean()) < threshold


def enhance_night(gray_frame):
    """Apply CLAHE contrast enhancement to a dark grayscale frame."""
    return _clahe.apply(gray_frame)


def brighten_color(frame):
    """Brighten the colour frame for on-screen display in low light."""
    return cv2.convertScaleAbs(frame, alpha=1.5, beta=40)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  YOLO  (shared model, thread-safe)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
_yolo_model = None
_yolo_lock  = threading.Lock()


def load_yolo(model_path):
    global _yolo_model
    if not YOLO_AVAILABLE:
        log.warning("ultralytics not installed — YOLO disabled.  pip install ultralytics")
        return
    try:
        log.info(f"Loading YOLO model: {model_path} ...")
        _yolo_model = YOLO(model_path)
        # Warm-up pass on a blank frame so first real inference isn't slow
        _yolo_model(
            __import__("numpy").zeros((480, 640, 3), dtype="uint8"),
            verbose=False,
        )
        log.info("✅ YOLO ready.")
    except Exception as exc:
        log.warning(f"YOLO load failed: {exc}")


def run_yolo(frame, confidence, targets):
    """
    Detect objects in *frame* and draw boxes for targeted classes.
    Returns list of detected class names (may contain duplicates for counts).
    """
    if _yolo_model is None:
        return []

    with _yolo_lock:
        results = _yolo_model(frame, conf=confidence, verbose=False)[0]

    detected = []
    for box in results.boxes:
        cls_name = results.names[int(box.cls)].lower()
        if cls_name not in targets:
            continue
        detected.append(cls_name)
        x1, y1, x2, y2 = map(int, box.xyxy[0])
        label = f"{cls_name} {float(box.conf):.0%}"
        cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 100, 0), 2)
        cv2.putText(frame, label, (x1, max(y1 - 6, 14)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 100, 0), 2)
    return detected


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  ALERTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
_alert_lock  = threading.Lock()
_last_alerts = {}   # cam_id -> epoch of last alert


def _alert_allowed(cam_id, cooldown):
    with _alert_lock:
        if time.time() - _last_alerts.get(cam_id, 0) >= cooldown:
            _last_alerts[cam_id] = time.time()
            return True
        return False


def _send_email(cfg, cam_id, objects, snapshot_path):
    a = cfg["alerts"]
    try:
        msg           = MIMEMultipart()
        msg["Subject"] = f"🚨 Motion Alert — Camera {cam_id}"
        msg["From"]    = a["email_user"]
        msg["To"]      = a["email_to"]

        body = (
            f"Motion detected on Camera {cam_id}\n"
            f"Time   : {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"Objects: {', '.join(objects) if objects else 'general motion'}\n"
        )
        msg.attach(MIMEText(body, "plain"))

        if snapshot_path and os.path.exists(snapshot_path):
            with open(snapshot_path, "rb") as fh:
                img_part = MIMEImage(fh.read(), name=os.path.basename(snapshot_path))
                msg.attach(img_part)

        with smtplib.SMTP(a["email_host"], int(a["email_port"])) as srv:
            srv.ehlo()
            srv.starttls()
            srv.login(a["email_user"], a["email_password"])
            srv.send_message(msg)

        log.info(f"[Cam {cam_id}] 📧 Email sent → {a['email_to']}")
    except Exception as exc:
        log.warning(f"[Cam {cam_id}] Email failed: {exc}")


def _send_sms(cfg, cam_id, objects):
    if not TWILIO_AVAILABLE:
        log.warning("twilio not installed — SMS skipped.  pip install twilio")
        return
    a = cfg["alerts"]
    try:
        client = TwilioClient(a["twilio_sid"], a["twilio_token"])
        body = (
            f"🚨 Cam {cam_id} | "
            f"{datetime.datetime.now().strftime('%H:%M:%S')} | "
            f"{', '.join(objects) if objects else 'motion detected'}"
        )
        client.messages.create(body=body, from_=a["twilio_from"], to=a["sms_to"])
        log.info(f"[Cam {cam_id}] 📱 SMS sent → {a['sms_to']}")
    except Exception as exc:
        log.warning(f"[Cam {cam_id}] SMS failed: {exc}")


def trigger_alerts(cfg, cam_id, objects, snapshot_path):
    """Fire email and/or SMS in background threads (non-blocking)."""
    cooldown = float(cfg["alerts"]["alert_cooldown_secs"])
    if not _alert_allowed(cam_id, cooldown):
        return
    a = cfg["alerts"]
    if a.getboolean("email_enabled"):
        threading.Thread(
            target=_send_email, args=(cfg, cam_id, objects, snapshot_path), daemon=True
        ).start()
    if a.getboolean("sms_enabled"):
        threading.Thread(
            target=_send_sms, args=(cfg, cam_id, objects), daemon=True
        ).start()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  HUD OVERLAY
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def draw_hud(frame, cam_id, recording, motion, objects, rec_elapsed, events, night_mode):
    h, w = frame.shape[:2]

    # Top bar
    cv2.rectangle(frame, (0, 0), (w, 36), (20, 20, 20), -1)

    if recording:
        color = (0, 60, 220)
        label = f"● REC  {rec_elapsed:.0f}s   CAM {cam_id}"
    elif motion:
        color = (0, 140, 255)
        label = f"⚡ Motion   CAM {cam_id}"
    else:
        color = (30, 180, 30)
        label = f"● Monitoring   CAM {cam_id}"

    cv2.putText(frame, label,
                (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.65, color, 2)

    ts = datetime.datetime.now().strftime("%Y-%m-%d  %H:%M:%S")
    cv2.putText(frame, ts,
                (w - 240, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.52, (180, 180, 180), 1)

    # YOLO detections
    if objects:
        unique = sorted(set(objects))
        cv2.putText(frame, f"Detected: {', '.join(unique)}",
                    (10, 58), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (80, 180, 255), 2)

    # Bottom bar
    footer = f"Events: {events}"
    if night_mode:
        footer += "   🌙 Night Mode"
    cv2.putText(frame, footer,
                (10, h - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (160, 160, 160), 1)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  CAMERA THREAD
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class CameraThread(threading.Thread):
    """One thread per camera — runs the full detect → record → alert pipeline."""

    def __init__(self, cam_id, source, cfg, stop_event):
        super().__init__(daemon=True, name=f"Cam-{cam_id}")
        self.cam_id     = cam_id
        self.source     = source
        self.cfg        = cfg
        self.stop_event = stop_event

        d = cfg["detection"]
        s = cfg["storage"]
        c = cfg["cameras"]

        self.width       = int(c["frame_width"])
        self.height      = int(c["frame_height"])
        self.fps         = float(c["fps"])
        self.threshold   = int(d["motion_threshold"])
        self.min_area    = int(d["min_contour_area"])
        self.timeout     = float(d["motion_timeout"])
        self.min_rec     = float(d["min_record_secs"])
        self.yolo_on     = d.getboolean("yolo_enabled") and YOLO_AVAILABLE
        self.yolo_conf   = float(d["yolo_confidence"])
        self.yolo_tgts   = {t.strip().lower() for t in d["yolo_targets"].split(",")}
        self.night_auto  = d.getboolean("night_mode_auto")
        self.night_thr   = float(d["night_brightness_threshold"])
        self.rec_dir     = s["recordings_dir"]
        self.snap_dir    = s["snapshots_dir"]
        self.retention   = int(s["retention_days"])
        self.show_mask   = s.getboolean("show_threshold_win")

    # ── helpers ──────────────────────────────────────────────
    def _open_camera(self):
        try:
            src = int(self.source)          # webcam index
        except ValueError:
            src = self.source               # URL / path

        cap = cv2.VideoCapture(src)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH,  self.width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        return cap

    # ── main loop ────────────────────────────────────────────
    def run(self):
        cap = self._open_camera()
        if not cap.isOpened():
            log.error(f"[Cam {self.cam_id}] Cannot open source '{self.source}'. Exiting thread.")
            return

        log.info(f"[Cam {self.cam_id}] Started — source: {self.source}")

        bg_sub = cv2.createBackgroundSubtractorMOG2(
            history=500, varThreshold=self.threshold, detectShadows=False
        )

        prev_gray      = None
        recording      = False
        writer         = None
        last_motion_t  = None
        rec_start_t    = None
        rec_ts         = None
        rec_vid        = None
        rec_snap       = None
        last_objects   = []
        event_count    = 0

        while not self.stop_event.is_set():
            ret, frame = cap.read()
            if not ret:
                log.warning(f"[Cam {self.cam_id}] Frame grab failed — retrying...")
                time.sleep(0.1)
                continue

            # ── Pre-process ──────────────────────────────────
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray = cv2.GaussianBlur(gray, (21, 21), 0)

            night = self.night_auto and is_dark(gray, self.night_thr)
            if night:
                gray  = enhance_night(gray)
                frame = brighten_color(frame)

            # ── Motion detection ─────────────────────────────
            fg_mask = bg_sub.apply(gray)
            fg_mask = cv2.dilate(fg_mask, None, iterations=2)

            if prev_gray is not None:
                diff   = cv2.absdiff(prev_gray, gray)
                thresh = cv2.threshold(diff, self.threshold, 255, cv2.THRESH_BINARY)[1]
                thresh = cv2.dilate(thresh, None, iterations=2)
                mask   = cv2.bitwise_or(fg_mask, thresh)
            else:
                mask = fg_mask

            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            motion = False
            for cnt in contours:
                if cv2.contourArea(cnt) < self.min_area:
                    continue
                motion       = True
                last_motion_t = time.time()
                x, y, w, h   = cv2.boundingRect(cnt)
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

            # ── YOLO ─────────────────────────────────────────
            yolo_hits = []
            if motion and self.yolo_on:
                yolo_hits = run_yolo(frame, self.yolo_conf, self.yolo_tgts)
                if yolo_hits:
                    last_objects = yolo_hits

            rec_elapsed = (time.time() - rec_start_t) if rec_start_t else 0.0

            # ── Recording FSM ────────────────────────────────
            if motion and not recording:
                event_count += 1
                rec_ts   = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                rec_vid  = os.path.join(
                    daily_folder(self.rec_dir), f"cam{self.cam_id}_{rec_ts}.avi"
                )
                rec_snap = os.path.join(
                    daily_folder(self.snap_dir), f"cam{self.cam_id}_{rec_ts}.jpg"
                )
                fourcc  = cv2.VideoWriter_fourcc(*"XVID")
                writer  = cv2.VideoWriter(
                    rec_vid, fourcc, self.fps, (frame.shape[1], frame.shape[0])
                )
                recording    = True
                rec_start_t  = time.time()
                cv2.imwrite(rec_snap, frame)
                log.info(f"[Cam {self.cam_id}] 🎥 Recording → {rec_vid}")
                log.info(f"[Cam {self.cam_id}] 📸 Snapshot  → {rec_snap}")
                trigger_alerts(self.cfg, self.cam_id, yolo_hits, rec_snap)

            elif recording:
                since_motion = time.time() - (last_motion_t or rec_start_t)
                if not motion and since_motion > self.timeout and rec_elapsed >= self.min_rec:
                    duration = time.time() - rec_start_t
                    recording = False
                    writer.release()
                    writer = None
                    append_csv(
                        self.cfg, rec_ts, self.cam_id,
                        duration, last_objects, rec_vid, rec_snap
                    )
                    log.info(f"[Cam {self.cam_id}] 🛑 Stopped ({duration:.1f}s) — "
                             f"objects: {last_objects or 'motion only'}")
                    last_objects = []
                    rec_start_t  = None

            if recording and writer:
                writer.write(frame)

            # ── HUD & display ────────────────────────────────
            draw_hud(frame, self.cam_id, recording, motion,
                     last_objects, rec_elapsed, event_count, night)

            cv2.imshow(f"Camera {self.cam_id}", frame)
            if self.show_mask:
                cv2.imshow(f"Mask {self.cam_id}", mask)

            prev_gray = gray

            # 'q' in any window signals global shutdown
            if cv2.waitKey(1) & 0xFF == ord("q"):
                self.stop_event.set()
                break

        # ── Cleanup ──────────────────────────────────────────
        cap.release()
        if writer:
            writer.release()
        log.info(f"[Cam {self.cam_id}] Thread stopped.")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  MAIN
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def main():
    parser = argparse.ArgumentParser(description="Motion Detector Pro")
    parser.add_argument("--config", default=CONFIG_FILE,
                        help="Path to config.ini (default: config.ini)")
    args = parser.parse_args()

    cfg = load_config(args.config)
    ensure_dirs(cfg)
    init_csv(cfg)

    ret_days = int(cfg["storage"]["retention_days"])
    cleanup_old(cfg["storage"]["recordings_dir"], ret_days)
    cleanup_old(cfg["storage"]["snapshots_dir"],  ret_days)

    # Log dependency status
    if not YOLO_AVAILABLE:
        log.warning("ultralytics missing → YOLO disabled.  pip install ultralytics")
    if not TWILIO_AVAILABLE:
        log.warning("twilio missing → SMS disabled.  pip install twilio")

    # Load YOLO once (shared across all camera threads)
    if cfg["detection"].getboolean("yolo_enabled"):
        load_yolo(cfg["detection"]["yolo_model"])

    sources   = [s.strip() for s in cfg["cameras"]["sources"].split(",")]
    stop_evt  = threading.Event()

    def shutdown(sig=None, frame=None):
        log.info("Shutdown signal received — stopping all cameras...")
        stop_evt.set()

    signal.signal(signal.SIGINT,  shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    threads = []
    for i, src in enumerate(sources):
        t = CameraThread(cam_id=i, source=src, cfg=cfg, stop_event=stop_evt)
        t.start()
        threads.append(t)

    log.info(
        f"✅ {len(threads)} camera(s) running.  "
        f"Press 'q' in any window or Ctrl-C to quit."
    )

    for t in threads:
        t.join()

    cv2.destroyAllWindows()
    log.info("All done. Goodbye.")


if __name__ == "__main__":
    main()

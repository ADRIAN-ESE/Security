# 🎥 Motion Detector Pro

A production-grade, multi-camera security system with AI-powered object detection, real-time alerts, automatic night mode, and a fully config-driven setup.

---

## Features

| Feature | Details |
|---------|---------|
| **Multi-camera** | Run any number of webcams or RTSP streams simultaneously, each in its own thread |
| **YOLOv8 detection** | Identifies people, cars, dogs (or any COCO class) — alerts only fire on real targets, not shadows |
| **Email alerts** | Sends a snapshot-attached email the moment a target is detected |
| **SMS alerts** | Instant Twilio SMS with camera ID, time, and detected objects |
| **Night mode** | Auto-detects dark frames and applies CLAHE enhancement — works in low light without IR hardware |
| **MOG2 + frame-diff** | Dual-engine motion detection for reliability across fast and slow cameras |
| **Per-camera CSV log** | Every event logged with timestamp, duration, objects, and file paths |
| **Daily folders** | Recordings and snapshots organised automatically into `YYYY-MM-DD` subdirectories |
| **Auto-cleanup** | Folders older than `retention_days` deleted on startup |
| **config.ini driven** | All settings in one file — never edit the script |
| **Clean shutdown** | Ctrl-C or `q` safely stops all threads, flushes writers, closes windows |

---

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run (generates config.ini on first run)
python motion_detector_pro.py

# 3. Edit config.ini to enable alerts, add cameras, tune detection
# 4. Run again
python motion_detector_pro.py
```

> **YOLO model** (~6 MB) downloads automatically on first run.

---

## Requirements

- Python 3.8+
- A webcam, USB camera, or RTSP stream

```bash
pip install -r requirements.txt
```

| Package | Purpose |
|---------|---------|
| `opencv-python` | Camera capture, motion detection, display |
| `ultralytics` | YOLOv8 object detection |
| `twilio` | SMS alerts (optional) |

---

## Configuration (`config.ini`)

Generated automatically on first run. All settings are here — never edit the Python file.

### `[cameras]`

| Key | Default | Description |
|-----|---------|-------------|
| `sources` | `0` | Comma-separated camera sources. Use `0,1` for two webcams, or `rtsp://user:pass@192.168.1.10/stream` for IP cameras |
| `frame_width` | `640` | Capture width |
| `frame_height` | `480` | Capture height |
| `fps` | `20` | Recording frame rate |

### `[detection]`

| Key | Default | Description |
|-----|---------|-------------|
| `motion_threshold` | `25` | Pixel-difference sensitivity. Lower = more sensitive |
| `min_contour_area` | `1000` | Minimum blob size to count as motion |
| `motion_timeout` | `5` | Seconds of no-motion before a clip stops |
| `min_record_secs` | `3` | Minimum clip length |
| `yolo_enabled` | `true` | Enable YOLOv8 object detection |
| `yolo_model` | `yolov8n.pt` | Model size: `n` (fastest) → `s` → `m` → `l` → `x` (most accurate) |
| `yolo_confidence` | `0.45` | Minimum confidence to count a detection |
| `yolo_targets` | `person,car,dog` | COCO classes to watch for |
| `night_mode_auto` | `true` | Auto-enable CLAHE enhancement on dark frames |
| `night_brightness_threshold` | `60` | Mean brightness (0–255) below which night mode activates |

### `[storage]`

| Key | Default | Description |
|-----|---------|-------------|
| `recordings_dir` | `recordings` | Root folder for video clips |
| `snapshots_dir` | `snapshots` | Root folder for trigger snapshots |
| `log_file` | `motion_log.csv` | Event log path |
| `retention_days` | `7` | Days before old folders are deleted |
| `show_threshold_win` | `false` | Show binary motion-mask window (useful when tuning) |

### `[alerts]`

| Key | Default | Description |
|-----|---------|-------------|
| `alert_cooldown_secs` | `60` | Minimum gap between alerts per camera |
| `email_enabled` | `false` | Enable email alerts |
| `email_host` | `smtp.gmail.com` | SMTP server |
| `email_port` | `587` | SMTP port (587 = STARTTLS) |
| `email_user` | _(empty)_ | Sending address |
| `email_password` | _(empty)_ | App password (Gmail: Settings → Security → App Passwords) |
| `email_to` | _(empty)_ | Recipient address |
| `sms_enabled` | `false` | Enable Twilio SMS |
| `twilio_sid` | _(empty)_ | Twilio Account SID |
| `twilio_token` | _(empty)_ | Twilio Auth Token |
| `twilio_from` | _(empty)_ | Your Twilio phone number e.g. `+15551234567` |
| `sms_to` | _(empty)_ | Recipient phone number e.g. `+447911123456` |

---

## Setting Up Alerts

### Email (Gmail)

1. Enable 2-Step Verification on your Google account
2. Go to **Google Account → Security → App Passwords**
3. Create a password for "Mail"
4. Paste the 16-character password into `email_password` in `config.ini`
5. Set `email_enabled = true`

> Works with any SMTP provider — change `email_host` and `email_port` accordingly.

### SMS (Twilio)

1. Sign up at [twilio.com](https://twilio.com) (free trial includes test credits)
2. Copy your **Account SID** and **Auth Token** from the dashboard
3. Get a Twilio phone number
4. Fill in `twilio_sid`, `twilio_token`, `twilio_from`, `sms_to`
5. Set `sms_enabled = true`

---

## Multi-Camera Setup

```ini
[cameras]
sources = 0,1,2
```

```ini
# Two webcams + one IP camera
sources = 0,1,rtsp://admin:password@192.168.1.10/h264Preview_01_main
```

Each source spawns its own thread and window (`Camera 0`, `Camera 1`, …). Recordings are prefixed with `cam0_`, `cam1_`, etc.

---

## Night Mode

Activates automatically when mean frame brightness drops below `night_brightness_threshold`. Applies CLAHE to the grayscale detection frame and brightens the colour display window. No extra hardware required.

```ini
[detection]
night_mode_auto = true
night_brightness_threshold = 60   ; increase to trigger sooner
```

---

## YOLO Model Sizes

| Model | Size | Speed | Accuracy | Best for |
|-------|------|-------|----------|---------|
| `yolov8n.pt` | 6 MB | ⚡⚡⚡⚡ | ★★☆☆ | Raspberry Pi, low-end hardware |
| `yolov8s.pt` | 22 MB | ⚡⚡⚡ | ★★★☆ | Most laptops |
| `yolov8m.pt` | 50 MB | ⚡⚡ | ★★★★ | Dedicated GPU |
| `yolov8l.pt` | 84 MB | ⚡ | ★★★★★ | Server / workstation |

---

## Output Structure

```
project/
├── motion_detector_pro.py
├── config.ini
├── requirements.txt
├── motion_detector.log
├── motion_log.csv
├── recordings/
│   └── 2025-06-01/
│       ├── cam0_2025-06-01_14-32-10.avi
│       └── cam1_2025-06-01_14-33-05.avi
└── snapshots/
    └── 2025-06-01/
        ├── cam0_2025-06-01_14-32-10.jpg
        └── cam1_2025-06-01_14-33-05.jpg
```

### motion_log.csv columns

| Column | Description |
|--------|-------------|
| Timestamp | Event start date/time |
| Camera | Camera ID |
| Duration (s) | Clip length in seconds |
| Objects Detected | YOLO classes found, or "motion only" |
| Video File | Path to `.avi` clip |
| Snapshot File | Path to `.jpg` snapshot |

---

## How It Works

```
Camera N (thread)
      │
      ▼
  Grayscale + Gaussian Blur
      │
      ├─── Dark frame? ──► CLAHE night enhancement
      │
      ├──► MOG2 background subtractor ──┐
      │                                  ├──► OR mask ──► Contours ──► Motion?
      └──► Frame diff + threshold ───────┘
                                                │
                                    ┌───────────┴───────────┐
                                   YES                       NO
                                    │                        │
                              Run YOLO                 Check timeout
                              Draw boxes               Stop clip if due
                                    │                  Log to CSV
                              Start recording
                              Save snapshot
                              Trigger alerts ──► Email thread
                                               └──► SMS thread
```

---

## Tuning Tips

- **Too many false alerts** → raise `min_contour_area` or `motion_threshold`; narrow `yolo_targets`
- **Missing real motion** → lower `motion_threshold`; lower `yolo_confidence`
- **Night mode too aggressive** → lower `night_brightness_threshold`
- **Clips too short** → raise `min_record_secs` or `motion_timeout`
- **Alert spam** → raise `alert_cooldown_secs`
- **Slow on CPU** → use `yolov8n.pt`; reduce resolution; set `yolo_enabled = false` if not needed

---

## File History

| File | Description |
|------|-------------|
| `Motion_1.py` | Original — basic detection |
| `motion1.py` | Added recording + snapshots |
| `Motion_detection.py` | Added timeout, daily folders, CSV, cleanup |
| `motion_detector.py` | Unified v1 — MOG2, SIGINT, improved HUD |
| **`motion_detector_pro.py`** | **This file — YOLO, alerts, night mode, multi-camera** |

---

## License

MIT — free to use, modify, and distribute.

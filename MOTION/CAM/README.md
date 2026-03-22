# 🎥 Motion Detector

A Python-based security camera system that detects motion, records video clips, saves snapshots, sends email alerts, and logs all events — all from a single script.

---

## Features

- **Dual-engine detection** — combines MOG2 adaptive background subtraction with classic frame-differencing for reliable, low false-positive detection
- **Auto-recording** — starts recording on motion and stops after a configurable timeout
- **Snapshot on trigger** — saves a JPEG at the moment motion is first detected
- **Email alerts** — sends an email with the snapshot attached the moment motion is detected; runs in a background thread so it never stalls the camera loop
- **Cooldown timer** — enforces a quiet period after each recording ends, preventing alert and recording spam
- **CSV event log** — every event is logged with timestamp, duration, and file paths
- **Daily folders** — recordings and snapshots are organised into `YYYY-MM-DD` subfolders automatically
- **Auto-cleanup** — folders older than a configurable number of days are deleted on startup
- **Live overlay** — on-screen status badge, timestamp, recording timer, cooldown countdown, and event counter
- **Motion mask window** — optional binary diff preview for tuning sensitivity
- **Clean shutdown** — Ctrl-C safely releases the camera and closes any open video file

---

## Requirements

- Python 3.7+
- OpenCV

Install dependencies:

```bash
pip install opencv-python
```

> No third-party libraries are needed for email — it uses Python's built-in `smtplib`.

---

## Usage

```bash
python motion_detector.py
```

| Key | Action |
|-----|--------|
| `q` | Quit cleanly |
| Ctrl-C | Quit cleanly (terminal) |

---

## Output Structure

```
project/
├── motion_detector.py
├── motion_log.csv
├── recordings/
│   └── 2025-06-01/
│       └── 2025-06-01_14-32-10.avi
└── snapshots/
    └── 2025-06-01/
        └── 2025-06-01_14-32-10.jpg
```

### motion_log.csv columns

| Column | Description |
|--------|-------------|
| Timestamp | Date and time the event started |
| Duration (s) | Length of the recorded clip in seconds |
| Video File | Path to the `.avi` recording |
| Snapshot File | Path to the `.jpg` snapshot |

---

## Configuration

All settings are in the `SETTINGS` block at the top of `motion_detector.py`. No other changes are needed.

### Detection & Recording

| Setting | Default | Description |
|---------|---------|-------------|
| `CAMERA_INDEX` | `0` | Camera to use (0 = default webcam) |
| `FRAME_WIDTH` | `640` | Capture width in pixels |
| `FRAME_HEIGHT` | `480` | Capture height in pixels |
| `FPS` | `20.0` | Recording frame rate |
| `MOTION_THRESHOLD` | `25` | Pixel-difference sensitivity — lower = more sensitive |
| `MIN_CONTOUR_AREA` | `1000` | Minimum blob size to count as motion (filters noise) |
| `MOTION_TIMEOUT` | `5` | Seconds of no-motion before stopping a recording |
| `MIN_RECORD_SECS` | `3` | Minimum clip length in seconds |
| `COOLDOWN_SECS` | `30` | Seconds to wait after a recording ends before a new one can start |
| `RETENTION_DAYS` | `7` | Days before old recordings/snapshots are auto-deleted |
| `SHOW_THRESHOLD_WIN` | `True` | Show the binary motion mask window |

### Email Alerts

| Setting | Description |
|---------|-------------|
| `EMAIL_ENABLED` | Set `False` to disable all email alerts |
| `EMAIL_SENDER` | The Gmail address alerts are sent from |
| `EMAIL_PASSWORD` | App Password for the sender account (see below) |
| `EMAIL_RECIPIENT` | Address that receives the alerts |
| `EMAIL_SUBJECT` | Subject line of the alert email |
| `SMTP_HOST` | SMTP server (default: `smtp.gmail.com`) |
| `SMTP_PORT` | SMTP port (default: `587`) |

### Setting up Gmail alerts

1. Enable **2-Step Verification** on your Google account
2. Go to **Google Account → Security → App Passwords**
3. Generate a new App Password for *Mail*
4. Paste it into `EMAIL_PASSWORD` — do **not** use your regular account password

For other email providers, update `SMTP_HOST` and `SMTP_PORT` accordingly (e.g. Outlook uses `smtp.office365.com`, port `587`).

### Tuning tips

- **Too many false triggers** (shadows, lighting changes) → increase `MOTION_THRESHOLD` or `MIN_CONTOUR_AREA`
- **Missing real motion** → decrease `MOTION_THRESHOLD`
- **Clips cut off too early** → increase `MOTION_TIMEOUT` or `MIN_RECORD_SECS`
- **Too many emails** → increase `COOLDOWN_SECS`
- **Using a USB or IP camera** → change `CAMERA_INDEX` to `1`, `2`, or the stream URL

---

## How It Works

```
Camera frame
     │
     ▼
Grayscale + Gaussian Blur
     │
     ├──► MOG2 Background Subtractor ──┐
     │                                  ├──► OR combined mask
     └──► Frame Difference + Threshold ─┘
                    │
                    ▼
           Find Contours (filter by area)
                    │
          ┌─────────┴──────────┐
          │ Motion detected?   │
          │                    │
         YES                   NO
          │                    │
   On cooldown?          Check timeout
          │                    │
         YES    NO        Stop if expired
          │      │             │
       Ignore  Start       Log duration
               recording
               Save snapshot
               Send email alert (async)
               Start cooldown on stop
```

---

## File History

| File | Description |
|------|-------------|
| `Motion_1.py` | Original — basic detection and threshold display |
| `motion1.py` | Added recording and snapshots |
| `Motion_detection.py` | Added timeout buffer, daily folders, CSV logging, cleanup |
| `motion_detector.py` | **This file** — unified version with cooldown timer and email alerts |

---

## License

MIT — free to use, modify, and distribute.

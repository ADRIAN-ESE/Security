# SysInfo & Geolocation Extractor — GUI Edition

A cybersecurity recon desktop app built with Python + Tkinter.

---

## Features

| Tab | What it does |
|-----|-------------|
| **📊 Dashboard** | System, CPU, RAM, Disk, Network info. Live CPU/RAM spark-line charts with 1-second refresh. |
| **🔍 Scanner** | Ping sweep across any subnet. Port scanner with risk annotations on common services. |
| **🌍 Geo / Map** | IP geolocation with proxy/hosting detection. Interactive map via `tkintermapview`. |
| **📋 History** | Stores up to 20 scans as JSON. Side-by-side comparison with changed fields highlighted. |

**Exports:** HTML (dark-themed), CSV, PDF (via reportlab)

---

## Project Structure

```
sysinfo_tool/
├── main.py          ← Run this
├── app.py           ← Tkinter GUI (4 tabs + header + status bar)
├── collectors.py    ← System/geo data collectors
├── scanner.py       ← Ping sweep & port scanner
├── exporters.py     ← HTML / CSV / PDF export
├── history.py       ← Scan history (JSON) & comparison
├── requirements.txt
└── scan_history.json  (auto-created on first scan)
```

---

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

For the interactive map tab:
```bash
pip install tkintermapview
```

For PDF export:
```bash
pip install reportlab
```

### 2. Run

```bash
python main.py
```

---

## IDE Configuration

### PyCharm
1. **File → Open** → select the `sysinfo_tool/` folder
2. **File → Settings → Project → Python Interpreter → + → install** `psutil`, `requests`, `reportlab`, `tkintermapview`
3. Right-click `main.py` → **Run 'main'**

### VSCode
1. Open folder in VSCode
2. Select interpreter: `Ctrl+Shift+P` → *Python: Select Interpreter*
3. Open terminal (`` Ctrl+` ``): `pip install -r requirements.txt`
4. Open `main.py` → press **F5** or **▶ Run**

---

## Usage Guide

### Run Full Scan
Click **▶ Run Full Scan** in the header. Collects all system data + geolocation and saves to history.

### Ping Sweep
1. Go to 🔍 Scanner tab
2. Set subnet (auto-detected from your local network)
3. Click **▶ Ping Sweep**
4. Select an alive host → click **⚡ Scan Ports on Selected Host**

### Custom Port Range
Enter comma-separated ports in the "Custom ports" field before scanning, e.g.:
```
80, 443, 8080, 8443, 22, 3306
```

### Compare Scans
1. Go to 📋 History tab → click 🔃 Refresh
2. Ctrl+click two scans
3. Click **⚖ Compare Selected (2)**
4. Yellow rows = changed values

### Export
Click **⬇ Export ▾** in the header → choose HTML / CSV / PDF.

---

## Security Notes

- **Geolocation** uses `ip-api.com` (free, no API key, rate-limited to 45 req/min)
- **Proxy/VPN detection** is ISP-level, not foolproof
- **Port scan** uses TCP connect — detected by firewalls/IDS
- Only scan networks **you own or have permission to scan**

---

## Dependencies

| Library | Purpose | Required |
|---------|---------|---------|
| `psutil` | CPU, RAM, disk, network | ✅ Yes |
| `requests` | Geolocation API | ✅ Yes |
| `reportlab` | PDF export | ⚠ For PDF only |
| `tkintermapview` | Interactive map | ⚠ For map only |
| `tkinter` | GUI (built into Python) | ✅ Yes |

---

## Disclaimer
For educational purposes only. Only use on systems you own or have explicit permission to audit.

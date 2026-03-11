# System Info & Geolocation Extractor

A cybersecurity recon tool that collects detailed system and network intelligence, then maps the machine's public IP to a geolocation.

---

## Features

| Category         | Data Collected                                                  |
|------------------|-----------------------------------------------------------------|
| **System**       | Hostname, OS, architecture, processor, user, MAC, boot time    |
| **CPU**          | Physical/logical cores, frequency, real-time usage             |
| **Memory**       | Total, used, available RAM, usage %                            |
| **Disk**         | All partitions, filesystem type, used/free space               |
| **Network**      | All interfaces, IP addresses (v4+v6), MAC, up/down status      |
| **Geolocation**  | Public IP, country, region, city, coordinates, ISP, ASN        |
| **Threat Flags** | Proxy/VPN detection, hosting/datacenter detection              |

---

## Setup

### 1. Clone or copy the files

```
system_info_extractor.py
requirements.txt
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Run

```bash
python system_info_extractor.py
```

---

## IDE Setup

### PyCharm
1. Open the folder as a project
2. Go to **File → Settings → Project → Python Interpreter**
3. Click **+** and install `psutil`, `requests`, `rich`
4. Run with the green ▶ button

### VSCode
1. Open the folder
2. Select Python interpreter: `Ctrl+Shift+P` → *Python: Select Interpreter*
3. Open terminal: `` Ctrl+` ``
4. Run `pip install -r requirements.txt`
5. Run with `F5` or `python system_info_extractor.py`

---

## Export to JSON

Uncomment the last line in `__main__` to save a full JSON report:

```python
export_json(report)           # saves to system_report.json
export_json(report, "out.json")  # custom filename
```

---

## Dependencies

| Library    | Purpose                        | Required? |
|------------|--------------------------------|-----------|
| `psutil`   | CPU, RAM, disk, network stats  | Yes       |
| `requests` | HTTP call to geolocation API   | Yes       |
| `rich`     | Colourful terminal output      | Optional  |

> Without `rich`, the tool falls back to a plain-text display.  
> Without `requests`, geolocation is skipped gracefully.

---

## Geolocation API

Uses [ip-api.com](http://ip-api.com) — **free**, no API key needed.  
Rate limit: 45 requests/minute from one IP.

---

## Cybersecurity Learning Points

- **MAC address exposure** — why spoofing matters
- **IP geolocation accuracy** — ISP-level, not street-level
- **Proxy/VPN detection** — how services flag anonymized traffic
- **ASN (Autonomous System Number)** — backbone of internet routing
- **Network interface enumeration** — used in pentesting recon phases

---

## Disclaimer

This tool is for **educational purposes only**.  
Only run it on systems you own or have explicit permission to audit.

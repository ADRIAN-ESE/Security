# Cybersecurity Python Projects

A categorized reference of 26 Python projects for learning and practicing cybersecurity skills.

---

## 🌐 Network

### 1. Port Scanner
**Difficulty:** Beginner
**Description:** Scan a host's open TCP/UDP ports using raw sockets or Scapy. Add banner grabbing and service fingerprinting for extra depth.
**Libraries:** `socket`, `scapy`, `concurrent.futures`

---

### 2. Packet Sniffer
**Difficulty:** Intermediate
**Description:** Capture and dissect live network packets. Parse Ethernet, IP, TCP, UDP, and DNS layers. Export captures to PCAP.
**Libraries:** `scapy`, `socket`, `struct`

---

### 3. DNS Recon Toolkit
**Difficulty:** Beginner
**Description:** Enumerate DNS records (A, MX, NS, TXT), perform zone transfer tests, subdomain brute-force, and WHOIS lookups.
**Libraries:** `dnspython`, `requests`, `python-whois`

---

### 4. ARP Spoofer & Detector
**Difficulty:** Intermediate
**Description:** Send crafted ARP replies to perform a man-in-the-middle attack on a LAN, then build a detector that alerts on ARP cache poisoning.
**Libraries:** `scapy`, `netfilterqueue`

---

### 5. Network Topology Mapper
**Difficulty:** Advanced
**Description:** Combine ICMP probing, ARP scanning, and SNMP queries to auto-discover and map all devices on a subnet.
**Libraries:** `scapy`, `nmap`, `networkx`

---

## 🔐 Cryptography

### 6. Password Cracker
**Difficulty:** Beginner
**Description:** Implement dictionary and brute-force attacks against hashed credentials. Support MD5, SHA-1, SHA-256, and bcrypt.
**Libraries:** `hashlib`, `itertools`, `passlib`

---

### 7. Caesar / Vigenère Cipher
**Difficulty:** Beginner
**Description:** Encode and decode classic substitution ciphers and add frequency analysis to crack them without the key.
**Libraries:** `string`, `collections`

---

### 8. File Encryption Tool
**Difficulty:** Intermediate
**Description:** Encrypt and decrypt files using AES-256 in GCM mode with PBKDF2 key derivation. Optional Fernet symmetric mode.
**Libraries:** `cryptography`, `secrets`, `hashlib`

---

## 🦠 Malware Analysis

### 9. Keylogger
**Difficulty:** Intermediate
**Description:** Capture keystrokes silently, log to file, and optionally email reports. Study detection evasion techniques ethically.
**Libraries:** `pynput`, `smtplib`, `schedule`

---

### 10. Process Injector (Shellcode)
**Difficulty:** Advanced
**Description:** Inject shellcode into a running process using Windows API calls via ctypes. Strictly for lab/educational use.
**Libraries:** `ctypes`, `psutil`, `struct`

---

### 11. Malware Sandbox Detector
**Difficulty:** Advanced
**Description:** Detect VM and sandbox environments by checking hardware fingerprints, timing, registry keys, and process lists.
**Libraries:** `psutil`, `winreg`, `platform`

---

## 🌍 Web Security

### 12. SQLi Scanner
**Difficulty:** Intermediate
**Description:** Crawl a target web app and inject SQL payloads into form fields and URL parameters. Detect error-based and boolean-based SQLi.
**Libraries:** `requests`, `BeautifulSoup4`, `urllib`

---

### 13. XSS Detector
**Difficulty:** Intermediate
**Description:** Inject reflected and stored XSS payloads into forms and headers. Parse responses to confirm script execution.
**Libraries:** `requests`, `BeautifulSoup4`, `selenium`

---

### 14. Web Crawler & Spider
**Difficulty:** Beginner
**Description:** Recursively map all URLs on a site, fingerprint technologies, identify hidden endpoints, and log misconfigurations.
**Libraries:** `requests`, `BeautifulSoup4`, `urllib`

---

### 15. JWT Token Analyzer
**Difficulty:** Intermediate
**Description:** Decode and inspect JWT tokens, test for alg:none attacks, and brute-force weak HMAC secrets.
**Libraries:** `PyJWT`, `requests`, `base64`

---

## 🔎 OSINT

### 16. OSINT Framework Tool
**Difficulty:** Intermediate
**Description:** Aggregate data about a target from Shodan, social media, WHOIS, and DNS. Build a unified threat profile.
**Libraries:** `shodan`, `requests`, `tweepy`

---

### 17. Email Header Analyzer
**Difficulty:** Beginner
**Description:** Parse raw email headers to trace routing hops, flag SPF/DKIM/DMARC failures, and geolocate sending IPs.
**Libraries:** `email`, `requests`, `dnspython`

---

### 18. Metadata Extractor
**Difficulty:** Beginner
**Description:** Strip and report EXIF/metadata from images, PDFs, and Office docs. Reveal author names, GPS coords, and software versions.
**Libraries:** `Pillow`, `exifread`, `PyPDF2`

---

## 🔬 Forensics & SIEM

### 19. Log Anomaly Detector
**Difficulty:** Intermediate
**Description:** Parse web server or syslog files, detect brute-force patterns, privilege escalation events, and port scans.
**Libraries:** `pandas`, `re`, `scikit-learn`

---

### 20. Memory Forensics Tool
**Difficulty:** Advanced
**Description:** Dump and parse process memory from a Windows host. Identify injected code, running malware artifacts, and secrets.
**Libraries:** `volatility3`, `ctypes`, `struct`

---

### 21. Honeypot
**Difficulty:** Intermediate
**Description:** Spin up fake SSH/HTTP services to log and analyze attacker behaviour. Feed events to a local SIEM dashboard.
**Libraries:** `socket`, `paramiko`, `Flask`

---

### 22. Intrusion Detection System
**Difficulty:** Advanced
**Description:** Monitor network traffic in real-time, match against Snort-style rules, and alert on suspicious patterns.
**Libraries:** `scapy`, `pandas`, `pyshark`

---

## ⚙️ Automation

### 23. Vulnerability Scanner
**Difficulty:** Intermediate
**Description:** Automate CVE lookups for installed software versions using the NVD API and generate HTML remediation reports.
**Libraries:** `requests`, `nmap`, `Jinja2`

---

### 24. Password Manager
**Difficulty:** Beginner
**Description:** CLI/GUI vault that stores credentials AES-encrypted with a master password. Auto-generate strong passwords.
**Libraries:** `cryptography`, `sqlite3`, `getpass`

---

### 25. Phishing Email Detector
**Difficulty:** Intermediate
**Description:** Classify email as phishing or legitimate using NLP features (URL patterns, sender spoofing, urgency language) and ML.
**Libraries:** `scikit-learn`, `nltk`, `email`

---

### 26. Reverse Shell Framework
**Difficulty:** Advanced
**Description:** Build a lightweight C2 framework with reverse TCP shell, file transfer, and screenshot capture for red-team labs.
**Libraries:** `socket`, `subprocess`, `threading`

---

## Difficulty Summary

| Level        | Projects |
|--------------|----------|
| Beginner     | 1, 3, 6, 7, 14, 17, 18, 24 |
| Intermediate | 2, 4, 9, 12, 13, 15, 16, 19, 21, 23, 25 |
| Advanced     | 5, 10, 11, 20, 22, 26 |

---

*Note: Projects involving malware simulation (9, 10, 11, 26) are strictly for lab/educational environments. Always obtain proper authorization before testing on any systems you do not own.*

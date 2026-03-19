# CyberSuite

> A browser-based security toolkit providing encryption, phishing analysis, and QR code generation — no server, no backend, entirely client-side.

---

## Project Files

| File | Edition | Description |
|------|---------|-------------|
| `cybersuite_v5.html` | **Primary** | Full-featured flagship edition. Three-tab layout: Cipher Suite, PhishGuard, and QR Studio. |
| `cyberdeck.html` | Alternate | Branded "CyberDeck — Security Suite". Same three modules with a different visual treatment. |
| `cipher_suite.html` | Standalone | Lightweight, focused cipher-only tool — useful as a self-contained drop-in. |

---

## Modules

### 🔐 Cipher Suite
Encrypt and decrypt messages using four selectable algorithms. Includes key input, encrypt/decrypt mode toggle, copy, swap, and clear utilities.

### 🎣 PhishGuard
Paste a suspicious email, SMS, or message body to receive a structured analysis — risk score, red flags, plain-language explanation, and a contextual security tip. Analysis is entirely local; no text is transmitted.

### 📱 QR Studio
Generate QR codes for URLs, plain text, Wi-Fi credentials, and vCard contacts. Live preview with a download button.

---

## Cipher Algorithms

All encryption runs in the browser via **CryptoJS 4.1.1** — no data is sent anywhere.

| Algorithm | Type | Notes |
|-----------|------|-------|
| **AES-256** | Modern encryption | Requires a passphrase. Recommended for sensitive data. Default. |
| **XOR** | Classical cipher | Output is Base64-encoded for readability. Not for high-security use. |
| **Caesar** | Classical cipher | Configurable character shift (default: 3). Non-alpha characters preserved. |
| **Base64** | Encoding | Encoding/decoding only — not encryption. No key required. |

---

## PhishGuard Output

Each analysis returns:

- **Risk score** — `LOW` / `MEDIUM` / `HIGH` / `CRITICAL`
- **Red flags** — specific suspicious phrases or patterns detected
- **Explanation** — plain-language breakdown of the threat
- **Security tip** — contextual advice for the detected attack vector

---

## QR Studio Input Modes

| Mode | Fields |
|------|--------|
| **URL** | Any web address |
| **Text** | Arbitrary plain text |
| **Wi-Fi** | SSID, password, security type (WPA / WEP / None) |
| **vCard** | Name, phone, email, organisation, URL |

---

## Usage

No build step or install required. Open any file directly in a browser:

```bash
# Open directly
open cybersuite_v5.html

# Or serve locally
npx serve .
# or
python3 -m http.server 8080
```

> An internet connection is required on first load for CDN-hosted fonts and library scripts.

---

## External Dependencies (CDN)

| Library | Version | Used for |
|---------|---------|---------|
| [CryptoJS](https://cdnjs.cloudflare.com/ajax/libs/crypto-js/4.1.1/crypto-js.min.js) | 4.1.1 | AES-256 encryption in Cipher Suite |
| [qrcodejs](https://cdnjs.cloudflare.com/ajax/libs/qrcodejs/1.0.0/qrcode.min.js) | 1.0.0 | QR code rendering in QR Studio |
| Google Fonts | — | Bebas Neue, Rajdhani, JetBrains Mono, Inter |

---

## Privacy & Security

- All cryptographic operations run locally via CryptoJS — no plaintext or keys leave your device.
- PhishGuard analysis is fully offline — pasted content is never transmitted.
- QR code generation is client-side — no data is sent to an external QR API.
- The only external network calls are CDN asset loads (fonts and libraries) on page load.

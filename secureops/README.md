# SecureOps Dashboard

Classical-cipher security log encryption + a real-time web dashboard for monitoring
simulated security events, built with Flask and Flask-SocketIO.

## Project structure

```
secureops/
├── app.py              # Flask + SocketIO server
├── core.py              # Ciphers, threat detection, encrypted storage, dashboard engine
├── requirements.txt
└── templates/
    └── dashboard.html    # Live-updating dashboard UI
```

All four items must sit in this exact layout — Flask looks for `templates/`
as a folder right next to `app.py`.

## Setup

From inside the `secureops/` folder:

```bash
pip install -r requirements.txt
python app.py
```

Then open **http://localhost:5000**.

## What it does

- Generates simulated security events (failed logins, malware signatures, port
  scans, etc.) at a randomized interval.
- Runs each event through `ThreatDetector` (Shannon entropy, Caesar-cipher
  detection via chi-squared analysis, Kasiski-style repeat detection).
- Encrypts each event (Vigenère by default) and persists it to `secure_logs.jsonl`,
  with a SHA-256 checksum for tamper detection.
- Streams new events to the browser in real time over Socket.IO and refreshes
  a polled snapshot every 10 seconds as a fallback.

## API endpoints

| Endpoint | Description |
|---|---|
| `GET /` | Dashboard UI |
| `GET /api/snapshot` | Current alert/threat counts, top sources, recent events |
| `GET /api/events?limit=50&decrypt=true` | Decrypted event history (`decrypt=false` for raw ciphertext) |

## Troubleshooting

**`Could not open requirements file`**
You're not in the `secureops/` directory. `cd` into it (check with `pwd` /
`ls`) before running `pip install -r requirements.txt`, or point pip at the
full path.

**`jinja2.exceptions.TemplateNotFound: dashboard.html`**
`templates/dashboard.html` isn't sitting next to `app.py`. Verify the layout
above with `ls -R` (or `dir /s` on Windows) — Flask requires that exact
subfolder name by default.

**Dashboard loads but header stays on "connecting…"**
The page is served correctly, but the browser can't open the Socket.IO
connection. Check, in order:
1. `pip show simple-websocket` — install it if missing
   (`pip install simple-websocket`), then restart `app.py`. Without it,
   Flask-SocketIO's dev server can't upgrade to websockets.
2. Browser DevTools (F12) → **Console** — an `io is not defined` error means
   the `socket.io.min.js` CDN script was blocked (ad-blocker, offline,
   firewall).
3. DevTools → **Network** tab, filter `socket.io` — confirm a request to
   `/socket.io/?EIO=4&transport=polling` returns `200`. If it's missing,
   refused, or non-200, that points to a local network/firewall block rather
   than an app bug.

## Notes

- `secure_logs.jsonl` is the encrypted event log; delete it to reset history.
- The in-memory encryption master key is regenerated every time the app
  restarts, by design for this demo — for real persistence across restarts
  you'd need to move key management to a proper KMS/secrets store.
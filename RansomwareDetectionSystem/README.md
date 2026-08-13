# Ransomware Detection System

A Python-based defensive cybersecurity project that monitors file-system activity, analyzes behavioral patterns, calculates risk, records security events and incidents in SQLite, and presents the results through a Flask web dashboard.

> **Project status:** Core monitoring, behavioral analysis, risk scoring, SQLite storage, dashboard, and incident-details functionality have been developed and tested during the current project build.

## Features

- Real-time file-system monitoring with Watchdog
- Detection of file creation and modification activity
- Behavioral analysis
- Risk scoring
- Ransomware-like behavior detection
- SQLite event and incident storage
- Flask web dashboard
- Incident list and incident-details pages
- JSON API for incidents and events
- Incident status storage
- Defensive testing through a local test folder

## Project Structure

```text
RansomwareDetectionSystem/
├── detector/
│   ├── __init__.py
│   ├── monitor.py
│   └── analyzer.py
│
├── database/
│   ├── __init__.py
│   └── security_database.py
│
├── web/
│   ├── __init__.py
│   ├── app.py
│   └── templates/
│       ├── dashboard.html
│       └── incident.html
│
├── tests/
│   └── simulator.py
│
├── test_folder/
│
└── security.db
```

## Requirements

Recommended environment:

- Python 3.x
- Flask
- Watchdog

Install the required packages:

```powershell
pip install flask watchdog
```

Install any additional packages required by the existing analyzer/monitor implementation if they are not already installed.

## Running the Project

Open PowerShell and move to the project directory:

```powershell
cd "C:\Users\User\Desktop\My Personal Projects\SECURITY\RansomwareDetectionSystem"
```

### Start the web dashboard

```powershell
python web\app.py
```

Then open:

```text
http://127.0.0.1:5000/
```

## Incident Details

The web application provides a dynamic incident route:

```text
/incident/<incident_id>
```

Examples:

```text
http://127.0.0.1:5000/incident/1
http://127.0.0.1:5000/incident/2
```

The incident page obtains its data from:

```text
/api/incidents/<incident_id>
```

For example:

```text
http://127.0.0.1:5000/api/incidents/1
```

## Available API Endpoints

| Endpoint | Purpose |
|---|---|
| `/` | Web dashboard |
| `/incident/<id>` | Incident details page |
| `/api/incidents` | Recent incidents as JSON |
| `/api/incidents/<id>` | One incident as JSON |
| `/api/events` | Recent file events as JSON |
| `/api/stats` | Dashboard statistics |

## Database

The project uses SQLite.

The main database file is:

```text
security.db
```

The database stores:

### Events

- ID
- Timestamp
- Event type
- File path
- Score
- Risk level

### Incidents

- ID
- Incident type
- Risk level
- Score
- Total events
- Modified count
- Renamed count
- Deleted count
- Created count
- Detection reasons
- Status
- Timestamp

The database implementation uses a fresh SQLite connection for database operations. This is important because the file monitor runs in a Watchdog thread while Flask handles web requests separately.

## Validation

### Check existing incidents

Run:

```powershell
python -c "from database.security_database import SecurityDatabase; db=SecurityDatabase(); print(db.get_incident(1)); print(db.get_incident(2))"
```

A successful result should return incident dictionaries when those IDs exist in the database.

### Check the incident API

Open:

```text
http://127.0.0.1:5000/api/incidents/1
```

Expected data contains fields similar to:

```json
{
  "id": 1,
  "incident_type": "RANSOMWARE",
  "risk_level": "HIGH",
  "score": 50,
  "total_events": 100,
  "modified": 50,
  "renamed": 0,
  "deleted": 0,
  "created": 50,
  "reasons": "Rapid file modification; Mass file modification",
  "status": "OPEN",
  "timestamp": "2026-08-08 16:19:08"
}
```

The exact values depend on the incidents currently stored in the database.

### Check the incident page

Open:

```text
http://127.0.0.1:5000/incident/1
```

The page should display the incident ID, score, risk level, status, event statistics, incident type, timestamp, and detection reasons.

## Testing the File Monitor

The project has a local test directory:

```text
test_folder/
```

The simulator can be used to generate test file activity:

```powershell
python tests\simulator.py
```

The monitor should report events such as:

```text
[EVENT] CREATED: ...
[EVENT] MODIFIED: ...
[ANALYSIS] Events=...
```

The testing performed so far produced a MEDIUM-risk state after rapid modification activity and later produced HIGH-risk ransomware incidents using multiple behavioral indicators.

## Development History / Completed Steps

1. Created the project foundation.
2. Implemented file-system monitoring.
3. Implemented behavioral analysis.
4. Implemented risk scoring.
5. Added ransomware-like behavior detection.
6. Added SQLite event and incident storage.
7. Resolved the SQLite cross-thread connection problem.
8. Added the Flask dashboard.
9. Added incident APIs.
10. Added dynamic incident-detail routing.
11. Connected dashboard incident IDs to their corresponding incident pages.

## Important Troubleshooting

### `ModuleNotFoundError`

Run commands from the project root:

```text
C:\Users\User\Desktop\My Personal Projects\SECURITY\RansomwareDetectionSystem
```

Also ensure the package marker files exist:

```text
detector/__init__.py
database/__init__.py
web/__init__.py
```

### SQLite thread error

If you see:

```text
SQLite objects created in a thread can only be used in that same thread
```

the database code should not reuse one SQLite connection between Watchdog and other threads. The current database implementation creates connections per operation.

### `no such column: timestamp`

This indicates that the existing SQLite schema does not match the current application schema. The current database initialization defines a `timestamp` field for incidents.

Do not immediately delete the database if it contains valuable test incidents. Inspect and migrate the schema first.

### Incident page shows an error

Check the API first:

```text
http://127.0.0.1:5000/api/incidents/1
```

If the API works, then test:

```text
http://127.0.0.1:5000/incident/1
```

### Incident does not exist

If `/api/incidents/2` returns a 404, that means incident ID 2 is not currently present in the database. Incident IDs depend on the records that have actually been created.

## Current Architecture

```text
                 File System
                      |
                      v
              +---------------+
              | Watchdog       |
              | File Monitor   |
              +-------+-------+
                      |
                      v
              +---------------+
              | Behavioral    |
              | Analyzer      |
              +-------+-------+
                      |
                      v
              +---------------+
              | Risk Scoring   |
              +-------+-------+
                      |
             +--------+--------+
             |                 |
             v                 v
       File Events        Incidents
             |                 |
             +--------+--------+
                      |
                      v
                SQLite DB
                      |
                      v
                Flask API
                      |
                      v
              Web Dashboard
                      |
                      v
              Incident Details
```

## Next Development Phase

The next planned phase is the **Incident Response and Alert System**.

Potential components include:

- Security alerts
- Incident status management
- Incident investigation workflow
- Event timeline
- Alert severity
- Incident resolution
- Dashboard notifications
- Better ransomware simulation for controlled testing
- Project logging and audit trail

## Security and Testing Scope

This project is intended for defensive cybersecurity education and controlled testing on systems and folders owned or authorized by the project operator.

Do not use the simulator or monitoring system against systems, files, or networks without authorization.

## Author

**Ransomware Detection System — Final Year Cybersecurity Project**

Development is being completed incrementally, with each subsystem tested before the next subsystem is added.

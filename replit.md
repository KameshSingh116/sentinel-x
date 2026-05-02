# Sentinel-X: Cross-Platform Intrusion & Behavior Monitoring System

## Overview
A full-stack cybersecurity monitoring system with a Python/Flask backend, dark-themed web dashboard, and React Native mobile app code.

## Architecture
- **Backend**: Python 3.11 + Flask, runs on port 5000 (serves both API & web dashboard)
- **Web Dashboard**: Jinja2 templates served by Flask, dark cybersecurity theme
- **Mobile**: React Native (Expo) code in `sentinel-x/mobile/`

## Project Structure
```
sentinel-x/
├── backend/
│   ├── app.py                  # Flask app, API routes, monitoring loop
│   ├── modules/
│   │   ├── system_monitor.py   # psutil-based CPU/memory/disk/process monitoring
│   │   ├── network_monitor.py  # Network connections, suspicious IP detection
│   │   ├── anomaly_detector.py # Rule-based anomaly detection engine
│   │   ├── logger.py           # SQLite + JSON dual logging
│   │   └── alert_system.py     # Alert management + SMTP email
│   └── templates/              # dashboard.html, alerts.html, logs.html, processes.html
├── mobile/                     # React Native (Expo) app
│   ├── App.js
│   ├── config.js               # Set BASE_URL here for mobile
│   └── screens/                # DashboardScreen, AlertsScreen, LogsScreen
├── database/                   # SQLite DB (auto-created: sentinel.db)
├── logs/                       # JSON event log (auto-created: events.json)
└── requirements.txt
```

## Running the Application
```bash
python sentinel-x/backend/app.py
```
Dashboard available at port 5000.

## Key Dependencies
- `flask` — Web framework + REST API
- `flask-cors` — CORS for mobile app access
- `psutil` — System monitoring (CPU, memory, disk, processes)
- `sqlite3` — Built-in Python, used for event/alert storage

## REST API Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Service health check |
| GET | `/api/status` | Full system + network snapshot |
| GET | `/api/logs` | Event log browser (params: limit, severity, type) |
| GET | `/api/alerts` | Alerts list (params: limit, resolved) |
| POST | `/api/alerts/<id>/resolve` | Resolve an alert |
| POST | `/api/trigger-test-alert` | Trigger a manual test alert |
| GET | `/api/processes` | Top 50 processes by CPU |
| GET | `/api/anomalies` | Recent anomaly detection history |

## Configuration (Environment Variables)
- `PORT` — Server port (default: 5000)
- `MONITOR_INTERVAL` — Seconds between scans (default: 30)
- `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS` — Email alert config
- `ALERT_EMAIL_TO` — Recipient email for high/critical alerts

## Mobile App Setup
1. `cd sentinel-x/mobile && npm install`
2. Edit `config.js` → set `BASE_URL` to backend URL
3. Run with `npx expo start`

## Workflow
- **Start application**: `python sentinel-x/backend/app.py` → port 5000 (webview)

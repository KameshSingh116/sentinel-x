# Sentinel-X: Cross-Platform Intrusion & Behavior Monitoring System

A production-quality cybersecurity monitoring system with a Python/Flask backend, web dashboard, and React Native mobile app.

---

## Features

- **Real-time System Monitoring** — CPU, memory, disk usage with threshold alerting
- **Network Monitoring** — Active connection tracking, suspicious IP detection, port analysis
- **Anomaly Detection** — Rule-based detection: spikes, sustained highs, sudden jumps, repeated patterns
- **REST API** — Full JSON API for all monitoring data
- **Alert System** — In-app alerts + optional SMTP email notifications
- **Event Logging** — SQLite database + JSON file logging with severity levels
- **Web Dashboard** — Dark-themed responsive dashboard with live auto-refresh
- **Mobile App** — React Native app (Dashboard, Alerts, Logs screens)

---

## Architecture

```
sentinel-x/
├── backend/                  # Flask REST API + Web Dashboard
│   ├── app.py                # Main Flask application & API routes
│   ├── modules/
│   │   ├── system_monitor.py # CPU, memory, disk, process monitoring
│   │   ├── network_monitor.py# Network connections & suspicious IP detection
│   │   ├── anomaly_detector.py # Rule-based anomaly detection engine
│   │   ├── logger.py         # SQLite + JSON logging system
│   │   └── alert_system.py   # Alert management + email notifications
│   ├── templates/            # Jinja2 HTML dashboard templates
│   └── static/               # CSS/JS static assets
├── mobile/                   # React Native mobile application
│   ├── App.js                # Navigation container
│   ├── config.js             # API base URL configuration
│   └── screens/
│       ├── DashboardScreen.js
│       ├── AlertsScreen.js
│       └── LogsScreen.js
├── database/                 # SQLite database (auto-created)
├── logs/                     # JSON event logs (auto-created)
└── requirements.txt
```

---

## Backend Setup

```bash
cd sentinel-x
pip install -r requirements.txt
cd backend
python app.py
```

The server starts on `http://0.0.0.0:5000`

### Environment Variables (optional)

| Variable         | Default           | Description                    |
|-----------------|-------------------|--------------------------------|
| `PORT`          | `5000`            | Server port                    |
| `MONITOR_INTERVAL` | `30`           | Seconds between scans          |
| `SMTP_HOST`     | `smtp.gmail.com`  | SMTP server for email alerts   |
| `SMTP_PORT`     | `587`             | SMTP port                      |
| `SMTP_USER`     | —                 | SMTP username/email            |
| `SMTP_PASS`     | —                 | SMTP password/app password     |
| `ALERT_EMAIL_TO`| —                 | Recipient email for alerts     |

---

## API Documentation

### `GET /api/health`
Returns service health status.

### `GET /api/status`
Returns full system + network status snapshot.

### `GET /api/logs`
Returns event logs from the database.

Query params: `limit` (default 100), `severity` (critical/high/medium/low/info), `type`

### `GET /api/alerts`
Returns stored alerts.

Query params: `limit`, `resolved` (true/false)

### `POST /api/alerts/<id>/resolve`
Marks an alert as resolved.

### `POST /api/trigger-test-alert`
Triggers a manual test alert.

### `GET /api/processes`
Returns top 50 processes sorted by CPU usage, with flagged unknown processes.

### `GET /api/anomalies`
Returns recent anomaly detection results.

---

## Mobile App Setup

```bash
cd sentinel-x/mobile
npm install
```

1. Edit `config.js` and set `BASE_URL` to your backend IP/URL
2. Run with Expo: `npm start`
3. Scan QR code with Expo Go app

---

## Web Dashboard

Access the dashboard at `http://localhost:5000` after starting the backend.

Pages:
- `/` — System dashboard (CPU, memory, network, recent alerts)
- `/alerts` — Alert management with resolve actions
- `/logs` — Event log browser with filtering
- `/processes` — Running process list with flagged process detection

---

## Anomaly Detection Rules

| Anomaly | Trigger | Severity |
|---------|---------|----------|
| CPU Spike | CPU > 80% | Medium/High |
| CPU Sudden Jump | +40% in one reading | High |
| Sustained High CPU | >70% for 5 readings | Critical |
| Memory Spike | Memory > 85% | Medium/High |
| Memory Sudden Jump | +30% in one reading | High |
| Suspicious Network | Known malicious ports or repeated IPs | High/Critical |
| High Connection Count | >200 active connections | Medium |
| Unknown Process | Unrecognized process with >10% CPU | High |

import sqlite3
import json
import datetime
import os
from typing import Dict, Any, List, Optional


DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "..", "database", "sentinel.db")
LOG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "..", "logs", "events.json")


def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            event_type TEXT NOT NULL,
            severity TEXT NOT NULL,
            description TEXT NOT NULL,
            metadata TEXT,
            source TEXT DEFAULT 'system'
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            alert_type TEXT NOT NULL,
            severity TEXT NOT NULL,
            message TEXT NOT NULL,
            resolved INTEGER DEFAULT 0,
            metadata TEXT
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_severity ON events(severity)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_alerts_timestamp ON alerts(timestamp)")
    conn.commit()
    conn.close()


def log_event(event_type: str, severity: str, description: str, metadata: Optional[Dict] = None, source: str = "system"):
    timestamp = datetime.datetime.utcnow().isoformat()
    record = {
        "timestamp": timestamp,
        "event_type": event_type,
        "severity": severity,
        "description": description,
        "metadata": metadata or {},
        "source": source
    }

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO events (timestamp, event_type, severity, description, metadata, source) VALUES (?, ?, ?, ?, ?, ?)",
            (timestamp, event_type, severity, description, json.dumps(metadata or {}), source)
        )
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[Logger] DB error: {e}")

    try:
        existing = []
        if os.path.exists(LOG_PATH):
            with open(LOG_PATH, "r") as f:
                try:
                    existing = json.load(f)
                except json.JSONDecodeError:
                    existing = []
        existing.append(record)
        existing = existing[-1000:]
        with open(LOG_PATH, "w") as f:
            json.dump(existing, f, indent=2)
    except Exception as e:
        print(f"[Logger] File error: {e}")

    return record


def store_alert(alert_type: str, severity: str, message: str, metadata: Optional[Dict] = None):
    timestamp = datetime.datetime.utcnow().isoformat()
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO alerts (timestamp, alert_type, severity, message, metadata) VALUES (?, ?, ?, ?, ?)",
            (timestamp, alert_type, severity, message, json.dumps(metadata or {}))
        )
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[Logger] Alert store error: {e}")

    log_event("alert_generated", severity, message, metadata, source="alert_system")


def get_events(limit: int = 100, severity: Optional[str] = None, event_type: Optional[str] = None) -> List[Dict]:
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        query = "SELECT * FROM events"
        params = []
        conditions = []
        if severity:
            conditions.append("severity = ?")
            params.append(severity)
        if event_type:
            conditions.append("event_type = ?")
            params.append(event_type)
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        result = []
        for row in rows:
            d = dict(row)
            try:
                d["metadata"] = json.loads(d.get("metadata") or "{}")
            except Exception:
                d["metadata"] = {}
            result.append(d)
        return result
    except Exception as e:
        print(f"[Logger] Get events error: {e}")
        return []


def get_alerts(limit: int = 100, resolved: Optional[bool] = None) -> List[Dict]:
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        query = "SELECT * FROM alerts"
        params = []
        if resolved is not None:
            query += " WHERE resolved = ?"
            params.append(1 if resolved else 0)
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        result = []
        for row in rows:
            d = dict(row)
            try:
                d["metadata"] = json.loads(d.get("metadata") or "{}")
            except Exception:
                d["metadata"] = {}
            result.append(d)
        return result
    except Exception as e:
        print(f"[Logger] Get alerts error: {e}")
        return []


def resolve_alert(alert_id: int) -> bool:
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("UPDATE alerts SET resolved = 1 WHERE id = ?", (alert_id,))
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False


def get_stats() -> Dict[str, Any]:
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM events")
        total_events = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM alerts")
        total_alerts = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM alerts WHERE resolved = 0")
        open_alerts = cursor.fetchone()[0]
        cursor.execute("SELECT severity, COUNT(*) FROM events GROUP BY severity")
        severity_counts = dict(cursor.fetchall())
        conn.close()
        return {
            "total_events": total_events,
            "total_alerts": total_alerts,
            "open_alerts": open_alerts,
            "severity_breakdown": severity_counts
        }
    except Exception as e:
        print(f"[Logger] Stats error: {e}")
        return {}

import datetime
from typing import Dict, Any, Optional, List
from .logger import store_alert, log_event


_alert_queue: List[Dict] = []


def trigger_alert(alert_type: str, severity: str, message: str, metadata: Optional[Dict] = None) -> Dict[str, Any]:
    store_alert(alert_type, severity, message, metadata)

    alert_record = {
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "alert_type": alert_type,
        "severity": severity,
        "message": message,
        "metadata": metadata or {}
    }

    _alert_queue.append(alert_record)
    if len(_alert_queue) > 200:
        _alert_queue.pop(0)

    return alert_record


def process_anomalies(anomalies: List[Dict]) -> List[Dict]:
    triggered = []
    for anomaly in anomalies:
        alert = trigger_alert(
            alert_type=anomaly.get("type", "unknown"),
            severity=anomaly.get("severity", "medium"),
            message=anomaly.get("description", "Anomaly detected"),
            metadata={"value": anomaly.get("value"), "detected_at": anomaly.get("timestamp")}
        )
        triggered.append(alert)
    return triggered


def trigger_test_alert() -> Dict[str, Any]:
    return trigger_alert(
        alert_type="test_alert",
        severity="high",
        message="This is a manual test alert triggered from the Sentinel-X dashboard.",
        metadata={"triggered_by": "manual", "test": True}
    )


def get_recent_alerts() -> List[Dict]:
    return list(reversed(_alert_queue[-50:]))

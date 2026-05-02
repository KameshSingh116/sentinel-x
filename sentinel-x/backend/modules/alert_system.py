import smtplib
import os
import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, Optional, List
from .logger import store_alert, log_event


SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASS = os.environ.get("SMTP_PASS", "")
ALERT_EMAIL_TO = os.environ.get("ALERT_EMAIL_TO", "")

_alert_queue: List[Dict] = []


def _build_email_body(alert_type: str, severity: str, message: str, metadata: Optional[Dict] = None) -> str:
    timestamp = datetime.datetime.utcnow().isoformat()
    meta_section = ""
    if metadata:
        meta_lines = "\n".join([f"  {k}: {v}" for k, v in metadata.items()])
        meta_section = f"\n\nAdditional Details:\n{meta_lines}"

    return f"""
SENTINEL-X SECURITY ALERT
==========================
Timestamp : {timestamp} UTC
Alert Type: {alert_type}
Severity  : {severity.upper()}
Message   : {message}{meta_section}

---
This alert was generated automatically by Sentinel-X Monitoring System.
Do NOT reply to this email.
"""


def send_email_alert(alert_type: str, severity: str, message: str, metadata: Optional[Dict] = None) -> bool:
    if not all([SMTP_USER, SMTP_PASS, ALERT_EMAIL_TO]):
        log_event(
            "email_alert_skipped",
            "info",
            f"Email not configured. Alert: [{severity.upper()}] {message}",
            source="alert_system"
        )
        return False

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"[Sentinel-X] {severity.upper()} Alert: {alert_type}"
        msg["From"] = SMTP_USER
        msg["To"] = ALERT_EMAIL_TO

        body = _build_email_body(alert_type, severity, message, metadata)
        msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(SMTP_USER, ALERT_EMAIL_TO, msg.as_string())

        log_event(
            "email_alert_sent",
            severity,
            f"Email alert sent: {message}",
            {"to": ALERT_EMAIL_TO, "alert_type": alert_type},
            source="alert_system"
        )
        return True

    except Exception as e:
        log_event(
            "email_alert_failed",
            "error",
            f"Failed to send email alert: {str(e)}",
            source="alert_system"
        )
        return False


def trigger_alert(alert_type: str, severity: str, message: str, metadata: Optional[Dict] = None, send_email: bool = True) -> Dict[str, Any]:
    store_alert(alert_type, severity, message, metadata)

    email_sent = False
    if send_email and severity in ("high", "critical"):
        email_sent = send_email_alert(alert_type, severity, message, metadata)

    alert_record = {
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "alert_type": alert_type,
        "severity": severity,
        "message": message,
        "metadata": metadata or {},
        "email_sent": email_sent
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
        severity="medium",
        message="This is a manual test alert triggered from the Sentinel-X dashboard.",
        metadata={"triggered_by": "manual", "test": True},
        send_email=False
    )


def get_recent_alerts() -> List[Dict]:
    return list(reversed(_alert_queue[-50:]))

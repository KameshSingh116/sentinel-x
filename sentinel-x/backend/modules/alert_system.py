import os
import datetime
import requests
from requests.auth import HTTPBasicAuth
from typing import Dict, Any, Optional, List
from .logger import store_alert, log_event


TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN  = os.environ.get("TWILIO_AUTH_TOKEN", "")
TWILIO_FROM        = os.environ.get("TWILIO_WHATSAPP_FROM", "")
TWILIO_TO          = os.environ.get("TWILIO_WHATSAPP_TO", "")

_alert_queue: List[Dict] = []


def _build_whatsapp_body(alert_type: str, severity: str, message: str, metadata: Optional[Dict] = None) -> str:
    timestamp = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    icon = {"critical": "🚨", "high": "⚠️", "medium": "🔔", "low": "ℹ️"}.get(severity, "🔔")
    lines = [
        f"{icon} *SENTINEL-X ALERT*",
        f"━━━━━━━━━━━━━━━━━━━━",
        f"*Type:* {alert_type}",
        f"*Severity:* {severity.upper()}",
        f"*Time:* {timestamp}",
        f"",
        f"*Message:*",
        f"{message}",
    ]
    if metadata:
        extra = {k: v for k, v in metadata.items() if k not in ("test",) and v is not None}
        if extra:
            lines += ["", "*Details:*"]
            for k, v in list(extra.items())[:4]:
                lines.append(f"• {k}: {v}")
    lines += ["", "_Sent by Sentinel-X Monitoring_"]
    return "\n".join(lines)


def send_whatsapp_alert(alert_type: str, severity: str, message: str, metadata: Optional[Dict] = None) -> bool:
    if not all([TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_FROM, TWILIO_TO]):
        log_event(
            "whatsapp_alert_skipped",
            "info",
            f"WhatsApp not configured. Alert: [{severity.upper()}] {message}",
            source="alert_system"
        )
        return False

    body = _build_whatsapp_body(alert_type, severity, message, metadata)
    url = f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_ACCOUNT_SID}/Messages.json"

    try:
        resp = requests.post(
            url,
            data={
                "From": TWILIO_FROM if TWILIO_FROM.startswith("whatsapp:") else f"whatsapp:{TWILIO_FROM}",
                "To":   TWILIO_TO   if TWILIO_TO.startswith("whatsapp:")   else f"whatsapp:{TWILIO_TO}",
                "Body": body,
            },
            auth=HTTPBasicAuth(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN),
            timeout=10
        )

        if resp.status_code == 201:
            log_event(
                "whatsapp_alert_sent",
                severity,
                f"WhatsApp alert sent: {message}",
                {"to": TWILIO_TO, "alert_type": alert_type, "sid": resp.json().get("sid")},
                source="alert_system"
            )
            return True
        else:
            error_msg = resp.json().get("message", resp.text)
            log_event(
                "whatsapp_alert_failed",
                "error",
                f"Twilio returned {resp.status_code}: {error_msg}",
                source="alert_system"
            )
            return False

    except Exception as e:
        log_event(
            "whatsapp_alert_failed",
            "error",
            f"Failed to send WhatsApp alert: {str(e)}",
            source="alert_system"
        )
        return False


def trigger_alert(alert_type: str, severity: str, message: str, metadata: Optional[Dict] = None, send_whatsapp: bool = True) -> Dict[str, Any]:
    store_alert(alert_type, severity, message, metadata)

    wa_sent = False
    if send_whatsapp and severity in ("high", "critical"):
        wa_sent = send_whatsapp_alert(alert_type, severity, message, metadata)

    alert_record = {
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "alert_type": alert_type,
        "severity": severity,
        "message": message,
        "metadata": metadata or {},
        "whatsapp_sent": wa_sent
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
        metadata={"triggered_by": "manual", "test": True},
        send_whatsapp=True
    )


def get_recent_alerts() -> List[Dict]:
    return list(reversed(_alert_queue[-50:]))

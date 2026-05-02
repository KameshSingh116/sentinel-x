import os
import sys
import datetime
import threading
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, jsonify, render_template, request
from flask_cors import CORS

from modules.system_monitor import get_system_status, get_process_list
from modules.network_monitor import get_network_summary
from modules.anomaly_detector import run_full_detection, get_anomaly_trend
from modules.logger import init_db, log_event, get_events, get_alerts, get_stats, resolve_alert
from modules.alert_system import trigger_alert, trigger_test_alert, process_anomalies, get_recent_alerts

app = Flask(__name__, template_folder="templates", static_folder="static")
CORS(app)

MONITOR_INTERVAL = int(os.environ.get("MONITOR_INTERVAL", "30"))
_last_status_cache = {}
_monitoring_active = False


def monitoring_loop():
    global _last_status_cache, _monitoring_active
    _monitoring_active = True
    log_event("system_start", "info", "Sentinel-X monitoring system started", source="core")

    while _monitoring_active:
        try:
            system_data = get_system_status()
            network_data = get_network_summary()
            processes = get_process_list()

            _last_status_cache = {
                "system": system_data,
                "network": network_data,
                "last_updated": datetime.datetime.utcnow().isoformat()
            }

            detection_result = run_full_detection(system_data, network_data, processes)

            if detection_result["anomaly_count"] > 0:
                triggered = process_anomalies(detection_result["anomalies"])
                log_event(
                    "anomalies_detected",
                    "warning",
                    f"{detection_result['anomaly_count']} anomalie(s) detected",
                    {"count": detection_result["anomaly_count"], "summary": detection_result["severity_summary"]},
                    source="anomaly_detector"
                )
            else:
                log_event("scan_clean", "info", "Routine scan completed — no anomalies detected", source="monitor")

        except Exception as e:
            log_event("monitor_error", "error", f"Monitoring loop error: {str(e)}", source="core")

        time.sleep(MONITOR_INTERVAL)


# ─── API ROUTES ───────────────────────────────────────────────────────────────

@app.route("/api/status", methods=["GET"])
def api_status():
    try:
        if _last_status_cache:
            return jsonify({
                "success": True,
                "data": _last_status_cache
            })
        system_data = get_system_status()
        network_data = get_network_summary()
        return jsonify({
            "success": True,
            "data": {
                "system": system_data,
                "network": network_data,
                "last_updated": datetime.datetime.utcnow().isoformat()
            }
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/logs", methods=["GET"])
def api_logs():
    try:
        limit = int(request.args.get("limit", 100))
        severity = request.args.get("severity")
        event_type = request.args.get("type")
        events = get_events(limit=limit, severity=severity, event_type=event_type)
        stats = get_stats()
        return jsonify({
            "success": True,
            "count": len(events),
            "stats": stats,
            "data": events
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/alerts", methods=["GET"])
def api_alerts():
    try:
        limit = int(request.args.get("limit", 100))
        resolved_param = request.args.get("resolved")
        resolved = None
        if resolved_param == "true":
            resolved = True
        elif resolved_param == "false":
            resolved = False
        alerts = get_alerts(limit=limit, resolved=resolved)
        recent = get_recent_alerts()
        return jsonify({
            "success": True,
            "count": len(alerts),
            "recent_runtime_alerts": recent[:10],
            "data": alerts
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/alerts/<int:alert_id>/resolve", methods=["POST"])
def api_resolve_alert(alert_id):
    try:
        success = resolve_alert(alert_id)
        return jsonify({"success": success, "alert_id": alert_id})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/trigger-test-alert", methods=["POST"])
def api_trigger_test():
    try:
        alert = trigger_test_alert()
        return jsonify({
            "success": True,
            "message": "Test alert triggered successfully",
            "alert": alert
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/processes", methods=["GET"])
def api_processes():
    try:
        processes = get_process_list()
        flagged = [p for p in processes if p.get("flagged")]
        return jsonify({
            "success": True,
            "total": len(processes),
            "flagged_count": len(flagged),
            "data": processes
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/anomalies", methods=["GET"])
def api_anomalies():
    try:
        trend = get_anomaly_trend()
        return jsonify({
            "success": True,
            "count": len(trend),
            "data": trend
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/health", methods=["GET"])
def api_health():
    return jsonify({
        "status": "online",
        "service": "Sentinel-X",
        "version": "1.0.0",
        "monitoring_active": _monitoring_active,
        "timestamp": datetime.datetime.utcnow().isoformat()
    })


# ─── WEB DASHBOARD ROUTES ─────────────────────────────────────────────────────

@app.route("/")
def dashboard():
    return render_template("dashboard.html")


@app.route("/alerts")
def alerts_page():
    return render_template("alerts.html")


@app.route("/logs")
def logs_page():
    return render_template("logs.html")


@app.route("/processes")
def processes_page():
    return render_template("processes.html")


if __name__ == "__main__":
    init_db()

    monitor_thread = threading.Thread(target=monitoring_loop, daemon=True)
    monitor_thread.start()

    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)

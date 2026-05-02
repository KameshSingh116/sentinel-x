import datetime
from typing import Dict, Any, List, Optional
from collections import deque


CPU_SPIKE_THRESHOLD = 80.0
MEMORY_SPIKE_THRESHOLD = 85.0
CPU_SUDDEN_JUMP = 40.0
MEMORY_SUDDEN_JUMP = 30.0

_cpu_history: deque = deque(maxlen=20)
_memory_history: deque = deque(maxlen=20)
_alert_history: List[Dict] = []


class Anomaly:
    def __init__(self, anomaly_type: str, severity: str, description: str, value: Any = None):
        self.type = anomaly_type
        self.severity = severity
        self.description = description
        self.value = value
        self.timestamp = datetime.datetime.utcnow().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "severity": self.severity,
            "description": self.description,
            "value": self.value,
            "timestamp": self.timestamp
        }


def detect_cpu_anomalies(cpu_percent: float) -> List[Anomaly]:
    anomalies = []
    _cpu_history.append(cpu_percent)

    if cpu_percent > CPU_SPIKE_THRESHOLD:
        anomalies.append(Anomaly(
            "cpu_spike",
            "high" if cpu_percent > 90 else "medium",
            f"CPU usage exceeded threshold: {cpu_percent:.1f}% (threshold: {CPU_SPIKE_THRESHOLD}%)",
            cpu_percent
        ))

    if len(_cpu_history) >= 3:
        prev_avg = sum(list(_cpu_history)[-4:-1]) / 3
        if cpu_percent - prev_avg > CPU_SUDDEN_JUMP:
            anomalies.append(Anomaly(
                "cpu_sudden_jump",
                "high",
                f"Sudden CPU spike detected: jumped {cpu_percent - prev_avg:.1f}% in last reading",
                {"current": cpu_percent, "previous_avg": round(prev_avg, 2)}
            ))

    if len(_cpu_history) >= 5:
        recent = list(_cpu_history)[-5:]
        if all(v > 70 for v in recent):
            anomalies.append(Anomaly(
                "cpu_sustained_high",
                "critical",
                f"Sustained high CPU usage for last 5 readings (avg: {sum(recent)/5:.1f}%)",
                {"readings": recent}
            ))

    return anomalies


def detect_memory_anomalies(memory_percent: float) -> List[Anomaly]:
    anomalies = []
    _memory_history.append(memory_percent)

    if memory_percent > MEMORY_SPIKE_THRESHOLD:
        anomalies.append(Anomaly(
            "memory_spike",
            "high" if memory_percent > 92 else "medium",
            f"Memory usage exceeded threshold: {memory_percent:.1f}% (threshold: {MEMORY_SPIKE_THRESHOLD}%)",
            memory_percent
        ))

    if len(_memory_history) >= 3:
        prev_avg = sum(list(_memory_history)[-4:-1]) / 3
        if memory_percent - prev_avg > MEMORY_SUDDEN_JUMP:
            anomalies.append(Anomaly(
                "memory_sudden_jump",
                "high",
                f"Sudden memory spike: jumped {memory_percent - prev_avg:.1f}% in last reading",
                {"current": memory_percent, "previous_avg": round(prev_avg, 2)}
            ))

    return anomalies


def detect_network_anomalies(suspicious_connections: int, total_connections: int) -> List[Anomaly]:
    anomalies = []

    if suspicious_connections > 0:
        ratio = suspicious_connections / max(total_connections, 1)
        anomalies.append(Anomaly(
            "suspicious_network",
            "critical" if ratio > 0.5 else "high",
            f"{suspicious_connections} suspicious network connection(s) detected out of {total_connections} total",
            {"suspicious": suspicious_connections, "total": total_connections}
        ))

    if total_connections > 200:
        anomalies.append(Anomaly(
            "high_connection_count",
            "medium",
            f"Unusually high number of network connections: {total_connections}",
            total_connections
        ))

    return anomalies


def detect_process_anomalies(flagged_processes: List[Dict]) -> List[Anomaly]:
    anomalies = []

    if flagged_processes:
        names = [p['name'] for p in flagged_processes[:5]]
        anomalies.append(Anomaly(
            "unknown_high_cpu_process",
            "high",
            f"Unknown/unrecognized process(es) consuming high CPU: {', '.join(names)}",
            flagged_processes[:5]
        ))

    return anomalies


def run_full_detection(system_data: Dict, network_data: Dict, processes: List[Dict]) -> Dict[str, Any]:
    all_anomalies = []

    all_anomalies += detect_cpu_anomalies(system_data.get("cpu", {}).get("usage_percent", 0))
    all_anomalies += detect_memory_anomalies(system_data.get("memory", {}).get("usage_percent", 0))
    all_anomalies += detect_network_anomalies(
        network_data.get("suspicious_connections", 0),
        network_data.get("total_connections", 0)
    )
    flagged = [p for p in processes if p.get("flagged")]
    all_anomalies += detect_process_anomalies(flagged)

    result = {
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "anomaly_count": len(all_anomalies),
        "anomalies": [a.to_dict() for a in all_anomalies],
        "severity_summary": {
            "critical": sum(1 for a in all_anomalies if a.severity == "critical"),
            "high": sum(1 for a in all_anomalies if a.severity == "high"),
            "medium": sum(1 for a in all_anomalies if a.severity == "medium"),
            "low": sum(1 for a in all_anomalies if a.severity == "low")
        }
    }

    _alert_history.append(result)
    if len(_alert_history) > 100:
        _alert_history.pop(0)

    return result


def get_anomaly_trend() -> List[Dict]:
    return _alert_history[-20:]

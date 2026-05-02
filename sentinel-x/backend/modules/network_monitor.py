import psutil
import datetime
import socket
from collections import Counter
from typing import Dict, Any, List


SUSPICIOUS_PORTS = {22, 23, 25, 445, 1433, 3306, 3389, 4444, 5900, 6379, 27017}
PRIVATE_IP_PREFIXES = ("10.", "172.16.", "172.17.", "172.18.", "172.19.", "192.168.", "127.")
CONNECTION_REPEAT_THRESHOLD = 5

_connection_history: List[str] = []


def is_private_ip(ip: str) -> bool:
    return any(ip.startswith(prefix) for prefix in PRIVATE_IP_PREFIXES)


def is_suspicious_port(port: int) -> bool:
    return port in SUSPICIOUS_PORTS


def get_active_connections() -> List[Dict[str, Any]]:
    global _connection_history
    connections = []

    try:
        net_conns = psutil.net_connections(kind='inet')
    except psutil.AccessDenied:
        return []

    ip_counter = Counter()
    for conn in net_conns:
        if conn.raddr:
            ip_counter[conn.raddr.ip] += 1

    _connection_history.extend(ip_counter.keys())
    _connection_history = _connection_history[-500:]
    repeat_ips = Counter(_connection_history)

    for conn in net_conns:
        remote_ip = conn.raddr.ip if conn.raddr else None
        remote_port = conn.raddr.port if conn.raddr else None
        local_port = conn.laddr.port if conn.laddr else None

        suspicious = False
        reason = []

        if remote_ip and not is_private_ip(remote_ip) and ip_counter[remote_ip] >= CONNECTION_REPEAT_THRESHOLD:
            suspicious = True
            reason.append(f"Repeated connections ({ip_counter[remote_ip]}x) from {remote_ip}")

        if remote_port and is_suspicious_port(remote_port):
            suspicious = True
            reason.append(f"Suspicious destination port {remote_port}")

        if local_port and is_suspicious_port(local_port):
            suspicious = True
            reason.append(f"Suspicious local port {local_port}")

        if remote_ip and repeat_ips[remote_ip] > 20:
            suspicious = True
            reason.append(f"High frequency IP in history: {remote_ip}")

        connections.append({
            "fd": conn.fd,
            "family": str(conn.family),
            "type": str(conn.type),
            "local_address": f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else None,
            "remote_address": f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else None,
            "remote_ip": remote_ip,
            "remote_port": remote_port,
            "status": conn.status,
            "pid": conn.pid,
            "suspicious": suspicious,
            "reason": "; ".join(reason) if reason else None
        })

    return connections


def get_network_io() -> Dict[str, Any]:
    io = psutil.net_io_counters()
    return {
        "bytes_sent_mb": round(io.bytes_sent / (1024 ** 2), 2),
        "bytes_recv_mb": round(io.bytes_recv / (1024 ** 2), 2),
        "packets_sent": io.packets_sent,
        "packets_recv": io.packets_recv,
        "errin": io.errin,
        "errout": io.errout,
        "dropin": io.dropin,
        "dropout": io.dropout
    }


def get_network_summary() -> Dict[str, Any]:
    connections = get_active_connections()
    suspicious = [c for c in connections if c["suspicious"]]
    io_stats = get_network_io()

    unique_ips = list({c["remote_ip"] for c in connections if c["remote_ip"]})
    external_ips = [ip for ip in unique_ips if not is_private_ip(ip)]

    return {
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "total_connections": len(connections),
        "suspicious_connections": len(suspicious),
        "unique_remote_ips": len(unique_ips),
        "external_ips": external_ips[:20],
        "suspicious_details": suspicious[:10],
        "io": io_stats,
        "alert": len(suspicious) > 0
    }

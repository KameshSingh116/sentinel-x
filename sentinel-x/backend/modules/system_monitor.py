import psutil
import datetime
from typing import Dict, Any, List


KNOWN_SAFE_PROCESSES = {
    "python", "python3", "node", "npm", "bash", "sh", "systemd",
    "nginx", "postgres", "redis", "sshd", "cron", "journald",
    "dbus", "udevd", "rsyslogd", "agetty", "login", "init",
    "flask", "gunicorn", "celery", "supervisor"
}

CPU_ALERT_THRESHOLD = 80.0
MEMORY_ALERT_THRESHOLD = 85.0


def get_cpu_info() -> Dict[str, Any]:
    cpu_percent = psutil.cpu_percent(interval=1)
    cpu_count = psutil.cpu_count()
    cpu_freq = psutil.cpu_freq()
    return {
        "usage_percent": cpu_percent,
        "core_count": cpu_count,
        "frequency_mhz": round(cpu_freq.current, 2) if cpu_freq else None,
        "alert": cpu_percent > CPU_ALERT_THRESHOLD
    }


def get_memory_info() -> Dict[str, Any]:
    mem = psutil.virtual_memory()
    swap = psutil.swap_memory()
    return {
        "total_gb": round(mem.total / (1024 ** 3), 2),
        "used_gb": round(mem.used / (1024 ** 3), 2),
        "available_gb": round(mem.available / (1024 ** 3), 2),
        "usage_percent": mem.percent,
        "swap_total_gb": round(swap.total / (1024 ** 3), 2),
        "swap_used_gb": round(swap.used / (1024 ** 3), 2),
        "alert": mem.percent > MEMORY_ALERT_THRESHOLD
    }


def get_disk_info() -> List[Dict[str, Any]]:
    partitions = []
    for part in psutil.disk_partitions():
        try:
            usage = psutil.disk_usage(part.mountpoint)
            partitions.append({
                "device": part.device,
                "mountpoint": part.mountpoint,
                "fstype": part.fstype,
                "total_gb": round(usage.total / (1024 ** 3), 2),
                "used_gb": round(usage.used / (1024 ** 3), 2),
                "free_gb": round(usage.free / (1024 ** 3), 2),
                "usage_percent": usage.percent
            })
        except PermissionError:
            continue
    return partitions


def get_process_list() -> List[Dict[str, Any]]:
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'username', 'cpu_percent', 'memory_percent', 'status', 'create_time']):
        try:
            info = proc.info
            is_unknown = info['name'] and info['name'].lower() not in KNOWN_SAFE_PROCESSES
            processes.append({
                "pid": info['pid'],
                "name": info['name'],
                "username": info['username'],
                "cpu_percent": round(info['cpu_percent'] or 0, 2),
                "memory_percent": round(info['memory_percent'] or 0, 2),
                "status": info['status'],
                "create_time": datetime.datetime.fromtimestamp(info['create_time']).isoformat() if info['create_time'] else None,
                "flagged": is_unknown and (info['cpu_percent'] or 0) > 10.0
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    return sorted(processes, key=lambda x: x['cpu_percent'], reverse=True)[:50]


def get_system_status() -> Dict[str, Any]:
    cpu = get_cpu_info()
    memory = get_memory_info()
    disks = get_disk_info()
    boot_time = psutil.boot_time()
    uptime_seconds = (datetime.datetime.now() - datetime.datetime.fromtimestamp(boot_time)).total_seconds()

    alerts = []
    if cpu["alert"]:
        alerts.append(f"High CPU usage: {cpu['usage_percent']}%")
    if memory["alert"]:
        alerts.append(f"High Memory usage: {memory['usage_percent']}%")

    return {
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "cpu": cpu,
        "memory": memory,
        "disks": disks,
        "boot_time": datetime.datetime.fromtimestamp(boot_time).isoformat(),
        "uptime_seconds": round(uptime_seconds),
        "system_alerts": alerts,
        "health": "critical" if len(alerts) > 1 else ("warning" if alerts else "healthy")
    }

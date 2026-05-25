import logging
import platform
import psutil
from datetime import datetime, timedelta
 
from config import CPU_WARN_THRESHOLD, RAM_WARN_THRESHOLD
 
logger = logging.getLogger("jarvis.skills.sysmon")
 
def get_full_report() -> str:
    """Return a comprehensive system status report."""
    lines = ["System Status Report", "=" * 22]
 
    cpu_pct   = psutil.cpu_percent(interval=1)
    cpu_cores = psutil.cpu_count(logical=False)
    cpu_freq  = psutil.cpu_freq()
    freq_str  = f" @ {cpu_freq.current:.0f} MHz" if cpu_freq else ""
    lines.append(f"CPU:    {cpu_pct:.1f}%  ({cpu_cores} cores{freq_str})")
 
    ram = psutil.virtual_memory()
    lines.append(
        f"RAM:    {ram.percent:.1f}%  "
        f"({_gb(ram.used)} used / {_gb(ram.total)} total)"
    )
 
    for part in psutil.disk_partitions():
        try:
            usage = psutil.disk_usage(part.mountpoint)
            lines.append(
                f"Disk [{part.device}]:  {usage.percent:.1f}%  "
                f"({_gb(usage.free)} free / {_gb(usage.total)} total)"
            )
        except PermissionError:
            pass
 
    battery = psutil.sensors_battery()
    if battery:
        status = "charging" if battery.power_plugged else "on battery"
        secs_left = battery.secsleft
        if secs_left > 0 and not battery.power_plugged:
            remaining = str(timedelta(seconds=int(secs_left)))
            lines.append(f"Battery: {battery.percent:.0f}%  ({status}, {remaining} remaining)")
        else:
            lines.append(f"Battery: {battery.percent:.0f}%  ({status})")
 
    net = psutil.net_io_counters()
    lines.append(
        f"Network: ↑ {_mb(net.bytes_sent)} sent  ↓ {_mb(net.bytes_recv)} received"
    )
 
    boot = datetime.fromtimestamp(psutil.boot_time())
    uptime = datetime.now() - boot
    hours, rem = divmod(int(uptime.total_seconds()), 3600)
    minutes     = rem // 60
    lines.append(f"Uptime:  {hours}h {minutes}m")
 
    lines.append(f"OS:     {platform.system()} {platform.release()}")
 
    return "\n".join(lines)
 
 
def get_quick_status() -> str:
    """One-liner status for voice response."""
    cpu = psutil.cpu_percent(interval=0.5)
    ram = psutil.virtual_memory()
    battery = psutil.sensors_battery()
 
    parts = [
        f"CPU at {cpu:.0f} percent",
        f"RAM at {ram.percent:.0f} percent ({_gb(ram.available)} free)",
    ]
    if battery:
        parts.append(
            f"battery at {battery.percent:.0f} percent "
            f"({'charging' if battery.power_plugged else 'on battery'})"
        )
    return ". ".join(parts) + "."
 
 
def check_warnings() -> list[str]:
    """Return a list of warning strings if any resource is above threshold."""
    warnings = []
    cpu = psutil.cpu_percent(interval=0.5)
    ram = psutil.virtual_memory()
 
    if cpu > CPU_WARN_THRESHOLD:
        warnings.append(f"CPU usage is at {cpu:.0f} percent — unusually high, sir.")
    if ram.percent > RAM_WARN_THRESHOLD:
        warnings.append(f"RAM usage is at {ram.percent:.0f} percent — consider closing applications.")
 
    battery = psutil.sensors_battery()
    if battery and not battery.power_plugged and battery.percent < 15:
        warnings.append(f"Battery is critically low at {battery.percent:.0f} percent.")
 
    return warnings
 
 
def is_sysmon_query(text: str) -> bool:
    triggers = [
        "cpu", "ram", "memory", "disk", "storage", "battery",
        "system status", "how's the system", "how is the system",
        "system health", "performance", "uptime", "network usage",
        "what's running", "resource", "how much memory",
    ]
    lower = text.lower()
    return any(t in lower for t in triggers)
 
def _gb(bytes_: int) -> str:
    return f"{bytes_ / 1e9:.1f} GB"
 
def _mb(bytes_: int) -> str:
    return f"{bytes_ / 1e6:.1f} MB"
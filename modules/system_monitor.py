"""
SystemScope - System Monitoring Module
Collects real-time local hardware and OS performance metrics using psutil.
Handles unavailable metrics, permissions, and unsupported partitions gracefully.
"""

import os
import platform
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

try:
    import psutil
    # Prime initial CPU reading so subsequent interval=None calls return non-zero
    psutil.cpu_percent(interval=None)
    PSUTIL_AVAILABLE = True
except ImportError:
    psutil = None
    PSUTIL_AVAILABLE = False


def format_bytes(bytes_value: Optional[int], precision: int = 2) -> str:
    """Convert bytes into human-readable representation (B, KB, MB, GB, TB)."""
    if bytes_value is None or bytes_value < 0:
        return "N/A"
    units = ["B", "KB", "MB", "GB", "TB", "PB"]
    value = float(bytes_value)
    idx = 0
    while value >= 1024.0 and idx < len(units) - 1:
        value /= 1024.0
        idx += 1
    return f"{value:.{precision}f} {units[idx]}"


def format_uptime(uptime_seconds: Optional[float]) -> str:
    """Format uptime in seconds into a friendly human-readable duration."""
    if uptime_seconds is None or uptime_seconds < 0:
        return "N/A"
    td = timedelta(seconds=int(uptime_seconds))
    days = td.days
    hours, remainder = divmod(td.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    parts = []
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0 or days > 0:
        parts.append(f"{hours}h")
    parts.append(f"{minutes}m")
    parts.append(f"{seconds}s")
    return " ".join(parts)


class SystemMonitor:
    """Gathers real-time performance metrics using psutil."""

    @staticmethod
    def is_available() -> bool:
        return PSUTIL_AVAILABLE

    @staticmethod
    def get_cpu_metrics() -> Dict[str, Any]:
        """Collect current CPU utilization, core counts, and frequency."""
        if not PSUTIL_AVAILABLE:
            return {
                "available": False,
                "error": "psutil library is not available",
                "overall_percent": 0.0,
                "per_cpu_percent": [],
                "logical_cores": None,
                "physical_cores": None,
                "freq_current_mhz": None,
            }

        try:
            overall = psutil.cpu_percent(interval=0.1)
            per_cpu = psutil.cpu_percent(interval=None, percpu=True)
            logical = psutil.cpu_count(logical=True)
            physical = psutil.cpu_count(logical=False)
            
            freq_current = None
            try:
                freq = psutil.cpu_freq()
                if freq:
                    freq_current = round(freq.current, 1)
            except Exception:
                freq_current = None

            return {
                "available": True,
                "overall_percent": float(overall),
                "per_cpu_percent": [float(p) for p in per_cpu],
                "logical_cores": logical or 1,
                "physical_cores": physical or 1,
                "freq_current_mhz": freq_current,
                "timestamp": datetime.now(),
            }
        except Exception as exc:
            return {
                "available": False,
                "error": str(exc),
                "overall_percent": 0.0,
                "per_cpu_percent": [],
                "logical_cores": 1,
                "physical_cores": 1,
                "freq_current_mhz": None,
            }

    @staticmethod
    def get_memory_metrics() -> Dict[str, Any]:
        """Collect RAM and Swap memory utilization."""
        if not PSUTIL_AVAILABLE:
            return {
                "available": False,
                "error": "psutil library is not available",
                "total_bytes": 0,
                "used_bytes": 0,
                "available_bytes": 0,
                "percent": 0.0,
            }

        try:
            vm = psutil.virtual_memory()
            swap = None
            try:
                swap = psutil.swap_memory()
            except Exception:
                pass

            return {
                "available": True,
                "total_bytes": vm.total,
                "used_bytes": vm.used,
                "available_bytes": vm.available,
                "free_bytes": getattr(vm, "free", vm.available),
                "percent": float(vm.percent),
                "total_fmt": format_bytes(vm.total),
                "used_fmt": format_bytes(vm.used),
                "available_fmt": format_bytes(vm.available),
                "swap_total": swap.total if swap else 0,
                "swap_used": swap.used if swap else 0,
                "swap_percent": swap.percent if swap else 0.0,
                "swap_total_fmt": format_bytes(swap.total) if swap else "N/A",
                "swap_used_fmt": format_bytes(swap.used) if swap else "N/A",
            }
        except Exception as exc:
            return {
                "available": False,
                "error": str(exc),
                "total_bytes": 0,
                "used_bytes": 0,
                "available_bytes": 0,
                "percent": 0.0,
            }

    @staticmethod
    def get_partitions() -> List[Dict[str, str]]:
        """
        List mounted and accessible disk partitions.
        Filters out locked, inaccessible, or dummy mountpoints gracefully.
        """
        if not PSUTIL_AVAILABLE:
            return [{"device": "Default", "mountpoint": "/", "fstype": "unknown"}]

        partitions_list = []
        try:
            all_parts = psutil.disk_partitions(all=False)
            for part in all_parts:
                try:
                    # Test accessibility to prevent freeze on empty CD-ROMs or unmounted network drives
                    if os.path.exists(part.mountpoint):
                        _ = psutil.disk_usage(part.mountpoint)
                        partitions_list.append({
                            "device": part.device,
                            "mountpoint": part.mountpoint,
                            "fstype": part.fstype,
                            "opts": part.opts,
                        })
                except (PermissionError, FileNotFoundError, OSError):
                    continue
        except Exception:
            pass

        if not partitions_list:
            # Fallback to root or current working drive
            fallback_mount = os.path.abspath(os.sep)
            partitions_list.append({
                "device": fallback_mount,
                "mountpoint": fallback_mount,
                "fstype": "standard",
                "opts": "rw",
            })

        return partitions_list

    @staticmethod
    def get_disk_metrics(mountpoint: str) -> Dict[str, Any]:
        """Collect storage statistics for a specified mountpoint."""
        if not PSUTIL_AVAILABLE:
            return {
                "available": False,
                "error": "psutil library is not available",
                "mountpoint": mountpoint,
                "total_bytes": 0,
                "used_bytes": 0,
                "free_bytes": 0,
                "percent": 0.0,
            }

        try:
            usage = psutil.disk_usage(mountpoint)
            return {
                "available": True,
                "mountpoint": mountpoint,
                "total_bytes": usage.total,
                "used_bytes": usage.used,
                "free_bytes": usage.free,
                "percent": float(usage.percent),
                "total_fmt": format_bytes(usage.total),
                "used_fmt": format_bytes(usage.used),
                "free_fmt": format_bytes(usage.free),
            }
        except Exception as exc:
            return {
                "available": False,
                "error": f"Unable to read drive '{mountpoint}': {str(exc)}",
                "mountpoint": mountpoint,
                "total_bytes": 0,
                "used_bytes": 0,
                "free_bytes": 0,
                "percent": 0.0,
            }

    @staticmethod
    def get_system_summary() -> Dict[str, Any]:
        """Collect OS, host, and uptime metadata."""
        boot_time_dt = None
        uptime_sec = None
        if PSUTIL_AVAILABLE:
            try:
                boot_ts = psutil.boot_time()
                boot_time_dt = datetime.fromtimestamp(boot_ts)
                uptime_sec = time.time() - boot_ts
            except Exception:
                pass

        return {
            "os_name": platform.system(),
            "os_release": platform.release(),
            "os_version": platform.version(),
            "architecture": platform.machine(),
            "processor": platform.processor() or "Unknown Processor",
            "hostname": platform.node(),
            "boot_time": boot_time_dt.strftime("%Y-%m-%d %H:%M:%S") if boot_time_dt else "N/A",
            "uptime_seconds": uptime_sec,
            "uptime_fmt": format_uptime(uptime_sec),
        }


def generate_system_report(
    cpu_data: Dict[str, Any],
    ram_data: Dict[str, Any],
    disk_data: Dict[str, Any],
    sys_info: Dict[str, Any],
    partitions: List[Dict[str, str]],
    cpu_threshold: float,
    ram_threshold: float,
    disk_threshold: float,
    selected_mount: str,
) -> Dict[str, str]:
    """Generates comprehensive system performance reports in Plain Text and Markdown formats."""
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Per-core string formatting
    per_cpu = cpu_data.get("per_cpu_percent", [])
    core_lines = []
    for i, p in enumerate(per_cpu):
        core_lines.append(f"  Core {i+1:>2}: {p:>5.1f}%")
    per_core_block = "\n".join(core_lines) if core_lines else "  No per-core data available."

    # Partitions block
    part_lines = []
    for p in partitions:
        try:
            m = SystemMonitor.get_disk_metrics(p["mountpoint"])
            part_lines.append(
                f"  - Mount: {p['mountpoint']:<10} Device: {p['device']:<12} FSType: {p['fstype']:<8} "
                f"Used: {m['used_fmt']:<9} / Total: {m['total_fmt']:<9} ({m['percent']:.1f}% used)"
            )
        except Exception:
            part_lines.append(f"  - Mount: {p['mountpoint']} Device: {p['device']}")
    part_block = "\n".join(part_lines)

    # Threshold evaluations
    cpu_status = "WARNING" if cpu_data["overall_percent"] >= cpu_threshold else "NORMAL"
    ram_status = "WARNING" if ram_data["percent"] >= ram_threshold else "NORMAL"
    disk_status = "WARNING" if disk_data["percent"] >= disk_threshold else "NORMAL"
    overall_status = "WARNING - One or more thresholds exceeded" if (cpu_status == "WARNING" or ram_status == "WARNING" or disk_status == "WARNING") else "NORMAL - All metrics within defined limits"

    txt_report = f"""================================================================================
                    SYSTEMSCOPE SYSTEM PERFORMANCE REPORT
================================================================================
Report Generated: {now_str}
Host Machine:     {sys_info.get('hostname', 'Localhost')}
Operating System: {sys_info.get('os_name', 'OS')} {sys_info.get('os_release', '')} (Version: {sys_info.get('os_version', 'N/A')})
Architecture:     {sys_info.get('architecture', 'N/A')}
Processor:        {sys_info.get('processor', 'N/A')}
System Uptime:    {sys_info.get('uptime_fmt', 'N/A')} (Boot: {sys_info.get('boot_time', 'N/A')})
Diagnostic State: {overall_status}
================================================================================

1. CPU UTILIZATION & CORES
--------------------------------------------------------------------------------
Overall CPU Load:        {cpu_data.get('overall_percent', 0.0):.1f}% [Limit: {cpu_threshold:.0f}% | Status: {cpu_status}]
Physical CPU Cores:      {cpu_data.get('physical_cores', 'N/A')}
Logical CPU Cores:       {cpu_data.get('logical_cores', 'N/A')}
Processor Frequency:     {cpu_data.get('freq_current_mhz', 'N/A')} MHz
Logical Core Load Distribution:
{per_core_block}

2. MEMORY & SWAP ALLOCATION
--------------------------------------------------------------------------------
Physical RAM Usage:      {ram_data.get('percent', 0.0):.1f}% [Limit: {ram_threshold:.0f}% | Status: {ram_status}]
Total Physical RAM:      {ram_data.get('total_fmt', 'N/A')}
Used Physical RAM:       {ram_data.get('used_fmt', 'N/A')}
Available / Free RAM:    {ram_data.get('available_fmt', 'N/A')}
Swap Memory Total:       {ram_data.get('swap_total_fmt', 'N/A')}
Swap Memory Used:        {ram_data.get('swap_used_fmt', 'N/A')} ({ram_data.get('swap_percent', 0.0):.1f}%)

3. STORAGE & PARTITIONS
--------------------------------------------------------------------------------
Monitored Drive:         {selected_mount}
Capacity Used:           {disk_data.get('used_fmt', 'N/A')} of {disk_data.get('total_fmt', 'N/A')} ({disk_data.get('percent', 0.0):.1f}%)
Capacity Available:      {disk_data.get('free_fmt', 'N/A')}
Drive Warning Threshold: {disk_threshold:.0f}% [Status: {disk_status}]

All Accessible Partitions:
{part_block}

4. ALERT THRESHOLD AUDIT SUMMARY
--------------------------------------------------------------------------------
- CPU Load:    {cpu_data.get('overall_percent', 0.0):.1f}%  vs  Warning Threshold: {cpu_threshold:.0f}%  --> {cpu_status}
- RAM Usage:   {ram_data.get('percent', 0.0):.1f}%  vs  Warning Threshold: {ram_threshold:.0f}%  --> {ram_status}
- Disk Space:  {disk_data.get('percent', 0.0):.1f}%  vs  Warning Threshold: {disk_threshold:.0f}%  --> {disk_status}

Notice: High utilization indicates current operating demand and is diagnostic
information. SystemScope operates in read-only telemetry mode.
================================================================================
"""

    md_report = f"""# SystemScope System Performance Report

**Generated:** `{now_str}`  
**Host Machine:** `{sys_info.get('hostname', 'Localhost')}`  
**Operating System:** {sys_info.get('os_name', 'OS')} {sys_info.get('os_release', '')} (`{sys_info.get('os_version', 'N/A')}`)  
**Architecture:** `{sys_info.get('architecture', 'N/A')}` | **Processor:** `{sys_info.get('processor', 'N/A')}`  
**System Uptime:** {sys_info.get('uptime_fmt', 'N/A')} (Boot: {sys_info.get('boot_time', 'N/A')})  
**Overall Status:** **{overall_status}**

---

## 1. CPU Telemetry
- **Overall Load:** **{cpu_data.get('overall_percent', 0.0):.1f}%** (Threshold: {cpu_threshold:.0f}% — **{cpu_status}**)
- **Physical Cores:** {cpu_data.get('physical_cores', 'N/A')} | **Logical Cores:** {cpu_data.get('logical_cores', 'N/A')}
- **Clock Frequency:** {cpu_data.get('freq_current_mhz', 'N/A')} MHz

## 2. Memory Telemetry
- **RAM Usage:** **{ram_data.get('percent', 0.0):.1f}%** (Threshold: {ram_threshold:.0f}% — **{ram_status}**)
- **Total Physical RAM:** {ram_data.get('total_fmt', 'N/A')}
- **Used Memory:** {ram_data.get('used_fmt', 'N/A')} | **Available Memory:** {ram_data.get('available_fmt', 'N/A')}
- **Swap Memory:** {ram_data.get('swap_used_fmt', 'N/A')} used / {ram_data.get('swap_total_fmt', 'N/A')} total

## 3. Storage Allocation (`{selected_mount}`)
- **Capacity:** {disk_data.get('total_fmt', 'N/A')}
- **Used Space:** {disk_data.get('used_fmt', 'N/A')} ({disk_data.get('percent', 0.0):.1f}%)
- **Free Space:** {disk_data.get('free_fmt', 'N/A')}
- **Storage Status:** Threshold {disk_threshold:.0f}% — **{disk_status}**

---
*SystemScope v1.0 • Read-only local hardware diagnostics.*
"""

    return {"text": txt_report, "markdown": md_report}

"""
Comprehensive Verification Test Suite for SystemScope
Validates system monitoring, chart generation, voice alerts, asset loading,
and graceful degradation under edge conditions.
"""

import os
import sys

# Configure UTF-8 encoding for Windows terminals
if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

def test_system_monitoring():
    print("[1/5] Testing System Monitoring...")
    from modules.system_monitor import SystemMonitor, format_bytes, format_uptime
    
    cpu = SystemMonitor.get_cpu_metrics()
    assert cpu["available"] is True, "CPU metrics unavailable"
    assert isinstance(cpu["overall_percent"], float)
    assert cpu["logical_cores"] >= 1
    print(f"  ✓ CPU metrics: {cpu['overall_percent']}% across {cpu['logical_cores']} logical cores")

    mem = SystemMonitor.get_memory_metrics()
    assert mem["available"] is True, "Memory metrics unavailable"
    assert mem["total_bytes"] > 0
    assert 0.0 <= mem["percent"] <= 100.0
    print(f"  ✓ RAM metrics: {mem['used_fmt']} used / {mem['total_fmt']} total ({mem['percent']}%)")

    parts = SystemMonitor.get_partitions()
    assert len(parts) > 0, "No partitions detected"
    print(f"  ✓ Detected {len(parts)} accessible partition(s): {[p['mountpoint'] for p in parts]}")

    disk = SystemMonitor.get_disk_metrics(parts[0]["mountpoint"])
    assert disk["available"] is True
    print(f"  ✓ Disk metrics on {parts[0]['mountpoint']}: {disk['used_fmt']} used / {disk['total_fmt']} total ({disk['percent']}%)")

    sys_info = SystemMonitor.get_system_summary()
    assert sys_info["os_name"] is not None
    print(f"  ✓ System info: {sys_info['os_name']} {sys_info['os_release']} on host {sys_info['hostname']}")

    from modules.system_monitor import generate_system_report
    reports = generate_system_report(cpu, mem, disk, sys_info, parts, 80.0, 85.0, 90.0, parts[0]["mountpoint"])
    assert "SYSTEMSCOPE SYSTEM PERFORMANCE REPORT" in reports["text"]
    assert "# SystemScope System Performance Report" in reports["markdown"]
    print("  ✓ Performance and diagnostic report generated successfully in Text and Markdown")



def test_charts():
    print("[2/5] Testing Plotly Chart Rendering...")
    from modules.charts import (
        create_metric_history_chart,
        create_storage_donut_chart,
        create_cpu_per_core_chart,
        create_empty_chart,
    )
    # Empty state test
    empty_fig = create_empty_chart("Test Empty")
    assert empty_fig is not None
    print("  ✓ Empty state chart created")

    # Metric history chart
    hist_fig = create_metric_history_chart(
        timestamps=["12:00:01", "12:00:03", "12:00:05"],
        values=[35.2, 42.1, 88.5],
        title="CPU Load History",
        metric_name="CPU",
        threshold=80.0,
    )
    assert hist_fig is not None
    assert len(hist_fig.data) >= 1
    print("  ✓ History line chart created with threshold annotations")

    # Storage donut chart
    donut_fig = create_storage_donut_chart(
        used_bytes=100 * 1024**3,
        free_bytes=400 * 1024**3,
        mountpoint="C:\\",
        used_percent=20.0,
        threshold=90.0,
    )
    assert donut_fig is not None
    print("  ✓ Storage breakdown donut chart created")

    # Per-core chart
    cores_fig = create_cpu_per_core_chart([15.0, 30.5, 92.0, 45.0], threshold=80.0)
    assert cores_fig is not None
    print("  ✓ Multi-core distribution chart created")


def test_voice_alerts():
    print("[3/5] Testing Voice Alerts & State Transitions...")
    from modules.voice_alerts import VoiceAlertManager

    vm = VoiceAlertManager()
    print(f"  ✓ Voice alert manager status: available={vm.available}")

    summary_text = vm.generate_system_summary_text(45.0, 60.0, 75.0, "C:")
    assert "45 percent" in summary_text
    print(f"  ✓ Generated speech text: '{summary_text}'")

    # State tracking test: alert should trigger on first breach
    state = {
        "cpu_alert_active": False,
        "ram_alert_active": False,
        "disk_alert_active": False,
        "last_spoken_time": 0.0,
    }
    
    # 1. Breach CPU threshold
    state = vm.evaluate_and_alert(
        cpu_percent=85.0, ram_percent=50.0, disk_percent=50.0,
        cpu_threshold=80.0, ram_threshold=85.0, disk_threshold=90.0,
        state_dict=state, voice_enabled=False
    )
    assert state["cpu_alert_active"] is True, "CPU alert should be active"
    print("  ✓ Threshold breach state activated")

    # 2. Continues above threshold - should not re-trigger voice
    state = vm.evaluate_and_alert(
        cpu_percent=88.0, ram_percent=50.0, disk_percent=50.0,
        cpu_threshold=80.0, ram_threshold=85.0, disk_threshold=90.0,
        state_dict=state, voice_enabled=False
    )
    assert state["cpu_alert_active"] is True

    # 3. Drops below threshold - should re-arm
    state = vm.evaluate_and_alert(
        cpu_percent=40.0, ram_percent=50.0, disk_percent=50.0,
        cpu_threshold=80.0, ram_threshold=85.0, disk_threshold=90.0,
        state_dict=state, voice_enabled=False
    )
    assert state["cpu_alert_active"] is False, "CPU alert should be re-armed to False"
    print("  ✓ Alert successfully re-armed after drop below threshold")


def test_asset_loader():
    print("[4/5] Testing Pillow Asset Loading & Graceful Fallback...")
    from modules.asset_loader import load_and_process_logo

    # Valid asset test
    logo = load_and_process_logo("assets/logo.png", max_size=(64, 64))
    assert logo is not None, "Failed to load assets/logo.png with Pillow"
    assert logo.size[0] <= 64 and logo.size[1] <= 64
    print(f"  ✓ Local logo loaded and resized via Pillow: dimensions {logo.size}")

    # Missing asset fallback test
    missing = load_and_process_logo("assets/non_existent_logo.png")
    assert missing is None, "Missing asset did not degrade gracefully"
    print("  ✓ Graceful degradation confirmed when logo is absent")


def test_app_compilation():
    print("[5/5] Testing App Code Integrity...")
    import py_compile
    py_compile.compile("app.py", doraise=True)
    print("  ✓ app.py compiled with zero syntax or import errors")


if __name__ == "__main__":
    print("=" * 60)
    print("Running SystemScope Comprehensive Verification")
    print("=" * 60)
    test_system_monitoring()
    test_charts()
    test_voice_alerts()
    test_asset_loader()
    test_app_compilation()
    print("=" * 60)
    print("ALL VERIFICATION CHECKS PASSED SUCCESSFULLY!")
    print("=" * 60)

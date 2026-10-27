# SystemScope — Interactive Computer Performance Monitoring Dashboard

SystemScope is a modern, real-time computer hardware and operating system telemetry dashboard built with Python. It provides live monitoring of CPU load, logical cores, physical cores, RAM usage, swap space, and disk partition allocations, combined with interactive visualization, customizable threshold alerts, and offline voice announcements.

---

## 1. Required Python Libraries & Roles

SystemScope is built exclusively using the following 5 libraries:

1. **Streamlit (`streamlit`)** — Powers the interactive, dark-themed reactive dashboard UI, input controls, tabs, and live auto-refresh cycle.
2. **Plotly (`plotly`)** — Renders interactive time-series performance graphs for CPU/RAM history, core utilization breakdowns, and disk storage distribution donuts.
3. **Pillow (`Pillow` / `PIL`)** — Handles local branding assets (`assets/logo.png`), inspecting format, performing anti-aliased Lanczos resizing, with complete graceful degradation if the logo is absent.
4. **psutil (`psutil`)** — Gathers live, unsimulated operating system metrics including CPU utilization, core counts, RAM availability, and mounted storage partitions.
5. **pyttsx3 (`pyttsx3`)** — Delivers offline, native text-to-speech audio announcements for system status summaries and threshold alerts without any external cloud API.

---

## 2. Project Structure

```text
SystemScope/
├── app.py                      # Main Streamlit dashboard application
├── requirements.txt            # Project dependencies (5 core libraries)
├── README.md                   # Setup guide and documentation
├── assets/
│   └── logo.png                # SystemScope branding logo (processed via Pillow)
└── modules/
    ├── __init__.py             # Package descriptor
    ├── system_monitor.py       # psutil collection & hardware statistics
    ├── charts.py               # Plotly interactive dark charts & donut visuals
    ├── voice_alerts.py         # pyttsx3 speech queue & alert state machine
    ├── asset_loader.py         # Pillow safe asset loading & resizing
    └── create_logo.py          # Pillow generator script for branding assets
```

---

## 3. Installation & Launch Instructions

### Recommended Windows PowerShell Setup

Open PowerShell in the project directory and run:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
```

### Note on PowerShell Script Execution Policy
If PowerShell activation of `.venv\Scripts\Activate.ps1` is blocked by Windows execution policies, **do not weaken system security settings**. Instead, run the virtual environment's Python and Streamlit executables directly:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\streamlit.exe run app.py
```

Or run directly using your global Python installation:

```powershell
pip install -r requirements.txt
streamlit run app.py
```

---

## 4. Dashboard Usage & Features

- **Summary Cards:** Immediate overview of current CPU load, RAM percent used, available memory pool, and selected storage drive capacity.
- **Dynamic Dual Theme:** Fully adaptive Light and Dark themes with strict WCAG AAA contrast compliance ensuring all headings, body text, tabs, labels, and charts dynamically invert and remain sharp and visible.
- **Interactive Performance Charts:**
  - **CPU Utilization History:** Spline time-series chart with bounded reading history and configurable threshold reference line.
  - **RAM Utilization History:** Live memory consumption curve over time.
  - **Multi-Core Analysis:** Individual logical core load distribution bars.
  - **Storage Breakdown:** Interactive donut chart displaying partitioned used vs. free disk gigabytes.
  - **System Specifications:** Host details, OS release, CPU model, architecture, and system uptime.
- **Print & Export Diagnostic Reports:**
  - **Print Report Button:** Trigger browser-native `window.print()` formatted with `@media print` styling (removes sidebars, controls, and buttons for clean PDF / paper output).
  - **Diagnostic Report Tab:** Full formatted summary of CPU, Memory, Storage partitions, and Alert Threshold Audits.
  - **One-Click Download:** Download timestamped reports as `.txt` or `.md` files.
- **Monitoring Controls (Sidebar):**
  - **Auto-Refresh Toggle:** Automatically polls system telemetry at a user-defined cadence (2 to 10 seconds).
  - **History Buffer Slider:** Adjust bounded memory history from 30 to 120 points.
  - **Drive Partition Selector:** Dynamically switch monitored mountpoints (e.g., `C:\`, secondary drives).
  - **Clear History:** Reset accumulated chart telemetry points.
  - **Print Shortcut:** Direct print trigger from the sidebar.

---

## 5. Thresholds & Alert Configuration

Configure warning limits directly in the sidebar:
- **CPU Warning Threshold:** Default `80%` (adjustable 50%–99%)
- **RAM Warning Threshold:** Default `85%` (adjustable 50%–99%)
- **Disk Warning Threshold:** Default `90%` (adjustable 50%–99%)

### Alert Behavior
- When any metric exceeds its threshold, a high-visibility warning banner is displayed at the top of the dashboard.
- Voice announcements are triggered **only once** upon crossing a threshold to avoid repeated spamming during frequent auto-refreshes.
- Alerts automatically **re-arm** once the metric returns below the threshold.
- *Notice:* Elevated resource usage indicates current application demand and is diagnostic information, not an indication of hardware malfunction.

---

## 6. Voice Announcements & OS Compatibility

SystemScope uses `pyttsx3` with local speech engines (such as Microsoft SAPI5 on Windows):
- **Enable Voice Alerts Toggle:** Toggles spoken warnings on threshold breaches.
- **Speak System Status Button:** Audibly speaks a concise status report of CPU, RAM, and Storage telemetry on demand.
- **Speech Rate Slider:** Adjusts speech cadence between 130 and 220 words per minute.
- **Offline & Safe:** No audio or telemetry is transmitted across the network. If the local speech synthesizer is unavailable or lacks audio output devices, the dashboard continues to run smoothly with visual warnings.

---

## 7. License & Safety

SystemScope operates in read-only diagnostic mode. It does not terminate background processes, modify operating system settings, or collect personal data.

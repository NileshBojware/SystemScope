# Antigravity Build Instructions — SystemScope

**Project:** SystemScope — Interactive Computer Performance Monitoring Dashboard Using Python

## Instructions for Antigravity

Build the application in the currently opened project folder. Do not stop after producing a plan or mock-up: implement the project, run available checks, fix errors, and leave it ready to launch.

## 1. Required Python libraries

Use these five libraries for their specified purposes:

1. **Streamlit** — dashboard UI and controls.
2. **Plotly** — interactive charts.
3. **Pillow** — handling local logo/icons or other visual assets.
4. **psutil** — collecting actual computer performance data.
5. **pyttsx3** — offline text-to-speech announcements.

Create `requirements.txt` with these dependencies. Do not replace the required libraries or add unnecessary dependencies.

## 2. Main requirements

Create a polished, modern dashboard with a dark theme, clear typography, balanced spacing, readable cards, and a professional system-monitoring appearance.

Display real local computer information—not hardcoded sample values—including:

- Current CPU usage percentage.
- Total, used, and available RAM.
- RAM usage percentage.
- Total, used, and free storage for an accessible disk/partition.
- Disk storage usage percentage.
- CPU logical core count where available.
- Last-updated time or monitoring status.

Use `psutil` to collect this information. Handle unavailable metrics and unsupported partitions gracefully.

## 3. Dashboard layout

Include:

- **Header:** SystemScope title, subtitle, and monitoring status.
- **Summary cards:** CPU usage, RAM usage, disk usage, and available RAM.
- **Performance charts:** Interactive CPU and RAM history charts using Plotly.
- **Storage view:** Visual breakdown of used versus free disk space.
- **System information:** CPU core count and selected partition.
- **Controls:** Refresh/update control and sensible monitoring settings.
- **Alert settings:** User-adjustable CPU, RAM, and disk warning thresholds.
- **Voice controls:** Enable/disable voice alerts and a “Speak System Status” button.
- **Alerts area:** Clearly show when a configured threshold is exceeded.

Use real, working Streamlit controls. If automatic refresh is implemented, use a compatible method and avoid unnecessary rapid reruns.

## 4. Charts and history

Use Plotly for interactive charts. Maintain a bounded history of recent CPU and RAM readings (for example, the last 60 readings) so memory use does not grow without limit.

- Include axis labels and useful hover details.
- Show a helpful loading/empty state before enough readings are available.
- Keep graphs readable on desktop browser sizes.
- Clearly label percentages and time.

## 5. Alerts

Provide configurable default thresholds:

- CPU: 80%.
- RAM: 85%.
- Disk storage: 90%.

Users must be able to change these defaults.

- Show a visible warning when a current value exceeds its configured threshold.
- Avoid repeated voice announcements for one continuing alert. Use alert-state tracking or a cooldown.
- Re-arm an alert after the value returns below its threshold.
- Keep alert behavior clear and predictable.
- Do not claim that high usage necessarily means the computer is damaged or that the app can automatically improve performance.

## 6. Voice announcements

Use `pyttsx3` for offline speech where the operating system's speech engine supports it.

Implement:

- A voice-alert enable/disable toggle.
- A **Speak System Status** button that reads a concise current summary.
- Short announcements when a configured threshold is crossed and voice alerts are enabled.
- Safe handling if the speech engine is unavailable.

Streamlit can rerun scripts frequently, so prevent repeated announcements on every rerun. Avoid initializing multiple competing speech engines. If voice output is unavailable, keep the dashboard usable and explain the limitation in the UI.

## 7. Pillow and visual assets

Use Pillow meaningfully for local image handling, such as loading/resizing a project logo or preparing an optional visual asset. The application must still work if no logo file exists. Do not require external image URLs or remote assets.

If useful, create a simple local logo asset and process it with Pillow. Do not use Pillow as a substitute for system monitoring or charting.

## 8. Suggested project structure

```text
SystemScope/
├── app.py
├── requirements.txt
├── README.md
├── assets/
│   └── logo.png              # optional
└── modules/
    ├── __init__.py
    ├── system_monitor.py     # psutil collection
    ├── charts.py             # Plotly charts
    └── voice_alerts.py       # pyttsx3 speech and alert control
```

Keep code readable, modular, and commented where helpful. A simpler structure is acceptable if it improves reliability, but retain clear separation between monitoring, charts, and voice logic.

## 9. Reliability and safety

- The app must only read and display system information.
- Do not terminate processes, change system settings, or perform automatic optimization.
- Do not collect or upload personal data.
- Do not use external APIs, cloud services, or downloaded datasets.
- Handle missing packages, unsupported metrics, inaccessible partitions, and voice-engine errors with useful messages.
- Do not silently swallow errors that prevent a feature from working.
- Avoid unsafe use of `eval` or execution of user-entered code.
- Keep the application local by default.

## 10. Testing and verification

After implementation:

1. Check that all required files exist.
2. Verify imports and syntax.
3. Run lightweight checks that are practical in the current environment.
4. Fix errors you discover.
5. If the dashboard can be launched in the environment, launch it or verify startup. If you cannot launch it, state exactly what the user should run.
6. Do not claim that a test passed unless you actually ran it.
7. Check that missing optional image assets and unavailable voice output are handled gracefully.

## 11. README and launch instructions

Write a `README.md` explaining what SystemScope does, the five libraries and their roles, installation, launch instructions, dashboard usage, alert configuration, and OS-dependent voice limitations.

Include these Windows-friendly commands:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
```

If PowerShell activation is blocked, explain that the user can run the environment's Python executable directly or use an appropriate shell; do not ask the user to weaken system security settings.

## 12. Completion checklist

Before declaring the project complete, verify that:

- [ ] The dashboard uses actual `psutil` readings.
- [ ] CPU, RAM, and disk information are displayed.
- [ ] Plotly charts use real readings and bounded history.
- [ ] Thresholds can be changed.
- [ ] Warnings appear when thresholds are exceeded.
- [ ] Voice can be enabled/disabled.
- [ ] The status speech button works when supported by the system.
- [ ] Voice failure does not crash the dashboard.
- [ ] Pillow handles local visual assets without making them mandatory.
- [ ] `requirements.txt` and `README.md` are complete.
- [ ] Launch instructions are correct.
- [ ] No external APIs or datasets are required.

**Final instruction:** Implement the actual working project in this folder. Prioritize correctness and usability over decorative effects. At the end, provide a concise summary of files created, checks actually performed, and the exact command needed to launch SystemScope.

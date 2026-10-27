"""
SystemScope — Interactive Computer Performance Monitoring Dashboard
Built with Streamlit, Plotly, Pillow, psutil, and pyttsx3.
Real-time telemetry, interactive visualization, customizable threshold alerts,
dual Light & Dark themes, and offline voice announcements.
"""

import time
from datetime import datetime
from collections import deque
import streamlit as st

# Import core modules
from modules.system_monitor import SystemMonitor, format_bytes, generate_system_report
from modules.charts import (
    create_metric_history_chart,
    create_storage_donut_chart,
    create_cpu_per_core_chart,
)
from modules.voice_alerts import VoiceAlertManager
from modules.asset_loader import load_and_process_logo
import streamlit.components.v1 as components

# ---------------------------------------------------------
# Streamlit Page Configuration
# ---------------------------------------------------------
st.set_page_config(
    page_title="SystemScope — Performance Monitor",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------
# Session State Initialization
# ---------------------------------------------------------
if "theme_mode" not in st.session_state:
    st.session_state.theme_mode = "☀️ Light"

if "history_timestamps" not in st.session_state:
    st.session_state.history_timestamps = deque(maxlen=60)
    st.session_state.history_cpu = deque(maxlen=60)
    st.session_state.history_ram = deque(maxlen=60)

if "alert_states" not in st.session_state:
    st.session_state.alert_states = {
        "cpu_alert_active": False,
        "ram_alert_active": False,
        "disk_alert_active": False,
        "last_spoken_time": 0.0,
    }

if "last_refresh_time" not in st.session_state:
    st.session_state.last_refresh_time = datetime.now()

if "trigger_print" not in st.session_state:
    st.session_state.trigger_print = False



# ---------------------------------------------------------
# Sidebar Controls & Configuration
# ---------------------------------------------------------
logo_img = load_and_process_logo("assets/logo.png", max_size=(80, 80))

with st.sidebar:
    col_sb_logo, col_sb_title = st.columns([1, 2.5])
    with col_sb_logo:
        if logo_img:
            st.image(logo_img, width=64)
        else:
            st.markdown("### ⚡")
    with col_sb_title:
        st.markdown(
            "### SystemScope\n<span style='color:#64748b;font-size:0.8rem;'>Telemetry & Voice Monitor</span>",
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # Theme Switcher Control
    theme_choice = st.radio(
        "🎨 Dashboard Theme",
        options=["☀️ Light", "🌙 Dark"],
        key="theme_mode",
        horizontal=True,
        help="Select between crisp Light and modern Dark themes",
    )
    is_light = (theme_choice == "☀️ Light")
    active_theme = "light" if is_light else "dark"

    st.markdown("---")

    # Monitoring & Refresh Settings
    st.markdown("#### ⚙️ Monitoring Settings")
    auto_refresh = st.toggle("Enable Auto-Refresh", value=True, help="Periodically poll system telemetry")
    refresh_interval = st.slider("Update Interval (seconds)", min_value=2, max_value=10, value=3, step=1)
    history_limit = st.select_slider("Chart History Buffer (readings)", options=[30, 45, 60, 90, 120], value=60)

    # Adjust deque sizes if changed
    if st.session_state.history_cpu.maxlen != history_limit:
        st.session_state.history_timestamps = deque(st.session_state.history_timestamps, maxlen=history_limit)
        st.session_state.history_cpu = deque(st.session_state.history_cpu, maxlen=history_limit)
        st.session_state.history_ram = deque(st.session_state.history_ram, maxlen=history_limit)

    # Partition selection
    partitions = SystemMonitor.get_partitions()
    partition_options = [p["mountpoint"] for p in partitions]
    selected_mount = st.selectbox("Monitored Disk Partition", options=partition_options, index=0)

    # Manual refresh button
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("🔄 Refresh", use_container_width=True):
            st.session_state.last_refresh_time = datetime.now()

    with col_btn2:
        if st.button("🧹 Clear History", use_container_width=True):
            st.session_state.history_timestamps.clear()
            st.session_state.history_cpu.clear()
            st.session_state.history_ram.clear()
            st.rerun()

    st.markdown("---")

    # Alert Thresholds
    st.markdown("#### 🚨 Warning Thresholds")
    cpu_threshold = st.slider("CPU Warning Threshold (%)", min_value=50, max_value=99, value=80, step=1)
    ram_threshold = st.slider("RAM Warning Threshold (%)", min_value=50, max_value=99, value=85, step=1)
    disk_threshold = st.slider("Disk Warning Threshold (%)", min_value=50, max_value=99, value=90, step=1)

    st.markdown("---")

    # Offline Voice Announcements Settings
    st.markdown("#### 🔊 Voice Controls (pyttsx3)")
    voice_manager = VoiceAlertManager()

    if voice_manager.available:
        voice_enabled = st.toggle("Enable Voice Alerts", value=True, help="Speaks alerts once when threshold is breached")
        voice_speed = st.slider("Speech Rate (WPM)", min_value=130, max_value=220, value=175, step=5)
        voice_manager.speech_rate = voice_speed

        btn_speech_summary = st.button("🎙️ Speak System Status", use_container_width=True)
        btn_test_voice = st.button("🧪 Test Voice Audio", use_container_width=True)

        st.caption("🟢 Voice Engine: SAPI5 Offline Active")
    else:
        voice_enabled = False
        btn_speech_summary = False
        btn_test_voice = False
        st.caption(f"⚠️ Voice Engine Unavailable: {voice_manager.engine_error or 'Not supported'}")

    st.markdown("---")

    # Reporting & Export
    st.markdown("#### 🖨️ System Report")
    if st.button("🖨️ Print Performance Report", use_container_width=True, key="btn_sb_print"):
        st.session_state.trigger_print = True

    st.markdown("---")
    st.caption("SystemScope v1.0 • Antigravity Python Monitor\nLocal diagnostics only.")



# ---------------------------------------------------------
# Dynamic CSS Injection Based on Selected Theme
# ---------------------------------------------------------
if is_light:
    THEME_CSS = """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;700&display=swap');

        /* Global base typography and background */
        html, body, [class*="css"], .stApp {
            font-family: 'Inter', -apple-system, sans-serif !important;
            background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 50%, #e2e8f0 100%) !important;
            color: #0f172a !important;
        }

        /* Headings: Deep dark slate for maximum contrast */
        h1, h2, h3, h4, h5, h6,
        [data-testid="stMarkdownContainer"] h1,
        [data-testid="stMarkdownContainer"] h2,
        [data-testid="stMarkdownContainer"] h3,
        [data-testid="stMarkdownContainer"] h4,
        [data-testid="stMarkdownContainer"] h5,
        [data-testid="stMarkdownContainer"] h6 {
            color: #0f172a !important;
            font-weight: 800 !important;
            letter-spacing: -0.01em;
        }

        /* Body text, markdown paragraphs, spans, lists */
        p, span, li, strong, b,
        [data-testid="stMarkdownContainer"] p,
        [data-testid="stMarkdownContainer"] span,
        [data-testid="stMarkdownContainer"] li,
        [data-testid="stMarkdownContainer"] strong,
        [data-testid="stMarkdownContainer"] b,
        [data-testid="stText"] {
            color: #0f172a !important;
        }

        /* Form Controls & Widget Labels (Sliders, Selectboxes, Toggles, Radios) */
        label,
        [data-testid="stWidgetLabel"],
        [data-testid="stWidgetLabel"] p,
        [data-testid="stWidgetLabel"] label,
        [data-testid="stWidgetLabel"] span,
        .stSlider label,
        .stSelectbox label,
        .stToggle label,
        .stRadio label {
            color: #0f172a !important;
            font-weight: 700 !important;
            font-size: 0.92rem !important;
        }

        /* Slider thumb and min/max numbers */
        div[data-testid="stThumbValue"],
        div[data-testid="stTickBar"] span {
            color: #0f172a !important;
            font-weight: 700 !important;
        }

        /* Radio options */
        [data-testid="stRadio"] div[role="radiogroup"] label span {
            color: #0f172a !important;
            font-weight: 600 !important;
        }

        /* Captions and subtext */
        [data-testid="stCaptionContainer"],
        [data-testid="stCaptionContainer"] p,
        .stCaption,
        small {
            color: #1e293b !important;
            font-weight: 600 !important;
        }

        /* Sidebar Styling */
        [data-testid="stSidebar"] {
            background-color: #ffffff !important;
            border-right: 1px solid #cbd5e1 !important;
        }
        [data-testid="stSidebar"] h1,
        [data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] h3,
        [data-testid="stSidebar"] h4,
        [data-testid="stSidebar"] p,
        [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] span {
            color: #0f172a !important;
        }
        [data-testid="stSidebar"] [data-testid="stCaptionContainer"] p {
            color: #334155 !important;
            font-weight: 600 !important;
        }

        /* Metric Cards */
        .metric-card {
            background: #ffffff !important;
            border: 1px solid #cbd5e1 !important;
            border-radius: 12px;
            padding: 18px 20px;
            box-shadow: 0 4px 16px rgba(15, 23, 42, 0.06), 0 1px 3px rgba(15, 23, 42, 0.04);
            transition: transform 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease;
        }
        .metric-card:hover {
            transform: translateY(-2px);
            border-color: #0284c7 !important;
            box-shadow: 0 8px 24px rgba(15, 23, 42, 0.1);
        }
        .metric-title {
            font-size: 0.84rem;
            font-weight: 800;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: #1e293b !important;
            margin-bottom: 6px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .metric-title span {
            color: #1e293b !important;
        }
        .metric-value {
            font-size: 2.2rem;
            font-weight: 900;
            color: #0f172a !important;
            line-height: 1.1;
            font-family: 'JetBrains Mono', monospace !important;
        }
        .metric-subtitle {
            font-size: 0.85rem;
            color: #334155 !important;
            font-weight: 500;
            margin-top: 6px;
        }
        .metric-subtitle b,
        .metric-subtitle strong {
            color: #0f172a !important;
            font-weight: 800 !important;
        }

        /* Badges */
        .badge-normal {
            background: #dcfce7 !important;
            color: #15803d !important;
            border: 1px solid #86efac !important;
            padding: 3px 10px;
            border-radius: 9999px;
            font-size: 0.74rem;
            font-weight: 800;
        }
        .badge-warning {
            background: #fee2e2 !important;
            color: #991b1b !important;
            border: 1px solid #fca5a5 !important;
            padding: 3px 10px;
            border-radius: 9999px;
            font-size: 0.74rem;
            font-weight: 800;
        }

        /* Status Pill */
        .status-pill {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 6px 16px;
            border-radius: 20px;
            font-size: 0.84rem;
            font-weight: 800;
            background: #ffffff !important;
            border: 1px solid #94a3b8 !important;
            color: #0f172a !important;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
        }
        .status-pill span {
            color: #0f172a !important;
            font-weight: 800 !important;
        }
        .pulse-dot {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background-color: #10b981;
            box-shadow: 0 0 8px #10b981;
        }

        /* Alert Banners */
        .alert-banner-warning {
            background: #fef2f2 !important;
            border-left: 5px solid #dc2626 !important;
            border-radius: 8px;
            padding: 14px 18px;
            margin-bottom: 12px;
            color: #991b1b !important;
            font-weight: 600;
            box-shadow: 0 2px 8px rgba(220, 38, 38, 0.08);
        }
        .alert-banner-warning b,
        .alert-banner-warning strong {
            color: #7f1d1d !important;
            font-weight: 800 !important;
        }
        .alert-banner-ok {
            background: #ecfdf5 !important;
            border-left: 5px solid #059669 !important;
            border-radius: 8px;
            padding: 12px 18px;
            margin-bottom: 12px;
            color: #065f46 !important;
            font-weight: 600;
            box-shadow: 0 2px 8px rgba(5, 150, 105, 0.08);
        }
        .alert-banner-ok b,
        .alert-banner-ok strong {
            color: #064e3b !important;
            font-weight: 800 !important;
        }

        /* Tabs in Light Mode */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
            background-color: #e2e8f0 !important;
            padding: 6px;
            border-radius: 10px;
            border: 1px solid #cbd5e1 !important;
        }
        .stTabs [data-baseweb="tab"] {
            border-radius: 6px;
            color: #1e293b !important;
            font-weight: 700 !important;
            font-size: 0.92rem !important;
            padding: 8px 18px;
        }
        .stTabs [data-baseweb="tab"] p,
        .stTabs [data-baseweb="tab"] span {
            color: #1e293b !important;
            font-weight: 700 !important;
        }
        .stTabs [data-baseweb="tab"]:hover {
            color: #0284c7 !important;
            background-color: rgba(255, 255, 255, 0.8) !important;
        }
        .stTabs [aria-selected="true"] {
            background-color: #ffffff !important;
            color: #0284c7 !important;
            font-weight: 800 !important;
            box-shadow: 0 2px 8px rgba(15, 23, 42, 0.08) !important;
            border: 1px solid #cbd5e1 !important;
        }
        .stTabs [aria-selected="true"] p,
        .stTabs [aria-selected="true"] span {
            color: #0284c7 !important;
            font-weight: 800 !important;
        }

        /* Buttons in Light Mode: Crisp white background, dark text, clean border (NO BLACK BOXES) */
        button,
        .stButton > button,
        div[data-testid="stButton"] > button,
        .stDownloadButton > button,
        div[data-testid="stDownloadButton"] > button,
        button[kind="secondary"],
        button[kind="primary"] {
            background-color: #ffffff !important;
            color: #0f172a !important;
            border: 1.5px solid #cbd5e1 !important;
            border-radius: 8px !important;
            font-weight: 700 !important;
            box-shadow: 0 1px 4px rgba(15, 23, 42, 0.08) !important;
            transition: all 0.2s ease !important;
        }
        button p,
        button span,
        button div,
        .stButton > button p,
        .stButton > button span,
        .stButton > button div,
        .stDownloadButton > button p,
        .stDownloadButton > button span {
            color: #0f172a !important;
            font-weight: 700 !important;
        }
        button:hover,
        .stButton > button:hover,
        div[data-testid="stButton"] > button:hover,
        .stDownloadButton > button:hover,
        div[data-testid="stDownloadButton"] > button:hover {
            background-color: #f1f5f9 !important;
            border-color: #0284c7 !important;
            color: #0284c7 !important;
            box-shadow: 0 4px 12px rgba(2, 132, 199, 0.15) !important;
        }
        button:hover p,
        button:hover span,
        .stButton > button:hover p,
        .stButton > button:hover span,
        .stDownloadButton > button:hover p,
        .stDownloadButton > button:hover span {
            color: #0284c7 !important;
        }

        /* Selectbox in Light Mode: Crisp white input box, dark text, dark arrow */
        div[data-baseweb="select"],
        div[data-baseweb="select"] > div,
        [data-testid="stSelectbox"] div[data-baseweb="select"] > div {
            background-color: #ffffff !important;
            color: #0f172a !important;
            border: 1.5px solid #cbd5e1 !important;
            border-radius: 8px !important;
            box-shadow: 0 1px 4px rgba(15, 23, 42, 0.06) !important;
        }
        div[data-baseweb="select"] span,
        div[data-baseweb="select"] div,
        div[data-baseweb="select"] p,
        [data-testid="stSelectbox"] span,
        [data-testid="stSelectbox"] div,
        [data-testid="stSelectbox"] p {
            color: #0f172a !important;
            font-weight: 700 !important;
        }
        div[data-baseweb="select"] svg {
            fill: #0f172a !important;
            color: #0f172a !important;
        }
        div[data-baseweb="select"]:hover > div {
            border-color: #0284c7 !important;
        }
        ul[role="listbox"],
        div[data-baseweb="popover"],
        div[data-baseweb="menu"] {
            background-color: #ffffff !important;
            border: 1px solid #cbd5e1 !important;
            border-radius: 8px !important;
            box-shadow: 0 10px 25px rgba(15, 23, 42, 0.15) !important;
        }
        li[role="option"],
        li[role="option"] span,
        li[role="option"] div {
            background-color: #ffffff !important;
            color: #0f172a !important;
            font-weight: 600 !important;
        }
        li[role="option"]:hover,
        li[role="option"][aria-selected="true"] {
            background-color: #f1f5f9 !important;
            color: #0284c7 !important;
        }
        li[role="option"]:hover span,
        li[role="option"][aria-selected="true"] span {
            color: #0284c7 !important;
        }

        /* Printable Media Styles */
        @media print {
            [data-testid="stSidebar"],
            [data-testid="collapsedControl"],
            header,
            .stButton,
            button,
            .no-print {
                display: none !important;
            }
            body, .stApp {
                background: #ffffff !important;
                color: #000000 !important;
            }
            .stApp > div {
                max-width: 100% !important;
                padding: 0 !important;
            }
            .metric-card {
                border: 1px solid #1e293b !important;
                background: #ffffff !important;
                box-shadow: none !important;
                break-inside: avoid;
                page-break-inside: avoid;
            }
            .metric-title, .metric-value, .metric-subtitle, p, span, h1, h2, h3, h4, div {
                color: #000000 !important;
            }
            .print-report-header {
                display: block !important;
                border-bottom: 2px solid #000000;
                padding-bottom: 12px;
                margin-bottom: 20px;
            }
        }
        @media screen {
            .print-report-header {
                display: none !important;
            }
        }
    </style>
    """
else:
    THEME_CSS = """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;700&display=swap');

        html, body, [class*="css"], .stApp {
            font-family: 'Inter', -apple-system, sans-serif !important;
            background: radial-gradient(circle at 10% 10%, #0d1527 0%, #080c14 100%) !important;
            color: #f1f5f9 !important;
        }

        h1, h2, h3, h4, h5, h6,
        [data-testid="stMarkdownContainer"] h1,
        [data-testid="stMarkdownContainer"] h2,
        [data-testid="stMarkdownContainer"] h3,
        [data-testid="stMarkdownContainer"] h4,
        [data-testid="stMarkdownContainer"] h5,
        [data-testid="stMarkdownContainer"] h6 {
            color: #f8fafc !important;
            font-weight: 800 !important;
            letter-spacing: -0.01em;
        }

        p, span, div, li, strong, b,
        [data-testid="stMarkdownContainer"] p,
        [data-testid="stMarkdownContainer"] span,
        [data-testid="stMarkdownContainer"] li,
        [data-testid="stMarkdownContainer"] strong,
        [data-testid="stMarkdownContainer"] b,
        [data-testid="stText"] {
            color: #f1f5f9 !important;
        }

        label,
        [data-testid="stWidgetLabel"],
        [data-testid="stWidgetLabel"] p,
        [data-testid="stWidgetLabel"] label,
        [data-testid="stWidgetLabel"] span,
        .stSlider label,
        .stSelectbox label,
        .stToggle label,
        .stRadio label {
            color: #f1f5f9 !important;
            font-weight: 600 !important;
        }

        div[data-testid="stThumbValue"],
        div[data-testid="stTickBar"] span {
            color: #f8fafc !important;
            font-weight: 700 !important;
        }

        [data-testid="stRadio"] div[role="radiogroup"] label span {
            color: #f1f5f9 !important;
            font-weight: 500 !important;
        }

        [data-testid="stCaptionContainer"],
        [data-testid="stCaptionContainer"] p,
        .stCaption,
        small {
            color: #94a3b8 !important;
        }

        [data-testid="stSidebar"] {
            background-color: #0b1120 !important;
            border-right: 1px solid rgba(56, 189, 248, 0.2) !important;
        }
        [data-testid="stSidebar"] h1,
        [data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] h3,
        [data-testid="stSidebar"] h4,
        [data-testid="stSidebar"] p,
        [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] span {
            color: #f1f5f9 !important;
        }
        [data-testid="stSidebar"] [data-testid="stCaptionContainer"] p {
            color: #94a3b8 !important;
        }

        .metric-card {
            background: rgba(17, 24, 39, 0.85) !important;
            border: 1px solid rgba(56, 189, 248, 0.25) !important;
            border-radius: 12px;
            padding: 18px 20px;
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.35);
            backdrop-filter: blur(12px);
            transition: transform 0.2s ease, border-color 0.2s ease;
        }
        .metric-card:hover {
            transform: translateY(-2px);
            border-color: rgba(56, 189, 248, 0.5) !important;
        }
        .metric-title {
            font-size: 0.84rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: #94a3b8 !important;
            margin-bottom: 6px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .metric-title span {
            color: #94a3b8 !important;
        }
        .metric-value {
            font-size: 2.2rem;
            font-weight: 900;
            color: #f8fafc !important;
            line-height: 1.1;
            font-family: 'JetBrains Mono', monospace !important;
        }
        .metric-subtitle {
            font-size: 0.85rem;
            color: #94a3b8 !important;
            margin-top: 6px;
        }
        .metric-subtitle b,
        .metric-subtitle strong {
            color: #f1f5f9 !important;
        }

        .badge-normal {
            background: rgba(16, 185, 129, 0.15) !important;
            color: #34d399 !important;
            border: 1px solid rgba(16, 185, 129, 0.3) !important;
            padding: 3px 10px;
            border-radius: 9999px;
            font-size: 0.74rem;
            font-weight: 700;
        }
        .badge-warning {
            background: rgba(239, 68, 68, 0.15) !important;
            color: #f87171 !important;
            border: 1px solid rgba(239, 68, 68, 0.3) !important;
            padding: 3px 10px;
            border-radius: 9999px;
            font-size: 0.74rem;
            font-weight: 700;
        }

        .status-pill {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 6px 16px;
            border-radius: 20px;
            font-size: 0.84rem;
            font-weight: 700;
            background: rgba(30, 41, 59, 0.9) !important;
            border: 1px solid rgba(148, 163, 184, 0.3) !important;
            color: #f1f5f9 !important;
        }
        .status-pill span {
            color: #f1f5f9 !important;
        }
        .pulse-dot {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background-color: #10b981;
            box-shadow: 0 0 10px #10b981;
        }

        .alert-banner-warning {
            background: rgba(239, 68, 68, 0.15) !important;
            border-left: 5px solid #ef4444 !important;
            border-radius: 8px;
            padding: 14px 18px;
            margin-bottom: 12px;
            color: #fecaca !important;
            font-weight: 500;
        }
        .alert-banner-ok {
            background: rgba(16, 185, 129, 0.12) !important;
            border-left: 5px solid #10b981 !important;
            border-radius: 8px;
            padding: 12px 18px;
            margin-bottom: 12px;
            color: #a7f3d0 !important;
            font-weight: 500;
        }

        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
            background-color: rgba(15, 23, 42, 0.8) !important;
            padding: 6px;
            border-radius: 10px;
            border: 1px solid rgba(51, 65, 85, 0.7) !important;
        }
        .stTabs [data-baseweb="tab"] {
            border-radius: 6px;
            color: #94a3b8 !important;
            font-weight: 600 !important;
            padding: 8px 18px;
        }
        .stTabs [data-baseweb="tab"] p,
        .stTabs [data-baseweb="tab"] span {
            color: #94a3b8 !important;
            font-weight: 600 !important;
        }
        .stTabs [aria-selected="true"] {
            background-color: rgba(56, 189, 248, 0.2) !important;
            color: #38bdf8 !important;
            font-weight: 800 !important;
            border: 1px solid rgba(56, 189, 248, 0.4) !important;
        }
        .stTabs [aria-selected="true"] p,
        .stTabs [aria-selected="true"] span {
            color: #38bdf8 !important;
            font-weight: 800 !important;
        }

        /* Buttons in Dark Mode: Slate-800 background, crisp white text, cyan border */
        button,
        .stButton > button,
        div[data-testid="stButton"] > button,
        .stDownloadButton > button,
        div[data-testid="stDownloadButton"] > button,
        button[kind="secondary"],
        button[kind="primary"] {
            background-color: #1e293b !important;
            color: #f8fafc !important;
            border: 1.5px solid rgba(56, 189, 248, 0.35) !important;
            border-radius: 8px !important;
            font-weight: 700 !important;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3) !important;
            transition: all 0.2s ease !important;
        }
        button p,
        button span,
        button div,
        .stButton > button p,
        .stButton > button span,
        .stButton > button div,
        .stDownloadButton > button p,
        .stDownloadButton > button span {
            color: #f8fafc !important;
            font-weight: 700 !important;
        }
        button:hover,
        .stButton > button:hover,
        div[data-testid="stButton"] > button:hover,
        .stDownloadButton > button:hover,
        div[data-testid="stDownloadButton"] > button:hover {
            background-color: rgba(56, 189, 248, 0.2) !important;
            border-color: #38bdf8 !important;
            color: #38bdf8 !important;
            box-shadow: 0 0 15px rgba(56, 189, 248, 0.25) !important;
        }
        button:hover p,
        button:hover span,
        .stButton > button:hover p,
        .stButton > button:hover span,
        .stDownloadButton > button:hover p,
        .stDownloadButton > button:hover span {
            color: #38bdf8 !important;
        }

        /* Selectbox in Dark Mode */
        div[data-baseweb="select"],
        div[data-baseweb="select"] > div,
        [data-testid="stSelectbox"] div[data-baseweb="select"] > div {
            background-color: #1e293b !important;
            color: #f8fafc !important;
            border: 1.5px solid rgba(56, 189, 248, 0.35) !important;
            border-radius: 8px !important;
        }
        div[data-baseweb="select"] span,
        div[data-baseweb="select"] div,
        div[data-baseweb="select"] p,
        [data-testid="stSelectbox"] span,
        [data-testid="stSelectbox"] div,
        [data-testid="stSelectbox"] p {
            color: #f8fafc !important;
            font-weight: 700 !important;
        }
        div[data-baseweb="select"] svg {
            fill: #38bdf8 !important;
            color: #38bdf8 !important;
        }
        div[data-baseweb="select"]:hover > div {
            border-color: #38bdf8 !important;
        }
        ul[role="listbox"],
        div[data-baseweb="popover"],
        div[data-baseweb="menu"] {
            background-color: #0b1120 !important;
            border: 1px solid rgba(56, 189, 248, 0.3) !important;
            border-radius: 8px !important;
        }
        li[role="option"],
        li[role="option"] span,
        li[role="option"] div {
            background-color: #0b1120 !important;
            color: #f8fafc !important;
            font-weight: 600 !important;
        }
        li[role="option"]:hover,
        li[role="option"][aria-selected="true"] {
            background-color: rgba(56, 189, 248, 0.2) !important;
            color: #38bdf8 !important;
        }
        li[role="option"]:hover span,
        li[role="option"][aria-selected="true"] span {
            color: #38bdf8 !important;
        }

        @media print {
            [data-testid="stSidebar"],
            [data-testid="collapsedControl"],
            header,
            .stButton,
            button,
            .no-print {
                display: none !important;
            }
            body, .stApp {
                background: #ffffff !important;
                color: #000000 !important;
            }
            .stApp > div {
                max-width: 100% !important;
                padding: 0 !important;
            }
            .metric-card {
                border: 1px solid #1e293b !important;
                background: #ffffff !important;
                box-shadow: none !important;
                break-inside: avoid;
                page-break-inside: avoid;
            }
            .metric-title, .metric-value, .metric-subtitle, p, span, h1, h2, h3, h4, div {
                color: #000000 !important;
            }
            .print-report-header {
                display: block !important;
                border-bottom: 2px solid #000000;
                padding-bottom: 12px;
                margin-bottom: 20px;
            }
        }
        @media screen {
            .print-report-header {
                display: none !important;
            }
        }
    </style>
    """

st.markdown(THEME_CSS, unsafe_allow_html=True)


# ---------------------------------------------------------
# Data Collection via psutil
# ---------------------------------------------------------
cpu_data = SystemMonitor.get_cpu_metrics()
ram_data = SystemMonitor.get_memory_metrics()
disk_data = SystemMonitor.get_disk_metrics(selected_mount)
sys_info = SystemMonitor.get_system_summary()

current_time_str = datetime.now().strftime("%H:%M:%S")

# Append readings to bounded history
st.session_state.history_timestamps.append(current_time_str)
st.session_state.history_cpu.append(cpu_data["overall_percent"])
st.session_state.history_ram.append(ram_data["percent"])
st.session_state.last_refresh_time = datetime.now()


# ---------------------------------------------------------
# Voice Alert Evaluation & Trigger Handling
# ---------------------------------------------------------
if voice_manager.available:
    if btn_test_voice:
        voice_manager.speak_async("SystemScope audio check. Voice alerts are operational.")
        st.toast("Playing test audio announcement...", icon="🔊")

    if btn_speech_summary:
        summary_phrase = voice_manager.generate_system_summary_text(
            cpu_percent=cpu_data["overall_percent"],
            ram_percent=ram_data["percent"],
            disk_percent=disk_data["percent"],
            disk_mount=selected_mount,
        )
        voice_manager.speak_async(summary_phrase)
        st.toast("Reading system status summary...", icon="🎙️")

    st.session_state.alert_states = voice_manager.evaluate_and_alert(
        cpu_percent=cpu_data["overall_percent"],
        ram_percent=ram_data["percent"],
        disk_percent=disk_data["percent"],
        cpu_threshold=cpu_threshold,
        ram_threshold=ram_threshold,
        disk_threshold=disk_threshold,
        state_dict=st.session_state.alert_states,
        voice_enabled=voice_enabled,
        cooldown_seconds=45.0,
    )


# ---------------------------------------------------------
# Main Dashboard Header & Quick Actions
# ---------------------------------------------------------
title_color = "#0f172a" if is_light else "#f8fafc"
sub_color = "#1e293b" if is_light else "#94a3b8"
badge_bg = "rgba(2, 132, 199, 0.12)" if is_light else "rgba(56, 189, 248, 0.15)"
badge_border = "rgba(2, 132, 199, 0.4)" if is_light else "rgba(56, 189, 248, 0.3)"
badge_txt = "#0284c7" if is_light else "#38bdf8"
time_color = "#1e293b" if is_light else "#cbd5e1"

# Printable banner visible only on paper/PDF printouts
st.markdown(
    f"""
    <div class="print-report-header">
        <h1 style="margin: 0; color: #000000; font-size: 1.8rem;">SystemScope — System Performance & Telemetry Report</h1>
        <p style="margin: 4px 0 0 0; color: #1e293b; font-size: 0.9rem;">
            Host: <b>{sys_info.get('hostname', 'Localhost')}</b> | OS: <b>{sys_info.get('os_name', 'OS')} {sys_info.get('os_release', '')}</b> | 
            Generated: <b>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</b> | Diagnostic Uptime: <b>{sys_info.get('uptime_fmt', 'N/A')}</b>
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

col_hdr_title, col_hdr_actions, col_hdr_badge = st.columns([2.6, 1.1, 1.3])
with col_hdr_title:
    st.markdown(
        f"""
        <div style="display: flex; align-items: center; gap: 14px; margin-bottom: 4px;">
            <h1 style="margin: 0; font-size: 2.1rem; font-weight: 800; letter-spacing: -0.02em; color: {title_color};">
                SystemScope
            </h1>
            <span style="background: {badge_bg}; color: {badge_txt}; border: 1px solid {badge_border}; padding: 4px 10px; border-radius: 6px; font-size: 0.75rem; font-weight: 700;">
                v1.0 {theme_choice}
            </span>
        </div>
        <p style="margin: 0; color: {sub_color}; font-size: 0.95rem; font-weight: 500;">
            Real-time interactive hardware performance & health dashboard for local machine.
        </p>
        """,
        unsafe_allow_html=True,
    )

with col_hdr_actions:
    st.markdown("<div style='height: 6px;'></div>", unsafe_allow_html=True)
    if st.button("🖨️ Print Report", use_container_width=True, key="btn_hdr_print", help="Open native print / save to PDF dialog"):
        st.session_state.trigger_print = True

with col_hdr_badge:
    status_text = "LIVE POLLING" if auto_refresh else "PAUSED"
    dot_color = "#10b981" if auto_refresh else "#f59e0b"
    st.markdown(
        f"""
        <div style="display: flex; flex-direction: column; align-items: flex-end; justify-content: center; height: 100%;">
            <div class="status-pill">
                <span class="pulse-dot" style="background-color: {dot_color}; box-shadow: 0 0 8px {dot_color};"></span>
                <span>{status_text}</span>
            </div>
            <div style="font-size: 0.78rem; color: {time_color}; margin-top: 6px; font-weight: 600;">
                Updated: <b>{current_time_str}</b> ({len(st.session_state.history_cpu)} readings)
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# Execute print trigger if activated
if st.session_state.get("trigger_print", False):
    st.session_state.trigger_print = False
    components.html(
        """
        <script>
        setTimeout(function() {
            window.parent.focus();
            window.parent.print();
        }, 250);
        </script>
        """,
        height=0,
        width=0,
    )

st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)



# ---------------------------------------------------------
# Threshold Alert Notices Banner
# ---------------------------------------------------------
active_warnings = []
if cpu_data["overall_percent"] >= cpu_threshold:
    active_warnings.append(f"<b>CPU Threshold Exceeded:</b> Current load is <b>{cpu_data['overall_percent']:.1f}%</b> (Warning limit: {cpu_threshold}%)")
if ram_data["percent"] >= ram_threshold:
    active_warnings.append(f"<b>Memory Threshold Exceeded:</b> Current RAM load is <b>{ram_data['percent']:.1f}%</b> (Warning limit: {ram_threshold}%)")
if disk_data["percent"] >= disk_threshold:
    active_warnings.append(f"<b>Storage Threshold Exceeded:</b> Drive <b>{selected_mount}</b> is at <b>{disk_data['percent']:.1f}%</b> capacity (Warning limit: {disk_threshold}%)")

if active_warnings:
    for warn in active_warnings:
        st.markdown(
            f"""
            <div class="alert-banner-warning">
                ⚠️ {warn}
            </div>
            """,
            unsafe_allow_html=True,
        )
else:
    st.markdown(
        """
        <div class="alert-banner-ok">
            ✅ <b>All Systems Nominal:</b> CPU, Memory, and Disk allocations are operating safely within configured limits.
        </div>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------
# Top Summary Metric Cards
# ---------------------------------------------------------
c_m1, c_m2, c_m3, c_m4 = st.columns(4)
pct_color = "#334155" if is_light else "#94a3b8"

# 1. CPU Card
with c_m1:
    cpu_val = cpu_data["overall_percent"]
    cpu_badge = "badge-warning" if cpu_val >= cpu_threshold else "badge-normal"
    cpu_badge_text = "WARNING" if cpu_val >= cpu_threshold else "NORMAL"
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-title">
                <span>CPU Load</span>
                <span class="{cpu_badge}">{cpu_badge_text}</span>
            </div>
            <div class="metric-value">{cpu_val:.1f}<span style="font-size:1.1rem;color:{pct_color};font-weight:700;">%</span></div>
            <div class="metric-subtitle">
                {cpu_data.get('logical_cores', 1)} Logical Cores • {cpu_data.get('freq_current_mhz', 'N/A')} MHz
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# 2. RAM Card
with c_m2:
    ram_val = ram_data["percent"]
    ram_badge = "badge-warning" if ram_val >= ram_threshold else "badge-normal"
    ram_badge_text = "WARNING" if ram_val >= ram_threshold else "NORMAL"
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-title">
                <span>RAM Usage</span>
                <span class="{ram_badge}">{ram_badge_text}</span>
            </div>
            <div class="metric-value">{ram_val:.1f}<span style="font-size:1.1rem;color:{pct_color};font-weight:700;">%</span></div>
            <div class="metric-subtitle">
                Used: <b>{ram_data['used_fmt']}</b> / {ram_data['total_fmt']}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# 3. Available RAM Card
with c_m3:
    avail_gb = ram_data["available_fmt"]
    val_color = "#0284c7" if is_light else "#38bdf8"
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-title">
                <span>Available RAM</span>
                <span class="badge-normal">FREE POOL</span>
            </div>
            <div class="metric-value" style="color: {val_color};">{avail_gb}</div>
            <div class="metric-subtitle">
                Swap Used: {ram_data.get('swap_used_fmt', '0 B')} ({ram_data.get('swap_percent', 0.0):.1f}%)
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# 4. Disk Storage Card
with c_m4:
    disk_val = disk_data["percent"]
    disk_badge = "badge-warning" if disk_val >= disk_threshold else "badge-normal"
    disk_badge_text = "WARNING" if disk_val >= disk_threshold else "NORMAL"
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-title">
                <span>Storage ({selected_mount})</span>
                <span class="{disk_badge}">{disk_badge_text}</span>
            </div>
            <div class="metric-value">{disk_val:.1f}<span style="font-size:1.1rem;color:{pct_color};font-weight:700;">%</span></div>
            <div class="metric-subtitle">
                Free: <b>{disk_data['free_fmt']}</b> of {disk_data['total_fmt']}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("<div style='height: 18px;'></div>", unsafe_allow_html=True)


# ---------------------------------------------------------
# Interactive Telemetry Tabs (Charts & System Insights)
# ---------------------------------------------------------
tab_charts, tab_cores, tab_storage, tab_system, tab_report = st.tabs([
    "📈 Performance History",
    "⚙️ Multi-Core Analysis",
    "💾 Storage & Disks",
    "ℹ️ System Specifications",
    "🖨️ Diagnostic Report & Print",
])

with tab_charts:
    st.markdown("<div style='height: 4px;'></div>", unsafe_allow_html=True)
    c_chart1, c_chart2 = st.columns(2)

    with c_chart1:
        cpu_fig = create_metric_history_chart(
            timestamps=list(st.session_state.history_timestamps),
            values=list(st.session_state.history_cpu),
            title="CPU Utilization History",
            metric_name="CPU Load",
            threshold=float(cpu_threshold),
            theme=active_theme,
        )
        st.plotly_chart(cpu_fig, use_container_width=True)

    with c_chart2:
        ram_line = "#7c3aed" if is_light else "#a855f7"
        ram_fill = "rgba(124, 58, 237, 0.16)" if is_light else "rgba(168, 85, 247, 0.16)"
        ram_fig = create_metric_history_chart(
            timestamps=list(st.session_state.history_timestamps),
            values=list(st.session_state.history_ram),
            title="RAM Utilization History",
            metric_name="RAM Usage",
            line_color=ram_line,
            fill_color=ram_fill,
            threshold=float(ram_threshold),
            theme=active_theme,
        )
        st.plotly_chart(ram_fig, use_container_width=True)

with tab_cores:
    st.markdown("<div style='height: 4px;'></div>", unsafe_allow_html=True)
    cores_fig = create_cpu_per_core_chart(
        per_cpu_percent=cpu_data.get("per_cpu_percent", []),
        threshold=float(cpu_threshold),
        theme=active_theme,
    )
    st.plotly_chart(cores_fig, use_container_width=True)
    
    # Detail table for core loads
    per_cpu = cpu_data.get("per_cpu_percent", [])
    if per_cpu:
        core_cols = st.columns(min(len(per_cpu), 6))
        for idx, val in enumerate(per_cpu):
            col_target = core_cols[idx % len(core_cols)]
            with col_target:
                bar_color = "#dc2626" if val >= cpu_threshold else ("#0284c7" if is_light else "#38bdf8")
                st.caption(f"Core {idx+1}")
                st.progress(min(max(float(val) / 100.0, 0.0), 1.0))
                st.markdown(f"<span style='color:{bar_color};font-weight:700;font-size:0.88rem;'>{val:.1f}%</span>", unsafe_allow_html=True)

with tab_storage:
    st.markdown("<div style='height: 4px;'></div>", unsafe_allow_html=True)
    col_d1, col_d2 = st.columns([1.2, 1])

    with col_d1:
        storage_fig = create_storage_donut_chart(
            used_bytes=disk_data["used_bytes"],
            free_bytes=disk_data["free_bytes"],
            mountpoint=selected_mount,
            used_percent=disk_data["percent"],
            threshold=float(disk_threshold),
            theme=active_theme,
        )
        st.plotly_chart(storage_fig, use_container_width=True)

    with col_d2:
        st.markdown(f"#### Partition Details: `{selected_mount}`")
        st.markdown(
            f"""
            - **Total Capacity:** {disk_data['total_fmt']}
            - **Space Used:** {disk_data['used_fmt']} ({disk_data['percent']:.1f}%)
            - **Free Space Available:** {disk_data['free_fmt']} ({100.0 - disk_data['percent']:.1f}%)
            - **Warning Threshold:** {disk_threshold}%
            - **Status:** {'⚠️ Exceeds Threshold' if disk_data['percent'] >= disk_threshold else '✅ Healthy Allocation'}
            """
        )
        st.markdown("##### Detected Storage Partitions")
        for p in partitions:
            try:
                u = SystemMonitor.get_disk_metrics(p["mountpoint"])
                st.caption(f"**Drive {p['device']}** ({p['fstype']}) — {u['used_fmt']} used / {u['total_fmt']} total ({u['percent']:.1f}%)")
            except Exception:
                st.caption(f"**Drive {p['device']}** ({p['fstype']}) — Mountpoint: {p['mountpoint']}")

with tab_system:
    st.markdown("<div style='height: 4px;'></div>", unsafe_allow_html=True)
    cs1, cs2 = st.columns(2)
    with cs1:
        st.markdown("#### 💻 Operating System & Host")
        st.markdown(f"- **OS:** {sys_info['os_name']} {sys_info['os_release']} ({sys_info['os_version']})")
        st.markdown(f"- **Architecture:** {sys_info['architecture']}")
        st.markdown(f"- **Hostname:** `{sys_info['hostname']}`")
        st.markdown(f"- **System Boot Time:** {sys_info['boot_time']}")
        st.markdown(f"- **System Uptime:** {sys_info['uptime_fmt']}")
    with cs2:
        st.markdown("#### ⚡ Hardware & Memory")
        st.markdown(f"- **Processor:** {sys_info['processor']}")
        st.markdown(f"- **Logical CPU Cores:** {cpu_data.get('logical_cores', 'N/A')}")
        st.markdown(f"- **Physical CPU Cores:** {cpu_data.get('physical_cores', 'N/A')}")
        st.markdown(f"- **Total Physical Memory:** {ram_data['total_fmt']}")
        st.markdown(f"- **Total Swap Memory:** {ram_data.get('swap_total_fmt', 'N/A')}")

with tab_report:
    st.markdown("<div style='height: 4px;'></div>", unsafe_allow_html=True)
    report_data = generate_system_report(
        cpu_data=cpu_data,
        ram_data=ram_data,
        disk_data=disk_data,
        sys_info=sys_info,
        partitions=partitions,
        cpu_threshold=float(cpu_threshold),
        ram_threshold=float(ram_threshold),
        disk_threshold=float(disk_threshold),
        selected_mount=selected_mount,
    )

    st.markdown("### 🖨️ Diagnostic Telemetry Report")
    st.markdown("Generate official system snapshots, print diagnostic records, or save reports locally.")

    col_rep1, col_rep2, col_rep3 = st.columns([1, 1, 1])
    with col_rep1:
        if st.button("🖨️ Print This Report", use_container_width=True, key="btn_tab_print"):
            components.html(
                """
                <script>
                setTimeout(function() {
                    window.parent.focus();
                    window.parent.print();
                }, 200);
                </script>
                """,
                height=0,
                width=0,
            )
    with col_rep2:
        st.download_button(
            "📥 Download Plain Text (.txt)",
            data=report_data["text"],
            file_name=f"SystemScope_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain",
            use_container_width=True,
            key="dl_report_txt",
        )
    with col_rep3:
        st.download_button(
            "📥 Download Markdown (.md)",
            data=report_data["markdown"],
            file_name=f"SystemScope_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
            mime="text/markdown",
            use_container_width=True,
            key="dl_report_md",
        )

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
    st.markdown("#### 📄 Formatted Diagnostic Record")
    st.code(report_data["text"], language="text")


st.markdown("---")

# Disclaimer & Diagnostics Notice
st.caption(
    "💡 **Telemetry Notice:** SystemScope monitors and visualizes local machine telemetry. "
    "Elevated CPU or memory utilization represents momentary operating system demand and is normal under intensive workloads. "
    "SystemScope operates in read-only diagnostic mode."
)


# ---------------------------------------------------------
# Auto-Refresh Execution Loop
# ---------------------------------------------------------
if auto_refresh:
    time.sleep(refresh_interval)
    st.rerun()

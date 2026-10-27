"""
SystemScope - Voice Alerts & Text-to-Speech Module
Provides offline natural speech announcements using pyttsx3.
Includes non-blocking speech queue, Windows COM thread safety,
state tracking to prevent repeated announcements on Streamlit reruns,
and cooldown-based alert re-arming.
"""

import threading
import time
import queue
from typing import Dict, Any, Optional

try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except ImportError:
    pyttsx3 = None
    PYTTSX3_AVAILABLE = False

try:
    import pythoncom
    PYTHONCOM_AVAILABLE = True
except ImportError:
    pythoncom = None
    PYTHONCOM_AVAILABLE = False


class VoiceAlertManager:
    """Manages offline text-to-speech engine and alert state transitions."""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(VoiceAlertManager, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self, speech_rate: int = 175):
        if self._initialized:
            return
        self.speech_rate = speech_rate
        self.available = PYTTSX3_AVAILABLE
        self.engine_error = None
        self._speech_queue = queue.Queue(maxsize=10)
        self._worker_thread = None
        self._is_running = True

        if self.available:
            try:
                # Test basic initialization
                if PYTHONCOM_AVAILABLE:
                    pythoncom.CoInitialize()
                test_eng = pyttsx3.init()
                test_eng.stop()
                self._start_worker()
            except Exception as e:
                self.available = False
                self.engine_error = str(e)
        else:
            self.engine_error = "pyttsx3 library not installed"

        self._initialized = True

    def _start_worker(self):
        """Starts background worker thread to process speech requests sequentially without freezing UI."""
        self._worker_thread = threading.Thread(target=self._speech_worker, daemon=True)
        self._worker_thread.start()

    def _speech_worker(self):
        """Dedicated worker thread for safe speech dispatch."""
        while self._is_running:
            try:
                text = self._speech_queue.get(timeout=1.0)
                if text is None:
                    break

                try:
                    if PYTHONCOM_AVAILABLE:
                        pythoncom.CoInitialize()
                    
                    eng = pyttsx3.init()
                    eng.setProperty("rate", self.speech_rate)
                    eng.setProperty("volume", 1.0)
                    eng.say(text)
                    eng.runAndWait()
                    eng.stop()
                except Exception as exc:
                    self.engine_error = f"Speech dispatch error: {exc}"
                finally:
                    if PYTHONCOM_AVAILABLE:
                        try:
                            pythoncom.CoUninitialize()
                        except Exception:
                            pass
                
                self._speech_queue.task_done()
                time.sleep(0.1)
            except queue.Empty:
                continue
            except Exception:
                pass

    def speak_async(self, text: str) -> bool:
        """Enqueue speech to be spoken asynchronously."""
        if not self.available or not text:
            return False
        try:
            # Drain queue if backed up to avoid stale announcements
            while self._speech_queue.qsize() > 2:
                try:
                    self._speech_queue.get_nowait()
                except queue.Empty:
                    break
            self._speech_queue.put_nowait(text)
            return True
        except queue.Full:
            return False

    def generate_system_summary_text(
        self,
        cpu_percent: float,
        ram_percent: float,
        disk_percent: float,
        disk_mount: str = "C",
    ) -> str:
        """Constructs concise, natural spoken summary of current telemetry."""
        mount_name = disk_mount.replace("\\", "").replace("/", "").strip() or "main drive"
        return (
            f"SystemScope Status Report: "
            f"CPU utilization is at {int(round(cpu_percent))} percent. "
            f"RAM usage is {int(round(ram_percent))} percent. "
            f"Storage usage on drive {mount_name} is {int(round(disk_percent))} percent."
        )

    def evaluate_and_alert(
        self,
        cpu_percent: float,
        ram_percent: float,
        disk_percent: float,
        cpu_threshold: float,
        ram_threshold: float,
        disk_threshold: float,
        state_dict: Dict[str, Any],
        voice_enabled: bool,
        cooldown_seconds: float = 45.0,
    ) -> Dict[str, Any]:
        """
        Evaluates metrics against user thresholds.
        Tracks state transitions so voice alerts only fire once when a threshold
        is breached, and are re-armed only after the value drops back below threshold.
        """
        current_time = time.time()
        spoken_events = []

        # Ensure state_dict has required fields
        state_dict.setdefault("cpu_alert_active", False)
        state_dict.setdefault("ram_alert_active", False)
        state_dict.setdefault("disk_alert_active", False)
        state_dict.setdefault("last_spoken_time", 0.0)

        # 1. CPU Alert evaluation
        if cpu_percent >= cpu_threshold:
            if not state_dict["cpu_alert_active"]:
                state_dict["cpu_alert_active"] = True
                spoken_events.append(f"Warning: CPU usage has reached {int(round(cpu_percent))} percent.")
        else:
            # Re-arm alert when back to normal
            state_dict["cpu_alert_active"] = False

        # 2. RAM Alert evaluation
        if ram_percent >= ram_threshold:
            if not state_dict["ram_alert_active"]:
                state_dict["ram_alert_active"] = True
                spoken_events.append(f"Notice: Memory usage has reached {int(round(ram_percent))} percent.")
        else:
            state_dict["ram_alert_active"] = False

        # 3. Disk Alert evaluation
        if disk_percent >= disk_threshold:
            if not state_dict["disk_alert_active"]:
                state_dict["disk_alert_active"] = True
                spoken_events.append(f"Notice: Disk storage usage has reached {int(round(disk_percent))} percent.")
        else:
            state_dict["disk_alert_active"] = False

        # If any new alerts were triggered and voice is enabled and cooldown passed
        if spoken_events and voice_enabled and self.available:
            if (current_time - state_dict["last_spoken_time"]) >= cooldown_seconds:
                announcement = " Attention: " + " ".join(spoken_events)
                self.speak_async(announcement)
                state_dict["last_spoken_time"] = current_time

        return state_dict

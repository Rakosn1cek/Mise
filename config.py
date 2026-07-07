import os
import json
import sys
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QCheckBox

CONFIG_PATH = os.path.expanduser("~/.config/mise/config.json")

DEFAULT_CONFIG = {
    "disable_gpu": True,
    "background_throttling": True,
    "process_limit": 3,
    "enable_notifications": True
}

def load_config():
    if not os.path.exists(CONFIG_PATH):
        return DEFAULT_CONFIG.copy()
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            user_data = json.load(f)
            # Ensure missing flags fall back to safe defaults if config is older
            fallback_data = DEFAULT_CONFIG.copy()
            fallback_data.update(user_data)
            return fallback_data
    except Exception:
        return DEFAULT_CONFIG.copy()

def save_config(config_data):
    try:
        os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=4)
    except Exception:
        pass


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setFixedWidth(400)
        self.setObjectName("SettingsWindow")
        
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.current_config = load_config()
        
        layout = QVBoxLayout()
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)
        
        header = QLabel("Hardware & Optimization Settings")
        header.setStyleSheet("font-weight: bold; color: #2ac3de; font-size: 14px; background: transparent;")
        layout.addWidget(header)
        
        # Individual checkbox allocations for precise flag mapping
        self.gpu_check = QCheckBox("Disable Hardware Acceleration (GPU)")
        self.throttle_check = QCheckBox("Enable Background Timer Throttling")
        self.noti_check = QCheckBox("Enable System Notifications Component")
        
        # Apply structural stylesheet overrides directly to check boxes
        checkbox_style = "color: #c0caf5; background: transparent; padding: 2px;"
        for cb in (self.gpu_check, self.throttle_check, self.noti_check):
            cb.setStyleSheet(checkbox_style)
            layout.addWidget(cb)
            
        # Set active visual states based on active disk configuration values
        self.gpu_check.setChecked(self.current_config.get("disable_gpu", True))
        self.throttle_check.setChecked(self.current_config.get("background_throttling", True))
        self.noti_check.setChecked(self.current_config.get("enable_notifications", True))
        
        action_layout = QHBoxLayout()
        action_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet("background-color: transparent; color: #c0caf5; border: 1px solid #24283b; padding: 6px 12px; border-radius: 4px;")
        cancel_btn.clicked.connect(self.reject)
        action_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton("Save Settings")
        save_btn.setStyleSheet("background-color: #364a85; color: #c0caf5; border: 1px solid #2ac3de; padding: 6px 12px; border-radius: 4px;")
        save_btn.clicked.connect(self.collect_and_accept)
        action_layout.addWidget(save_btn)
        
        layout.addLayout(action_layout)
        self.setLayout(layout)
        
    def collect_and_accept(self):
        self.current_config["disable_gpu"] = self.gpu_check.isChecked()
        self.current_config["background_throttling"] = self.throttle_check.isChecked()
        self.current_config["enable_notifications"] = self.noti_check.isChecked()
        
        if self.throttle_check.isChecked():
            self.current_config["process_limit"] = 3
        else:
            self.current_config["process_limit"] = 6
            
        save_config(self.current_config)
        self.accept()
        
        # Safely shut down the window execution layer and request a clean application restart
        import sys
        from PyQt6.QtWidgets import QApplication
        QApplication.quit()
        
        # Re-execute the primary script entry point with the updated configuration flags
        import subprocess
        subprocess.Popen([sys.executable] + sys.argv)

def initialize_engine_switches():
    """Appends performance and security flags to the global initialization runtime."""
    # Static rendering flags shared across all target devices
    sys.argv.append("--disable-reading-from-canvas")
    sys.argv.append("--disable-shared-workers")
    sys.argv.append("--enable-strict-mixed-content-checking")
    sys.argv.append("--disable-battery-saver")
    sys.argv.append("--log-level=2")
    sys.argv.append("--disable-speech-api")
    sys.argv.append("--disable-gpu-animation")
    sys.argv.append("--disable-features=Translate,BlinkFeatures,AudioServiceOutOfProcess")
    sys.argv.append("--enable-low-end-device-mode")

    # Aggressive memory compaction and cache discarding flags
    sys.argv.append("--memory-pressure-off-threshold-percent=30")
    sys.argv.append("--aggressive-cache-discard")
    sys.argv.append("--js-flags=--expose-gc")

    # Force the engine to negotiate standard TLS grease and cipher layouts
    sys.argv.append("--enable-features=TLSExtensionGrease")
    sys.argv.append("--crypto-evaluation-scope=all")
    
    # Mask Chromium networking features that expose the internal wrapper profile
    sys.argv.append("--disable-ssl-key-logging")
    sys.argv.append("--disable-http2-grease")

    # Read the granular parameters from our isolated config engine
    cfg = load_config()

    if cfg.get("disable_gpu", True):
        sys.argv.append("--disable-gpu")
        sys.argv.append("--disable-gpu-compositing")

    if cfg.get("background_throttling", True):
        sys.argv.append("--enable-background-timer-throttling")
        sys.argv.append("--add-delay-to-background-timer-tasks")
        
    limit = cfg.get("process_limit", 3)
    sys.argv.append(f"--renderer-process-limit={limit}")

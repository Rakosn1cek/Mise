# memoryguard.py
# Distro-agnostic memory manager for QtWebEngine applications
import os
from PyQt6.QtCore import QObject, QTimer

class MemoryGuard(QObject):
    def __init__(self, browser_window, interval_ms=60000, max_gb=1.8):
        super().__init__(browser_window)
        self.browser = browser_window
        self.max_bytes = int(max_gb * 1024 * 1024 * 1024)
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.check_memory_usage)
        self.timer.start(interval_ms)
        
    def _get_renderer_memory(self):
        total_rss = 0
        try:
            pid_list = [pid for pid in os.listdir('/proc') if pid.isdigit()]
            for pid in pid_list:
                try:
                    with open(f'/proc/{pid}/cmdline', 'r', errors='ignore') as f:
                        cmdline = f.read()
                    
                    if "QtWebEngineProcess" in cmdline and "--type=rend" in cmdline:
                        with open(f'/proc/{pid}/statm', 'r') as f:
                            rss_pages = int(f.read().split()[1])
                            total_rss += rss_pages * 4096
                except (IOError, IndexError):
                    continue
        except Exception:
            pass
        return total_rss

    def check_memory_usage(self):
        if not hasattr(self.browser, 'current_active_view') or not self.browser.current_active_view:
            return

        current_memory = self._get_renderer_memory()
        
        if current_memory >= self.max_bytes:
            page = self.browser.current_active_view.page()
            if not page:
                return

            js_check = """
            (function() {
                var el = document.activeElement;
                if (!el) return false;
                var tagName = el.tagName.toLowerCase();
                return tagName === 'input' || tagName === 'textarea' || el.isContentEditable;
            })();
            """
            page.runJavaScript(js_check, self.evaluate_idle_state)

    def evaluate_idle_state(self, is_typing):
        if is_typing:
            return

        # Trigger the seamless view container warm-up inside the main app layout
        if hasattr(self.browser, 'prepare_background_swap'):
            self.browser.prepare_background_swap()

import subprocess

class NotificationWorker:
    def __init__(self):
        # Default state can be managed explicitly here
        self.enabled = True

    def toggle_state(self):
        """Swaps the notification permission parameter state."""
        self.enabled = not self.enabled
        return self.enabled

    def handle_incoming_notification(self, notification, message_text=None):
        """Processes the web engine notification callback routing if enabled."""
        if not self.enabled:
            return

        # Check if the incoming variable is a string layout or a native engine object wrapper
        if isinstance(notification, str):
            title = notification
            message = message_text if message_text else ""
        else:
            try:
                title = notification.title()
                message = notification.message()
            except AttributeError:
                # Fallback safeguard if parameter parsing mismatches completely
                return
        
        try:
            subprocess.Popen([
                "notify-send",
                "-a", "Mise",
                title,
                message
            ])
        except Exception:
            pass

import subprocess

class NotificationWorker:
    def __init__(self):
        # Default state can be managed explicitly here
        self.enabled = True

    def toggle_state(self):
        """Swaps the notification permission parameter state."""
        self.enabled = not self.enabled
        return self.enabled

    def handle_incoming_notification(self, notification):
        """Processes the web engine notification callback routing if enabled."""
        if not self.enabled:
            return

        title = notification.title()
        message = notification.message()
        
        try:
            subprocess.Popen([
                "notify-send",
                "-a", "Mise",
                title,
                message
            ])
        except Exception:
            pass

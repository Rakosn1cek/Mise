from PyQt6.QtWebEngineCore import QWebEnginePage

class PermissionEngine:
    def __init__(self):
        # Explicit granular permission mapping for trusted application endpoints
        self.allowed_permissions = {
            "google.com": [
                QWebEnginePage.Feature.MediaAudioCapture, 
                QWebEnginePage.Feature.MediaVideoCapture, 
                QWebEnginePage.Feature.DesktopVideoCapture
            ],
            "meet.google.com": [
                QWebEnginePage.Feature.MediaAudioCapture, 
                QWebEnginePage.Feature.MediaVideoCapture, 
                QWebEnginePage.Feature.DesktopVideoCapture
            ],
            "gmail.com": [
                QWebEnginePage.Feature.Notifications
            ],
            "zoho.eu": [
                QWebEnginePage.Feature.Notifications
            ],
            "zoho.com": [
                QWebEnginePage.Feature.Notifications
            ],
            "reddit.com": [
                QWebEnginePage.Feature.Notifications
            ]
        }

    def evaluate_request(self, page, security_origin, feature):
        """Evaluates incoming resource requests and routes them dynamically."""
        if not page:
            return

        requesting_host = security_origin.host().lower()
        
        # Check requested feature against trusted domains
        for trusted_domain, allowed_features in self.allowed_permissions.items():
            if requesting_host == trusted_domain or requesting_host.endswith("." + trusted_domain):
                if feature in allowed_features:
                    page.setFeaturePermission(
                        security_origin, 
                        feature, 
                        QWebEnginePage.PermissionPolicy.PermissionGrantedByUser
                    )
                    return

        # Explicitly deny access if the domain or feature is not predefined
        page.setFeaturePermission(
            security_origin, 
            feature, 
            QWebEnginePage.PermissionPolicy.PermissionDeniedByUser
        )

from PyQt6.QtWebEngineCore import QWebEngineUrlRequestInterceptor

class TelemetryBlocker(QWebEngineUrlRequestInterceptor):
    """
    Network request interceptor to drop tracking streams and native advertisement domains.
    """
    def interceptRequest(self, info):
        url = info.requestUrl()
        host = url.host().lower()
        url_str = url.toString().lower()
        
        # Hard block specific ad distribution endpoints completely
        if "alb.reddit.com" in host or host.endswith(".reddit.com/api/eval"):
            info.block(True)
            return

        block_keywords = [
            "telemetry", "analytics", "metrics", "log-upload", 
            "browser-intake", "stats", "pagead", "doubleclick"
        ]
        if any(keyword in url_str for keyword in block_keywords):
            info.block(True)

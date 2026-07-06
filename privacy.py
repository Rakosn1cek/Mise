# Way to handle isolated, off-the-record browser profiles
from PyQt6.QtWebEngineCore import QWebEngineProfile

class PrivacyManager:
    def __init__(self, shared_profile):
        # Keep a reference to the main application daily driver profile
        self.shared_profile = shared_profile
        
        # Unique, isolated in-memory profile
        # The storage_name identifier groups all private tabs together in memory
        self.private_profile = QWebEngineProfile("MisePrivateProfile")
        
        # Private profile to never persist data to disk
        self.private_profile.setHttpCacheType(QWebEngineProfile.HttpCacheType.MemoryHttpCache)
        self.private_profile.setPersistentCookiesPolicy(QWebEngineProfile.PersistentCookiesPolicy.NoPersistentCookies)
        
        # Custom User-Agent from the main setup to keep the fingerprint uniform
        default_ua = QWebEngineProfile.defaultProfile().httpUserAgent()
        self.private_profile.setHttpUserAgent(default_ua)

        # Internal boolean tracking variable for manual switching state
        self.private_browsing_enabled = False

    def configure_page_profile(self, page, private_mode=False):
        """
        Binds a QWebEnginePage to either the global default profile 
        or the isolated private profile based on the toggle state.
        """
        if private_mode:
            # Re-initialising the page with the private profile context
            # Note: A page's profile cannot be changed after creation, 
            # so the page layout must be instantiated with this profile.
            return page.__class__(self.private_profile)
        return page

    def toggle_private_browsing(self):
        """Switches the private mode state flag."""
        self.private_browsing_enabled = not self.private_browsing_enabled
        return "ON" if self.private_browsing_enabled else "OFF"

    def get_target_profile(self, url_str):
        """Evaluates domain rules and manual toggles to return the correct profile layer."""
        if self.private_browsing_enabled or "ycombinator.com" in url_str.lower():
            return self.private_profile
        return self.shared_profile

    def get_current_active_profile(self):
        """Returns whichever profile layer is currently in active use based on the toggle state."""
        return self.private_profile if self.private_browsing_enabled else self.shared_profile

    def clear_site_cookies(self, current_webview):
        """Surgically purges cookies for the active domain or wipes the container globally."""
        profile = self.get_current_active_profile()
        
        if current_webview and current_webview.page():
            target_url = current_webview.url()
            host = target_url.host().lower()
            
            if host and target_url.toString() != "about:blank":
                # Isolating the core root domain (e.g., reddit.com)
                root_domain = ".".join(host.split(".")[-2:])
                cookie_store = profile.cookieStore()
                
                def cookie_filter(cookie):
                    cookie_domain = cookie.domain().lower()
                    if root_domain in cookie_domain:
                        cookie_store.deleteCookie(cookie)
                
                cookie_store.loadAllCookies()
                cookie_store.cookieAdded.connect(cookie_filter)
                return f"Cookies cleared for {root_domain}"

        # Global fallback if executed on a blank tab or dashboard view
        profile.cookieStore().deleteAllCookies()
        return "All profile cookies cleared globally"

    def clear_cache(self):
        """Clears the HTTP cache layer safely for the active engine profile."""
        profile = self.get_current_active_profile()
        
        try:
            # Executing the core cache clear routine
            profile.clearHttpCache()
            return "Browser HTTP network cache cleared"
        except Exception as e:
            return f"Cache clear initialization failed: {str(e)}"

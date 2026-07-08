#!/usr/bin/env python3

import os
import sys
import json
import re
import subprocess

# Core system hooks MUST run explicitly before local module references trigger
os.environ["QT_LOGGING_RULES"] = "qt.webenginecontext.debug=false;*.warning=false"
os.environ["GLOG_minloglevel"] = "2"
os.environ["QT_QPA_PLATFORMTHEME"] = "xdgdesktopportal"

try:
    stderr_fileno = sys.stderr.fileno()
    null_fileno = os.open(os.devnull, os.O_WRONLY)
    os.dup2(null_fileno, stderr_fileno)
except Exception:
    pass

from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QKeySequence, QShortcut, QFont, QColor, QAction
from PyQt6.QtWebEngineCore import QWebEngineProfile, QWebEngineSettings, QWebEngineUrlRequestInterceptor, QWebEngineScript, QWebEnginePage, QWebEngineContextMenuRequest
from PyQt6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QStackedLayout,
    QWidget,
    QStackedWidget,
    QDialog,
    QMenu,
)
from PyQt6.QtWebEngineWidgets import QWebEngineView

from permissions import PermissionEngine
from theme import get_browser_stylesheet
from workspace import WorkspaceEngine, WorkspaceDashboard
from blocker import TelemetryBlocker
from palette import CommandPalette
from privacy import PrivacyManager
from config import initialize_engine_switches

notification_worker_mod = __import__("notification-worker")
NotificationWorker = notification_worker_mod.NotificationWorker

help_menu_mod = __import__("help-menu")
HelpMenu = help_menu_mod.HelpMenu

# --------------------------------------------------------------------

# Absolute intercept handler to prevent Chromium console noise from spilling into the terminal
def silence_console_messages(level, message, line, sourceid):
    pass


class TelemetryBlocker(QWebEngineUrlRequestInterceptor):
    def interceptRequest(self, info):
        # Extract the destination URL and host
        target_url = info.requestUrl()
        target_url_str = target_url.toString().lower()
        target_host = target_url.host().lower()
        
        # Extract the top-level domain currently loaded in the active tab context
        first_party_url = info.firstPartyUrl()
        first_party_host = first_party_url.host().lower()

        block_keywords = [
            "telemetry", "analytics", "metrics", "log-upload", 
            "browser-intake", "stats", "pagead", "doubleclick"
        ]
        
        # Check if the network request hits any privacy block triggers
        if any(keyword in target_url_str for keyword in block_keywords):
            
            # Extract basic root domains to compare context (e.g., reddit.com)
            # This strips subdomains like api.github.com or svc.reddit.com down to the core domain
            target_root = ".".join(target_host.split(".")[-2:])
            first_party_root = ".".join(first_party_host.split(".")[-2:])
            
            # If the request is first-party (the site loading its own asset mechanics), bypass the block
            if target_root == first_party_root and first_party_root != "":
                return

            # If it's a third-party domain (like google-analytics hitting a reddit page), block it
            info.block(True)

class SettingsDialog(QDialog):
    def __init__(self, parent=None, current_mode="low_end"):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setFixedWidth(360)
        self.setObjectName("SettingsWindow")
        
        # Apply clean translucent windows flags
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        header = QLabel("Hardware Optimization Profile")
        header.setStyleSheet("font-weight: bold; color: #2ac3de; font-size: 14px;")
        layout.addWidget(header)
        
        # Configuration toggle buttons using descriptive state text
        self.low_end_btn = QPushButton("Low-End / Fanless Profile (Throttled)")
        self.high_end_btn = QPushButton("High-End / Performance Profile (Uncapped)")
        
        # Highlight active setting selection on window draw
        self.selected_mode = current_mode
        self.update_button_states()
        
        self.low_end_btn.clicked.connect(lambda: self.set_profile("low_end"))
        self.high_end_btn.clicked.connect(lambda: self.set_profile("high_end"))
        
        layout.addWidget(self.low_end_btn)
        layout.addWidget(self.high_end_btn)
        
        # Bottom window termination control rows
        action_layout = QHBoxLayout()
        action_layout.addStretch()
        
        save_btn = QPushButton("Save & Exit")
        save_btn.clicked.connect(self.accept)
        action_layout.addWidget(save_btn)
        
        layout.addLayout(action_layout)
        self.setLayout(layout)
        
    def set_profile(self, mode):
        self.selected_mode = mode
        self.update_button_states()
        
    def update_button_states(self):
        # Explicit style application based on selection mechanics
        if self.selected_mode == "low_end":
            self.low_end_btn.setStyleSheet("background-color: #364a85; color: #c0caf5; border: 1px solid #2ac3de;")
            self.high_end_btn.setStyleSheet("background-color: transparent; color: #c0caf5; border: 1px solid #24283b;")
        else:
            self.low_end_btn.setStyleSheet("background-color: transparent; color: #c0caf5; border: 1px solid #24283b;")
            self.high_end_btn.setStyleSheet("background-color: #364a85; color: #c0caf5; border: 1px solid #2ac3de;")


class MiseBrowser(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Mise")
        self.resize(1600, 1040)

        # Track system-wide preferences inside clean initialization parameter variables
        self.is_dark_layout = True  # Toggle manually to False for light interface layout setup

        self.workspace_engine = WorkspaceEngine(self)
        self.dashboard_view = WorkspaceDashboard(self)
        self.dashboard_active = False

        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        sidebar_layout = QVBoxLayout()
        sidebar_layout.setContentsMargins(4, 4, 4, 4)
        sidebar_layout.setSpacing(4)

        # Active workspace text indicator label
        self.workspace_label = QLabel(
            f"{self.workspace_engine.current_workspace}"
        )
        self.workspace_label.setObjectName("WorkspaceLabel")
        sidebar_layout.addWidget(self.workspace_label)

        # Horizontal action row container for compact browser navigation controls
        nav_action_layout = QHBoxLayout()
        nav_action_layout.setContentsMargins(4, 2, 4, 6)
        nav_action_layout.setSpacing(12)

        # Back history navigation button using Nerd Font icon
        self.back_btn = QPushButton("󰁍")
        self.back_btn.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.back_btn.setToolTip("Go Back")
        self.back_btn.setObjectName("NavIconButton")
        self.back_btn.setFixedWidth(24)
        self.back_btn.clicked.connect(self.navigate_back)
        nav_action_layout.addWidget(self.back_btn)

        # Forward history navigation button using Nerd Font icon
        self.forward_btn = QPushButton("󰁔")
        self.forward_btn.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.forward_btn.setToolTip("Go Forward")
        self.forward_btn.setObjectName("NavIconButton")
        self.forward_btn.setFixedWidth(24)
        self.forward_btn.clicked.connect(self.navigate_forward)
        nav_action_layout.addWidget(self.forward_btn)

        # New tab launcher button using Nerd Font plus symbol
        self.toggle_nav_btn = QPushButton("󰐕")
        self.toggle_nav_btn.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.toggle_nav_btn.setToolTip("New Tab / Navigation")
        self.toggle_nav_btn.setObjectName("NavIconButton")
        self.toggle_nav_btn.setFixedWidth(24)
        self.toggle_nav_btn.clicked.connect(self.toggle_address_bar)
        nav_action_layout.addWidget(self.toggle_nav_btn)

        # Workspaces dashboard toggle button using Nerd Font menu grid icon
        self.menu_btn = QPushButton("󰍜")
        self.menu_btn.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.menu_btn.setToolTip("Workspaces Dashboard")
        self.menu_btn.setObjectName("NavIconButton")
        self.menu_btn.setFixedWidth(24)
        self.menu_btn.clicked.connect(self.toggle_dashboard_view)
        nav_action_layout.addWidget(self.menu_btn)

        nav_action_layout.addStretch()
        sidebar_layout.addLayout(nav_action_layout)

        self.tab_list = QListWidget()
        self.tab_list.setObjectName("TabList")
        self.tab_list.currentRowChanged.connect(lambda idx: self.switch_tab(idx, force_focus=False))
        sidebar_layout.addWidget(self.tab_list)

        # Create a bottom action row container for style and notification controls
        bottom_theme_layout = QHBoxLayout()
        bottom_theme_layout.setContentsMargins(4, 4, 4, 4)
        bottom_theme_layout.setSpacing(8)
        
        # Instantiate the theme selection action button
        self.theme_toggle_btn = QPushButton("󰖔" if self.is_dark_layout else "󰖨")
        self.theme_toggle_btn.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.theme_toggle_btn.setObjectName("ThemeToggleBtn")
        self.theme_toggle_btn.setFixedWidth(32)
        self.theme_toggle_btn.setToolTip("Toggle Light/Dark Mode")
        self.theme_toggle_btn.clicked.connect(self.toggle_theme_mode)
        bottom_theme_layout.addWidget(self.theme_toggle_btn)

        # Instantiate the notification toggle button using Nerd Font bell icons
        self.noti_toggle_btn = QPushButton("󰂚")
        self.noti_toggle_btn.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.noti_toggle_btn.setObjectName("NotiToggleBtn")
        self.noti_toggle_btn.setFixedWidth(32)
        self.noti_toggle_btn.setToolTip("Toggle Web Notifications")
        self.noti_toggle_btn.clicked.connect(self.toggle_notification_service)
        bottom_theme_layout.addWidget(self.noti_toggle_btn)
        
        bottom_theme_layout.addStretch()
        sidebar_layout.addLayout(bottom_theme_layout)

        # Change sidebar_widget to self.sidebar_widget
        self.sidebar_widget = QWidget()
        self.sidebar_widget.setObjectName("Sidebar")
        self.sidebar_widget.setFixedWidth(260)
        self.sidebar_widget.setLayout(sidebar_layout)
        main_layout.addWidget(self.sidebar_widget)

        right_content_layout = QVBoxLayout()
        right_content_layout.setContentsMargins(0, 0, 0, 0)
        right_content_layout.setSpacing(0)

        self.content_container = QWidget()
        self.content_area = QStackedLayout(self.content_container)
        self.content_area.setContentsMargins(0, 0, 0, 0)
        self.content_area.setSpacing(0)
        
        right_content_layout.addWidget(self.content_container)

        self.right_container_widget = QWidget()
        self.right_container_widget.setLayout(right_content_layout)
        main_layout.addWidget(self.right_container_widget)

        self.url_bar = QLineEdit(self.right_container_widget)
        self.url_bar.setPlaceholderText("Search or enter address...")
        self.url_bar.setObjectName("WideAddressBar")
        self.url_bar.returnPressed.connect(self.navigate_to_url)
        self.url_bar.hide()

        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        # Establish a secure configuration storage path for browser profiles
        storage_path = os.path.expanduser("~/.config/mise/browser_profile")
        os.makedirs(storage_path, exist_ok=True)
        
        self.shared_profile = QWebEngineProfile("MiseSharedProfile", self)
        self.shared_profile.setPersistentStoragePath(storage_path)
        self.shared_profile.setPersistentCookiesPolicy(QWebEngineProfile.PersistentCookiesPolicy.AllowPersistentCookies)
        
        self.shared_profile.setHttpCacheType(QWebEngineProfile.HttpCacheType.DiskHttpCache)

        user_agent = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
        QWebEngineProfile.defaultProfile().setHttpUserAgent(user_agent)
        
        scrollbar_script = QWebEngineScript()
        scrollbar_script.setSourceCode("""
            const style = document.createElement('style');
            style.innerHTML = 'html { overflow-y: scroll !important; }';
            document.documentElement.appendChild(style);
        """)
        scrollbar_script.setInjectionPoint(QWebEngineScript.InjectionPoint.DocumentCreation)
        scrollbar_script.setWorldId(QWebEngineScript.ScriptWorldId.MainWorld)
        scrollbar_script.setRunsOnSubFrames(True)
        
        # Register the script layout rule to your shared daily driver profile
        self.shared_profile.scripts().insert(scrollbar_script)

        hint_script = QWebEngineScript()
        hinter_path = os.path.join(os.path.dirname(__file__), "hinter.js")
        if os.path.exists(hinter_path):
            with open(hinter_path, "r", encoding="utf-8") as f:
                hint_script.setSourceCode(f.read())
            hint_script.setInjectionPoint(QWebEngineScript.InjectionPoint.DocumentCreation)
            hint_script.setWorldId(QWebEngineScript.ScriptWorldId.MainWorld)
            hint_script.setRunsOnSubFrames(True)
            self.shared_profile.scripts().insert(hint_script)

        # Instantiate the isolated notification controller module
        self.notification_worker = NotificationWorker()
        self.shared_profile.setNotificationPresenter(self.notification_worker.handle_incoming_notification)

        self.interceptor = TelemetryBlocker()
        self.shared_profile.setUrlRequestInterceptor(self.interceptor)
        
        self.shared_profile.downloadRequested.connect(self.handle_incoming_download)

        # Instantiate the privacy manager wrapper context passing the shared profile instance
        self.privacy_manager = PrivacyManager(self.shared_profile)

        self.private_profile = QWebEngineProfile("MisePrivateProfile", self)
        self.private_profile.setHttpCacheType(QWebEngineProfile.HttpCacheType.MemoryHttpCache)
        self.private_profile.setPersistentCookiesPolicy(QWebEngineProfile.PersistentCookiesPolicy.NoPersistentCookies)
        self.private_profile.setHttpUserAgent(self.shared_profile.httpUserAgent())
                
        # New boolean toggle mapping tracker for manual switching state
        self.private_browsing_enabled = False
        
        self.setStyleSheet(get_browser_stylesheet(self.is_dark_layout))
        self.apply_interface_fonts()

        # Instantiate the isolated background permissions policy rule book
        self.permission_engine = PermissionEngine()

    def apply_interface_fonts(self):
        """Uniform text properties across sidebar elements, navigation nodes, and workspace items."""
        ui_font = QFont("Noto Sans", 14)
        self.tab_list.setFont(ui_font)
        self.url_bar.setFont(ui_font)
        self.dashboard_view.view_tree.setFont(ui_font)

        icon_font = QFont("Noto Sans", 16)
        self.theme_toggle_btn.setFont(icon_font)
        self.noti_toggle_btn.setFont(icon_font)

    def keyPressEvent(self, event):
        modifiers = event.modifiers()
        is_ctrl = modifiers == Qt.KeyboardModifier.ControlModifier
        is_ctrl_shift = modifiers == (
            Qt.KeyboardModifier.ControlModifier
            | Qt.KeyboardModifier.ShiftModifier
        )

        if is_ctrl and event.key() == Qt.Key.Key_T:
            self.add_new_tab("https://duckduckgo.com", force_focus=True)
            event.accept()
            return

        if is_ctrl and event.key() == Qt.Key.Key_W:
            if self.dashboard_active:
                self.quick_remove_current()
            else:
                self.close_current_tab()
            event.accept()
            return

        if is_ctrl_shift and event.key() == Qt.Key.Key_W:
            self.toggle_dashboard_view()
            event.accept()
            return

        if is_ctrl and event.key() == Qt.Key.Key_S:
            self.quick_save_workspace()
            event.accept()
            return

        if is_ctrl and event.key() == Qt.Key.Key_R:
            if not self.dashboard_active:
                current_idx = self.tab_list.currentRow()
                active_ws = self.workspace_engine.current_workspace
                if current_idx != -1 and current_idx < len(self.workspace_engine.workspaces[active_ws]):
                    self.workspace_engine.workspaces[active_ws][current_idx].reload()
            event.accept()
            return

        if is_ctrl and event.key() == Qt.Key.Key_D:
            self.quick_remove_current()
            event.accept()
            return

        if is_ctrl and event.key() == Qt.Key.Key_L:
            self.toggle_address_bar()
            event.accept()
            return

        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if self.tab_list.hasFocus():
                current_idx = self.tab_list.currentRow()
                if current_idx != -1:
                    self.switch_tab(current_idx, force_focus=True)
                    event.accept()
                    return

        if is_ctrl and event.key() == Qt.Key.Key_M:
            self.tab_list.setFocus()
            event.accept()
            return

        if is_ctrl and event.key() == Qt.Key.Key_F:
            self.trigger_link_hints()
            event.accept()
            return

        if event.key() == Qt.Key.Key_F1:
            self.show_help_menu()
            event.accept()
            return

        if is_ctrl and event.key() == Qt.Key.Key_B:
            if hasattr(self, 'current_active_view'):
                self.current_active_view.setFocus()
                event.accept()
                return

        if is_ctrl and event.key() == Qt.Key.Key_P:
            self.open_command_palette()
            event.accept()
            return

        if is_ctrl_shift and event.key() == Qt.Key.Key_P:
            self.toggle_private_browsing()
            event.accept()
            return
                            
        super().keyPressEvent(event)

    def add_new_tab(self, url_str, workspace_name=None, force_focus=True):
        # Route to the memory-isolated profile if private mode is toggled or target domain matches
        if getattr(self, "private_browsing_enabled", False) or "ycombinator.com" in url_str.lower():
            target_profile = self.private_profile
        else:
            target_profile = self.shared_profile

        # Pass the evaluated profile directly into the native C++ engine factory layout
        web_page = QWebEnginePage(target_profile, self)
        web_page.javaScriptConsoleMessage = silence_console_messages
        web_page.featurePermissionRequested.connect(
            lambda origin, feat, p=web_page: self.permission_engine.evaluate_request(p, origin, feat)
        )

        class MiseWebView(QWebEngineView):
            def createWindow(self, type):
                # Intercept links targeting new windows or tabs and route them through the main window pipeline
                new_view = QWebEngineView(self.window())
                self.window().add_new_tab("about:blank", force_focus=True)
                
                return new_view
                
                # Get the newly created view instance from the active workspace array to attach the page pipeline
                active_ws = self.window().workspace_engine.current_workspace
                active_tabs = self.window().workspace_engine.workspaces[active_ws]
                target_view = active_tabs[-1]

                if type == QWebEnginePage.WebWindowType.WebBrowserTab or type == QWebEnginePage.WebWindowType.WebBrowserWindow:
                    target_view.page().urlChanged.connect(lambda url: target_view.setUrl(url))
                    
                return target_view
                            
            def contextMenuEvent(self, event):
                menu = QMenu(self)
                menu.setObjectName("ContextMenu")
                
                menu.setWindowFlags(menu.windowFlags() | Qt.WindowType.FramelessWindowHint | Qt.WindowType.NoDropShadowWindowHint)
                menu.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
                
                data = self.lastContextMenuRequest()
                selected_text = data.selectedText().strip()
                is_image = data.mediaType() == QWebEngineContextMenuRequest.MediaType.MediaTypeImage
                link_url = data.linkUrl()
                
                # Condition: Right click target contains a valid web reference URL
                if link_url.isValid() and not link_url.isEmpty():
                    copy_link_action = QAction("Copy Link Address", self)
                    copy_link_action.triggered.connect(lambda: self.triggerPageAction(self.page().WebAction.CopyLinkToClipboard))
                    menu.addAction(copy_link_action)
                    
                    open_tab_action = QAction("Open Link in New Tab", self)
                    open_tab_action.triggered.connect(lambda: self.window().add_new_tab(link_url.toString()))
                    menu.addAction(open_tab_action)
                    
                    menu.addSeparator()
                
                # 1. Condition: User highlighted a text string
                if selected_text:
                    text_preview = selected_text if len(selected_text) < 15 else f"{selected_text[:12]}..."
                    search_action = QAction(f"Search with DuckDuckGo for '{text_preview}'", self)
                    search_action.triggered.connect(
                        lambda: self.window().add_new_tab(f"https://duckduckgo.com/?q={selected_text}")
                    )
                    menu.addAction(search_action)

                    # New Arch Wiki contextual lookup action pass
                    arch_action = QAction(f"Search Arch Wiki for '{text_preview}'", self)
                    arch_action.triggered.connect(
                        lambda: self.window().add_new_tab(f"https://wiki.archlinux.org/index.php?search={selected_text}")
                    )
                    menu.addAction(arch_action)
                    
                    menu.addSeparator()
                    
                    copy_action = QAction("Copy", self)
                    copy_action.triggered.connect(lambda: self.triggerPageAction(self.page().WebAction.Copy))
                    menu.addAction(copy_action)
                
                # 2. Condition: User right-clicked on an image asset node
                elif is_image:
                    copy_img_action = QAction("Copy Image", self)
                    copy_img_action.triggered.connect(lambda: self.triggerPageAction(self.page().WebAction.CopyImageToClipboard))
                    menu.addAction(copy_img_action)
                    
                    save_img_action = QAction("Save Image As...", self)
                    save_img_action.triggered.connect(lambda: self.triggerPageAction(self.page().WebAction.DownloadImageToDisk))
                    menu.addAction(save_img_action)
                
                # 3. Fallback Condition: Standard empty background canvas right-click
                else:
                    copy_action = QAction("Copy", self)
                    copy_action.triggered.connect(lambda: self.triggerPageAction(self.page().WebAction.Copy))
                    menu.addAction(copy_action)
                    
                    paste_action = QAction("Paste", self)
                    paste_action.triggered.connect(lambda: self.triggerPageAction(self.page().WebAction.Paste))
                    menu.addAction(paste_action)
                    
                    menu.addSeparator()
                    
                    back_action = QAction("Go Back", self)
                    back_action.triggered.connect(lambda: self.triggerPageAction(self.page().WebAction.Back))
                    back_action.setEnabled(self.history().canGoBack())
                    menu.addAction(back_action)

                    forward_action = QAction("Go Forward", self)
                    forward_action.triggered.connect(lambda: self.triggerPageAction(self.page().WebAction.Forward))
                    forward_action.setEnabled(self.history().canGoForward())
                    menu.addAction(forward_action)

                    # New terminal execution action
                    run_action = QAction("Run in Terminal", self)
                    run_action.triggered.connect(lambda: self.window().run_in_terminal(selected_text))
                    menu.addAction(run_action)

                         
                menu.popup(event.globalPos())

        webview = MiseWebView()
        webview.setPage(web_page)
        bg_hex = "#c6d1d1" if self.is_dark_layout else "#f5f6f9"
        web_page.setBackgroundColor(QColor(bg_hex))

        settings = webview.settings()
        settings.setAttribute(QWebEngineSettings.WebAttribute.ForceDarkMode, self.is_dark_layout)
        
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalStorageEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.PluginsEnabled, False)
        settings.setAttribute(QWebEngineSettings.WebAttribute.ScrollAnimatorEnabled, False)
        settings.setAttribute(QWebEngineSettings.WebAttribute.HyperlinkAuditingEnabled, False)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, False)
        settings.setAttribute(QWebEngineSettings.WebAttribute.PlaybackRequiresUserGesture, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptCanAccessClipboard, True)
        
        # Hardware acceleration must be True to prevent Gemini canvas loops from cooking the CPU
        settings.setAttribute(QWebEngineSettings.WebAttribute.WebGLEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.Accelerated2dCanvasEnabled, True)

        webview.titleChanged.connect(
            lambda title, wv=webview: self.update_tab_titles(wv, title)
        )
        webview.urlChanged.connect(
            lambda url, wv=webview: self.update_url_field(wv, url)
        )
        webview.page().linkHovered.connect(
            lambda url: webview.setToolTip(url) if url else webview.setToolTip("")
        )

        target_ws = workspace_name if workspace_name else self.workspace_engine.current_workspace
        self.workspace_engine.workspaces[target_ws].append(webview)
        webview.setUrl(QUrl(url_str))

        if target_ws == self.workspace_engine.current_workspace:
            self.tab_list.addItem("Loading...")
            self.content_area.addWidget(webview)
            new_index = len(self.workspace_engine.workspaces[target_ws]) - 1
            self.tab_list.setCurrentRow(new_index)
            self.switch_tab(new_index, force_focus=force_focus)
        else:
            webview.hide()

    def switch_tab(self, index, force_focus=True):
        if index < 0:
            return

        active_ws = self.workspace_engine.current_workspace
        tabs = self.workspace_engine.workspaces.get(active_ws, [])
        valid_tabs = [t for t in tabs if not isinstance(t, str)]

        if index >= len(valid_tabs):
            return

        target_webview = valid_tabs[index]

        try:
            if self.content_area.indexOf(target_webview) == -1:
                self.content_area.addWidget(target_webview)

            self.current_active_view = target_webview
            self.content_area.setCurrentWidget(target_webview)

            if hasattr(self, 'url_bar') and self.url_bar:
                self.url_bar.setText(target_webview.url().toString())

            # Evaluate whether the underlying rendering engine page is active and responding
            if target_webview.page() and not target_webview.page().isLoading():
                # Execute a lightweight, non-blocking check to verify if the JavaScript environment is responsive
                target_webview.page().runJavaScript(
                    "1;", 
                    lambda res: target_webview.reload() if res is None else None
                )

            if force_focus:
                target_webview.setFocus()
        except RuntimeError:
            pass

    def close_current_tab(self):
        active_ws = self.workspace_engine.current_workspace
        active_tabs = self.workspace_engine.workspaces[active_ws]
        if len(active_tabs) <= 1:
            return

        current_index = self.tab_list.currentRow()
        if current_index == -1:
            return

        webview_to_remove = active_tabs.pop(current_index)
        item_to_remove = self.tab_list.takeItem(current_index)
        del item_to_remove

        if not isinstance(webview_to_remove, str) and webview_to_remove.page():
            webview_to_remove.setPage(None)

        if not isinstance(webview_to_remove, str):
            webview_to_remove.deleteLater()

        new_index = max(0, current_index - 1)
        self.tab_list.setCurrentRow(new_index)
        self.switch_tab(new_index, force_focus=False)

    def quick_save_workspace(self):
        active_ws = self.workspace_engine.current_workspace
        current_idx = self.tab_list.currentRow()
        if current_idx == -1:
            return

        current_url = (
            self.workspace_engine.workspaces[active_ws][current_idx]
            .url()
            .toString()
        )
        self.add_new_tab(current_url, force_focus=True)

    def quick_remove_current(self):
        if self.dashboard_active:
            item = self.dashboard_view.view_tree.currentItem()
            if item:
                payload = item.data(Qt.ItemDataRole.UserRole)
                if payload:
                    self.execute_inline_removal(payload)
                    self.dashboard_view.refresh_view_data()
        else:
            self.close_current_tab()

    def execute_inline_removal(self, payload):
        node_type = payload[0]
        if node_type == "tab":
            _, target_ws, tab_idx = payload
            if len(self.workspace_engine.workspaces[target_ws]) > 1:
                webview = self.workspace_engine.workspaces[target_ws].pop(
                    tab_idx
                )
                if target_ws == self.workspace_engine.current_workspace:
                    self.tab_list.takeItem(tab_idx)
                if not isinstance(webview, str) and webview.page():
                    webview.setPage(None)
                if not isinstance(webview, str):
                    webview.deleteLater()
        elif node_type == "workspace":
            _, ws_name = payload
            if len(self.workspace_engine.workspaces) > 1:
                if ws_name == self.workspace_engine.current_workspace:
                    remaining_keys = [
                        k
                        for k in self.workspace_engine.workspaces.keys()
                        if k != ws_name
                    ]
                    self.workspace_engine.switch_workspace_record(
                        remaining_keys[0], track_focus=False
                    )

                tabs_to_clear = self.workspace_engine.workspaces.pop(ws_name)
                for wv in tabs_to_clear:
                    if not isinstance(wv, str):
                        if wv.page():
                            wv.setPage(None)
                        wv.deleteLater()

    def toggle_dashboard_view(self):
        if self.dashboard_active:
            self.close_dashboard()
        else:
            self.open_dashboard()

    def open_dashboard(self):
        for ws_name, webviews in self.workspace_engine.workspaces.items():
            for webview in webviews:
                try:
                    if not isinstance(webview, str):
                        webview.hide()
                        self.content_area.removeWidget(webview)
                except RuntimeError:
                    pass

        self.content_area.addWidget(self.dashboard_view)
        self.dashboard_view.refresh_view_data()
        self.dashboard_view.show()
        self.dashboard_view.view_tree.setFocus()
        self.dashboard_active = True

    def close_dashboard(self):
        self.dashboard_view.hide()
        self.content_area.removeWidget(self.dashboard_view)
        self.dashboard_active = False

        active_ws = self.workspace_engine.current_workspace
        current_idx = self.tab_list.currentRow()
        tabs = self.workspace_engine.workspaces.get(active_ws, [])
        valid_tabs = [t for t in tabs if not isinstance(t, str)]

        if current_idx < 0 or current_idx >= len(valid_tabs):
            current_idx = 0

        for idx, webview in enumerate(valid_tabs):
            try:
                if idx == current_idx:
                    self.content_area.addWidget(webview)
                    webview.show()
                    webview.setFocus()
                else:
                    webview.hide()
                    self.content_area.removeWidget(webview)
            except RuntimeError:
                pass

    def update_tab_titles(self, webview, title):
        # Match opening bracket, extract numbers, ignore subsequent descriptive text inside the brackets
        match = re.match(r"^\((\d+)[^)]*\)", title)
        
        last_count = getattr(webview, "last_notification_count", 0)
        
        if match:
            current_count = int(match.group(1))
            if current_count > last_count:
                try:
                    subprocess.Popen([
                        "notify-send",
                        "-a", "Mise",
                        "New Message",
                        f"{current_count} unread in {title[match.end():].strip()}"
                    ])
                except Exception:
                    pass
            webview.last_notification_count = current_count
        else:
            webview.last_notification_count = 0

        active_ws = self.workspace_engine.current_workspace
        active_tabs = self.workspace_engine.workspaces[active_ws]
        if webview in active_tabs:
            index = active_tabs.index(webview)
            display_title = (
                title[:28] + "..." if len(title) > 28 else title
            ) or "New Tab"
            try:
                self.tab_list.item(index).setText(display_title)
            except AttributeError:
                pass

    def update_url_field(self, webview, url):
        active_ws = self.workspace_engine.current_workspace
        active_tabs = self.workspace_engine.workspaces[active_ws]
        current_index = self.tab_list.currentRow()
        
        if current_index != -1 and current_index < len(active_tabs):
            if active_tabs[current_index] == webview:
                self.url_bar.setText(url.toString())

    def eventFilter(self, watched, event):
        from PyQt6.QtCore import QEvent
        if event.type() == QEvent.Type.KeyPress:
            self.keyPressEvent(event)
            if event.isAccepted():
                return True
        return False

    def hot_reload_theme(self):

        self.setStyleSheet("")
        fresh_css = get_browser_stylesheet(self.is_dark_layout)
        self.setStyleSheet(fresh_css)
        
        if hasattr(self, "sidebar_widget"):
            self.sidebar_widget.style().unpolish(self.sidebar_widget)
            self.sidebar_widget.style().polish(self.sidebar_widget)
            self.sidebar_widget.update()
    
        self.workspace_label.setText(
            f"{self.workspace_engine.current_workspace}"
        )
    
        self.shared_profile.settings().setAttribute(
            QWebEngineSettings.WebAttribute.ForceDarkMode, self.is_dark_layout
        )
        
        # Clear out any stale custom scripts to prevent persistent style overrides
        scripts = self.shared_profile.scripts()
        for script in scripts.toList():
            if script.name() == "theme_override":
                scripts.remove(script)
        
        bg_hex = "#c6d1d1" if self.is_dark_layout else "#f5f6f9"
        canvas_colour = QColor(bg_hex)
    
        for ws_name, tabs in self.workspace_engine.workspaces.items():
            for webview in tabs:
                if not isinstance(webview, str):
                    webview.settings().setAttribute(
                        QWebEngineSettings.WebAttribute.ForceDarkMode, self.is_dark_layout
                    )
                    if webview.page():
                        webview.page().setBackgroundColor(canvas_colour)
                        
                    if webview.isVisible():
                        webview.reload()
        
        if self.dashboard_active:
            self.dashboard_view.refresh_view_data()
            
        self.update()

    def restore_active_workspace_tabs(self):
            """Constructs web views for every saved URL mapping belonging to the entire session layout on initialization."""
            self.workspace_label.setText(f"{self.workspace_engine.current_workspace}")
            session_file = os.path.expanduser("~/.config/mise/session.json")
            all_workspaces_config = {self.workspace_engine.current_workspace: ["https://duckduckgo.com"]}
            
            if os.path.exists(session_file):
                try:
                    with open(session_file, "r", encoding="utf-8") as f:
                        session_data = json.load(f)
                    saved_groups = session_data.get("workspaces", {})
                    if saved_groups:
                        all_workspaces_config = saved_groups
                except Exception:
                    pass
    
            for ws_name, urls in all_workspaces_config.items():
                self.workspace_engine.create_workspace_record(ws_name)
                
                if ws_name == self.workspace_engine.current_workspace:
                    for url in urls:
                        if url == "about:blank" or not url.strip():
                            url = "https://duckduckgo.com"
                        self.add_new_tab(url, ws_name, force_focus=False)
                else:
                    self.workspace_engine.workspaces[ws_name] = []
                    self.workspace_engine.session_strings_cache[ws_name] = urls
    
            if self.tab_list.count() > 0:
                self.tab_list.setCurrentRow(0)
                self.switch_tab(0, force_focus=False)
    
            self.hot_reload_theme()


    def closeEvent(self, event):
        self.workspace_engine.save_session()
        event.accept()

    def toggle_address_bar(self):
        """Toggles a floating overlay address bar populated with the active tab's URL for viewing or modification."""
        if self.url_bar.isVisible():
            self.url_bar.hide()
            active_ws = self.workspace_engine.current_workspace
            current_idx = self.tab_list.currentRow()
            tabs = self.workspace_engine.workspaces.get(active_ws, [])
            
            if 0 <= current_idx < len(tabs) and not isinstance(tabs[current_idx], str):
                try:
                    tabs[current_idx].setFocus()
                except RuntimeError:
                    pass
        else:
            active_ws = self.workspace_engine.current_workspace
            current_idx = self.tab_list.currentRow()
            tabs = self.workspace_engine.workspaces.get(active_ws, [])
            
            # Populate the address bar with the current tab's URL if it exists
            if 0 <= current_idx < len(tabs) and not isinstance(tabs[current_idx], str):
                current_url = tabs[current_idx].url().toString()
                # Clear out fallback blank states for a cleaner typing experience
                if current_url == "about:blank":
                    self.url_bar.clear()
                else:
                    self.url_bar.setText(current_url)
                    self.url_bar.selectAll() # Highlight text for quick replacement searches
            else:
                self.url_bar.clear()
            
            parent_widget = self.url_bar.parentWidget()
            if parent_widget:
                self.url_bar.setGeometry(10, 10, parent_widget.width() - 20, 50)
            
            self.url_bar.show()
            self.url_bar.setFocus()
            self.url_bar.raise_()

    def navigate_to_url(self):
        input_text = self.url_bar.text().strip()
        if not input_text:
            return

        active_ws = self.workspace_engine.current_workspace
        current_index = self.tab_list.currentRow()
        tabs = self.workspace_engine.workspaces.get(active_ws, [])
        
        if current_index == -1 or current_index >= len(tabs) or isinstance(tabs[current_index], str):
            return

        clean_host = input_text.split('/')[0].lower()
        is_ip = any(clean_host.startswith(prefix) for prefix in ["192.168.", "10.", "172."]) or clean_host.startswith("127.0.")
        is_local_host = any(clean_host.startswith(host) for host in ["localhost", "router", "gateway"])
        has_tld = any(tld in clean_host for tld in [".com", ".org", ".net", ".cz", ".uk", ".moe", ".local", ".lan", ".gov", ".edu"])

        if " " in input_text:
            url = f"https://duckduckgo.com/?q={input_text.replace(' ', '+')}"
        elif input_text.startswith(("http://", "https://")):
            url = input_text
        elif is_ip or is_local_host or has_tld:
            url = f"http://{input_text}" if is_ip else f"https://{input_text}"
        else:
            url = f"https://duckduckgo.com/?q={input_text.replace(' ', '+')}"

        try:
            target_webview = tabs[current_index]
            target_webview.setUrl(QUrl(url))
            
            if self.content_area.indexOf(target_webview) == -1:
                self.content_area.addWidget(target_webview)
            
            target_webview.show()
            target_webview.setFocus()
        except RuntimeError:
            pass

        self.url_bar.hide()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, "url_bar") and self.url_bar.isVisible():
            parent_widget = self.url_bar.parentWidget()
            if parent_widget:
                self.url_bar.setGeometry(10, 10, parent_widget.width() - 20, 50)

    def navigate_back(self):
        if self.dashboard_active:
            return
        active_ws = self.workspace_engine.current_workspace
        current_idx = self.tab_list.currentRow()
        tabs = self.workspace_engine.workspaces.get(active_ws, [])
        if 0 <= current_idx < len(tabs) and not isinstance(tabs[current_idx], str):
            try:
                tabs[current_idx].back()
            except RuntimeError:
                pass

    def navigate_forward(self):
        if self.dashboard_active:
            return
        active_ws = self.workspace_engine.current_workspace
        current_idx = self.tab_list.currentRow()
        tabs = self.workspace_engine.workspaces.get(active_ws, [])
        if 0 <= current_idx < len(tabs) and not isinstance(tabs[current_idx], str):
            try:
                tabs[current_idx].forward()
            except RuntimeError:
                pass

    def toggle_theme_mode(self):
        """Swaps layout configuration parameters and updates active sidebar toggle components."""
        self.is_dark_layout = not self.is_dark_layout
        self.theme_toggle_btn.setText("󰖔" if self.is_dark_layout else "󰖨")
        self.hot_reload_theme()

    def handle_incoming_download(self, download_item):
        """Intercepts engine download triggers and prompts the native portal picker."""
        from PyQt6.QtWidgets import QFileDialog
        from PyQt6.QtCore import QDir

        suggested_name = download_item.suggestedFileName()
        default_dir = os.path.expanduser("~/Downloads")
        os.makedirs(default_dir, exist_ok=True)

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save File As",
            os.path.join(default_dir, suggested_name)
        )

        if file_path:
            target_dir = os.path.dirname(file_path)
            target_name = os.path.basename(file_path)

            download_item.setDownloadDirectory(target_dir)
            download_item.setDownloadFileName(target_name)
            download_item.accept()

            self.workspace_label.setText(f" Downloading: {target_name[:20]}...")

            download_item.isFinishedChanged.connect(
                lambda: self.workspace_label.setText(f" {self.workspace_engine.current_workspace}")
            )
        else:
            download_item.cancel()

    def toggle_notification_service(self):
        """Triggers the worker toggle function and updates the interface indicator icon state."""
        is_active = self.notification_worker.toggle_state()
        
        # Swap between active bell and disabled bell indicators
        self.noti_toggle_btn.setText("󰂚" if is_active else "󰂛")

    def trigger_link_hints(self):
        """Executes the injected JavaScript function to paint navigation overlays on the current canvas."""
        active_ws = self.workspace_engine.current_workspace
        current_idx = self.tab_list.currentRow()
        tabs = self.workspace_engine.workspaces.get(active_ws, [])
        
        if 0 <= current_idx < len(tabs) and not isinstance(tabs[current_idx], str):
            try:
                tabs[current_idx].page().runJavaScript("window.toggleHints();")
            except RuntimeError:
                pass
    def show_help_menu(self):
        """Instantiates and displays the modal reference overlay asynchronously."""
        self.help_overlay = HelpMenu(self, self.is_dark_layout)
        self.help_overlay.show()
        
    def open_settings_window(self):
        from config import SettingsDialog
        dialog = SettingsDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Inform the user that core system flag updates apply cleanly upon app restart
            self.workspace_label.setText(" Settings saved. Restart required.")

    def open_command_palette(self):
        theme_colors = {
            "bg_main": "#1a1b26" if self.is_dark_layout else "#f5f6f9",
            "text": "#c0caf5" if self.is_dark_layout else "#3c3e4f",
            "border": "#24283b" if self.is_dark_layout else "#d2d3db",
            "selected": "#364a85" if self.is_dark_layout else "#cfe2fe"
        }
        
        commands = {
            "Toggle Theme": self.toggle_theme_mode,
            "Toggle Dashboard": self.toggle_dashboard_view,
            "Focus Address Bar": self.toggle_address_bar,
            "Show Help": self.show_help_menu,
            "Close Current": self.close_current_tab,
            "Save Workspace": self.quick_save_workspace,
            "Open Settings": self.open_settings_window,
            "Clear Cookies": self.clear_active_site_cookies,
            "Clear Cache": self.clear_active_site_cache
        }
        self.palette = CommandPalette(self, commands, theme_colors)
        self.palette.show()

    def run_in_terminal(self, command):
        """Copies text cleanly to the global clipboard and opens a platform-appropriate terminal."""
        if not command.strip():
            return

        # Use built-in cross-platform Qt clipboard instead of wl-copy
        QApplication.clipboard().setText(command)
            
        import platform
        system_platform = platform.system()

        try:
            if system_platform == "Linux":
                # Check for standard minimalist terminal setups
                for term in ["kitty", "alacritty", "foot", "st", "xterm"]:
                    if subprocess.run(["which", term], capture_output=True).returncode == 0:
                        subprocess.Popen([term])
                        return
                # Fallback to general terminal desktop executor if specific TUIs aren't matched
                subprocess.Popen(["xdg-terminal-exec"])
                
            elif system_platform == "Windows":
                # Launch Windows Terminal if available, fallback to classic cmd
                import shutil
                if shutil.which("wt"):
                    subprocess.Popen(["wt"])
                else:
                    subprocess.Popen(["cmd"], creationflags=subprocess.CREATE_NEW_CONSOLE)
                    
            elif system_platform == "Darwin":
                # Launch default macOS Terminal via open binary
                subprocess.Popen(["open", "-a", "Terminal"])
        except Exception:
            pass
    
    def purge_site_data(domain_name):
        """
        Finds and deletes all persistent cookies matching a specific domain 
        and triggers an asynchronous network cache clear.
        """
        profile = QWebEngineProfile.defaultProfile()
        cookie_store = profile.cookieStore()
        
        # Simple sanitisation to ensure subdomains match correctly
        target_domain = domain_name.lower().strip()
        if not target_domain.startswith("."):
            # Catch cases where cookie domains start with a dot
            dot_domain = f".{target_domain}"
        else:
            dot_domain = target_domain
            target_domain = target_domain.lstrip(".")
    
        def cookie_filter(cookie):
            cookie_domain = cookie.domain().lower()
            # Delete if the cookie domain matches exactly or is a subdomain variation
            if cookie_domain == target_domain or cookie_domain == dot_domain or cookie_domain.endswith(dot_domain):
                cookie_store.deleteCookie(cookie)
    
        # Iterates through the cookie jar asynchronously and applies the filter logic
        cookie_store.loadAllCookies()
        cookie_store.cookieAdded.connect(cookie_filter)
        
        # Clear the global HTTP memory and disk cache layers asynchronously
        profile.clearHttpCache()

    def toggle_private_browsing(self):
        """Switches the private mode state and updates the status indicator."""
        status = self.privacy_manager.toggle_private_browsing()
    
        active_ws = self.workspace_engine.current_workspace
        self.workspace_label.setText(f"{active_ws} 󰕥  : {status}")

    def clear_active_site_cookies(self):
        """Surgically purges cookies for the active domain via the privacy module."""
        current_view = getattr(self, 'current_active_view', None)
        result_msg = self.privacy_manager.clear_site_cookies(current_view)
        
        # Calling the worker instance directly passing two separate text string arguments
        if hasattr(self, 'notification_worker'):
            self.notification_worker.handle_incoming_notification("Mise Security", result_msg)

    def clear_active_site_cache(self):
        """Clears the HTTP cache layer via the privacy module safely."""
        result_msg = self.privacy_manager.clear_cache()
        
        # Calling the worker instance directly passing two separate text string arguments
        if hasattr(self, 'notification_worker'):
            self.notification_worker.handle_incoming_notification("Mise System", result_msg)
        
if __name__ == "__main__":
    import sys
    from config import initialize_engine_switches
    
    # Configure hardware optimization arguments before QApplication initializes the socket
    initialize_engine_switches()

    app = QApplication(sys.argv)
    app.__version__ = "0.1.0"
    browser = MiseBrowser()
    app.installEventFilter(browser)

    browser.show()
    browser.restore_active_workspace_tabs()
    
    sys.exit(app.exec())

import json
import os
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QDragEnterEvent, QDropEvent, QKeyEvent, QFont
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QLineEdit,
    QLabel,
)
from PyQt6.QtWebEngineWidgets import QWebEngineView


class WorkspaceDashboard(QWidget):

    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.manager = main_window.workspace_engine

        layout = QVBoxLayout()
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)

        header = QLabel("Workspaces")
        header.setObjectName("DashboardHeader")
        layout.addWidget(header)

        self.view_tree = QListWidget()
        self.view_tree.setObjectName("DashboardTree")
        self.view_tree.setDragEnabled(True)
        self.view_tree.setAcceptDrops(True)
        self.view_tree.setDropIndicatorShown(True)

        self.view_tree.itemDoubleClicked.connect(self.handle_double_click)
        self.view_tree.keyPressEvent = self._tree_key_press

        # Wire up index selection triggers cleanly to follow row offsets
        self.view_tree.currentRowChanged.connect(self._handle_row_selection)

        self.view_tree.dragEnterEvent = self._drag_enter_event
        self.view_tree.dropEvent = self._drop_event
        layout.addWidget(self.view_tree)

        add_btn = QPushButton("[+] New Workspace Group")
        add_btn.setObjectName("DashboardBtn")
        add_btn.clicked.connect(self.add_workspace_entry)
        layout.addWidget(add_btn)

        self.setLayout(layout)

    def refresh_view_data(self):
        self.view_tree.clear()

        for ws_name, tabs in self.manager.workspaces.items():
            ws_header = QListWidgetItem(f" {ws_name}")
            ws_header.setData(Qt.ItemDataRole.UserRole, ("workspace", ws_name))
            workspace_font = QFont("Noto Sans", 16)
            workspace_font.setBold(True)
            ws_header.setFont(workspace_font)

            if ws_name == self.manager.current_workspace:
                ws_header.setText(f" {ws_name} (Active)")

            self.view_tree.addItem(ws_header)

            valid_tabs = []

            if not tabs and ws_name in self.manager.session_strings_cache:
                for url in self.manager.session_strings_cache[ws_name]:
                    display_string = f"    󰈙  {url[:50]}..."
                    tab_item = QListWidgetItem(display_string)
                    tab_item.setData(
                        Qt.ItemDataRole.UserRole, ("tab", ws_name, len(valid_tabs))
                    )
                    self.view_tree.addItem(tab_item)
                    valid_tabs.append(url)
            else:
                for idx, webview in enumerate(tabs):
                    try:
                        # Get title from WebView or cache
                        ws_titles = self.manager.session_titles_cache.get(ws_name, [])
                        
                        if isinstance(webview, str):
                            title = ws_titles[idx] if idx < len(ws_titles) else "Inactive Tab"
                            url = webview
                        else:
                            title = webview.title() or (ws_titles[idx] if idx < len(ws_titles) else "Loading...")
                            url = webview.url().toString()
                        
                        display_string = (
                            f"    󰈙  {title[:30]}... ({url[:40]}...)"
                            if len(title) > 30
                            else f"    󰈙  {title} ({url[:40]}...)"
                        )

                        tab_item = QListWidgetItem(display_string)
                        tab_item.setData(
                            Qt.ItemDataRole.UserRole, ("tab", ws_name, len(valid_tabs))
                        )
                        self.view_tree.addItem(tab_item)
                        valid_tabs.append(webview)
                    except (RuntimeError, AttributeError):
                        pass

            self.manager.workspaces[ws_name] = valid_tabs

    def add_workspace_entry(self):
        self.manager.create_workspace_record()
        self.refresh_view_data()

    def handle_double_click(self, item):
        payload = item.data(Qt.ItemDataRole.UserRole)
        if not payload:
            return

        node_type = payload[0]

        if node_type == "tab":
            _, target_ws, target_tab_idx = payload
            self.manager.switch_workspace_record(target_ws)
            self.main_window.tab_list.setCurrentRow(target_tab_idx)
            self.main_window.close_dashboard()

        elif node_type == "workspace":
            _, old_name = payload
            self.inline_rename_workspace(item, old_name)

    def inline_rename_workspace(self, item, old_name):
        edit_field = QLineEdit()
        edit_field.setText(old_name)
        edit_field.setObjectName("InlineRenameField")

        self.view_tree.setItemWidget(item, edit_field)
        edit_field.setFocus()
        edit_field.selectAll()

        has_run = False

        def save_name():
            nonlocal has_run
            if has_run:
                return
            has_run = True

            try:
                edit_field.returnPressed.disconnect()
                edit_field.editingFinished.disconnect()
            except Exception:
                pass

            new_name = edit_field.text().strip()
            self.view_tree.removeItemWidget(item)

            if new_name and new_name != old_name:
                self.manager.rename_workspace_record(old_name, new_name)

            self.refresh_view_data()

        edit_field.returnPressed.connect(save_name)
        edit_field.editingFinished.connect(save_name)

    def _handle_row_selection(self, row_idx):

        pass

    def _tree_key_press(self, event: QKeyEvent):
        item = self.view_tree.currentItem()
        if not item:
            return

        payload = item.data(Qt.ItemDataRole.UserRole)

        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if payload:
                if payload[0] == "workspace":
                    target_ws = payload[1]
                    # Only switch the engine record when explicitly confirmed via Enter
                    self.manager.switch_workspace_record(target_ws, track_focus=False)
                    self.refresh_view_data()
                elif payload[0] == "tab":
                    _, target_ws, target_tab_idx = payload
                    # Force the manager to target the selected workspace context cleanly
                    self.manager.switch_workspace_record(target_ws, track_focus=True)
                    self.main_window.tab_list.setCurrentRow(target_tab_idx)
                    self.main_window.close_dashboard()
            event.accept()

        elif event.key() == Qt.Key.Key_Delete:
            if payload:
                self.main_window.execute_inline_removal(payload)
                self.refresh_view_data()
            event.accept()
        else:
            super(QListWidget, self.view_tree).keyPressEvent(event)

    def _drag_enter_event(self, event: QDragEnterEvent):
        item = self.view_tree.currentItem()
        if item:
            payload = item.data(Qt.ItemDataRole.UserRole)
            if payload and payload[0] == "tab":
                event.acceptProposedAction()

    def _drop_event(self, event: QDropEvent):
        target_item = self.view_tree.itemAt(event.position().toPoint())
        source_item = self.view_tree.currentItem()

        if not target_item or not source_item:
            return

        source_payload = source_item.data(Qt.ItemDataRole.UserRole)
        target_payload = target_item.data(Qt.ItemDataRole.UserRole)

        if not source_payload or not target_payload:
            return

        _, source_ws, source_tab_idx = source_payload
        target_ws = target_payload[1]

        if source_ws != target_ws:
            webview = self.manager.workspaces[source_ws].pop(source_tab_idx)
            self.manager.workspaces[target_ws].append(webview)

            if source_ws == self.manager.current_workspace:
                self.main_window.tab_list.takeItem(source_tab_idx)

            self.refresh_view_data()
            event.acceptProposedAction()


class WorkspaceEngine:

    def __init__(self, main_window):
        self.main_window = main_window
        self.session_file = os.path.expanduser("~/.config/mise/session.json")
        self.workspaces = {}
        self.session_strings_cache = {}
        self.session_titles_cache = {}
        self.current_workspace = "Workspace 1"
        self.load_session()

    # ... (other methods)

    def switch_workspace_record(self, target_ws, track_focus=False):
        if target_ws == self.current_workspace:
            return

        # Dehydrate current workspace: Cache URLs and titles, then destroy widgets to free memory
        current_tabs = self.workspaces[self.current_workspace]
        self.session_strings_cache[self.current_workspace] = []
        self.session_titles_cache[self.current_workspace] = []
        
        for webview in current_tabs:
            if not isinstance(webview, str):
                self.session_strings_cache[self.current_workspace].append(webview.url().toString())
                self.session_titles_cache[self.current_workspace].append(webview.title())
                
                webview.hide()
                self.main_window.content_area.removeWidget(webview)
                
                if webview.page():
                    webview.page().deleteLater()
                webview.deleteLater()
            else:
                self.session_strings_cache[self.current_workspace].append(webview)
                self.session_titles_cache[self.current_workspace].append("Inactive")

        # Mark all as dehydrated
        self.workspaces[self.current_workspace] = ["dehydrated"] * len(current_tabs)

        self.current_workspace = target_ws
        self.main_window.workspace_label.setText(f" {target_ws}")
        self.main_window.tab_list.clear()

        # Rehydrate target workspace
        if not self.workspaces[target_ws] or isinstance(self.workspaces[target_ws][0], str):
            urls_to_load = self.session_strings_cache.get(target_ws, ["https://duckduckgo.com"])
            self.workspaces[target_ws] = []
            for url in urls_to_load:
                self.main_window.add_new_tab(url, target_ws, force_focus=track_focus)
            self.main_window.hot_reload_theme()
            
            if self.main_window.dashboard_active:
                self.main_window.dashboard_view.refresh_view_data()
            return

        valid_target_tabs = [w for w in self.workspaces[target_ws] if not isinstance(w, str)]

        for idx, webview in enumerate(valid_target_tabs):
            try:
                webview.titleChanged.connect(
                    lambda title, wv=webview: self.main_window.update_tab_titles(wv, title)
                )
                webview.urlChanged.connect(
                    lambda url, wv=webview: self.main_window.update_url_field(wv, url)
                )

                self.main_window.content_area.addWidget(webview)

                title = webview.title() or "Loading..."
                display_title = (title[:24] + "...") if len(title) > 24 else title
                self.main_window.tab_list.addItem(display_title)
                
                if idx == 0:
                    webview.show()
                    # Hand over layout focus tracking parameters directly back to the main window core
                    self.main_window.current_active_view = webview
                else:
                    webview.hide()
            except RuntimeError:
                pass

        if self.main_window.tab_list.count() > 0:
            self.main_window.tab_list.setCurrentRow(0)
            self.main_window.switch_tab(0, force_focus=track_focus)

    def save_session(self):
        session_data = {
            "current_workspace": self.current_workspace,
            "workspaces": {},
        }

        for ws_name, tabs in self.workspaces.items():
            if tabs and not isinstance(tabs[0], str):
                urls = [webview.url().toString() for webview in tabs if webview.url().isValid()]
                session_data["workspaces"][ws_name] = urls if urls else ["https://duckduckgo.com"]
            else:
                session_data["workspaces"][ws_name] = self.session_strings_cache.get(
                    ws_name, ["https://duckduckgo.com"]
                )

        try:
            os.makedirs(os.path.dirname(self.session_file), exist_ok=True)
            with open(self.session_file, "w", encoding="utf-8") as f:
                json.dump(session_data, f, indent=4)
        except Exception:
            pass

    def create_workspace_record(self, name=None):
        if name is None:
            next_index = len(self.workspaces) + 1
            name = f"Workspace {next_index}"
        if name not in self.workspaces:
            self.workspaces[name] = []
        return name

    def load_session(self):
        if os.path.exists(self.session_file):
            try:
                with open(self.session_file, "r", encoding="utf-8") as f:
                    session_data = json.load(f)

                saved_workspaces = session_data.get("workspaces", {})
                
                # Dynamically choose the first workspace key available instead of "Workspace 1"
                fallback_name = list(saved_workspaces.keys())[0] if saved_workspaces else "Workspace 1"
                self.current_workspace = session_data.get("current_workspace", fallback_name)

                if saved_workspaces:
                    for ws_name, urls in saved_workspaces.items():
                        self.workspaces[ws_name] = []
                        self.session_strings_cache[ws_name] = urls
                    return
            except Exception:
                pass

        self.workspaces = {"Workspace 1": []}

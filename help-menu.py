from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel

class HelpMenu(QDialog):
    def __init__(self, parent=None, is_dark=True):
        super().__init__(parent)
        self.setWindowTitle("Mise Reference")
        self.setModal(True)
        self.resize(550, 600)
        
        layout = QVBoxLayout(self)
        
        reference_text = """
Navigation & Workspaces
--------------------------------------------------
Ctrl + T           New DuckDuckGo Tab
Ctrl + L           Toggle Floating Address Bar
Ctrl + W           Close Current Tab (or Node)
Ctrl + Shift + W   Toggle Workspace Dashboard
Ctrl + S           Quick Save Active Workspace
Ctrl + R           Reload Active Tab
Ctrl + D           Quick Remove Current
Ctrl + M           Focus Sidebar Tab List
Ctrl + B           Focus Active Webview
Enter              Switch to Selected Sidebar Tab

Web Interaction
--------------------------------------------------
Ctrl + F           Toggle Link Hints Overlay
Right Click        Contextual Actions + (Arch Wiki)
Ctrl + Shift + P   Toggle Private Browsing On/Off

Sidebar Controls
--------------------------------------------------
Sun/Moon Icon      Toggle Light/Dark Layout
Bell Icon          Toggle Web Notifications
        """
        
        text_label = QLabel(reference_text)
        
        bg_colour = "#124647" if is_dark else "#f5f6f9"
        text_colour = "#c0caf5" if is_dark else "#3c3e4f"
        
        self.setStyleSheet(f"""
            background-color: {bg_colour}; 
            color: {text_colour}; 
            font-family: monospace; 
            font-size: 14px; 
            padding: 20px;
        """)
        
        layout.addWidget(text_label)

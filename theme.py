def get_browser_stylesheet(is_dark=True):
    if is_dark:
        colors = {
            "bg_main": "#1a1b26",
            "bg_sidebar": "#16161e",
            "text": "#c0caf5",
            "accent": "#2ac3de",
            "border": "#24283b",
            "selected": "#364a85"
        }
    else:
        colors = {
            "bg_main": "#c6d1d1",
            "bg_sidebar": "#e1e2e7",
            "text": "#3c3e4f",
            "accent": "#007acc",
            "border": "#d2d3db",
            "selected": "#cfe2fe"
        }

    return f"""
        QMainWindow {{
            background-color: {colors["bg_main"]};
        }}
        QWidget#Sidebar, QWidget#Sidebar > QWidget {{
            background-color: {colors["bg_sidebar"]};
            border-right: 1px solid {colors["border"]};
        }}
        QLabel#WorkspaceLabel {{
            color: {colors["text"]};
            font-weight: bold;
            font-size: 20px;
            padding: 6px;
            background: transparent;
        }}
        QListWidget#TabList, QListWidget#DashboardTree {{
            background-color: transparent;
            border: none;
            font-size: 14px;
            color: {colors["text"]};
        }}
        QListWidget#TabList::item, QListWidget#DashboardTree::item {{
            padding: 8px;
            border-radius: 4px;
            font-size: 14px;
        }}
        QListWidget#TabList::item:selected, QListWidget#DashboardTree::item:selected {{
            background-color: {colors["selected"]};
            color: {colors["text"]};
        }}
        QLineEdit#WideAddressBar {{
            background-color: {colors["bg_main"]};
            color: {colors["text"]};
            border: 1px solid {colors["border"]};
            border-radius: 6px;
            padding: 8px;
        }}
        QPushButton#NavIconButton, QPushButton#ThemeToggleBtn, QPushButton#NotiToggleBtn {{
            background-color: transparent;
            color: {colors["text"]};
            font-size: 18px;
            border: none;
            border-radius: 4px;
            padding: 4px;
        }}
        QPushButton#NavIconButton:hover, QPushButton#ThemeToggleBtn:hover, QPushButton#NotiToggleBtn:hover {{
            background-color: {colors["selected"]};
        }}
        
        QLabel#DashboardHeader {{
            color: {colors["text"]};
            font-size: 24px;
            font-weight: bold;
            background: transparent;
        }}
        QPushButton#DashboardBtn {{
            background-color: {colors["bg_sidebar"]};
            color: {colors["text"]};
            font-size: 16px;
            border: 1px solid {colors["border"]};
            border-radius: 4px;
            padding: 8px;
        }}
        QPushButton#DashboardBtn:hover {{
            background-color: {colors["selected"]};
        }}
        QMenu#ContextMenu {{
            background-color: {colors["bg_sidebar"]};
            border: 1px solid {colors["border"]};
            border-radius: 8px;
            padding: 6px 0px;
        }}
        QMenu#ContextMenu::item {{
            color: {colors["text"]};
            padding: 10px 44px 10px 20px;
            font-size: 14px;
            font-family: sans-serif;
        }}
        QMenu#ContextMenu::item:selected {{
            background-color: {colors["selected"]};
            color: {colors["text"]};
        }}
        QMenu#ContextMenu::item:disabled {{
            color: {colors["border"]};
        }}
        QMenu#ContextMenu::separator {{
            height: 1px;
            background-color: {colors["border"]};
            margin: 6px 0px;
        }}
    """

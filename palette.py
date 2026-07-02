from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLineEdit, QListWidget, QListWidgetItem
from PyQt6.QtCore import Qt

class CommandPalette(QDialog):
    def __init__(self, parent, commands, theme_colors):
        super().__init__(parent)
        self.commands = commands
        self.theme = theme_colors
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.resize(600, 400)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        self.input = QLineEdit(self)
        self.input.setPlaceholderText("Search commands...")
        self.input.textChanged.connect(self.filter_commands)
        layout.addWidget(self.input)

        self.list = QListWidget(self)
        self.list.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.list.itemActivated.connect(self.execute_command)
        layout.addWidget(self.list)

        self.setStyleSheet(f"""
            QDialog {{
                background-color: rgba(22, 22, 30, 0.95);
                border: 1px solid {self.theme["border"]};
                border-radius: 8px;
            }}
            QLineEdit {{
                background-color: {self.theme["bg_main"]};
                color: {self.theme["text"]};
                border: 1px solid {self.theme["border"]};
                border-radius: 4px;
                padding: 10px;
                font-size: 14px;
            }}
            QListWidget {{
                background-color: transparent;
                border: none;
                color: {self.theme["text"]};
                font-size: 14px;
            }}
            QListWidget::item {{
                padding: 12px;
                border-radius: 4px;
            }}
            QListWidget::item:selected {{
                background-color: {self.theme["selected"]};
                color: {self.theme["text"]};
            }}
        """)

        self.populate_list(list(self.commands.keys()))
        self.input.setFocus()

    def populate_list(self, items):
        self.list.clear()
        for item in items:
            self.list.addItem(QListWidgetItem(item))
        if self.list.count() > 0:
            self.list.setCurrentRow(0)

    def filter_commands(self, text):
        search = text.lower()
        matches = [cmd for cmd in self.commands if search in cmd.lower()]
        self.populate_list(matches)

    def execute_command(self, item=None):
        # Prefer the selected item, fall back to the input text
        cmd_text = item.text() if item else self.input.text()
        
        if cmd_text in self.commands:
            self.commands[cmd_text]()
        else:
            # Treat as a raw shell command
            self.parent().run_in_terminal(cmd_text)
        self.close()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.close()
        elif event.key() == Qt.Key.Key_Down:
            self.list.setCurrentRow((self.list.currentRow() + 1) % self.list.count())
        elif event.key() == Qt.Key.Key_Up:
            self.list.setCurrentRow((self.list.currentRow() - 1) % self.list.count())
        elif event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            # Execute selected item if available, or the raw text in input
            item = self.list.currentItem()
            self.execute_command(item)
        else:
            super().keyPressEvent(event)

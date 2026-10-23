from PySide6.QtCore import QTimer, Qt
from PySide6.QtWidgets import QLabel, QWidget


class Toast(QLabel):
    def __init__(self, parent: QWidget, text: str, error: bool = False):
        super().__init__(text, parent)
        color = "#A63D40" if error else "#24735B"
        self.setStyleSheet(f"background:{color}; color:white; padding:12px 18px; border-radius:7px;")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.adjustSize()
        self.move(parent.width() - self.width() - 25, 70)
        self.show()
        QTimer.singleShot(3500, self.deleteLater)


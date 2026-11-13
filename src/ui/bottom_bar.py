from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QWidget


class BottomBar(QWidget):
    refreshRequested = pyqtSignal()
    prevRequested = pyqtSignal()
    nextRequested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        self.status_label = QLabel("Источник: Яндекс")
        self.status_label.setObjectName("statusLabel")

        self.prev_button = QPushButton("← Назад")
        self.prev_button.clicked.connect(self.prevRequested.emit)
        self.prev_button.setEnabled(False)

        self.refresh_button = QPushButton("Обновить")
        self.refresh_button.clicked.connect(self.refreshRequested.emit)

        self.next_button = QPushButton("Дальше →")
        self.next_button.setObjectName("primaryBtn")
        self.next_button.clicked.connect(self.nextRequested.emit)

        layout.addWidget(self.status_label)
        layout.addStretch()
        layout.addWidget(self.prev_button)
        layout.addWidget(self.refresh_button)
        layout.addWidget(self.next_button)

    def set_status(self, text: str):
        self.status_label.setText(text)

    def set_page(self, page: int):
        self.prev_button.setEnabled(page > 0)

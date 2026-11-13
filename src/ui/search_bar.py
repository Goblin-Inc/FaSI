from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QComboBox, QHBoxLayout, QLineEdit, QPushButton, QWidget


class SearchBar(QWidget):
    searchRequested = pyqtSignal(str, str)  # query, provider_key
    providerChanged = pyqtSignal(str)

    PROVIDERS_MAP = {
        "Яндекс": "yandex",
        "Google": "google",
        "DuckDuckGo": "ddg",
    }

    def __init__(self, default_provider: str = "yandex", parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        self.search_input = QLineEdit()
        self.search_input.setObjectName("searchInput")
        self.search_input.setPlaceholderText("Введите запрос, например: обои 1920x1080")
        self.search_input.returnPressed.connect(self._emit_search)

        self.clear_button = QPushButton("×")
        self.clear_button.setObjectName("clearBtn")
        self.clear_button.setFixedWidth(42)
        self.clear_button.setToolTip("Очистить запрос")
        self.clear_button.clicked.connect(self.search_input.clear)

        self.provider_combo = QComboBox()
        for label, key in self.PROVIDERS_MAP.items():
            self.provider_combo.addItem(label, key)

        idx = self.provider_combo.findData(default_provider)
        if idx >= 0:
            self.provider_combo.setCurrentIndex(idx)

        self.provider_combo.currentIndexChanged.connect(self._on_provider_changed)

        self.search_button = QPushButton("Поиск")
        self.search_button.setObjectName("primaryBtn")
        self.search_button.clicked.connect(self._emit_search)

        layout.addWidget(self.search_input, 1)
        layout.addWidget(self.clear_button)
        layout.addWidget(self.provider_combo)
        layout.addWidget(self.search_button)

    def current_provider_key(self) -> str:
        return self.provider_combo.currentData() or "yandex"

    def current_provider_display(self) -> str:
        return self.provider_combo.currentText()

    def query_text(self) -> str:
        return self.search_input.text().strip()

    def set_query_text(self, text: str):
        self.search_input.setText(text)

    def _on_provider_changed(self):
        self.providerChanged.emit(self.current_provider_key())
        self._emit_search()

    def _emit_search(self):
        self.searchRequested.emit(self.query_text(), self.current_provider_key())

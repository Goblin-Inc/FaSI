from pathlib import Path
from typing import Dict
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeySequence, QShortcut
from PyQt6.QtWidgets import QMainWindow, QVBoxLayout, QWidget

from src.core.config import config
from src.core.hotkey_manager import HotkeyManager
from src.core.image_worker import ImageWorkerPool, SearchTask
from src.providers import BaseProvider
from src.providers.ddg_providers import DDGProvider
from src.providers.google_providers import GoogleProvider
from src.providers.yandex_providers import YandexProvider

from .bottom_bar import BottomBar
from .image_grid import ImageGrid
from .search_bar import SearchBar


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FaSI — Fast Search Images")
        self.resize(1220, 820)

        # Полупрозрачное окно с мягким фоном
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setWindowOpacity(0.96)

        self.worker_pool = ImageWorkerPool()
        self.providers: Dict[str, BaseProvider] = {
            "yandex": YandexProvider(),
            "google": GoogleProvider(),
            "ddg": DDGProvider(),
        }

        self.current_page = 0
        self.current_query = "обои 1920x1080"
        self.current_provider_key = config.get("default_provider", "yandex")

        self._load_stylesheet()
        self._build_ui()
        self._setup_shortcuts()

        # Подключаем C++ глобальный хоткей (Alt+Space)
        self.hotkey_manager = HotkeyManager(self)
        self.hotkey_manager.activated.connect(self.toggle_visibility)
        self.hotkey_manager.start()

        # Первичный поиск при старте
        self.search_bar.set_query_text(self.current_query)
        self.start_search(self.current_query, self.current_provider_key, reset_page=True)

    def _load_stylesheet(self):
        qss_path = Path(__file__).resolve().parent / "styles.qss"
        if qss_path.exists():
            with open(qss_path, "r", encoding="utf-8") as f:
                self.setStyleSheet(f.read())

    def _build_ui(self):
        central = QWidget()
        central.setObjectName("centralWidget")
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(16)

        self.search_bar = SearchBar(default_provider=self.current_provider_key)
        self.search_bar.searchRequested.connect(
            lambda q, p: self.start_search(q, p, reset_page=True)
        )

        self.image_grid = ImageGrid(self.worker_pool)
        self.image_grid.statusMessage.connect(self.on_status_message)

        self.bottom_bar = BottomBar()
        self.bottom_bar.refreshRequested.connect(self.refresh_page)
        self.bottom_bar.prevRequested.connect(self.prev_page)
        self.bottom_bar.nextRequested.connect(self.next_page)

        main_layout.addWidget(self.search_bar)
        main_layout.addWidget(self.image_grid, 1)
        main_layout.addWidget(self.bottom_bar)

        self.setCentralWidget(central)

    def _setup_shortcuts(self):
        esc_shortcut = QShortcut(QKeySequence("Escape"), self)
        esc_shortcut.activated.connect(self.search_bar.search_input.setFocus)

    def toggle_visibility(self):
        if self.isVisible() and self.isActiveWindow():
            self.hide()
        else:
            self.showNormal()
            self.raise_()
            self.activateWindow()
            self.search_bar.search_input.setFocus()
            self.search_bar.search_input.selectAll()

    def start_search(self, query: str, provider_key: str, reset_page: bool = False):
        if not query:
            query = "обои 1920x1080"
        if reset_page:
            self.current_page = 0

        self.current_query = query
        self.current_provider_key = provider_key
        config.set("default_provider", provider_key)

        provider = self.providers.get(provider_key, self.providers["yandex"])
        self.setWindowTitle(f"FaSI — {query} ({provider.display_name})")
        self.bottom_bar.set_page(self.current_page)
        self.bottom_bar.set_status(
            f"Источник: {provider.display_name}  •  Страница {self.current_page + 1}  •  Поиск..."
        )
        self.image_grid.show_message("Загрузка изображений...")

        count = config.get("results_per_page", 20)
        task = SearchTask(provider, query, self.current_page, count)
        task.signals.finished.connect(self._on_search_finished)
        task.signals.error.connect(self._on_search_error)
        self.worker_pool.start(task)

    def _on_search_finished(self, results: list):
        provider = self.providers.get(self.current_provider_key, self.providers["yandex"])
        self.bottom_bar.set_status(
            f"Источник: {provider.display_name}  •  Страница {self.current_page + 1}  •  Найдено: {len(results)}"
        )
        self.image_grid.populate(results)

    def _on_search_error(self, error_msg: str):
        self.bottom_bar.set_status(f"Ошибка поиска: {error_msg}")
        self.image_grid.show_message(f"Ошибка при поиске: {error_msg}")

    def on_status_message(self, msg: str):
        provider = self.providers.get(self.current_provider_key, self.providers["yandex"])
        self.bottom_bar.set_status(f"Источник: {provider.display_name}  •  {msg}")

    def refresh_page(self):
        self.start_search(self.current_query, self.current_provider_key, reset_page=False)

    def next_page(self):
        self.current_page += 1
        self.start_search(self.current_query, self.current_provider_key, reset_page=False)

    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.start_search(self.current_query, self.current_provider_key, reset_page=False)

    def closeEvent(self, event):
        self.hotkey_manager.stop()
        super().closeEvent(event)

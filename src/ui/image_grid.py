from typing import List
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QImage
from PyQt6.QtWidgets import QGridLayout, QLabel, QScrollArea, QWidget

from src.core.image_worker import ImageDownloadTask, ImageWorkerPool
from src.providers import ImageResult
from .image_card import ImageCard


class ImageGrid(QScrollArea):
    statusMessage = pyqtSignal(str)

    def __init__(self, worker_pool: ImageWorkerPool, parent=None):
        super().__init__(parent)
        self.worker_pool = worker_pool
        self.cards: List[ImageCard] = []

        self.setObjectName("resultsArea")
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.container = QWidget()
        self.grid_layout = QGridLayout(self.container)
        self.grid_layout.setSpacing(14)
        self.grid_layout.setContentsMargins(10, 10, 10, 10)
        for col in range(4):
            self.grid_layout.setColumnStretch(col, 1)
        self.setWidget(self.container)

    def clear_grid(self):
        self.cards.clear()
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def show_message(self, text: str):
        self.clear_grid()
        lbl = QLabel(text)
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet("color: #cbd5e1; font-size: 16px; padding: 40px;")
        self.grid_layout.addWidget(lbl, 0, 0, 1, 4)

    def populate(self, results: List[ImageResult]):
        self.clear_grid()
        if not results:
            self.show_message("Ничего не найдено. Попробуйте другой запрос.")
            return

        for idx, item in enumerate(results):
            card = ImageCard(item, self.worker_pool)
            card.statusMessage.connect(self.statusMessage.emit)
            self.cards.append(card)

            row = idx // 4
            col = idx % 4
            self.grid_layout.addWidget(card, row, col)

            dl_task = ImageDownloadTask(idx, item.thumb_url, item.full_url)
            dl_task.signals.loaded.connect(self._on_thumb_loaded)
            dl_task.signals.failed.connect(self._on_thumb_failed)
            self.worker_pool.start(dl_task)

    def _on_thumb_loaded(self, idx: int, img: QImage, raw: bytes):
        if 0 <= idx < len(self.cards):
            self.cards[idx].set_image(img, raw)

    def _on_thumb_failed(self, idx: int):
        if 0 <= idx < len(self.cards):
            self.cards[idx].set_failed()

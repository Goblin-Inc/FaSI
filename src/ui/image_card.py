import os
import re
from pathlib import Path
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)

from src.core.config import config
from src.core.image_worker import FullImageTask, ImageWorkerPool
from src.providers import ImageResult
from src.utils.clipboard import copy_image_to_clipboard


class ImageCard(QFrame):
    statusMessage = pyqtSignal(str)

    def __init__(self, result: ImageResult, worker_pool: ImageWorkerPool, parent=None):
        super().__init__(parent)
        self.result = result
        self.worker_pool = worker_pool
        self.loaded_image: QImage | None = None
        self.raw_bytes: bytes = b""

        self.setObjectName("imageCard")
        self.setFixedHeight(265)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        self.image_label = QLabel("Загрузка...")
        self.image_label.setObjectName("imagePreview")
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setFixedHeight(170)
        layout.addWidget(self.image_label)

        clean_title = (result.title or "Изображение").strip()
        if len(clean_title) > 52:
            clean_title = clean_title[:49] + "..."
        self.title_label = QLabel(clean_title)
        self.title_label.setObjectName("cardTitle")
        self.title_label.setWordWrap(True)
        layout.addWidget(self.title_label)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        self.copy_btn = QPushButton("📋 В буфер")
        self.copy_btn.setObjectName("copyCardBtn")
        self.copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.copy_btn.clicked.connect(self.on_copy_clicked)

        self.download_btn = QPushButton("💾 Скачать")
        self.download_btn.setObjectName("downloadCardBtn")
        self.download_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.download_btn.clicked.connect(self.on_download_clicked)

        btn_row.addWidget(self.copy_btn)
        btn_row.addWidget(self.download_btn)
        layout.addLayout(btn_row)

    def set_image(self, image: QImage, raw_bytes: bytes):
        self.loaded_image = image
        self.raw_bytes = raw_bytes
        pixmap = QPixmap.fromImage(image)
        scaled = pixmap.scaled(
            300,
            170,
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.image_label.setPixmap(scaled)

    def set_failed(self):
        self.image_label.setText("Недоступно")

    def on_copy_clicked(self):
        self.copy_btn.setText("⏳...")
        self.copy_btn.setEnabled(False)
        task = FullImageTask(self.result.full_url, self.result.thumb_url)
        task.signals.finished.connect(self._finish_copy)
        task.signals.error.connect(self._fallback_copy)
        self.worker_pool.start(task)

    def _finish_copy(self, img: QImage, _raw: bytes):
        copy_image_to_clipboard(img)
        self.copy_btn.setText("✓ Скопировано")
        self.copy_btn.setEnabled(True)
        self.statusMessage.emit("Картинка скопирована в буфер обмена!")

    def _fallback_copy(self, _err: str):
        if self.loaded_image and not self.loaded_image.isNull():
            copy_image_to_clipboard(self.loaded_image)
            self.copy_btn.setText("✓ Скопировано")
            self.statusMessage.emit("Превью скопировано в буфер обмена!")
        else:
            self.copy_btn.setText("📋 В буфер")
            self.statusMessage.emit("Ошибка копирования изображения")
        self.copy_btn.setEnabled(True)

    def on_download_clicked(self):
        default_dir = config.get("download_path", str(Path.home() / "Pictures"))
        safe_name = re.sub(r'[^a-zA-Z0-9а-яА-Я_\-]+', '_', self.result.title or "image").strip("_")[:40]
        if not safe_name:
            safe_name = "fasi_image"
        default_path = os.path.join(default_dir, f"{safe_name}.png")

        save_path, _ = QFileDialog.getSaveFileName(
            self,
            "Сохранить изображение",
            default_path,
            "Изображения (*.png *.jpg *.jpeg *.webp);;Все файлы (*)",
        )
        if not save_path:
            return

        config.set("download_path", str(Path(save_path).parent))
        self.download_btn.setText("⏳...")
        self.download_btn.setEnabled(False)

        task = FullImageTask(self.result.full_url, self.result.thumb_url)
        task.signals.finished.connect(lambda img, raw: self._finish_save(save_path, img, raw))
        task.signals.error.connect(lambda _err: self._fallback_save(save_path))
        self.worker_pool.start(task)

    def _finish_save(self, save_path: str, img: QImage, raw: bytes):
        try:
            if not img.save(save_path):
                with open(save_path, "wb") as f:
                    f.write(raw)
            self.download_btn.setText("✓ Скачано")
            self.statusMessage.emit(f"Сохранено: {save_path}")
        except Exception as e:
            self.download_btn.setText("💾 Скачать")
            self.statusMessage.emit(f"Ошибка сохранения: {e}")
        self.download_btn.setEnabled(True)

    def _fallback_save(self, save_path: str):
        if self.loaded_image and not self.loaded_image.isNull():
            self.loaded_image.save(save_path)
            self.download_btn.setText("✓ Скачано")
            self.statusMessage.emit(f"Сохранено: {save_path}")
        else:
            self.download_btn.setText("💾 Скачать")
            self.statusMessage.emit("Не удалось скачать изображение")
        self.download_btn.setEnabled(True)

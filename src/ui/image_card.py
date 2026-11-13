import os
import re
from pathlib import Path
from PyQt6.QtCore import Qt, QRect, pyqtSignal
from PyQt6.QtGui import QImage, QPainter, QPainterPath, QPixmap
from PyQt6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from src.core.config import config
from src.core.image_worker import FullImageTask, ImageWorkerPool
from src.providers import ImageResult
from src.utils.clipboard import copy_image_to_clipboard


class ImagePreviewWidget(QLabel):
    """Виджет превью, который аккуратно заполняет блок без растягивания сетки."""

    def __init__(self, text: str = "Загрузка...", parent=None):
        super().__init__(text, parent)
        self.setObjectName("imagePreview")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setFixedHeight(165)
        self.setMinimumWidth(100)
        self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Fixed)
        self._pixmap: QPixmap | None = None

    def set_preview_pixmap(self, pixmap: QPixmap):
        self._pixmap = pixmap
        self.setText("")
        self.update()

    def paintEvent(self, event):
        if self._pixmap and not self._pixmap.isNull():
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

            path = QPainterPath()
            path.addRoundedRect(0.0, 0.0, float(self.width()), float(self.height()), 12.0, 12.0)
            painter.setClipPath(path)

            scaled = self._pixmap.scaled(
                self.size(),
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation,
            )
            x = (self.width() - scaled.width()) // 2
            y = (self.height() - scaled.height()) // 2
            painter.drawPixmap(x, y, scaled)
            painter.end()
        else:
            super().paintEvent(event)


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
        self.setMinimumWidth(180)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        self.image_label = ImagePreviewWidget("Загрузка...")
        layout.addWidget(self.image_label)

        clean_title = (result.title or "Изображение").strip()
        if len(clean_title) > 42:
            clean_title = clean_title[:39] + "..."
        self.title_label = QLabel(clean_title)
        self.title_label.setObjectName("cardTitle")
        self.title_label.setFixedHeight(20)
        self.title_label.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Fixed)
        layout.addWidget(self.title_label)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        self.copy_btn = QPushButton("📋 В буфер")
        self.copy_btn.setObjectName("copyCardBtn")
        self.copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.copy_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.copy_btn.clicked.connect(self.on_copy_clicked)

        self.download_btn = QPushButton("💾 Скачать")
        self.download_btn.setObjectName("downloadCardBtn")
        self.download_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.download_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.download_btn.clicked.connect(self.on_download_clicked)

        btn_row.addWidget(self.copy_btn)
        btn_row.addWidget(self.download_btn)
        layout.addLayout(btn_row)

    def set_image(self, image: QImage, raw_bytes: bytes):
        self.loaded_image = image
        self.raw_bytes = raw_bytes
        pixmap = QPixmap.fromImage(image)
        self.image_label.set_preview_pixmap(pixmap)

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

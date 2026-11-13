import requests
from typing import List
from PyQt6.QtCore import QObject, QRunnable, QThreadPool, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QImage

from src.providers import BaseProvider, ImageResult
from .config import config


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/128.0.0.0 Safari/537.36"
    ),
    "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
}


class SearchSignals(QObject):
    finished = pyqtSignal(list)
    error = pyqtSignal(str)


class SearchTask(QRunnable):
    def __init__(self, provider: BaseProvider, query: str, page: int, count: int):
        super().__init__()
        self.provider = provider
        self.query = query
        self.page = page
        self.count = count
        self.signals = SearchSignals()

    @pyqtSlot()
    def run(self):
        try:
            items: List[ImageResult] = self.provider.search(
                self.query, page=self.page, count=self.count
            )
            self.signals.finished.emit(items)
        except Exception as e:
            self.signals.error.emit(str(e))


class ImageDownloadSignals(QObject):
    loaded = pyqtSignal(int, QImage, bytes)
    failed = pyqtSignal(int)


class ImageDownloadTask(QRunnable):
    def __init__(self, index: int, thumb_url: str, full_url: str = ""):
        super().__init__()
        self.index = index
        self.thumb_url = thumb_url
        self.full_url = full_url
        self.signals = ImageDownloadSignals()

    @pyqtSlot()
    def run(self):
        timeout = config.get("timeout", 10)
        for url in (self.thumb_url, self.full_url):
            if not url:
                continue
            try:
                resp = requests.get(url, headers=HEADERS, timeout=timeout)
                resp.raise_for_status()
                raw_bytes = resp.content
                img = QImage()
                if img.loadFromData(raw_bytes) and not img.isNull():
                    self.signals.loaded.emit(self.index, img, raw_bytes)
                    return
            except Exception:
                continue
        self.signals.failed.emit(self.index)


class FullImageSignals(QObject):
    finished = pyqtSignal(QImage, bytes)
    error = pyqtSignal(str)


class FullImageTask(QRunnable):
    def __init__(self, full_url: str, fallback_url: str = ""):
        super().__init__()
        self.full_url = full_url
        self.fallback_url = fallback_url
        self.signals = FullImageSignals()

    @pyqtSlot()
    def run(self):
        timeout = config.get("timeout", 10)
        for url in (self.full_url, self.fallback_url):
            if not url:
                continue
            try:
                resp = requests.get(url, headers=HEADERS, timeout=timeout)
                resp.raise_for_status()
                raw = resp.content
                img = QImage()
                if img.loadFromData(raw) and not img.isNull():
                    self.signals.finished.emit(img, raw)
                    return
            except Exception as e:
                last_err = str(e)
        self.signals.error.emit("Не удалось загрузить оригинал изображения")


class ImageWorkerPool:
    def __init__(self):
        self.pool = QThreadPool.globalInstance()
        self.pool.setMaxThreadCount(8)

    def start(self, task: QRunnable):
        self.pool.start(task)

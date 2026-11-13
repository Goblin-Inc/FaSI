from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List


@dataclass
class ImageResult:
    thumb_url: str
    full_url: str
    title: str
    source: str
    width: int = 0
    height: int = 0


class BaseProvider(ABC):
    name: str = "base"
    display_name: str = "Base"

    HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/128.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
    }

    @abstractmethod
    def search(self, query: str, page: int = 0, count: int = 20) -> List[ImageResult]:
        pass
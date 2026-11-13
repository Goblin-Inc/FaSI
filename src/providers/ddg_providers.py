from typing import List
from duckduckgo_search import DDGS
from . import BaseProvider, ImageResult


class DDGProvider(BaseProvider):
    name = "ddg"
    display_name = "DuckDuckGo"

    def search(self, query: str, page: int = 0, count: int = 20) -> List[ImageResult]:
        results: List[ImageResult] = []
        try:
            max_results = (page + 1) * count
            with DDGS() as ddgs:
                ddg_gen = ddgs.images(
                    keywords=query,
                    region="ru-ru",
                    safesearch="off",
                    max_results=max_results
                )
                all_items = list(ddg_gen)

            start_idx = page * count
            for item in all_items[start_idx:start_idx + count]:
                results.append(ImageResult(
                    thumb_url=item.get("thumbnail", ""),
                    full_url=item.get("image", ""),
                    title=item.get("title", query),
                    source=self.display_name,
                    width=int(item.get("width", 0) or 0),
                    height=int(item.get("height", 0) or 0)
                ))
        except Exception as e:
            print(f"[DDGProvider] Ошибка поиска: {e}")

        return results
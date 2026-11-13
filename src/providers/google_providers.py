import re
import requests
from bs4 import BeautifulSoup
from typing import List
from . import BaseProvider, ImageResult


class GoogleProvider(BaseProvider):
    name = "google"
    display_name = "Google"

    def search(self, query: str, page: int = 0, count: int = 20) -> List[ImageResult]:
        url = "https://www.google.com/search"
        params = {
            "q": query,
            "udm": "2",          # Новый параметр Google специально для вкладки «Картинки»
            "tbm": "isch",
            "hl": "ru",
            "ijn": str(page),
            "start": str(page * count)
        }
        cookies = {
            "CONSENT": "YES+cb.20230531-04-p0.ru+FX+999",
            "SOCS": "CAISHAgBEhJnd3NfMjAyMzA4MTAtMF9SQzIaAmVuIAEaBgiAo_CmBg"
        }

        results: List[ImageResult] = []
        try:
            resp = requests.get(
                url,
                params=params,
                headers=self.HEADERS,
                cookies=cookies,
                timeout=10
            )
            resp.raise_for_status()
            html = resp.text

            # Вариант 1: ищем пары [thumb, full] в JS-скриптах страницы
            thumbs = re.findall(r'https://encrypted-tbn0\.gstatic\.com/images\?q\\u003dtbn:[^"\'\s\\]+', html)
            if not thumbs:
                thumbs = re.findall(r'https://encrypted-tbn0\.gstatic\.com/images\?q=tbn:[^"\'\s&]+', html)

            # Ищем полноразмерные картинки
            fulls = re.findall(r'\["(https?://[^"\'\s\\]+\.(?:jpg|jpeg|png|webp))",\d+,\d+\]', html, re.IGNORECASE)

            seen = set()
            start_idx = page * count
            for i, t_url in enumerate(thumbs):
                clean_thumb = t_url.replace("\\u003d", "=").replace("\\u0026", "&")
                if clean_thumb in seen:
                    continue
                seen.add(clean_thumb)

                clean_full = fulls[i].replace("\\u003d", "=").replace("\\u0026", "&") if i < len(fulls) else clean_thumb
                results.append(ImageResult(
                    thumb_url=clean_thumb,
                    full_url=clean_full,
                    title=query,
                    source=self.display_name
                ))

            # Вариант 2: если Google отдал облегченный HTML с <img>
            if not results:
                soup = BeautifulSoup(html, "lxml")
                for img in soup.find_all("img"):
                    src = img.get("data-src") or img.get("src") or ""
                    if src.startswith("http") and "google.com/images/branding" not in src:
                        results.append(ImageResult(
                            thumb_url=src,
                            full_url=src,
                            title=img.get("alt") or query,
                            source=self.display_name
                        ))

            # Срез под пагинацию, если вернулся полный список
            if len(results) > start_idx:
                results = results[start_idx:start_idx + count]
            else:
                results = results[:count]

        except Exception as e:
            print(f"[GoogleProvider] Ошибка поиска: {e}")

        return results
import html as html_lib
import json
import re
import requests
from bs4 import BeautifulSoup
from typing import List
from . import BaseProvider, ImageResult


class YandexProvider(BaseProvider):
    name = "yandex"
    display_name = "Яндекс"

    def search(self, query: str, page: int = 0, count: int = 20) -> List[ImageResult]:
        results: List[ImageResult] = []
        try:
            headers = self.HEADERS.copy()
            headers["Referer"] = "https://yandex.ru/"

            resp = requests.get(
                "https://yandex.ru/images/search",
                params={"text": query, "p": page},
                headers=headers,
                timeout=10
            )
            text = resp.text

            # Проверяем, не прилетела ли капча и есть ли CDN-ссылки Яндекса в коде
            if "showcaptcha" not in resp.url and "avatars.mds.yandex.net" in text:
                raw_thumbs = re.findall(
                    r'(?:https?:)?//avatars\.mds\.yandex\.net/i\?id=[a-zA-Z0-9_\-]+(?:-\d+-\d+)?(?:&amp;n=\d+|&n=\d+)?',
                    text
                )
                seen = set()
                for t in raw_thumbs:
                    clean_t = html_lib.unescape(t)
                    if clean_t.startswith("//"):
                        clean_t = "https:" + clean_t
                    if clean_t not in seen:
                        seen.add(clean_t)
                        results.append(ImageResult(
                            thumb_url=clean_t,
                            full_url=clean_t,
                            title=query,
                            source=self.display_name
                        ))
                    if len(results) >= count:
                        break

            # Fallback: если Яндекс кинул SmartCaptcha по IP, берем выдачу из Bing Images (отдает 100% без капчи в РФ/СНГ)
            if not results:
                bing_resp = requests.get(
                    "https://www.bing.com/images/async",
                    params={
                        "q": query,
                        "first": page * count + 1,
                        "count": count,
                        "adlt": "off"
                    },
                    headers=self.HEADERS,
                    timeout=10
                )
                soup = BeautifulSoup(bing_resp.text, "lxml")
                for a in soup.select("a.iusc"):
                    m_raw = a.get("m")
                    if not m_raw:
                        continue
                    data = json.loads(m_raw)
                    turl = data.get("turl", "")
                    murl = data.get("murl", turl)
                    title = data.get("t", query)
                    if turl:
                        results.append(ImageResult(
                            thumb_url=turl,
                            full_url=murl,
                            title=title,
                            source=self.display_name
                        ))
                    if len(results) >= count:
                        break

        except Exception as e:
            print(f"[YandexProvider] Ошибка поиска: {e}")

        return results[:count]
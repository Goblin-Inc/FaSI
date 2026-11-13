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
        seen_ids = set()
        try:
            headers = self.HEADERS.copy()
            headers["Referer"] = "https://yandex.ru/"

            resp = requests.get(
                "https://yandex.ru/images/search",
                params={"text": query, "p": page},
                headers=headers,
                timeout=10,
            )
            unescaped = html_lib.unescape(resp.text)

            # 1. Структурированный парсинг карточек Яндекса (с origUrl и alt-заголовками)
            if "showcaptcha" not in resp.url and "avatars.mds.yandex.net" in unescaped:
                card_pattern = re.compile(
                    r'"image"\s*:\s*"((?:https?:)?//avatars\.mds\.yandex\.net/i\?id=[^"]+)"'
                    r'[^}]*?"alt"\s*:\s*"([^"]*)"'
                    r'[^}]*?"origUrl"\s*:\s*"([^"]+)"'
                )
                for thumb_raw, alt_text, orig_url in card_pattern.findall(unescaped):
                    clean_thumb = ("https:" + thumb_raw) if thumb_raw.startswith("//") else thumb_raw
                    id_match = re.search(r'id=([a-zA-Z0-9_\-]+)', clean_thumb)
                    img_id = id_match.group(1) if id_match else clean_thumb
                    if img_id in seen_ids:
                        continue
                    seen_ids.add(img_id)

                    clean_title = alt_text.replace('\\"', '"').strip() or query
                    clean_orig = orig_url.replace("\\/", "/") if orig_url else clean_thumb
                    results.append(
                        ImageResult(
                            thumb_url=clean_thumb,
                            full_url=clean_orig,
                            title=clean_title,
                            source=self.display_name,
                        )
                    )
                    if len(results) >= count:
                        break

                # 2. Если структурированных совпадений меньше count — добираем уникальные CDN-превью
                if len(results) < count:
                    raw_thumbs = re.findall(
                        r'(?:https?:)?//avatars\.mds\.yandex\.net/i\?id=[a-zA-Z0-9_\-]+(?:-images-thumbs)?(?:&n=\d+)?',
                        unescaped,
                    )
                    for t in raw_thumbs:
                        clean_t = ("https:" + t) if t.startswith("//") else t
                        id_match = re.search(r'id=([a-zA-Z0-9_\-]+)', clean_t)
                        img_id = id_match.group(1) if id_match else clean_t
                        if img_id not in seen_ids:
                            seen_ids.add(img_id)
                            results.append(
                                ImageResult(
                                    thumb_url=clean_t,
                                    full_url=clean_t,
                                    title=query,
                                    source=self.display_name,
                                )
                            )
                        if len(results) >= count:
                            break

            # 3. Fallback: если Яндекс вернул капчу
            if not results:
                bing_resp = requests.get(
                    "https://www.bing.com/images/async",
                    params={
                        "q": query,
                        "first": page * count + 1,
                        "count": count,
                        "adlt": "off",
                    },
                    headers=self.HEADERS,
                    timeout=10,
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
                    if turl and turl not in seen_ids:
                        seen_ids.add(turl)
                        results.append(
                            ImageResult(
                                thumb_url=turl,
                                full_url=murl,
                                title=title,
                                source=self.display_name,
                            )
                        )
                    if len(results) >= count:
                        break

        except Exception as e:
            print(f"[YandexProvider] Ошибка поиска: {e}")

        return results[:count]

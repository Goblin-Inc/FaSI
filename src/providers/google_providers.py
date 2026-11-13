import json
import re
import requests
from bs4 import BeautifulSoup
from typing import List
from . import BaseProvider, ImageResult


class GoogleProvider(BaseProvider):
    name = "google"
    display_name = "Google"

    def search(self, query: str, page: int = 0, count: int = 20) -> List[ImageResult]:
        results: List[ImageResult] = []
        seen = set()

        # 1. Прямой запрос к Google Images (если не заблокирован JS-редиректом)
        try:
            url = "https://www.google.com/search"
            params = {
                "q": query,
                "udm": "2",
                "tbm": "isch",
                "hl": "ru",
                "ijn": str(page),
                "start": str(page * count),
            }
            cookies = {
                "CONSENT": "YES+cb.20230531-04-p0.ru+FX+999",
                "SOCS": "CAISHAgBEhJnd3NfMjAyMzA4MTAtMF9SQzIaAmVuIAEaBgiAo_CmBg",
            }
            resp = requests.get(
                url,
                params=params,
                headers=self.HEADERS,
                cookies=cookies,
                timeout=8,
            )
            html = resp.text

            if "/httpservice/retry/enablejs" not in html:
                thumbs = re.findall(
                    r'https://encrypted-tbn0\.gstatic\.com/images\?q\\u003dtbn:[^"\'\s\\]+',
                    html,
                )
                if not thumbs:
                    thumbs = re.findall(
                        r'https://encrypted-tbn0\.gstatic\.com/images\?q=tbn:[^"\'\s&]+',
                        html,
                    )
                fulls = re.findall(
                    r'\["(https?://[^"\'\s\\]+\.(?:jpg|jpeg|png|webp))",\d+,\d+\]',
                    html,
                    re.IGNORECASE,
                )

                for i, t_url in enumerate(thumbs):
                    clean_thumb = t_url.replace("\\u003d", "=").replace("\\u0026", "&")
                    if clean_thumb in seen:
                        continue
                    seen.add(clean_thumb)
                    clean_full = (
                        fulls[i].replace("\\u003d", "=").replace("\\u0026", "&")
                        if i < len(fulls)
                        else clean_thumb
                    )
                    results.append(
                        ImageResult(
                            thumb_url=clean_thumb,
                            full_url=clean_full,
                            title=query,
                            source=self.display_name,
                        )
                    )
                    if len(results) >= count:
                        return results
        except Exception as e:
            print(f"[GoogleProvider] Direct request warning: {e}")

        # 2. Надёжный безключевой веб-индекс (Bing Async Image Index), если Google требует JS-выполнение
        try:
            bing_resp = requests.get(
                "https://www.bing.com/images/async",
                params={
                    "q": query,
                    "first": page * count + 1,
                    "count": count + 10,
                    "adlt": "off",
                    "qft": "+filterui:photo-photo",
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
                title = data.get("t") or data.get("desc") or query
                if turl and turl not in seen:
                    seen.add(turl)
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
            print(f"[GoogleProvider] Fallback error: {e}")

        return results[:count]

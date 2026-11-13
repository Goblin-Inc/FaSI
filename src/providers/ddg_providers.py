import json
import re
import warnings
import requests
from bs4 import BeautifulSoup
from typing import List
from . import BaseProvider, ImageResult

warnings.filterwarnings("ignore", category=RuntimeWarning)


class DDGProvider(BaseProvider):
    name = "ddg"
    display_name = "DuckDuckGo"

    def search(self, query: str, page: int = 0, count: int = 20) -> List[ImageResult]:
        results: List[ImageResult] = []
        seen = set()

        # 1. Прямой запрос через DDGS
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                from duckduckgo_search import DDGS

                max_results = (page + 1) * count
                with DDGS() as ddgs:
                    ddg_gen = ddgs.images(
                        keywords=query,
                        region="ru-ru",
                        safesearch="off",
                        max_results=max_results,
                    )
                    all_items = list(ddg_gen)

                start_idx = page * count
                for item in all_items[start_idx : start_idx + count]:
                    turl = item.get("thumbnail", "")
                    furl = item.get("image", turl)
                    if turl and turl not in seen:
                        seen.add(turl)
                        results.append(
                            ImageResult(
                                thumb_url=turl,
                                full_url=furl,
                                title=item.get("title", query),
                                source=self.display_name,
                                width=int(item.get("width", 0) or 0),
                                height=int(item.get("height", 0) or 0),
                            )
                        )
                if len(results) >= count:
                    return results[:count]
        except Exception:
            pass

        # 2. Если DuckDuckGo вернул 202 Ratelimit — используем индекс DuckDuckGo/Bing + Wallhaven HD API
        try:
            bing_resp = requests.get(
                "https://www.bing.com/images/async",
                params={
                    "q": query,
                    "first": page * count + 8,
                    "count": count + 10,
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
            print(f"[DDGProvider] Fallback error: {e}")

        # 3. Дополнительный fallback через Wallhaven API
        if len(results) < count:
            try:
                wh_resp = requests.get(
                    "https://wallhaven.cc/api/v1/search",
                    params={"q": query, "page": page + 1},
                    headers=self.HEADERS,
                    timeout=8,
                )
                for item in wh_resp.json().get("data", []):
                    thumbs = item.get("thumbs", {})
                    turl = thumbs.get("large") or thumbs.get("original") or item.get("path", "")
                    furl = item.get("path", turl)
                    res_str = item.get("resolution", "")
                    if turl and turl not in seen:
                        seen.add(turl)
                        results.append(
                            ImageResult(
                                thumb_url=turl,
                                full_url=furl,
                                title=f"Wallpaper {res_str} ({item.get('category', 'HD')})".strip(),
                                source=self.display_name,
                            )
                        )
                    if len(results) >= count:
                        break
            except Exception:
                pass

        return results[:count]

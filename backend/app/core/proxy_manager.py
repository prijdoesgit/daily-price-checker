import random
from typing import Optional
from app.core.config import settings


class ProxyManager:
    def __init__(self):
        self._proxies = settings.proxy_list_parsed
        self._failed: set[str] = set()
        self._success_count: dict[str, int] = {}

    def get_proxy(self) -> Optional[dict]:
        available = [p for p in self._proxies if p not in self._failed]
        if not available:
            self._failed.clear()
            available = self._proxies

        if not available:
            return None

        proxy_url = random.choice(available)
        return {"server": proxy_url}

    def get_brightdata_proxy(self) -> Optional[dict]:
        if not all([settings.BRIGHTDATA_USERNAME, settings.BRIGHTDATA_PASSWORD, settings.BRIGHTDATA_HOST]):
            return None
        session_id = random.randint(100000, 999999)
        username = f"{settings.BRIGHTDATA_USERNAME}-session-{session_id}-country-in"
        return {
            "server": f"http://{settings.BRIGHTDATA_HOST}",
            "username": username,
            "password": settings.BRIGHTDATA_PASSWORD,
        }

    def mark_failed(self, proxy_url: str):
        self._failed.add(proxy_url)

    def mark_success(self, proxy_url: str):
        self._failed.discard(proxy_url)
        self._success_count[proxy_url] = self._success_count.get(proxy_url, 0) + 1

    def get_best_proxy(self) -> Optional[dict]:
        brightdata = self.get_brightdata_proxy()
        if brightdata:
            return brightdata
        return self.get_proxy()

    @property
    def has_proxies(self) -> bool:
        return bool(self._proxies) or bool(settings.BRIGHTDATA_HOST)


proxy_manager = ProxyManager()

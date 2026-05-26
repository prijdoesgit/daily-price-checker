import asyncio
import random
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from playwright.async_api import async_playwright, Browser, BrowserContext, Page, TimeoutError as PWTimeout

from app.core.anti_bot import (
    configure_stealth_page, human_delay, simulate_human_scroll,
    get_playwright_launch_args, get_random_headers
)
from app.core.proxy_manager import proxy_manager
from app.core.config import settings

log = structlog.get_logger()


@dataclass
class ScrapedPrice:
    platform_slug: str
    medication_name: str
    strength: str
    price: Optional[float]
    mrp: Optional[float]
    discount_pct: Optional[float]
    is_available: bool
    product_url: Optional[str]
    product_name_raw: Optional[str]
    pack_info: Optional[str] = None
    scraped_at: datetime = field(default_factory=datetime.utcnow)


class BaseScraper(ABC):
    platform_slug: str = ""
    platform_name: str = ""
    base_url: str = ""

    def __init__(self):
        self.log = structlog.get_logger(platform=self.platform_slug)

    async def scrape_all_medications(self, medications: list[dict]) -> list[ScrapedPrice]:
        results = []
        browser = None
        try:
            async with async_playwright() as pw:
                launch_args = get_playwright_launch_args()
                proxy = proxy_manager.get_best_proxy()
                if proxy:
                    launch_args["proxy"] = proxy
                browser = await pw.chromium.launch(**launch_args)
                context = await browser.new_context(
                    user_agent=get_random_headers().get("User-Agent"),
                    locale="en-IN",
                    timezone_id="Asia/Kolkata",
                    viewport={"width": 1366, "height": 768},
                )
                await context.set_extra_http_headers(get_random_headers())

                for med in medications:
                    try:
                        page_results = await self._scrape_medication(context, med)
                        results.extend(page_results)
                        await human_delay(settings.SCRAPING_DELAY_MIN, settings.SCRAPING_DELAY_MAX)
                    except Exception as e:
                        self.log.warning("Failed to scrape medication", medication=med.get("name"), error=str(e))

        except Exception as e:
            self.log.error("Scraper crashed", error=str(e))
        finally:
            if browser:
                await browser.close()

        return results

    @abstractmethod
    async def _scrape_medication(self, context, medication: dict) -> list[ScrapedPrice]:
        """Scrape prices for a single medication on this platform."""
        pass

    async def _safe_get_text(self, page: Page, selector: str, default: Optional[str] = None) -> Optional[str]:
        try:
            el = await page.query_selector(selector)
            if el:
                return (await el.text_content() or "").strip()
        except Exception:
            pass
        return default

    def _parse_price(self, price_str: Optional[str]) -> Optional[float]:
        if not price_str:
            return None
        cleaned = price_str.replace("₹", "").replace(",", "").replace("MRP", "").strip()
        try:
            return float(cleaned)
        except (ValueError, TypeError):
            return None

    def _calc_discount(self, price: Optional[float], mrp: Optional[float]) -> Optional[float]:
        if price and mrp and mrp > 0:
            return round((1 - price / mrp) * 100, 1)
        return None

    def _build_search_url(self, medication_name: str, strength: str) -> str:
        query = f"{medication_name} {strength}".strip()
        return self._format_search_url(query)

    def _format_search_url(self, query: str) -> str:
        import urllib.parse
        return f"{self.base_url}/search?q={urllib.parse.quote(query)}"

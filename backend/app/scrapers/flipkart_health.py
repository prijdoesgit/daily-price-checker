import urllib.parse
from app.scrapers.base import BaseScraper, ScrapedPrice
from app.core.anti_bot import configure_stealth_page, human_delay


class FlipkartHealthScraper(BaseScraper):
    platform_slug = "flipkart_health"
    platform_name = "Flipkart Health+"
    base_url = "https://www.flipkarthealthplus.com"

    def _format_search_url(self, query: str) -> str:
        return f"{self.base_url}/search?q={urllib.parse.quote(query)}"

    async def _scrape_medication(self, context, medication: dict) -> list[ScrapedPrice]:
        results = []
        name = medication["name"]
        strength = medication["strength"]
        page = await context.new_page()
        await configure_stealth_page(page)
        search_url = self._build_search_url(name, strength)
        try:
            await page.goto(search_url, wait_until="domcontentloaded", timeout=30000)
            await human_delay(2.0, 4.0)
            cards = await page.query_selector_all('[class*="product"], [class*="Product"]')
            for card in cards[:2]:
                try:
                    price_el = await card.query_selector('[class*="price"]')
                    price = self._parse_price((await price_el.text_content()) if price_el else None)
                    link_el = await card.query_selector("a")
                    href = await link_el.get_attribute("href") if link_el else None
                    product_url = f"{self.base_url}{href}" if href and href.startswith("/") else href
                    if price:
                        results.append(ScrapedPrice(platform_slug=self.platform_slug, medication_name=name, strength=strength,
                            price=price, mrp=price, discount_pct=None, is_available=True, product_url=product_url, product_name_raw=None))
                        break
                except Exception:
                    continue
        except Exception as e:
            self.log.warning("Flipkart Health scrape failed", name=name, error=str(e))
        finally:
            await page.close()
        if not results:
            results.append(ScrapedPrice(platform_slug=self.platform_slug, medication_name=name, strength=strength,
                price=None, mrp=None, discount_pct=None, is_available=False, product_url=search_url, product_name_raw=None))
        return results

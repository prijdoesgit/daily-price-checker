import urllib.parse
from typing import Optional
from app.scrapers.base import BaseScraper, ScrapedPrice
from app.core.anti_bot import configure_stealth_page, human_delay, simulate_human_scroll


class PharmEasyScraper(BaseScraper):
    platform_slug = "pharmeasy"
    platform_name = "PharmEasy"
    base_url = "https://pharmeasy.in"

    def _format_search_url(self, query: str) -> str:
        return f"{self.base_url}/search/all?name={urllib.parse.quote(query)}"

    async def _scrape_medication(self, context, medication: dict) -> list[ScrapedPrice]:
        results = []
        name = medication["name"]
        strength = medication["strength"]

        page = await context.new_page()
        await configure_stealth_page(page)

        search_url = self._build_search_url(name, strength)
        self.log.info("Scraping PharmEasy", url=search_url)

        try:
            await page.goto(search_url, wait_until="domcontentloaded", timeout=30000)
            await human_delay(2.0, 4.0)
            await simulate_human_scroll(page, 3)

            # Wait for product cards
            try:
                await page.wait_for_selector('[class*="ProductCard"]', timeout=10000)
            except Exception:
                pass

            product_cards = await page.query_selector_all('[class*="ProductCard_productCard"]')
            if not product_cards:
                product_cards = await page.query_selector_all('[class*="ProductCard"]')

            for card in product_cards[:3]:
                try:
                    product_name = await self._safe_get_text(card if hasattr(card, 'query_selector') else page,
                                                             '[class*="ProductTitle"]')
                    if not product_name:
                        product_name = await card.evaluate('el => el.querySelector("[class*=\\"title\\"]")?.textContent')

                    # Price selectors
                    price_el = await card.query_selector('[class*="Price__price"]')
                    if not price_el:
                        price_el = await card.query_selector('[class*="discountedPrice"]')
                    price_text = (await price_el.text_content()).strip() if price_el else None

                    mrp_el = await card.query_selector('[class*="Price__mrp"]')
                    if not mrp_el:
                        mrp_el = await card.query_selector('[class*="originalPrice"]')
                    mrp_text = (await mrp_el.text_content()).strip() if mrp_el else None

                    price = self._parse_price(price_text)
                    mrp = self._parse_price(mrp_text) or price

                    # Product URL
                    link_el = await card.query_selector("a")
                    href = await link_el.get_attribute("href") if link_el else None
                    product_url = f"{self.base_url}{href}" if href and href.startswith("/") else href

                    if price is not None:
                        results.append(ScrapedPrice(
                            platform_slug=self.platform_slug,
                            medication_name=name,
                            strength=strength,
                            price=price,
                            mrp=mrp,
                            discount_pct=self._calc_discount(price, mrp),
                            is_available=True,
                            product_url=product_url,
                            product_name_raw=product_name,
                        ))
                        break

                except Exception as e:
                    self.log.debug("Card parse error", error=str(e))
                    continue

            if not results:
                results.append(ScrapedPrice(
                    platform_slug=self.platform_slug,
                    medication_name=name,
                    strength=strength,
                    price=None,
                    mrp=None,
                    discount_pct=None,
                    is_available=False,
                    product_url=search_url,
                    product_name_raw=None,
                ))

        except Exception as e:
            self.log.warning("PharmEasy scrape failed", name=name, strength=strength, error=str(e))
            results.append(ScrapedPrice(
                platform_slug=self.platform_slug,
                medication_name=name,
                strength=strength,
                price=None,
                mrp=None,
                discount_pct=None,
                is_available=False,
                product_url=search_url,
                product_name_raw=None,
            ))
        finally:
            await page.close()

        return results

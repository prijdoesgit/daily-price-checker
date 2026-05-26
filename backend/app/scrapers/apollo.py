import urllib.parse
from app.scrapers.base import BaseScraper, ScrapedPrice
from app.core.anti_bot import configure_stealth_page, human_delay, simulate_human_scroll


class ApolloScraper(BaseScraper):
    platform_slug = "apollo"
    platform_name = "Apollo Pharmacy"
    base_url = "https://www.apollopharmacy.in"

    def _format_search_url(self, query: str) -> str:
        return f"{self.base_url}/search/{urllib.parse.quote(query)}"

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
            await simulate_human_scroll(page, 2)

            try:
                await page.wait_for_selector('[class*="ProductCard"]', timeout=8000)
            except Exception:
                pass

            cards = await page.query_selector_all('[class*="productCard"], [class*="ProductCard"], .product-card')

            for card in cards[:3]:
                try:
                    price_el = await card.query_selector('[class*="price"], [class*="Price"]')
                    price_text = (await price_el.text_content()) if price_el else None

                    mrp_el = await card.query_selector('[class*="mrp"], [class*="MRP"], [class*="original"]')
                    mrp_text = (await mrp_el.text_content()) if mrp_el else None

                    price = self._parse_price(price_text)
                    mrp = self._parse_price(mrp_text) or price

                    link_el = await card.query_selector("a")
                    href = await link_el.get_attribute("href") if link_el else None
                    product_url = f"{self.base_url}{href}" if href and href.startswith("/") else href

                    name_el = await card.query_selector('[class*="title"], [class*="name"], h3, h4')
                    product_name = (await name_el.text_content()).strip() if name_el else None

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
                except Exception:
                    continue

        except Exception as e:
            self.log.warning("Apollo scrape failed", name=name, error=str(e))
        finally:
            await page.close()

        if not results:
            results.append(ScrapedPrice(
                platform_slug=self.platform_slug,
                medication_name=name,
                strength=strength,
                price=None, mrp=None, discount_pct=None,
                is_available=False, product_url=search_url, product_name_raw=None,
            ))
        return results

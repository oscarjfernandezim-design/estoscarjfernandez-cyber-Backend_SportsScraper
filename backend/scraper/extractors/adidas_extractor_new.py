from __future__ import annotations

from typing import Any
from urllib.parse import quote_plus

from scrapling.fetchers import Fetcher

from extractors.base_scraper_new import BaseProductScraper


class AdidasScraper(BaseProductScraper):
    store_name = "Adidas Tienda Oficial"
    brand = "Adidas"
    base_url = "https://www.adidas.co"

    def _build_search_url(self, query: str, page: int) -> str:
        encoded = quote_plus(query.strip())
        if page <= 1:
            return f"{self.base_url}/search?q={encoded}"
        return f"{self.base_url}/search?q={encoded}&page={page}"

    def scrape_category(self, category: str, pages: int = 2) -> list[dict[str, Any]]:
        results = []
        for page_number in range(1, pages + 1):
            url = self._build_search_url(category, page_number)
            candidate_pages = self._get_candidate_pages(url)
            for page in candidate_pages:
                products = self._extract_products_from_page(page, url, limit=50)
                results.extend(products)
        return results

    def _extract_products_from_page(
        self, page: Any, url: str, limit: int = 50
    ) -> list[dict[str, Any]]:
        products: list[dict[str, Any]] = []
        seen_urls: set[str] = set()

        cards = self._css(page, 'div[data-testid="product-card-main"]')
        for card in cards[:limit]:
            try:
                link_elem = self._css(card, 'a::attr(href)').get()
                image_src = self._css(card, 'img::attr(src)').get()
                price_text = self._css(card, 'div[data-testid="main-price"] span::text').get()
                title = self._css(card, 'h4::text').get()

                if not title or not price_text:
                    continue

                absolute_url = self._resolve_url(self.base_url, link_elem)
                if absolute_url in seen_urls:
                    continue
                seen_urls.add(absolute_url)

                clean_price = self._parse_price(price_text)
                if clean_price is None:
                    continue

                image_url = self._resolve_url(self.base_url, image_src) if image_src else None

                products.append(
                    {
                        "product_name": title.strip(),
                        "price": clean_price,
                        "product_url": absolute_url,
                        "image_url": image_url,
                    }
                )
            except Exception:
                continue

        return products

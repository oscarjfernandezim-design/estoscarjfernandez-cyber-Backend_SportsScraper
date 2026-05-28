from __future__ import annotations

from typing import Any
from urllib.parse import quote_plus

from extractors.base_scraper import BaseProductScraper


class PumaScraper(BaseProductScraper):
    store_name = "Puma Tienda Oficial"
    brand = "Puma"
    base_url = "https://us.puma.com"

    def _build_search_url(self, query: str, page: int) -> str:
        encoded = quote_plus(query.strip())
        if page <= 1:
            return f"{self.base_url}/us/es/search?q={encoded}"
        return f"{self.base_url}/us/es/search?q={encoded}&page={page}"

    def scrape_category(self, category: str, pages: int = 2) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        for page_number in range(1, pages + 1):
            url = self._build_search_url(category, page_number)
            candidate_pages = self._get_candidate_pages(url)
            for page in candidate_pages:
                results.extend(self._extract_products_from_page(page, url, limit=50))
        return results

    def _extract_products_from_page(self, page: Any, url: str, limit: int = 50) -> list[dict[str, Any]]:
        products: list[dict[str, Any]] = []

        def first(nodes):
            return nodes[0] if nodes and len(nodes) > 0 else None

        cards = self._css(page, 'div[data-primary-product="true"], .product-tile, .product-grid__item')
        seen = set()
        for card in cards[:limit]:
            try:
                a_node = first(self._css(card, 'a[data-test-id="product-list-item-link"], a'))
                h2_node = first(self._css(card, "h2"))
                h3_node = first(self._css(card, "h3"))
                price_node = first(self._css(card, 'span[data-test-id="sale-price"], .product-price'))
                img_node = first(self._css(card, "img"))

                title = None
                if h2_node and getattr(h2_node, 'text', None):
                    title = h2_node.text.strip()
                if h3_node and getattr(h3_node, 'text', None):
                    title = f"{title} {h3_node.text.strip()}".strip() if title else h3_node.text.strip()

                price_text = price_node.text.strip() if price_node and getattr(price_node, 'text', None) else None
                href = a_node.attrib.get("href") if a_node is not None else None
                image_src = img_node.attrib.get("src") if img_node is not None else None

                if not title or not price_text:
                    continue

                product_url = self._resolve_url(self.base_url, href)
                if product_url in seen:
                    continue
                seen.add(product_url)

                price = self._parse_price(price_text)
                if price is None:
                    continue

                image_url = self._resolve_url(self.base_url, image_src) if image_src else None

                products.append({
                    "product_name": title,
                    "price": price,
                    "product_url": product_url,
                    "image_url": image_url,
                })
            except Exception:
                continue

        return products

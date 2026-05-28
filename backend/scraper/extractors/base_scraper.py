from __future__ import annotations

import re
from abc import ABC, abstractmethod
from typing import Any
from urllib.parse import urljoin

from scrapling.fetchers import Fetcher


class BaseProductScraper(ABC):
    store_name: str
    brand: str
    base_url: str

    @staticmethod
    def _css(node: Any, selector: str) -> Any:
        """CSS selector helper."""
        return node.css(selector)

    @staticmethod
    def _get_candidate_pages(url: str) -> list[Any]:
        """Fetch page using Fetcher."""
        try:
            page = Fetcher.get(url)
            if getattr(page, "status", 0) == 200:
                return [page]
        except Exception as e:
            print(f"    Error fetching {url}: {str(e)[:50]}")
        return []

    @staticmethod
    def _extract_first_number(value: str | None) -> str | None:
        """Extract first number from string."""
        if not value:
            return None
        match = re.search(r"\d[\d\.,]*", value)
        return match.group(0) if match else None

    @staticmethod
    def _parse_price(price_text: str | None) -> float | None:
        """Parse price from text."""
        if not price_text:
            return None
        cleaned = re.sub(r"[^0-9,\.]", "", price_text)
        if not cleaned:
            return None
        last_dot = cleaned.rfind(".")
        last_comma = cleaned.rfind(",")
        if last_dot == -1 and last_comma == -1:
            return float(cleaned)
        if last_dot > -1 and last_comma > -1:
            sep = "." if last_dot > last_comma else ","
            cleaned = cleaned.replace("," if sep == "." else ".", "")
        else:
            sep = "." if last_dot > -1 else ","
        parts = cleaned.split(sep)
        if len(parts) == 1:
            return float(parts[0])
        if all(len(part) == 3 for part in parts[1:]):
            return float("".join(parts))
        integer_part = "".join(parts[:-1]) or "0"
        decimal_part = parts[-1]
        normalized = (
            f"{integer_part}.{decimal_part}" if decimal_part else integer_part
        )
        return float(normalized)

    @staticmethod
    def _resolve_url(base_url: str, href: str | None) -> str:
        """Resolve absolute URL from relative href."""
        if not href:
            return base_url
        return urljoin(base_url, href)

    @abstractmethod
    def scrape_category(self, category: str, pages: int = 2) -> list[dict[str, Any]]:
        """Scrape products from a category across multiple pages."""
        pass

    @abstractmethod
    def _build_search_url(self, query: str, page: int) -> str:
        """Build search URL for a query and page number."""
        pass

    @abstractmethod
    def _extract_products_from_page(
        self, page: Any, url: str, limit: int = 100
    ) -> list[dict[str, Any]]:
        """Extract products from a single page."""
        pass

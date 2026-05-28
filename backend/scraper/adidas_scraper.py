from __future__ import annotations

import argparse
import json
import os
import re
import sys
from decimal import Decimal, InvalidOperation
from typing import Any
from urllib.parse import quote_plus, urljoin

from dotenv import load_dotenv
from scrapling.fetchers import PlayWrightFetcher as Fetcher

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from database.db import get_connection

TARGET_URL = "https://www.adidas.co/"
STORE_NAME = "Adidas"
DEFAULT_BRAND = "Adidas"


def _css(node: Any, selector: str) -> Any:
    return node.css(selector)


def _get_candidate_pages(url: str) -> list[Any]:
    pages: list[Any] = []

    try:
        static_page = Fetcher.fetch(url, headless=True, network_idle=True)
        if getattr(static_page, "status", 0) == 200:
            pages.append(static_page)
    except Exception as exc:
        raise RuntimeError(f"Fetcher failed: {exc}")

    if not pages:
        raise RuntimeError("Could not fetch page with Fetcher")

    return pages


def _extract_first_number(value: str | None) -> str | None:
    if not value:
        return None
    match = re.search(r"\d[\d\.,]*", value)
    return match.group(0) if match else None


def _build_search_urls(search: str) -> list[str]:
    encoded = quote_plus(search.strip())
    return [
        f"https://www.adidas.co/search?q={encoded}",
        f"https://www.adidas.co/search?q={encoded}&sort=price-low-to-high",
        f"https://www.adidas.co/search?query={encoded}",
    ]


def _is_product_type(value: Any) -> bool:
    if isinstance(value, str):
        return value.lower() == "product"
    if isinstance(value, list):
        return any(isinstance(item, str) and item.lower() == "product" for item in value)
    return False


def _extract_products_from_jsonld(raw_json_blocks: list[str]) -> list[dict[str, Any]]:
    products: list[dict[str, Any]] = []
    seen_keys: set[str] = set()

    def add_product(item: dict[str, Any]) -> None:
        offers = item.get("offers")
        if isinstance(offers, list):
            offers = offers[0] if offers else {}
        if not isinstance(offers, dict):
            offers = {}

        name = item.get("name")
        url = item.get("url")
        key = f"{name}|{url}"
        if key in seen_keys:
            return
        seen_keys.add(key)

        products.append(
            {
                "name": name,
                "sku": item.get("sku"),
                "brand": item.get("brand", {}).get("name") if isinstance(item.get("brand"), dict) else item.get("brand"),
                "price": offers.get("price"),
                "currency": offers.get("priceCurrency"),
                "availability": offers.get("availability"),
                "url": url,
                "image": item.get("image"),
                "source": "json-ld",
            }
        )

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            if _is_product_type(node.get("@type")):
                add_product(node)
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)

    for raw in raw_json_blocks:
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            continue
        walk(payload)

    return products


def _looks_like_product_url(href: str) -> bool:
    if not href:
        return False
    if ".html" not in href:
        return False
    if re.search(r"/[A-Z0-9]{6}\.html", href, re.IGNORECASE):
        return True
    return "products" in href or "product" in href


def _extract_product_links_from_html(page: Any, base_url: str, limit: int) -> list[dict[str, Any]]:
    fallback_products: list[dict[str, Any]] = []
    seen_urls: set[str] = set()

    for link in _css(page, "a[href*='.html']"):
        href = _css(link, "::attr(href)").get()
        if not href or not _looks_like_product_url(href):
            continue

        absolute_url = urljoin(base_url, href)
        if absolute_url in seen_urls:
            continue
        seen_urls.add(absolute_url)

        title = (_css(link, "::attr(title)").get() or _css(link, "::text").get() or "").strip()

        fallback_products.append(
            {
                "name": title or None,
                "url": absolute_url,
                "source": "html-link",
            }
        )

        if len(fallback_products) >= limit:
            break

    return fallback_products


def _extract_products_from_cards(page: Any, base_url: str, limit: int) -> list[dict[str, Any]]:
    products: list[dict[str, Any]] = []
    seen_urls: set[str] = set()

    cards = _css(page, "article[data-testid*='product-card'], div[data-testid*='product-card'], div[class*='product-card']")
    for card in cards:
        href = _css(card, "a[data-testid*='product-card-link']::attr(href)").get()
        if not href:
            href = _css(card, "a::attr(href)").get()
        if not href or not _looks_like_product_url(href):
            continue

        absolute_url = urljoin(base_url, href)
        if absolute_url in seen_urls:
            continue
        seen_urls.add(absolute_url)

        name = (
            _css(card, "[data-testid*='product-card-title']::text").get()
            or _css(card, "[data-testid*='product-title']::text").get()
            or _css(card, "span[class*='title']::text").get()
            or _css(card, "p::text").get()
            or ""
        ).strip() or None

        image = _css(card, "img::attr(src)").get()

        price_candidates = _css(card, "[data-testid*='price']::text").getall()
        if not price_candidates:
            price_candidates = _css(card, "span[class*='price']::text").getall()
        if not price_candidates:
            price_candidates = _css(card, "div[class*='gl-price'] span::text").getall()

        price_text = " ".join(value.strip() for value in price_candidates if value and value.strip())

        products.append(
            {
                "name": name,
                "url": absolute_url,
                "image": image,
                "price": _extract_first_number(price_text),
                "source": "html-card",
            }
        )

        if len(products) >= limit:
            break

    return products


def _normalize_numeric_string(raw_value: str) -> str | None:
    cleaned = re.sub(r"[^\d\.,]", "", raw_value)
    if not cleaned:
        return None

    if "." in cleaned and "," in cleaned:
        last_dot = cleaned.rfind(".")
        last_comma = cleaned.rfind(",")
        decimal_sep = "." if last_dot > last_comma else ","
        thousands_sep = "," if decimal_sep == "." else "."
        cleaned = cleaned.replace(thousands_sep, "")
        cleaned = cleaned.replace(decimal_sep, ".")
        return cleaned

    if "," in cleaned:
        last_comma = cleaned.rfind(",")
        decimals = len(cleaned) - last_comma - 1
        if 0 < decimals <= 2:
            cleaned = cleaned.replace(".", "")
            cleaned = cleaned.replace(",", ".")
        else:
            cleaned = cleaned.replace(",", "")
        return cleaned

    if "." in cleaned:
        last_dot = cleaned.rfind(".")
        decimals = len(cleaned) - last_dot - 1
        if 0 < decimals <= 2:
            cleaned = cleaned.replace(",", "")
        else:
            cleaned = cleaned.replace(".", "")
        return cleaned

    return cleaned


def _parse_price(value: Any) -> Decimal | None:
    if value is None:
        return None

    if isinstance(value, (int, float, Decimal)):
        return Decimal(str(value)).quantize(Decimal("0.01"))

    if isinstance(value, str):
        normalized = _normalize_numeric_string(value)
        if not normalized:
            return None
        try:
            return Decimal(normalized).quantize(Decimal("0.01"))
        except InvalidOperation:
            return None

    return None


def _derive_name_from_url(url: str | None) -> str | None:
    if not url:
        return None
    slug = url.rstrip("/").split("/")[-1]
    slug = slug.replace(".html", "")
    slug = re.sub(r"[-_]+", " ", slug)
    slug = re.sub(r"[^\w\s]", "", slug)
    name = slug.strip()
    return name.title() if name else None


def _store_products(products: list[dict[str, Any]], category: str | None) -> int:
    stored_prices = 0
    category_value = (category or "General").strip()[:50] or "General"

    with get_connection() as conn:
        with conn.cursor() as cur:
            for product in products:
                name = (product.get("name") or "").strip()
                if not name:
                    name = _derive_name_from_url(product.get("url"))
                if not name:
                    continue

                brand = product.get("brand") or DEFAULT_BRAND
                if isinstance(brand, list):
                    brand = brand[0] if brand else DEFAULT_BRAND
                brand = str(brand).strip() or DEFAULT_BRAND

                image = product.get("image")
                if isinstance(image, list):
                    image = image[0] if image else None
                product_url = product.get("url")

                cur.execute(
                    """
                    INSERT INTO products (product_name, brand, category, image_url)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (product_name)
                    DO UPDATE SET
                        brand = EXCLUDED.brand,
                        category = EXCLUDED.category,
                        image_url = COALESCE(EXCLUDED.image_url, products.image_url)
                    RETURNING id;
                    """,
                    (name[:255], brand[:100], category_value, image),
                )
                product_id = cur.fetchone()["id"]

                price_value = _parse_price(product.get("price"))
                if price_value is None:
                    price_value = _parse_price(product.get("original_price"))

                if price_value is None or not product_url:
                    continue

                cur.execute(
                    """
                    INSERT INTO product_prices (product_id, store_name, price, product_url)
                    VALUES (%s, %s, %s, %s);
                    """,
                    (product_id, STORE_NAME, price_value, product_url),
                )
                stored_prices += 1

        conn.commit()

    return stored_prices


def scrape_adidas(search: str | None = None, max_items: int = 20) -> tuple[list[dict[str, Any]], str]:
    """Scrape Adidas products; optionally target search result pages."""
    urls = _build_search_urls(search) if search else [TARGET_URL]

    for url in urls:
        try:
            pages = _get_candidate_pages(url)
        except RuntimeError:
            continue
        for page in pages:
            raw_json_blocks = _css(page, "script[type='application/ld+json']::text").getall()
            products = _extract_products_from_jsonld(raw_json_blocks)

            if not products:
                products = _extract_products_from_cards(page, url, limit=max_items)

            if not products:
                products = _extract_product_links_from_html(page, url, limit=max_items)

            if products:
                return products[:max_items], url

    raise RuntimeError("Could not extract products from Adidas with the current strategy")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Scrape products from adidas.co and store in PostgreSQL")
    parser.add_argument(
        "--search",
        type=str,
        default=None,
        help="Product keyword to search, for example: ultraboost",
    )
    parser.add_argument(
        "--max-items",
        type=int,
        default=5,
        help="Maximum number of products to store",
    )
    return parser.parse_args()


def main() -> None:
    load_dotenv()
    args = _parse_args()
    data, source_url = scrape_adidas(search=args.search, max_items=args.max_items)
    stored = _store_products(data, category=args.search)
    print(f"Collected {len(data)} product records from {source_url}")
    print(f"Stored {stored} price records in the database")


if __name__ == "__main__":
    main()

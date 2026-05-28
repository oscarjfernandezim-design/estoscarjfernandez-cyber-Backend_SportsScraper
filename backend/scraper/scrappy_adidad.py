from __future__ import annotations

import argparse
import json
import os
import re
import sys
from decimal import Decimal, InvalidOperation
from typing import Any
from urllib.parse import quote_plus, urljoin, urlparse

from scrapling.fetchers import Fetcher

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from backend.database.db import get_connection

CATEGORIES = ["running", "lifestyle", "training", "basketball", "soccer", "discounts"]

BRAND_CONFIG = {
    "adidas": {
        "display": "Adidas",
        "base_url": "https://www.adidas.com/us",
        "search_urls": [
            "https://www.adidas.com/us/search?q={query}",
            "https://www.adidas.com/us/{query}",
        ],
        "discount_urls": [
            "https://www.adidas.com/us/sale",
        ],
        "product_url_patterns": [r"/us/.+\.html$"],
    },
    "nike": {
        "display": "Nike",
        "base_url": "https://www.nike.com",
        "search_urls": [
            "https://www.nike.com/w?q={query}",
            "https://www.nike.com/es/w?q={query}",
        ],
        "discount_urls": [
            "https://www.nike.com/w/sale-3yaep",
            "https://www.nike.com/es/w/rebajas-3yaep",
        ],
        "product_url_patterns": [r"/t/.+", r"/es/t/.+"],
    },
    "puma": {
        "display": "Puma",
        "base_url": "https://us.puma.com",
        "search_urls": [
            "https://us.puma.com/us/en/search?q={query}",
            "https://us.puma.com/us/en/{query}",
        ],
        "discount_urls": [
            "https://us.puma.com/us/en/sale/all-sale",
        ],
        "product_url_patterns": [r"/us/en/pd/", r"/us/en/.+\.html$"],
    },
}


def _css(node: Any, selector: str) -> Any:
    return node.css(selector)


def _safe_get(mapping: Any, *keys: str) -> Any:
    current = mapping
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def _extract_price_number(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)

    text = str(value)
    # Prefer explicit money tokens and ignore zero/noise values.
    money_tokens = re.findall(r"(?:\$|usd\s*)(\d[\d,]*(?:\.\d{1,2})?)", text, flags=re.IGNORECASE)
    for token in money_tokens:
        try:
            parsed = float(token.replace(",", ""))
            if parsed > 0:
                return parsed
        except ValueError:
            continue

    # Accept explicit price labels without currency symbols.
    labelled_match = re.search(r"(?:sale\s+price|price|now|from)\s*[:]?\s*(\d+(?:[\.,]\d{1,2})?)", text, flags=re.IGNORECASE)
    if not labelled_match:
        return None
    cleaned = labelled_match.group(1).replace(",", "")

    try:
        parsed = float(cleaned)
        return parsed if parsed > 0 else None
    except ValueError:
        return None


def _build_search_urls(search: str) -> list[str]:
    encoded = quote_plus(search.strip())
    return [encoded]


def _get_candidate_pages(url: str) -> list[Any]:
    pages: list[Any] = []

    # StealthyFetcher depends on patchright; when unavailable, continue with static fetch.
    try:
        from scrapling.fetchers import StealthyFetcher

        stealth_page = StealthyFetcher.fetch(url, headless=True, network_idle=True, adaptive=True)
        if getattr(stealth_page, "status", 200) == 200:
            pages.append(stealth_page)
    except Exception:
        pass

    try:
        static_page = Fetcher.get(url)
        if getattr(static_page, "status", 0) == 200:
            pages.append(static_page)
    except Exception:
        pass

    return pages


def _extract_price_from_pdp(product_url: str) -> float | None:
    """Fetch a product detail page and try to parse a real price.

    Puma search cards often omit plain text prices in static HTML.
    """
    try:
        page = Fetcher.get(product_url)
        if getattr(page, "status", 0) != 200:
            return None
    except Exception:
        return None

    meta_price = _css(page, 'meta[property="product:price:amount"]::attr(content)').get()
    parsed_meta = _extract_price_number(meta_price)
    if parsed_meta is not None:
        return parsed_meta

    ld_blocks = _css(page, "script[type='application/ld+json']::text").getall()
    for raw in ld_blocks:
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            continue

        stack: list[Any] = [payload]
        while stack:
            node = stack.pop()
            if isinstance(node, dict):
                node_type = node.get("@type")
                is_product = (isinstance(node_type, str) and node_type.lower() == "product") or (
                    isinstance(node_type, list)
                    and any(isinstance(item, str) and item.lower() == "product" for item in node_type)
                )
                if is_product:
                    offers = node.get("offers")
                    if isinstance(offers, dict):
                        parsed = _extract_price_number(offers.get("price"))
                        if parsed is not None:
                            return parsed
                    elif isinstance(offers, list):
                        for offer in offers:
                            if not isinstance(offer, dict):
                                continue
                            parsed = _extract_price_number(offer.get("price"))
                            if parsed is not None:
                                return parsed
                stack.extend(node.values())
            elif isinstance(node, list):
                stack.extend(node)

    return None


def _first_non_empty(*values: Any) -> Any:
    for value in values:
        if value is None:
            continue
        if isinstance(value, str) and not value.strip():
            continue
        return value
    return None


def _to_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _looks_like_product_url(url: str, brand_key: str) -> bool:
    patterns = BRAND_CONFIG[brand_key]["product_url_patterns"]
    return any(re.search(pattern, url) for pattern in patterns)


def _normalize_product(raw: dict[str, Any], base_url: str, brand_name: str, category: str) -> dict[str, Any] | None:
    name = raw.get("name") or raw.get("title")
    url = _first_non_empty(
        raw.get("url"),
        raw.get("link"),
        raw.get("pdpUrl"),
        raw.get("productUrl"),
        raw.get("href"),
    )
    if url:
        if isinstance(url, dict):
            url = _first_non_empty(url.get("url"), url.get("path"))
        if isinstance(url, str):
            if url.startswith("https:/") and not url.startswith("https://"):
                url = url.replace("https:/", "https://", 1)
            if url.startswith("http:/") and not url.startswith("http://"):
                url = url.replace("http:/", "http://", 1)
        url = urljoin(base_url, str(url))

    sku = _first_non_empty(raw.get("sku"), raw.get("id"), raw.get("model_number"), raw.get("styleColor"))
    image = _first_non_empty(raw.get("image"), raw.get("image_url"), raw.get("imageUrl"), raw.get("thumbnail"))
    if isinstance(image, list):
        image = image[0] if image else None

    brand = raw.get("brand")
    if isinstance(brand, dict):
        brand = brand.get("name")

    offers = raw.get("offers")
    offer_price: Any = None
    if isinstance(offers, dict):
        offer_price = _first_non_empty(offers.get("price"), offers.get("lowPrice"), offers.get("highPrice"))
    elif isinstance(offers, list) and offers:
        first_offer = offers[0]
        if isinstance(first_offer, dict):
            offer_price = _first_non_empty(first_offer.get("price"), first_offer.get("lowPrice"), first_offer.get("highPrice"))

    price = (
        _extract_price_number(offer_price)
        or _extract_price_number(raw.get("price"))
        or _extract_price_number(raw.get("salePrice"))
        or _extract_price_number(raw.get("currentPrice"))
        or _extract_price_number(raw.get("value"))
        or _extract_price_number(_safe_get(raw, "pricing_information", "currentPrice"))
        or _extract_price_number(_safe_get(raw, "price", "current"))
        or _extract_price_number(_safe_get(raw, "prices", "current"))
        or _extract_price_number(_safe_get(raw, "priceRange", "minVariantPrice", "amount"))
    )

    if not name and not url:
        return None

    if not name and isinstance(url, str):
        path_fragment = url.split("?")[0].rstrip("/").split("/")[-2:]
        if path_fragment:
            slug = path_fragment[-2] if len(path_fragment) == 2 else path_fragment[-1]
            name = slug.replace("-", " ").title() if slug else None

    return {
        "name": name,
        "sku": sku,
        "brand": brand or brand_name,
        "category": category,
        "price": price,
        "url": url,
        "image": image,
    }


def _extract_products_from_jsonld(
    page: Any,
    base_url: str,
    brand_key: str,
    category: str,
    limit: int,
) -> list[dict[str, Any]]:
    products: list[dict[str, Any]] = []
    seen: set[str] = set()
    brand_name = BRAND_CONFIG[brand_key]["display"]

    raw_json_blocks = _css(page, "script[type='application/ld+json']::text").getall()
    for raw_json in raw_json_blocks:
        try:
            payload = json.loads(raw_json)
        except json.JSONDecodeError:
            continue

        stack: list[Any] = [payload]
        while stack:
            node = stack.pop()
            if isinstance(node, dict):
                node_type = node.get("@type")
                if (isinstance(node_type, str) and node_type.lower() == "product") or (
                    isinstance(node_type, list)
                    and any(isinstance(item, str) and item.lower() == "product" for item in node_type)
                ):
                    normalized = _normalize_product(node, base_url, brand_name=brand_name, category=category)
                    if normalized:
                        key = f"{normalized.get('name')}|{normalized.get('url')}"
                        if key not in seen:
                            seen.add(key)
                            normalized["source"] = "json-ld"
                            products.append(normalized)
                stack.extend(node.values())
            elif isinstance(node, list):
                stack.extend(node)

            if len(products) >= limit:
                return products

    return products


def _extract_products_from_next_data(page: Any, base_url: str, limit: int) -> list[dict[str, Any]]:
    raw_next_data = _css(page, "script#__NEXT_DATA__::text").get()
    if not raw_next_data:
        return []

    try:
        payload = json.loads(raw_next_data)
    except json.JSONDecodeError:
        return []

    products: list[dict[str, Any]] = []
    seen: set[str] = set()

    stack: list[Any] = [payload]
    while stack:
        node = stack.pop()
        if isinstance(node, dict):
            has_product_shape = any(key in node for key in ("pdpUrl", "productUrl", "sku", "model_number"))
            if has_product_shape:
                normalized = _normalize_product(node, base_url)
                if normalized:
                    key = f"{normalized.get('name')}|{normalized.get('url')}"
                    if key not in seen:
                        seen.add(key)
                        normalized["source"] = "next-data"
                        products.append(normalized)
            stack.extend(node.values())
        elif isinstance(node, list):
            stack.extend(node)

        if len(products) >= limit:
            return products

    return products


def _extract_products_from_embedded_json(
    page: Any,
    base_url: str,
    brand_key: str,
    category: str,
    limit: int,
) -> list[dict[str, Any]]:
    products: list[dict[str, Any]] = []
    seen: set[str] = set()
    brand_name = BRAND_CONFIG[brand_key]["display"]

    json_scripts = _css(page, "script[type='application/json']::text").getall()
    for raw in json_scripts:
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            continue

        stack: list[Any] = [payload]
        while stack:
            node = stack.pop()
            if isinstance(node, dict):
                has_name = any(key in node for key in ("name", "title"))
                has_url = any(key in node for key in ("url", "link", "pdpUrl", "productUrl", "href"))
                has_price = any(key in node for key in ("price", "salePrice", "currentPrice", "offers", "prices"))
                if has_name and has_url and has_price:
                    normalized = _normalize_product(node, base_url, brand_name=brand_name, category=category)
                    if normalized and normalized.get("url"):
                        key = f"{normalized.get('name')}|{normalized.get('url')}"
                        if key not in seen:
                            seen.add(key)
                            normalized["source"] = "embedded-json"
                            products.append(normalized)
                stack.extend(node.values())
            elif isinstance(node, list):
                stack.extend(node)

            if len(products) >= limit:
                return products

    return products


def _extract_products_from_next_data(
    page: Any,
    base_url: str,
    brand_key: str,
    category: str,
    limit: int,
) -> list[dict[str, Any]]:
    raw_next_data = _css(page, "script#__NEXT_DATA__::text").get()
    if not raw_next_data:
        return []

    try:
        payload = json.loads(raw_next_data)
    except json.JSONDecodeError:
        return []

    products: list[dict[str, Any]] = []
    seen: set[str] = set()
    brand_name = BRAND_CONFIG[brand_key]["display"]

    stack: list[Any] = [payload]
    while stack:
        node = stack.pop()
        if isinstance(node, dict):
            has_url = any(key in node for key in ("url", "link", "pdpUrl", "productUrl", "href"))
            has_name = any(key in node for key in ("name", "title"))
            has_price = any(key in node for key in ("price", "salePrice", "currentPrice", "offers", "prices", "pricing_information"))
            has_product_shape = has_url and has_name and has_price
            if has_product_shape:
                normalized = _normalize_product(node, base_url, brand_name=brand_name, category=category)
                if normalized and normalized.get("price") is not None:
                    key = f"{normalized.get('name')}|{normalized.get('url')}"
                    if key not in seen:
                        seen.add(key)
                        normalized["source"] = "next-data"
                        products.append(normalized)
            stack.extend(node.values())
        elif isinstance(node, list):
            stack.extend(node)

        if len(products) >= limit:
            return products

    return products


def _extract_products_from_html(
    page: Any,
    base_url: str,
    brand_key: str,
    category: str,
    limit: int,
) -> list[dict[str, Any]]:
    products: list[dict[str, Any]] = []
    seen_urls: set[str] = set()
    brand_name = BRAND_CONFIG[brand_key]["display"]

    for card in _css(page, "article, li, div"):
        href = _css(card, "a[href]::attr(href)").get()
        if not href:
            continue

        url = urljoin(base_url, href)
        if not _looks_like_product_url(url, brand_key):
            continue

        if url in seen_urls:
            continue
        seen_urls.add(url)

        name = (
            _css(card, "h3::text").get()
            or _css(card, "h2::text").get()
            or _css(card, "a::attr(title)").get()
            or _css(card, "a::attr(aria-label)").get()
            or _css(card, "img::attr(alt)").get()
            or ""
        ).strip() or None
        if not name:
            path_match = re.search(r"/(?:us|es)/(?:en/)?([^/]+)/[A-Za-z0-9\-]+(?:\.html)?$", url)
            if path_match:
                name = path_match.group(1).replace("-", " ").title()

        image = _first_non_empty(_css(card, "img::attr(src)").get(), _css(card, "img::attr(data-src)").get())
        price_candidates = [
            _css(card, 'span[data-test-id="sale-price"]::text').get(),
            _css(card, 'span[data-test-id="price"]::text').get(),
            _css(card, '[data-test-id="sale-price"]::text').get(),
            _css(card, '[data-test-id="price"]::text').get(),
            _css(card, '.product-price::text').get(),
            _css(card, '[class*="price"]::text').get(),
        ]
        text_blob = " ".join(t.strip() for t in _css(card, "::text").getall() if t and t.strip())

        parsed_price = None
        for candidate in price_candidates:
            parsed_price = _extract_price_number(candidate)
            if parsed_price is not None:
                break
        if parsed_price is None:
            parsed_price = _extract_price_number(text_blob)
        if parsed_price is None or parsed_price <= 0:
            if brand_key == "puma":
                parsed_price = _extract_price_from_pdp(url)
        if parsed_price is None or parsed_price <= 0:
            continue

        products.append(
            {
                "name": name,
                "sku": None,
                "brand": brand_name,
                "category": category,
                "price": parsed_price,
                "url": url,
                "image": image,
                "source": "html",
            }
        )

        if len(products) >= limit:
            break

    return products


def _build_brand_category_urls(brand_key: str, category: str) -> list[str]:
    config = BRAND_CONFIG[brand_key]
    if category == "discounts":
        return list(config["discount_urls"])

    encoded = _build_search_urls(category)[0]
    return [template.format(query=encoded) for template in config["search_urls"]]


def scrape_brand_category(brand_key: str, category: str, max_items: int = 20, pages: int = 2) -> tuple[list[dict[str, Any]], str]:
    """Scrape a brand/category combination across multiple candidate URLs and pages.

    pages: number of paginated search pages to attempt per search/discount URL.
    """
    urls = _build_brand_category_urls(brand_key, category)
    last_url = urls[0] if urls else BRAND_CONFIG[brand_key]["base_url"]
    collected: list[dict[str, Any]] = []
    seen_keys: set[str] = set()

    def _collect(products: list[dict[str, Any]]):
        for product in products:
            if product.get("price") is None:
                continue
            key = f"{product.get('name')}|{product.get('url')}"
            if key in seen_keys:
                continue
            seen_keys.add(key)
            collected.append(product)
            if len(collected) >= max_items:
                return True
        return False

    for base in urls:
        # iterate requested pagination for each search/discount URL
        for page_number in range(1, pages + 1):
            if page_number == 1:
                url = base
            else:
                separator = "&" if "?" in base else "?"
                url = f"{base}{separator}page={page_number}"

            last_url = url
            candidate_pages = _get_candidate_pages(url)
            for page in candidate_pages:
                products = _extract_products_from_jsonld(
                    page,
                    url,
                    brand_key=brand_key,
                    category=category,
                    limit=max_items,
                )
                if not products:
                    products = _extract_products_from_next_data(
                        page,
                        url,
                        brand_key=brand_key,
                        category=category,
                        limit=max_items,
                    )
                if not products:
                    products = _extract_products_from_embedded_json(
                        page,
                        url,
                        brand_key=brand_key,
                        category=category,
                        limit=max_items,
                    )
                if not products:
                    products = _extract_products_from_html(
                        page,
                        url,
                        brand_key=brand_key,
                        category=category,
                        limit=max_items,
                    )
                if products and _collect(products):
                    return collected[:max_items], url

    return collected[:max_items], last_url


def _to_decimal(value: float | None) -> Decimal | None:
    if value is None:
        return None
    try:
        return Decimal(str(value)).quantize(Decimal("0.01"))
    except (InvalidOperation, ValueError):
        return None


def _build_storage_name(brand: str, raw_name: str, product_url: str | None) -> str:
    """Build a stable unique-ish product name to avoid collapsing variants.

    The DB currently has UNIQUE(product_name), so we append an URL token.
    """
    base = f"{brand} - {raw_name}".strip()
    if not product_url:
        return base[:255]

    token = None
    try:
        parsed = urlparse(product_url)
        segments = [seg for seg in parsed.path.split('/') if seg]
        if segments:
            token = segments[-1]
        if parsed.query:
            swatch_match = re.search(r"(?:^|&)swatch=([^&]+)", parsed.query, flags=re.IGNORECASE)
            if swatch_match:
                swatch = swatch_match.group(1)
                token = f"{token}-{swatch}" if token else swatch
    except Exception:
        token = None

    if token:
        token = re.sub(r"[^a-zA-Z0-9\-_.]", "", token)
        return f"{base} [{token}]"[:255]
    return base[:255]


def save_products_to_db(products: list[dict[str, Any]]) -> int:
    inserted_rows = 0
    with get_connection() as conn:
        with conn.cursor() as cur:
            for product in products:
                brand = product.get("brand") or "Unknown"
                category = product.get("category") or "General"
                raw_name = product.get("name") or "Unnamed Product"
                product_url = product.get("url")
                name = _build_storage_name(brand, raw_name, product_url)
                image_url = product.get("image")
                product_url = product_url or BRAND_CONFIG["adidas"]["base_url"]
                price_decimal = _to_decimal(product.get("price"))

                if price_decimal is None:
                    continue

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
                    (name, brand, category, image_url),
                )
                row = cur.fetchone()
                if not row:
                    continue

                product_id = row["id"] if isinstance(row, dict) else row[0]

                cur.execute(
                    """
                    INSERT INTO product_prices (product_id, store_name, price, product_url)
                    VALUES (%s, %s, %s, %s);
                    """,
                    (product_id, brand, price_decimal, product_url),
                )
                inserted_rows += 1

        conn.commit()

    return inserted_rows


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scrape Adidas, Nike and Puma for 5 categories plus discounts and save to PostgreSQL"
    )
    parser.add_argument("--max-items", type=int, default=5, help="Maximum products per category and brand")
    parser.add_argument(
        "--brands",
        type=str,
        default="adidas,nike,puma",
        help="Comma-separated brands: adidas,nike,puma",
    )
    parser.add_argument("--dry-run", action="store_true", help="Do not write into PostgreSQL")
    parser.add_argument(
        "--output",
        type=str,
        default="multi_brand_products.json",
        help="Output JSON filename",
    )
    parser.add_argument("--pages", type=int, default=2, help="Pages per search URL to fetch")
    return parser.parse_args()


def main() -> None:
    args = _parse_args()

    selected_brands = [item.strip().lower() for item in args.brands.split(",") if item.strip()]
    invalid = [brand for brand in selected_brands if brand not in BRAND_CONFIG]
    if invalid:
        raise ValueError(f"Invalid brands: {', '.join(invalid)}")

    all_products: list[dict[str, Any]] = []
    report: dict[str, dict[str, Any]] = {}

    for brand_key in selected_brands:
        report[brand_key] = {}
        for category in CATEGORIES:
            products, source_url = scrape_brand_category(brand_key, category, max_items=args.max_items, pages=args.pages)
            report[brand_key][category] = {
                "count": len(products),
                "source_url": source_url,
            }
            all_products.extend(products)
            print(f"{brand_key} | {category}: {len(products)} products")

    with open(args.output, "w", encoding="utf-8") as file_obj:
        json.dump({"summary": report, "products": all_products}, file_obj, indent=2, ensure_ascii=False)

    print(f"Saved extracted data to {args.output}")

    if args.dry_run:
        print("Dry-run enabled: skipped PostgreSQL persistence")
        return

    inserted = save_products_to_db(all_products)
    print(f"Stored {inserted} product price rows in PostgreSQL")


if __name__ == "__main__":
    main()

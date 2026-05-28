"""
scrappy_brands.py — Scraper Adidas / Nike / Puma (5 categorías)
Uso:
    python -m backend.scraper.scrappy_brands --store puma --max-items 8
    python -m backend.scraper.scrappy_brands --store all --max-items 8
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from decimal import Decimal, InvalidOperation
from typing import Any
from urllib.parse import quote_plus, urljoin

from dotenv import load_dotenv
from scrapling.fetchers import Fetcher, StealthyFetcher

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
load_dotenv()
from backend.database.db import get_connection

StealthyFetcher.adaptive = True

CATEGORIES = ["running", "lifestyle", "training", "basketball", "football"]

STORES = {
    "adidas": {
        "name": "Adidas",
        "brand": "Adidas",
        "base_url": "https://www.adidas.co",
        "search_urls": lambda q: [
            f"https://www.adidas.co/search?q={quote_plus(q)}",
        ],
    },
    "nike": {
        "name": "Nike",
        "brand": "Nike",
        "base_url": "https://www.nike.com",
        "search_urls": lambda q: [
            f"https://www.nike.com/co/w?q={quote_plus(q)}&vst={quote_plus(q)}",
        ],
    },
    "puma": {
        "name": "Puma",
        "brand": "Puma",
        "base_url": "https://us.puma.com",
        "search_urls": lambda q: [
            f"https://us.puma.com/us/es/search?q={quote_plus(q)}",
            f"https://us.puma.com/us/en/search?q={quote_plus(q)}",
        ],
    },
}


def _css(node: Any, selector: str) -> Any:
    return node.css(selector)


def _extract_number(value: str | None) -> str | None:
    if not value:
        return None
    # Buscar precio tipo $99.99 o 399.960 o 399,960
    match = re.search(r"[\d]+[\d\.,]*", value.replace(",", "."))
    return match.group(0).rstrip(".") if match else None


def _is_product_type(value: Any) -> bool:
    if isinstance(value, str):
        return value.lower() == "product"
    if isinstance(value, list):
        return any(isinstance(i, str) and i.lower() == "product" for i in value)
    return False


def _extract_from_jsonld(raw_blocks: list[str], base_url: str) -> list[dict[str, Any]]:
    products: list[dict[str, Any]] = []
    seen: set[str] = set()

    def add(item: dict[str, Any]) -> None:
        offers = item.get("offers")
        if isinstance(offers, list):
            offers = offers[0] if offers else {}
        if not isinstance(offers, dict):
            offers = {}
        name = item.get("name")
        url = item.get("url") or ""
        if not url.startswith("http"):
            url = urljoin(base_url, url)
        key = f"{name}|{url}"
        if key in seen:
            return
        seen.add(key)
        image = item.get("image")
        if isinstance(image, list):
            image = image[0] if image else None
        products.append({
            "name": name,
            "brand": (item.get("brand") or {}).get("name") if isinstance(item.get("brand"), dict) else item.get("brand"),
            "price": str(offers.get("price", "")) or None,
            "url": url,
            "image": image,
            "source": "json-ld",
        })

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            if _is_product_type(node.get("@type")):
                add(node)
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)

    for raw in raw_blocks:
        try:
            walk(json.loads(raw))
        except json.JSONDecodeError:
            continue
    return products


# ─── PUMA ─────────────────────────────────────────────────────────────────────
# HTML: <li data-test-id="product-list-item">
#   <a aria-label="Nombre, Precio descontado, $99.99, ..." href="/us/es/pd/...">
#   <img src="https://images.puma.com/...">
#   <h2>Nombre</h2>
#   <span data-test-id="sale-price">$99.99</span>

def _extract_puma(page: Any, base_url: str, limit: int) -> list[dict[str, Any]]:
    products: list[dict[str, Any]] = []
    seen: set[str] = set()

    cards = _css(page, "li[data-test-id='product-list-item']")
    for card in cards:
        href = _css(card, "a[data-test-id='product-list-item-link']::attr(href)").get()
        if not href:
            href = _css(card, "a[aria-label]::attr(href)").get()
        if not href:
            continue

        absolute_url = urljoin(base_url, href)
        clean_url = re.sub(r"\?.*", "", absolute_url)
        if clean_url in seen:
            continue
        seen.add(clean_url)

        # Nombre desde h2 dentro del card
        name = (_css(card, "h2::text").get() or "").strip() or None

        # Si no hay nombre, parsear aria-label
        if not name:
            aria = _css(card, "a[aria-label]::attr(aria-label)").get() or ""
            aria_clean = re.sub(r"^\d+ Colou?rs?,\s*", "", aria)
            name_match = re.match(r"^(.+?)(?:,\s*(?:Preci[oa]|Discount|Regular|\$))", aria_clean, re.IGNORECASE)
            name = name_match.group(1).strip() if name_match else aria_clean.split(",")[0].strip() or None

        # Precio desde data-test-id="sale-price" o "price"
        price_raw = (
            _css(card, "span[data-test-id='sale-price']::text").get()
            or _css(card, "span[data-test-id='price']::text").get()
            or ""
        )

        # Imagen directa del img dentro del card
        img = _css(card, "img::attr(src)").get()

        if not name:
            continue

        products.append({
            "name": name,
            "url": absolute_url,
            "image": img,
            "price": _extract_number(price_raw),
            "source": "puma-card",
        })

        if len(products) >= limit:
            break

    # Fallback: aria-label en links /pd/
    if not products:
        for link in _css(page, "a[href*='/pd/'][aria-label]"):
            href = _css(link, "::attr(href)").get()
            aria = _css(link, "::attr(aria-label)").get() or ""
            if not href or not aria:
                continue
            absolute_url = urljoin(base_url, href)
            clean_url = re.sub(r"\?.*", "", absolute_url)
            if clean_url in seen:
                continue
            seen.add(clean_url)
            aria_clean = re.sub(r"^\d+ Colou?rs?,\s*", "", aria)
            price_match = re.search(r"\$\s*([\d,]+(?:\.\d{1,2})?)", aria_clean)
            price = price_match.group(1).replace(",", "") if price_match else None
            name_match = re.match(r"^(.+?)(?:,\s*(?:Preci[oa]|Discount|Regular|\$))", aria_clean, re.IGNORECASE)
            name = name_match.group(1).strip() if name_match else aria_clean.split(",")[0].strip() or None
            img = _css(link, "img::attr(src)").get()
            if not name:
                continue
            products.append({"name": name, "url": absolute_url, "image": img, "price": price, "source": "puma-aria"})
            if len(products) >= limit:
                break

    return products


# ─── ADIDAS ───────────────────────────────────────────────────────────────────
# HTML: <article data-testid="plp-product-card">
#   <img data-testid="product-card-primary-image" src="...">
#   <a href="https://www.adidas.co/tenis-samba-og/B75806.html">
#   <span class="_sale-color_...">$399.960</span>  (o en main-price)
#   <p data-testid="product-card-title">Tenis Samba OG</p>

def _extract_adidas(page: Any, base_url: str, limit: int) -> list[dict[str, Any]]:
    products: list[dict[str, Any]] = []
    seen: set[str] = set()

    cards = _css(page, "article[data-testid='plp-product-card']")
    for card in cards:
        href = (_css(card, "a[data-testid='product-card-image-link']::attr(href)").get()
                or _css(card, "a[data-testid='product-card-description-link']::attr(href)").get()
                or _css(card, "a[href*='.html']::attr(href)").get())
        if not href:
            continue

        absolute_url = href if href.startswith("http") else urljoin(base_url, href)
        if absolute_url in seen:
            continue
        seen.add(absolute_url)

        # Nombre
        name = (_css(card, "p[data-testid='product-card-title']::text").get() or "").strip() or None

        # Precio de venta (primer span dentro de main-price)
        price_raw = (
            _css(card, "div[data-testid='main-price'] span:last-child::text").get()
            or _css(card, "div[data-testid='main-price'] span::text").get()
            or _css(card, "div[data-testid='price-component'] span::text").get()
            or ""
        )

        # Imagen principal
        img = _css(card, "img[data-testid='product-card-primary-image']::attr(src)").get()

        if not name:
            continue

        products.append({
            "name": name,
            "url": absolute_url,
            "image": img,
            "price": _extract_number(price_raw),
            "source": "adidas-card",
        })

        if len(products) >= limit:
            break

    # Fallback JSON-LD
    if not products:
        raw_blocks = _css(page, "script[type='application/ld+json']::text").getall()
        products = _extract_from_jsonld(raw_blocks, base_url)

    return products[:limit]


# ─── NIKE ─────────────────────────────────────────────────────────────────────

def _extract_nike(page: Any, base_url: str, limit: int) -> list[dict[str, Any]]:
    products: list[dict[str, Any]] = []
    seen: set[str] = set()

    # Intentar JSON-LD primero (Nike a veces lo incluye)
    raw_blocks = _css(page, "script[type='application/ld+json']::text").getall()
    products = _extract_from_jsonld(raw_blocks, base_url)
    if products:
        return products[:limit]

    # Cards
    cards = (_css(page, "div[data-testid='product-card']")
             or _css(page, "div[class*='product-card']"))
    for card in cards:
        href = (_css(card, "a[data-testid='product-card__link-overlay']::attr(href)").get()
                or _css(card, "a::attr(href)").get())
        if not href:
            continue
        absolute_url = urljoin(base_url, href)
        if absolute_url in seen:
            continue
        seen.add(absolute_url)
        name = (_css(card, "div[data-testid='product-card__title']::text").get()
                or _css(card, "div[class*='title']::text").get()
                or _css(card, "h3::text").get() or "").strip() or None
        price_raw = (_css(card, "div[data-testid='product-price']::text").get()
                     or _css(card, "div[class*='price']::text").get() or "")
        img = _css(card, "img::attr(src)").get()
        products.append({"name": name, "url": absolute_url, "image": img,
                         "price": _extract_number(price_raw), "source": "nike-card"})
        if len(products) >= limit:
            break

    return products[:limit]


# ─── FETCH ────────────────────────────────────────────────────────────────────

def _get_pages(url: str) -> list[Any]:
    pages: list[Any] = []
    try:
        stealth = StealthyFetcher.fetch(url, headless=True, network_idle=True, adaptive=True)
        if getattr(stealth, "status", 200) == 200:
            pages.append(stealth)
            print(f"    ✓ StealthyFetcher OK")
    except Exception as e:
        print(f"    ✗ StealthyFetcher falló: {e}")

    if not pages:
        try:
            static = Fetcher.get(url)
            if getattr(static, "status", 0) == 200:
                pages.append(static)
                print(f"    ✓ Fetcher estático OK")
        except Exception as e:
            print(f"    ✗ Fetcher estático falló: {e}")

    return pages


# ─── SCRAPER PRINCIPAL ────────────────────────────────────────────────────────

def scrape_store_category(store_key: str, category: str, max_items: int = 10) -> list[dict[str, Any]]:
    store = STORES[store_key]
    base_url = store["base_url"]

    for url in store["search_urls"](category):
        print(f"  → {url}")
        pages = _get_pages(url)

        for page in pages:
            if store_key == "puma":
                products = _extract_puma(page, base_url, max_items)
            elif store_key == "nike":
                products = _extract_nike(page, base_url, max_items)
            else:
                products = _extract_adidas(page, base_url, max_items)

            if products:
                for p in products:
                    p["brand"] = p.get("brand") or store["brand"]
                    p["category"] = category
                    p["store_name"] = store["name"]
                n_price = sum(1 for p in products if p.get("price"))
                n_img = sum(1 for p in products if p.get("image"))
                print(f"    → {len(products)} productos | {n_price} con precio | {n_img} con imagen")
                return products[:max_items]

        time.sleep(1)

    print(f"  ⚠️  Sin resultados: {store['name']} / {category}")
    return []


# ─── GUARDAR EN BD ────────────────────────────────────────────────────────────

def _parse_price(value: Any) -> Decimal | None:
    if value is None:
        return None
    cleaned = re.sub(r"[^\d\.]", "", str(value))
    if not cleaned:
        return None
    try:
        d = Decimal(cleaned).quantize(Decimal("0.01"))
        return d if d > 0 else None
    except InvalidOperation:
        return None


def save_products(products: list[dict[str, Any]]) -> int:
    stored = 0
    with get_connection() as conn:
        with conn.cursor() as cur:
            for p in products:
                name = (p.get("name") or "").strip()[:255]
                if not name:
                    continue
                brand = (p.get("brand") or "Unknown").strip()[:100]
                category = (p.get("category") or "General").strip()[:50]
                store_name = (p.get("store_name") or brand).strip()[:100]
                image = p.get("image")
                if isinstance(image, list):
                    image = image[0] if image else None
                url = (p.get("url") or "").strip()

                cur.execute("""
                    INSERT INTO products (product_name, brand, category, image_url)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (product_name) DO UPDATE SET
                        brand     = EXCLUDED.brand,
                        category  = EXCLUDED.category,
                        image_url = COALESCE(EXCLUDED.image_url, products.image_url)
                    RETURNING id;
                """, (name, brand, category, image))
                pid = cur.fetchone()["id"]

                price = _parse_price(p.get("price"))
                if price and url:
                    cur.execute("""
                        INSERT INTO product_prices (product_id, store_name, price, product_url)
                        VALUES (%s, %s, %s, %s);
                    """, (pid, store_name, price, url[:500]))
                    stored += 1
                elif not price:
                    # Guardar producto sin precio igual (al menos en products)
                    pass

        conn.commit()
    return stored


# ─── MAIN ─────────────────────────────────────────────────────────────────────

def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Scraper Adidas / Nike / Puma")
    parser.add_argument("--store", choices=["adidas", "nike", "puma", "all"], default="all")
    parser.add_argument("--category", type=str, default=None)
    parser.add_argument("--max-items", type=int, default=8)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    stores = list(STORES.keys()) if args.store == "all" else [args.store]
    categories = [args.category] if args.category else CATEGORIES

    total_products: list[dict[str, Any]] = []
    total_stored = 0

    for store_key in stores:
        print(f"\n{'='*50}")
        print(f"🏪 {STORES[store_key]['name']}")
        print(f"{'='*50}")
        for category in categories:
            print(f"\n📦 {category}")
            products = scrape_store_category(store_key, category, args.max_items)
            if products:
                stored = save_products(products)
                total_stored += stored
                print(f"    💾 Guardados en BD: {stored}")
            total_products.extend(products)
            time.sleep(2)

    print(f"\n{'='*50}")
    print(f"✅ Total recolectados : {len(total_products)}")
    print(f"✅ Total guardados BD : {total_stored}")
    print(f"{'='*50}\n")


if __name__ == "__main__":
    main()
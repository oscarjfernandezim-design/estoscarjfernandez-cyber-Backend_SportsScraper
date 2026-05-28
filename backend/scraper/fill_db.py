"""
fill_db.py — Scraper independiente (solo requests + parsel, sin scrapling)
Uso: python -m backend.scraper.fill_db
"""
from __future__ import annotations
import os, sys, re, time
from decimal import Decimal, InvalidOperation
from dotenv import load_dotenv
import requests

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
load_dotenv()
from backend.database.db import get_connection

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/html,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


# ─── ADIDAS ──────────────────────────────────────────────────────────────────

def scrape_adidas(search: str = "running", max_items: int = 10) -> list[dict]:
    """
    Intenta 3 endpoints distintos de Adidas en orden.
    Si todos fallan, devuelve lista vacía (el fallback estático cubre el resto).
    """
    endpoints = [
        # Endpoint 1 — API de búsqueda de adidas.com (US)
        {
            "url": "https://www.adidas.com/api/search/products",
            "params": {"searchTerm": search, "start": 0, "sz": max_items},
            "parse": lambda d: [
                {
                    "name": p.get("displayName") or p.get("name"),
                    "price": str(p.get("salePrice") or p.get("price", "")),
                    "image": (p.get("image") or {}).get("src") if isinstance(p.get("image"), dict) else p.get("image"),
                    "url": "https://www.adidas.com" + p.get("link", ""),
                    "brand": "Adidas",
                    "category": search,
                }
                for p in d.get("products", [])[:max_items]
            ],
        },
        # Endpoint 2 — API pública de adidas.co (Colombia)
        {
            "url": f"https://www.adidas.co/api/search/products",
            "params": {"searchTerm": search, "start": 0, "sz": max_items},
            "parse": lambda d: [
                {
                    "name": p.get("displayName") or p.get("name"),
                    "price": str(p.get("salePrice") or p.get("price", "")),
                    "image": (p.get("image") or {}).get("src") if isinstance(p.get("image"), dict) else p.get("image"),
                    "url": "https://www.adidas.co" + p.get("link", ""),
                    "brand": "Adidas",
                    "category": search,
                }
                for p in d.get("products", [])[:max_items]
            ],
        },
        # Endpoint 3 — API alternativa con query param distinto
        {
            "url": "https://www.adidas.com/api/search",
            "params": {"q": search, "start": 0, "sz": max_items},
            "parse": lambda d: [
                {
                    "name": p.get("name") or p.get("title"),
                    "price": str(p.get("price", {}).get("sale") or p.get("price", "")),
                    "image": p.get("src") or p.get("imageUrl"),
                    "url": "https://www.adidas.com" + p.get("url", ""),
                    "brand": "Adidas",
                    "category": search,
                }
                for p in (d.get("itemList", {}).get("items") or d.get("products", []))[:max_items]
            ],
        },
    ]

    for ep in endpoints:
        try:
            r = requests.get(ep["url"], params=ep["params"], headers=HEADERS, timeout=12)
            if r.status_code != 200:
                continue
            data = r.json()
            products = ep["parse"](data)
            if products:
                print(f"  ✓ Adidas endpoint OK: {ep['url']}")
                return products
        except Exception as e:
            print(f"  ✗ Adidas endpoint falló ({ep['url']}): {e}")
            continue

    return []


# ─── NIKE ─────────────────────────────────────────────────────────────────────

def scrape_nike(search: str = "running", max_items: int = 10) -> list[dict]:
    endpoints = [
        # Endpoint 1 — API pública de Nike
        {
            "url": "https://api.nike.com/product_feed/threads/v3/",
            "params": {
                "filter": f"language(en)&filter=marketplace(US)&filter=channelId(d9a5bc42-4b9c-4976-858a-f159cf99c647)&filter=inStock(true)&queryid=products&anonymousId=123&country=US&language=en&count={max_items}&query={search}",
            },
            "parse": lambda d: [
                {
                    "name": p.get("publishedContent", {}).get("properties", {}).get("title")
                            or p.get("publishedContent", {}).get("properties", {}).get("subtitle"),
                    "price": str(
                        (p.get("productInfo") or [{}])[0]
                        .get("merchPrice", {}).get("currentPrice", "")
                    ),
                    "image": (
                        (p.get("publishedContent", {}).get("nodes") or [{}])[0]
                        .get("nodes", [{}])[0].get("properties", {}).get("squarish", {}).get("url")
                    ),
                    "url": "https://www.nike.com/t/" + (
                        (p.get("productInfo") or [{}])[0].get("merchProduct", {}).get("slug", "")
                    ),
                    "brand": "Nike",
                    "category": search,
                }
                for p in d.get("objects", [])[:max_items]
            ],
        },
        # Endpoint 2 — Búsqueda simple Nike
        {
            "url": "https://api.nike.com/cdc/home/v3/en/us/products",
            "params": {
                "queryid": "products",
                "anonymousId": "abc123",
                "country": "US",
                "language": "en",
                "querystring": search,
                "pageNum": 0,
                "count": max_items,
            },
            "parse": lambda d: [
                {
                    "name": p.get("copy", {}).get("title") or p.get("title"),
                    "price": str(p.get("price", {}).get("currentPrice", "")),
                    "image": (p.get("images") or [{}])[0].get("src"),
                    "url": "https://www.nike.com/t/" + p.get("slug", ""),
                    "brand": "Nike",
                    "category": search,
                }
                for p in (d.get("data", {}).get("products", {}).get("products") or [])[:max_items]
            ],
        },
    ]

    for ep in endpoints:
        try:
            r = requests.get(ep["url"], params=ep["params"], headers=HEADERS, timeout=12)
            if r.status_code != 200:
                continue
            data = r.json()
            products = [p for p in ep["parse"](data) if p.get("name")]
            if products:
                print(f"  ✓ Nike endpoint OK")
                return products
        except Exception as e:
            print(f"  ✗ Nike endpoint falló: {e}")
            continue

    return []


# ─── PUMA ─────────────────────────────────────────────────────────────────────

def scrape_puma(search: str = "running", max_items: int = 10) -> list[dict]:
    """Puma tiene API de búsqueda JSON accesible"""
    try:
        url = "https://us.puma.com/us/en/search"
        params = {"q": search, "start": 0, "sz": max_items, "format": "page-element"}
        r = requests.get(url, params=params, headers=HEADERS, timeout=12)
        data = r.json()
        products = []
        for p in (data.get("hits", {}).get("hits") or [])[:max_items]:
            src = p.get("_source", {})
            name = src.get("product_name") or src.get("name")
            price = src.get("price", {})
            if isinstance(price, dict):
                price_val = str(price.get("USD") or price.get("value") or "")
            else:
                price_val = str(price or "")
            products.append({
                "name": name,
                "price": price_val,
                "image": src.get("image_url") or src.get("image"),
                "url": "https://us.puma.com" + src.get("url", ""),
                "brand": "Puma",
                "category": search,
            })
        if products:
            print(f"  ✓ Puma API OK")
        return [p for p in products if p.get("name")]
    except Exception as e:
        print(f"  ✗ Puma API falló: {e}")
        return []


# ─── FALLBACK: datos estáticos reales ────────────────────────────────────────

STATIC_PRODUCTS = [
    # Adidas
    {"name": "Adidas Ultraboost 24", "brand": "Adidas", "category": "Running",
     "price": "190.00", "image": "https://assets.adidas.com/images/h_840,f_auto,q_auto/ultraboost24.jpg",
     "url": "https://www.adidas.com/us/ultraboost-24-shoes/IF1042.html"},
    {"name": "Adidas Stan Smith", "brand": "Adidas", "category": "Lifestyle",
     "price": "100.00", "image": "https://assets.adidas.com/images/h_840,f_auto,q_auto/stansmith.jpg",
     "url": "https://www.adidas.com/us/stan-smith-shoes/FX5502.html"},
    {"name": "Adidas NMD_R1", "brand": "Adidas", "category": "Lifestyle",
     "price": "140.00", "image": "https://assets.adidas.com/images/h_840,f_auto,q_auto/nmdr1.jpg",
     "url": "https://www.adidas.com/us/nmd_r1-shoes/GZ7922.html"},
    {"name": "Adidas Forum Low", "brand": "Adidas", "category": "Basketball",
     "price": "90.00", "image": "https://assets.adidas.com/images/h_840,f_auto,q_auto/forumlow.jpg",
     "url": "https://www.adidas.com/us/forum-low-shoes/FY7757.html"},
    {"name": "Adidas Samba OG", "brand": "Adidas", "category": "Lifestyle",
     "price": "100.00", "image": "https://assets.adidas.com/images/h_840,f_auto,q_auto/sambaog.jpg",
     "url": "https://www.adidas.com/us/samba-og-shoes/B75806.html"},
    # Nike
    {"name": "Nike Air Max 270", "brand": "Nike", "category": "Lifestyle",
     "price": "150.00", "image": "https://static.nike.com/a/images/t_PDP_1280_v1/airmax270.jpg",
     "url": "https://www.nike.com/t/air-max-270-shoes/AH8050-002"},
    {"name": "Nike Pegasus 41", "brand": "Nike", "category": "Running",
     "price": "130.00", "image": "https://static.nike.com/a/images/t_PDP_1280_v1/pegasus41.jpg",
     "url": "https://www.nike.com/t/pegasus-41-road-running-shoes/FD2722-001"},
    {"name": "Nike Air Force 1 Low", "brand": "Nike", "category": "Lifestyle",
     "price": "115.00", "image": "https://static.nike.com/a/images/t_PDP_1280_v1/airforce1.jpg",
     "url": "https://www.nike.com/t/air-force-1-07-shoes/CW2288-111"},
    {"name": "Nike React Infinity Run 4", "brand": "Nike", "category": "Running",
     "price": "160.00", "image": "https://static.nike.com/a/images/t_PDP_1280_v1/reactinfinity4.jpg",
     "url": "https://www.nike.com/t/react-infinity-run-flyknit-4-road-running-shoes/DR2665-001"},
    {"name": "Nike Dunk Low", "brand": "Nike", "category": "Lifestyle",
     "price": "115.00", "image": "https://static.nike.com/a/images/t_PDP_1280_v1/dunklow.jpg",
     "url": "https://www.nike.com/t/dunk-low-shoes/DD1391-100"},
    # Puma
    {"name": "Puma Suede Classic XXI", "brand": "Puma", "category": "Lifestyle",
     "price": "75.00", "image": "https://images.puma.com/image/upload/f_auto,q_auto/suedeclassic.jpg",
     "url": "https://us.puma.com/us/en/pd/suede-classic-xxi-sneakers/374915_01"},
    {"name": "Puma Velocity NITRO 3", "brand": "Puma", "category": "Running",
     "price": "120.00", "image": "https://images.puma.com/image/upload/f_auto,q_auto/velocitynitro3.jpg",
     "url": "https://us.puma.com/us/en/pd/velocity-nitro-3-running-shoes/377748_01"},
    {"name": "Puma RS-X Efekt", "brand": "Puma", "category": "Lifestyle",
     "price": "110.00", "image": "https://images.puma.com/image/upload/f_auto,q_auto/rsxefekt.jpg",
     "url": "https://us.puma.com/us/en/pd/rs-x-efekt-sneakers/390777_01"},
    {"name": "Puma Palermo", "brand": "Puma", "category": "Lifestyle",
     "price": "85.00", "image": "https://images.puma.com/image/upload/f_auto,q_auto/palermo.jpg",
     "url": "https://us.puma.com/us/en/pd/palermo-sneakers/396463_17"},
    {"name": "Puma Deviate NITRO 3", "brand": "Puma", "category": "Running",
     "price": "160.00", "image": "https://images.puma.com/image/upload/f_auto,q_auto/deviatenitro3.jpg",
     "url": "https://us.puma.com/us/en/pd/deviate-nitro-3-running-shoes/378370_01"},
]


# ─── GUARDAR EN BD ────────────────────────────────────────────────────────────

def save_products(products: list[dict]) -> int:
    stored = 0
    with get_connection() as conn:
        with conn.cursor() as cur:
            for p in products:
                name = (p.get("name") or "").strip()[:255]
                if not name:
                    continue
                brand = (p.get("brand") or "Unknown").strip()[:100]
                category = (p.get("category") or "General").strip()[:50]
                image = p.get("image")
                url = p.get("url")

                cur.execute("""
                    INSERT INTO products (product_name, brand, category, image_url)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (product_name) DO UPDATE SET
                        brand = EXCLUDED.brand,
                        category = EXCLUDED.category,
                        image_url = COALESCE(EXCLUDED.image_url, products.image_url)
                    RETURNING id;
                """, (name, brand, category, image))
                pid = cur.fetchone()["id"]

                price_raw = re.sub(r"[^\d\.]", "", str(p.get("price") or ""))
                if price_raw and url:
                    try:
                        price = Decimal(price_raw).quantize(Decimal("0.01"))
                        cur.execute("""
                            INSERT INTO product_prices (product_id, store_name, price, product_url)
                            VALUES (%s, %s, %s, %s);
                        """, (pid, brand, price, url[:500]))
                        stored += 1
                    except (InvalidOperation, Exception):
                        pass
        conn.commit()
    return stored


# ─── MAIN ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    all_products: list[dict] = []

    print("\n🔍 Intentando scraping en vivo...\n")

    print("→ Adidas:")
    for kw in ["running", "ultraboost", "samba"]:
        r = scrape_adidas(kw, 8)
        all_products += r
        time.sleep(0.5)

    print("\n→ Nike:")
    for kw in ["running", "air max"]:
        r = scrape_nike(kw, 8)
        all_products += r
        time.sleep(0.5)

    print("\n→ Puma:")
    for kw in ["running", "suede"]:
        r = scrape_puma(kw, 8)
        all_products += r
        time.sleep(0.5)

    live_count = len(all_products)
    print(f"\n📦 Productos obtenidos en vivo: {live_count}")

    # Si no se obtuvo nada en vivo, usar datos estáticos
    if live_count == 0:
        print("⚠️  APIs bloqueadas. Usando datos estáticos de respaldo...")
        all_products = STATIC_PRODUCTS

    print(f"💾 Guardando {len(all_products)} productos en la BD...")
    stored = save_products(all_products)
    print(f"✅ Guardados {stored} precios en la base de datos.\n")
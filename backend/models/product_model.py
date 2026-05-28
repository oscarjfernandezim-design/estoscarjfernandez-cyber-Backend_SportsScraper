from typing import Any, List, Optional
from backend.database.db import get_connection


def list_products(limit: int = 100, offset: int = 0, q: Optional[str] = None, brand: Optional[str] = None, category: Optional[str] = None, sort: str = 'newest') -> List[dict[str, Any]]:
    filters = []
    params = []
    if q:
        filters.append("(p.product_name ILIKE %s OR p.brand ILIKE %s)")
        params.extend([f"%{q}%", f"%{q}%"])
    if brand:
        filters.append("p.brand = %s")
        params.append(brand)
    if category:
        filters.append("p.category = %s")
        params.append(category)

    where = f"WHERE {' AND '.join(filters)}" if filters else ""

    order = "p.id DESC"
    if sort == 'price-low':
        order = "(SELECT price FROM product_prices WHERE product_id = p.id ORDER BY scraped_at DESC LIMIT 1) ASC NULLS LAST"
    elif sort == 'price-high':
        order = "(SELECT price FROM product_prices WHERE product_id = p.id ORDER BY scraped_at DESC LIMIT 1) DESC NULLS LAST"

    query = (
        "SELECT p.id, p.product_name, p.brand, p.category, p.image_url, "
        "(SELECT price FROM product_prices WHERE product_id = p.id ORDER BY scraped_at DESC LIMIT 1) as latest_price "
        f"FROM products p {where} ORDER BY {order} LIMIT %s OFFSET %s"
    )
    params.extend([limit, offset])
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, tuple(params))
            rows = cur.fetchall()
    return [dict(row) for row in rows]


def get_price_history(product_id: int) -> List[dict[str, Any]]:
    query = (
        "SELECT id, store_name, price, product_url, scraped_at "
        "FROM product_prices WHERE product_id = %s ORDER BY scraped_at ASC"
    )
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (product_id,))
            rows = cur.fetchall()
    return [dict(row) for row in rows]


def get_product_by_id(product_id: int) -> dict[str, Any] | None:
    query = "SELECT id, product_name, brand, category, image_url FROM products WHERE id = %s"
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (product_id,))
            row = cur.fetchone()
    return dict(row) if row else None


def get_offers_for_product(product_id: int) -> List[dict[str, Any]]:
    # return latest price per store for given product
    query = (
        "SELECT DISTINCT ON (store_name) store_name, price, product_url, scraped_at "
        "FROM product_prices WHERE product_id = %s ORDER BY store_name, scraped_at DESC"
    )
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (product_id,))
            rows = cur.fetchall()
    return [dict(row) for row in rows]

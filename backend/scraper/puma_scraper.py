from typing import Any
from .scrappy_adidad import scrape_brand_category, save_products_to_db


def scrape_category(category: str, max_items: int = 5, persist: bool = False) -> list[dict[str, Any]]:
    products, src = scrape_brand_category("puma", category, max_items=max_items)
    if persist and products:
        save_products_to_db(products)
    return products


def run_all(categories: list[str], max_items: int = 5, persist: bool = False) -> list[dict[str, Any]]:
    all_products = []
    for cat in categories:
        prods = scrape_category(cat, max_items=max_items, persist=persist)
        all_products.extend(prods)
    return all_products

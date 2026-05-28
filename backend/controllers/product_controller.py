from flask import jsonify, request
from typing import Any

from backend.models.product_model import list_products, get_price_history, get_product_by_id, get_offers_for_product


def list_products_handler():
    limit = int(request.args.get("limit", 100))
    offset = int(request.args.get("offset", 0))
    q = request.args.get('q')
    brand = request.args.get('brand')
    category = request.args.get('category')
    sort = request.args.get('sort', 'newest')
    products = list_products(limit=limit, offset=offset, q=q, brand=brand, category=category, sort=sort)
    return jsonify(products)


def product_prices_handler(product_id: int):
    product = get_product_by_id(product_id)
    if not product:
        return jsonify({"error": "Product not found"}), 404
    history = get_price_history(product_id)
    return jsonify({"product": product, "history": history})


def product_offers_handler(product_id: int):
    product = get_product_by_id(product_id)
    if not product:
        return jsonify({"error": "Product not found"}), 404
    offers = get_offers_for_product(product_id)
    return jsonify({"product": product, "offers": offers})

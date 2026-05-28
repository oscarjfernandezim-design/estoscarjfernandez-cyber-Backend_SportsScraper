from flask import Blueprint
from backend.controllers.product_controller import list_products_handler, product_prices_handler, product_offers_handler

product_bp = Blueprint("products", __name__)

product_bp.add_url_rule("/", endpoint="list_products", view_func=list_products_handler, methods=["GET"])
product_bp.add_url_rule("/<int:product_id>/prices", endpoint="product_prices", view_func=product_prices_handler, methods=["GET"])
product_bp.add_url_rule("/<int:product_id>/offers", endpoint="product_offers", view_func=product_offers_handler, methods=["GET"])

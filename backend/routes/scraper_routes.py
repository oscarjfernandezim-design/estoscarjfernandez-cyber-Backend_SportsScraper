from flask import Blueprint
from backend.controllers.scraper_controller import run_scraper_handler, health_check_handler

scraper_bp = Blueprint('scraper', __name__)

scraper_bp.add_url_rule('/run', endpoint='run_scraper', view_func=run_scraper_handler, methods=['POST'])
scraper_bp.add_url_rule('/health', endpoint='scraper_health', view_func=health_check_handler, methods=['GET'])

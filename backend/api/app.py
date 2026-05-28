import os
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from dotenv import load_dotenv
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS

from backend.routes.user_routes import user_bp
from backend.routes.product_routes import product_bp


load_dotenv()


def create_app() -> Flask:
    app = Flask(__name__)
    CORS(app)

    app.register_blueprint(user_bp, url_prefix="/api/users")
    app.register_blueprint(product_bp, url_prefix="/api/products")
    from backend.routes.alert_routes import alert_bp
    app.register_blueprint(alert_bp, url_prefix="/api/alerts")
    from backend.routes.auth_routes import auth_bp
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    from backend.routes.scraper_routes import scraper_bp
    app.register_blueprint(scraper_bp, url_prefix="/api/scraper")

    @app.get("/")
    def serve_index():
        return send_from_directory(ROOT_DIR, "index.html")

    @app.get("/health")
    def health():
        return jsonify({"message": "API running", "docs": "/api/users"})

    @app.get("/css/<path:filename>")
    def serve_css(filename: str):
        return send_from_directory(ROOT_DIR / "css", filename)

    @app.get("/js/<path:filename>")
    def serve_js(filename: str):
        return send_from_directory(ROOT_DIR / "js", filename)

    @app.get("/img/<path:filename>")
    def serve_img(filename: str):
        return send_from_directory(ROOT_DIR / "img", filename)

    @app.get("/favicon.ico")
    def favicon():
        return ("", 204)

    @app.errorhandler(Exception)
    def handle_error(error):
        status = getattr(error, "status_code", 500)
        message = str(error) if str(error) else "Internal server error"
        return jsonify({"error": message}), status

    return app


app = create_app()


if __name__ == "__main__":
    port = int(os.getenv("PORT", "3000"))
    app.run(host='0.0.0.0', port=3000, threaded=False)

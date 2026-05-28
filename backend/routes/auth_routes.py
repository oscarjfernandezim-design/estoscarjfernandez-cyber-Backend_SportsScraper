from flask import Blueprint
from backend.controllers.auth_controller import register_handler, login_handler, change_password_handler

auth_bp = Blueprint('auth', __name__)

auth_bp.add_url_rule('/register', endpoint='register', view_func=register_handler, methods=['POST'])
auth_bp.add_url_rule('/login', endpoint='login', view_func=login_handler, methods=['POST'])
auth_bp.add_url_rule('/change-password', endpoint='change_password', view_func=change_password_handler, methods=['POST'])

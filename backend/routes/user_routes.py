from flask import Blueprint

from backend.controllers.user_controller import (
    create_user_handler,
    delete_user_handler,
    list_users,
    update_user_handler,
)


user_bp = Blueprint("users", __name__)


user_bp.get("/")(list_users)
user_bp.post("/")(create_user_handler)
user_bp.put("/<int:user_id>")(update_user_handler)
user_bp.delete("/<int:user_id>")(delete_user_handler)

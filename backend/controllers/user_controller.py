import re

from flask import jsonify, request

from backend.models.user_model import (
    DuplicateEmailError,
    create_user,
    delete_user,
    get_all_users,
    update_user,
)


EMAIL_REGEX = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def _validate_payload(data):
    full_name = str(data.get("full_name", "")).strip()
    email = str(data.get("email", "")).strip().lower()

    if not full_name or not email:
        return None, "full_name and email are required"

    if not EMAIL_REGEX.match(email):
        return None, "email format is invalid"

    return {"full_name": full_name, "email": email}, None


def list_users():
    users = get_all_users()
    return jsonify(users), 200


def create_user_handler():
    payload, error = _validate_payload(request.get_json(silent=True) or {})
    if error:
        return jsonify({"error": error}), 400

    try:
        new_user = create_user(payload["full_name"], payload["email"])
        return jsonify(new_user), 201
    except DuplicateEmailError as exc:
        return jsonify({"error": str(exc)}), 409


def update_user_handler(user_id: int):
    if user_id <= 0:
        return jsonify({"error": "invalid id"}), 400

    payload, error = _validate_payload(request.get_json(silent=True) or {})
    if error:
        return jsonify({"error": error}), 400

    try:
        updated = update_user(user_id, payload["full_name"], payload["email"])
        if not updated:
            return jsonify({"error": "user not found"}), 404
        return jsonify(updated), 200
    except DuplicateEmailError as exc:
        return jsonify({"error": str(exc)}), 409


def delete_user_handler(user_id: int):
    if user_id <= 0:
        return jsonify({"error": "invalid id"}), 400

    deleted = delete_user(user_id)
    if not deleted:
        return jsonify({"error": "user not found"}), 404

    return "", 204

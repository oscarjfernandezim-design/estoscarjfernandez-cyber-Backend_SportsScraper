import os
import jwt
from datetime import datetime, timedelta
from flask import jsonify, request, current_app
from werkzeug.security import check_password_hash

from backend.models.user_model import (
    create_user,
    authenticate_user,
    DuplicateEmailError,
    get_user_by_id,
    update_password,
)
from backend.utils.jwt_utils import get_current_user_id


def _get_jwt_secret():
    return os.getenv('JWT_SECRET', 'dev-secret')


def register_handler():
    body = request.get_json() or {}
    name = str(body.get('full_name', '')).strip()
    email = str(body.get('email', '')).strip().lower()
    password = str(body.get('password', ''))
    if not name or not email or not password:
        return jsonify({'error': 'full_name, email and password required'}), 400
    try:
        user = create_user(name, email, password)
        return jsonify(user), 201
    except DuplicateEmailError as exc:
        return jsonify({'error': str(exc)}), 409


def login_handler():
    body = request.get_json() or {}
    email = str(body.get('email', '')).strip().lower()
    password = str(body.get('password', ''))
    if not email or not password:
        return jsonify({'error': 'email and password required'}), 400

    user = authenticate_user(email, password)
    if not user:
        return jsonify({'error': 'invalid credentials'}), 401

    payload = {
        'sub': user['id'],
        'name': user['full_name'],
        'exp': datetime.utcnow() + timedelta(days=7)
    }
    token = jwt.encode(payload, _get_jwt_secret(), algorithm='HS256')
    return jsonify({'token': token, 'user': user})


def change_password_handler():
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({'error': 'unauthorized'}), 401

    body = request.get_json() or {}
    old_password = str(body.get('old_password', ''))
    new_password = str(body.get('new_password', ''))

    if not old_password or not new_password:
        return jsonify({'error': 'old_password and new_password required'}), 400

    if len(new_password) < 6:
        return jsonify({'error': 'new password must have at least 6 characters'}), 400

    user = get_user_by_id(int(user_id))
    if not user:
        return jsonify({'error': 'user not found'}), 404

    stored_password = user.get('password') if isinstance(user, dict) else user[3]
    if not stored_password or not check_password_hash(stored_password, old_password):
        return jsonify({'error': 'invalid current password'}), 401

    updated_user = update_password(int(user_id), new_password)
    if not updated_user:
        return jsonify({'error': 'could not update password'}), 500

    return jsonify({'success': True}), 200

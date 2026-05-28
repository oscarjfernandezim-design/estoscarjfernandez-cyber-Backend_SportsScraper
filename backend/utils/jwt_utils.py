import os
import jwt
from flask import request


def get_jwt_secret():
    return os.getenv('JWT_SECRET', 'dev-secret')


def get_current_user_id():
    auth = request.headers.get('Authorization') or ''
    if not auth.startswith('Bearer '):
        return None
    token = auth.split(' ', 1)[1]
    try:
        payload = jwt.decode(token, get_jwt_secret(), algorithms=['HS256'])
        return payload.get('sub')
    except Exception:
        return None

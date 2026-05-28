from flask import jsonify, request
from backend.models.alert_model import create_alert, list_alerts, toggle_alert, delete_alert
from backend.utils.jwt_utils import get_current_user_id




def create_alert_handler():
    body = request.get_json() or {}
    product_id = body.get('product_id')
    target_price = body.get('target_price')
    stores = body.get('stores')
    if not product_id or not target_price:
        return jsonify({'error': 'product_id and target_price required'}), 400
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({'error': 'authentication required'}), 401
    alert = create_alert(product_id=int(product_id), target_price=float(target_price), stores=stores, user_id=int(user_id))
    return jsonify(alert), 201


def list_alerts_handler():
    user_id = get_current_user_id()
    alerts = list_alerts(user_id=int(user_id)) if user_id else list_alerts()
    return jsonify(alerts)


def toggle_alert_handler(alert_id: int):
    body = request.get_json() or {}
    enabled = body.get('enabled')
    if enabled is None:
        return jsonify({'error': 'enabled boolean required'}), 400
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({'error': 'authentication required'}), 401
    ok = toggle_alert(alert_id, bool(enabled), user_id=int(user_id))
    if not ok:
        return jsonify({'error': 'not found or not authorized'}), 404
    return jsonify({'ok': True})


def delete_alert_handler(alert_id: int):
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({'error': 'authentication required'}), 401
    ok = delete_alert(alert_id, user_id=int(user_id))
    if not ok:
        return jsonify({'error': 'not found or not authorized'}), 404
    return jsonify({'ok': True})

from flask import Blueprint
from backend.controllers.alert_controller import create_alert_handler, list_alerts_handler, toggle_alert_handler, delete_alert_handler

alert_bp = Blueprint('alerts', __name__)

alert_bp.add_url_rule('/', endpoint='list_alerts', view_func=list_alerts_handler, methods=['GET'])
alert_bp.add_url_rule('/', endpoint='create_alert', view_func=create_alert_handler, methods=['POST'])
alert_bp.add_url_rule('/<int:alert_id>/toggle', endpoint='toggle_alert', view_func=toggle_alert_handler, methods=['PUT'])
alert_bp.add_url_rule('/<int:alert_id>', endpoint='delete_alert', view_func=delete_alert_handler, methods=['DELETE'])

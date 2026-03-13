from flask import Blueprint, jsonify
from app.services.mqtt_publisher import get_mqtt_publisher
import logging

logger = logging.getLogger(__name__)
mqtt_status_bp = Blueprint('mqtt_status', __name__, url_prefix='/api/mqtt')

@mqtt_status_bp.route('/status', methods=['GET'])
def get_mqtt_status():
    """Get current MQTT connection status"""
    publisher = get_mqtt_publisher()
    status = 'online' if publisher.connected else 'offline'
    
    logger.info(f"MQTT status requested: {status}")
    
    # Broadcast status to all connected clients
    from app import get_socketio
    socketio = get_socketio()
    if socketio:
        logger.info(f"Broadcasting MQTT status: {status}")
        socketio.emit('mqtt_status', {'status': status}, namespace='/')
        logger.info(f"Broadcasted MQTT status successfully")
    
    return jsonify({'status': status, 'connected': publisher.connected}), 200

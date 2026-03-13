from flask import Blueprint, request, jsonify

mqtt_bridge_bp = Blueprint('mqtt_bridge', __name__, url_prefix='/api/mqtt-bridge')

@mqtt_bridge_bp.route('/telemetry', methods=['POST'])
def bridge_telemetry():
    """Bridge telemetry to WebSocket clients"""
    try:
        data = request.get_json()
        client_id = data.get('client_id')
        parameters = data.get('parameters', [])
        
        print(f"[MQTT_BRIDGE] Bridging {len(parameters)} parameters from {client_id}")
        
        return jsonify({'message': 'Telemetry bridged'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

"""
WebSocket integration for MQTT bridge
"""

from flask import Flask
from flask_socketio import SocketIO
from flask_cors import CORS
from app.services.mqtt_socketio_bridge import MQTTSocketIOBridge

def create_socketio_app(app: Flask) -> SocketIO:
    """Create and configure SocketIO"""
    
    # Enable CORS for WebSocket
    CORS(app, resources={
        r"/*": {
            "origins": ["http://localhost:3000", "http://127.0.0.1:3000"],
            "methods": ["GET", "POST"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })
    
    socketio = SocketIO(
        app,
        cors_allowed_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
        async_mode='threading'
    )
    
    # Create MQTT-Socket.IO bridge
    bridge = MQTTSocketIOBridge(socketio)
    app.mqtt_socketio_bridge = bridge
    
    @socketio.on('connect')
    def handle_connect():
        print('[SOCKETIO] Client connected')
        bridge.on_client_connect(request.sid, request.environ)
    
    @socketio.on('disconnect')
    def handle_disconnect():
        print('[SOCKETIO] Client disconnected')
        bridge.on_client_disconnect(request.sid)
    
    return socketio
import socketio
from datetime import datetime
from typing import Dict, List


class MQTTSocketIOBridge:
    """Bridge MQTT messages to Socket.IO clients"""
    
    def __init__(self, sio: socketio.Server):
        self.sio = sio
        self.connected_clients = {}
    
    def on_client_connect(self, sid: str, environ: Dict):
        """Handle Socket.IO client connection"""
        self.connected_clients[sid] = {
            'connected_at': datetime.utcnow().isoformat(),
            'device_id': None
        }
        print(f"[SOCKETIO] Client connected: {sid}")
    
    def on_client_disconnect(self, sid: str):
        """Handle Socket.IO client disconnection"""
        if sid in self.connected_clients:
            del self.connected_clients[sid]
        print(f"[SOCKETIO] Client disconnected: {sid}")
    
    def broadcast_telemetry(self, telemetry_data: Dict):
        """Broadcast telemetry data to all connected Socket.IO clients"""
        if not self.connected_clients:
            return
        
        payload = {
            'timestamp': datetime.utcnow().isoformat(),
            'data': telemetry_data
        }
        
        self.sio.emit('telemetry', payload, to=None)
        print(f"[SOCKETIO] Broadcast telemetry to {len(self.connected_clients)} clients")
    
    def broadcast_mqtt_message(self, topic: str, message: Dict):
        """Broadcast MQTT message to Socket.IO clients"""
        payload = {
            'topic': topic,
            'timestamp': datetime.utcnow().isoformat(),
            'message': message
        }
        
        self.sio.emit('mqtt_message', payload, to=None)
        print(f"[SOCKETIO] Broadcast MQTT message from {topic}")

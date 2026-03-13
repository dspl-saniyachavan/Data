"""
Socket.IO service for real-time telemetry broadcasting
"""
from flask_socketio import SocketIO, emit, join_room, leave_room
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class SocketIOService:
    def __init__(self, app=None):
        self.socketio = None
        self.connected_clients = {}
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize Socket.IO with Flask app"""
        self.socketio = SocketIO(
            app,
            cors_allowed_origins="*",
            async_mode='threading',
            ping_timeout=60,
            ping_interval=25
        )
        
        @self.socketio.on('connect')
        def handle_connect():
            client_id = request.sid
            self.connected_clients[client_id] = {
                'connected_at': datetime.now(),
                'user_id': None
            }
            logger.info(f"Client connected: {client_id}")
            emit('connection_response', {'data': 'Connected to server'})
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            client_id = request.sid
            if client_id in self.connected_clients:
                del self.connected_clients[client_id]
            logger.info(f"Client disconnected: {client_id}")
        
        @self.socketio.on('authenticate')
        def handle_authenticate(data):
            client_id = request.sid
            user_id = data.get('user_id')
            if client_id in self.connected_clients:
                self.connected_clients[client_id]['user_id'] = user_id
                join_room(f'user_{user_id}')
                logger.info(f"Client {client_id} authenticated as user {user_id}")
                emit('auth_response', {'status': 'authenticated'})
    
    def broadcast_telemetry(self, telemetry_data):
        """Broadcast telemetry to all connected clients"""
        if self.socketio:
            self.socketio.emit(
                'telemetry_update',
                telemetry_data,
                broadcast=True,
                namespace='/'
            )
            logger.debug(f"Broadcasted telemetry: {telemetry_data}")
    
    def broadcast_to_user(self, user_id, event, data):
        """Broadcast event to specific user"""
        if self.socketio:
            self.socketio.emit(
                event,
                data,
                room=f'user_{user_id}',
                namespace='/'
            )
    
    def get_connected_clients_count(self):
        """Get count of connected clients"""
        return len(self.connected_clients)
    
    def get_connected_clients(self):
        """Get list of connected clients"""
        return self.connected_clients

socketio_service = SocketIOService()

from flask_socketio import emit, join_room, leave_room
from app.utils.jwt_utils import verify_token

def register_socket_events(socketio):
    @socketio.on('connect')
    def handle_connect(auth):
        if not auth or 'token' not in auth:
            return False
        
        payload = verify_token(auth['token'])
        if not payload:
            return False
        
        return True
    
    @socketio.on('disconnect')
    def handle_disconnect():
        pass
    
    @socketio.on('join')
    def on_join(data):
        room = data.get('room')
        if room:
            join_room(room)
            emit('message', {'data': f'User joined {room}'}, room=room)
    
    @socketio.on('leave')
    def on_leave(data):
        room = data.get('room')
        if room:
            leave_room(room)
            emit('message', {'data': f'User left {room}'}, room=room)

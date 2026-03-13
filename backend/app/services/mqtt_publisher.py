"""
MQTT Publisher for user, role, and permission changes
"""

import json
import paho.mqtt.client as mqtt
from datetime import datetime
from config.config import Config


class MQTTPublisher:
    """Publish user, role, and permission changes to MQTT topics"""
    
    def __init__(self):
        self.client = None
        self.connected = False
        self.socketio = None
    
    def initialize(self):
        """Initialize MQTT connection"""
        if self.client is None:
            self._connect()
    
    def set_socketio(self, socketio):
        """Set Socket.IO instance for broadcasting status"""
        self.socketio = socketio
    
    def _connect(self):
        """Connect to MQTT broker"""
        try:
            try:
                # Try new API (paho-mqtt 2.0+)
                self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
            except AttributeError:
                # Fall back to old API (paho-mqtt 1.x)
                self.client = mqtt.Client()
            
            if Config.MQTT_USE_TLS:
                self.client.tls_set(ca_certs=Config.MQTT_CA_CERTS)
                self.client.tls_insecure = False
            
            self.client.on_connect = self._on_connect
            self.client.on_disconnect = self._on_disconnect
            
            self.client.connect(Config.MQTT_BROKER, Config.MQTT_PORT, Config.MQTT_KEEPALIVE)
            self.client.loop_start()
            print(f"[MQTT_PUB] Connecting to {Config.MQTT_BROKER}:{Config.MQTT_PORT}")
        except Exception as e:
            print(f"[MQTT_PUB] Connection error: {e}")
    
    def _on_connect(self, client, userdata, flags, rc, properties=None):
        """Callback on connect"""
        if rc == 0:
            self.connected = True
            print(f"[MQTT_PUB] Connected to broker")
            if self.socketio:
                try:
                    print(f"[MQTT_PUB] Emitting online status to all clients")
                    self.socketio.emit('mqtt_status', {'status': 'online'}, namespace='/')
                    print(f"[MQTT_PUB] Emitted online status successfully")
                    
                    # Trigger auto-flush of buffered data
                    print(f"[MQTT_PUB] Triggering auto-flush of buffered data")
                    self._auto_flush_buffer()
                except Exception as e:
                    print(f"[MQTT_PUB] Error emitting status: {e}")
                    import traceback
                    traceback.print_exc()
            else:
                print(f"[MQTT_PUB] SocketIO not set, cannot emit status")
        else:
            self.connected = False
            print(f"[MQTT_PUB] Connection failed (rc={rc})")
            if self.socketio:
                try:
                    self.socketio.emit('mqtt_status', {'status': 'offline'}, namespace='/')
                except Exception as e:
                    print(f"[MQTT_PUB] Error emitting status: {e}")
    
    def _on_disconnect(self, client, userdata, flags, rc, properties=None):
        """Callback on disconnect"""
        self.connected = False
        print(f"[MQTT_PUB] Disconnected (rc={rc})")
        if self.socketio:
            try:
                print(f"[MQTT_PUB] Emitting offline status to all clients")
                self.socketio.emit('mqtt_status', {'status': 'offline'}, namespace='/')
                print(f"[MQTT_PUB] Emitted offline status successfully")
            except Exception as e:
                print(f"[MQTT_PUB] Error emitting status: {e}")
                import traceback
                traceback.print_exc()
        else:
            print(f"[MQTT_PUB] SocketIO not set, cannot emit status")
    
    def publish_user_created(self, user_data: dict):
        """Publish user creation event"""
        payload = {
            'type': 'user_created',
            'timestamp': datetime.now().isoformat(),
            'user': {
                'id': user_data.get('id'),
                'email': user_data.get('email'),
                'name': user_data.get('name'),
                'role': user_data.get('role'),
                'is_active': user_data.get('is_active', True)
            }
        }
        self._publish('precisionpulse/sync/users/created', payload)
    
    def publish_user_updated(self, user_data: dict):
        """Publish user update event"""
        payload = {
            'type': 'user_updated',
            'timestamp': datetime.now().isoformat(),
            'user': {
                'id': user_data.get('id'),
                'email': user_data.get('email'),
                'name': user_data.get('name'),
                'role': user_data.get('role'),
                'is_active': user_data.get('is_active', True)
            }
        }
        self._publish('precisionpulse/sync/users/updated', payload)
    
    def publish_user_deleted(self, user_id: int, email: str):
        """Publish user deletion event"""
        payload = {
            'type': 'user_deleted',
            'timestamp': datetime.now().isoformat(),
            'user': {
                'id': user_id,
                'email': email
            }
        }
        self._publish('precisionpulse/sync/users/deleted', payload)
    
    def publish_role_changed(self, user_id: int, email: str, old_role: str, new_role: str):
        """Publish role change event"""
        payload = {
            'type': 'role_changed',
            'timestamp': datetime.now().isoformat(),
            'user_id': user_id,
            'email': email,
            'old_role': old_role,
            'new_role': new_role
        }
        self._publish('precisionpulse/sync/roles/changed', payload)
    
    def publish_permission_changed(self, role: str, permissions: list):
        """Publish permission change event"""
        payload = {
            'type': 'permission_changed',
            'timestamp': datetime.now().isoformat(),
            'role': role,
            'permissions': permissions
        }
        self._publish('precisionpulse/sync/permissions/changed', payload)
    
    def _publish(self, topic: str, payload: dict):
        """Publish message to MQTT topic"""
        if not self.connected:
            print(f"[MQTT_PUB] Not connected, skipping publish to {topic}")
            return False
        
        try:
            result = self.client.publish(topic, json.dumps(payload), qos=1)
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                print(f"[MQTT_PUB] Published to {topic}")
                return True
            else:
                print(f"[MQTT_PUB] Publish failed (rc={result.rc})")
                return False
        except Exception as e:
            print(f"[MQTT_PUB] Error publishing to {topic}: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from broker"""
        if self.client:
            self.client.loop_stop()
            self.client.disconnect()
    
    def _auto_flush_buffer(self):
        """Auto-flush buffered data when MQTT reconnects"""
        import threading
        import time
        
        def flush_after_delay():
            time.sleep(2)  # Wait 2 seconds after reconnection
            try:
                import requests
                response = requests.delete('http://localhost:5000/api/buffer/telemetry/flush', timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    count = data.get('count', 0)
                    print(f"[MQTT_PUB] Auto-flushed {count} buffered records")
                else:
                    print(f"[MQTT_PUB] Auto-flush failed: {response.status_code}")
            except Exception as e:
                print(f"[MQTT_PUB] Auto-flush error: {e}")
        
        flush_thread = threading.Thread(target=flush_after_delay, daemon=True)
        flush_thread.start()


# Global instance
mqtt_publisher = None


def get_mqtt_publisher():
    """Get or create MQTT publisher instance"""
    global mqtt_publisher
    if mqtt_publisher is None:
        mqtt_publisher = MQTTPublisher()
        mqtt_publisher.initialize()
    return mqtt_publisher

def init_mqtt_publisher(socketio):
    """Initialize MQTT publisher with Socket.IO instance"""
    global mqtt_publisher
    if mqtt_publisher is None:
        mqtt_publisher = MQTTPublisher()
    mqtt_publisher.set_socketio(socketio)
    mqtt_publisher.initialize()
    return mqtt_publisher

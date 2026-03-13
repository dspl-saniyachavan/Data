"""
MQTT Subscriber for backend to receive telemetry and sync messages
"""

import paho.mqtt.client as mqtt
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class MQTTSubscriber:
    """MQTT subscriber for backend"""
    
    def __init__(self, broker='localhost', port=1883, use_tls=False, ca_certs=None, app=None):
        self.broker = broker
        self.port = port
        self.use_tls = use_tls
        self.ca_certs = ca_certs
        self.app = app
        try:
            self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        except AttributeError:
            self.client = mqtt.Client()
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message
        self.connected = False
        self.socketio = None
    
    def set_socketio(self, socketio):
        """Set Socket.IO instance for broadcasting status"""
        self.socketio = socketio
    
    def set_app(self, app):
        """Set Flask app for database operations"""
        self.app = app
    
    def connect(self):
        """Connect to MQTT broker"""
        try:
            if self.use_tls:
                import ssl
                self.client.tls_set(
                    ca_certs=self.ca_certs,
                    certfile=None,
                    keyfile=None,
                    cert_reqs=ssl.CERT_NONE,
                    tls_version=ssl.PROTOCOL_TLSv1_2
                )
                self.client.tls_insecure_set(True)
            
            logger.info(f"Connecting to MQTT broker at {self.broker}:{self.port} (TLS: {self.use_tls})")
            self.client.connect(self.broker, self.port, 60)
            self.client.loop_forever()
        except Exception as e:
            logger.error(f"MQTT connection error: {e}")
            import traceback
            traceback.print_exc()
    
    def _on_connect(self, client, userdata, flags, rc, properties=None):
        """Handle connection"""
        if rc == 0:
            self.connected = True
            logger.info("MQTT subscriber connected")
            client.subscribe("precisionpulse/+/telemetry")
            client.subscribe("telemetry/stream")
            client.subscribe("precisionpulse/sync/#")
            client.subscribe("precisionpulse/config/update")
            client.subscribe("precisionpulse/config/bulk-update")
            if self.socketio:
                try:
                    logger.info("Emitting MQTT online status to all clients")
                    self.socketio.emit('mqtt_status', {'status': 'online'}, namespace='/')
                    self.socketio.emit('mqtt_connected', {}, namespace='/')
                    logger.info("Emitted MQTT online status successfully")
                except Exception as e:
                    logger.error(f"Error emitting status: {e}")
                    import traceback
                    traceback.print_exc()
            else:
                logger.warning("SocketIO not set, cannot emit status")
        else:
            self.connected = False
            logger.error(f"MQTT connection failed: {rc}")
            if self.socketio:
                try:
                    self.socketio.emit('mqtt_status', {'status': 'offline'}, namespace='/')
                    self.socketio.emit('mqtt_disconnected', {}, namespace='/')
                except Exception as e:
                    logger.error(f"Error emitting status: {e}")
    
    def _on_disconnect(self, client, userdata, flags, rc, properties=None):
        """Handle disconnection"""
        self.connected = False
        logger.warning(f"MQTT subscriber disconnected (rc={rc})")
        if self.socketio:
            try:
                logger.info("Emitting MQTT offline status to all clients")
                self.socketio.emit('mqtt_status', {'status': 'offline'}, namespace='/')
                self.socketio.emit('mqtt_disconnected', {}, namespace='/')
                logger.info("Emitted MQTT offline status successfully")
            except Exception as e:
                logger.error(f"Error emitting status: {e}")
                import traceback
                traceback.print_exc()
        else:
            logger.warning("SocketIO not set, cannot emit status")
    
    def _on_message(self, client, userdata, msg):
        """Handle incoming messages"""
        try:
            topic = msg.topic
            payload = json.loads(msg.payload.decode())
            logger.info(f"MQTT message received on {topic}")
            
            if "telemetry" in topic:
                self._handle_telemetry(payload)
            elif "sync" in topic:
                self._handle_sync(payload)
            elif "config" in topic:
                self._handle_config(payload)
        except Exception as e:
            logger.error(f"Message handling error: {e}")
            import traceback
            traceback.print_exc()
    
    def _handle_telemetry(self, payload):
        """Handle telemetry messages"""
        try:
            client_id = payload.get('client_id')
            timestamp_str = payload.get('timestamp')
            parameters = payload.get('parameters', [])
            
            logger.info(f"Telemetry from {client_id}: {len(parameters)} parameters")
            
            # Parse timestamp
            try:
                timestamp = datetime.fromisoformat(timestamp_str) if timestamp_str else datetime.utcnow()
            except:
                timestamp = datetime.utcnow()
            
            # NOTE: Database storage is handled by /api/telemetry/stream endpoint
            # MQTT subscriber only broadcasts to Socket.IO to avoid duplication
            
            # Broadcast via Socket.IO to all connected clients
            if self.socketio:
                try:
                    broadcast_data = {
                        'client_id': client_id,
                        'timestamp': timestamp.isoformat(),
                        'data': {'parameters': parameters}
                    }
                    
                    # Emit to all clients
                    self.socketio.emit('telemetry', broadcast_data, namespace='/')
                    self.socketio.emit('parameter_stream_update', broadcast_data, namespace='/')
                    
                    logger.info(f"Broadcasted telemetry to all clients via Socket.IO")
                except Exception as e:
                    logger.error(f"Error broadcasting telemetry: {e}")
                    import traceback
                    traceback.print_exc()
            else:
                logger.warning("SocketIO not set, cannot broadcast telemetry")
        
        except Exception as e:
            logger.error(f"Error handling telemetry: {e}")
            import traceback
            traceback.print_exc()
    
    def _handle_sync(self, payload):
        """Handle sync messages"""
        try:
            action = payload.get('action')
            logger.info(f"Sync message: {action}")
        except Exception as e:
            logger.error(f"Error handling sync: {e}")
    
    def _handle_config(self, payload):
        """Handle configuration update messages"""
        try:
            action = payload.get('action')
            logger.info(f"Config update received: {action}")
        except Exception as e:
            logger.error(f"Error handling config: {e}")

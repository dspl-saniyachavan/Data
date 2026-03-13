"""
MQTT Service for real-time bidirectional communication
"""

import json
from PySide6.QtCore import QObject, Signal
from src.core.config import Config
from src.services.mqtt_interface import IMQTTClient
from datetime import datetime


class MQTTService(QObject):
    """Service for MQTT communication with loose coupling"""
    
    # Signals
    connected = Signal()
    disconnected = Signal()
    message_received = Signal(str, dict)
    parameter_update_received = Signal(str, float)
    config_update_received = Signal(dict)
    
    def __init__(self, device_id: str, mqtt_client: IMQTTClient):
        super().__init__()
        self.device_id = device_id
        self.client = mqtt_client
        self.is_connected = False
        
        # Setup callbacks
        self.client.set_on_connect_callback(self._on_connect)
        self.client.set_on_disconnect_callback(self._on_disconnect)
        self.client.set_on_message_callback(self._on_message)
        
        # Device-specific topics
        self.telemetry_topic = f"precisionpulse/{device_id}/telemetry"
        self.command_topic = f"precisionpulse/{device_id}/command"
        self.heartbeat_topic = f"precisionpulse/{device_id}/heartbeat"
    
    def connect(self):
        """Connect to MQTT broker"""
        try:
            print(f"[MQTT] Connecting to {Config.MQTT_BROKER}:{Config.MQTT_PORT}...")
            success = self.client.connect(Config.MQTT_BROKER, Config.MQTT_PORT, Config.MQTT_KEEPALIVE)
            if success:
                self.client.loop_start()
                print(f"[MQTT] Connection initiated successfully")
            else:
                print(f"[MQTT] Connection failed with code: {success}")
            return success
        except Exception as e:
            print(f"[MQTT] Connection error: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from MQTT broker"""
        self.client.loop_stop()
        self.client.disconnect()
    
    def _on_connect(self, client, userdata, flags, rc):
        """Callback when connected to broker"""
        if rc == 0:
            print(f"[MQTT] Connected to broker at {Config.MQTT_BROKER}:{Config.MQTT_PORT}")
            self.is_connected = True
            self.connected.emit()
            
            # Subscribe to device-specific command topic
            self.client.subscribe(self.command_topic)
            self.client.subscribe(f"{Config.MQTT_TOPIC_COMMANDS}/config/update")
            
            # Subscribe to ALL telemetry and heartbeat topics
            self.client.subscribe("precisionpulse/+/telemetry")
            self.client.subscribe("precisionpulse/+/heartbeat")
            
            # Subscribe to sync topics for parameter updates
            self.client.subscribe("precisionpulse/sync/parameters")
            self.client.subscribe("precisionpulse/sync/users/#")
            print(f"[MQTT] Subscribed to sync topics")
            
            # Send heartbeat
            self._send_heartbeat()
        else:
            print(f"[MQTT] Connection failed (code: {rc})")
    
    def _on_disconnect(self, client, userdata, rc):
        """Callback when disconnected from broker"""
        print(f"[MQTT] Disconnected from broker")
        self.is_connected = False
        self.disconnected.emit()
    
    def _on_message(self, client, userdata, msg):
        """Callback when message received"""
        try:
            topic = msg.topic
            payload = json.loads(msg.payload.decode())
            print(f"[MQTT] Received message on topic: {topic}")
            
            # Handle sync messages
            if "sync" in topic:
                self.message_received.emit(topic, payload)
            
            # Handle telemetry from other clients
            elif "telemetry" in topic and topic != self.telemetry_topic:
                # Emit parameter updates so admin dashboard shows remote data
                if 'parameters' in payload:
                    for param in payload['parameters']:
                        self.parameter_update_received.emit(param['id'], param['value'])
            
            # Handle parameter updates
            elif 'parameters/update' in topic or payload.get('type') == 'parameter_update':
                param_id = payload.get('parameter_id')
                value = payload.get('value')
                if param_id and value is not None:
                    self.parameter_update_received.emit(param_id, float(value))
            
            # Handle configuration updates
            elif 'config/update' in topic or payload.get('type') == 'config_update':
                config_data = payload.get('config', {})
                if config_data:
                    self.config_update_received.emit(config_data)
                    if payload.get('command_id'):
                        self.acknowledge_command(payload['command_id'])
            
        except Exception as e:
            print(f"[MQTT] Message handling error: {e}")
    
    def publish_telemetry(self, parameters: list) -> bool:
        """Publish telemetry data to backend API"""
        if not parameters:
            return False
        
        try:
            import requests
            from src.core.config import Config
            
            payload = {
                'client_id': self.device_id,
                'timestamp': datetime.utcnow().isoformat(),
                'parameters': parameters
            }
            
            # Send to backend HTTP API
            try:
                response = requests.post(
                    f"{Config.BACKEND_URL}/api/telemetry/stream",
                    json=payload,
                    timeout=5
                )
                if response.status_code == 200:
                    print(f"[MQTT] Telemetry sent to backend API")
                else:
                    print(f"[MQTT] Backend API error: {response.status_code}")
            except Exception as e:
                print(f"[MQTT] Backend API error: {e}")
            
            # Also publish to MQTT for real-time subscribers
            if self.is_connected:
                success = self.client.publish(
                    self.telemetry_topic,
                    json.dumps(payload),
                    qos=1
                )
                if success:
                    print(f"[MQTT] Telemetry published to MQTT broker")
                return success
            
            return True
        except Exception as e:
            print(f"[MQTT] Publish error: {e}")
            return False
    
    def publish_buffered_data(self, buffered_data: list) -> bool:
        """Publish buffered historical data"""
        if not self.is_connected:
            return False
        
        try:
            payload = {
                'device_id': self.device_id,
                'type': 'buffered_sync',
                'data': buffered_data
            }
            
            return self.client.publish(
                f"{Config.MQTT_TOPIC_SYNC}/buffered",
                json.dumps(payload),
                qos=2
            )
        except Exception as e:
            return False
    
    def acknowledge_command(self, command_id: str) -> bool:
        """Acknowledge received command"""
        if not self.is_connected:
            return False
        
        try:
            payload = {
                'device_id': self.device_id,
                'command_id': command_id,
                'status': 'acknowledged',
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }
            
            return self.client.publish(
                f"{Config.MQTT_TOPIC_COMMANDS}/ack",
                json.dumps(payload),
                qos=1
            )
        except Exception as e:
            return False
    
    def _send_heartbeat(self):
        """Send heartbeat to indicate device is online"""
        if not self.is_connected:
            return
        
        try:
            payload = {
                'client_id': self.device_id,
                'status': 'online',
                'timestamp': datetime.utcnow().isoformat()
            }
            
            self.client.publish(
                self.heartbeat_topic,
                json.dumps(payload),
                qos=1
            )
        except Exception as e:
            pass

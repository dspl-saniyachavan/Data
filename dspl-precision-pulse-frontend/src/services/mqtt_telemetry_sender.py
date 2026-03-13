import json
from datetime import datetime
from PySide6.QtCore import QObject, QTimer, Signal
from src.core.config import Config


class MQTTTelemetrySender(QObject):
    """Send telemetry via MQTT every 2 seconds with timestamps"""
    
    telemetry_sent = Signal(str)  # timestamp
    
    def __init__(self, mqtt_service, telemetry_service):
        super().__init__()
        self.mqtt_service = mqtt_service
        self.telemetry_service = telemetry_service
        self.timer = QTimer()
        self.timer.timeout.connect(self._send_mqtt_telemetry)
    
    def start(self, interval: int = 2):
        """Start sending MQTT telemetry every interval seconds"""
        self.timer.start(interval * 1000)
        print(f"[MQTT_SENDER] Started sending telemetry every {interval}s")
    
    def stop(self):
        """Stop sending MQTT telemetry"""
        self.timer.stop()
        print(f"[MQTT_SENDER] Stopped")
    
    def _send_mqtt_telemetry(self):
        """Send telemetry via MQTT with timestamp"""
        if not self.mqtt_service.is_connected:
            return
        
        parameters = self.telemetry_service.get_parameters()
        if not parameters:
            return
        
        timestamp = datetime.utcnow().isoformat()
        
        payload = {
            'client_id': self.mqtt_service.device_id,
            'timestamp': timestamp,
            'parameters': [
                {
                    'id': p['id'],
                    'name': p['name'],
                    'value': p['value'],
                    'unit': p['unit']
                }
                for p in parameters.values()
            ]
        }
        
        try:
            success = self.mqtt_service.client.publish(
                self.mqtt_service.telemetry_topic,
                json.dumps(payload),
                qos=1
            )
            if success:
                print(f"[MQTT_SENDER] Published telemetry at {timestamp}")
                self.telemetry_sent.emit(timestamp)
        except Exception as e:
            print(f"[MQTT_SENDER] Error: {e}")

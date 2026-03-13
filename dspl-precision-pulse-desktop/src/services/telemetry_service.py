"""
Telemetry Service for parameter management and synchronization
"""

import random
from typing import Dict, List
from PySide6.QtCore import QObject, QTimer, Signal
from src.core.config import Config, ConfigManager


class TelemetryService(QObject):
    """Service for managing telemetry data and synchronization"""
    
    # Signals
    parameters_updated = Signal()
    parameter_changed = Signal(str, float)
    connection_status_changed = Signal(bool)
    buffered_data_synced = Signal(int)
    
    def __init__(self, mqtt_service, database_manager, parameter_sync_service=None):
        super().__init__()
        self.mqtt_service = mqtt_service
        self.db = database_manager
        self.parameter_sync_service = parameter_sync_service
        self.config_manager = ConfigManager()
        self.parameters = self._initialize_parameters()
        self.previous_values = {}
        self.last_print_time = 0
        self.push_timer = QTimer()
        self.heartbeat_timer = QTimer()
        self.refresh_timer = QTimer()
        self.flush_timer = QTimer()
        self.resume_timer = QTimer()
        self.is_streaming = False
        self.is_connected = False
        self.is_flushing = False
        
        # Connect MQTT signals
        self.mqtt_service.connected.connect(self._on_mqtt_connected)
        self.mqtt_service.disconnected.connect(self._on_mqtt_disconnected)
        self.mqtt_service.parameter_update_received.connect(self._on_parameter_update)
        self.mqtt_service.config_update_received.connect(self._on_config_update)
        
        # Connect config manager signals
        self.config_manager.config_updated.connect(self._apply_config_update)
        
        # Connect parameter sync service if provided
        if self.parameter_sync_service:
            self.parameter_sync_service.parameters_fetched.connect(self._on_parameters_fetched)
        
        self.refresh_timer.timeout.connect(self._refresh_telemetry_from_backend)
        self.flush_timer.timeout.connect(self._flush_buffered_data)
        self.resume_timer.timeout.connect(self._resume_streaming)
        
        # Start flush timer immediately
        self.flush_timer.start(5000)
        
    def _initialize_parameters(self) -> Dict:
        """Initialize parameters from database or parameter sync service"""
        if self.parameter_sync_service:
            synced_params = self.parameter_sync_service.get_enabled_parameters()
            if synced_params:
                print(f"[INIT] Got {len(synced_params)} parameters from sync service")
                return self._build_parameters_dict(synced_params)
        
        enabled_params = self.db.get_enabled_parameters()
        if enabled_params:
            print(f"[INIT] Got {len(enabled_params)} parameters from database")
            return self._build_parameters_dict(enabled_params)
        
        print(f"[INIT] No parameters found")
        return {}
    
    def _build_parameters_dict(self, params: List[Dict]) -> Dict:
        """Build parameters dictionary from list"""
        parameters = {}
        colors = ["#64a8fc", "#7f58f5", '#c084fc', '#f472b6', '#fb923c', '#34d399', '#fbbf24', '#f87171']
        
        for i, param in enumerate(params):
            param_id = param.get('id') or param.get('parameter_id')
            initial_value = param.get('value', (param.get('max', 100) + param.get('min', 0)) / 2)
            parameters[param_id] = {
                'id': param_id,
                'name': param.get('name', 'Unknown'),
                'value': initial_value,
                'unit': param.get('unit', ''),
                'min': param.get('min', 0),
                'max': param.get('max', 100),
                'color': colors[i % len(colors)]
            }
        
        return parameters
    
    def start_streaming(self, interval: int = 2):
        """Start streaming telemetry data"""
        print(f"[TELEMETRY] Starting streaming (interval: {interval}s)")
        self.is_streaming = True
        
        if self.parameter_sync_service:
            self.parameter_sync_service._sync_parameters()
            self.parameter_sync_service.start_sync(30)
        
        if not self.mqtt_service.client.is_connected():
            print(f"[TELEMETRY] Connecting to MQTT broker...")
            self.mqtt_service.connect()
        
        if not self.parameters:
            self.refresh_parameters()
        
        # Start push timer only - don't call _push_data immediately to avoid duplicate
        self.push_timer.timeout.connect(self._generate_and_push)
        self.push_timer.start(interval * 1000)
        
        self.heartbeat_timer.timeout.connect(self._send_heartbeat)
        self.heartbeat_timer.start(Config.HEARTBEAT_INTERVAL * 1000)
        
        # Don't start refresh_timer when streaming - it's only for non-streaming mode
        
        print(f"[TELEMETRY] Streaming started with {len(self.parameters)} parameters")
        
    def stop_streaming(self):
        """Stop streaming telemetry data"""
        self.is_streaming = False
        self.push_timer.stop()
        self.heartbeat_timer.stop()
        self.refresh_timer.stop()
        
    def _generate_data(self):
        """Generate simulated sensor data"""
        import time
        current_time = time.time()
        
        for param_id, param in self.parameters.items():
            variation = (param['max'] - param['min']) * 0.05
            new_value = param['value'] + random.uniform(-variation, variation)
            new_value = max(param['min'], min(param['max'], new_value))
            param['value'] = round(new_value, 2)
        
        if current_time - self.last_print_time >= 3:
            param_values = [f"{p['name']}={p['value']}" for p in self.parameters.values()]
            print(f"[DATA] {', '.join(param_values)}")
            self.last_print_time = current_time
    
    def _generate_and_push(self):
        """Generate data and push immediately"""
        if self.is_flushing:
            return
        self._generate_data()
        self._push_data()
            
    def _push_data(self):
        """Push current parameter values to backend"""
        if not self.parameters or self.is_flushing:
            return
        
        # Stop pushing data if MQTT is disconnected
        if not self.mqtt_service.client.is_connected():
            print(f"[TELEMETRY] MQTT disconnected - stopping data push")
            return
        
        from datetime import datetime
        from .parameter_streaming_data import ParameterStreamingData, ParameterStreamingPayload
        
        current_timestamp = datetime.now().isoformat()
        
        streaming_params = [
            ParameterStreamingData.from_parameter(p, self.mqtt_service.device_id, current_timestamp)
            for p in self.parameters.values()
        ]
        
        payload_obj = ParameterStreamingPayload(
            client_id=self.mqtt_service.device_id,
            timestamp=current_timestamp,
            parameters=streaming_params
        )
        
        # Store parameter stream data locally
        try:
            for param in streaming_params:
                self.db.store_parameter_stream(
                    parameter_id=param.parameter_id,
                    value=param.value
                )
        except Exception as e:
            print(f"[TELEMETRY] Error storing parameter stream: {e}")
        
        self.parameters_updated.emit()
        
        try:
            import requests
            payload_dict = payload_obj.to_dict()
            
            requests.post(
                f"{Config.BACKEND_URL}/api/telemetry/stream",
                json=payload_dict,
                timeout=5
            )
            
            print(f"[TELEMETRY] Sent {len(streaming_params)} parameters")
            
        except Exception as e:
            print(f"[TELEMETRY] Error: {e}")
            # Buffer data on error
            for param in streaming_params:
                self.db.buffer_telemetry(
                    parameter_id=param.parameter_id,
                    value=param.value
                )
        
        if self.mqtt_service.client.is_connected():
            self.mqtt_service.publish_telemetry([p.to_dict() for p in streaming_params])

    
    def _on_mqtt_connected(self):
        """Handle MQTT connection established"""
        self.is_connected = True
        self.connection_status_changed.emit(True)
        print(f"[MQTT] Status: CONNECTED - Starting flush")
        
        # Pause streaming to flush buffered data first
        if self.is_streaming:
            self.is_flushing = True
            self.push_timer.stop()
            print(f"[FLUSH] Paused live streaming")
        
        # Flush buffered data immediately
        self._flush_buffered_data()
        
        # Refresh parameters
        self.refresh_parameters()
        if self.parameter_sync_service:
            self.parameter_sync_service._sync_parameters()
        
        if self.parameters:
            self._generate_data()
        
        # Resume streaming after 2 seconds
        if self.is_streaming:
            self.resume_timer.start(2000)
    
    def _resume_streaming(self):
        """Resume live streaming after buffered data flush"""
        self.resume_timer.stop()
        if self.is_streaming:
            self.is_flushing = False
            self.push_timer.start(3000)
            print(f"[FLUSH] Resumed live streaming")
    
    def _on_mqtt_disconnected(self):
        """Handle MQTT disconnection"""
        self.is_connected = False
        self.connection_status_changed.emit(False)
        print(f"[MQTT] Status: DISCONNECTED - Stopping data generation")
        
        # Stop data generation and push timers
        if self.is_streaming:
            self.push_timer.stop()
            self.heartbeat_timer.stop()
            print(f"[TELEMETRY] Paused data generation and chart updates")
    
    def _flush_buffered_data(self):
        """Flush buffered data to MQTT broker"""
        try:
            buffered = self.db.get_buffered_data()
            if not buffered:
                print(f"[FLUSH] No buffered data to flush")
                return
            
            print(f"[FLUSH] Flushing {len(buffered)} buffered records")
            
            success = self.mqtt_service.publish_buffered_data(buffered)
            
            if success:
                buffer_ids = [r['id'] for r in buffered]
                self.db.mark_data_synced(buffer_ids)
                self.db.clear_synced_data()
                self._delete_buffered_data(buffer_ids)
                print(f"[FLUSH] Successfully flushed {len(buffered)} records")
                self.buffered_data_synced.emit(len(buffered))
            else:
                print(f"[FLUSH] Failed to publish - will retry")
        except Exception as e:
            print(f"[FLUSH] Error: {e}")
    
    def _delete_buffered_data(self, buffer_ids: List[int]):
        """Delete buffered data after successful sync"""
        try:
            self.db.delete_buffered_data(buffer_ids)
            print(f"[FLUSH] Deleted {len(buffer_ids)} buffered records from local_buffer table")
        except Exception as e:
            print(f"[FLUSH] Error deleting buffered data: {e}")
    
    def _on_parameter_update(self, param_id: str, new_value: float):
        """Handle parameter update from web"""
        if param_id in self.parameters:
            self.parameters[param_id]['value'] = float(new_value)
            self.parameter_changed.emit(param_id, float(new_value))
    
    def _send_heartbeat(self):
        """Send heartbeat to indicate device is alive"""
        if self.mqtt_service.client.is_connected:
            self.mqtt_service._send_heartbeat()
                        
    def refresh_parameters(self):
        """Refresh parameters from database or API"""
        old_params = set(self.parameters.keys())
        
        if self.parameter_sync_service:
            self.parameter_sync_service._sync_parameters()
            synced_params = self.parameter_sync_service.get_enabled_parameters()
            if synced_params:
                self.parameters = self._build_parameters_dict(synced_params)
            else:
                self.parameters = self._initialize_parameters()
        else:
            self.parameters = self._initialize_parameters()
        
        new_params = set(self.parameters.keys())
        
        added = new_params - old_params
        for param_id in added:
            print(f"[PARAM] Added: {self.parameters[param_id]['name']}")
        
        removed = old_params - new_params
        for param_id in removed:
            print(f"[PARAM] Removed: {param_id}")
        
        self.parameters_updated.emit()
        print(f"[PARAM] Refreshed {len(self.parameters)} parameters")
    
    def get_parameters(self) -> Dict:
        """Get current parameters"""
        return self.parameters
    
    def get_parameter(self, param_id: str) -> Dict:
        """Get specific parameter"""
        return self.parameters.get(param_id)
    
    def set_parameter_value(self, param_id: str, value: float):
        """Manually set parameter value"""
        if param_id in self.parameters:
            self.parameters[param_id]['value'] = value
            self.parameter_changed.emit(param_id, value)
    
    def _on_config_update(self, config_data: dict):
        """Handle configuration update from remote command"""
        self.config_manager.update_config(config_data)
    
    def _on_parameters_fetched(self, parameters: list):
        """Handle parameters fetched from backend API"""
        if parameters:
            print(f"[PARAM_SYNC] Updating parameters: {len(parameters)} parameters")
            self.parameters = self._build_parameters_dict(parameters)
            self.parameters_updated.emit()
    
    def _apply_config_update(self, key: str, value: str):
        """Apply configuration update to running service"""
        if key == 'TELEMETRY_INTERVAL':
            new_interval = int(value)
            if self.is_streaming:
                self.push_timer.stop()
                self.push_timer.start(new_interval * 1000)
        
        elif key == 'HEARTBEAT_INTERVAL':
            new_interval = int(value)
            if self.is_streaming:
                self.heartbeat_timer.stop()
                self.heartbeat_timer.start(new_interval * 1000)
    
    def _refresh_telemetry_from_backend(self):
        """Fetch latest telemetry data from backend API"""
        if self.is_streaming:
            return
        
        try:
            import requests
            response = requests.get(
                f"{Config.BACKEND_URL}/api/telemetry/latest",
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json().get('data', {}).get('parameters', [])
                for item in data:
                    param_id = item.get('id') or item.get('parameter_id')
                    if param_id in self.parameters:
                        self.parameters[param_id]['value'] = float(item.get('value', 0))
                self.parameters_updated.emit()
        except requests.exceptions.RequestException:
            pass

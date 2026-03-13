"""
Parameter synchronization service for desktop application
"""

from typing import List, Dict
from PySide6.QtCore import QObject, Signal, QTimer
import requests


class ParameterSyncService(QObject):
    """Service for syncing parameters from backend"""
    
    parameters_fetched = Signal(list)
    parameter_updated = Signal(dict)
    sync_error = Signal(str)
    
    def __init__(self, backend_url: str = "http://localhost:5000", mqtt_service=None):
        super().__init__()
        self.backend_url = backend_url
        self.mqtt_service = mqtt_service
        self.parameters = []
        self.sync_timer = QTimer()
        self.sync_timer.timeout.connect(self._sync_parameters)
        
        # Connect to MQTT parameter updates
        if mqtt_service:
            mqtt_service.message_received.connect(self._on_mqtt_message)
    
    def start_sync(self, interval: int = 30):
        """Start periodic parameter sync"""
        self.sync_timer.start(interval * 1000)
        self._sync_parameters()
    
    def stop_sync(self):
        """Stop periodic sync"""
        self.sync_timer.stop()
    
    def _sync_parameters(self):
        """Fetch parameters from backend"""
        try:
            response = requests.get(
                f"{self.backend_url}/api/internal/parameters",
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                self.parameters = data.get('parameters', [])
                print(f"[PARAM_SYNC] Fetched {len(self.parameters)} parameters from backend")
                self.parameters_fetched.emit(self.parameters)
            else:
                error = f"Backend returned {response.status_code}"
                print(f"[PARAM_SYNC] Error: {error}")
                self.sync_error.emit(error)
        except Exception as e:
            error = f"Failed to sync parameters: {str(e)}"
            print(f"[PARAM_SYNC] {error}")
            self.sync_error.emit(error)
    
    def _on_mqtt_message(self, topic: str, payload: dict):
        """Handle MQTT parameter sync messages"""
        print(f"[PARAM_SYNC] Received MQTT message on topic: {topic}")
        print(f"[PARAM_SYNC] Payload: {payload}")
        
        if "sync/parameters" in topic:
            action = payload.get('action')
            param = payload.get('parameter')
            source = payload.get('source', 'unknown')
            
            print(f"[PARAM_SYNC] Action: {action}, Parameter: {param.get('name') if param else 'None'}, Source: {source}")
            
            if not param:
                print(f"[PARAM_SYNC] No parameter data in payload")
                return
            
            if action == 'create':
                # Add new parameter
                if param not in self.parameters:
                    self.parameters.append(param)
                    print(f"[PARAM_SYNC] Parameter created: {param.get('name')}")
                    self.parameter_updated.emit(param)
                    self.parameters_fetched.emit(self.parameters)
            
            elif action == 'update':
                # Update existing parameter
                updated = False
                for i, p in enumerate(self.parameters):
                    if p.get('id') == param.get('id'):
                        self.parameters[i] = param
                        updated = True
                        print(f"[PARAM_SYNC] Parameter updated: {param.get('name')}")
                        break
                
                if not updated:
                    # Parameter not found locally, add it
                    self.parameters.append(param)
                    print(f"[PARAM_SYNC] Parameter added (not found locally): {param.get('name')}")
                
                self.parameter_updated.emit(param)
                self.parameters_fetched.emit(self.parameters)
            
            elif action == 'delete':
                # Remove parameter
                original_count = len(self.parameters)
                self.parameters = [p for p in self.parameters if p.get('id') != param.get('id')]
                if len(self.parameters) < original_count:
                    print(f"[PARAM_SYNC] Parameter deleted: {param.get('name')}")
                    self.parameter_updated.emit(param)
                    self.parameters_fetched.emit(self.parameters)
                else:
                    print(f"[PARAM_SYNC] Parameter not found for deletion: {param.get('name')}")
    
    def get_enabled_parameters(self) -> List[Dict]:
        """Get only enabled parameters"""
        return [p for p in self.parameters if p.get('enabled', False)]
    
    def get_all_parameters(self) -> List[Dict]:
        """Get all parameters"""
        return self.parameters

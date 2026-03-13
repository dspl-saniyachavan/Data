"""
Parameter synchronization service for desktop application
"""

from typing import List, Dict
from PySide6.QtCore import QObject, Signal, QTimer
import requests


class ParameterSyncService(QObject):
    """Service for syncing parameters from backend"""
    
    parameters_fetched = Signal(list)
    sync_error = Signal(str)
    
    def __init__(self, backend_url: str = "http://localhost:5000"):
        super().__init__()
        self.backend_url = backend_url
        self.parameters = []
        self.sync_timer = QTimer()
        self.sync_timer.timeout.connect(self._sync_parameters)
    
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
    
    def get_enabled_parameters(self) -> List[Dict]:
        """Get only enabled parameters"""
        return [p for p in self.parameters if p.get('enabled', False)]
    
    def get_all_parameters(self) -> List[Dict]:
        """Get all parameters"""
        return self.parameters

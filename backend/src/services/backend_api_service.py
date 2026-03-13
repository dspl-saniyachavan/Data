"""
Backend API Service for frontend parameter synchronization
"""

import requests
import json
from typing import List, Dict, Optional
from src.core.config import Config


class BackendAPIService:
    """Service to communicate with backend API"""
    
    def __init__(self, token: Optional[str] = None):
        self.token = token
        self.base_url = Config.BACKEND_URL
        self.headers = {
            'Content-Type': 'application/json'
        }
        if token:
            self.headers['Authorization'] = f'Bearer {token}'
    
    def set_token(self, token: str):
        """Set authentication token"""
        self.token = token
        self.headers['Authorization'] = f'Bearer {token}'
    
    def get_parameters(self) -> Optional[List[Dict]]:
        """Fetch all parameters from backend"""
        try:
            url = f"{self.base_url}/api/parameters"
            print(f"[API] GET {url}")
            
            response = requests.get(url, headers=self.headers, timeout=5)
            
            if response.status_code == 200:
                parameters = response.json()
                print(f"[API] Fetched {len(parameters)} parameters")
                return parameters
            else:
                print(f"[API] Error: {response.status_code}")
                return None
        
        except Exception as e:
            print(f"[API] Error fetching parameters: {e}")
            return None
    
    def add_parameter(self, name: str, unit: str, description: str) -> Optional[Dict]:
        """Add new parameter"""
        try:
            url = f"{self.base_url}/api/parameters"
            payload = {
                'name': name,
                'unit': unit,
                'description': description
            }
            print(f"[API] POST {url}")
            
            response = requests.post(url, json=payload, headers=self.headers, timeout=5)
            
            if response.status_code == 201:
                parameter = response.json()
                print(f"[API] Created parameter: {name}")
                return parameter
            else:
                print(f"[API] Error: {response.status_code}")
                return None
        
        except Exception as e:
            print(f"[API] Error adding parameter: {e}")
            return None
    
    def update_parameter(self, param_id: int, **kwargs) -> Optional[Dict]:
        """Update parameter"""
        try:
            url = f"{self.base_url}/api/parameters/{param_id}"
            print(f"[API] PUT {url}")
            
            response = requests.put(url, json=kwargs, headers=self.headers, timeout=5)
            
            if response.status_code == 200:
                parameter = response.json()
                print(f"[API] Updated parameter: {param_id}")
                return parameter
            else:
                print(f"[API] Error: {response.status_code}")
                return None
        
        except Exception as e:
            print(f"[API] Error updating parameter: {e}")
            return None
    
    def delete_parameter(self, param_id: int) -> bool:
        """Delete parameter"""
        try:
            url = f"{self.base_url}/api/parameters/{param_id}"
            print(f"[API] DELETE {url}")
            
            response = requests.delete(url, headers=self.headers, timeout=5)
            
            if response.status_code == 200:
                print(f"[API] Deleted parameter: {param_id}")
                return True
            else:
                print(f"[API] Error: {response.status_code}")
                return False
        
        except Exception as e:
            print(f"[API] Error deleting parameter: {e}")
            return False

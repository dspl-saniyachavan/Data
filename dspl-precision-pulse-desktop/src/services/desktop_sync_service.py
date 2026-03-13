"""
Sync service for desktop application to sync with backend PostgreSQL
"""
import requests
import sqlite3
from datetime import datetime
from src.core.config import Config

class DesktopSyncService:
    """Service to sync desktop SQLite with backend PostgreSQL"""
    
    def __init__(self, db_manager, base_url="http://localhost:5000"):
        self.db_manager = db_manager
        self.base_url = base_url
        self.token = None
    
    def set_auth_token(self, token):
        """Set authentication token for API calls"""
        self.token = token
    
    def get_headers(self):
        """Get headers with authentication"""
        headers = {'Content-Type': 'application/json'}
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'
        return headers
    
    def sync_parameter_to_backend(self, param_data):
        """Sync parameter from SQLite to backend PostgreSQL"""
        try:
            # Convert SQLite parameter to backend format
            backend_param = {
                'name': param_data['name'],
                'unit': param_data['unit'],
                'description': param_data.get('description', ''),
                'enabled': param_data.get('enabled', True)
            }
            
            response = requests.post(
                f"{self.base_url}/api/parameters",
                json=backend_param,
                headers=self.get_headers()
            )
            
            return response.status_code in [200, 201]
        except Exception as e:
            print(f"Error syncing parameter to backend: {e}")
            return False
    
    def sync_user_to_backend(self, user_data):
        """Sync user from SQLite to backend PostgreSQL"""
        try:
            # Note: User creation would need a separate API endpoint
            # For now, just log the sync attempt
            print(f"Would sync user {user_data['email']} to backend")
            return True
        except Exception as e:
            print(f"Error syncing user to backend: {e}")
            return False
    
    def fetch_parameters_from_backend(self):
        """Fetch parameters from backend and sync to local SQLite"""
        try:
            response = requests.get(
                f"{self.base_url}/api/parameters",
                headers=self.get_headers()
            )
            
            if response.status_code == 200:
                data = response.json()
                parameters = data.get('parameters', [])
                
                with sqlite3.connect(self.db_manager.db_path) as conn:
                    cursor = conn.cursor()
                    
                    for param in parameters:
                        param_id = param['name'].lower().replace(' ', '_')
                        cursor.execute('''
                            INSERT OR REPLACE INTO parameters (id, name, unit, description, enabled)
                            VALUES (?, ?, ?, ?, ?)
                        ''', (param_id, param['name'], param['unit'], 
                              param.get('description', ''), param.get('enabled', True)))
                    
                    conn.commit()
                return True
        except Exception as e:
            print(f"Error fetching parameters from backend: {e}")
            return False
    
    def sync_all_to_backend(self):
        """Sync all local data to backend"""
        # Sync parameters
        with sqlite3.connect(self.db_manager.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id, name, unit, description, enabled FROM parameters')
            
            for row in cursor.fetchall():
                param_data = {
                    'id': row[0],
                    'name': row[1],
                    'unit': row[2],
                    'description': row[3],
                    'enabled': bool(row[4])
                }
                self.sync_parameter_to_backend(param_data)
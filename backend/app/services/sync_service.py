"""
Database sync service to mirror data between PostgreSQL (backend) and SQLite (desktop)
"""
import sqlite3
from datetime import datetime
from app.models import db
from app.models.user import User
from app.models.parameter import Parameter

class DatabaseSyncService:
    """Service to sync data between PostgreSQL and SQLite databases"""
    
    def __init__(self, sqlite_path=None):
        self.sqlite_path = sqlite_path or '/home/saniyachavani/Documents/Precision_Pulse/dspl-precision-pulse-desktop/data/precision_pulse.db'
    
    def sync_user_to_sqlite(self, user_data):
        """Sync user from PostgreSQL to SQLite"""
        try:
            with sqlite3.connect(self.sqlite_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT id FROM users WHERE email = ?', (user_data['email'],))
                existing = cursor.fetchone()
                
                if existing:
                    cursor.execute('''
                        UPDATE users SET name = ?, role = ?, is_active = ?, password_hash = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE email = ?
                    ''', (user_data['name'], user_data['role'], user_data['is_active'], 
                          user_data['password_hash'], user_data['email']))
                else:
                    cursor.execute('''
                        INSERT INTO users (email, name, password_hash, role, is_active, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    ''', (user_data['email'], user_data['name'], user_data['password_hash'], 
                          user_data['role'], user_data['is_active']))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error syncing user to SQLite: {e}")
            return False
    
    def sync_parameter_to_sqlite(self, param_data):
        """Sync parameter from PostgreSQL to SQLite"""
        try:
            with sqlite3.connect(self.sqlite_path) as conn:
                cursor = conn.cursor()
                param_id = param_data['name'].lower().replace(' ', '_')
                cursor.execute('''
                    INSERT OR REPLACE INTO parameters (id, name, unit, description, enabled)
                    VALUES (?, ?, ?, ?, ?)
                ''', (param_id, param_data['name'], param_data['unit'], 
                      param_data['description'], param_data['enabled']))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error syncing parameter to SQLite: {e}")
            return False

sync_service = DatabaseSyncService()
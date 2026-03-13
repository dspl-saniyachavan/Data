"""
Database manager for local SQLite operations
"""

import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Optional
from argon2 import PasswordHasher
import bcrypt
from src.core.config import Config

class DatabaseManager:
    """Manages local SQLite database operations"""
    
    def __init__(self):
        self.db_path = Config.DATABASE_PATH
        self.ph = PasswordHasher()
        
    def initialize_database(self):
        """Initialize database with required tables"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    password_hash TEXT NOT NULL,
                    role TEXT DEFAULT 'user',
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT (datetime('now', 'localtime')),
                    updated_at TIMESTAMP DEFAULT (datetime('now', 'localtime'))
                )
            ''')
            
            # Parameters table for local sync
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS parameters (
                    id INTEGER PRIMARY KEY,
                    name TEXT UNIQUE NOT NULL,
                    unit TEXT NOT NULL,
                    description TEXT DEFAULT '',
                    enabled BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT (datetime('now', 'localtime')),
                    updated_at TIMESTAMP DEFAULT (datetime('now', 'localtime'))
                )
            ''')
            
            # Parameter stream table for storing streamed data
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS parameter_stream (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    parameter_id INTEGER NOT NULL,
                    value REAL NOT NULL,
                    timestamp TIMESTAMP DEFAULT (datetime('now', 'localtime')),
                    synced BOOLEAN DEFAULT 0
                )
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_parameter_stream_param_id ON parameter_stream(parameter_id)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_parameter_stream_timestamp ON parameter_stream(timestamp)
            ''')
            
            # Local buffer table for offline data with foreign key
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS local_buffer (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    parameter_id INTEGER NOT NULL,
                    value REAL NOT NULL,
                    timestamp TIMESTAMP DEFAULT (datetime('now', 'localtime')),
                    synced BOOLEAN DEFAULT 0,
                    FOREIGN KEY (parameter_id) REFERENCES parameters(id)
                )
            ''')
            
            # Server log table for tracking all changes
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS server_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    resource_type TEXT NOT NULL,
                    resource_id TEXT,
                    action TEXT NOT NULL,
                    old_value TEXT,
                    new_value TEXT,
                    status TEXT DEFAULT 'success',
                    error_message TEXT,
                    timestamp TIMESTAMP DEFAULT (datetime('now', 'localtime')),
                    user_email TEXT,
                    device_id TEXT
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS config (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT (datetime('now', 'localtime'))
                )
            ''')
            
            # Permissions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS permissions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    role TEXT NOT NULL,
                    resource TEXT NOT NULL,
                    action TEXT NOT NULL,
                    allowed BOOLEAN DEFAULT 1,
                    UNIQUE(role, resource, action)
                )
            ''')
            
            conn.commit()
            self._migrate_timestamps(conn)
            self._create_default_data()
    
    def _migrate_timestamps(self, conn):
        """Migrate existing UTC timestamps to local time"""
        cursor = conn.cursor()
        try:
            cursor.execute('SELECT COUNT(*) FROM users')
            if cursor.fetchone()[0] > 0:
                cursor.execute('''
                    UPDATE users SET updated_at = datetime('now', 'localtime')
                    WHERE updated_at IS NULL
                ''')
            cursor.execute('SELECT COUNT(*) FROM parameters')
            if cursor.fetchone()[0] > 0:
                cursor.execute('''
                    UPDATE parameters SET updated_at = datetime('now', 'localtime')
                    WHERE updated_at IS NULL
                ''')
            conn.commit()
        except Exception as e:
            print(f"[DB] Migration error: {e}")
    
    def _create_default_data(self):
        """Create default users and parameters"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Check if admin user exists
            cursor.execute('SELECT COUNT(*) FROM users WHERE email = ?', ('admin@precisionpulse.com',))
            if cursor.fetchone()[0] == 0:
                admin_hash = self.ph.hash('admin123')
                cursor.execute('''
                    INSERT INTO users (email, name, password_hash, role)
                    VALUES (?, ?, ?, ?)
                ''', ('admin@precisionpulse.com', 'Admin User', admin_hash, 'admin'))
            
            # Check if client user exists
            cursor.execute('SELECT COUNT(*) FROM users WHERE email = ?', ('client@precisionpulse.com',))
            if cursor.fetchone()[0] == 0:
                client_hash = self.ph.hash('client123')
                cursor.execute('''
                    INSERT INTO users (email, name, password_hash, role)
                    VALUES (?, ?, ?, ?)
                ''', ('client@precisionpulse.com', 'Client User', client_hash, 'client'))
            
            # Check if regular user exists
            cursor.execute('SELECT COUNT(*) FROM users WHERE email = ?', ('user@precisionpulse.com',))
            if cursor.fetchone()[0] == 0:
                user_hash = self.ph.hash('user123')
                cursor.execute('''
                    INSERT INTO users (email, name, password_hash, role)
                    VALUES (?, ?, ?, ?)
                ''', ('user@precisionpulse.com', 'Regular User', user_hash, 'user'))
            
            # Default permissions
            default_permissions = [
                # Admin - full access
                ('admin', 'users', 'read'), ('admin', 'users', 'write'),
                ('admin', 'roles', 'read'), ('admin', 'roles', 'write'),
                ('admin', 'config', 'read'), ('admin', 'config', 'write'),
                ('admin', 'livedata', 'read'), ('admin', 'livedata', 'write'),
                ('admin', 'reports', 'read'), ('admin', 'reports', 'export'),
                ('admin', 'web', 'login'), ('admin', 'desktop', 'login'),
                
                # Client - data sending and config reading
                ('client', 'config', 'read'),
                ('client', 'livedata', 'write'), ('client', 'desktop', 'login'),
                
                # User - viewing only
                ('user', 'livedata', 'read'), ('user', 'reports', 'read'),
                ('user', 'web', 'login'), ('user', 'desktop', 'login'),
            ]
            
            for role, resource, action in default_permissions:
                cursor.execute('''
                    INSERT OR IGNORE INTO permissions (role, resource, action, allowed)
                    VALUES (?, ?, ?, 1)
                ''', (role, resource, action))
            
            conn.commit()
    
    def authenticate_user(self, email: str, password: str) -> Optional[Dict]:
        """Authenticate user credentials with both bcrypt and argon2 support"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, email, name, password_hash, role, is_active
                FROM users WHERE email = ? AND is_active = 1
            ''', (email,))
            
            user = cursor.fetchone()
            if user:
                password_hash = user[3]
                try:
                    # Try bcrypt first (for users created from web app)
                    if password_hash.startswith('$2b$'):
                        if bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8')):
                            return {
                                'id': user[0],
                                'email': user[1],
                                'name': user[2],
                                'role': user[4]
                            }
                    else:
                        # Try argon2 (for users created locally)
                        self.ph.verify(password_hash, password)
                        return {
                            'id': user[0],
                            'email': user[1],
                            'name': user[2],
                            'role': user[4]
                        }
                except:
                    return None
            return None
    
    def get_enabled_parameters(self) -> List[Dict]:
        """Get enabled parameters from local SQLite first, fallback to backend API"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, name, unit, description, enabled
                FROM parameters WHERE enabled = 1
                ORDER BY name
            ''')
            
            local_params = [
                {
                    'id': str(row[0]),
                    'name': row[1],
                    'unit': row[2],
                    'description': row[3] or ''
                }
                for row in cursor.fetchall()
            ]
            
            if local_params:
                print(f"Using {len(local_params)} parameters from SQLite")
                return local_params
        
        try:
            import requests
            response = requests.get(
                "http://localhost:5000/api/internal/parameters",
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                parameters = data.get('parameters', [])
                print(f"Using {len(parameters)} parameters from backend API")
                
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    for param in parameters:
                        if param.get('enabled', False):
                            cursor.execute('''
                                INSERT OR REPLACE INTO parameters (id, name, unit, enabled, description, created_at, updated_at)
                                VALUES (?, ?, ?, ?, ?, datetime('now', 'localtime'), datetime('now', 'localtime'))
                            ''', (param['id'], param['name'], param['unit'], 
                                  param.get('enabled', True), param.get('description', '')))
                    conn.commit()
                
                return [
                    {
                        'id': str(param['id']),
                        'name': param['name'],
                        'unit': param['unit'],
                        'description': param.get('description', '')
                    }
                    for param in parameters if param.get('enabled', False)
                ]
        except requests.exceptions.RequestException as e:
            print(f"Error fetching parameters from backend: {e}")
        
        return []
    
    def buffer_telemetry(self, parameter_id: int, value: float):
        """Buffer telemetry data when offline"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO local_buffer (parameter_id, value, timestamp)
                VALUES (?, ?, datetime('now', 'localtime'))
            ''', (parameter_id, value))
            conn.commit()
    
    def store_parameter_stream(self, parameter_id: int, value: float):
        """Store parameter stream data"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                # Ensure parameter_id is integer
                param_id = int(parameter_id) if parameter_id else None
                if param_id is None:
                    print(f"[DB] Warning: Invalid parameter_id for stream storage")
                    return
                cursor.execute('''
                    INSERT INTO parameter_stream (parameter_id, value, timestamp)
                    VALUES (?, ?, datetime('now', 'localtime'))
                ''', (param_id, float(value)))
                conn.commit()
                print(f"[DB] Stored parameter_stream: param_id={param_id}, value={value}")
        except Exception as e:
            print(f"[DB] Error storing parameter_stream: {e}")
    
    def get_buffered_data(self) -> List[Dict]:
        """Get all unsynced buffered data with parameter details"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT lb.id, lb.parameter_id, p.name, p.unit, lb.value, lb.timestamp
                FROM local_buffer lb
                JOIN parameters p ON lb.parameter_id = p.id
                WHERE lb.synced = 0
                ORDER BY lb.timestamp ASC
            ''')
            
            return [
                {
                    'id': row[0],
                    'parameter_id': row[1],
                    'parameter_name': row[2],
                    'unit': row[3],
                    'value': row[4],
                    'timestamp': row[5]
                }
                for row in cursor.fetchall()
            ]
    
    def get_parameter_stream_data(self, parameter_id: Optional[int] = None, limit: int = 100) -> List[Dict]:
        """Get parameter stream data"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            if parameter_id:
                cursor.execute('''
                    SELECT ps.id, ps.parameter_id, p.name, p.unit, ps.value, ps.timestamp
                    FROM parameter_stream ps
                    JOIN parameters p ON ps.parameter_id = p.id
                    WHERE ps.parameter_id = ?
                    ORDER BY ps.timestamp DESC
                    LIMIT ?
                ''', (parameter_id, limit))
            else:
                cursor.execute('''
                    SELECT ps.id, ps.parameter_id, p.name, p.unit, ps.value, ps.timestamp
                    FROM parameter_stream ps
                    JOIN parameters p ON ps.parameter_id = p.id
                    ORDER BY ps.timestamp DESC
                    LIMIT ?
                ''', (limit,))
            
            return [
                {
                    'id': row[0],
                    'parameter_id': row[1],
                    'parameter_name': row[2],
                    'unit': row[3],
                    'value': row[4],
                    'timestamp': row[5]
                }
                for row in cursor.fetchall()
            ]
    
    def log_server_event(self, event_type: str, resource_type: str, action: str, 
                        resource_id: Optional[str] = None, old_value: Optional[str] = None,
                        new_value: Optional[str] = None, status: str = 'success',
                        error_message: Optional[str] = None, user_email: Optional[str] = None,
                        device_id: Optional[str] = None):
        """Log server event to database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO server_log 
                (event_type, resource_type, resource_id, action, old_value, new_value, 
                 status, error_message, user_email, device_id, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now', 'localtime'))
            ''', (event_type, resource_type, resource_id, action, old_value, new_value,
                  status, error_message, user_email, device_id))
            conn.commit()
    
    def get_server_logs(self, limit: int = 100, event_type: Optional[str] = None) -> List[Dict]:
        """Get server logs"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            if event_type:
                cursor.execute('''
                    SELECT id, event_type, resource_type, resource_id, action, old_value, 
                           new_value, status, error_message, timestamp, user_email, device_id
                    FROM server_log
                    WHERE event_type = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                ''', (event_type, limit))
            else:
                cursor.execute('''
                    SELECT id, event_type, resource_type, resource_id, action, old_value, 
                           new_value, status, error_message, timestamp, user_email, device_id
                    FROM server_log
                    ORDER BY timestamp DESC
                    LIMIT ?
                ''', (limit,))
            
            return [
                {
                    'id': row[0],
                    'event_type': row[1],
                    'resource_type': row[2],
                    'resource_id': row[3],
                    'action': row[4],
                    'old_value': row[5],
                    'new_value': row[6],
                    'status': row[7],
                    'error_message': row[8],
                    'timestamp': row[9],
                    'user_email': row[10],
                    'device_id': row[11]
                }
                for row in cursor.fetchall()
            ]
    
    def mark_data_synced(self, buffer_ids: List[int]):
        """Mark buffered data as synced"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            placeholders = ','.join('?' * len(buffer_ids))
            cursor.execute(f'''
                UPDATE local_buffer 
                SET synced = 1 
                WHERE id IN ({placeholders})
            ''', buffer_ids)
            conn.commit()
    
    def clear_synced_data(self):
        """Clear old synced data"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                DELETE FROM local_buffer 
                WHERE synced = 1 AND timestamp < datetime('now', 'localtime', '-1 day')
            ''')
            conn.commit()
    
    def check_permission(self, role: str, resource: str, action: str) -> bool:
        """Check if role has permission for resource action"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT allowed FROM permissions
                WHERE role = ? AND resource = ? AND action = ?
            ''', (role, resource, action))
            result = cursor.fetchone()
            return result[0] == 1 if result else False

    def delete_buffered_data(self, buffer_ids: List[int]):
        """Delete buffered data by IDs"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            placeholders = ','.join('?' * len(buffer_ids))
            cursor.execute(f'''
                DELETE FROM local_buffer 
                WHERE id IN ({placeholders})
            ''', buffer_ids)
            conn.commit()
            print(f"[DB] Deleted {cursor.rowcount} buffered records")
    
    def mark_parameter_stream_synced(self, stream_ids: List[int]):
        """Mark parameter stream data as synced"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            placeholders = ','.join('?' * len(stream_ids))
            cursor.execute(f'''
                UPDATE parameter_stream 
                SET synced = 1 
                WHERE id IN ({placeholders})
            ''', stream_ids)
            conn.commit()

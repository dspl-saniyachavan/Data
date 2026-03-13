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
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Local buffer table for offline data
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS local_buffer (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    parameter_id TEXT NOT NULL,
                    parameter_name TEXT NOT NULL,
                    value REAL NOT NULL,
                    unit TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    synced BOOLEAN DEFAULT 0
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
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS config (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Parameters table - removed as parameters are now managed by backend
            # Parameters are fetched from the web application backend
            
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
            self._create_default_data()
    
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
            
            # Default parameters - removed as parameters are now managed by backend
            # Parameters are fetched from the web application backend
            
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
        # Try local SQLite first
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
                print(f"  Using {len(local_params)} parameters from SQLite")
                return local_params
        
        # Fallback to backend API
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
                print(f"🌐 Using {len(parameters)} parameters from backend API")
                
                # Save to local SQLite for future use
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    for param in parameters:
                        if param.get('enabled', False):
                            cursor.execute('''
                                INSERT OR REPLACE INTO parameters (id, name, unit, enabled, description)
                                VALUES (?, ?, ?, ?, ?)
                            ''', (param['id'], param['name'], param['unit'], 
                                  param.get('enabled', True), param.get('description', '')))
                    conn.commit()
                
                # Return only enabled parameters
                return [
                    {
                        'id': str(param['id']),
                        'name': param['name'],
                        'unit': param['unit'],
                        'description': param.get('description', '')
                    }
                    for param in parameters if param.get('enabled', False)
                ]
        except Exception as e:
            print(f"Error fetching parameters from backend: {e}")
        
        # Return empty list if both sources fail
        return []
    
    def buffer_telemetry(self, parameter_id: str, parameter_name: str, value: float, unit: str):
        """Buffer telemetry data when offline"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO local_buffer (parameter_id, parameter_name, value, unit)
                VALUES (?, ?, ?, ?)
            ''', (parameter_id, parameter_name, value, unit))
            conn.commit()
    
    def get_buffered_data(self) -> List[Dict]:
        """Get all unsynced buffered data"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, parameter_id, parameter_name, value, unit, timestamp
                FROM local_buffer WHERE synced = 0
                ORDER BY timestamp ASC
            ''')
            
            return [
                {
                    'id': row[0],
                    'parameter_id': row[1],
                    'parameter_name': row[2],
                    'value': row[3],
                    'unit': row[4],
                    'timestamp': row[5]
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
                WHERE synced = 1 AND timestamp < datetime('now', '-1 day')
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
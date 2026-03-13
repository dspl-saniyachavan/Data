"""
User synchronization service for desktop application
"""

from typing import List, Dict
from PySide6.QtCore import QObject, Signal
import requests


class UserSyncService(QObject):
    """Service for syncing user, role, and permission changes from backend via MQTT"""
    
    user_created = Signal(dict)
    user_updated = Signal(dict)
    user_deleted = Signal(int, str)  # user_id, email
    role_changed = Signal(int, str, str, str)  # user_id, email, old_role, new_role
    permission_changed = Signal(str, list)  # role, permissions
    sync_error = Signal(str)
    
    def __init__(self, mqtt_service=None):
        super().__init__()
        self.mqtt_service = mqtt_service
        self.users = []
        
        # Connect to MQTT message signals
        if mqtt_service:
            mqtt_service.message_received.connect(self._on_mqtt_message)
    
    def _on_mqtt_message(self, topic: str, payload: dict):
        """Handle MQTT user sync messages"""
        try:
            msg_type = payload.get('type')
            
            if 'sync/users/created' in topic or msg_type == 'user_created':
                user = payload.get('user', {})
                self.users.append(user)
                print(f"[USER_SYNC] User created: {user.get('email')}")
                self.user_created.emit(user)
            
            elif 'sync/users/updated' in topic or msg_type == 'user_updated':
                user = payload.get('user', {})
                for i, u in enumerate(self.users):
                    if u.get('id') == user.get('id'):
                        self.users[i] = user
                        break
                print(f"[USER_SYNC] User updated: {user.get('email')}")
                self.user_updated.emit(user)
            
            elif 'sync/users/deleted' in topic or msg_type == 'user_deleted':
                user = payload.get('user', {})
                user_id = user.get('id')
                email = user.get('email')
                self.users = [u for u in self.users if u.get('id') != user_id]
                print(f"[USER_SYNC] User deleted: {email}")
                self.user_deleted.emit(user_id, email)
            
            elif 'sync/roles/changed' in topic or msg_type == 'role_changed':
                user_id = payload.get('user_id')
                email = payload.get('email')
                old_role = payload.get('old_role')
                new_role = payload.get('new_role')
                
                # Update user role in local list
                for u in self.users:
                    if u.get('id') == user_id:
                        u['role'] = new_role
                        break
                
                print(f"[USER_SYNC] Role changed for {email}: {old_role} -> {new_role}")
                self.role_changed.emit(user_id, email, old_role, new_role)
            
            elif 'sync/permissions/changed' in topic or msg_type == 'permission_changed':
                role = payload.get('role')
                permissions = payload.get('permissions', [])
                print(f"[USER_SYNC] Permissions changed for role {role}")
                self.permission_changed.emit(role, permissions)
        
        except Exception as e:
            error = f"Error processing user sync message: {str(e)}"
            print(f"[USER_SYNC] {error}")
            self.sync_error.emit(error)
    
    def get_users(self) -> List[Dict]:
        """Get all synced users"""
        return self.users
    
    def get_user_by_id(self, user_id: int) -> Dict:
        """Get user by ID"""
        for u in self.users:
            if u.get('id') == user_id:
                return u
        return None
    
    def get_user_by_email(self, email: str) -> Dict:
        """Get user by email"""
        for u in self.users:
            if u.get('email') == email:
                return u
        return None

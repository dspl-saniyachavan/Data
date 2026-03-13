"""
MQTT sync service for backend to handle desktop sync messages
"""

import json
import asyncio
import ssl
from gmqtt import Client as MQTTClient
from app.models import db
from app.models.user import User
from app.models.parameter import Parameter
from config.config import Config

class MQTTSyncService:
    def __init__(self, app):
        self.app = app
        self.client = None
        
    async def start(self):
        """Start MQTT client and subscribe to sync topics"""
        self.client = MQTTClient("backend_sync")
        
        # Set message handler
        self.client.on_message = self.handle_message
        
        # Configure TLS if enabled
        if Config.MQTT_USE_TLS:
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            self.client.set_tls_params(
                ca_certs=Config.MQTT_CA_CERTS,
                certfile=None,
                keyfile=None,
                cert_reqs=ssl.CERT_NONE,
                tls_version=ssl.PROTOCOL_TLSv1_2,
                ciphers=None
            )
        
        # Connect to MQTT broker
        await self.client.connect(Config.MQTT_BROKER, Config.MQTT_PORT)
        
        # Subscribe to sync topics
        self.client.subscribe('precisionpulse/sync/users/#', qos=1)
        self.client.subscribe('precisionpulse/sync/parameters', qos=1)
        
        print("✓ Backend MQTT sync service started")
    
    def handle_message(self, client, topic, payload, qos, properties):
        """Handle incoming sync messages"""
        try:
            data = json.loads(payload.decode('utf-8'))
            
            # Skip messages from backend itself
            if data.get('source') == 'backend':
                return
            
            with self.app.app_context():
                if 'users' in topic:
                    self.sync_user(data)
                elif 'parameters' in topic:
                    self.sync_parameter(data)
                    
        except Exception as e:
            print(f"MQTT sync error: {e}")
    
    def sync_user(self, data):
        """Sync user changes from desktop"""
        action = data.get('action')
        user_data = data.get('user', {})
        
        try:
            if action == 'create':
                existing = User.query.filter_by(email=user_data['email']).first()
                if not existing:
                    user = User(
                        email=user_data['email'],
                        name=user_data['name'],
                        password_hash=user_data.get('password_hash', ''),
                        role=user_data.get('account_type', 'user')
                    )
                    db.session.add(user)
                    db.session.commit()
                    print(f"✓ Synced user create: {user_data['email']}")
            
            elif action == 'update':
                user = User.query.filter_by(email=user_data['email']).first()
                if user:
                    user.name = user_data['name']
                    user.role = user_data.get('account_type', user.role)
                    user.is_active = user_data.get('is_active', user.is_active)
                    db.session.commit()
                    print(f"✓ Synced user update: {user_data['email']}")
            
            elif action == 'delete':
                user = User.query.filter_by(email=user_data['email']).first()
                if user:
                    db.session.delete(user)
                    db.session.commit()
                    print(f"✓ Synced user delete: {user_data['email']}")
                    
        except Exception as e:
            db.session.rollback()
            print(f"User sync error: {e}")
    
    def sync_parameter(self, data):
        """Sync parameter changes from desktop"""
        action = data.get('action', 'update')
        param_data = data.get('parameter', {})
        
        try:
            print(f"📥 Backend sync - Action: {action}, Parameter: {param_data.get('name', param_data.get('id', 'unknown'))}")
            if action == 'delete':
                param = Parameter.query.get(param_data.get('id'))
                if param:
                    db.session.delete(param)
                    db.session.commit()
                    print(f"✓ Synced parameter delete: {param_data.get('id')}")
            else:
                param = Parameter.query.get(param_data.get('id'))
                if param:
                    param.name = param_data.get('name', param.name)
                    param.unit = param_data.get('unit', param.unit)
                    param.enabled = param_data.get('enabled', param.enabled)
                    param.description = param_data.get('description', param.description)
                    db.session.commit()
                    print(f"✓ Synced parameter update: {param.name}")
                else:
                    # Create new parameter
                    param = Parameter(
                        name=param_data['name'],
                        unit=param_data['unit'],
                        enabled=param_data.get('enabled', True),
                        description=param_data.get('description', '')
                    )
                    db.session.add(param)
                    db.session.commit()
                    print(f"✓ Synced parameter create: {param.name}")
                    
        except Exception as e:
            db.session.rollback()
            print(f"Parameter sync error: {e}")
    
    async def publish_change(self, topic, data):
        """Publish changes to MQTT"""
        if self.client:
            data['source'] = 'backend'
            self.client.publish(topic, json.dumps(data), qos=1)
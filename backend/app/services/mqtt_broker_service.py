"""
MQTT Broker service for backend with TLS and WebSocket support
"""

import asyncio
import ssl
import json
from typing import Dict, Any
from hbmqtt.broker import Broker
from hbmqtt.client import MQTTClient
from flask import Flask
from flask_socketio import SocketIO, emit

class MQTTBrokerService:
    """MQTT Broker with TLS and WebSocket bridge"""
    
    def __init__(self, app: Flask, socketio: SocketIO):
        self.app = app
        self.socketio = socketio
        self.broker = None
        self.client = None
        self.running = False
        
    async def start_broker(self):
        """Start MQTT broker with TLS"""
        config = {
            'listeners': {
                'default': {
                    'type': 'tcp',
                    'bind': '0.0.0.0:1883'
                },
                'tls': {
                    'type': 'tcp',
                    'bind': '0.0.0.0:8883',
                    'ssl': 'on',
                    'cafile': '/path/to/ca.crt',
                    'certfile': '/path/to/server.crt',
                    'keyfile': '/path/to/server.key'
                },
                'ws': {
                    'type': 'ws',
                    'bind': '0.0.0.0:9001',
                    'max_connections': 50
                }
            },
            'sys_interval': 10,
            'auth': {
                'allow-anonymous': True,
                'password-file': None
            }
        }
        
        self.broker = Broker(config)
        await self.broker.start()
        print("✓ MQTT Broker started with TLS and WebSocket support")
        
        # Start client to bridge MQTT to WebSocket
        await self.start_mqtt_client()
        
    async def start_mqtt_client(self):
        """Start MQTT client to bridge messages to WebSocket"""
        self.client = MQTTClient()
        await self.client.connect('mqtt://localhost:1883/')
        await self.client.subscribe([
            ('precisionpulse/+/telemetry', 0),
            ('precisionpulse/+/heartbeat', 0),
            ('precisionpulse/sync/+', 0)
        ])
        
        # Start message handling loop
        asyncio.create_task(self.handle_mqtt_messages())
        
    async def handle_mqtt_messages(self):
        """Handle MQTT messages and forward to WebSocket"""
        try:
            while True:
                message = await self.client.deliver_message()
                topic = message.variable_header.topic_name
                payload = message.payload.data.decode('utf-8')
                
                # Forward to WebSocket clients
                self.socketio.emit('mqtt_message', {
                    'topic': topic,
                    'payload': json.loads(payload) if payload else {}
                })
                
        except Exception as e:
            print(f"Error handling MQTT messages: {e}")
            
    async def stop(self):
        """Stop MQTT broker and client"""
        if self.client:
            await self.client.disconnect()
        if self.broker:
            await self.broker.shutdown()
        self.running = False
        print("✓ MQTT Broker stopped")

# Global broker instance
mqtt_broker_service = None

def init_mqtt_broker(app: Flask, socketio: SocketIO):
    """Initialize MQTT broker service"""
    global mqtt_broker_service
    mqtt_broker_service = MQTTBrokerService(app, socketio)
    return mqtt_broker_service
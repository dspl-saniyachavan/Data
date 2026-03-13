"""
WebSocket Service for real-time parameter updates
"""

import asyncio
import json
from typing import Callable, Optional
from src.core.config import Config


class WebSocketService:
    """Service for WebSocket communication with frontend"""
    
    def __init__(self):
        self.ws = None
        self.connected = False
        self.on_message_callback = None
        self.on_connect_callback = None
        self.on_disconnect_callback = None
    
    def set_on_message_callback(self, callback: Callable):
        """Set callback for incoming messages"""
        self.on_message_callback = callback
    
    def set_on_connect_callback(self, callback: Callable):
        """Set callback for connection"""
        self.on_connect_callback = callback
    
    def set_on_disconnect_callback(self, callback: Callable):
        """Set callback for disconnection"""
        self.on_disconnect_callback = callback
    
    async def connect(self):
        """Connect to WebSocket server"""
        try:
            import websockets
            ws_url = f"ws://localhost:3000/ws/parameters"
            print(f"[WS] Connecting to {ws_url}")
            
            self.ws = await websockets.connect(ws_url)
            self.connected = True
            print(f"[WS] Connected")
            
            if self.on_connect_callback:
                self.on_connect_callback()
            
            # Listen for messages
            await self._listen()
        
        except Exception as e:
            print(f"[WS] Connection error: {e}")
            self.connected = False
    
    async def _listen(self):
        """Listen for incoming messages"""
        try:
            async for message in self.ws:
                if self.on_message_callback:
                    data = json.loads(message)
                    self.on_message_callback(data)
        except Exception as e:
            print(f"[WS] Listen error: {e}")
            self.connected = False
            if self.on_disconnect_callback:
                self.on_disconnect_callback()
    
    async def send(self, data: dict):
        """Send message to WebSocket"""
        if self.connected and self.ws:
            try:
                await self.ws.send(json.dumps(data))
            except Exception as e:
                print(f"[WS] Send error: {e}")
    
    async def disconnect(self):
        """Disconnect from WebSocket"""
        if self.ws:
            await self.ws.close()
            self.connected = False
            print(f"[WS] Disconnected")

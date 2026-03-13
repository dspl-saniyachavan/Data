"""
WebSocket Service - DEPRECATED

This service is no longer used. All communication between desktop and frontend
must go through the backend API. Direct desktop <-> frontend communication is not allowed.

All data flows through: Desktop <-> Backend <-> Frontend
"""

import logging

logger = logging.getLogger(__name__)


class WebSocketService:
    """Deprecated - Do not use. Use backend API instead."""
    
    def __init__(self):
        logger.warning("[DEPRECATED] WebSocketService is deprecated. Use backend API instead.")
        self.ws = None
        self.connected = False
    
    async def connect(self):
        """Deprecated - Do not use"""
        logger.error("[DEPRECATED] WebSocketService.connect() should not be called. Use backend API.")
        raise NotImplementedError("WebSocketService is deprecated. All communication must go through backend.")
    
    async def disconnect(self):
        """Deprecated - Do not use"""
        logger.error("[DEPRECATED] WebSocketService.disconnect() should not be called.")
        pass
    
    async def send(self, data: dict):
        """Deprecated - Do not use"""
        logger.error("[DEPRECATED] WebSocketService.send() should not be called. Use backend API.")
        raise NotImplementedError("WebSocketService is deprecated. All communication must go through backend.")

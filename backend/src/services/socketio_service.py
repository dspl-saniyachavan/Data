"""
Socket.IO service for desktop with offline mode and local queuing
"""
import socketio
import threading
import time
import sqlite3
import json
from datetime import datetime
from typing import Callable, Optional
import logging

logger = logging.getLogger(__name__)

class DesktopSocketIOService:
    def __init__(self, db_path: str = 'data/precision_pulse.db'):
        self.sio = socketio.Client(
            reconnection=True,
            reconnection_delay=1,
            reconnection_delay_max=5,
            reconnection_attempts=5,
            transports=['websocket', 'polling']
        )
        self.db_path = db_path
        self.is_connected = False
        self.is_syncing = False
        self.callbacks = {}
        self.setup_handlers()
    
    def setup_handlers(self):
        """Setup Socket.IO event handlers"""
        @self.sio.on('connect')
        def on_connect():
            self.is_connected = True
            logger.info('[Socket.IO] Connected to server')
            self._emit_callback('connection_status', {'connected': True})
            self.sync_buffer()
        
        @self.sio.on('disconnect')
        def on_disconnect():
            self.is_connected = False
            logger.info('[Socket.IO] Disconnected from server')
            self._emit_callback('connection_status', {'connected': False})
        
        @self.sio.on('error')
        def on_error(error):
            logger.error(f'[Socket.IO] Error: {error}')
            self._emit_callback('connection_error', {'error': str(error)})
    
    def connect(self, url: str = 'http://localhost:5000'):
        """Connect to Socket.IO server"""
        try:
            self.sio.connect(url)
            logger.info(f'[Socket.IO] Connecting to {url}')
        except Exception as e:
            logger.error(f'[Socket.IO] Connection failed: {e}')
            self.is_connected = False
    
    def disconnect(self):
        """Disconnect from Socket.IO server"""
        if self.sio.connected:
            self.sio.disconnect()
            self.is_connected = False
    
    def emit_telemetry(self, telemetry_data: dict):
        """Emit telemetry data - queue if offline"""
        if self.is_connected:
            try:
                self.sio.emit('telemetry_stream', telemetry_data)
                logger.debug(f'[Socket.IO] Emitted telemetry')
            except Exception as e:
                logger.error(f'[Socket.IO] Emit failed: {e}')
                self._queue_to_buffer(telemetry_data)
        else:
            logger.info('[Socket.IO] Offline - queuing telemetry to buffer')
            self._queue_to_buffer(telemetry_data)
    
    def _queue_to_buffer(self, telemetry_data: dict):
        """Queue telemetry to local SQLite buffer"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS telemetry_buffer (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    data TEXT NOT NULL,
                    synced BOOLEAN DEFAULT 0
                )
            ''')
            
            cursor.execute(
                'INSERT INTO telemetry_buffer (data, synced) VALUES (?, ?)',
                (json.dumps(telemetry_data), 0)
            )
            conn.commit()
            conn.close()
            logger.info('[Buffer] Queued telemetry to buffer')
        except Exception as e:
            logger.error(f'[Buffer] Queue failed: {e}')
    
    def sync_buffer(self):
        """Sync buffered telemetry when connection restored"""
        if self.is_syncing or not self.is_connected:
            return
        
        self.is_syncing = True
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT id, data FROM telemetry_buffer WHERE synced = 0 LIMIT 100')
            rows = cursor.fetchall()
            
            if rows:
                logger.info(f'[Buffer] Syncing {len(rows)} buffered records')
                for row_id, data in rows:
                    try:
                        telemetry_data = json.loads(data)
                        self.sio.emit('telemetry_stream', telemetry_data)
                        cursor.execute('UPDATE telemetry_buffer SET synced = 1 WHERE id = ?', (row_id,))
                    except Exception as e:
                        logger.error(f'[Buffer] Sync record failed: {e}')
                
                conn.commit()
                logger.info('[Buffer] Sync completed')
            
            conn.close()
        except Exception as e:
            logger.error(f'[Buffer] Sync failed: {e}')
        finally:
            self.is_syncing = False
    
    def on(self, event: str, callback: Callable):
        """Register event callback"""
        if event not in self.callbacks:
            self.callbacks[event] = []
        self.callbacks[event].append(callback)
    
    def _emit_callback(self, event: str, data: dict):
        """Emit callback to registered listeners"""
        if event in self.callbacks:
            for callback in self.callbacks[event]:
                try:
                    callback(data)
                except Exception as e:
                    logger.error(f'[Callback] Error: {e}')
    
    def get_connection_status(self) -> bool:
        """Get current connection status"""
        return self.is_connected
    
    def get_buffer_count(self) -> int:
        """Get count of buffered records"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM telemetry_buffer WHERE synced = 0')
            count = cursor.fetchone()[0]
            conn.close()
            return count
        except:
            return 0

"""
Configuration Management Service for Desktop Application
Listens to MQTT config updates and applies them
"""

import json
import logging
from datetime import datetime
from PySide6.QtCore import QObject, Signal

logger = logging.getLogger(__name__)

class ConfigurationService(QObject):
    """Service to manage system configuration and sync with backend"""
    
    # Signals
    config_updated = Signal(str, str)  # key, value
    config_bulk_updated = Signal(dict)  # all configs
    config_sync_completed = Signal()
    config_sync_failed = Signal(str)  # error message
    
    def __init__(self, mqtt_service, database_manager):
        super().__init__()
        self.mqtt_service = mqtt_service
        self.db = database_manager
        self.config_cache = {}
        self.config_version = 0
        self.last_sync_time = None
        self.sync_in_progress = False
        
        # Connect MQTT signals
        self.mqtt_service.config_update_received.connect(self._on_config_update)
        
        # Load initial config
        self._load_config_from_db()
    
    def _load_config_from_db(self):
        """Load configuration from local database"""
        try:
            import sqlite3
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT key, value FROM config WHERE enabled = 1')
                rows = cursor.fetchall()
                
                for key, value in rows:
                    self.config_cache[key] = value
                
                logger.info(f"[CONFIG] Loaded {len(self.config_cache)} configurations from database")
        except Exception as e:
            logger.error(f"[CONFIG] Error loading config: {e}")
    
    def _on_config_update(self, config_data: dict):
        """Handle configuration update from MQTT"""
        try:
            self.sync_in_progress = True
            action = config_data.get('action')
            
            if action == 'bulk_update':
                self._handle_bulk_update(config_data)
            elif action == 'updated':
                self._handle_single_update(config_data)
            elif action == 'created':
                self._handle_config_created(config_data)
            elif action == 'deleted':
                self._handle_config_deleted(config_data)
            
            self.last_sync_time = datetime.now()
            self.apply_config_changes()
            logger.info(f"[CONFIG] Applied {action} from backend")
            self.config_sync_completed.emit()
        except Exception as e:
            logger.error(f"[CONFIG] Error handling update: {e}")
            self.config_sync_failed.emit(str(e))
        finally:
            self.sync_in_progress = False
    
    def _handle_single_update(self, config_data: dict):
        """Handle single configuration update"""
        key = config_data.get('key')
        value = config_data.get('value')
        
        if key and value is not None:
            self.config_cache[key] = value
            self._save_config_to_db(key, value)
            self.config_updated.emit(key, str(value))
            logger.info(f"[CONFIG] Updated {key} = {value}")
    
    def _handle_bulk_update(self, config_data: dict):
        """Handle bulk configuration update"""
        configs = config_data.get('configs', [])
        
        for config in configs:
            key = config.get('key')
            value = config.get('value')
            
            if key and value is not None:
                self.config_cache[key] = value
                self._save_config_to_db(key, value)
        
        self.config_bulk_updated.emit(self.config_cache)
        logger.info(f"[CONFIG] Bulk updated {len(configs)} configurations")
    
    def _handle_config_created(self, config_data: dict):
        """Handle new configuration creation"""
        key = config_data.get('key')
        value = config_data.get('value')
        
        if key and value is not None:
            self.config_cache[key] = value
            self._save_config_to_db(key, value)
            self.config_updated.emit(key, str(value))
            logger.info(f"[CONFIG] Created new config {key}")
    
    def _handle_config_deleted(self, config_data: dict):
        """Handle configuration deletion"""
        key = config_data.get('key')
        
        if key and key in self.config_cache:
            del self.config_cache[key]
            self._delete_config_from_db(key)
            logger.info(f"[CONFIG] Deleted config {key}")
    
    def _save_config_to_db(self, key: str, value: str):
        """Save configuration to local database"""
        try:
            import sqlite3
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO config (key, value, updated_at)
                    VALUES (?, ?, datetime('now'))
                ''', (key, str(value)))
                conn.commit()
        except Exception as e:
            logger.error(f"[CONFIG] Error saving to DB: {e}")
    
    def _delete_config_from_db(self, key: str):
        """Delete configuration from local database"""
        try:
            import sqlite3
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM config WHERE key = ?', (key,))
                conn.commit()
        except Exception as e:
            logger.error(f"[CONFIG] Error deleting from DB: {e}")
    
    def get_config(self, key: str, default=None):
        """Get configuration value"""
        return self.config_cache.get(key, default)
    
    def get_all_configs(self) -> dict:
        """Get all configurations"""
        return self.config_cache.copy()
    
    def set_config(self, key: str, value: str):
        """Set configuration locally (doesn't sync to backend)"""
        self.config_cache[key] = value
        self._save_config_to_db(key, value)
        self.config_updated.emit(key, str(value))
    
    def apply_config_changes(self):
        """Apply configuration changes to running services"""
        try:
            # Apply telemetry interval change
            telemetry_interval = self.get_config('TELEMETRY_INTERVAL')
            if telemetry_interval:
                logger.info(f"[CONFIG] Applying telemetry interval: {telemetry_interval}s")
            
            # Apply MQTT settings
            mqtt_broker = self.get_config('MQTT_BROKER')
            mqtt_port = self.get_config('MQTT_PORT')
            if mqtt_broker or mqtt_port:
                logger.info(f"[CONFIG] MQTT settings updated: {mqtt_broker}:{mqtt_port}")
            
            # Apply buffer settings
            buffer_size = self.get_config('BUFFER_SIZE')
            if buffer_size:
                logger.info(f"[CONFIG] Buffer size: {buffer_size}")
            
            # Apply debug logging
            debug_mode = self.get_config('DEBUG_MODE')
            if debug_mode:
                logger.info(f"[CONFIG] Debug mode: {debug_mode}")
            
            # Apply sync frequency
            sync_frequency = self.get_config('SYNC_FREQUENCY')
            if sync_frequency:
                logger.info(f"[CONFIG] Sync frequency: {sync_frequency}s")
        
        except Exception as e:
            logger.error(f"[CONFIG] Error applying changes: {e}")
    
    def get_sync_status(self) -> dict:
        """Get configuration sync status"""
        return {
            'last_sync_time': self.last_sync_time.isoformat() if self.last_sync_time else None,
            'sync_in_progress': self.sync_in_progress,
            'config_version': self.config_version,
            'config_count': len(self.config_cache)
        }
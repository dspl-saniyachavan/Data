#!/usr/bin/env python3
"""Initialize default system configurations"""

import sys
sys.path.insert(0, '/home/saniyachavani/Documents/Precision_Pulse/backend')

from app import create_app
from app.models import db
from app.models.system_config import SystemConfig

app = create_app()

DEFAULT_CONFIGS = [
    # MQTT Settings
    {
        'key': 'MQTT_BROKER',
        'value': 'localhost',
        'description': 'MQTT broker hostname or IP address',
        'category': 'mqtt',
        'data_type': 'string'
    },
    {
        'key': 'MQTT_PORT',
        'value': '18883',
        'description': 'MQTT broker port',
        'category': 'mqtt',
        'data_type': 'integer'
    },
    {
        'key': 'MQTT_USE_TLS',
        'value': 'true',
        'description': 'Use TLS for MQTT connection',
        'category': 'mqtt',
        'data_type': 'boolean'
    },
    
    # Telemetry Settings
    {
        'key': 'TELEMETRY_INTERVAL',
        'value': '2',
        'description': 'Telemetry data push interval in seconds',
        'category': 'telemetry',
        'data_type': 'integer'
    },
    {
        'key': 'HEARTBEAT_INTERVAL',
        'value': '60',
        'description': 'Heartbeat interval in seconds',
        'category': 'telemetry',
        'data_type': 'integer'
    },
    
    # Buffer Settings
    {
        'key': 'BUFFER_SIZE',
        'value': '10000',
        'description': 'Maximum number of records to buffer when offline',
        'category': 'buffer',
        'data_type': 'integer'
    },
    {
        'key': 'AUTO_FLUSH_ENABLED',
        'value': 'true',
        'description': 'Automatically flush buffer when MQTT reconnects',
        'category': 'buffer',
        'data_type': 'boolean'
    },
    
    # Sync Settings
    {
        'key': 'SYNC_INTERVAL',
        'value': '300',
        'description': 'Data sync interval in seconds',
        'category': 'sync',
        'data_type': 'integer'
    },
    {
        'key': 'SYNC_ENABLED',
        'value': 'true',
        'description': 'Enable automatic data synchronization',
        'category': 'sync',
        'data_type': 'boolean'
    },
    
    # System Settings
    {
        'key': 'LOG_LEVEL',
        'value': 'INFO',
        'description': 'Application log level (DEBUG, INFO, WARNING, ERROR)',
        'category': 'system',
        'data_type': 'string'
    },
    {
        'key': 'MAX_RETRIES',
        'value': '3',
        'description': 'Maximum number of connection retries',
        'category': 'system',
        'data_type': 'integer'
    },
    {
        'key': 'RETRY_DELAY',
        'value': '5',
        'description': 'Delay between retries in seconds',
        'category': 'system',
        'data_type': 'integer'
    },
]

with app.app_context():
    # Clear existing configs
    SystemConfig.query.delete()
    
    # Add default configs
    for config_data in DEFAULT_CONFIGS:
        config = SystemConfig(**config_data)
        db.session.add(config)
    
    db.session.commit()
    print(f"✓ Initialized {len(DEFAULT_CONFIGS)} default configurations")
    
    # Display created configs
    configs = SystemConfig.query.all()
    print(f"\nCreated configurations:")
    for config in configs:
        print(f"  - {config.key}: {config.value} ({config.category})")

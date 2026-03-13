#!/usr/bin/env python3
"""Initialize default system configurations - Simple Version"""

import sys
import os

# Add backend to path
sys.path.insert(0, '/home/saniyachavani/Documents/Precision_Pulse/backend')

from app import create_app
from app.models import db
from app.models.system_config import SystemConfig

app = create_app()

DEFAULT_CONFIGS = [
    ('MQTT_BROKER', 'localhost', 'MQTT broker hostname or IP address', 'mqtt', 'string'),
    ('MQTT_PORT', '18883', 'MQTT broker port', 'mqtt', 'integer'),
    ('MQTT_USE_TLS', 'true', 'Use TLS for MQTT connection', 'mqtt', 'boolean'),
    ('TELEMETRY_INTERVAL', '2', 'Telemetry data push interval in seconds', 'telemetry', 'integer'),
    ('HEARTBEAT_INTERVAL', '60', 'Heartbeat interval in seconds', 'telemetry', 'integer'),
    ('BUFFER_SIZE', '10000', 'Maximum number of records to buffer when offline', 'buffer', 'integer'),
    ('AUTO_FLUSH_ENABLED', 'true', 'Automatically flush buffer when MQTT reconnects', 'buffer', 'boolean'),
    ('SYNC_INTERVAL', '300', 'Data sync interval in seconds', 'sync', 'integer'),
    ('SYNC_ENABLED', 'true', 'Enable automatic data synchronization', 'sync', 'boolean'),
    ('LOG_LEVEL', 'INFO', 'Application log level (DEBUG, INFO, WARNING, ERROR)', 'system', 'string'),
    ('MAX_RETRIES', '3', 'Maximum number of connection retries', 'system', 'integer'),
    ('RETRY_DELAY', '5', 'Delay between retries in seconds', 'system', 'integer'),
]

with app.app_context():
    try:
        # Check if configs already exist
        existing_count = SystemConfig.query.count()
        if existing_count > 0:
            print(f"✓ {existing_count} configurations already exist")
            print("\nExisting configurations:")
            configs = SystemConfig.query.all()
            for config in configs:
                print(f"  - {config.key}: {config.value} ({config.category})")
            sys.exit(0)
        
        # Add default configs
        for key, value, description, category, data_type in DEFAULT_CONFIGS:
            config = SystemConfig(
                key=key,
                value=value,
                description=description,
                category=category,
                data_type=data_type
            )
            db.session.add(config)
        
        db.session.commit()
        print(f"✓ Initialized {len(DEFAULT_CONFIGS)} default configurations")
        
        # Display created configs
        configs = SystemConfig.query.all()
        print(f"\nCreated configurations:")
        for config in configs:
            print(f"  - {config.key}: {config.value} ({config.category})")
        
    except Exception as e:
        db.session.rollback()
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

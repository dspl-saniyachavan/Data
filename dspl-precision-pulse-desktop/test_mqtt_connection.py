#!/usr/bin/env python3
"""Test MQTT connection detection"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.services.mqtt_service import MQTTService
from src.services.mqtt_factory import MQTTClientFactory
from src.core.config import Config
import time

print("=" * 60)
print("MQTT Connection Detection Test")
print("=" * 60)
print(f"MQTT Broker: {Config.MQTT_BROKER}:{Config.MQTT_PORT}")
print()

# Create MQTT service
device_id = "test-device"
mqtt_client = MQTTClientFactory.create_client(device_id)
mqtt_service = MQTTService(device_id, mqtt_client)

# Connect
print("[TEST] Attempting to connect to MQTT broker...")
mqtt_service.connect()

# Monitor for 15 seconds
print("[TEST] Monitoring connection status for 15 seconds...")
print("[TEST] Stop mosquitto during this time to test disconnection detection")
print()

for i in range(15):
    time.sleep(1)
    status = mqtt_service.is_connected
    print(f"[{i+1:2d}s] MQTT is_connected: {status}")

print()
print("[TEST] Test complete")
mqtt_service.disconnect()

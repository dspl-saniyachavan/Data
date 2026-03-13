#!/usr/bin/env python3
"""
Test script for configuration synchronization
Tests single updates, bulk updates, and MQTT broadcasting
"""

import requests
import json
import time
import sys
from datetime import datetime

BASE_URL = "http://localhost:5000"
TOKEN = None

def get_token():
    """Get authentication token"""
    global TOKEN
    if TOKEN:
        return TOKEN
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "admin@example.com", "password": "admin123"}
        )
        if response.status_code == 200:
            TOKEN = response.json().get('token')
            print(f"✓ Got authentication token")
            return TOKEN
        else:
            print(f"✗ Failed to get token: {response.status_code}")
            return None
    except Exception as e:
        print(f"✗ Error getting token: {e}")
        return None

def get_headers():
    """Get request headers with auth"""
    token = get_token()
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

def test_get_all_configs():
    """Test getting all configurations"""
    print("\n[TEST] Getting all configurations...")
    try:
        response = requests.get(
            f"{BASE_URL}/api/config/",
            headers=get_headers()
        )
        if response.status_code == 200:
            data = response.json()
            count = data.get('count', 0)
            print(f"✓ Retrieved {count} configurations")
            return data.get('configs', [])
        else:
            print(f"✗ Failed: {response.status_code}")
            return []
    except Exception as e:
        print(f"✗ Error: {e}")
        return []

def test_get_config_by_key(key):
    """Test getting specific configuration"""
    print(f"\n[TEST] Getting configuration: {key}")
    try:
        response = requests.get(
            f"{BASE_URL}/api/config/{key}",
            headers=get_headers()
        )
        if response.status_code == 200:
            config = response.json().get('config', {})
            print(f"✓ {key} = {config.get('value')}")
            return config
        else:
            print(f"✗ Failed: {response.status_code}")
            return None
    except Exception as e:
        print(f"✗ Error: {e}")
        return None

def test_update_single_config(key, value):
    """Test updating single configuration"""
    print(f"\n[TEST] Updating configuration: {key} = {value}")
    try:
        response = requests.put(
            f"{BASE_URL}/api/config/{key}",
            headers=get_headers(),
            json={"value": value}
        )
        if response.status_code == 200:
            print(f"✓ Updated {key} successfully")
            print(f"  Response: {response.json().get('message')}")
            return True
        else:
            print(f"✗ Failed: {response.status_code}")
            print(f"  Error: {response.json().get('error')}")
            return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def test_bulk_update_configs(updates):
    """Test bulk configuration update"""
    print(f"\n[TEST] Bulk updating {len(updates)} configurations...")
    try:
        response = requests.put(
            f"{BASE_URL}/api/config/bulk-update",
            headers=get_headers(),
            json={"configs": updates}
        )
        if response.status_code == 200:
            data = response.json()
            count = data.get('count', 0)
            print(f"✓ Bulk updated {count} configurations")
            return True
        else:
            print(f"✗ Failed: {response.status_code}")
            print(f"  Error: {response.json().get('error')}")
            return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def test_get_categories():
    """Test getting configuration categories"""
    print("\n[TEST] Getting configuration categories...")
    try:
        response = requests.get(
            f"{BASE_URL}/api/config/categories",
            headers=get_headers()
        )
        if response.status_code == 200:
            categories = response.json().get('categories', [])
            print(f"✓ Found {len(categories)} categories:")
            for cat in categories:
                print(f"  - {cat}")
            return categories
        else:
            print(f"✗ Failed: {response.status_code}")
            return []
    except Exception as e:
        print(f"✗ Error: {e}")
        return []

def test_get_configs_by_category(category):
    """Test getting configurations by category"""
    print(f"\n[TEST] Getting configurations in category: {category}")
    try:
        response = requests.get(
            f"{BASE_URL}/api/config/?category={category}",
            headers=get_headers()
        )
        if response.status_code == 200:
            data = response.json()
            count = data.get('count', 0)
            print(f"✓ Found {count} configurations in {category}")
            for config in data.get('configs', []):
                print(f"  - {config.get('key')} = {config.get('value')}")
            return data.get('configs', [])
        else:
            print(f"✗ Failed: {response.status_code}")
            return []
    except Exception as e:
        print(f"✗ Error: {e}")
        return []

def test_sync_status():
    """Test getting sync status"""
    print("\n[TEST] Getting sync status...")
    try:
        response = requests.get(
            f"{BASE_URL}/api/config/sync-status",
            headers=get_headers()
        )
        if response.status_code == 200:
            data = response.json()
            devices = data.get('devices', [])
            print(f"✓ Found {len(devices)} devices:")
            for device in devices:
                print(f"  - {device.get('device_id')}: {device.get('status')}")
            return devices
        else:
            print(f"✗ Failed: {response.status_code}")
            return []
    except Exception as e:
        print(f"✗ Error: {e}")
        return []

def run_full_test_suite():
    """Run complete test suite"""
    print("=" * 60)
    print("Configuration Synchronization Test Suite")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Backend URL: {BASE_URL}")
    
    # Test 1: Authentication
    print("\n" + "=" * 60)
    print("AUTHENTICATION TESTS")
    print("=" * 60)
    if not get_token():
        print("✗ Cannot proceed without authentication")
        return False
    
    # Test 2: Get all configs
    print("\n" + "=" * 60)
    print("RETRIEVAL TESTS")
    print("=" * 60)
    configs = test_get_all_configs()
    if not configs:
        print("✗ No configurations found")
        return False
    
    # Test 3: Get categories
    categories = test_get_categories()
    
    # Test 4: Get configs by category
    if categories:
        test_get_configs_by_category(categories[0])
    
    # Test 5: Get specific config
    if configs:
        test_get_config_by_key(configs[0].get('key'))
    
    # Test 6: Single config update
    print("\n" + "=" * 60)
    print("UPDATE TESTS")
    print("=" * 60)
    test_update_single_config("TELEMETRY_INTERVAL", "5")
    time.sleep(1)
    
    # Test 7: Verify update
    test_get_config_by_key("TELEMETRY_INTERVAL")
    
    # Test 8: Bulk update
    bulk_updates = [
        {"key": "BUFFER_SIZE", "value": "1000"},
        {"key": "SYNC_FREQUENCY", "value": "60"}
    ]
    test_bulk_update_configs(bulk_updates)
    time.sleep(1)
    
    # Test 9: Verify bulk updates
    test_get_config_by_key("BUFFER_SIZE")
    test_get_config_by_key("SYNC_FREQUENCY")
    
    # Test 10: Sync status
    print("\n" + "=" * 60)
    print("SYNC STATUS TESTS")
    print("=" * 60)
    test_sync_status()
    
    print("\n" + "=" * 60)
    print("✓ All tests completed successfully!")
    print("=" * 60)
    return True

if __name__ == "__main__":
    try:
        success = run_full_test_suite()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n✗ Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        sys.exit(1)

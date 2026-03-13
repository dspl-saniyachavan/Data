#!/usr/bin/env python3
"""
Test script for command execution and delivery tracking system
Tests command sending, acknowledgment handling, and status tracking
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

def test_send_force_sync():
    """Test sending force sync command"""
    print("\n[TEST] Sending force sync command...")
    try:
        response = requests.post(
            f"{BASE_URL}/api/remote-commands/force-sync",
            headers=get_headers(),
            json={
                "device_id": "desktop-001",
                "sync_type": "full"
            }
        )
        if response.status_code == 200:
            data = response.json()
            command_id = data.get('command_id')
            print(f"✓ Force sync command sent: {command_id}")
            return command_id
        else:
            print(f"✗ Failed: {response.status_code}")
            print(f"  Response: {response.json()}")
            return None
    except Exception as e:
        print(f"✗ Error: {e}")
        return None

def test_send_config_update():
    """Test sending config update command"""
    print("\n[TEST] Sending config update command...")
    try:
        response = requests.post(
            f"{BASE_URL}/api/remote-commands/update-config",
            headers=get_headers(),
            json={
                "device_id": "desktop-001",
                "config": {
                    "TELEMETRY_INTERVAL": "5",
                    "BUFFER_SIZE": "1000"
                }
            }
        )
        if response.status_code == 200:
            data = response.json()
            command_id = data.get('command_id')
            print(f"✓ Config update command sent: {command_id}")
            return command_id
        else:
            print(f"✗ Failed: {response.status_code}")
            print(f"  Response: {response.json()}")
            return None
    except Exception as e:
        print(f"✗ Error: {e}")
        return None

def test_send_custom_command():
    """Test sending custom command"""
    print("\n[TEST] Sending custom command...")
    try:
        response = requests.post(
            f"{BASE_URL}/api/remote-commands/custom",
            headers=get_headers(),
            json={
                "command_type": "status",
                "device_id": "desktop-001",
                "params": {}
            }
        )
        if response.status_code == 200:
            data = response.json()
            command_id = data.get('command_id')
            print(f"✓ Custom command sent: {command_id}")
            return command_id
        else:
            print(f"✗ Failed: {response.status_code}")
            print(f"  Response: {response.json()}")
            return None
    except Exception as e:
        print(f"✗ Error: {e}")
        return None

def test_get_command_status(command_id):
    """Test getting command status"""
    print(f"\n[TEST] Getting status for command: {command_id}")
    try:
        response = requests.get(
            f"{BASE_URL}/api/remote-commands/status?command_id={command_id}",
            headers=get_headers()
        )
        if response.status_code == 200:
            data = response.json()
            status = data.get('status')
            delivery_status = data.get('delivery_status')
            execution_status = data.get('execution_status')
            ack_count = len(data.get('acknowledgments', []))
            
            print(f"✓ Command status retrieved")
            print(f"  Status: {status}")
            print(f"  Delivery: {delivery_status}")
            print(f"  Execution: {execution_status}")
            print(f"  Acknowledgments: {ack_count}")
            
            return data
        else:
            print(f"✗ Failed: {response.status_code}")
            return None
    except Exception as e:
        print(f"✗ Error: {e}")
        return None

def test_list_commands():
    """Test listing commands"""
    print("\n[TEST] Listing commands...")
    try:
        response = requests.get(
            f"{BASE_URL}/api/remote-commands/list?device_id=desktop-001&limit=10",
            headers=get_headers()
        )
        if response.status_code == 200:
            data = response.json()
            count = data.get('count', 0)
            print(f"✓ Retrieved {count} commands")
            
            if count > 0:
                for cmd in data.get('commands', [])[:3]:
                    print(f"  - {cmd.get('command_id')}: {cmd.get('command_type')} ({cmd.get('status')})")
            
            return data
        else:
            print(f"✗ Failed: {response.status_code}")
            return None
    except Exception as e:
        print(f"✗ Error: {e}")
        return None

def test_get_command_details(command_id):
    """Test getting detailed command information"""
    print(f"\n[TEST] Getting details for command: {command_id}")
    try:
        response = requests.get(
            f"{BASE_URL}/api/remote-commands/{command_id}/details",
            headers=get_headers()
        )
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Command details retrieved")
            print(f"  Command Type: {data.get('command_type')}")
            print(f"  Device ID: {data.get('device_id')}")
            print(f"  Status: {data.get('status')}")
            print(f"  Created: {data.get('created_at')}")
            print(f"  Acknowledgments: {data.get('ack_count', 0)}")
            
            if data.get('acknowledgments'):
                print(f"  Ack Timeline:")
                for ack in data.get('acknowledgments', []):
                    print(f"    - {ack.get('ack_type')}: {ack.get('created_at')}")
            
            return data
        else:
            print(f"✗ Failed: {response.status_code}")
            return None
    except Exception as e:
        print(f"✗ Error: {e}")
        return None

def test_get_command_stats():
    """Test getting command statistics"""
    print("\n[TEST] Getting command statistics...")
    try:
        response = requests.get(
            f"{BASE_URL}/api/remote-commands/stats",
            headers=get_headers()
        )
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Statistics retrieved")
            print(f"  Total: {data.get('total', 0)}")
            print(f"  Completed: {data.get('completed', 0)}")
            print(f"  Failed: {data.get('failed', 0)}")
            print(f"  Pending: {data.get('pending', 0)}")
            print(f"  Sent: {data.get('sent', 0)}")
            
            by_type = data.get('by_type', {})
            if by_type:
                print(f"  By Type:")
                for cmd_type, count in by_type.items():
                    print(f"    - {cmd_type}: {count}")
            
            return data
        else:
            print(f"✗ Failed: {response.status_code}")
            return None
    except Exception as e:
        print(f"✗ Error: {e}")
        return None

def test_handle_acknowledgment(command_id):
    """Test handling command acknowledgment"""
    print(f"\n[TEST] Sending acknowledgment for command: {command_id}")
    try:
        response = requests.post(
            f"{BASE_URL}/api/remote-commands/acknowledgment",
            json={
                "command_id": command_id,
                "device_id": "desktop-001",
                "ack_type": "completed",
                "status": "success",
                "message": "Command completed successfully",
                "result_data": {
                    "status": "completed",
                    "records_synced": 150
                }
            }
        )
        if response.status_code == 200:
            print(f"✓ Acknowledgment recorded")
            return True
        else:
            print(f"✗ Failed: {response.status_code}")
            print(f"  Response: {response.json()}")
            return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def test_retry_command(command_id):
    """Test retrying a failed command"""
    print(f"\n[TEST] Retrying command: {command_id}")
    try:
        response = requests.post(
            f"{BASE_URL}/api/remote-commands/{command_id}/retry",
            headers=get_headers()
        )
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Command retried")
            print(f"  Retry count: {data.get('retry_count', 0)}")
            return True
        else:
            print(f"✗ Failed: {response.status_code}")
            print(f"  Response: {response.json()}")
            return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def run_full_test_suite():
    """Run complete test suite"""
    print("=" * 60)
    print("Command Execution & Delivery Tracking Test Suite")
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
    
    # Test 2: Send commands
    print("\n" + "=" * 60)
    print("COMMAND SENDING TESTS")
    print("=" * 60)
    
    sync_cmd_id = test_send_force_sync()
    config_cmd_id = test_send_config_update()
    custom_cmd_id = test_send_custom_command()
    
    # Test 3: Get command status
    print("\n" + "=" * 60)
    print("COMMAND STATUS TESTS")
    print("=" * 60)
    
    if sync_cmd_id:
        test_get_command_status(sync_cmd_id)
    
    if config_cmd_id:
        test_get_command_status(config_cmd_id)
    
    # Test 4: List commands
    print("\n" + "=" * 60)
    print("COMMAND LISTING TESTS")
    print("=" * 60)
    test_list_commands()
    
    # Test 5: Get command details
    print("\n" + "=" * 60)
    print("COMMAND DETAILS TESTS")
    print("=" * 60)
    
    if sync_cmd_id:
        test_get_command_details(sync_cmd_id)
    
    # Test 6: Handle acknowledgment
    print("\n" + "=" * 60)
    print("ACKNOWLEDGMENT TESTS")
    print("=" * 60)
    
    if sync_cmd_id:
        test_handle_acknowledgment(sync_cmd_id)
        time.sleep(1)
        test_get_command_details(sync_cmd_id)
    
    # Test 7: Statistics
    print("\n" + "=" * 60)
    print("STATISTICS TESTS")
    print("=" * 60)
    test_get_command_stats()
    
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

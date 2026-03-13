#!/usr/bin/env python3
"""Test MQTT status broadcasting to Socket.IO clients"""

import socketio
import time
import threading
from app import create_app

# Create Flask app
app = create_app()
sio = app.socketio

# Track received events
received_events = []

# Create Socket.IO client
client = socketio.Client()

@client.on('connect')
def on_connect():
    print('[CLIENT] Connected to server')

@client.on('mqtt_status')
def on_mqtt_status(data):
    print(f'[CLIENT] Received MQTT status: {data}')
    received_events.append(data)

@client.on('connection_response')
def on_connection_response(data):
    print(f'[CLIENT] Connection response: {data}')

def run_server():
    """Run Flask-SocketIO server"""
    print('[SERVER] Starting server...')
    sio.run(app, host='127.0.0.1', port=5001, debug=False, use_reloader=False)

def test_client():
    """Test Socket.IO client connection"""
    time.sleep(2)  # Wait for server to start
    
    print('[CLIENT] Connecting to server...')
    try:
        client.connect('http://127.0.0.1:5001')
        
        # Wait for events
        time.sleep(3)
        
        # Check MQTT status via API
        import requests
        response = requests.get('http://127.0.0.1:5001/api/mqtt/status')
        print(f'[API] MQTT status: {response.json()}')
        
        # Wait for broadcast
        time.sleep(2)
        
        print(f'\n[RESULT] Received {len(received_events)} mqtt_status events')
        for event in received_events:
            print(f'  - {event}')
        
        client.disconnect()
        
    except Exception as e:
        print(f'[CLIENT] Error: {e}')
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    # Start server in background thread
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    
    # Run client test
    test_client()
    
    print('\n[TEST] Complete')

#!/usr/bin/env python3
"""Test buffer route reading from SQLite"""

import sys
sys.path.insert(0, '/home/saniyachavani/Documents/Precision_Pulse/backend')

from app import create_app
import json

app = create_app()

with app.test_client() as client:
    response = client.get('/api/buffer/telemetry/latest')
    print(f'Status: {response.status_code}')
    print(f'Response: {response.get_json()}')
    
    data = response.get_json()
    if data:
        print(f"\nBuffer count: {data.get('count', 0)}")
        for record in data.get('buffer', [])[:3]:
            print(f"  - {record['parameter_name']}: {record['value']} {record['unit']}")

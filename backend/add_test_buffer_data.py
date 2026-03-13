#!/usr/bin/env python3
"""Add test buffer data to database"""

from app import create_app
from app.models import db
from app.models.telemetry_buffer import TelemetryBuffer
from datetime import datetime

app = create_app()

with app.app_context():
    # Clear existing buffer
    TelemetryBuffer.query.delete()
    
    # Add test data
    test_data = [
        {'parameter_id': 1, 'parameter_name': 'Temperature', 'value': 25.5, 'unit': '°C'},
        {'parameter_id': 2, 'parameter_name': 'Humidity', 'value': 65.2, 'unit': '%'},
        {'parameter_id': 3, 'parameter_name': 'Pressure', 'value': 1013.25, 'unit': 'hPa'},
    ]
    
    for data in test_data:
        record = TelemetryBuffer(
            device_id='test-device',
            parameter_id=data['parameter_id'],
            parameter_name=data['parameter_name'],
            value=data['value'],
            unit=data['unit'],
            timestamp=datetime.utcnow(),
            synced=False
        )
        db.session.add(record)
    
    db.session.commit()
    print(f"Added {len(test_data)} test buffer records")

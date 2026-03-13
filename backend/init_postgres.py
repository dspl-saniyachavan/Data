#!/usr/bin/env python3
"""
Initialize PostgreSQL database for Precision Pulse
"""
import os
import sys
from app import create_app
from app.models import db
from app.models.parameter import Parameter

def init_database():
    """Initialize the database with tables and default data"""
    app = create_app()
    
    with app.app_context():
        try:
            # Drop all tables and recreate (for development)
            print("Dropping existing tables...")
            db.drop_all()
            
            print("Creating tables...")
            db.create_all()
            
            # Create default parameters
            default_parameters = [
                {
                    'name': 'Temperature',
                    'unit': '°C',
                    'description': 'Ambient temperature measurement'
                },
                {
                    'name': 'Pressure',
                    'unit': 'kPa',
                    'description': 'System pressure measurement'
                },
                {
                    'name': 'Flow Rate',
                    'unit': 'L/min',
                    'description': 'Liquid flow rate measurement'
                },
                {
                    'name': 'Humidity',
                    'unit': '%',
                    'description': 'Relative humidity measurement'
                },
                {
                    'name': 'Voltage',
                    'unit': 'V',
                    'description': 'System voltage measurement'
                }
            ]
            
            print("Creating default parameters...")
            for param_data in default_parameters:
                parameter = Parameter(**param_data)
                db.session.add(parameter)
            
            db.session.commit()
            print(f"Successfully created {len(default_parameters)} default parameters")
            
            # Verify creation
            count = Parameter.query.count()
            print(f"Total parameters in database: {count}")
            
        except Exception as e:
            print(f"Error initializing database: {e}")
            db.session.rollback()
            sys.exit(1)

if __name__ == '__main__':
    init_database()
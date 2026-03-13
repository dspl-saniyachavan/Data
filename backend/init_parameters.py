#!/usr/bin/env python3
"""Initialize PostgreSQL database with parameters table and default data"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.models import db
from app.models.parameter import Parameter

def init_database():
    """Initialize database with tables and default parameters"""
    app = create_app()
    
    with app.app_context():
        # Create all tables
        db.create_all()
        print("✓ Database tables created")
        
        # Check if parameters already exist
        existing_count = Parameter.query.count()
        if existing_count > 0:
            print(f"✓ Database already has {existing_count} parameters")
            return
        
        # Define 3 default parameters
        default_parameters = [
            Parameter(
                name='Temperature',
                unit='°C',
                description='Ambient temperature sensor reading',
                enabled=True,
                is_default=True
            ),
            Parameter(
                name='Pressure',
                unit='kPa',
                description='System pressure measurement',
                enabled=True,
                is_default=True
            ),
            Parameter(
                name='Flow Rate',
                unit='L/s',
                description='Liquid flow rate measurement',
                enabled=True,
                is_default=True
            )
        ]
        
        # Add parameters to database
        for param in default_parameters:
            db.session.add(param)
            print(f"✓ Added parameter: {param.name}")
        
        db.session.commit()
        print("✓ Default parameters initialized successfully!")

if __name__ == '__main__':
    try:
        init_database()
        print("\n✓ Database initialization complete!")
    except Exception as e:
        print(f"✗ Error: {e}")
        sys.exit(1)

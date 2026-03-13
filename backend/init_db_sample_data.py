#!/usr/bin/env python3
"""
Database Initialization Script
Populates PostgreSQL database with sample data for testing and development
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app
from app.models import db
from app.models.user import User
from app.models.parameter import Parameter
from datetime import datetime


def init_database():
    """Initialize database with sample data"""
    app = create_app()
    
    with app.app_context():
        print("=" * 60)
        print("Database Initialization")
        print("=" * 60)
        
        # Check if tables exist
        inspector = db.inspect(db.engine)
        tables = inspector.get_table_names()
        
        if not tables:
            print("\n✗ No tables found. Creating tables...")
            db.create_all()
            print("✓ Tables created successfully")
        else:
            print(f"\n✓ Found {len(tables)} existing tables")
        
        # Check existing data
        user_count = User.query.count()
        param_count = Parameter.query.count()
        
        print(f"\nCurrent data:")
        print(f"  Users: {user_count}")
        print(f"  Parameters: {param_count}")
        
        # Initialize users if empty
        if user_count == 0:
            print("\n✓ Initializing users...")
            users_data = [
                ('admin@precisionpulse.com', 'Admin User', 'admin123', 'admin'),
                ('user@precisionpulse.com', 'Regular User', 'user123', 'user'),
                ('client@precisionpulse.com', 'Client User', 'client123', 'client')
            ]
            
            for email, name, password, role in users_data:
                user = User(email=email, name=name, role=role, is_active=True)
                user.set_password(password)
                db.session.add(user)
            
            db.session.commit()
            print(f"  ✓ Created {len(users_data)} users")
            print("\n  Default credentials:")
            for email, name, password, role in users_data:
                print(f"    - {email} / {password}")
        
        # Initialize parameters if empty
        if param_count == 0:
            print("\n✓ Initializing parameters...")
            parameters = [
                Parameter(
                    name='Temperature',
                    unit='°C',
                    description='Room temperature sensor',
                    enabled=True
                ),
                Parameter(
                    name='Humidity',
                    unit='%',
                    description='Relative humidity sensor',
                    enabled=True
                ),
                Parameter(
                    name='Pressure',
                    unit='hPa',
                    description='Atmospheric pressure sensor',
                    enabled=True
                ),
                Parameter(
                    name='CO2 Level',
                    unit='ppm',
                    description='Carbon dioxide concentration',
                    enabled=True
                ),
                Parameter(
                    name='Light Intensity',
                    unit='lux',
                    description='Ambient light level',
                    enabled=True
                ),
                Parameter(
                    name='Air Quality',
                    unit='AQI',
                    description='Air quality index',
                    enabled=True
                )
            ]
            
            for param in parameters:
                db.session.add(param)
            
            db.session.commit()
            print(f"  ✓ Created {len(parameters)} parameters")
        
        # Verify data
        print("\n" + "=" * 60)
        print("Verification")
        print("=" * 60)
        
        final_users = User.query.count()
        final_params = Parameter.query.count()
        
        print(f"\nFinal data:")
        print(f"  Users: {final_users}")
        print(f"  Parameters: {final_params}")
        
        # List users
        print("\nUsers:")
        for user in User.query.all():
            print(f"  - {user.email} ({user.role})")
        
        # List parameters
        print("\nParameters:")
        for param in Parameter.query.all():
            print(f"  - {param.name} ({param.unit})")
        
        print("\n" + "=" * 60)
        print("✓ Database initialization complete!")
        print("=" * 60)


if __name__ == '__main__':
    try:
        init_database()
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

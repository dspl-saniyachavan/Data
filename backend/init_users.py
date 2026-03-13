#!/usr/bin/env python
"""
Script to add default admin user to database
Run this after starting the backend
"""

import sys
sys.path.insert(0, '/home/saniyachavani/Documents/Precision_Pulse/backend')

from app import create_app
from app.models import db
from app.models.user import User

app = create_app()

with app.app_context():
    # Check if admin user exists
    admin = User.query.filter_by(email='admin@precisionpulse.com').first()
    
    if admin:
        print("✓ Admin user already exists")
    else:
        # Create admin user
        admin = User(
            email='admin@precisionpulse.com',
            name='Admin User',
            role='admin',
            is_active=True
        )
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print("✓ Admin user created: admin@precisionpulse.com / admin123")
    
    # Check if regular user exists
    user = User.query.filter_by(email='user@precisionpulse.com').first()
    
    if user:
        print("✓ Regular user already exists")
    else:
        # Create regular user
        user = User(
            email='user@precisionpulse.com',
            name='Regular User',
            role='user',
            is_active=True
        )
        user.set_password('user123')
        db.session.add(user)
        db.session.commit()
        print("✓ Regular user created: user@precisionpulse.com / user123")
    
    print("\n✓ Database initialized with default users")

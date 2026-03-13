#!/bin/bash

# Start PostgreSQL service
sudo service postgresql start

# Create database as postgres user
sudo -u postgres createdb precision_pulse 2>/dev/null || echo "Database may already exist"

# Initialize tables and users
cd /home/saniyachavani/Documents/Precision_Pulse/backend
python3 init_db.py

echo "✓ PostgreSQL setup complete"

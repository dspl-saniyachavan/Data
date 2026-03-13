#!/bin/bash

# Precision Pulse Backend Startup Script

echo "Starting Precision Pulse Backend..."

# Check if PostgreSQL is running
if ! pg_isready -q; then
    echo "PostgreSQL is not running. Please start PostgreSQL first."
    echo "On Ubuntu/Debian: sudo systemctl start postgresql"
    echo "On macOS with Homebrew: brew services start postgresql"
    exit 1
fi

# Check if database exists, create if not
DB_NAME="precision_pulse"
DB_USER="postgres"

echo "Checking if database '$DB_NAME' exists..."
if ! psql -U $DB_USER -lqt | cut -d \| -f 1 | grep -qw $DB_NAME; then
    echo "Creating database '$DB_NAME'..."
    createdb -U $DB_USER $DB_NAME
    echo "Database created successfully."
else
    echo "Database '$DB_NAME' already exists."
fi

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Initialize database tables
echo "Initializing database tables..."
python3 init_postgres.py

# Start Flask server
echo "Starting Flask server on http://localhost:5000..."
python3 run.py
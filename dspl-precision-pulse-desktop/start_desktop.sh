#!/bin/bash

# Desktop App Launcher with Debug

cd /home/saniyachavani/Documents/Precision_Pulse/dspl-precision-pulse-desktop

echo "╔════════════════════════════════════════════╗"
echo "║   PrecisionPulse Desktop App Launcher      ║"
echo "╚════════════════════════════════════════════╝"
echo ""

# Check dependencies
echo "Checking dependencies..."

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "✗ Python3 not found"
    exit 1
fi
echo "✓ Python3: $(python3 --version)"

# Check PySide6
if ! python3 -c "import PySide6" 2>/dev/null; then
    echo "✗ PySide6 not installed"
    echo "Installing PySide6..."
    pip3 install PySide6
fi
echo "✓ PySide6 installed"

# Check other dependencies
echo "Checking other dependencies..."
python3 -c "
import sys
try:
    import paho.mqtt.client as mqtt
    import requests
    import argon2
    print('✓ All dependencies OK')
except ImportError as e:
    print(f'✗ Missing dependency: {e}')
    sys.exit(1)
"

if [ $? -ne 0 ]; then
    echo "Installing missing dependencies..."
    pip3 install -r requirements.txt
fi

echo ""
echo "Checking backend connection..."
if curl -s http://localhost:5000/api/health > /dev/null 2>&1; then
    echo "✓ Backend is running"
else
    echo "✗ Backend is NOT running"
    echo "Please start backend first:"
    echo "  cd /home/saniyachavani/Documents/Precision_Pulse"
    echo "  ./debug_and_start.sh"
    exit 1
fi

echo ""
echo "Starting Desktop App..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Run the app
python3 main.py 2>&1 | tee /tmp/desktop_app.log

echo ""
echo "Desktop app closed."
echo "Log saved to: /tmp/desktop_app.log"

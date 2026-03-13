#!/bin/bash

# Frontend Startup Script with Node Version Check

cd /home/saniyachavani/Documents/Precision_Pulse/dspl-precision-pulse-frontend

echo "╔════════════════════════════════════════════╗"
echo "║   PrecisionPulse Frontend Startup          ║"
echo "╚════════════════════════════════════════════╝"
echo ""

# Check Node version
NODE_VERSION=$(node --version | cut -d'v' -f2 | cut -d'.' -f1)
echo "Node.js version: $(node --version)"

if [ "$NODE_VERSION" -lt 18 ]; then
    echo "❌ Error: Node.js 18 or higher is required"
    echo "Current version: $(node --version)"
    echo ""
    echo "Please upgrade Node.js:"
    echo "  Using nvm: nvm install 20 && nvm use 20"
    echo "  Or download from: https://nodejs.org/"
    exit 1
fi

echo "✓ Node.js version OK"
echo ""

# Kill existing processes
echo "Cleaning up existing processes..."
pkill -f "next dev" 2>/dev/null
lsof -ti:3000 | xargs kill -9 2>/dev/null
echo "✓ Cleanup complete"
echo ""

# Clean cache
echo "Cleaning cache..."
rm -rf .next/dev/lock .next/cache 2>/dev/null
echo "✓ Cache cleaned"
echo ""

# Check dependencies
echo "Checking dependencies..."
if [ ! -d "node_modules" ]; then
    echo "Installing dependencies..."
    npm install
fi
echo "✓ Dependencies OK"
echo ""

# Start frontend
echo "Starting Next.js development server..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📍 Frontend will be available at: http://localhost:3000"
echo ""
echo "Press Ctrl+C to stop"
echo ""

# Use exec to replace shell with npm process
exec npm run dev

#!/bin/bash

# Database Sync Master Script
# Syncs SQLite ↔ PostgreSQL and initializes all data

set -e

BACKEND_DIR="/home/saniyachavani/Documents/Precision_Pulse/backend"

echo "============================================================"
echo "PRECISION PULSE - DATABASE SYNC MASTER SCRIPT"
echo "============================================================"

cd "$BACKEND_DIR"

echo ""
echo "============================================================"
echo "[1/3] Mirror SQLite → PostgreSQL"
echo "============================================================"
python mirror_databases.py
echo "✓ Step 1 completed"

sleep 1

echo ""
echo "============================================================"
echo "[2/3] Initialize Default Users in PostgreSQL"
echo "============================================================"
python init_users.py
echo "✓ Step 2 completed"

sleep 1

echo ""
echo "============================================================"
echo "[3/3] Mirror PostgreSQL → SQLite"
echo "============================================================"
python mirror_databases_reverse.py
echo "✓ Step 3 completed"

echo ""
echo "============================================================"
echo "✓ ALL DATABASE SYNC COMPLETED SUCCESSFULLY"
echo "============================================================"
echo ""
echo "Next steps:"
echo "1. Start Backend:  cd $BACKEND_DIR && python run.py"
echo "2. Start Desktop:  cd $BACKEND_DIR/../dspl-precision-pulse-desktop && python main.py"
echo "3. Start Frontend: cd $BACKEND_DIR/../dspl-precision-pulse-frontend && npm run dev"
echo ""

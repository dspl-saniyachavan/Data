#!/bin/bash
# Environment Setup Script for Precision Pulse Parameter Management

echo "=========================================="
echo "Precision Pulse - Environment Setup"
echo "=========================================="

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Step 1: Check PostgreSQL
echo -e "\n${BLUE}[STEP 1]${NC} Checking PostgreSQL installation..."
if command -v psql &> /dev/null; then
    echo -e "${GREEN}✓${NC} PostgreSQL is installed"
    psql --version
else
    echo -e "${YELLOW}✗${NC} PostgreSQL not found. Please install PostgreSQL first."
    echo "  Ubuntu/Debian: sudo apt-get install postgresql postgresql-contrib"
    echo "  macOS: brew install postgresql"
    exit 1
fi

# Step 2: Create database
echo -e "\n${BLUE}[STEP 2]${NC} Creating PostgreSQL database..."
sudo -u postgres psql -c "CREATE DATABASE precision_pulse;" 2>/dev/null || echo "Database may already exist"
echo -e "${GREEN}✓${NC} Database ready"

# Step 3: Create .env file
echo -e "\n${BLUE}[STEP 3]${NC} Creating .env file..."
if [ ! -f ".env" ]; then
    cat > .env << EOF
# PostgreSQL Configuration
DATABASE_URL=postgresql://postgres:postgres@localhost/precision_pulse

# JWT Configuration
JWT_SECRET=precision-pulse-super-secret-jwt-key-2024-development-only
JWT_ALGORITHM=HS256
JWT_EXPIRATION=86400

# Flask Configuration
FLASK_ENV=development
FLASK_DEBUG=True
EOF
    echo -e "${GREEN}✓${NC} .env file created"
else
    echo -e "${YELLOW}!${NC} .env file already exists"
fi

# Step 4: Install Python dependencies
echo -e "\n${BLUE}[STEP 4]${NC} Installing Python dependencies..."
if command -v pip3 &> /dev/null; then
    pip3 install -r requirements.txt
    echo -e "${GREEN}✓${NC} Dependencies installed"
else
    echo -e "${YELLOW}✗${NC} pip3 not found. Please install Python 3 first."
    exit 1
fi

# Step 5: Initialize database
echo -e "\n${BLUE}[STEP 5]${NC} Initializing database with default parameters..."
python3 init_parameters.py
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓${NC} Database initialized successfully"
else
    echo -e "${YELLOW}✗${NC} Database initialization failed"
    exit 1
fi

# Step 6: Run tests
echo -e "\n${BLUE}[STEP 6]${NC} Running parameter tests..."
python3 test_parameters.py
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓${NC} All tests passed"
else
    echo -e "${YELLOW}✗${NC} Some tests failed"
fi

# Summary
echo -e "\n${BLUE}=========================================="
echo "Setup Complete!"
echo "==========================================${NC}"
echo -e "\n${GREEN}Next Steps:${NC}"
echo "1. Start the backend server:"
echo "   python3 run.py"
echo ""
echo "2. Access the frontend:"
echo "   http://localhost:3000/parameters"
echo ""
echo "3. Login with admin credentials:"
echo "   Email: admin@precisionpulse.com"
echo "   Password: admin123"
echo ""
echo -e "${YELLOW}Documentation:${NC}"
echo "- API Reference: PARAMETER_API.md"
echo "- Setup Guide: PARAMETER_SETUP.md"
echo "- Implementation: IMPLEMENTATION_SUMMARY.md"
echo "- Verification: VERIFICATION_CHECKLIST.md"

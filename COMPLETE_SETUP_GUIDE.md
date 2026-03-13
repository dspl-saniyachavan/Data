# Complete Setup & Troubleshooting Guide

## 🎯 Overview

This guide covers:
- ✅ CORS & Authentication fixes
- ✅ Frontend compilation fixes
- ✅ Backend setup
- ✅ Database setup
- ✅ Running the full stack
- ✅ Troubleshooting common issues

## 📋 Prerequisites

- Python 3.8+
- Node.js 16+
- PostgreSQL 12+
- npm or yarn
- Git

## 🚀 Quick Start (5 minutes)

### Terminal 1: Backend

```bash
cd backend
pip install -r requirements.txt
python run.py
```

Expected: `Running on http://127.0.0.1:5000`

### Terminal 2: Frontend

```bash
cd dspl-precision-pulse-frontend
npm install
npm run dev
```

Expected: `ready - started server on 0.0.0.0:3000`

### Terminal 3: Access Application

```
Frontend: http://localhost:3000
Backend API: http://localhost:5000
Swagger Docs: http://localhost:5000/api/docs
```

## 🔧 Detailed Setup

### Step 1: Backend Setup

```bash
cd backend

# Create virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cat > .env << EOF
DATABASE_URL=postgresql://postgres:postgres@localhost/precision_pulse
JWT_SECRET=precision-pulse-super-secret-jwt-key-2024-development-only
MQTT_BROKER=localhost
MQTT_PORT=18883
MQTT_USE_TLS=true
MQTT_CA_CERTS=config/ca.crt
EOF

# Initialize database
python -c "
from app import create_app, db
from app.models.user import User
import bcrypt

app = create_app()
with app.app_context():
    db.create_all()
    
    # Create default user if not exists
    user = User.query.filter_by(email='admin@example.com').first()
    if not user:
        hashed = bcrypt.hashpw(b'password123', bcrypt.gensalt()).decode()
        user = User(
            email='admin@example.com',
            name='Admin User',
            password_hash=hashed,
            role='admin'
        )
        db.session.add(user)
        db.session.commit()
        print('✅ Admin user created: admin@example.com / password123')
    else:
        print('✅ Admin user already exists')
"

# Start backend
python run.py
```

### Step 2: Frontend Setup

```bash
cd dspl-precision-pulse-frontend

# Create .env.local file
cat > .env.local << EOF
NEXT_PUBLIC_BACKEND_URL=http://localhost:5000
JWT_SECRET=precision-pulse-super-secret-jwt-key-2024-development-only
EOF

# Install dependencies
npm install

# Start dev server
npm run dev
```

### Step 3: Database Setup

```bash
# Create PostgreSQL database
createdb precision_pulse

# Or using psql
psql -U postgres -c "CREATE DATABASE precision_pulse;"

# Verify connection
psql -U postgres -d precision_pulse -c "SELECT 1;"
```

## ✅ Verification Checklist

### Backend

- [ ] Backend running on port 5000
- [ ] No errors in terminal
- [ ] Database connected
- [ ] Swagger docs accessible at http://localhost:5000/api/docs

### Frontend

- [ ] Frontend running on port 3000
- [ ] No compilation errors
- [ ] No errors in browser console (F12)
- [ ] Can access http://localhost:3000

### Integration

- [ ] Can login with admin@example.com / password123
- [ ] Redirected to dashboard after login
- [ ] Can see parameters and telemetry
- [ ] Socket.IO connected (check console)

## 🐛 Troubleshooting

### Backend Issues

#### Port 5000 Already in Use

```bash
# Find process using port 5000
lsof -i :5000

# Kill process
kill -9 <PID>

# Or use different port
python run.py --port 5001
```

#### Database Connection Error

```bash
# Check PostgreSQL is running
psql -U postgres -c "SELECT 1;"

# Verify DATABASE_URL in .env
cat .env | grep DATABASE_URL

# Test connection
python -c "
from sqlalchemy import create_engine
engine = create_engine('postgresql://postgres:postgres@localhost/precision_pulse')
with engine.connect() as conn:
    print('✅ Database connected')
"
```

#### Import Errors

```bash
# Reinstall dependencies
pip install --upgrade -r requirements.txt

# Check Python version
python --version  # Should be 3.8+

# Check virtual environment
which python  # Should show venv path
```

### Frontend Issues

#### Port 3000 Already in Use

```bash
# Find process using port 3000
lsof -i :3000

# Kill process
kill -9 <PID>

# Or use different port
npm run dev -- -p 3001
```

#### Module Not Found

```bash
# Clean install
rm -rf node_modules package-lock.json
npm install

# Verify node_modules
ls node_modules | grep socket.io-client
```

#### Compilation Errors

```bash
# Check TypeScript
npx tsc --noEmit

# Build to see all errors
npm run build

# Clear cache
rm -rf .next
npm run dev
```

#### CORS Errors

**Error:** "Access to XMLHttpRequest blocked by CORS policy"

**Solution:**
1. Verify backend is running
2. Check `.env.local` has correct BACKEND_URL
3. Verify CORS in `backend/app/__init__.py`
4. Restart both servers

### Login Issues

#### "Invalid credentials"

**Solution:**
1. Verify user exists in database
2. Check password is correct
3. Verify JWT_SECRET matches
4. Check backend logs

#### "Network error"

**Solution:**
1. Verify backend is running
2. Check network tab (F12)
3. Verify API endpoint URL
4. Check CORS headers

#### Infinite redirect loop

**Solution:**
1. Clear browser cookies
2. Check middleware logic
3. Verify token is being stored
4. Check browser console for errors

## 📊 Testing

### Test Login

```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"password123"}'
```

Expected response:
```json
{
  "token": "eyJ...",
  "user": {
    "id": 1,
    "email": "admin@example.com",
    "name": "Admin User",
    "role": "admin"
  }
}
```

### Test Protected Endpoint

```bash
TOKEN="your_token_here"

curl -X GET http://localhost:5000/api/parameters \
  -H "Authorization: Bearer $TOKEN"
```

### Test Swagger UI

1. Go to http://localhost:5000/api/docs
2. Click "Authorize"
3. Enter: `Bearer <token>`
4. Test endpoints

## 🔐 Security Checklist

- [ ] JWT_SECRET is strong and unique
- [ ] Database password is strong
- [ ] CORS origins are restricted
- [ ] HTTPS enabled in production
- [ ] Sensitive data not logged
- [ ] SQL injection prevention
- [ ] XSS protection enabled
- [ ] CSRF tokens used

## 📁 Project Structure

```
PrecisionpulseDocs/
├── backend/
│   ├── app/
│   │   ├── __init__.py          ← CORS configured
│   │   ├── routes/
│   │   ├── models/
│   │   ├── controllers/
│   │   └── services/
│   ├── config/
│   ├── requirements.txt
│   ├── run.py
│   └── .env
│
├── dspl-precision-pulse-frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── login/
│   │   │   ├── dashboard/
│   │   │   └── ...
│   │   ├── lib/
│   │   │   └── jwt.ts           ← Fixed
│   │   ├── middleware.ts        ← Updated
│   │   └── ...
│   ├── next.config.ts           ← Updated
│   ├── .env.local
│   └── package.json
│
├── CORS_AUTHENTICATION_FIX.md
├── FRONTEND_COMPILATION_FIX.md
├── QUICK_START.md
└── README.md
```

## 🎯 Common Workflows

### Add New User

```bash
python -c "
from app import create_app, db
from app.models.user import User
import bcrypt

app = create_app()
with app.app_context():
    hashed = bcrypt.hashpw(b'password123', bcrypt.gensalt()).decode()
    user = User(
        email='newuser@example.com',
        name='New User',
        password_hash=hashed,
        role='user'
    )
    db.session.add(user)
    db.session.commit()
    print('✅ User created')
"
```

### Reset Database

```bash
python -c "
from app import create_app, db

app = create_app()
with app.app_context():
    db.drop_all()
    db.create_all()
    print('✅ Database reset')
"
```

### View Database

```bash
psql -U postgres -d precision_pulse

# List tables
\dt

# View users
SELECT * FROM user;

# Exit
\q
```

## 📚 Documentation Files

| File | Purpose |
|------|---------|
| `CORS_AUTHENTICATION_FIX.md` | CORS and auth troubleshooting |
| `FRONTEND_COMPILATION_FIX.md` | Frontend compilation issues |
| `QUICK_START.md` | Quick start guide |
| `SWAGGER_SETUP.md` | Swagger documentation |
| `ARCHITECTURE_DIAGRAMS.md` | System architecture |

## 🆘 Getting Help

1. **Check Documentation**
   - Read relevant .md file
   - Check error message carefully

2. **Check Logs**
   - Backend terminal
   - Frontend terminal
   - Browser console (F12)
   - Browser network tab (F12 → Network)

3. **Verify Setup**
   - Both servers running
   - Correct ports
   - Environment variables set
   - Database connected

4. **Try Clean Install**
   ```bash
   # Backend
   pip install --upgrade -r requirements.txt
   
   # Frontend
   rm -rf node_modules package-lock.json
   npm install
   ```

5. **Restart Everything**
   - Kill all processes
   - Clear caches
   - Start fresh

## 🚀 Next Steps

1. ✅ Verify login works
2. ✅ Test API endpoints
3. ✅ Check real-time features
4. ✅ Test MQTT integration
5. ✅ Deploy to production

## 📞 Support Resources

- [Next.js Docs](https://nextjs.org/docs)
- [Flask Docs](https://flask.palletsprojects.com/)
- [PostgreSQL Docs](https://www.postgresql.org/docs/)
- [Socket.IO Docs](https://socket.io/docs/)
- [CORS Guide](https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS)

---

**Last Updated**: 2024
**Status**: ✅ Complete and Ready

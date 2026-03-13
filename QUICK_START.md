# Quick Start Guide - PrecisionPulse Full Stack

## Prerequisites

- Python 3.8+
- Node.js 16+
- PostgreSQL running
- MQTT Broker running (optional for basic testing)

## 🚀 Running the Full Stack

### Terminal 1: Start Backend

```bash
cd backend
pip install -r requirements.txt
python run.py
```

Expected output:
```
 * Running on http://127.0.0.1:5000
 * Swagger UI: http://localhost:5000/api/docs
```

### Terminal 2: Start Frontend

```bash
cd dspl-precision-pulse-frontend
npm install
npm run dev
```

Expected output:
```
> ready - started server on 0.0.0.0:3000, url: http://localhost:3000
```

### Terminal 3: (Optional) Start MQTT Broker

```bash
mosquitto -c config/mosquitto.conf
```

## 🌐 Access Points

| Service | URL | Purpose |
|---------|-----|---------|
| Frontend | http://localhost:3000 | Web UI |
| Backend API | http://localhost:5000 | REST API |
| Swagger Docs | http://localhost:5000/api/docs | API Documentation |
| MQTT Broker | localhost:18883 | Message Broker |

## 🔐 Default Credentials

Check your database for user credentials. If none exist, create one:

```bash
cd backend
python -c "
from app import create_app, db
from app.models.user import User
import bcrypt

app = create_app()
with app.app_context():
    # Check if user exists
    user = User.query.filter_by(email='admin@example.com').first()
    if not user:
        hashed = bcrypt.hashpw(b'password123', bcrypt.gensalt()).decode()
        user = User(email='admin@example.com', name='Admin', password_hash=hashed, role='admin')
        db.session.add(user)
        db.session.commit()
        print('User created: admin@example.com / password123')
    else:
        print('User already exists')
"
```

## 🧪 Test Login

1. Open http://localhost:3000 in browser
2. You'll be redirected to login page
3. Enter credentials:
   - Email: `admin@example.com`
   - Password: `password123`
4. Click "Sign In"
5. You should be redirected to dashboard

## 📊 Test API Endpoints

### Using Swagger UI

1. Go to http://localhost:5000/api/docs
2. Click "Authorize" button
3. Get token from login endpoint
4. Enter: `Bearer <token>`
5. Test endpoints

### Using cURL

```bash
# Login
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"password123"}'

# Get token from response, then use it:
TOKEN="your_token_here"

# Get parameters
curl -X GET http://localhost:5000/api/parameters \
  -H "Authorization: Bearer $TOKEN"

# Create parameter
curl -X POST http://localhost:5000/api/parameters \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"temperature","value":"25.5","unit":"celsius"}'
```

## 🔧 Environment Variables

### Frontend (`.env.local`)
```
NEXT_PUBLIC_BACKEND_URL=http://localhost:5000
JWT_SECRET=precision-pulse-super-secret-jwt-key-2024-development-only
```

### Backend (`.env`)
```
DATABASE_URL=postgresql://postgres:postgres@localhost/precision_pulse
JWT_SECRET=precision-pulse-super-secret-jwt-key-2024-development-only
MQTT_BROKER=localhost
MQTT_PORT=18883
MQTT_USE_TLS=true
MQTT_CA_CERTS=config/ca.crt
```

## 🐛 Troubleshooting

### Backend won't start
```bash
# Check if port 5000 is in use
lsof -i :5000

# Check database connection
python -c "from config.config import Config; print(Config.SQLALCHEMY_DATABASE_URI)"
```

### Frontend won't start
```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
npm run dev
```

### CORS errors
- Verify backend is running on port 5000
- Check `.env.local` has correct BACKEND_URL
- Restart both servers
- Clear browser cache

### Login not working
- Check credentials in database
- Verify JWT_SECRET matches
- Check browser console for errors
- Check backend logs

## 📚 Documentation

- [CORS & Authentication Fix](./CORS_AUTHENTICATION_FIX.md)
- [Swagger API Docs](./backend/SWAGGER_SETUP.md)
- [Backend README](./backend/README.md)
- [Frontend README](./dspl-precision-pulse-frontend/README.md)

## 🎯 Next Steps

1. ✅ Verify login works
2. ✅ Test API endpoints via Swagger
3. ✅ Check real-time features (Socket.IO)
4. ✅ Test MQTT integration
5. ✅ Deploy to production

## 💡 Tips

- Use `npm run dev` for frontend development (hot reload)
- Use `python run.py` for backend (auto-reload with debugger)
- Check logs in both terminals for errors
- Use browser DevTools (F12) to debug frontend
- Use Swagger UI to test API without Postman

## 🆘 Need Help?

1. Check the troubleshooting section above
2. Review error messages in console/logs
3. Check documentation files
4. Verify all services are running
5. Ensure ports 3000, 5000, 5432 are available

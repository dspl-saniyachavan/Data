# Quick Reference Card

## 🚀 Start Application (3 Commands)

```bash
# Terminal 1: Backend
cd backend && python run.py

# Terminal 2: Frontend
cd dspl-precision-pulse-frontend && npm run dev

# Terminal 3: Access
# Frontend: http://localhost:3000
# Backend: http://localhost:5000
# Swagger: http://localhost:5000/api/docs
```

## 🔐 Login Credentials

```
Email: admin@example.com
Password: password123
```

## 📍 Important URLs

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:5000 |
| Swagger Docs | http://localhost:5000/api/docs |
| Database | localhost:5432 |

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
```

## 🐛 Quick Fixes

### Port Already in Use
```bash
# Find process
lsof -i :3000  # or :5000

# Kill process
kill -9 <PID>
```

### Frontend Compilation Error
```bash
rm -rf node_modules package-lock.json
npm install
npm run dev
```

### Backend Import Error
```bash
pip install --upgrade -r requirements.txt
python run.py
```

### CORS Error
1. Verify backend is running
2. Check `.env.local` has correct URL
3. Restart both servers

### Login Not Working
1. Check credentials: admin@example.com / password123
2. Verify JWT_SECRET matches
3. Check browser console (F12)

## 📚 Documentation Files

| File | Purpose |
|------|---------|
| `COMPLETE_SETUP_GUIDE.md` | Full setup instructions |
| `QUICK_START.md` | Quick start guide |
| `CORS_AUTHENTICATION_FIX.md` | CORS troubleshooting |
| `FRONTEND_COMPILATION_FIX.md` | Frontend issues |
| `IMPLEMENTATION_COMPLETE.md` | Summary of all changes |

## 🧪 Test Commands

### Test Backend
```bash
# Check if running
curl http://localhost:5000/api/docs

# Login
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"password123"}'
```

### Test Frontend
```bash
# Check if running
curl http://localhost:3000

# Check for errors
# Open browser console: F12 → Console tab
```

## 🔑 API Endpoints

### Auth
- `POST /api/auth/login` - Login
- `POST /api/auth/register` - Register

### Parameters
- `GET /api/parameters` - List all
- `POST /api/parameters` - Create
- `GET /api/parameters/{id}` - Get one
- `PUT /api/parameters/{id}` - Update
- `DELETE /api/parameters/{id}` - Delete

### Users
- `GET /api/users` - List all
- `POST /api/users` - Create
- `GET /api/users/{id}` - Get one
- `PUT /api/users/{id}` - Update
- `DELETE /api/users/{id}` - Delete

## 💾 Database Commands

```bash
# Connect to database
psql -U postgres -d precision_pulse

# List tables
\dt

# View users
SELECT * FROM user;

# Exit
\q
```

## 🎯 Common Tasks

### Add New User
```bash
python -c "
from app import create_app, db
from app.models.user import User
import bcrypt

app = create_app()
with app.app_context():
    hashed = bcrypt.hashpw(b'password123', bcrypt.gensalt()).decode()
    user = User(email='user@example.com', name='User', password_hash=hashed, role='user')
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

### Clear Frontend Cache
```bash
rm -rf .next
npm run dev
```

## 🔍 Debugging

### Check Backend Logs
- Look in terminal where `python run.py` is running
- Check for errors and warnings

### Check Frontend Logs
- Open browser: F12 → Console tab
- Look for red errors
- Check Network tab for failed requests

### Check Database
```bash
psql -U postgres -d precision_pulse
SELECT * FROM user;
\q
```

## ✅ Verification Checklist

- [ ] Backend running on port 5000
- [ ] Frontend running on port 3000
- [ ] Can login with admin@example.com / password123
- [ ] Redirected to dashboard after login
- [ ] No errors in browser console
- [ ] Swagger docs accessible
- [ ] API endpoints working
- [ ] Database connected

## 🚀 Deployment

### Build Frontend
```bash
npm run build
npm start
```

### Build Backend
```bash
pip install -r requirements.txt
python run.py
```

### Production Checklist
- [ ] Update CORS origins
- [ ] Use HTTPS
- [ ] Set strong JWT_SECRET
- [ ] Set strong database password
- [ ] Disable Swagger docs
- [ ] Enable security headers
- [ ] Set up SSL certificates
- [ ] Configure environment variables

## 📞 Need Help?

1. **Check Documentation**
   - Read relevant .md file
   - Check error message

2. **Check Logs**
   - Backend terminal
   - Frontend console (F12)
   - Network tab (F12 → Network)

3. **Try Common Fixes**
   - Restart servers
   - Clear cache
   - Clean install dependencies
   - Check environment variables

4. **Verify Setup**
   - Both servers running
   - Correct ports
   - Database connected
   - Environment variables set

## 🎓 Resources

- [Next.js Docs](https://nextjs.org/docs)
- [Flask Docs](https://flask.palletsprojects.com/)
- [PostgreSQL Docs](https://www.postgresql.org/docs/)
- [Socket.IO Docs](https://socket.io/docs/)

## 📊 Project Status

✅ Backend: Complete
✅ Frontend: Complete
✅ Database: Complete
✅ Authentication: Complete
✅ API Documentation: Complete
✅ Real-time: Complete
✅ Testing: Complete
✅ Documentation: Complete

---

**Everything is ready to use!** 🎉

Start with: `COMPLETE_SETUP_GUIDE.md`

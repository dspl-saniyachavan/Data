# CORS & Authentication Troubleshooting Guide

## Error: "Unsafe attempt to load URL from frame"

This error occurs when your frontend and backend are on different origins (different ports/domains) and CORS is not properly configured.

## ✅ What Was Fixed

### 1. Backend CORS Configuration (`app/__init__.py`)
- Updated to accept requests from `http://localhost:3000` (frontend)
- Added support for credentials (cookies, auth headers)
- Configured proper HTTP methods and headers
- Added max_age for preflight caching

### 2. Frontend Configuration (`next.config.ts`)
- Added API rewrites to proxy backend requests
- Configured security headers
- Enabled proper CORS handling

### 3. Login Page (`src/app/login/page.tsx`)
- Uses environment variable for backend URL
- Added `credentials: 'include'` for CORS
- Changed from `window.location.href` to `router.push()` for proper navigation

### 4. Middleware (`src/middleware.ts`)
- Improved redirect logic
- Better token verification
- Proper handling of login page access

## 🚀 Setup Instructions

### Step 1: Ensure Backend is Running
```bash
cd backend
python run.py
```
Backend should be at: `http://localhost:5000`

### Step 2: Ensure Frontend is Running
```bash
cd dspl-precision-pulse-frontend
npm run dev
```
Frontend should be at: `http://localhost:3000`

### Step 3: Verify Environment Variables

**Frontend** (`.env.local`):
```
NEXT_PUBLIC_BACKEND_URL=http://localhost:5000
JWT_SECRET=precision-pulse-super-secret-jwt-key-2024-development-only
```

**Backend** (`.env`):
```
DATABASE_URL=postgresql://postgres:postgres@localhost/precision_pulse
JWT_SECRET=precision-pulse-super-secret-jwt-key-2024-development-only
MQTT_BROKER=localhost
MQTT_PORT=18883
```

## 🔍 Testing the Fix

### Test 1: Check Backend CORS Headers
```bash
curl -i -X OPTIONS http://localhost:5000/api/auth/login \
  -H "Origin: http://localhost:3000" \
  -H "Access-Control-Request-Method: POST"
```

Expected response should include:
```
Access-Control-Allow-Origin: http://localhost:3000
Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS, PATCH
Access-Control-Allow-Credentials: true
```

### Test 2: Test Login Endpoint
```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -H "Origin: http://localhost:3000" \
  -d '{"email":"admin@example.com","password":"password"}'
```

### Test 3: Access Frontend
1. Open `http://localhost:3000` in browser
2. You should be redirected to `/login`
3. Try logging in with valid credentials
4. Check browser console for errors (F12 → Console tab)

## 🐛 Common Issues & Solutions

### Issue 1: "CORS policy: No 'Access-Control-Allow-Origin' header"

**Cause**: Backend CORS not configured correctly

**Solution**:
1. Verify `CORS()` is called in `app/__init__.py`
2. Check origins list includes `http://localhost:3000`
3. Restart Flask server

### Issue 2: "Credentials mode is 'include' but Access-Control-Allow-Credentials is missing"

**Cause**: CORS credentials not enabled

**Solution**:
1. Ensure `supports_credentials=True` in CORS config
2. Verify `credentials: 'include'` in fetch requests
3. Restart both servers

### Issue 3: Login page redirects to login infinitely

**Cause**: Token verification failing or middleware issue

**Solution**:
1. Check browser console for errors
2. Verify JWT_SECRET matches between frontend and backend
3. Check token is being stored in cookies
4. Clear browser cookies and try again

### Issue 4: "Cannot POST /api/auth/login"

**Cause**: Backend route not registered or wrong URL

**Solution**:
1. Verify backend is running: `curl http://localhost:5000/api/docs`
2. Check auth_routes.py is registered in `app/__init__.py`
3. Verify URL is correct: `http://localhost:5000/api/auth/login`

## 📋 Checklist

- [ ] Backend running on `http://localhost:5000`
- [ ] Frontend running on `http://localhost:3000`
- [ ] `.env.local` has `NEXT_PUBLIC_BACKEND_URL=http://localhost:5000`
- [ ] Backend `.env` has correct database URL
- [ ] JWT_SECRET matches in both frontend and backend
- [ ] CORS is enabled in Flask app
- [ ] Login page uses environment variable for backend URL
- [ ] Middleware properly handles redirects
- [ ] Browser cookies are enabled
- [ ] No firewall blocking ports 3000 and 5000

## 🔐 Security Notes

### Development vs Production

**Development** (current setup):
- CORS allows localhost:3000
- Credentials enabled
- Swagger docs accessible

**Production** (when deploying):
1. Update CORS origins to your domain
2. Use HTTPS instead of HTTP
3. Set secure cookie flags
4. Disable Swagger docs
5. Use environment variables for secrets

### Example Production CORS:
```python
CORS(app, 
    origins=["https://yourdomain.com"],
    methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
    supports_credentials=True
)
```

## 📚 Resources

- [CORS Documentation](https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS)
- [Flask-CORS](https://flask-cors.readthedocs.io/)
- [Next.js Rewrites](https://nextjs.org/docs/api-reference/next.config.js/rewrites)
- [JWT Best Practices](https://tools.ietf.org/html/rfc8725)

## 🆘 Still Having Issues?

1. Check browser console (F12 → Console)
2. Check browser network tab (F12 → Network)
3. Check backend logs (terminal where Flask is running)
4. Check frontend logs (terminal where Next.js is running)
5. Verify both servers are actually running
6. Try clearing browser cache and cookies
7. Restart both servers

## 🎯 Next Steps

Once login is working:
1. Test other API endpoints
2. Verify token is being stored correctly
3. Test protected routes
4. Check Socket.IO connection
5. Test real-time features

# Architecture & Flow Diagrams

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         BROWSER                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  http://localhost:3000                                   │   │
│  │  ┌────────────────────────────────────────────────────┐  │   │
│  │  │  Next.js Frontend (React)                          │  │   │
│  │  │  - Login Page                                      │  │   │
│  │  │  - Dashboard                                       │  │   │
│  │  │  - Parameters, Telemetry, etc.                     │  │   │
│  │  └────────────────────────────────────────────────────┘  │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ HTTP Requests
                              │ (via Next.js rewrites)
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    BACKEND SERVER                                │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  http://localhost:5000                                   │   │
│  │  ┌────────────────────────────────────────────────────┐  │   │
│  │  │  Flask Application (Python)                        │  │   │
│  │  │  - CORS Enabled                                    │  │   │
│  │  │  - JWT Authentication                              │  │   │
│  │  │  - REST API Endpoints                              │  │   │
│  │  │  - Swagger Documentation                           │  │   │
│  │  │  - Socket.IO (Real-time)                           │  │   │
│  │  └────────────────────────────────────────────────────┘  │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ SQL Queries
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    DATABASE                                      │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  PostgreSQL (localhost:5432)                             │   │
│  │  - Users                                                 │   │
│  │  - Parameters                                            │   │
│  │  - Telemetry Data                                        │   │
│  │  - Audit Logs                                            │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## Authentication Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    LOGIN FLOW                                    │
└─────────────────────────────────────────────────────────────────┘

1. User enters credentials
   ┌──────────────────┐
   │ Email: admin@... │
   │ Password: ****   │
   └──────────────────┘
           │
           ▼
2. Frontend sends POST /api/auth/login
   ┌─────────────────────────────────────┐
   │ POST http://localhost:5000/api/auth │
   │ {email, password}                   │
   └─────────────────────────────────────┘
           │
           ▼
3. Backend validates credentials
   ┌──────────────────────────────────────┐
   │ Check user in database               │
   │ Verify password hash                 │
   └──────────────────────────────────────┘
           │
           ▼
4. Backend generates JWT token
   ┌──────────────────────────────────────┐
   │ Create JWT with user info            │
   │ Sign with JWT_SECRET                 │
   └──────────────────────────────────────┘
           │
           ▼
5. Backend returns token
   ┌──────────────────────────────────────┐
   │ Response: {token, user}              │
   │ Status: 200 OK                       │
   └──────────────────────────────────────┘
           │
           ▼
6. Frontend stores token
   ┌──────────────────────────────────────┐
   │ localStorage.setItem('token', token) │
   │ setTokenCookie(token)                │
   └──────────────────────────────────────┘
           │
           ▼
7. Frontend redirects to dashboard
   ┌──────────────────────────────────────┐
   │ router.push('/dashboard')            │
   │ Middleware verifies token            │
   └──────────────────────────────────────┘
           │
           ▼
   ✅ User logged in successfully
```

## CORS Request Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    CORS FLOW                                    │
└─────────────────────────────────────────────────────────────────┘

Browser (localhost:3000) → Backend (localhost:5000)

1. Browser sends preflight request (OPTIONS)
   ┌──────────────────────────────────────────┐
   │ OPTIONS /api/auth/login                  │
   │ Origin: http://localhost:3000            │
   │ Access-Control-Request-Method: POST      │
   └──────────────────────────────────────────┘
           │
           ▼
2. Backend checks CORS configuration
   ┌──────────────────────────────────────────┐
   │ Is origin in allowed list?               │
   │ ✅ http://localhost:3000 - YES           │
   │ Are methods allowed?                     │
   │ ✅ POST - YES                            │
   │ Are headers allowed?                     │
   │ ✅ Content-Type, Authorization - YES     │
   └──────────────────────────────────────────┘
           │
           ▼
3. Backend sends CORS headers
   ┌──────────────────────────────────────────┐
   │ Access-Control-Allow-Origin:             │
   │   http://localhost:3000                  │
   │ Access-Control-Allow-Methods:            │
   │   GET, POST, PUT, DELETE, OPTIONS, PATCH │
   │ Access-Control-Allow-Headers:            │
   │   Content-Type, Authorization            │
   │ Access-Control-Allow-Credentials: true   │
   │ Access-Control-Max-Age: 3600             │
   └──────────────────────────────────────────┘
           │
           ▼
4. Browser allows actual request
   ┌──────────────────────────────────────────┐
   │ POST /api/auth/login                     │
   │ {email, password}                        │
   └──────────────────────────────────────────┘
           │
           ▼
   ✅ Request succeeds
```

## API Request Flow (After Login)

```
┌─────────────────────────────────────────────────────────────────┐
│                    API REQUEST FLOW                              │
└─────────────────────────────────────────────────────────────────┘

1. Frontend makes API request with token
   ┌──────────────────────────────────────────┐
   │ GET /api/parameters                      │
   │ Authorization: Bearer <token>            │
   │ Content-Type: application/json           │
   └──────────────────────────────────────────┘
           │
           ▼
2. Next.js rewrites to backend
   ┌──────────────────────────────────────────┐
   │ next.config.ts rewrites:                 │
   │ /api/* → http://localhost:5000/api/*     │
   └──────────────────────────────────────────┘
           │
           ▼
3. Backend receives request
   ┌──────────────────────────────────────────┐
   │ Extract token from Authorization header  │
   │ Verify JWT signature                     │
   │ Check token expiration                   │
   └──────────────────────────────────────────┘
           │
           ▼
4. Backend processes request
   ┌──────────────────────────────────────────┐
   │ Query database for parameters            │
   │ Apply search, sort, pagination           │
   │ Format response                          │
   └──────────────────────────────────────────┘
           │
           ▼
5. Backend returns response
   ┌──────────────────────────────────────────┐
   │ {                                        │
   │   "parameters": [...],                   │
   │   "total": 42,                           │
   │   "pages": 5,                            │
   │   "current_page": 1                      │
   │ }                                        │
   │ Status: 200 OK                           │
   └──────────────────────────────────────────┘
           │
           ▼
6. Frontend receives response
   ┌──────────────────────────────────────────┐
   │ Parse JSON                               │
   │ Update component state                   │
   │ Re-render UI                             │
   └──────────────────────────────────────────┘
           │
           ▼
   ✅ Data displayed to user
```

## File Structure

```
PrecisionpulseDocs/
├── backend/
│   ├── app/
│   │   ├── __init__.py          ← CORS configured here
│   │   ├── routes/
│   │   │   ├── auth_routes.py   ← Login endpoint
│   │   │   └── ...
│   │   ├── models/
│   │   ├── controllers/
│   │   └── services/
│   ├── config/
│   │   └── config.py
│   ├── requirements.txt
│   ├── run.py
│   └── SWAGGER_SETUP.md
│
├── dspl-precision-pulse-frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── login/
│   │   │   │   └── page.tsx     ← Login page (updated)
│   │   │   ├── dashboard/
│   │   │   └── ...
│   │   └── middleware.ts        ← Auth middleware (updated)
│   ├── next.config.ts           ← CORS rewrites (updated)
│   ├── .env.local               ← Backend URL
│   └── package.json
│
├── CORS_AUTHENTICATION_FIX.md   ← Troubleshooting guide
├── CORS_FIX_SUMMARY.md          ← This summary
├── QUICK_START.md               ← Quick start guide
└── README.md
```

## Environment Variables

```
Frontend (.env.local):
├── NEXT_PUBLIC_BACKEND_URL=http://localhost:5000
└── JWT_SECRET=precision-pulse-super-secret-jwt-key-2024-development-only

Backend (.env):
├── DATABASE_URL=postgresql://postgres:postgres@localhost/precision_pulse
├── JWT_SECRET=precision-pulse-super-secret-jwt-key-2024-development-only
├── MQTT_BROKER=localhost
├── MQTT_PORT=18883
├── MQTT_USE_TLS=true
└── MQTT_CA_CERTS=config/ca.crt
```

## Port Mapping

```
┌──────────────────────────────────────────┐
│           SERVICE PORTS                  │
├──────────────────────────────────────────┤
│ Frontend (Next.js)    │ 3000             │
│ Backend (Flask)       │ 5000             │
│ Database (PostgreSQL) │ 5432             │
│ MQTT Broker           │ 18883 (TLS)      │
│ Swagger Docs          │ 5000/api/docs    │
└──────────────────────────────────────────┘
```

## Security Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    SECURITY LAYERS                               │
└─────────────────────────────────────────────────────────────────┘

1. CORS Validation
   ✅ Only allowed origins can access API
   ✅ Only allowed methods permitted
   ✅ Only allowed headers accepted

2. JWT Authentication
   ✅ Token signed with secret
   ✅ Token expiration checked
   ✅ User identity verified

3. Middleware Protection
   ✅ Protected routes require token
   ✅ Admin routes check role
   ✅ Invalid tokens rejected

4. HTTPS (Production)
   ✅ Encrypted communication
   ✅ Secure cookies
   ✅ Certificate validation

5. Database Security
   ✅ Password hashing (bcrypt)
   ✅ SQL injection prevention
   ✅ Access control
```

---

**All diagrams show the current working configuration after fixes applied.**

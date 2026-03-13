# PrecisionPulse Backend

Flask REST API with MQTT integration, WebSocket support, and real-time data streaming.

## Features

- JWT authentication with role-based access control
- MQTT broker integration for telemetry streaming
- WebSocket support for real-time updates
- Parameter management and synchronization
- Telemetry data buffering and sync
- User and configuration management
- SQLAlchemy ORM with SQLite/PostgreSQL support

## Quick Start

### Prerequisites
- Python 3.8+
- MQTT broker (Mosquitto or similar)
- PostgreSQL (optional, SQLite by default)

### Installation

```bash
# Clone repository
git clone https://github.com/DevAngles-Interns-2026/dspl-precision-pulse-backend.git
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
```

### Configuration

Create `.env` file:

```env
FLASK_ENV=development
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///instance/precision_pulse.db
MQTT_BROKER=localhost
MQTT_PORT=8883
MQTT_USE_TLS=false
JWT_SECRET=your-jwt-secret
```

### Run Server

```bash
python run.py
```

Server runs on `http://localhost:5000`

## API Endpoints

### Authentication
- `POST /api/auth/login` - User login
- `POST /api/auth/register` - Register new user

### Parameters
- `GET /api/parameters` - Get all parameters
- `POST /api/parameters` - Create parameter
- `PUT /api/parameters/:id` - Update parameter
- `DELETE /api/parameters/:id` - Delete parameter

### Telemetry
- `GET /api/telemetry/latest` - Get latest telemetry data
- `GET /api/telemetry/history` - Get telemetry history

### Users (Admin only)
- `GET /api/users` - List all users
- `POST /api/users` - Create user
- `PUT /api/users/:id` - Update user
- `DELETE /api/users/:id` - Delete user

### Internal (Desktop sync)
- `GET /api/internal/parameters` - Get parameters for sync
- `PUT /api/internal/sync-parameter` - Sync parameter
- `DELETE /api/internal/sync-parameter-delete` - Delete parameter

## Project Structure

```
backend/
├── app/
│   ├── controllers/      # Request handlers
│   ├── models/           # Database models
│   ├── routes/           # API endpoints
│   ├── services/         # Business logic
│   ├── middleware/       # Auth middleware
│   ├── events/           # WebSocket events
│   └── utils/            # Utilities
├── config/               # Configuration & SSL certs
├── instance/             # SQLite database
├── run.py                # Entry point
├── requirements.txt      # Dependencies
└── .env                  # Environment variables
```

## Default Users

| Role | Email | Password |
|------|-------|----------|
| Admin | admin@precisionpulse.com | admin123 |
| Client | client@precisionpulse.com | client123 |
| User | user@precisionpulse.com | user123 |

## Technologies

- **Framework**: Flask
- **ORM**: SQLAlchemy
- **Authentication**: JWT + Argon2
- **Real-time**: Socket.IO
- **Messaging**: MQTT (paho-mqtt)
- **Database**: SQLite/PostgreSQL

## MQTT Topics

- `precisionpulse/telemetry` - Telemetry data stream
- `precisionpulse/heartbeat` - Connection heartbeat
- `precisionpulse/sync/users/#` - User synchronization
- `precisionpulse/sync/config` - Configuration sync
- `precisionpulse/sync/parameters` - Parameter sync
- `precisionpulse/commands/config/update` - Remote config updates

## Development

### Initialize Database
```bash
python create_db.py
python init_users.py
python init_parameters.py
```

### Run with PostgreSQL
```bash
python init_postgres.py
# Update DATABASE_URL in .env
python run.py
```

## Troubleshooting

**Port 5000 already in use:**
```bash
python run.py --port 5001
```

**MQTT connection fails:**
- Verify broker is running
- Check MQTT_BROKER and MQTT_PORT in .env
- Ensure TLS certificates exist if MQTT_USE_TLS=true

**Database errors:**
- Delete `instance/precision_pulse.db` to reset
- Run `python create_db.py` to reinitialize

**JWT errors:**
- Verify JWT_SECRET is set in .env
- Check token expiration

## License

MIT License - See LICENSE file

## Support

For issues and questions, contact the development team.

# PrecisionPulse API Documentation

## Overview
PrecisionPulse is a real-time telemetry and parameter management system with support for MQTT, WebSocket, and REST APIs.

## Base URL
```
http://localhost:5000
```

## Swagger UI
Access interactive API documentation at:
```
http://localhost:5000/apidocs
```

---

## Authentication

### Login
**POST** `/api/auth/login`

Request:
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

Response:
```json
{
  "token": "eyJhbGciOiJIUzI1NiIs...",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "name": "User Name",
    "role": "admin"
  }
}
```

### Logout
**POST** `/api/auth/logout`

Headers: `Authorization: Bearer <token>`

---

## Parameters

### Get All Parameters
**GET** `/api/parameters`

Headers: `Authorization: Bearer <token>`

Response:
```json
{
  "parameters": [
    {
      "id": 1,
      "name": "Temperature",
      "unit": "°C",
      "description": "Room temperature",
      "enabled": true,
      "created_at": "2024-01-01T10:00:00"
    }
  ]
}
```

### Create Parameter
**POST** `/api/parameters`

Headers: `Authorization: Bearer <token>`

Request:
```json
{
  "name": "Humidity",
  "unit": "%",
  "description": "Room humidity",
  "enabled": true
}
```

### Update Parameter
**PUT** `/api/parameters/<id>`

Headers: `Authorization: Bearer <token>`

Request:
```json
{
  "name": "Humidity",
  "enabled": false
}
```

### Delete Parameter
**DELETE** `/api/parameters/<id>`

Headers: `Authorization: Bearer <token>`

---

## Telemetry

### Stream Telemetry
**POST** `/api/telemetry/stream`

Request:
```json
{
  "client_id": "device-001",
  "timestamp": "2024-01-01T10:00:00",
  "parameters": [
    {
      "id": 1,
      "name": "Temperature",
      "value": 25.5,
      "unit": "°C"
    }
  ]
}
```

### Get Latest Telemetry
**GET** `/api/telemetry/latest`

Response:
```json
{
  "data": {
    "timestamp": 1704110400000,
    "parameters": [
      {
        "id": 1,
        "name": "Temperature",
        "value": 25.5,
        "unit": "°C"
      }
    ]
  }
}
```

### Get Telemetry History
**GET** `/api/telemetry/history`

Response:
```json
{
  "data": [
    {
      "id": 1,
      "name": "Temperature",
      "unit": "°C",
      "values": [
        {
          "value": 25.5,
          "timestamp": 1704110400000
        }
      ]
    }
  ]
}
```

---

## Users

### Get All Users
**GET** `/api/users`

Headers: `Authorization: Bearer <token>`

### Create User
**POST** `/api/users`

Headers: `Authorization: Bearer <token>`

Request:
```json
{
  "email": "newuser@example.com",
  "name": "New User",
  "password": "password123",
  "role": "user"
}
```

### Update User
**PUT** `/api/users/<id>`

Headers: `Authorization: Bearer <token>`

### Delete User
**DELETE** `/api/users/<id>`

Headers: `Authorization: Bearer <token>`

---

## Buffer Management

### Get Buffered Data
**GET** `/api/buffer/telemetry/latest`

Headers: `Authorization: Bearer <token>`

Response:
```json
{
  "buffer": [
    {
      "id": 1,
      "device_id": "device-001",
      "parameter_id": 1,
      "parameter_name": "Temperature",
      "value": 25.5,
      "unit": "°C",
      "timestamp": "2024-01-01T10:00:00",
      "synced": false
    }
  ],
  "count": 1
}
```

### Mark Data as Synced
**PUT** `/api/buffer/telemetry/mark-synced`

Request:
```json
{
  "ids": [1, 2, 3]
}
```

---

## Remote Commands

### Force Sync
**POST** `/api/remote-commands/force-sync`

Headers: `Authorization: Bearer <token>`

Request:
```json
{
  "device_id": "device-001",
  "sync_type": "full"
}
```

Response:
```json
{
  "success": true,
  "command_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Force sync command sent",
  "device_id": "device-001",
  "sync_type": "full"
}
```

### Update Config
**POST** `/api/remote-commands/update-config`

Headers: `Authorization: Bearer <token>`

Request:
```json
{
  "device_id": "device-001",
  "config": {
    "mqtt_broker": "localhost",
    "mqtt_port": 18883,
    "sync_interval": 300
  }
}
```

Response:
```json
{
  "success": true,
  "command_id": "550e8400-e29b-41d4-a716-446655440001",
  "message": "Config update command sent",
  "device_id": "device-001"
}
```

### Get Command Status
**GET** `/api/remote-commands/status?command_id=<id>`

Headers: `Authorization: Bearer <token>`

Response:
```json
{
  "command": "force_sync",
  "device_id": "device-001",
  "status": "sent",
  "timestamp": "2024-01-01T10:00:00"
}
```

---

## Error Responses

### 400 Bad Request
```json
{
  "error": "Invalid request parameters"
}
```

### 401 Unauthorized
```json
{
  "error": "Missing or invalid authentication token"
}
```

### 403 Forbidden
```json
{
  "error": "Insufficient permissions"
}
```

### 404 Not Found
```json
{
  "error": "Resource not found"
}
```

### 500 Internal Server Error
```json
{
  "error": "Internal server error"
}
```

---

## Status Codes

| Code | Description |
|------|-------------|
| 200 | OK |
| 201 | Created |
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 500 | Internal Server Error |

---

## WebSocket Events

### Connect
```javascript
socket.on('connect', () => {
  console.log('Connected to server');
});
```

### MQTT Status
```javascript
socket.on('mqtt_status', (data) => {
  console.log('MQTT Status:', data.status); // 'online' | 'offline'
});
```

### Telemetry Update
```javascript
socket.on('telemetry_update', (data) => {
  console.log('Telemetry:', data);
});
```

---

## Rate Limiting
- No rate limiting currently implemented
- Recommended: 100 requests per minute per IP

## Authentication
- JWT tokens expire after 24 hours
- Include token in Authorization header: `Bearer <token>`

## CORS
- Enabled for all origins
- Credentials: included


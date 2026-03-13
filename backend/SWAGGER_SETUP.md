# Swagger API Documentation Setup

## Overview
Swagger UI has been integrated into your Flask API for interactive API documentation and testing.

## Access Swagger UI

Once your Flask app is running, access Swagger documentation at:

```
http://localhost:5000/api/docs
```

## Features

✅ **Interactive API Testing** - Test endpoints directly from the browser
✅ **JWT Authentication** - Secure endpoints with Bearer token
✅ **Request/Response Examples** - See example payloads
✅ **Auto-generated Documentation** - Based on route docstrings

## How to Use

### 1. Start Your Flask Application

```bash
cd backend
python run.py
```

### 2. Open Swagger UI

Navigate to: `http://localhost:5000/api/docs`

### 3. Authenticate (For Protected Routes)

1. Click the **"Authorize"** button (top right)
2. Enter your JWT token in format: `Bearer <your_token>`
3. Click **"Authorize"**
4. Click **"Close"**

### 4. Test Endpoints

1. Click on any endpoint to expand it
2. Click **"Try it out"**
3. Fill in required parameters
4. Click **"Execute"**
5. View the response below

## Adding Documentation to New Routes

When creating new routes, add Swagger documentation using docstrings:

```python
@your_bp.route('/example', methods=['POST'])
@token_required
def example_endpoint():
    """
    Example Endpoint
    ---
    tags:
      - Example
    security:
      - Bearer: []
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - field1
          properties:
            field1:
              type: string
              example: value1
            field2:
              type: integer
              example: 42
    responses:
      200:
        description: Success
        schema:
          type: object
          properties:
            message:
              type: string
      400:
        description: Bad request
      401:
        description: Unauthorized
    """
    # Your endpoint logic here
    pass
```

## Configuration

Swagger configuration is in `app/__init__.py`:

```python
swagger_config = {
    "headers": [],
    "specs": [
        {
            "endpoint": 'apispec',
            "route": '/apispec.json',
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True,
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/api/docs"
}

swagger_template = {
    "swagger": "2.0",
    "info": {
        "title": "PrecisionPulse API",
        "description": "API documentation for PrecisionPulse backend",
        "version": "1.0.0"
    },
    "securityDefinitions": {
        "Bearer": {
            "type": "apiKey",
            "name": "Authorization",
            "in": "header",
            "description": "JWT Authorization header using the Bearer scheme"
        }
    }
}
```

## Documented Routes

Currently documented routes:

### Authentication
- `POST /api/auth/login` - User login
- `POST /api/auth/register` - User registration

### Parameters
- `GET /api/parameters` - Get all parameters (with search, sort, pagination)
- `POST /api/parameters` - Create parameter
- `GET /api/parameters/{id}` - Get parameter by ID
- `PUT /api/parameters/{id}` - Update parameter
- `DELETE /api/parameters/{id}` - Delete parameter

## Next Steps

To document remaining routes, follow the same pattern in:
- `app/routes/user_routes.py`
- `app/routes/telemetry_routes.py`
- `app/routes/buffer_routes.py`
- And other route files

## Troubleshooting

### Swagger UI not loading
- Ensure `flasgger` is installed: `pip install flasgger`
- Check Flask app is running
- Verify no port conflicts

### Authentication not working
- Get JWT token from `/api/auth/login`
- Click "Authorize" button
- Enter: `Bearer <your_token>`
- Don't forget the "Bearer " prefix

### Documentation not showing
- Check docstring format matches YAML syntax
- Ensure proper indentation
- Restart Flask app after changes

## Resources

- [Flasgger Documentation](https://github.com/flasgger/flasgger)
- [Swagger Specification](https://swagger.io/specification/v2/)
- [OpenAPI Guide](https://swagger.io/docs/specification/about/)

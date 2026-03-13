from functools import wraps
from flask import request, jsonify

ROLE_PERMISSIONS = {
    'admin': ['user.create', 'user.read', 'user.update', 'user.delete', 'role.manage', 'permission.manage'],
    'user': ['user.read'],
    'client': []
}

def require_permission(permission):
    """Decorator to check if user has required permission"""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if not hasattr(request, 'user'):
                return jsonify({'error': 'User not authenticated'}), 401
            
            user_role = request.user.get('role')
            allowed_permissions = ROLE_PERMISSIONS.get(user_role, [])
            
            if permission not in allowed_permissions:
                return jsonify({'error': f'Insufficient permissions. Required: {permission}'}), 403
            
            return f(*args, **kwargs)
        return decorated
    return decorator

def validate_request_payload(required_fields):
    """Decorator to validate request payload"""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            data = request.get_json()
            
            if not data:
                return jsonify({'error': 'Request body is required'}), 400
            
            missing_fields = [field for field in required_fields if field not in data or not data[field]]
            if missing_fields:
                return jsonify({'error': f'Missing required fields: {", ".join(missing_fields)}'}), 400
            
            return f(*args, **kwargs)
        return decorated
    return decorator

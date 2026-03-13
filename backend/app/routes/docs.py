"""
API Documentation endpoints
"""

from flask import Blueprint

docs_bp = Blueprint('docs', __name__, url_prefix='/api/docs')

@docs_bp.route('/auth', methods=['GET'])
def auth_docs():
    """
    Authentication Endpoints
    ---
    get:
      summary: Get authentication documentation
      responses:
        200:
          description: Authentication API documentation
    """
    return {
        'endpoints': [
            {
                'path': '/api/auth/login',
                'method': 'POST',
                'description': 'User login',
                'body': {'email': 'string', 'password': 'string'},
                'response': {'token': 'string', 'user': 'object'}
            },
            {
                'path': '/api/auth/logout',
                'method': 'POST',
                'description': 'User logout',
                'auth': 'required'
            }
        ]
    }

@docs_bp.route('/parameters', methods=['GET'])
def parameters_docs():
    """
    Parameters Endpoints
    ---
    get:
      summary: Get parameters documentation
      responses:
        200:
          description: Parameters API documentation
    """
    return {
        'endpoints': [
            {
                'path': '/api/parameters',
                'method': 'GET',
                'description': 'Get all parameters',
                'auth': 'required',
                'response': {'parameters': 'array'}
            },
            {
                'path': '/api/parameters',
                'method': 'POST',
                'description': 'Create parameter',
                'auth': 'required',
                'body': {'name': 'string', 'unit': 'string', 'description': 'string'}
            },
            {
                'path': '/api/parameters/<id>',
                'method': 'PUT',
                'description': 'Update parameter',
                'auth': 'required'
            },
            {
                'path': '/api/parameters/<id>',
                'method': 'DELETE',
                'description': 'Delete parameter',
                'auth': 'required'
            }
        ]
    }

@docs_bp.route('/telemetry', methods=['GET'])
def telemetry_docs():
    """
    Telemetry Endpoints
    ---
    get:
      summary: Get telemetry documentation
      responses:
        200:
          description: Telemetry API documentation
    """
    return {
        'endpoints': [
            {
                'path': '/api/telemetry/stream',
                'method': 'POST',
                'description': 'Stream telemetry data',
                'body': {'client_id': 'string', 'timestamp': 'string', 'parameters': 'array'}
            },
            {
                'path': '/api/telemetry/latest',
                'method': 'GET',
                'description': 'Get latest telemetry',
                'response': {'timestamp': 'number', 'parameters': 'array'}
            },
            {
                'path': '/api/telemetry/history',
                'method': 'GET',
                'description': 'Get telemetry history',
                'response': {'data': 'array'}
            }
        ]
    }

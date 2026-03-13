from flask import Blueprint, request, jsonify
from flasgger import swag_from
from app.controllers.auth_controller import AuthController

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

@auth_bp.route('/login', methods=['POST'])
def login():
    """
    User Login
    ---
    tags:
      - Authentication
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - email
            - password
          properties:
            email:
              type: string
              example: user@example.com
            password:
              type: string
              example: password123
    responses:
      200:
        description: Login successful
        schema:
          type: object
          properties:
            token:
              type: string
            user:
              type: object
      400:
        description: Invalid credentials
      401:
        description: Unauthorized
    """
    data = request.get_json()
    
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Email and password required'}), 400
    
    result, status = AuthController.login(data['email'], data['password'])
    return jsonify(result), status

@auth_bp.route('/register', methods=['POST'])
def register():
    """
    User Registration
    ---
    tags:
      - Authentication
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - email
            - password
            - name
          properties:
            email:
              type: string
              example: newuser@example.com
            password:
              type: string
              example: password123
            name:
              type: string
              example: John Doe
            role:
              type: string
              example: user
              default: user
    responses:
      201:
        description: User registered successfully
        schema:
          type: object
          properties:
            message:
              type: string
            user:
              type: object
      400:
        description: Invalid input or user already exists
    """
    data = request.get_json()
    
    if not data or not data.get('email') or not data.get('password') or not data.get('name'):
        return jsonify({'error': 'Email, name, and password required'}), 400
    
    result, status = AuthController.register(
        data['email'],
        data['name'],
        data['password'],
        data.get('role', 'user')
    )
    return jsonify(result), status

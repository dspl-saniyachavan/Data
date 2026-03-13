from flask import Blueprint, request, jsonify
from app.controllers.user_controller import UserController
from app.middleware.auth_middleware import token_required

user_bp = Blueprint('users', __name__, url_prefix='/api/users')

@user_bp.route('', methods=['GET'])
@token_required
def get_users():
    result, status = UserController.get_all_users()
    return jsonify(result), status

@user_bp.route('', methods=['POST'])
@token_required
def create_user():
    data = request.get_json()
    
    if not data or not data.get('email') or not data.get('password') or not data.get('name'):
        return jsonify({'error': 'Email, name, and password required'}), 400
    
    result, status = UserController.create_user(
        data['email'],
        data['name'],
        data['password'],
        data.get('role', 'user')
    )
    return jsonify(result), status

@user_bp.route('/<int:user_id>', methods=['PUT'])
@token_required
def update_user(user_id):
    data = request.get_json()
    result, status = UserController.update_user(user_id, **data)
    return jsonify(result), status

@user_bp.route('/<int:user_id>', methods=['DELETE'])
@token_required
def delete_user(user_id):
    result, status = UserController.delete_user(user_id)
    return jsonify(result), status

@user_bp.route('/<int:user_id>/change-password', methods=['POST'])
@token_required
def change_password(user_id):
    data = request.get_json()
    
    if not data or not data.get('currentPassword') or not data.get('newPassword'):
        return jsonify({'error': 'Current password and new password required'}), 400
    
    result, status = UserController.change_password(
        user_id,
        data['currentPassword'],
        data['newPassword']
    )
    return jsonify(result), status

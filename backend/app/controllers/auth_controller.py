from app.models.user import User
from app.models import db
from app.utils.jwt_utils import create_token
from flask import jsonify

class AuthController:
    @staticmethod
    def login(email, password):
        user = User.query.filter_by(email=email).first()
        
        if not user or not user.check_password(password):
            return {'error': 'Invalid credentials'}, 401
        
        if not user.is_active:
            return {'error': 'Account is disabled'}, 403
        
        token = create_token(user.id, user.email, user.role)
        return {
            'token': token,
            'user': user.to_dict()
        }, 200
    
    @staticmethod
    def register(email, name, password, role='user'):
        if User.query.filter_by(email=email).first():
            return {'error': 'Email already exists'}, 409
        
        user = User(email=email, name=name, role=role)
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        token = create_token(user.id, user.email, user.role)
        return {
            'token': token,
            'user': user.to_dict()
        }, 201

from app.models.user import User
from app.models import db
from app.services.sync_service import sync_service

class UserController:
    @staticmethod
    def get_all_users():
        users = User.query.all()
        return [user.to_dict() for user in users], 200
    
    @staticmethod
    def create_user(email, name, password, role='user'):
        if User.query.filter_by(email=email).first():
            return {'error': 'Email already exists'}, 409
        
        user = User(email=email, name=name, role=role)
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        # Sync to SQLite
        sync_service.sync_user_to_sqlite({
            'email': user.email,
            'name': user.name,
            'password_hash': user.password_hash,
            'role': user.role,
            'is_active': user.is_active
        })
        
        return user.to_dict(), 201
    
    @staticmethod
    def update_user(user_id, **kwargs):
        user = User.query.get(user_id)
        if not user:
            return {'error': 'User not found'}, 404
        
        for key, value in kwargs.items():
            if key == 'password':
                user.set_password(value)
            elif key == 'password_hash':
                user.password_hash = value  # Direct hash update for sync
            elif hasattr(user, key):
                setattr(user, key, value)
        
        db.session.commit()
        
        # Sync to SQLite
        sync_service.sync_user_to_sqlite({
            'email': user.email,
            'name': user.name,
            'password_hash': user.password_hash,
            'role': user.role,
            'is_active': user.is_active
        })
        
        return user.to_dict(), 200
    
    @staticmethod
    def delete_user(user_id):
        user = User.query.get(user_id)
        if not user:
            return {'error': 'User not found'}, 404
        
        db.session.delete(user)
        db.session.commit()
        
        # Sync deletion to SQLite
        try:
            import sqlite3
            with sqlite3.connect(sync_service.sqlite_path) as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM users WHERE email = ?', (user.email,))
                conn.commit()
        except Exception as e:
            print(f"Error syncing user deletion to SQLite: {e}")
        
        return {'message': 'User deleted'}, 200
    
    @staticmethod
    def change_password(user_id, current_password, new_password):
        user = User.query.get(user_id)
        if not user:
            return {'error': 'User not found'}, 404
        
        if not user.check_password(current_password):
            return {'error': 'Current password is incorrect'}, 401
        
        user.set_password(new_password)
        db.session.commit()
        return {'message': 'Password changed successfully'}, 200

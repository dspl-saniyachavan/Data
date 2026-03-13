"""
Internal routes for desktop-backend synchronization
These endpoints are called by desktop app to sync data with backend
"""

from flask import Blueprint, request, jsonify
from app.models import db
from app.models.user import User
from app.services.mqtt_publisher import get_mqtt_publisher
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

internal_bp = Blueprint('internal', __name__, url_prefix='/api/internal')

@internal_bp.route('/sync-user-password', methods=['POST'])
def sync_user_password():
    """
    Sync password change from desktop to backend
    Called by desktop app when user changes password locally
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        email = data.get('email')
        password_hash = data.get('password_hash')
        
        if not email or not password_hash:
            return jsonify({'error': 'Email and password_hash required'}), 400
        
        # Find user by email
        user = User.query.filter_by(email=email).first()
        
        if not user:
            logger.warning(f"[SYNC] Password sync attempted for non-existent user: {email}")
            return jsonify({'error': 'User not found'}), 404
        
        # Update password hash in backend database
        user.password_hash = password_hash
        user.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        logger.info(f"[SYNC] Password synchronized for user: {email}")
        
        # Broadcast password change event via MQTT
        try:
            publisher = get_mqtt_publisher()
            payload = {
                'event': 'user_password_changed',
                'email': email,
                'timestamp': datetime.utcnow().isoformat(),
                'source': 'desktop'
            }
            publisher._publish('precisionpulse/sync/users/password-changed', payload)
        except Exception as e:
            logger.error(f"[SYNC] Failed to broadcast password change: {e}")
        
        return jsonify({
            'success': True,
            'message': 'Password synchronized successfully',
            'email': email
        }), 200
    
    except Exception as e:
        logger.error(f"[SYNC] Error syncing password: {e}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@internal_bp.route('/sync-user-profile', methods=['POST'])
def sync_user_profile():
    """
    Sync user profile changes from desktop to backend
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        email = data.get('email')
        name = data.get('name')
        
        if not email:
            return jsonify({'error': 'Email required'}), 400
        
        # Find user by email
        user = User.query.filter_by(email=email).first()
        
        if not user:
            logger.warning(f"[SYNC] Profile sync attempted for non-existent user: {email}")
            return jsonify({'error': 'User not found'}), 404
        
        # Update profile fields
        if name:
            user.name = name
        
        user.updated_at = datetime.utcnow()
        db.session.commit()
        
        logger.info(f"[SYNC] Profile synchronized for user: {email}")
        
        # Broadcast profile change event via MQTT
        try:
            publisher = get_mqtt_publisher()
            payload = {
                'event': 'user_profile_changed',
                'email': email,
                'name': name,
                'timestamp': datetime.utcnow().isoformat(),
                'source': 'desktop'
            }
            publisher._publish('precisionpulse/sync/users/profile-changed', payload)
        except Exception as e:
            logger.error(f"[SYNC] Failed to broadcast profile change: {e}")
        
        return jsonify({
            'success': True,
            'message': 'Profile synchronized successfully',
            'email': email
        }), 200
    
    except Exception as e:
        logger.error(f"[SYNC] Error syncing profile: {e}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@internal_bp.route('/sync-status', methods=['GET'])
def get_sync_status():
    """
    Get synchronization status
    """
    try:
        return jsonify({
            'status': 'online',
            'timestamp': datetime.utcnow().isoformat(),
            'version': '1.0'
        }), 200
    except Exception as e:
        logger.error(f"[SYNC] Error getting sync status: {e}")
        return jsonify({'error': str(e)}), 500

@internal_bp.route('/parameters', methods=['GET'])
def get_parameters():
    """
    Get all parameters for desktop app (no auth required)
    """
    try:
        from app.models.parameter import Parameter
        parameters = Parameter.query.order_by(Parameter.created_at.desc()).all()
        return jsonify({
            'parameters': [param.to_dict() for param in parameters]
        }), 200
    except Exception as e:
        logger.error(f"[INTERNAL] Error fetching parameters: {e}")
        return jsonify({'error': str(e)}), 500

@internal_bp.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint for desktop app
    """
    try:
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat()
        }), 200
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 500

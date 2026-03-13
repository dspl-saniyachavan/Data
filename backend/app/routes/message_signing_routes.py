"""
Message Signing Routes
API endpoints for managing message signing and security monitoring
"""

from flask import Blueprint, jsonify, request
from app.services.message_signing_service import get_message_signing_service
from app.services.message_signing_config import MessageSigningConfig
from functools import wraps

message_signing_bp = Blueprint('message_signing', __name__, url_prefix='/api/security/signing')


def require_admin(f):
    """Decorator to require admin role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if user is admin (implement based on your auth system)
        from flask import g
        if not hasattr(g, 'user') or g.user.get('role') != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        return f(*args, **kwargs)
    return decorated_function


@message_signing_bp.route('/config', methods=['GET'])
@require_admin
def get_signing_config():
    """Get current signing configuration"""
    try:
        signing_service = get_message_signing_service()
        
        return jsonify({
            'success': True,
            'config': {
                'signing_enabled': True,
                'sensitive_commands': list(MessageSigningConfig.SENSITIVE_COMMANDS),
                'nonce_cache_ttl': MessageSigningConfig.NONCE_CACHE_TTL,
                'timestamp_tolerance': MessageSigningConfig.TIMESTAMP_TOLERANCE,
                'algorithm': 'HMAC-SHA256',
                'version': '1.0'
            },
            'stats': signing_service.get_signing_stats()
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@message_signing_bp.route('/stats', methods=['GET'])
@require_admin
def get_signing_stats():
    """Get signing statistics and security metrics"""
    try:
        signing_service = get_message_signing_service()
        stats = signing_service.get_signing_stats()
        
        return jsonify({
            'success': True,
            'stats': stats,
            'timestamp': __import__('datetime').datetime.utcnow().isoformat()
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@message_signing_bp.route('/verify-test', methods=['POST'])
@require_admin
def verify_test_message():
    """Test message verification (for debugging)"""
    try:
        data = request.get_json()
        message = data.get('message')
        
        if not message:
            return jsonify({'error': 'Message required'}), 400
        
        signing_service = get_message_signing_service()
        is_valid, error, payload = signing_service.verify_message(message)
        
        return jsonify({
            'success': True,
            'is_valid': is_valid,
            'error': error,
            'payload': payload if is_valid else None
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@message_signing_bp.route('/sign-test', methods=['POST'])
@require_admin
def sign_test_message():
    """Test message signing (for debugging)"""
    try:
        data = request.get_json()
        payload = data.get('payload')
        message_type = data.get('message_type', 'test')
        
        if not payload:
            return jsonify({'error': 'Payload required'}), 400
        
        signing_service = get_message_signing_service()
        signed_message = signing_service.sign_message(payload, message_type)
        
        return jsonify({
            'success': True,
            'signed_message': signed_message
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@message_signing_bp.route('/sensitive-commands', methods=['GET'])
@require_admin
def get_sensitive_commands():
    """Get list of commands that require signing"""
    return jsonify({
        'success': True,
        'sensitive_commands': list(MessageSigningConfig.SENSITIVE_COMMANDS),
        'count': len(MessageSigningConfig.SENSITIVE_COMMANDS)
    }), 200


@message_signing_bp.route('/security-report', methods=['GET'])
@require_admin
def get_security_report():
    """Get comprehensive security report"""
    try:
        signing_service = get_message_signing_service()
        stats = signing_service.get_signing_stats()
        
        # Calculate security metrics
        total_messages = stats.get('nonce_cache_size', 0)
        
        report = {
            'success': True,
            'timestamp': __import__('datetime').datetime.utcnow().isoformat(),
            'signing_enabled': True,
            'algorithm': 'HMAC-SHA256',
            'version': '1.0',
            'configuration': {
                'sensitive_commands': len(MessageSigningConfig.SENSITIVE_COMMANDS),
                'nonce_cache_ttl_seconds': MessageSigningConfig.NONCE_CACHE_TTL,
                'timestamp_tolerance_seconds': MessageSigningConfig.TIMESTAMP_TOLERANCE
            },
            'statistics': stats,
            'recommendations': []
        }
        
        # Add recommendations based on stats
        if stats.get('replay_attacks_detected', 0) > 0:
            report['recommendations'].append(
                'Replay attacks detected - review device security and network'
            )
        
        if total_messages > 10000:
            report['recommendations'].append(
                'High nonce cache size - consider increasing TTL or implementing distributed cache'
            )
        
        return jsonify(report), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@message_signing_bp.route('/health', methods=['GET'])
def signing_health():
    """Health check for signing service"""
    try:
        signing_service = get_message_signing_service()
        
        return jsonify({
            'success': True,
            'status': 'healthy',
            'signing_enabled': True,
            'algorithm': 'HMAC-SHA256'
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'status': 'unhealthy',
            'error': str(e)
        }), 500

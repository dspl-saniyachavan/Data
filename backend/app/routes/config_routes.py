from flask import Blueprint, request, jsonify
from app.models import db
from app.models.system_config import SystemConfig
from app.middleware.auth_middleware import token_required
from datetime import datetime
import json

config_bp = Blueprint('config', __name__, url_prefix='/api/config')

@config_bp.route('/', methods=['GET'])
@token_required
def get_all_configs():
    """Get all configuration settings"""
    try:
        category = request.args.get('category')
        
        if category:
            configs = SystemConfig.query.filter_by(category=category).all()
        else:
            configs = SystemConfig.query.all()
        
        return jsonify({
            'configs': [config.to_dict() for config in configs],
            'count': len(configs)
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@config_bp.route('/public', methods=['GET'])
def get_all_configs_public():
    """Get all configuration settings (public endpoint for testing)"""
    try:
        category = request.args.get('category')
        
        if category:
            configs = SystemConfig.query.filter_by(category=category).all()
        else:
            configs = SystemConfig.query.all()
        
        return jsonify({
            'configs': [config.to_dict() for config in configs],
            'count': len(configs)
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@config_bp.route('/<key>', methods=['GET'])
@token_required
def get_config(key):
    """Get specific configuration by key"""
    try:
        config = SystemConfig.query.filter_by(key=key).first()
        
        if not config:
            return jsonify({'error': 'Configuration not found'}), 404
        
        return jsonify({'config': config.to_dict()}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@config_bp.route('/', methods=['POST'])
@token_required
def create_config():
    """Create new configuration setting"""
    try:
        data = request.get_json()
        user = request.user
        
        # Validate required fields
        if not data.get('key') or not data.get('value'):
            return jsonify({'error': 'Key and value are required'}), 400
        
        # Check if key already exists
        existing = SystemConfig.query.filter_by(key=data['key']).first()
        if existing:
            return jsonify({'error': 'Configuration key already exists'}), 400
        
        config = SystemConfig(
            key=data['key'],
            value=str(data['value']),
            description=data.get('description'),
            category=data.get('category', 'general'),
            data_type=data.get('data_type', 'string'),
            is_sensitive=data.get('is_sensitive', False),
            updated_by=user.get('email')
        )
        
        db.session.add(config)
        db.session.commit()
        
        # Broadcast config change via MQTT
        _broadcast_config_change('created', config)
        
        return jsonify({
            'message': 'Configuration created',
            'config': config.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@config_bp.route('/<key>', methods=['PUT'])
@token_required
def update_config(key):
    """Update existing configuration"""
    try:
        data = request.get_json()
        user = request.user
        
        config = SystemConfig.query.filter_by(key=key).first()
        if not config:
            return jsonify({'error': 'Configuration not found'}), 404
        
        old_value = config.value
        
        # Update fields
        if 'value' in data:
            config.value = str(data['value'])
        if 'description' in data:
            config.description = data['description']
        if 'category' in data:
            config.category = data['category']
        if 'data_type' in data:
            config.data_type = data['data_type']
        if 'is_sensitive' in data:
            config.is_sensitive = data['is_sensitive']
        
        config.updated_by = user.get('email')
        config.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        # Broadcast config change via MQTT
        _broadcast_config_change('updated', config, old_value)
        
        return jsonify({
            'message': 'Configuration updated',
            'config': config.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@config_bp.route('/<key>', methods=['DELETE'])
@token_required
def delete_config(key):
    """Delete configuration"""
    try:
        config = SystemConfig.query.filter_by(key=key).first()
        if not config:
            return jsonify({'error': 'Configuration not found'}), 404
        
        db.session.delete(config)
        db.session.commit()
        
        # Broadcast config deletion via MQTT
        _broadcast_config_change('deleted', config)
        
        return jsonify({'message': 'Configuration deleted'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@config_bp.route('/bulk-update', methods=['PUT'])
@token_required
def bulk_update_configs():
    """Update multiple configurations at once"""
    try:
        data = request.get_json()
        user = request.user
        configs = data.get('configs', [])
        
        if not configs:
            return jsonify({'error': 'No configurations provided'}), 400
        
        updated_count = 0
        updated_configs = []
        
        for config_data in configs:
            key = config_data.get('key')
            value = config_data.get('value')
            
            if not key or value is None:
                continue
            
            config = SystemConfig.query.filter_by(key=key).first()
            if config:
                config.value = str(value)
                config.updated_by = user.get('email')
                config.updated_at = datetime.utcnow()
                updated_count += 1
                updated_configs.append(config)
        
        db.session.commit()
        
        # Broadcast bulk config change
        _broadcast_bulk_config_change(updated_configs)
        
        return jsonify({
            'message': f'Updated {updated_count} configurations',
            'count': updated_count
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@config_bp.route('/categories', methods=['GET'])
@token_required
def get_categories():
    """Get all configuration categories"""
    try:
        categories = db.session.query(SystemConfig.category).distinct().all()
        return jsonify({
            'categories': [cat[0] for cat in categories]
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@config_bp.route('/sync-status', methods=['GET'])
@token_required
def get_sync_status():
    """Get configuration sync status for all devices"""
    try:
        # This would track which devices have synced configs
        # For now, return mock data
        return jsonify({
            'devices': [
                {
                    'device_id': 'desktop-001',
                    'last_sync': datetime.utcnow().isoformat(),
                    'status': 'synced',
                    'config_version': 1
                }
            ]
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def _broadcast_config_change(action, config, old_value=None):
    """Broadcast configuration change via MQTT and Socket.IO"""
    try:
        from app.services.mqtt_publisher import get_mqtt_publisher
        from app import get_socketio
        
        payload = {
            'action': action,
            'key': config.key,
            'value': config.value,
            'old_value': old_value,
            'category': config.category,
            'data_type': config.data_type,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Publish to MQTT
        publisher = get_mqtt_publisher()
        if publisher.connected:
            topic = 'precisionpulse/config/update'
            publisher._publish(topic, payload)
            print(f"[CONFIG] Broadcasted {action} for {config.key} via MQTT")
        
        # Emit via Socket.IO
        socketio = get_socketio()
        if socketio:
            socketio.emit('config_update', payload, namespace='/')
            print(f"[CONFIG] Emitted {action} for {config.key} via Socket.IO")
        
    except Exception as e:
        print(f"[CONFIG] Error broadcasting change: {e}")

def _broadcast_bulk_config_change(configs):
    """Broadcast bulk configuration changes"""
    try:
        from app.services.mqtt_publisher import get_mqtt_publisher
        from app import get_socketio
        
        payload = {
            'action': 'bulk_update',
            'configs': [
                {
                    'key': config.key,
                    'value': config.value,
                    'category': config.category,
                    'data_type': config.data_type
                }
                for config in configs
            ],
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Publish to MQTT
        publisher = get_mqtt_publisher()
        if publisher.connected:
            topic = 'precisionpulse/config/bulk-update'
            publisher._publish(topic, payload)
            print(f"[CONFIG] Broadcasted bulk update via MQTT")
        
        # Emit via Socket.IO
        socketio = get_socketio()
        if socketio:
            socketio.emit('config_bulk_update', payload, namespace='/')
            print(f"[CONFIG] Emitted bulk update via Socket.IO")
        
    except Exception as e:
        print(f"[CONFIG] Error broadcasting bulk change: {e}")

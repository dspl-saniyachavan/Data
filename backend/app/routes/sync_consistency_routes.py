"""
Sync Consistency Routes
Endpoints for managing sync operations and verifying consistency
"""

from flask import Blueprint, jsonify, request
from app.services.sync_ordering_service import sync_ordering_service, SyncOperation
from app.middleware.sync_consistency_middleware import (
    sync_operation, ordered_sync_batch, ensure_idempotent, verify_sync_consistency
)
from app.middleware.auth_middleware import token_required

sync_consistency_bp = Blueprint('sync_consistency', __name__, url_prefix='/api/sync')


@sync_consistency_bp.route('/operations', methods=['GET'])
@token_required
def get_operations():
    """Get recent sync operations"""
    limit = request.args.get('limit', 100, type=int)
    operations = sync_ordering_service.get_operation_log(limit)
    
    return jsonify({
        'total': len(operations),
        'operations': operations
    }), 200


@sync_consistency_bp.route('/operations/<operation_id>', methods=['GET'])
@token_required
def get_operation(operation_id):
    """Get specific sync operation"""
    operation = sync_ordering_service.get_operation_by_id(operation_id)
    
    if not operation:
        return jsonify({'error': 'Operation not found'}), 404
    
    return jsonify(operation), 200


@sync_consistency_bp.route('/verify-consistency', methods=['GET'])
@token_required
def verify_consistency():
    """Verify sync consistency"""
    consistency = sync_ordering_service.verify_consistency()
    
    status_code = 200 if consistency['is_consistent'] else 400
    return jsonify(consistency), status_code


@sync_consistency_bp.route('/batch', methods=['POST'])
@token_required
@ordered_sync_batch()
def sync_batch():
    """Execute batch of sync operations in order"""
    data = request.get_json() or {}
    operations = data.get('operations', [])
    
    if not operations:
        return jsonify({'error': 'No operations provided'}), 400
    
    # Convert to sync operations
    sync_ops = []
    for op in operations:
        try:
            op_type = SyncOperation[op.get('type', 'USER_UPDATE').upper()]
        except KeyError:
            return jsonify({'error': f"Invalid operation type: {op.get('type')}"}), 400
        
        sync_op = sync_ordering_service.create_sync_operation(
            operation_type=op_type,
            entity_id=op.get('entity_id', 'unknown'),
            data=op.get('data', {}),
            source=op.get('source', 'batch')
        )
        sync_ops.append(sync_op)
    
    # Execute operations in order
    results = sync_ordering_service.execute_operations_ordered(sync_ops)
    
    return jsonify(results), 200


@sync_consistency_bp.route('/user/create', methods=['POST'])
@token_required
@sync_operation(SyncOperation.USER_CREATE)
@verify_sync_consistency()
def sync_user_create():
    """Create user with sync ordering"""
    data = request.get_json() or {}
    
    success, result, error = sync_ordering_service.execute_operation(
        sync_ordering_service.create_sync_operation(
            operation_type=SyncOperation.USER_CREATE,
            entity_id=data.get('email', 'unknown'),
            data=data,
            source='api'
        )
    )
    
    if not success:
        return jsonify({'error': error}), 400
    
    return jsonify({'result': result}), 201


@sync_consistency_bp.route('/user/update', methods=['POST'])
@token_required
@sync_operation(SyncOperation.USER_UPDATE)
@ensure_idempotent()
@verify_sync_consistency()
def sync_user_update():
    """Update user with sync ordering"""
    data = request.get_json() or {}
    
    success, result, error = sync_ordering_service.execute_operation(
        sync_ordering_service.create_sync_operation(
            operation_type=SyncOperation.USER_UPDATE,
            entity_id=data.get('email', 'unknown'),
            data=data,
            source='api'
        )
    )
    
    if not success:
        return jsonify({'error': error}), 400
    
    return jsonify({'result': result}), 200


@sync_consistency_bp.route('/user/delete', methods=['POST'])
@token_required
@sync_operation(SyncOperation.USER_DELETE)
@ensure_idempotent()
@verify_sync_consistency()
def sync_user_delete():
    """Delete user with sync ordering"""
    data = request.get_json() or {}
    
    success, result, error = sync_ordering_service.execute_operation(
        sync_ordering_service.create_sync_operation(
            operation_type=SyncOperation.USER_DELETE,
            entity_id=data.get('email', 'unknown'),
            data=data,
            source='api'
        )
    )
    
    if not success:
        return jsonify({'error': error}), 400
    
    return jsonify({'result': result}), 200


@sync_consistency_bp.route('/parameter/create', methods=['POST'])
@token_required
@sync_operation(SyncOperation.PARAMETER_CREATE)
@verify_sync_consistency()
def sync_parameter_create():
    """Create parameter with sync ordering"""
    data = request.get_json() or {}
    
    success, result, error = sync_ordering_service.execute_operation(
        sync_ordering_service.create_sync_operation(
            operation_type=SyncOperation.PARAMETER_CREATE,
            entity_id=data.get('name', 'unknown'),
            data=data,
            source='api'
        )
    )
    
    if not success:
        return jsonify({'error': error}), 400
    
    return jsonify({'result': result}), 201


@sync_consistency_bp.route('/parameter/update', methods=['POST'])
@token_required
@sync_operation(SyncOperation.PARAMETER_UPDATE)
@ensure_idempotent()
@verify_sync_consistency()
def sync_parameter_update():
    """Update parameter with sync ordering"""
    data = request.get_json() or {}
    
    success, result, error = sync_ordering_service.execute_operation(
        sync_ordering_service.create_sync_operation(
            operation_type=SyncOperation.PARAMETER_UPDATE,
            entity_id=data.get('id') or data.get('name', 'unknown'),
            data=data,
            source='api'
        )
    )
    
    if not success:
        return jsonify({'error': error}), 400
    
    return jsonify({'result': result}), 200


@sync_consistency_bp.route('/parameter/delete', methods=['POST'])
@token_required
@sync_operation(SyncOperation.PARAMETER_DELETE)
@ensure_idempotent()
@verify_sync_consistency()
def sync_parameter_delete():
    """Delete parameter with sync ordering"""
    data = request.get_json() or {}
    
    success, result, error = sync_ordering_service.execute_operation(
        sync_ordering_service.create_sync_operation(
            operation_type=SyncOperation.PARAMETER_DELETE,
            entity_id=data.get('id') or data.get('name', 'unknown'),
            data=data,
            source='api'
        )
    )
    
    if not success:
        return jsonify({'error': error}), 400
    
    return jsonify({'result': result}), 200


@sync_consistency_bp.route('/role/change', methods=['POST'])
@token_required
@sync_operation(SyncOperation.ROLE_CHANGE)
@ensure_idempotent()
@verify_sync_consistency()
def sync_role_change():
    """Change user role with sync ordering"""
    data = request.get_json() or {}
    
    success, result, error = sync_ordering_service.execute_operation(
        sync_ordering_service.create_sync_operation(
            operation_type=SyncOperation.ROLE_CHANGE,
            entity_id=data.get('email', 'unknown'),
            data=data,
            source='api'
        )
    )
    
    if not success:
        return jsonify({'error': error}), 400
    
    return jsonify({'result': result}), 200


@sync_consistency_bp.route('/permissions/change', methods=['POST'])
@token_required
@sync_operation(SyncOperation.PERMISSION_CHANGE)
@verify_sync_consistency()
def sync_permission_change():
    """Change role permissions with sync ordering"""
    data = request.get_json() or {}
    
    success, result, error = sync_ordering_service.execute_operation(
        sync_ordering_service.create_sync_operation(
            operation_type=SyncOperation.PERMISSION_CHANGE,
            entity_id=data.get('role', 'unknown'),
            data=data,
            source='api'
        )
    )
    
    if not success:
        return jsonify({'error': error}), 400
    
    return jsonify({'result': result}), 200

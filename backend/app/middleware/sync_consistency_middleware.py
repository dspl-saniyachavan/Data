"""
Sync Consistency Middleware
Enforces ordering, idempotency, and consistency for sync operations
"""

from functools import wraps
from flask import request, jsonify
from app.services.sync_ordering_service import sync_ordering_service, SyncOperation
import logging

logger = logging.getLogger(__name__)


def sync_operation(operation_type: SyncOperation):
    """
    Decorator to track and enforce consistency for sync operations
    
    Usage:
        @sync_operation(SyncOperation.USER_CREATE)
        def create_user():
            ...
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                # Extract entity ID from request
                data = request.get_json() or {}
                entity_id = data.get('id') or data.get('email') or data.get('name') or 'unknown'
                source = data.get('source', 'api')
                
                # Create sync operation
                operation = sync_ordering_service.create_sync_operation(
                    operation_type=operation_type,
                    entity_id=entity_id,
                    data=data,
                    source=source
                )
                
                # Execute the actual endpoint
                result = f(*args, **kwargs)
                
                # Mark operation as completed
                operation['status'] = 'completed'
                
                # If result is a tuple (response, status_code), extract response
                if isinstance(result, tuple):
                    response_data = result[0]
                    status_code = result[1]
                else:
                    response_data = result
                    status_code = 200
                
                # Add operation tracking to response
                if isinstance(response_data, dict):
                    response_data['_operation_id'] = operation['operation_id']
                    response_data['_sequence'] = operation['sequence']
                
                return (response_data, status_code) if isinstance(result, tuple) else response_data
            
            except Exception as e:
                logger.error(f"Sync operation error: {str(e)}")
                return jsonify({'error': str(e), 'operation_type': operation_type.value}), 500
        
        return decorated_function
    return decorator


def ordered_sync_batch():
    """
    Decorator for batch sync operations
    Ensures all operations in batch execute in order with consistency
    
    Usage:
        @ordered_sync_batch()
        def sync_batch():
            ...
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                data = request.get_json() or {}
                operations = data.get('operations', [])
                
                if not operations:
                    return jsonify({'error': 'No operations provided'}), 400
                
                # Convert to sync operations
                sync_ops = []
                for op in operations:
                    op_type = SyncOperation[op.get('type', 'USER_UPDATE').upper()]
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
            
            except Exception as e:
                logger.error(f"Batch sync error: {str(e)}")
                return jsonify({'error': str(e)}), 500
        
        return decorated_function
    return decorator


def ensure_idempotent():
    """
    Decorator to ensure operation is idempotent
    Uses operation_id from request to detect replays
    
    Usage:
        @ensure_idempotent()
        def update_user():
            ...
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                data = request.get_json() or {}
                operation_id = data.get('_operation_id')
                
                if operation_id:
                    # Check if operation already executed
                    cached = sync_ordering_service.idempotency_cache.get(operation_id)
                    if cached:
                        logger.info(f"Idempotent replay detected: {operation_id}")
                        return jsonify({
                            'message': 'Operation already executed',
                            'result': cached['result'],
                            'executed_at': cached['executed_at'],
                            'is_replay': True
                        }), 200
                
                # Execute the actual endpoint
                result = f(*args, **kwargs)
                
                # Add operation ID to response for future replays
                if isinstance(result, dict):
                    result['_operation_id'] = operation_id
                
                return result
            
            except Exception as e:
                logger.error(f"Idempotency check error: {str(e)}")
                return jsonify({'error': str(e)}), 500
        
        return decorated_function
    return decorator


def verify_sync_consistency():
    """
    Decorator to verify sync consistency after operation
    
    Usage:
        @verify_sync_consistency()
        def critical_sync_operation():
            ...
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                # Execute the actual endpoint
                result = f(*args, **kwargs)
                
                # Verify consistency
                consistency = sync_ordering_service.verify_consistency()
                
                # Add consistency info to response
                if isinstance(result, tuple):
                    response_data = result[0]
                    status_code = result[1]
                else:
                    response_data = result
                    status_code = 200
                
                if isinstance(response_data, dict):
                    response_data['_consistency'] = {
                        'is_consistent': consistency['is_consistent'],
                        'issues': consistency['issues']
                    }
                
                return (response_data, status_code) if isinstance(result, tuple) else response_data
            
            except Exception as e:
                logger.error(f"Consistency verification error: {str(e)}")
                return jsonify({'error': str(e)}), 500
        
        return decorated_function
    return decorator

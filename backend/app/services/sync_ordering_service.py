"""
Sync Ordering and Consistency Service
Ensures sync operations are repeatable, ordered, and produce consistent state
"""

from datetime import datetime
from typing import Dict, Any, List, Tuple, Optional
from enum import Enum
import json
import logging
from app.models import db

logger = logging.getLogger(__name__)


class SyncOperation(Enum):
    """Types of sync operations"""
    USER_CREATE = "user_create"
    USER_UPDATE = "user_update"
    USER_DELETE = "user_delete"
    PARAMETER_CREATE = "parameter_create"
    PARAMETER_UPDATE = "parameter_update"
    PARAMETER_DELETE = "parameter_delete"
    ROLE_CHANGE = "role_change"
    PERMISSION_CHANGE = "permission_change"


class SyncOrderingService:
    """Manages sync operation ordering and consistency"""
    
    def __init__(self):
        self.operation_log = []
        self.sequence_counter = 0
        self.idempotency_cache = {}  # Maps operation_id -> result
        self.state_snapshots = {}  # Maps sequence -> state hash
    
    def create_sync_operation(self, operation_type: SyncOperation, entity_id: str, 
                             data: Dict[str, Any], source: str = "unknown") -> Dict[str, Any]:
        """
        Create a sync operation with ordering metadata
        
        Args:
            operation_type: Type of operation
            entity_id: ID of entity being synced
            data: Operation data
            source: Source of operation (backend, desktop, frontend)
        
        Returns:
            Operation with sequence number and idempotency key
        """
        self.sequence_counter += 1
        operation_id = f"{source}_{operation_type.value}_{entity_id}_{self.sequence_counter}"
        
        operation = {
            'operation_id': operation_id,
            'sequence': self.sequence_counter,
            'type': operation_type.value,
            'entity_id': entity_id,
            'data': data,
            'source': source,
            'timestamp': datetime.utcnow().isoformat(),
            'status': 'pending'
        }
        
        self.operation_log.append(operation)
        logger.info(f"Created sync operation: {operation_id} (seq: {self.sequence_counter})")
        
        return operation
    
    def execute_operation(self, operation: Dict[str, Any]) -> Tuple[bool, Any, Optional[str]]:
        """
        Execute sync operation with idempotency guarantee
        
        Args:
            operation: Operation to execute
        
        Returns:
            Tuple of (success, result, error_message)
        """
        operation_id = operation['operation_id']
        
        # Check idempotency cache
        if operation_id in self.idempotency_cache:
            cached_result = self.idempotency_cache[operation_id]
            logger.info(f"Operation {operation_id} already executed (cached)")
            return (cached_result['success'], cached_result['result'], cached_result.get('error'))
        
        try:
            op_type = operation['type']
            data = operation['data']
            
            if op_type == SyncOperation.USER_CREATE.value:
                result = self._execute_user_create(data)
            elif op_type == SyncOperation.USER_UPDATE.value:
                result = self._execute_user_update(data)
            elif op_type == SyncOperation.USER_DELETE.value:
                result = self._execute_user_delete(data)
            elif op_type == SyncOperation.PARAMETER_CREATE.value:
                result = self._execute_parameter_create(data)
            elif op_type == SyncOperation.PARAMETER_UPDATE.value:
                result = self._execute_parameter_update(data)
            elif op_type == SyncOperation.PARAMETER_DELETE.value:
                result = self._execute_parameter_delete(data)
            elif op_type == SyncOperation.ROLE_CHANGE.value:
                result = self._execute_role_change(data)
            elif op_type == SyncOperation.PERMISSION_CHANGE.value:
                result = self._execute_permission_change(data)
            else:
                raise ValueError(f"Unknown operation type: {op_type}")
            
            # Cache successful result
            self.idempotency_cache[operation_id] = {
                'success': True,
                'result': result,
                'executed_at': datetime.utcnow().isoformat()
            }
            
            # Update operation status
            operation['status'] = 'completed'
            operation['result'] = result
            operation['completed_at'] = datetime.utcnow().isoformat()
            
            logger.info(f"Operation {operation_id} completed successfully")
            return (True, result, None)
        
        except Exception as e:
            error_msg = str(e)
            
            # Cache error for idempotency
            self.idempotency_cache[operation_id] = {
                'success': False,
                'result': None,
                'error': error_msg,
                'executed_at': datetime.utcnow().isoformat()
            }
            
            operation['status'] = 'failed'
            operation['error'] = error_msg
            operation['failed_at'] = datetime.utcnow().isoformat()
            
            logger.error(f"Operation {operation_id} failed: {error_msg}")
            return (False, None, error_msg)
    
    def execute_operations_ordered(self, operations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Execute multiple operations in order with transaction boundaries
        
        Args:
            operations: List of operations to execute in order
        
        Returns:
            Summary of execution results
        """
        results = {
            'total': len(operations),
            'succeeded': 0,
            'failed': 0,
            'operations': [],
            'started_at': datetime.utcnow().isoformat()
        }
        
        for operation in operations:
            success, result, error = self.execute_operation(operation)
            
            results['operations'].append({
                'operation_id': operation['operation_id'],
                'sequence': operation['sequence'],
                'success': success,
                'result': result,
                'error': error
            })
            
            if success:
                results['succeeded'] += 1
            else:
                results['failed'] += 1
                # Stop on first failure to maintain consistency
                logger.warning(f"Stopping batch execution due to failure in {operation['operation_id']}")
                break
        
        results['completed_at'] = datetime.utcnow().isoformat()
        return results
    
    def _execute_user_create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute user create operation"""
        from app.models.user import User
        
        email = data.get('email')
        if not email:
            raise ValueError("Email required for user create")
        
        # Check if user already exists (idempotency)
        existing = User.query.filter_by(email=email).first()
        if existing:
            logger.info(f"User {email} already exists, returning existing user")
            return {'user_id': existing.id, 'email': email, 'action': 'already_exists'}
        
        user = User(
            email=email,
            name=data.get('name', ''),
            password_hash=data.get('password_hash', ''),
            role=data.get('role', 'user'),
            is_active=data.get('is_active', True)
        )
        db.session.add(user)
        db.session.commit()
        
        return {'user_id': user.id, 'email': email, 'action': 'created'}
    
    def _execute_user_update(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute user update operation"""
        from app.models.user import User
        
        email = data.get('email')
        if not email:
            raise ValueError("Email required for user update")
        
        user = User.query.filter_by(email=email).first()
        if not user:
            raise ValueError(f"User {email} not found")
        
        # Update only provided fields
        if 'name' in data:
            user.name = data['name']
        if 'role' in data:
            user.role = data['role']
        if 'is_active' in data:
            user.is_active = data['is_active']
        
        user.updated_at = datetime.utcnow()
        db.session.commit()
        
        return {'user_id': user.id, 'email': email, 'action': 'updated'}
    
    def _execute_user_delete(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute user delete operation"""
        from app.models.user import User
        
        email = data.get('email')
        if not email:
            raise ValueError("Email required for user delete")
        
        user = User.query.filter_by(email=email).first()
        if not user:
            logger.info(f"User {email} not found, treating as already deleted")
            return {'email': email, 'action': 'already_deleted'}
        
        db.session.delete(user)
        db.session.commit()
        
        return {'email': email, 'action': 'deleted'}
    
    def _execute_parameter_create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute parameter create operation"""
        from app.models.parameter import Parameter
        
        name = data.get('name')
        if not name:
            raise ValueError("Name required for parameter create")
        
        # Check if parameter already exists (idempotency)
        existing = Parameter.query.filter_by(name=name).first()
        if existing:
            logger.info(f"Parameter {name} already exists, returning existing parameter")
            return {'parameter_id': existing.id, 'name': name, 'action': 'already_exists'}
        
        param = Parameter(
            name=name,
            unit=data.get('unit', ''),
            description=data.get('description', ''),
            enabled=data.get('enabled', True)
        )
        db.session.add(param)
        db.session.commit()
        
        return {'parameter_id': param.id, 'name': name, 'action': 'created'}
    
    def _execute_parameter_update(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute parameter update operation"""
        from app.models.parameter import Parameter
        
        param_id = data.get('id')
        name = data.get('name')
        
        if not param_id and not name:
            raise ValueError("Parameter ID or name required for update")
        
        if param_id:
            param = Parameter.query.get(param_id)
        else:
            param = Parameter.query.filter_by(name=name).first()
        
        if not param:
            raise ValueError(f"Parameter not found")
        
        # Update only provided fields
        if 'name' in data:
            param.name = data['name']
        if 'unit' in data:
            param.unit = data['unit']
        if 'description' in data:
            param.description = data['description']
        if 'enabled' in data:
            param.enabled = data['enabled']
        
        param.updated_at = datetime.utcnow()
        db.session.commit()
        
        return {'parameter_id': param.id, 'name': param.name, 'action': 'updated'}
    
    def _execute_parameter_delete(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute parameter delete operation"""
        from app.models.parameter import Parameter
        
        param_id = data.get('id')
        name = data.get('name')
        
        if not param_id and not name:
            raise ValueError("Parameter ID or name required for delete")
        
        if param_id:
            param = Parameter.query.get(param_id)
        else:
            param = Parameter.query.filter_by(name=name).first()
        
        if not param:
            logger.info(f"Parameter not found, treating as already deleted")
            return {'name': name or param_id, 'action': 'already_deleted'}
        
        db.session.delete(param)
        db.session.commit()
        
        return {'parameter_id': param.id, 'name': param.name, 'action': 'deleted'}
    
    def _execute_role_change(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute role change operation"""
        from app.models.user import User
        
        email = data.get('email')
        new_role = data.get('new_role')
        
        if not email or not new_role:
            raise ValueError("Email and new_role required for role change")
        
        user = User.query.filter_by(email=email).first()
        if not user:
            raise ValueError(f"User {email} not found")
        
        old_role = user.role
        user.role = new_role
        user.updated_at = datetime.utcnow()
        db.session.commit()
        
        return {'email': email, 'old_role': old_role, 'new_role': new_role, 'action': 'role_changed'}
    
    def _execute_permission_change(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute permission change operation"""
        # This is a placeholder for permission management
        # Actual implementation depends on permission storage model
        role = data.get('role')
        permissions = data.get('permissions', [])
        
        if not role:
            raise ValueError("Role required for permission change")
        
        logger.info(f"Permission change for role {role}: {permissions}")
        return {'role': role, 'permissions': permissions, 'action': 'permissions_changed'}
    
    def get_operation_log(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent operation log"""
        return self.operation_log[-limit:]
    
    def get_operation_by_id(self, operation_id: str) -> Optional[Dict[str, Any]]:
        """Get operation by ID"""
        for op in self.operation_log:
            if op['operation_id'] == operation_id:
                return op
        return None
    
    def verify_consistency(self) -> Dict[str, Any]:
        """
        Verify sync consistency by checking:
        - All operations executed in sequence
        - No gaps in sequence numbers
        - All operations have consistent state
        """
        from app.models.user import User
        from app.models.parameter import Parameter
        
        issues = []
        
        # Check sequence continuity
        sequences = sorted([op['sequence'] for op in self.operation_log])
        if sequences:
            for i, seq in enumerate(sequences, 1):
                if seq != i:
                    issues.append(f"Sequence gap: expected {i}, got {seq}")
        
        # Check database consistency
        users = User.query.all()
        parameters = Parameter.query.all()
        
        # Verify all users have updated_at
        for user in users:
            if not user.updated_at:
                issues.append(f"User {user.email} missing updated_at")
        
        # Verify all parameters have updated_at
        for param in parameters:
            if not param.updated_at:
                issues.append(f"Parameter {param.name} missing updated_at")
        
        return {
            'is_consistent': len(issues) == 0,
            'total_operations': len(self.operation_log),
            'total_users': len(users),
            'total_parameters': len(parameters),
            'issues': issues,
            'verified_at': datetime.utcnow().isoformat()
        }
    
    def clear_cache(self):
        """Clear idempotency cache (use with caution)"""
        self.idempotency_cache.clear()
        logger.warning("Idempotency cache cleared")
    
    def reset(self):
        """Reset service state (use with caution)"""
        self.operation_log.clear()
        self.sequence_counter = 0
        self.idempotency_cache.clear()
        self.state_snapshots.clear()
        logger.warning("Sync ordering service reset")


# Global instance
sync_ordering_service = SyncOrderingService()

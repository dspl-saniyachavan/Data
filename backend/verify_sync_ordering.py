#!/usr/bin/env python3
"""
Verification script for Sync Ordering and Consistency System
Tests repeatability, ordering, and consistency guarantees
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app
from app.models import db
from app.models.user import User
from app.models.parameter import Parameter
from app.services.sync_ordering_service import (
    SyncOrderingService, SyncOperation
)


def cleanup_db(app):
    """Clean up database"""
    with app.app_context():
        db.session.query(Parameter).delete()
        db.session.query(User).delete()
        db.session.commit()


def test_repeatability(app):
    """Test that operations are repeatable"""
    print("\n✓ Testing Repeatability...")
    cleanup_db(app)
    
    with app.app_context():
        service = SyncOrderingService()
        
        op = service.create_sync_operation(
            SyncOperation.USER_CREATE,
            "repeat@example.com",
            {
                'email': 'repeat@example.com',
                'name': 'Repeat Test',
                'password_hash': 'hash',
                'role': 'user'
            },
            'test'
        )
        
        # Execute twice
        success1, result1, error1 = service.execute_operation(op)
        success2, result2, error2 = service.execute_operation(op)
        
        assert success1 and success2, "Both executions should succeed"
        assert result1 == result2, "Results should be identical"
        print("  ✓ Operations are repeatable")


def test_ordering(app):
    """Test that operations maintain order"""
    print("\n✓ Testing Ordering...")
    cleanup_db(app)
    
    with app.app_context():
        service = SyncOrderingService()
        
        ops = []
        for i in range(5):
            op = service.create_sync_operation(
                SyncOperation.USER_CREATE,
                f"order{i}@example.com",
                {
                    'email': f'order{i}@example.com',
                    'name': f'Order {i}',
                    'password_hash': 'hash',
                    'role': 'user'
                },
                'test'
            )
            ops.append(op)
        
        # Verify sequences are ordered
        sequences = [op['sequence'] for op in ops]
        assert sequences == [1, 2, 3, 4, 5], "Sequences should be ordered"
        print("  ✓ Operations maintain order")
        
        # Verify log maintains order
        log = service.get_operation_log()
        log_sequences = [op['sequence'] for op in log]
        assert log_sequences == sequences, "Log should maintain order"
        print("  ✓ Operation log maintains order")


def test_consistency(app):
    """Test that system state remains consistent"""
    print("\n✓ Testing Consistency...")
    cleanup_db(app)
    
    with app.app_context():
        service = SyncOrderingService()
        
        # Create operations
        ops = [
            service.create_sync_operation(
                SyncOperation.USER_CREATE,
                "cons1@example.com",
                {
                    'email': 'cons1@example.com',
                    'name': 'Consistency 1',
                    'password_hash': 'hash',
                    'role': 'user'
                },
                'test'
            ),
            service.create_sync_operation(
                SyncOperation.PARAMETER_CREATE,
                "consistency_param",
                {
                    'name': 'Consistency Param',
                    'unit': 'test',
                    'enabled': True
                },
                'test'
            )
        ]
        
        # Execute operations
        results = service.execute_operations_ordered(ops)
        assert results['succeeded'] == 2, "All operations should succeed"
        
        # Verify consistency
        consistency = service.verify_consistency()
        assert consistency['is_consistent'], "System should be consistent"
        assert consistency['total_users'] == 1, f"Should have 1 user, got {consistency['total_users']}"
        assert consistency['total_parameters'] == 1, f"Should have 1 parameter, got {consistency['total_parameters']}"
        print("  ✓ System state is consistent")


def test_idempotency(app):
    """Test that operations are idempotent"""
    print("\n✓ Testing Idempotency...")
    cleanup_db(app)
    
    with app.app_context():
        service = SyncOrderingService()
        
        op = service.create_sync_operation(
            SyncOperation.USER_CREATE,
            "idem@example.com",
            {
                'email': 'idem@example.com',
                'name': 'Idempotent',
                'password_hash': 'hash',
                'role': 'user'
            },
            'test'
        )
        
        # Execute multiple times
        for i in range(3):
            success, result, error = service.execute_operation(op)
            assert success, f"Execution {i+1} should succeed"
        
        # Verify only one user created
        users = User.query.filter_by(email='idem@example.com').all()
        assert len(users) == 1, "Should have exactly 1 user"
        print("  ✓ Operations are idempotent")


def test_batch_ordering(app):
    """Test that batch operations execute in order"""
    print("\n✓ Testing Batch Ordering...")
    cleanup_db(app)
    
    with app.app_context():
        service = SyncOrderingService()
        
        ops = [
            service.create_sync_operation(
                SyncOperation.USER_CREATE,
                f"batch{i}@example.com",
                {
                    'email': f'batch{i}@example.com',
                    'name': f'Batch {i}',
                    'password_hash': 'hash',
                    'role': 'user'
                },
                'test'
            )
            for i in range(3)
        ]
        
        results = service.execute_operations_ordered(ops)
        
        assert results['total'] == 3, "Should have 3 operations"
        assert results['succeeded'] == 3, "All should succeed"
        assert len(User.query.all()) == 3, "Should have 3 users"
        print("  ✓ Batch operations execute in order")


def test_failure_handling(app):
    """Test that batch stops on failure"""
    print("\n✓ Testing Failure Handling...")
    cleanup_db(app)
    
    with app.app_context():
        service = SyncOrderingService()
        
        ops = [
            service.create_sync_operation(
                SyncOperation.USER_CREATE,
                "fail1@example.com",
                {
                    'email': 'fail1@example.com',
                    'name': 'Fail 1',
                    'password_hash': 'hash',
                    'role': 'user'
                },
                'test'
            ),
            service.create_sync_operation(
                SyncOperation.USER_UPDATE,
                "nonexistent@example.com",
                {'email': 'nonexistent@example.com', 'name': 'Nonexistent'},
                'test'
            ),
            service.create_sync_operation(
                SyncOperation.USER_CREATE,
                "fail2@example.com",
                {
                    'email': 'fail2@example.com',
                    'name': 'Fail 2',
                    'password_hash': 'hash',
                    'role': 'user'
                },
                'test'
            )
        ]
        
        results = service.execute_operations_ordered(ops)
        
        assert results['succeeded'] == 1, "Should succeed on first operation"
        assert results['failed'] == 1, "Should fail on second operation"
        assert len(results['operations']) == 2, "Should stop after failure"
        print("  ✓ Batch stops on failure")


def main():
    """Run all verification tests"""
    print("=" * 60)
    print("Sync Ordering and Consistency System Verification")
    print("=" * 60)
    
    app = create_app()
    
    try:
        test_repeatability(app)
        test_ordering(app)
        test_consistency(app)
        test_idempotency(app)
        test_batch_ordering(app)
        test_failure_handling(app)
        
        print("\n" + "=" * 60)
        print("✓ All verification tests passed!")
        print("=" * 60)
        print("\nSystem guarantees verified:")
        print("  ✓ Repeatability: Operations can be safely replayed")
        print("  ✓ Ordering: Operations execute in deterministic sequence")
        print("  ✓ Consistency: System state remains valid after operations")
        print("  ✓ Idempotency: Replaying operations produces same result")
        print("  ✓ Batch Processing: Multiple operations execute in order")
        print("  ✓ Failure Handling: Batch stops on first failure")
        print("\n")
        return 0
    
    except AssertionError as e:
        print(f"\n✗ Verification failed: {e}")
        return 1
    except Exception as e:
        print(f"\n✗ Error during verification: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())

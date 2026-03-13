"""
Conflict Resolution Middleware for Flask API
Automatically resolves conflicts using timestamp-based strategy
"""

from functools import wraps
from flask import request, jsonify
from datetime import datetime
from app.services.conflict_resolver import ConflictResolver
import logging

logger = logging.getLogger(__name__)


def resolve_conflicts(f):
    """
    Decorator to automatically resolve conflicts in API requests
    Expects request body to have 'local' and 'remote' data with 'updated_at' timestamps
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            data = request.get_json()
            
            # Check if this is a conflict resolution request
            if data and 'local' in data and 'remote' in data:
                local = data.get('local')
                remote = data.get('remote')
                
                # Resolve conflict
                resolved, strategy = ConflictResolver.resolve_conflict(local, remote)
                
                # Add resolution metadata
                data['resolved_data'] = resolved
                data['resolution_strategy'] = strategy
                data['resolved_at'] = datetime.utcnow().isoformat()
                
                logger.info(f"Conflict resolved using strategy: {strategy}")
                
                # Update request with resolved data
                request.resolved_data = resolved
                request.resolution_strategy = strategy
            
            return f(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in conflict resolution: {e}")
            return jsonify({'error': str(e)}), 500
    
    return decorated_function


def batch_resolve_conflicts(f):
    """
    Decorator to resolve multiple conflicts in batch
    Expects request body to have 'conflicts' array
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            data = request.get_json()
            
            if data and 'conflicts' in data:
                conflicts = data.get('conflicts', [])
                
                # Resolve all conflicts
                resolved = ConflictResolver.resolve_conflicts_batch(conflicts)
                
                # Add resolution metadata
                data['resolved_conflicts'] = resolved
                data['total_resolved'] = len(resolved)
                data['resolved_at'] = datetime.utcnow().isoformat()
                
                logger.info(f"Batch resolved {len(resolved)} conflicts")
                
                # Update request
                request.resolved_conflicts = resolved
            
            return f(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in batch conflict resolution: {e}")
            return jsonify({'error': str(e)}), 500
    
    return decorated_function


def detect_and_resolve_conflicts(f):
    """
    Decorator to detect and resolve conflicts between local and remote records
    Expects request body to have 'local_records' and 'remote_records' arrays
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            data = request.get_json()
            
            if data and 'local_records' in data and 'remote_records' in data:
                local_records = data.get('local_records', [])
                remote_records = data.get('remote_records', [])
                
                # Detect conflicts
                conflicts = ConflictResolver.detect_conflicts(local_records, remote_records)
                
                if conflicts:
                    # Resolve detected conflicts
                    resolved = ConflictResolver.resolve_conflicts_batch(
                        [{'id': c['id'], 'local': c['local'], 'remote': c['remote']} for c in conflicts]
                    )
                    
                    # Get summary
                    summary = ConflictResolver.get_conflict_summary(conflicts)
                    
                    # Add to request
                    request.detected_conflicts = conflicts
                    request.resolved_conflicts = resolved
                    request.conflict_summary = summary
                    
                    logger.info(f"Detected {len(conflicts)} conflicts, resolved all")
                else:
                    request.detected_conflicts = []
                    request.resolved_conflicts = []
                    request.conflict_summary = {
                        'total_conflicts': 0,
                        'local_wins': 0,
                        'remote_wins': 0
                    }
                    logger.info("No conflicts detected")
            
            return f(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in conflict detection and resolution: {e}")
            return jsonify({'error': str(e)}), 500
    
    return decorated_function

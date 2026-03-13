"""
Conflict Resolution API Routes
Endpoints for resolving data conflicts using timestamp-based strategy
"""

from flask import Blueprint, request, jsonify
from app.services.conflict_resolver import ConflictResolver
from app.middleware.conflict_resolution_middleware import (
    resolve_conflicts, batch_resolve_conflicts, detect_and_resolve_conflicts
)
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

conflict_routes = Blueprint('conflicts', __name__, url_prefix='/api/conflicts')


@conflict_routes.route('/resolve', methods=['POST'])
@resolve_conflicts
def resolve_single_conflict():
    """
    Resolve a single conflict between local and remote data
    
    Request body:
    {
        "local": {..., "updated_at": "2024-01-15T10:30:45.123Z"},
        "remote": {..., "updated_at": "2024-01-15T10:35:45.123Z"}
    }
    
    Response:
    {
        "resolved_data": {...},
        "resolution_strategy": "remote",
        "local_timestamp": "2024-01-15T10:30:45.123Z",
        "remote_timestamp": "2024-01-15T10:35:45.123Z",
        "resolved_at": "2024-01-15T10:36:00.000Z"
    }
    """
    try:
        data = request.get_json()
        local = data.get('local')
        remote = data.get('remote')
        
        if not local or not remote:
            return jsonify({'error': 'Both local and remote data required'}), 400
        
        resolved, strategy = ConflictResolver.resolve_conflict(local, remote)
        
        return jsonify({
            'resolved_data': resolved,
            'resolution_strategy': strategy,
            'local_timestamp': ConflictResolver._get_timestamp(local).isoformat() if ConflictResolver._get_timestamp(local) else None,
            'remote_timestamp': ConflictResolver._get_timestamp(remote).isoformat() if ConflictResolver._get_timestamp(remote) else None,
            'resolved_at': datetime.utcnow().isoformat()
        }), 200
    except Exception as e:
        logger.error(f"Error resolving conflict: {e}")
        return jsonify({'error': str(e)}), 500


@conflict_routes.route('/resolve-batch', methods=['POST'])
@batch_resolve_conflicts
def resolve_batch_conflicts():
    """
    Resolve multiple conflicts in batch
    
    Request body:
    {
        "conflicts": [
            {
                "id": 1,
                "local": {..., "updated_at": "..."},
                "remote": {..., "updated_at": "..."}
            },
            ...
        ]
    }
    
    Response:
    {
        "resolved_conflicts": [
            {
                "id": 1,
                "data": {...},
                "strategy": "remote",
                "resolved_at": "..."
            },
            ...
        ],
        "total_resolved": 2,
        "resolved_at": "..."
    }
    """
    try:
        data = request.get_json()
        conflicts = data.get('conflicts', [])
        
        if not conflicts:
            return jsonify({'error': 'Conflicts array required'}), 400
        
        resolved = ConflictResolver.resolve_conflicts_batch(conflicts)
        
        return jsonify({
            'resolved_conflicts': resolved,
            'total_resolved': len(resolved),
            'resolved_at': datetime.utcnow().isoformat()
        }), 200
    except Exception as e:
        logger.error(f"Error resolving batch conflicts: {e}")
        return jsonify({'error': str(e)}), 500


@conflict_routes.route('/detect', methods=['POST'])
@detect_and_resolve_conflicts
def detect_conflicts():
    """
    Detect conflicts between local and remote records
    
    Request body:
    {
        "local_records": [{...}, ...],
        "remote_records": [{...}, ...]
    }
    
    Response:
    {
        "detected_conflicts": [
            {
                "id": 1,
                "local": {...},
                "remote": {...},
                "local_timestamp": "...",
                "remote_timestamp": "...",
                "detected_at": "..."
            },
            ...
        ],
        "resolved_conflicts": [...],
        "summary": {
            "total_conflicts": 2,
            "local_wins": 1,
            "remote_wins": 1,
            "local_win_percentage": 50.0,
            "remote_win_percentage": 50.0
        }
    }
    """
    try:
        data = request.get_json()
        local_records = data.get('local_records', [])
        remote_records = data.get('remote_records', [])
        
        if not local_records or not remote_records:
            return jsonify({'error': 'Both local_records and remote_records required'}), 400
        
        conflicts = ConflictResolver.detect_conflicts(local_records, remote_records)
        
        if conflicts:
            resolved = ConflictResolver.resolve_conflicts_batch(
                [{'id': c['id'], 'local': c['local'], 'remote': c['remote']} for c in conflicts]
            )
            summary = ConflictResolver.get_conflict_summary(conflicts)
        else:
            resolved = []
            summary = {
                'total_conflicts': 0,
                'local_wins': 0,
                'remote_wins': 0,
                'local_win_percentage': 0,
                'remote_win_percentage': 0
            }
        
        return jsonify({
            'detected_conflicts': conflicts,
            'resolved_conflicts': resolved,
            'summary': summary
        }), 200
    except Exception as e:
        logger.error(f"Error detecting conflicts: {e}")
        return jsonify({'error': str(e)}), 500


@conflict_routes.route('/merge-fields', methods=['POST'])
def merge_field_changes():
    """
    Merge changes field-by-field using per-field timestamps
    
    Request body:
    {
        "local": {...},
        "remote": {...},
        "field_timestamps": {
            "name": {"local": "...", "remote": "..."},
            "email": {"local": "...", "remote": "..."}
        }
    }
    
    Response:
    {
        "merged_data": {...},
        "conflict_resolved": true,
        "merged_at": "..."
    }
    """
    try:
        data = request.get_json()
        local = data.get('local')
        remote = data.get('remote')
        field_timestamps = data.get('field_timestamps', {})
        
        if not local or not remote:
            return jsonify({'error': 'Both local and remote data required'}), 400
        
        merged = ConflictResolver.merge_field_changes(local, remote, field_timestamps)
        
        return jsonify({
            'merged_data': merged,
            'conflict_resolved': merged.get('conflict_resolved', False),
            'merged_at': datetime.utcnow().isoformat()
        }), 200
    except Exception as e:
        logger.error(f"Error merging field changes: {e}")
        return jsonify({'error': str(e)}), 500


@conflict_routes.route('/summary', methods=['POST'])
def get_conflict_summary():
    """
    Get summary statistics of conflicts
    
    Request body:
    {
        "conflicts": [...]
    }
    
    Response:
    {
        "total_conflicts": 10,
        "local_wins": 6,
        "remote_wins": 4,
        "local_win_percentage": 60.0,
        "remote_win_percentage": 40.0
    }
    """
    try:
        data = request.get_json()
        conflicts = data.get('conflicts', [])
        
        if not conflicts:
            return jsonify({'error': 'Conflicts array required'}), 400
        
        summary = ConflictResolver.get_conflict_summary(conflicts)
        
        return jsonify(summary), 200
    except Exception as e:
        logger.error(f"Error generating conflict summary: {e}")
        return jsonify({'error': str(e)}), 500

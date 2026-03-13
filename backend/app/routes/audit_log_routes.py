"""
Audit Log Routes
API endpoints for querying and analyzing audit logs
"""

from flask import Blueprint, jsonify, request
from datetime import datetime, timedelta
from app.services.audit_logging_service import get_audit_logging_service
from functools import wraps

audit_log_bp = Blueprint('audit_logs', __name__, url_prefix='/api/audit')


def require_admin(f):
    """Decorator to require admin role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from flask import g
        if not hasattr(g, 'user') or g.user.get('role') != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        return f(*args, **kwargs)
    return decorated_function


@audit_log_bp.route('/logs', methods=['GET'])
@require_admin
def get_audit_logs():
    """Get audit logs with filtering"""
    try:
        audit_service = get_audit_logging_service()
        
        # Get query parameters
        event_type = request.args.get('event_type')
        resource_type = request.args.get('resource_type')
        actor_email = request.args.get('actor_email')
        device_id = request.args.get('device_id')
        limit = int(request.args.get('limit', 100))
        offset = int(request.args.get('offset', 0))
        
        # Parse date range
        start_date = None
        end_date = None
        
        if request.args.get('start_date'):
            try:
                start_date = datetime.fromisoformat(request.args.get('start_date'))
            except:
                pass
        
        if request.args.get('end_date'):
            try:
                end_date = datetime.fromisoformat(request.args.get('end_date'))
            except:
                pass
        
        # Get logs
        logs, total_count = audit_service.get_audit_logs(
            event_type=event_type,
            resource_type=resource_type,
            actor_email=actor_email,
            device_id=device_id,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            offset=offset
        )
        
        return jsonify({
            'success': True,
            'logs': [log.to_dict() for log in logs],
            'total_count': total_count,
            'limit': limit,
            'offset': offset
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@audit_log_bp.route('/logs/<int:log_id>', methods=['GET'])
@require_admin
def get_audit_log(log_id):
    """Get specific audit log entry"""
    try:
        from app.models.audit_log import AuditLog
        
        log = AuditLog.query.get(log_id)
        if not log:
            return jsonify({'error': 'Audit log not found'}), 404
        
        return jsonify({
            'success': True,
            'log': log.to_dict()
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@audit_log_bp.route('/user-activity/<user_email>', methods=['GET'])
@require_admin
def get_user_activity(user_email):
    """Get activity log for specific user"""
    try:
        audit_service = get_audit_logging_service()
        limit = int(request.args.get('limit', 50))
        
        logs = audit_service.get_user_activity(user_email, limit)
        
        return jsonify({
            'success': True,
            'user_email': user_email,
            'logs': [log.to_dict() for log in logs],
            'count': len(logs)
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@audit_log_bp.route('/resource-history/<resource_type>/<resource_id>', methods=['GET'])
@require_admin
def get_resource_history(resource_type, resource_id):
    """Get change history for specific resource"""
    try:
        audit_service = get_audit_logging_service()
        
        logs = audit_service.get_resource_history(resource_type, resource_id)
        
        return jsonify({
            'success': True,
            'resource_type': resource_type,
            'resource_id': resource_id,
            'logs': [log.to_dict() for log in logs],
            'count': len(logs)
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@audit_log_bp.route('/events', methods=['GET'])
@require_admin
def get_event_types():
    """Get list of available event types"""
    from app.models.audit_log import AuditEventType
    
    event_types = [e.value for e in AuditEventType]
    
    return jsonify({
        'success': True,
        'event_types': event_types,
        'count': len(event_types)
    }), 200


@audit_log_bp.route('/statistics', methods=['GET'])
@require_admin
def get_audit_statistics():
    """Get audit log statistics"""
    try:
        from app.models.audit_log import AuditLog
        from sqlalchemy import func
        
        # Get date range
        days = int(request.args.get('days', 7))
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Event type distribution
        event_distribution = AuditLog.query.filter(
            AuditLog.created_at >= start_date
        ).with_entities(
            AuditLog.event_type,
            func.count(AuditLog.id).label('count')
        ).group_by(AuditLog.event_type).all()
        
        # Resource type distribution
        resource_distribution = AuditLog.query.filter(
            AuditLog.created_at >= start_date
        ).with_entities(
            AuditLog.resource_type,
            func.count(AuditLog.id).label('count')
        ).group_by(AuditLog.resource_type).all()
        
        # Status distribution
        status_distribution = AuditLog.query.filter(
            AuditLog.created_at >= start_date
        ).with_entities(
            AuditLog.status,
            func.count(AuditLog.id).label('count')
        ).group_by(AuditLog.status).all()
        
        # Severity distribution
        severity_distribution = AuditLog.query.filter(
            AuditLog.created_at >= start_date
        ).with_entities(
            AuditLog.severity,
            func.count(AuditLog.id).label('count')
        ).group_by(AuditLog.severity).all()
        
        # Top actors
        top_actors = AuditLog.query.filter(
            AuditLog.created_at >= start_date
        ).with_entities(
            AuditLog.actor_email,
            func.count(AuditLog.id).label('count')
        ).group_by(AuditLog.actor_email).order_by(
            func.count(AuditLog.id).desc()
        ).limit(10).all()
        
        # Total events
        total_events = AuditLog.query.filter(
            AuditLog.created_at >= start_date
        ).count()
        
        return jsonify({
            'success': True,
            'period_days': days,
            'total_events': total_events,
            'event_distribution': [
                {'event_type': e[0], 'count': e[1]} for e in event_distribution
            ],
            'resource_distribution': [
                {'resource_type': r[0], 'count': r[1]} for r in resource_distribution
            ],
            'status_distribution': [
                {'status': s[0], 'count': s[1]} for s in status_distribution
            ],
            'severity_distribution': [
                {'severity': sv[0], 'count': sv[1]} for sv in severity_distribution
            ],
            'top_actors': [
                {'actor_email': a[0], 'count': a[1]} for a in top_actors
            ]
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@audit_log_bp.route('/security-events', methods=['GET'])
@require_admin
def get_security_events():
    """Get security-related events"""
    try:
        audit_service = get_audit_logging_service()
        
        limit = int(request.args.get('limit', 100))
        offset = int(request.args.get('offset', 0))
        
        # Get security events
        logs, total_count = audit_service.get_audit_logs(
            resource_type='security',
            limit=limit,
            offset=offset
        )
        
        return jsonify({
            'success': True,
            'logs': [log.to_dict() for log in logs],
            'total_count': total_count,
            'limit': limit,
            'offset': offset
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@audit_log_bp.route('/failed-operations', methods=['GET'])
@require_admin
def get_failed_operations():
    """Get failed operations"""
    try:
        from app.models.audit_log import AuditLog
        
        limit = int(request.args.get('limit', 100))
        offset = int(request.args.get('offset', 0))
        
        query = AuditLog.query.filter_by(status='failure')
        total_count = query.count()
        
        logs = query.order_by(AuditLog.created_at.desc()).limit(limit).offset(offset).all()
        
        return jsonify({
            'success': True,
            'logs': [log.to_dict() for log in logs],
            'total_count': total_count,
            'limit': limit,
            'offset': offset
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@audit_log_bp.route('/export', methods=['GET'])
@require_admin
def export_audit_logs():
    """Export audit logs as CSV"""
    try:
        import csv
        from io import StringIO
        from flask import make_response
        
        audit_service = get_audit_logging_service()
        
        # Get all logs for export
        logs, _ = audit_service.get_audit_logs(limit=10000)
        
        # Create CSV
        output = StringIO()
        writer = csv.DictWriter(output, fieldnames=[
            'id', 'event_type', 'severity', 'actor_email', 'resource_type',
            'resource_id', 'action', 'status', 'created_at'
        ])
        
        writer.writeheader()
        for log in logs:
            writer.writerow({
                'id': log.id,
                'event_type': log.event_type,
                'severity': log.severity,
                'actor_email': log.actor_email,
                'resource_type': log.resource_type,
                'resource_id': log.resource_id,
                'action': log.action,
                'status': log.status,
                'created_at': log.created_at.isoformat()
            })
        
        response = make_response(output.getvalue())
        response.headers['Content-Disposition'] = 'attachment; filename=audit_logs.csv'
        response.headers['Content-Type'] = 'text/csv'
        
        return response, 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@audit_log_bp.route('/health', methods=['GET'])
def audit_health():
    """Health check for audit logging"""
    try:
        from app.models.audit_log import AuditLog
        
        # Check if we can query the database
        count = AuditLog.query.count()
        
        return jsonify({
            'success': True,
            'status': 'healthy',
            'total_logs': count
        }), 200
    
    except Exception as e:
        return jsonify({
            'success': False,
            'status': 'unhealthy',
            'error': str(e)
        }), 500

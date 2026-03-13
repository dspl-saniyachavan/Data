"""
Report and Health Routes
API endpoints for generating reports, managing retention, and system health
"""

from flask import Blueprint, jsonify, request
from datetime import datetime, timedelta
from app.services.report_generation_service import get_report_generation_service
from app.services.log_retention_service import get_log_retention_service
from functools import wraps

report_bp = Blueprint('reports', __name__, url_prefix='/api/reports')


def require_admin(f):
    """Decorator to require admin role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from flask import g
        if not hasattr(g, 'user') or g.user.get('role') != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        return f(*args, **kwargs)
    return decorated_function


@report_bp.route('/audit', methods=['GET'])
@require_admin
def get_audit_report():
    """Generate audit report"""
    try:
        report_service = get_report_generation_service()
        
        # Get date range
        days = int(request.args.get('days', 7))
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get filters
        event_types = request.args.getlist('event_types')
        resource_types = request.args.getlist('resource_types')
        
        report = report_service.generate_audit_report(
            start_date=start_date,
            end_date=end_date,
            event_types=event_types if event_types else None,
            resource_types=resource_types if resource_types else None
        )
        
        return jsonify({
            'success': True,
            'report': report
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@report_bp.route('/config-changes', methods=['GET'])
@require_admin
def get_config_change_report():
    """Generate configuration change report"""
    try:
        report_service = get_report_generation_service()
        
        # Get date range
        days = int(request.args.get('days', 7))
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        report = report_service.generate_config_change_report(
            start_date=start_date,
            end_date=end_date
        )
        
        return jsonify({
            'success': True,
            'report': report
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@report_bp.route('/failures', methods=['GET'])
@require_admin
def get_failure_report():
    """Generate failure and error report"""
    try:
        report_service = get_report_generation_service()
        
        # Get date range
        days = int(request.args.get('days', 7))
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get details flag
        include_details = request.args.get('details', 'true').lower() == 'true'
        
        report = report_service.generate_failure_report(
            start_date=start_date,
            end_date=end_date,
            include_details=include_details
        )
        
        return jsonify({
            'success': True,
            'report': report
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@report_bp.route('/offline-events', methods=['GET'])
@require_admin
def get_offline_events_report():
    """Generate offline/disconnection events report"""
    try:
        report_service = get_report_generation_service()
        
        # Get date range
        days = int(request.args.get('days', 7))
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        report = report_service.generate_offline_events_report(
            start_date=start_date,
            end_date=end_date
        )
        
        return jsonify({
            'success': True,
            'report': report
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@report_bp.route('/system-health', methods=['GET'])
@require_admin
def get_system_health_report():
    """Generate system health report"""
    try:
        report_service = get_report_generation_service()
        report = report_service.generate_system_health_report()
        
        return jsonify({
            'success': True,
            'report': report
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@report_bp.route('/retention/statistics', methods=['GET'])
@require_admin
def get_retention_statistics():
    """Get log retention statistics"""
    try:
        retention_service = get_log_retention_service()
        stats = retention_service.get_retention_statistics()
        
        return jsonify({
            'success': True,
            'statistics': stats
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@report_bp.route('/retention/cleanup', methods=['POST'])
@require_admin
def cleanup_logs():
    """Execute log cleanup based on retention policies"""
    try:
        retention_service = get_log_retention_service()
        
        # Get dry run flag
        dry_run = request.json.get('dry_run', False) if request.json else False
        
        result = retention_service.cleanup_expired_logs(dry_run=dry_run)
        
        return jsonify({
            'success': result.get('success', False),
            'result': result
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@report_bp.route('/retention/cleanup-severity', methods=['POST'])
@require_admin
def cleanup_by_severity():
    """Clean up logs by severity level"""
    try:
        retention_service = get_log_retention_service()
        
        data = request.json or {}
        severity = data.get('severity')
        dry_run = data.get('dry_run', False)
        
        if not severity:
            return jsonify({'error': 'severity required'}), 400
        
        result = retention_service.cleanup_by_severity(severity, dry_run=dry_run)
        
        return jsonify({
            'success': result.get('success', False),
            'result': result
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@report_bp.route('/retention/cleanup-event', methods=['POST'])
@require_admin
def cleanup_by_event():
    """Clean up logs by event type"""
    try:
        retention_service = get_log_retention_service()
        
        data = request.json or {}
        event_type = data.get('event_type')
        dry_run = data.get('dry_run', False)
        
        if not event_type:
            return jsonify({'error': 'event_type required'}), 400
        
        result = retention_service.cleanup_by_event_type(event_type, dry_run=dry_run)
        
        return jsonify({
            'success': result.get('success', False),
            'result': result
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@report_bp.route('/retention/cleanup-old', methods=['POST'])
@require_admin
def cleanup_old():
    """Clean up all logs older than specified days"""
    try:
        retention_service = get_log_retention_service()
        
        data = request.json or {}
        days = data.get('days', 365)
        dry_run = data.get('dry_run', False)
        
        result = retention_service.cleanup_old_logs(days, dry_run=dry_run)
        
        return jsonify({
            'success': result.get('success', False),
            'result': result
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@report_bp.route('/retention/set-policy', methods=['POST'])
@require_admin
def set_retention_policy():
    """Set retention policy for severity or event type"""
    try:
        retention_service = get_log_retention_service()
        
        data = request.json or {}
        policy_type = data.get('type')  # 'severity' or 'event'
        name = data.get('name')
        days = data.get('days')
        
        if not policy_type or not name or days is None:
            return jsonify({'error': 'type, name, and days required'}), 400
        
        if policy_type == 'severity':
            retention_service.set_retention_policy(name, days)
        elif policy_type == 'event':
            retention_service.set_event_retention_policy(name, days)
        else:
            return jsonify({'error': 'Invalid policy type'}), 400
        
        return jsonify({
            'success': True,
            'message': f'Set {name} retention to {days} days'
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@report_bp.route('/retention/archive', methods=['POST'])
@require_admin
def archive_logs():
    """Archive logs older than specified days"""
    try:
        retention_service = get_log_retention_service()
        
        data = request.json or {}
        days = data.get('days', 90)
        
        result = retention_service.archive_logs(days)
        
        return jsonify({
            'success': result.get('success', False),
            'result': result
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@report_bp.route('/health', methods=['GET'])
def report_health():
    """Health check for reporting service"""
    try:
        report_service = get_report_generation_service()
        health = report_service.generate_system_health_report()
        
        return jsonify({
            'success': True,
            'status': 'healthy',
            'health': health
        }), 200
    
    except Exception as e:
        return jsonify({
            'success': False,
            'status': 'unhealthy',
            'error': str(e)
        }), 500

"""
Report Generation Service for creating audit, configuration, and failure reports
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from app.models import db
from app.models.audit_log import AuditLog, AuditEventType
from sqlalchemy import func


class ReportGenerationService:
    """Service for generating various system reports"""
    
    def generate_audit_report(
        self,
        start_date: datetime,
        end_date: datetime,
        event_types: List[str] = None,
        resource_types: List[str] = None
    ) -> Dict[str, Any]:
        """
        Generate comprehensive audit report
        
        Args:
            start_date: Report start date
            end_date: Report end date
            event_types: Filter by event types
            resource_types: Filter by resource types
        
        Returns:
            Report dictionary with statistics and details
        """
        try:
            query = AuditLog.query.filter(
                AuditLog.created_at >= start_date,
                AuditLog.created_at <= end_date
            )
            
            if event_types:
                query = query.filter(AuditLog.event_type.in_(event_types))
            if resource_types:
                query = query.filter(AuditLog.resource_type.in_(resource_types))
            
            logs = query.all()
            
            # Calculate statistics
            total_events = len(logs)
            success_count = sum(1 for log in logs if log.status == 'success')
            failure_count = sum(1 for log in logs if log.status == 'failure')
            
            # Event type distribution
            event_distribution = {}
            for log in logs:
                event_distribution[log.event_type] = event_distribution.get(log.event_type, 0) + 1
            
            # Severity distribution
            severity_distribution = {}
            for log in logs:
                severity_distribution[log.severity] = severity_distribution.get(log.severity, 0) + 1
            
            # Top actors
            actor_activity = {}
            for log in logs:
                if log.actor_email:
                    actor_activity[log.actor_email] = actor_activity.get(log.actor_email, 0) + 1
            
            top_actors = sorted(actor_activity.items(), key=lambda x: x[1], reverse=True)[:10]
            
            # Resource changes
            resource_changes = {}
            for log in logs:
                if log.resource_type and log.action in ['create', 'update', 'delete']:
                    key = f"{log.resource_type}:{log.action}"
                    resource_changes[key] = resource_changes.get(key, 0) + 1
            
            return {
                'report_type': 'audit',
                'period': {
                    'start': start_date.isoformat(),
                    'end': end_date.isoformat()
                },
                'summary': {
                    'total_events': total_events,
                    'successful_events': success_count,
                    'failed_events': failure_count,
                    'success_rate': (success_count / total_events * 100) if total_events > 0 else 0
                },
                'event_distribution': event_distribution,
                'severity_distribution': severity_distribution,
                'top_actors': [{'email': email, 'count': count} for email, count in top_actors],
                'resource_changes': resource_changes,
                'generated_at': datetime.utcnow().isoformat()
            }
        
        except Exception as e:
            print(f"[REPORT] Error generating audit report: {e}")
            return {'error': str(e)}
    
    def generate_config_change_report(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """
        Generate configuration change report
        
        Returns:
            Report with config changes, who made them, and impact
        """
        try:
            config_events = [
                AuditEventType.CONFIG_CREATED.value,
                AuditEventType.CONFIG_UPDATED.value,
                AuditEventType.CONFIG_DELETED.value,
                AuditEventType.CONFIG_SYNCED.value,
                AuditEventType.CONFIG_BULK_UPDATE.value
            ]
            
            logs = AuditLog.query.filter(
                AuditLog.created_at >= start_date,
                AuditLog.created_at <= end_date,
                AuditLog.event_type.in_(config_events)
            ).all()
            
            # Group by action
            changes_by_action = {}
            for log in logs:
                action = log.action
                if action not in changes_by_action:
                    changes_by_action[action] = []
                changes_by_action[action].append({
                    'config_id': log.resource_id,
                    'config_name': log.resource_name,
                    'actor': log.actor_email,
                    'timestamp': log.created_at.isoformat(),
                    'old_values': log.old_values,
                    'new_values': log.new_values,
                    'status': log.status
                })
            
            # Calculate impact
            total_changes = len(logs)
            successful_changes = sum(1 for log in logs if log.status == 'success')
            failed_changes = sum(1 for log in logs if log.status == 'failure')
            
            # Most changed configs
            config_change_count = {}
            for log in logs:
                if log.resource_id:
                    config_change_count[log.resource_id] = config_change_count.get(log.resource_id, 0) + 1
            
            most_changed = sorted(config_change_count.items(), key=lambda x: x[1], reverse=True)[:10]
            
            return {
                'report_type': 'config_changes',
                'period': {
                    'start': start_date.isoformat(),
                    'end': end_date.isoformat()
                },
                'summary': {
                    'total_changes': total_changes,
                    'successful_changes': successful_changes,
                    'failed_changes': failed_changes,
                    'success_rate': (successful_changes / total_changes * 100) if total_changes > 0 else 0
                },
                'changes_by_action': changes_by_action,
                'most_changed_configs': [
                    {'config_id': cid, 'change_count': count} for cid, count in most_changed
                ],
                'generated_at': datetime.utcnow().isoformat()
            }
        
        except Exception as e:
            print(f"[REPORT] Error generating config change report: {e}")
            return {'error': str(e)}
    
    def generate_failure_report(
        self,
        start_date: datetime,
        end_date: datetime,
        include_details: bool = True
    ) -> Dict[str, Any]:
        """
        Generate failure and error report
        
        Returns:
            Report with failures, errors, and root causes
        """
        try:
            failures = AuditLog.query.filter(
                AuditLog.created_at >= start_date,
                AuditLog.created_at <= end_date,
                AuditLog.status == 'failure'
            ).all()
            
            # Group by event type
            failures_by_type = {}
            for log in failures:
                event_type = log.event_type
                if event_type not in failures_by_type:
                    failures_by_type[event_type] = []
                
                failure_info = {
                    'timestamp': log.created_at.isoformat(),
                    'resource': f"{log.resource_type}:{log.resource_id}",
                    'actor': log.actor_email,
                    'error': log.error_message,
                    'severity': log.severity
                }
                
                if include_details:
                    failure_info['context'] = log.context
                
                failures_by_type[event_type].append(failure_info)
            
            # Calculate statistics
            total_failures = len(failures)
            
            # Failure rate by event type
            failure_rate_by_type = {}
            for event_type in failures_by_type:
                total_of_type = AuditLog.query.filter(
                    AuditLog.created_at >= start_date,
                    AuditLog.created_at <= end_date,
                    AuditLog.event_type == event_type
                ).count()
                
                if total_of_type > 0:
                    failure_rate_by_type[event_type] = {
                        'failures': len(failures_by_type[event_type]),
                        'total': total_of_type,
                        'rate': (len(failures_by_type[event_type]) / total_of_type * 100)
                    }
            
            # Most common errors
            error_counts = {}
            for log in failures:
                error = log.error_message or 'Unknown error'
                error_counts[error] = error_counts.get(error, 0) + 1
            
            most_common_errors = sorted(error_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            
            # Critical failures
            critical_failures = [log for log in failures if log.severity == 'critical']
            
            return {
                'report_type': 'failures',
                'period': {
                    'start': start_date.isoformat(),
                    'end': end_date.isoformat()
                },
                'summary': {
                    'total_failures': total_failures,
                    'critical_failures': len(critical_failures),
                    'failure_types': len(failures_by_type)
                },
                'failures_by_type': failures_by_type,
                'failure_rate_by_type': failure_rate_by_type,
                'most_common_errors': [
                    {'error': error, 'count': count} for error, count in most_common_errors
                ],
                'critical_failures': [
                    {
                        'timestamp': log.created_at.isoformat(),
                        'event_type': log.event_type,
                        'resource': f"{log.resource_type}:{log.resource_id}",
                        'error': log.error_message
                    } for log in critical_failures
                ],
                'generated_at': datetime.utcnow().isoformat()
            }
        
        except Exception as e:
            print(f"[REPORT] Error generating failure report: {e}")
            return {'error': str(e)}
    
    def generate_offline_events_report(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """
        Generate report of offline/disconnection events
        
        Returns:
            Report with offline periods and device status
        """
        try:
            offline_events = AuditLog.query.filter(
                AuditLog.created_at >= start_date,
                AuditLog.created_at <= end_date,
                AuditLog.event_type.in_([
                    AuditEventType.MQTT_DISCONNECTED.value,
                    AuditEventType.SYSTEM_SHUTDOWN.value
                ])
            ).all()
            
            online_events = AuditLog.query.filter(
                AuditLog.created_at >= start_date,
                AuditLog.created_at <= end_date,
                AuditLog.event_type.in_([
                    AuditEventType.MQTT_CONNECTED.value,
                    AuditEventType.SYSTEM_STARTUP.value
                ])
            ).all()
            
            # Group by device
            offline_by_device = {}
            for log in offline_events:
                device_id = log.device_id or 'unknown'
                if device_id not in offline_by_device:
                    offline_by_device[device_id] = []
                offline_by_device[device_id].append({
                    'timestamp': log.created_at.isoformat(),
                    'event_type': log.event_type,
                    'reason': log.error_message
                })
            
            # Calculate uptime
            total_seconds = (end_date - start_date).total_seconds()
            offline_seconds_by_device = {}
            
            for device_id, events in offline_by_device.items():
                offline_seconds = 0
                for i, event in enumerate(events):
                    if i + 1 < len(events):
                        next_event = events[i + 1]
                        event_time = datetime.fromisoformat(event['timestamp'])
                        next_time = datetime.fromisoformat(next_event['timestamp'])
                        offline_seconds += (next_time - event_time).total_seconds()
                
                offline_seconds_by_device[device_id] = {
                    'offline_seconds': offline_seconds,
                    'uptime_percentage': ((total_seconds - offline_seconds) / total_seconds * 100) if total_seconds > 0 else 0
                }
            
            return {
                'report_type': 'offline_events',
                'period': {
                    'start': start_date.isoformat(),
                    'end': end_date.isoformat()
                },
                'summary': {
                    'total_offline_events': len(offline_events),
                    'total_online_events': len(online_events),
                    'affected_devices': len(offline_by_device)
                },
                'offline_by_device': offline_by_device,
                'device_uptime': offline_seconds_by_device,
                'generated_at': datetime.utcnow().isoformat()
            }
        
        except Exception as e:
            print(f"[REPORT] Error generating offline events report: {e}")
            return {'error': str(e)}
    
    def generate_system_health_report(self) -> Dict[str, Any]:
        """
        Generate current system health report
        
        Returns:
            Report with system status, recent issues, and metrics
        """
        try:
            now = datetime.utcnow()
            last_24h = now - timedelta(hours=24)
            
            # Recent events
            recent_events = AuditLog.query.filter(
                AuditLog.created_at >= last_24h
            ).count()
            
            # Recent failures
            recent_failures = AuditLog.query.filter(
                AuditLog.created_at >= last_24h,
                AuditLog.status == 'failure'
            ).count()
            
            # Recent security events
            security_events = AuditLog.query.filter(
                AuditLog.created_at >= last_24h,
                AuditLog.resource_type == 'security'
            ).count()
            
            # Last successful sync
            last_sync = AuditLog.query.filter(
                AuditLog.event_type == AuditEventType.CONFIG_SYNCED.value,
                AuditLog.status == 'success'
            ).order_by(AuditLog.created_at.desc()).first()
            
            # Connected devices
            connected_devices = AuditLog.query.filter(
                AuditLog.event_type == AuditEventType.MQTT_CONNECTED.value,
                AuditLog.created_at >= last_24h
            ).with_entities(AuditLog.device_id).distinct().count()
            
            # Calculate health score (0-100)
            health_score = 100
            if recent_failures > 0:
                health_score -= min(recent_failures * 5, 30)
            if security_events > 0:
                health_score -= min(security_events * 10, 40)
            
            health_status = 'healthy' if health_score >= 80 else 'degraded' if health_score >= 50 else 'critical'
            
            return {
                'report_type': 'system_health',
                'timestamp': now.isoformat(),
                'health_score': health_score,
                'health_status': health_status,
                'metrics': {
                    'recent_events_24h': recent_events,
                    'recent_failures_24h': recent_failures,
                    'security_events_24h': security_events,
                    'connected_devices': connected_devices
                },
                'last_sync': last_sync.created_at.isoformat() if last_sync else None,
                'generated_at': now.isoformat()
            }
        
        except Exception as e:
            print(f"[REPORT] Error generating system health report: {e}")
            return {'error': str(e)}


def get_report_generation_service() -> ReportGenerationService:
    """Get or create report generation service instance"""
    return ReportGenerationService()

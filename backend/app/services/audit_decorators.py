"""
Audit Logging Decorators
Automatic audit logging for route handlers
"""

from functools import wraps
from flask import request, g
from app.services.audit_logging_service import get_audit_logging_service
import json


def audit_log(
    event_type: str,
    resource_type: str = None,
    action: str = None,
    extract_resource_id=None,
    extract_resource_name=None,
    extract_old_values=None,
    extract_new_values=None,
    severity: str = 'info'
):
    """
    Decorator for automatic audit logging
    
    Args:
        event_type: Type of event to log
        resource_type: Type of resource affected
        action: Action performed (create, read, update, delete)
        extract_resource_id: Function to extract resource ID from response
        extract_resource_name: Function to extract resource name from response
        extract_old_values: Function to extract old values from request
        extract_new_values: Function to extract new values from response
        severity: Severity level (info, warning, error, critical)
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            audit_service = get_audit_logging_service()
            
            # Get actor information
            actor_id = None
            actor_email = None
            if hasattr(g, 'user'):
                actor_id = g.user.get('id')
                actor_email = g.user.get('email')
            
            # Get IP address
            actor_ip = request.remote_addr
            
            # Extract request data
            request_data = None
            try:
                if request.method in ['POST', 'PUT', 'PATCH']:
                    request_data = request.get_json()
            except:
                pass
            
            # Extract old values if provided
            old_values = None
            if extract_old_values and request_data:
                try:
                    old_values = extract_old_values(request_data)
                except:
                    pass
            
            # Execute the route handler
            try:
                response = f(*args, **kwargs)
                status = 'success'
                error_message = None
                
                # Extract response data
                response_data = None
                if isinstance(response, tuple):
                    response_data = response[0]
                    status_code = response[1] if len(response) > 1 else 200
                else:
                    response_data = response
                    status_code = 200
                
                # Check for error status codes
                if status_code >= 400:
                    status = 'failure'
                    if isinstance(response_data, dict):
                        error_message = response_data.get('error', 'Operation failed')
                
                # Extract resource information
                resource_id = None
                resource_name = None
                new_values = None
                
                if isinstance(response_data, dict):
                    if extract_resource_id:
                        try:
                            resource_id = extract_resource_id(response_data)
                        except:
                            pass
                    
                    if extract_resource_name:
                        try:
                            resource_name = extract_resource_name(response_data)
                        except:
                            pass
                    
                    if extract_new_values:
                        try:
                            new_values = extract_new_values(response_data)
                        except:
                            pass
                
                # Log the event
                audit_service.log_event(
                    event_type=event_type,
                    action=action or request.method.lower(),
                    resource_type=resource_type,
                    resource_id=resource_id,
                    resource_name=resource_name,
                    actor_id=actor_id,
                    actor_email=actor_email,
                    actor_ip=actor_ip,
                    old_values=old_values,
                    new_values=new_values,
                    context={
                        'method': request.method,
                        'path': request.path,
                        'status_code': status_code
                    },
                    status=status,
                    error_message=error_message,
                    severity=severity
                )
                
                return response
            
            except Exception as e:
                # Log the error
                audit_service.log_event(
                    event_type=event_type,
                    action=action or request.method.lower(),
                    resource_type=resource_type,
                    actor_id=actor_id,
                    actor_email=actor_email,
                    actor_ip=actor_ip,
                    context={
                        'method': request.method,
                        'path': request.path,
                        'error_type': type(e).__name__
                    },
                    status='failure',
                    error_message=str(e),
                    severity='error'
                )
                
                raise
        
        return decorated_function
    return decorator


def audit_telemetry(f):
    """Decorator for telemetry operations"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        audit_service = get_audit_logging_service()
        
        try:
            response = f(*args, **kwargs)
            
            # Extract telemetry info from response
            response_data = response[0] if isinstance(response, tuple) else response
            
            if isinstance(response_data, dict):
                device_id = response_data.get('device_id')
                parameter_count = response_data.get('parameter_count', 0)
                
                if device_id:
                    audit_service.log_telemetry_received(
                        device_id=device_id,
                        parameter_count=parameter_count
                    )
            
            return response
        
        except Exception as e:
            raise
    
    return decorated_function


def audit_command(f):
    """Decorator for command operations"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        audit_service = get_audit_logging_service()
        
        # Get actor information
        actor_email = None
        if hasattr(g, 'user'):
            actor_email = g.user.get('email')
        
        try:
            response = f(*args, **kwargs)
            
            # Extract command info from response
            response_data = response[0] if isinstance(response, tuple) else response
            
            if isinstance(response_data, dict):
                command_id = response_data.get('command_id')
                command_type = response_data.get('command_type')
                device_id = response_data.get('device_id')
                success = response_data.get('success', False)
                
                if command_id and success:
                    audit_service.log_command_sent(
                        command_id=command_id,
                        command_type=command_type or 'unknown',
                        device_id=device_id or 'broadcast',
                        actor_email=actor_email
                    )
            
            return response
        
        except Exception as e:
            raise
    
    return decorated_function


def audit_config(f):
    """Decorator for configuration operations"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        audit_service = get_audit_logging_service()
        
        # Get actor information
        actor_email = None
        if hasattr(g, 'user'):
            actor_email = g.user.get('email')
        
        try:
            response = f(*args, **kwargs)
            
            # Extract config info from response
            response_data = response[0] if isinstance(response, tuple) else response
            
            if isinstance(response_data, dict):
                config_id = response_data.get('id')
                config_name = response_data.get('name')
                
                if config_id:
                    audit_service.log_config_updated(
                        config_id=str(config_id),
                        config_name=config_name or 'unknown',
                        old_values={},
                        new_values=response_data,
                        actor_email=actor_email
                    )
            
            return response
        
        except Exception as e:
            raise
    
    return decorated_function


def audit_user(f):
    """Decorator for user management operations"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        audit_service = get_audit_logging_service()
        
        # Get actor information
        actor_email = None
        if hasattr(g, 'user'):
            actor_email = g.user.get('email')
        
        try:
            response = f(*args, **kwargs)
            
            # Extract user info from response
            response_data = response[0] if isinstance(response, tuple) else response
            
            if isinstance(response_data, dict):
                user_id = response_data.get('id')
                user_email = response_data.get('email')
                
                if user_id:
                    audit_service.log_user_updated(
                        user_id=user_id,
                        user_email=user_email or 'unknown',
                        old_values={},
                        new_values=response_data,
                        actor_email=actor_email
                    )
            
            return response
        
        except Exception as e:
            raise
    
    return decorated_function

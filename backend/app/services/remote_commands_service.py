"""
Remote Commands Service for sending commands to remote devices via MQTT
with delivery tracking and acknowledgment handling
"""
import json
import uuid
from datetime import datetime
from app.services.mqtt_publisher import get_mqtt_publisher
from app.services.message_signing_service import get_message_signing_service
from app.models import db
from app.models.command_execution import CommandExecution, CommandAcknowledgment

class RemoteCommandsService:
    """Service to send remote commands to devices with delivery tracking"""
    
    def __init__(self):
        self.mqtt_publisher = None
        self.signing_service = None
        self.command_history = {}
    
    def _get_publisher(self):
        """Lazy load MQTT publisher"""
        if self.mqtt_publisher is None:
            self.mqtt_publisher = get_mqtt_publisher()
        return self.mqtt_publisher
    
    def _get_signing_service(self):
        """Lazy load message signing service"""
        if self.signing_service is None:
            try:
                self.signing_service = get_message_signing_service()
            except ValueError:
                # Signing service not initialized yet
                return None
        return self.signing_service
    
    def _prepare_payload(self, payload: dict, command_type: str) -> dict:
        """Prepare payload with optional signing"""
        signing_service = self._get_signing_service()
        
        if signing_service and signing_service.should_sign_message(command_type):
            return signing_service.sign_message(payload, command_type)
        
        return payload
    
    def send_force_sync(self, device_id=None, sync_type='full', user_email=None):
        """Send force sync command to device(s) with delivery tracking"""
        command_id = str(uuid.uuid4())
        
        payload = {
            'command': 'force_sync',
            'command_id': command_id,
            'timestamp': datetime.utcnow().isoformat(),
            'sync_type': sync_type
        }
        
        # Sign sensitive command
        payload = self._prepare_payload(payload, 'force_sync')
        
        # Create command execution record
        try:
            cmd_exec = CommandExecution(
                command_id=command_id,
                command_type='force_sync',
                device_id=device_id,
                target_type='device' if device_id else 'broadcast',
                payload=payload,
                status='pending',
                created_by=user_email
            )
            db.session.add(cmd_exec)
            db.session.commit()
            print(f"[COMMANDS] Created execution record for {command_id}")
        except Exception as e:
            print(f"[COMMANDS] Error creating execution record: {e}")
            db.session.rollback()
        
        topic = f'precisionpulse/commands/{device_id}/sync' if device_id else 'precisionpulse/commands/broadcast/sync'
        
        success = self._get_publisher()._publish(topic, payload)
        
        # Update status to sent
        if success:
            try:
                cmd_exec = CommandExecution.query.filter_by(command_id=command_id).first()
                if cmd_exec:
                    cmd_exec.status = 'sent'
                    cmd_exec.delivery_status = 'sent'
                    cmd_exec.sent_at = datetime.utcnow()
                    db.session.commit()
                    print(f"[COMMANDS] Updated status to sent for {command_id}")
            except Exception as e:
                print(f"[COMMANDS] Error updating status: {e}")
                db.session.rollback()
        
        self.command_history[command_id] = {
            'command': 'force_sync',
            'device_id': device_id or 'all',
            'status': 'sent' if success else 'failed',
            'timestamp': datetime.utcnow().isoformat()
        }
        
        return {
            'success': success,
            'command_id': command_id,
            'message': f'Force sync command {"sent" if success else "failed"}',
            'device_id': device_id or 'all',
            'sync_type': sync_type
        }
    
    def send_config_update(self, device_id=None, config=None, user_email=None):
        """Send config update command to device(s) with delivery tracking"""
        if not config:
            return {'success': False, 'error': 'Config data required'}
        
        command_id = str(uuid.uuid4())
        
        payload = {
            'command': 'update_config',
            'command_id': command_id,
            'timestamp': datetime.utcnow().isoformat(),
            'config': config
        }
        
        # Sign sensitive command
        payload = self._prepare_payload(payload, 'update_config')
        
        # Create command execution record
        try:
            cmd_exec = CommandExecution(
                command_id=command_id,
                command_type='update_config',
                device_id=device_id,
                target_type='device' if device_id else 'broadcast',
                payload=payload,
                status='pending',
                created_by=user_email
            )
            db.session.add(cmd_exec)
            db.session.commit()
            print(f"[COMMANDS] Created execution record for {command_id}")
        except Exception as e:
            print(f"[COMMANDS] Error creating execution record: {e}")
            db.session.rollback()
        
        topic = f'precisionpulse/commands/{device_id}/config' if device_id else 'precisionpulse/commands/broadcast/config'
        
        success = self._get_publisher()._publish(topic, payload)
        
        # Update status to sent
        if success:
            try:
                cmd_exec = CommandExecution.query.filter_by(command_id=command_id).first()
                if cmd_exec:
                    cmd_exec.status = 'sent'
                    cmd_exec.delivery_status = 'sent'
                    cmd_exec.sent_at = datetime.utcnow()
                    db.session.commit()
                    print(f"[COMMANDS] Updated status to sent for {command_id}")
            except Exception as e:
                print(f"[COMMANDS] Error updating status: {e}")
                db.session.rollback()
        
        self.command_history[command_id] = {
            'command': 'update_config',
            'device_id': device_id or 'all',
            'status': 'sent' if success else 'failed',
            'timestamp': datetime.utcnow().isoformat(),
            'config': config
        }
        
        return {
            'success': success,
            'command_id': command_id,
            'message': f'Config update command {"sent" if success else "failed"}',
            'device_id': device_id or 'all'
        }
    
    def send_custom_command(self, command_type, device_id=None, params=None, user_email=None):
        """Send custom command to device(s)"""
        command_id = str(uuid.uuid4())
        
        payload = {
            'command': command_type,
            'command_id': command_id,
            'timestamp': datetime.utcnow().isoformat(),
            'params': params or {}
        }
        
        # Sign sensitive command
        payload = self._prepare_payload(payload, command_type)
        
        # Create command execution record
        try:
            cmd_exec = CommandExecution(
                command_id=command_id,
                command_type=command_type,
                device_id=device_id,
                target_type='device' if device_id else 'broadcast',
                payload=payload,
                status='pending',
                created_by=user_email
            )
            db.session.add(cmd_exec)
            db.session.commit()
            print(f"[COMMANDS] Created execution record for {command_id}")
        except Exception as e:
            print(f"[COMMANDS] Error creating execution record: {e}")
            db.session.rollback()
        
        topic = f'precisionpulse/commands/{device_id}/{command_type}' if device_id else f'precisionpulse/commands/broadcast/{command_type}'
        
        success = self._get_publisher()._publish(topic, payload)
        
        # Update status to sent
        if success:
            try:
                cmd_exec = CommandExecution.query.filter_by(command_id=command_id).first()
                if cmd_exec:
                    cmd_exec.status = 'sent'
                    cmd_exec.delivery_status = 'sent'
                    cmd_exec.sent_at = datetime.utcnow()
                    db.session.commit()
                    print(f"[COMMANDS] Updated status to sent for {command_id}")
            except Exception as e:
                print(f"[COMMANDS] Error updating status: {e}")
                db.session.rollback()
        
        signing_service = self._get_signing_service()
        is_signed = signing_service and signing_service.should_sign_message(command_type)
        
        return {
            'success': success,
            'command_id': command_id,
            'message': f'Command {"sent" if success else "failed"}',
            'device_id': device_id or 'all',
            'command_type': command_type,
            'signed': is_signed
        }
    
    def get_command_status(self, command_id=None, device_id=None):
        """Get status of commands from database"""
        try:
            if command_id:
                cmd_exec = CommandExecution.query.filter_by(command_id=command_id).first()
                if cmd_exec:
                    acks = CommandAcknowledgment.query.filter_by(command_id=command_id).all()
                    result = cmd_exec.to_dict()
                    result['acknowledgments'] = [ack.to_dict() for ack in acks]
                    return result
                return {'error': 'Command not found'}
            
            if device_id:
                commands = CommandExecution.query.filter_by(device_id=device_id).all()
                return {
                    'commands': [cmd.to_dict() for cmd in commands],
                    'count': len(commands)
                }
            
            commands = CommandExecution.query.all()
            return {
                'commands': [cmd.to_dict() for cmd in commands],
                'count': len(commands)
            }
        except Exception as e:
            print(f"[COMMANDS] Error getting command status: {e}")
            return {'error': str(e)}
    
    def handle_command_acknowledgment(self, command_id, device_id, ack_type, status, message=None, result_data=None):
        """Handle acknowledgment from device"""
        try:
            ack = CommandAcknowledgment(
                command_id=command_id,
                device_id=device_id,
                ack_type=ack_type,
                status=status,
                message=message,
                result_data=result_data
            )
            db.session.add(ack)
            
            cmd_exec = CommandExecution.query.filter_by(command_id=command_id).first()
            if cmd_exec:
                if ack_type == 'received':
                    cmd_exec.delivery_status = 'delivered'
                    cmd_exec.delivered_at = datetime.utcnow()
                    cmd_exec.status = 'delivered'
                elif ack_type == 'executing':
                    cmd_exec.execution_status = 'executing'
                    cmd_exec.started_at = datetime.utcnow()
                    cmd_exec.status = 'executing'
                elif ack_type == 'completed':
                    cmd_exec.execution_status = 'completed'
                    cmd_exec.completed_at = datetime.utcnow()
                    cmd_exec.status = 'completed'
                    cmd_exec.result_data = result_data
                elif ack_type == 'failed':
                    cmd_exec.execution_status = 'failed'
                    cmd_exec.status = 'failed'
                    cmd_exec.error_message = message
                    cmd_exec.result_data = result_data
            
            db.session.commit()
            print(f"[COMMANDS] Recorded acknowledgment for {command_id}: {ack_type}")
            return {'success': True, 'message': 'Acknowledgment recorded'}
        except Exception as e:
            print(f"[COMMANDS] Error handling acknowledgment: {e}")
            db.session.rollback()
            return {'success': False, 'error': str(e)}

remote_commands_service = RemoteCommandsService()

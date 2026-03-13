from flask import request, jsonify
from app.models.parameter import Parameter
from app.models import db
from sqlalchemy.exc import IntegrityError
from marshmallow import Schema, fields, ValidationError
from app.services.sync_service import sync_service
import asyncio
import json
from datetime import datetime

class ParameterSchema(Schema):
    name = fields.Str(required=True, validate=lambda x: len(x.strip()) > 0)
    unit = fields.Str(required=True, validate=lambda x: len(x.strip()) > 0)
    description = fields.Str(allow_none=True, load_default="")
    enabled = fields.Bool(load_default=True)

class ParameterController:
    @staticmethod
    def get_all_parameters():
        try:
            parameters = Parameter.query.order_by(Parameter.created_at.desc()).all()
            return {'parameters': [param.to_dict() for param in parameters]}, 200
        except Exception as e:
            return {'error': f'Failed to fetch parameters: {str(e)}'}, 500
    
    @staticmethod
    def create_parameter(data):
        schema = ParameterSchema()
        try:
            validated_data = schema.load(data)
        except ValidationError as err:
            return {'error': 'Validation failed', 'details': err.messages}, 400
        
        try:
            # Check if parameter name already exists
            existing = Parameter.query.filter_by(name=validated_data['name'].strip()).first()
            if existing:
                return {'error': 'Parameter with this name already exists'}, 409
            
            parameter = Parameter(
                name=validated_data['name'].strip(),
                unit=validated_data['unit'].strip(),
                description=validated_data.get('description', '').strip(),
                enabled=validated_data.get('enabled', True)
            )
            
            db.session.add(parameter)
            db.session.commit()
            
            # Sync to SQLite
            sync_service.sync_parameter_to_sqlite({
                'name': parameter.name,
                'unit': parameter.unit,
                'description': parameter.description,
                'enabled': parameter.enabled
            })
            
            # Publish MQTT sync message
            ParameterController._publish_parameter_sync(parameter.to_dict(), 'create')
            
            return {'message': 'Parameter created successfully', 'parameter': parameter.to_dict()}, 201
            
        except IntegrityError:
            db.session.rollback()
            return {'error': 'Parameter with this name already exists'}, 409
        except Exception as e:
            db.session.rollback()
            return {'error': f'Failed to create parameter: {str(e)}'}, 500
    
    @staticmethod
    def get_parameter_by_id(param_id):
        try:
            parameter = Parameter.query.get(param_id)
            if not parameter:
                return {'error': 'Parameter not found'}, 404
            return {'parameter': parameter.to_dict()}, 200
        except Exception as e:
            return {'error': f'Failed to fetch parameter: {str(e)}'}, 500
    
    @staticmethod
    def update_parameter(param_id, data):
        schema = ParameterSchema(partial=True)
        try:
            validated_data = schema.load(data)
        except ValidationError as err:
            return {'error': 'Validation failed', 'details': err.messages}, 400
        
        try:
            parameter = Parameter.query.get(param_id)
            if not parameter:
                return {'error': 'Parameter not found'}, 404
            
            # Check name uniqueness if name is being updated
            if 'name' in validated_data:
                existing = Parameter.query.filter(
                    Parameter.name == validated_data['name'].strip(),
                    Parameter.id != param_id
                ).first()
                if existing:
                    return {'error': 'Parameter with this name already exists'}, 409
            
            # Update fields
            for key, value in validated_data.items():
                if key in ['name', 'unit', 'description']:
                    setattr(parameter, key, value.strip() if isinstance(value, str) else value)
                else:
                    setattr(parameter, key, value)
            
            db.session.commit()
            
            # Sync to SQLite
            sync_service.sync_parameter_to_sqlite({
                'name': parameter.name,
                'unit': parameter.unit,
                'description': parameter.description,
                'enabled': parameter.enabled
            })
            
            # Publish MQTT sync message
            ParameterController._publish_parameter_sync(parameter.to_dict(), 'update')
            
            return {'message': 'Parameter updated successfully', 'parameter': parameter.to_dict()}, 200
            
        except IntegrityError:
            db.session.rollback()
            return {'error': 'Parameter with this name already exists'}, 409
        except Exception as e:
            db.session.rollback()
            return {'error': f'Failed to update parameter: {str(e)}'}, 500
    
    @staticmethod
    def delete_parameter(param_id):
        try:
            parameter = Parameter.query.get(param_id)
            if not parameter:
                return {'error': 'Parameter not found'}, 404
            
            param_dict = parameter.to_dict()  # Store before deletion
            
            db.session.delete(parameter)
            db.session.commit()
            
            # Sync deletion to SQLite
            try:
                import sqlite3
                with sqlite3.connect(sync_service.sqlite_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute('DELETE FROM parameters WHERE name = ?', (parameter.name,))
                    conn.commit()
            except Exception as e:
                print(f"Error syncing parameter deletion to SQLite: {e}")
            
            # Publish MQTT sync message
            print(f"📤 Publishing parameter delete sync: {param_dict['name']} (ID: {param_dict['id']})")
            ParameterController._publish_parameter_sync(param_dict, 'delete')
            
            return {'message': 'Parameter deleted successfully'}, 200
            
        except Exception as e:
            db.session.rollback()
            return {'error': f'Failed to delete parameter: {str(e)}'}, 500
    
    @staticmethod
    def _publish_parameter_sync(parameter_data, action):
        """Publish parameter sync message to MQTT"""
        try:
            from gmqtt import Client as MQTTClient
            import threading
            
            def publish():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                async def _publish():
                    client = MQTTClient("backend_param_sync")
                    await client.connect('localhost', 1883)
                    
                    payload = {
                        'action': action,
                        'parameter': parameter_data,
                        'source': 'backend',
                        'timestamp': datetime.utcnow().isoformat() + 'Z'
                    }
                    
                    await client.publish(
                        "precisionpulse/sync/parameters",
                        json.dumps(payload),
                        qos=1
                    )
                    print(f"📤 MQTT sync published: {action} - {parameter_data.get('name', parameter_data.get('id'))}")
                    await client.disconnect()
                
                loop.run_until_complete(_publish())
                loop.close()
            
            thread = threading.Thread(target=publish, daemon=True)
            thread.start()
            
        except Exception as e:
            print(f"Error publishing parameter sync: {e}")

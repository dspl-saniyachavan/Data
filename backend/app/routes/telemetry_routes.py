from flask import Blueprint, request, jsonify, current_app
from datetime import datetime, timedelta
from app.models.parameter_stream import ParameterStream
from app.models import db
from sqlalchemy import desc, func
from sqlalchemy.sql import text
from app.services.data_freshness_monitor import DataFreshnessMonitor
import logging

logger = logging.getLogger(__name__)

telemetry_bp = Blueprint('telemetry', __name__, url_prefix='/api/telemetry')

@telemetry_bp.route('/stream', methods=['POST'])
def stream_telemetry():
    """Receive telemetry stream from MQTT (desktop client)"""
    try:
        logger.info("[TELEMETRY] /stream endpoint called")
        
        data = request.get_json()
        logger.info(f"[TELEMETRY] Received data: {data}")
        
        client_id = data.get('client_id')
        timestamp_str = data.get('timestamp')
        parameters = data.get('parameters', [])
        
        logger.info(f"[TELEMETRY] client_id={client_id}, parameters count={len(parameters)}")
        
        if not client_id or not parameters:
            logger.warning(f"[TELEMETRY] Missing client_id or parameters")
            return jsonify({'error': 'Missing client_id or parameters'}), 400
        
        # Parse timestamp
        try:
            timestamp = datetime.fromisoformat(timestamp_str) if timestamp_str else datetime.utcnow()
        except Exception as e:
            logger.warning(f"[TELEMETRY] Error parsing timestamp: {e}")
            timestamp = datetime.utcnow()
        
        logger.info(f"[TELEMETRY] Timestamp: {timestamp}")
        
        # Store each parameter with minimal fields
        stored_count = 0
        for p in parameters:
            try:
                param_id = p.get('parameter_id') or p.get('id')
                value = float(p.get('value', 0))
                
                logger.info(f"[TELEMETRY] Storing param_id={param_id}, value={value}")
                
                param_record = ParameterStream(
                    parameter_id=param_id,
                    value=value,
                    timestamp=timestamp,
                    synced=False
                )
                db.session.add(param_record)
                stored_count += 1
                
                logger.info(f"[TELEMETRY] Added to session: param_id={param_id}")
            except Exception as e:
                logger.error(f"[TELEMETRY] Error processing parameter: {e}", exc_info=True)
        
        logger.info(f"[TELEMETRY] About to commit {stored_count} records")
        
        try:
            db.session.commit()
            logger.info(f"[TELEMETRY] Successfully committed {stored_count} records")
        except Exception as e:
            logger.error(f"[TELEMETRY] Error committing to database: {e}", exc_info=True)
            db.session.rollback()
            return jsonify({'error': f'Database error: {str(e)}'}), 500
        
        # Record data freshness
        if hasattr(current_app, 'data_freshness_monitor'):
            try:
                current_app.data_freshness_monitor.record_data(client_id)
                logger.info(f"[TELEMETRY] Recorded data freshness for {client_id}")
            except Exception as e:
                logger.error(f"[TELEMETRY] Error recording data freshness: {e}")
        
        # Broadcast via Socket.IO
        if hasattr(current_app, 'socketio'):
            try:
                normalized_params = [
                    {
                        'id': p.get('parameter_id') or p.get('id'),
                        'name': p.get('name'),
                        'value': float(p.get('value', 0)),
                        'unit': p.get('unit', '')
                    }
                    for p in parameters
                ]
                current_app.socketio.emit(
                    'telemetry',
                    {
                        'client_id': client_id,
                        'timestamp': timestamp.isoformat(),
                        'data': {'parameters': normalized_params}
                    },
                    namespace='/'
                )
                logger.info(f"[TELEMETRY] Broadcasted to Socket.IO")
            except Exception as e:
                logger.error(f"[TELEMETRY] Error broadcasting: {e}")
        
        logger.info(f"[TELEMETRY] Successfully processed {len(parameters)} parameters from {client_id}")
        
        return jsonify({'message': 'Telemetry received', 'count': len(parameters)}), 200
    except Exception as e:
        logger.error(f"[TELEMETRY] Unexpected error: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@telemetry_bp.route('/latest', methods=['GET'])
def get_latest_telemetry():
    """Get latest telemetry data for all parameters"""
    try:
        logger.info("[TELEMETRY] /latest endpoint called")
        
        # Get latest record for each parameter
        latest_dict = {}
        all_records = db.session.query(ParameterStream).order_by(
            ParameterStream.parameter_id,
            ParameterStream.timestamp.desc()
        ).all()
        
        logger.info(f"[TELEMETRY] Found {len(all_records)} total records")
        
        for record in all_records:
            if record.parameter_id not in latest_dict:
                latest_dict[record.parameter_id] = record
        
        # Format response for frontend dashboard
        parameters = []
        for param_id in sorted(latest_dict.keys()):
            p = latest_dict[param_id]
            parameters.append({
                'id': p.parameter_id,
                'value': p.value,
                'timestamp': int(p.timestamp.timestamp() * 1000) if p.timestamp else None
            })
        
        logger.info(f"[TELEMETRY] Returning {len(parameters)} latest parameters")
        
        return jsonify({
            'data': {
                'parameters': parameters,
                'timestamp': datetime.utcnow().isoformat()
            },
            'count': len(parameters)
        }), 200
    except Exception as e:
        logger.error(f"[TELEMETRY] Error in /latest: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@telemetry_bp.route('/parameter/<int:param_id>/latest', methods=['GET'])
def get_parameter_latest(param_id):
    """Get latest value for specific parameter"""
    try:
        latest = db.session.query(ParameterStream).filter(
            ParameterStream.parameter_id == param_id
        ).order_by(desc(ParameterStream.timestamp)).first()
        
        if not latest:
            return jsonify({'error': 'Parameter not found'}), 404
        
        return jsonify({'telemetry': latest.to_dict()}), 200
    except Exception as e:
        logger.error(f"[TELEMETRY] Error in /parameter/<param_id>/latest: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@telemetry_bp.route('/parameter/<int:param_id>/history', methods=['GET'])
def get_parameter_history(param_id):
    """Get historical telemetry data for parameter"""
    try:
        minutes = request.args.get('minutes', 60, type=int)
        limit = request.args.get('limit', 1000, type=int)
        
        start_time = datetime.utcnow() - timedelta(minutes=minutes)
        
        history = db.session.query(ParameterStream).filter(
            (ParameterStream.parameter_id == param_id) &
            (ParameterStream.timestamp >= start_time)
        ).order_by(desc(ParameterStream.timestamp)).limit(limit).all()
        
        return jsonify({
            'parameter_id': param_id,
            'time_range_minutes': minutes,
            'data': [p.to_dict() for p in history],
            'count': len(history)
        }), 200
    except Exception as e:
        logger.error(f"[TELEMETRY] Error in /parameter/<param_id>/history: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@telemetry_bp.route('/debug', methods=['GET'])
def debug_telemetry():
    """Debug endpoint to see recent telemetry"""
    try:
        logger.info("[TELEMETRY] /debug endpoint called")
        
        # Check if table exists
        try:
            count = db.session.query(ParameterStream).count()
            logger.info(f"[TELEMETRY] Total records in parameter_stream: {count}")
        except Exception as e:
            logger.error(f"[TELEMETRY] Error counting records: {e}")
        
        recent = db.session.query(ParameterStream).order_by(
            desc(ParameterStream.timestamp)
        ).limit(50).all()
        
        logger.info(f"[TELEMETRY] Found {len(recent)} recent records")
        
        return jsonify({
            'recent_records': [p.to_dict() for p in recent],
            'count': len(recent)
        }), 200
    except Exception as e:
        logger.error(f"[TELEMETRY] Error in /debug: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@telemetry_bp.route('/check-table', methods=['GET'])
def check_table():
    """Check if parameter_stream table exists and has data"""
    try:
        logger.info("[TELEMETRY] /check-table endpoint called")
        
        # Try to query the table
        count = db.session.query(ParameterStream).count()
        
        # Get table info
        inspector = db.inspect(db.engine)
        tables = inspector.get_table_names()
        
        table_exists = 'parameter_stream' in tables
        
        if table_exists:
            columns = [col['name'] for col in inspector.get_columns('parameter_stream')]
        else:
            columns = []
        
        return jsonify({
            'table_exists': table_exists,
            'columns': columns,
            'record_count': count,
            'all_tables': tables
        }), 200
    except Exception as e:
        logger.error(f"[TELEMETRY] Error in /check-table: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@telemetry_bp.route('/test-insert', methods=['POST'])
def test_insert():
    """Test endpoint to insert a test record"""
    try:
        logger.info("[TELEMETRY] /test-insert endpoint called")
        
        # Create test record
        test_record = ParameterStream(
            parameter_id=999,
            value=42.5,
            timestamp=datetime.utcnow(),
            synced=False
        )
        
        logger.info("Adding test record to session")
        db.session.add(test_record)
        
        logger.info("Committing test record")
        db.session.commit()
        
        logger.info("Test record committed successfully")
        
        # Verify
        count = db.session.query(ParameterStream).count()
        
        return jsonify({
            'message': 'Test record inserted successfully',
            'total_records': count
        }), 200
    except Exception as e:
        logger.error(f"[TELEMETRY] Error in /test-insert: {e}", exc_info=True)
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

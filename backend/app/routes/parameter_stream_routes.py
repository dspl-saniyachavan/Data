from flask import Blueprint, request, jsonify, current_app
from datetime import datetime, timedelta
from app.models.parameter_stream import ParameterStream
from app.models import db
from sqlalchemy import and_, desc

parameter_stream_bp = Blueprint('parameter_stream', __name__, url_prefix='/api/parameter-stream')

@parameter_stream_bp.route('/push', methods=['POST'])
def push_parameter_stream():
    """Receive parameter stream data from MQTT (desktop app)"""
    try:
        data = request.get_json()
        client_id = data.get('client_id')
        timestamp_str = data.get('timestamp')
        parameters = data.get('parameters', [])
        
        if not client_id or not parameters:
            return jsonify({'error': 'Missing client_id or parameters'}), 400
        
        # Parse timestamp
        try:
            timestamp = datetime.fromisoformat(timestamp_str) if timestamp_str else datetime.utcnow()
        except:
            timestamp = datetime.utcnow()
        
        # Store each parameter with minimal fields
        for param in parameters:
            stream_record = ParameterStream(
                parameter_id=param.get('id') or param.get('parameter_id'),
                value=float(param.get('value', 0)),
                timestamp=timestamp,
                synced=False
            )
            db.session.add(stream_record)
        
        db.session.commit()
        
        # Broadcast via Socket.IO
        if hasattr(current_app, 'socketio'):
            current_app.socketio.emit(
                'parameter_stream_update',
                {
                    'client_id': client_id,
                    'timestamp': timestamp.isoformat(),
                    'data': {'parameters': parameters}
                },
                namespace='/'
            )
        
        print(f"[PARAM_STREAM] Received {len(parameters)} parameters from {client_id}")
        return jsonify({'message': 'Parameter stream received', 'count': len(parameters)}), 200
    except Exception as e:
        print(f"[PARAM_STREAM] Error: {e}")
        return jsonify({'error': str(e)}), 500

@parameter_stream_bp.route('/latest', methods=['GET'])
def get_latest_parameter_stream():
    """Get latest parameter stream data for all parameters"""
    try:
        # Get latest record for each parameter
        latest_dict = {}
        all_records = db.session.query(ParameterStream).order_by(
            ParameterStream.parameter_id,
            ParameterStream.timestamp.desc()
        ).all()
        
        for record in all_records:
            if record.parameter_id not in latest_dict:
                latest_dict[record.parameter_id] = record
        
        return jsonify({
            'parameters': [p.to_dict() for p in latest_dict.values()],
            'count': len(latest_dict)
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@parameter_stream_bp.route('/parameter/<int:param_id>/latest', methods=['GET'])
def get_parameter_latest(param_id):
    """Get latest value for specific parameter"""
    try:
        latest = db.session.query(ParameterStream).filter(
            ParameterStream.parameter_id == param_id
        ).order_by(desc(ParameterStream.timestamp)).first()
        
        if not latest:
            return jsonify({'error': 'Parameter not found'}), 404
        
        return jsonify(latest.to_dict()), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@parameter_stream_bp.route('/parameter/<int:param_id>/history', methods=['GET'])
def get_parameter_history(param_id):
    """Get historical parameter stream data with time range filtering"""
    try:
        minutes = request.args.get('minutes', 60, type=int)
        limit = request.args.get('limit', 1000, type=int)
        
        start_time = datetime.utcnow() - timedelta(minutes=minutes)
        
        history = db.session.query(ParameterStream).filter(
            and_(
                ParameterStream.parameter_id == param_id,
                ParameterStream.timestamp >= start_time
            )
        ).order_by(desc(ParameterStream.timestamp)).limit(limit).all()
        
        return jsonify({
            'parameter_id': param_id,
            'time_range_minutes': minutes,
            'data': [p.to_dict() for p in history],
            'count': len(history)
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@parameter_stream_bp.route('/filter', methods=['POST'])
def filter_parameter_stream():
    """Filter parameter stream data by constraints"""
    try:
        filters = request.get_json()
        
        query = db.session.query(ParameterStream)
        
        # Parameter filter
        if filters.get('parameter_id'):
            query = query.filter(ParameterStream.parameter_id == filters['parameter_id'])
        
        # Value range filter
        if filters.get('min_value') is not None:
            query = query.filter(ParameterStream.value >= filters['min_value'])
        if filters.get('max_value') is not None:
            query = query.filter(ParameterStream.value <= filters['max_value'])
        
        # Time range filter
        if filters.get('start_time'):
            try:
                start = datetime.fromisoformat(filters['start_time'])
                query = query.filter(ParameterStream.timestamp >= start)
            except:
                pass
        
        if filters.get('end_time'):
            try:
                end = datetime.fromisoformat(filters['end_time'])
                query = query.filter(ParameterStream.timestamp <= end)
            except:
                pass
        
        # Synced filter
        if filters.get('synced') is not None:
            query = query.filter(ParameterStream.synced == filters['synced'])
        
        # Limit results
        limit = filters.get('limit', 1000)
        results = query.order_by(desc(ParameterStream.timestamp)).limit(limit).all()
        
        return jsonify({
            'filters': filters,
            'data': [p.to_dict() for p in results],
            'count': len(results)
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@parameter_stream_bp.route('/statistics', methods=['GET'])
def get_statistics():
    """Get statistics for parameter stream data"""
    try:
        param_id = request.args.get('parameter_id', type=int)
        minutes = request.args.get('minutes', 60, type=int)
        
        start_time = datetime.utcnow() - timedelta(minutes=minutes)
        
        query = db.session.query(ParameterStream).filter(
            ParameterStream.timestamp >= start_time
        )
        
        if param_id:
            query = query.filter(ParameterStream.parameter_id == param_id)
        
        records = query.all()
        
        if not records:
            return jsonify({'error': 'No data found'}), 404
        
        values = [r.value for r in records]
        
        stats = {
            'count': len(records),
            'min': min(values),
            'max': max(values),
            'avg': sum(values) / len(values),
            'latest': records[0].to_dict() if records else None,
            'time_range_minutes': minutes
        }
        
        return jsonify(stats), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@parameter_stream_bp.route('/cleanup', methods=['POST'])
def cleanup_old_data():
    """Clean up old parameter stream data (admin only)"""
    try:
        days = request.json.get('days', 30) if request.json else 30
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        deleted = db.session.query(ParameterStream).filter(
            ParameterStream.timestamp < cutoff_date
        ).delete()
        
        db.session.commit()
        
        return jsonify({
            'message': f'Deleted {deleted} records older than {days} days',
            'deleted_count': deleted
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@parameter_stream_bp.route('/mark-synced', methods=['PUT'])
def mark_synced():
    """Mark parameter stream records as synced"""
    try:
        data = request.get_json()
        stream_ids = data.get('ids', [])
        
        if not stream_ids:
            return jsonify({'error': 'No IDs provided'}), 400
        
        updated = db.session.query(ParameterStream).filter(
            ParameterStream.id.in_(stream_ids)
        ).update({'synced': True})
        
        db.session.commit()
        
        return jsonify({
            'message': f'Marked {updated} records as synced',
            'updated_count': updated
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

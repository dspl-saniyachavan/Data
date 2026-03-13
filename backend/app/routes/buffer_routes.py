from flask import Blueprint, request, jsonify
from datetime import datetime
from app.models import db
from app.models.telemetry_buffer import TelemetryBuffer
import sqlite3
import os

buffer_bp = Blueprint('buffer', __name__, url_prefix='/api/buffer')

# Path to desktop SQLite database
DESKTOP_DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
    'dspl-precision-pulse-desktop', 'data', 'precision_pulse.db'
)

@buffer_bp.route('/telemetry', methods=['POST'])
def buffer_telemetry():
    """Buffer telemetry data when offline"""
    try:
        data = request.get_json()
        device_id = data.get('device_id', 'unknown')
        timestamp = data.get('timestamp')
        parameters = data.get('parameters', [])
        
        for param in parameters:
            buffer_record = TelemetryBuffer(
                device_id=device_id,
                parameter_id=param.get('id') or param.get('parameter_id'),
                parameter_name=param.get('name', 'Unknown'),
                value=param.get('value', 0),
                unit=param.get('unit', ''),
                timestamp=datetime.fromisoformat(timestamp.replace('Z', '+00:00')) if timestamp else datetime.utcnow(),
                synced=False
            )
            db.session.add(buffer_record)
        
        db.session.commit()
        print(f"[BUFFER] Buffered {len(parameters)} parameters from {device_id}")
        
        return jsonify({'message': 'Data buffered', 'count': len(parameters)}), 201
    except Exception as e:
        db.session.rollback()
        print(f"[BUFFER] Error: {e}")
        return jsonify({'error': str(e)}), 500

@buffer_bp.route('/telemetry/latest', methods=['GET'])
def get_buffered_telemetry():
    """Get buffered telemetry from desktop SQLite local_buffer table"""
    try:
        print(f"[BUFFER] Checking desktop database at: {DESKTOP_DB_PATH}")
        print(f"[BUFFER] Database exists: {os.path.exists(DESKTOP_DB_PATH)}")
        
        # Try to read from desktop SQLite database
        if os.path.exists(DESKTOP_DB_PATH):
            with sqlite3.connect(DESKTOP_DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id, parameter_id, parameter_name, value, unit, timestamp
                    FROM local_buffer
                    ORDER BY timestamp DESC
                ''')
                rows = cursor.fetchall()
                
                buffer_data = []
                for row in rows:
                    buffer_data.append({
                        'id': row[0],
                        'device_id': 'desktop',
                        'parameter_id': row[1],
                        'parameter_name': row[2],
                        'value': float(row[3]),
                        'unit': row[4] or '',
                        'timestamp': row[5],
                        'synced': False
                    })
                
                print(f"[BUFFER] Retrieved {len(buffer_data)} records from local_buffer")
                
                # Emit buffer update via Socket.IO
                from app import get_socketio
                socketio = get_socketio()
                if socketio:
                    socketio.emit('buffer_update', {'count': len(buffer_data)}, namespace='/')
                    print(f"[BUFFER] Emitted buffer_update event")
                
                return jsonify({'buffer': buffer_data, 'count': len(buffer_data)}), 200
        else:
            print(f"[BUFFER] Desktop database not found, using PostgreSQL fallback")
            # Fallback to PostgreSQL telemetry_buffer
            buffered_records = TelemetryBuffer.query.filter_by(synced=False).order_by(TelemetryBuffer.timestamp.desc()).all()
            
            buffer_data = []
            for record in buffered_records:
                buffer_data.append({
                    'id': record.id,
                    'device_id': record.device_id,
                    'parameter_id': record.parameter_id,
                    'parameter_name': record.parameter_name,
                    'value': float(record.value),
                    'unit': record.unit or '',
                    'timestamp': record.timestamp.isoformat() if record.timestamp else '',
                    'synced': record.synced
                })
            
            return jsonify({'buffer': buffer_data, 'count': len(buffer_data)}), 200
    except Exception as e:
        print(f"[BUFFER] Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@buffer_bp.route('/telemetry/flush', methods=['DELETE'])
def flush_synced():
    """Flush all buffered records from desktop SQLite local_buffer table"""
    try:
        count = 0
        
        # Try to flush from desktop SQLite database
        if os.path.exists(DESKTOP_DB_PATH):
            with sqlite3.connect(DESKTOP_DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM local_buffer')
                count = cursor.fetchone()[0]
                
                cursor.execute('DELETE FROM local_buffer')
                conn.commit()
                
                print(f"[BUFFER] Flushed {count} records from local_buffer")
        else:
            # Fallback to PostgreSQL
            synced_records = TelemetryBuffer.query.filter_by(synced=True).all()
            count = len(synced_records)
            
            for record in synced_records:
                db.session.delete(record)
            
            db.session.commit()
            print(f"[BUFFER] Flushed {count} synced records from PostgreSQL")
        
        # Emit buffer flushed event via Socket.IO
        from app import get_socketio
        socketio = get_socketio()
        if socketio:
            socketio.emit('buffer_flushed', {'count': count}, namespace='/')
        
        return jsonify({'message': 'Buffered records flushed', 'count': count}), 200
    except Exception as e:
        if 'db' in locals():
            db.session.rollback()
        print(f"[BUFFER] Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@buffer_bp.route('/telemetry/mark-synced', methods=['PUT'])
def mark_synced():
    """Mark buffered records as synced in database"""
    try:
        data = request.get_json()
        ids = data.get('ids', [])
        
        TelemetryBuffer.query.filter(TelemetryBuffer.id.in_(ids)).update(
            {TelemetryBuffer.synced: True},
            synchronize_session=False
        )
        db.session.commit()
        
        print(f"[BUFFER] Marked {len(ids)} records as synced")
        return jsonify({'message': 'Records marked as synced'}), 200
    except Exception as e:
        db.session.rollback()
        print(f"[BUFFER] Error: {e}")
        return jsonify({'error': str(e)}), 500

from app.models import db
from datetime import datetime


class ParameterStream(db.Model):
    """Model to store parameter streaming data from devices - matches desktop SQLite schema"""
    __tablename__ = 'parameter_stream'
    
    id = db.Column(db.Integer, primary_key=True)
    parameter_id = db.Column(db.Integer, nullable=False, index=True)
    value = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, index=True, default=datetime.utcnow)
    synced = db.Column(db.Boolean, default=False, index=True)
    
    __table_args__ = (
        db.Index('idx_parameter_stream_param_id', 'parameter_id'),
        db.Index('idx_parameter_stream_timestamp', 'timestamp'),
        db.Index('idx_parameter_stream_synced', 'synced'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'parameter_id': self.parameter_id,
            'value': self.value,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'synced': self.synced
        }

from app.models import db
from datetime import datetime

class SystemConfig(db.Model):
    """Model for system configuration settings"""
    __tablename__ = 'system_config'
    
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False, index=True)
    value = db.Column(db.Text, nullable=False)
    description = db.Column(db.String(255))
    category = db.Column(db.String(50), default='general')
    data_type = db.Column(db.String(20), default='string')  # string, integer, boolean, json
    is_sensitive = db.Column(db.Boolean, default=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = db.Column(db.String(100))
    
    def to_dict(self):
        return {
            'id': self.id,
            'key': self.key,
            'value': self.value if not self.is_sensitive else '***',
            'description': self.description,
            'category': self.category,
            'data_type': self.data_type,
            'is_sensitive': self.is_sensitive,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'updated_by': self.updated_by
        }
    
    def get_typed_value(self):
        """Return value with proper type conversion"""
        if self.data_type == 'integer':
            return int(self.value)
        elif self.data_type == 'boolean':
            return self.value.lower() in ('true', '1', 'yes')
        elif self.data_type == 'json':
            import json
            return json.loads(self.value)
        return self.value

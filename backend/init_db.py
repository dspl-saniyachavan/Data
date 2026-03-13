#!/usr/bin/env python
"""
Database initialization script to ensure all tables are created properly
"""

import sys
import os

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.models import db
from app.models.parameter_stream import ParameterStream
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_db():
    """Initialize database and create all tables"""
    app = create_app()
    
    with app.app_context():
        logger.info("Creating all database tables...")
        
        try:
            # Drop and recreate parameter_stream table
            logger.info("Dropping parameter_stream table if exists...")
            ParameterStream.__table__.drop(db.engine, checkfirst=True)
            logger.info("Dropped parameter_stream table")
        except Exception as e:
            logger.warning(f"Could not drop table: {e}")
        
        try:
            logger.info("Creating all tables...")
            db.create_all()
            logger.info("All tables created successfully")
        except Exception as e:
            logger.error(f"Error creating tables: {e}", exc_info=True)
            return False
        
        # Verify table exists
        try:
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            
            if 'parameter_stream' in tables:
                logger.info("✓ parameter_stream table exists")
                columns = [col['name'] for col in inspector.get_columns('parameter_stream')]
                logger.info(f"  Columns: {columns}")
            else:
                logger.error("✗ parameter_stream table NOT found")
                return False
            
            # Try to insert a test record
            logger.info("Testing insert...")
            test_record = ParameterStream(
                parameter_id=1,
                value=42.5,
                synced=False
            )
            db.session.add(test_record)
            db.session.commit()
            logger.info("✓ Test record inserted successfully")
            
            # Verify record was saved
            count = db.session.query(ParameterStream).count()
            logger.info(f"✓ Total records in parameter_stream: {count}")
            
            # Clean up test record
            db.session.query(ParameterStream).delete()
            db.session.commit()
            logger.info("✓ Test record cleaned up")
            
            return True
        except Exception as e:
            logger.error(f"Error verifying table: {e}", exc_info=True)
            return False

if __name__ == '__main__':
    success = init_db()
    sys.exit(0 if success else 1)

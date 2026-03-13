#!/usr/bin/env python
"""
Migration script to recreate parameter_stream table with exact SQLite schema
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.models import db
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_parameter_stream():
    """Migrate parameter_stream table to match SQLite schema"""
    app = create_app()
    
    with app.app_context():
        logger.info("=" * 70)
        logger.info("PARAMETER_STREAM TABLE MIGRATION")
        logger.info("=" * 70)
        
        try:
            # 1. Drop existing table if it exists
            logger.info("\n1. Dropping existing parameter_stream table...")
            try:
                db.session.execute(text('DROP TABLE IF EXISTS parameter_stream CASCADE'))
                db.session.commit()
                logger.info("✓ Table dropped successfully")
            except Exception as e:
                logger.warning(f"  Could not drop table: {e}")
                db.session.rollback()
            
            # 2. Create new table with exact SQLite schema
            logger.info("\n2. Creating parameter_stream table with SQLite schema...")
            try:
                create_table_sql = '''
                CREATE TABLE parameter_stream (
                    id SERIAL PRIMARY KEY,
                    parameter_id INTEGER NOT NULL,
                    value FLOAT NOT NULL,
                    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    synced BOOLEAN DEFAULT FALSE
                )
                '''
                db.session.execute(text(create_table_sql))
                db.session.commit()
                logger.info("✓ Table created successfully")
            except Exception as e:
                logger.error(f"✗ Error creating table: {e}")
                db.session.rollback()
                return False
            
            # 3. Create indexes
            logger.info("\n3. Creating indexes...")
            try:
                indexes = [
                    ('idx_parameter_stream_param_id', 'parameter_id'),
                    ('idx_parameter_stream_timestamp', 'timestamp'),
                    ('idx_parameter_stream_synced', 'synced'),
                ]
                
                for idx_name, column in indexes:
                    try:
                        create_idx_sql = f'CREATE INDEX {idx_name} ON parameter_stream({column})'
                        db.session.execute(text(create_idx_sql))
                        logger.info(f"  ✓ Created index: {idx_name}")
                    except Exception as e:
                        logger.warning(f"  Could not create index {idx_name}: {e}")
                
                db.session.commit()
            except Exception as e:
                logger.error(f"✗ Error creating indexes: {e}")
                db.session.rollback()
                return False
            
            # 4. Verify table structure
            logger.info("\n4. Verifying table structure...")
            try:
                inspector = db.inspect(db.engine)
                columns = inspector.get_columns('parameter_stream')
                
                logger.info("  Table columns:")
                for col in columns:
                    logger.info(f"    - {col['name']}: {col['type']} (nullable={col['nullable']})")
                
                # Verify required columns exist
                required_columns = {'id', 'parameter_id', 'value', 'timestamp', 'synced'}
                actual_columns = {col['name'] for col in columns}
                
                if required_columns == actual_columns:
                    logger.info("✓ All required columns present")
                else:
                    missing = required_columns - actual_columns
                    extra = actual_columns - required_columns
                    if missing:
                        logger.error(f"✗ Missing columns: {missing}")
                    if extra:
                        logger.warning(f"  Extra columns: {extra}")
                    return False
            except Exception as e:
                logger.error(f"✗ Error verifying table: {e}")
                return False
            
            # 5. Test insert
            logger.info("\n5. Testing insert operation...")
            try:
                from app.models.parameter_stream import ParameterStream
                from datetime import datetime
                
                test_record = ParameterStream(
                    parameter_id=1,
                    value=25.5,
                    timestamp=datetime.utcnow(),
                    synced=False
                )
                db.session.add(test_record)
                db.session.commit()
                logger.info("✓ Test record inserted successfully")
                
                # Verify
                count = db.session.query(ParameterStream).count()
                logger.info(f"✓ Total records in table: {count}")
                
                # Clean up test record
                db.session.query(ParameterStream).delete()
                db.session.commit()
                logger.info("✓ Test record cleaned up")
            except Exception as e:
                logger.error(f"✗ Error testing insert: {e}")
                db.session.rollback()
                return False
            
            logger.info("\n" + "=" * 70)
            logger.info("MIGRATION COMPLETED SUCCESSFULLY ✓")
            logger.info("=" * 70)
            logger.info("\nTable schema matches SQLite:")
            logger.info("  - id: INTEGER PRIMARY KEY")
            logger.info("  - parameter_id: INTEGER NOT NULL")
            logger.info("  - value: FLOAT NOT NULL")
            logger.info("  - timestamp: TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
            logger.info("  - synced: BOOLEAN DEFAULT FALSE")
            logger.info("\nIndexes created:")
            logger.info("  - idx_parameter_stream_param_id")
            logger.info("  - idx_parameter_stream_timestamp")
            logger.info("  - idx_parameter_stream_synced")
            
            return True
        except Exception as e:
            logger.error(f"✗ Unexpected error: {e}", exc_info=True)
            return False

if __name__ == '__main__':
    success = migrate_parameter_stream()
    sys.exit(0 if success else 1)

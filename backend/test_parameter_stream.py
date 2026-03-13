#!/usr/bin/env python
"""
Test script to verify parameter_stream table and test data insertion
"""

import sys
import os
import json
from datetime import datetime

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.models import db
from app.models.parameter_stream import ParameterStream
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_parameter_stream():
    """Test parameter_stream table operations"""
    app = create_app()
    
    with app.app_context():
        logger.info("=" * 60)
        logger.info("PARAMETER_STREAM TABLE TEST")
        logger.info("=" * 60)
        
        # 1. Check table exists
        logger.info("\n1. Checking if table exists...")
        try:
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            
            if 'parameter_stream' in tables:
                logger.info("✓ parameter_stream table EXISTS")
                columns = [col['name'] for col in inspector.get_columns('parameter_stream')]
                logger.info(f"  Columns: {columns}")
                
                # Get column details
                for col in inspector.get_columns('parameter_stream'):
                    logger.info(f"    - {col['name']}: {col['type']}")
            else:
                logger.error("✗ parameter_stream table NOT FOUND")
                logger.info(f"  Available tables: {tables}")
                return False
        except Exception as e:
            logger.error(f"Error checking table: {e}", exc_info=True)
            return False
        
        # 2. Count existing records
        logger.info("\n2. Counting existing records...")
        try:
            count = db.session.query(ParameterStream).count()
            logger.info(f"✓ Total records: {count}")
        except Exception as e:
            logger.error(f"Error counting records: {e}", exc_info=True)
            return False
        
        # 3. Test insert
        logger.info("\n3. Testing insert operation...")
        try:
            test_record = ParameterStream(
                parameter_id=999,
                value=123.45,
                timestamp=datetime.utcnow(),
                synced=False
            )
            logger.info(f"  Created record: param_id=999, value=123.45")
            
            db.session.add(test_record)
            logger.info("  Added to session")
            
            db.session.commit()
            logger.info("✓ Record committed successfully")
            
            # Verify it was saved
            saved = db.session.query(ParameterStream).filter_by(parameter_id=999).first()
            if saved:
                logger.info(f"✓ Record verified in database: id={saved.id}, value={saved.value}")
            else:
                logger.error("✗ Record NOT found after commit")
                return False
        except Exception as e:
            logger.error(f"Error inserting record: {e}", exc_info=True)
            db.session.rollback()
            return False
        
        # 4. Test bulk insert (like telemetry stream)
        logger.info("\n4. Testing bulk insert (simulating telemetry stream)...")
        try:
            records = []
            for i in range(1, 6):
                record = ParameterStream(
                    parameter_id=i,
                    value=float(i * 10.5),
                    timestamp=datetime.utcnow(),
                    synced=False
                )
                records.append(record)
                db.session.add(record)
            
            logger.info(f"  Added {len(records)} records to session")
            db.session.commit()
            logger.info(f"✓ Bulk insert committed successfully")
            
            # Verify
            count = db.session.query(ParameterStream).count()
            logger.info(f"✓ Total records after bulk insert: {count}")
        except Exception as e:
            logger.error(f"Error in bulk insert: {e}", exc_info=True)
            db.session.rollback()
            return False
        
        # 5. Test query
        logger.info("\n5. Testing query operations...")
        try:
            all_records = db.session.query(ParameterStream).all()
            logger.info(f"✓ Retrieved {len(all_records)} records")
            
            for record in all_records[-5:]:
                logger.info(f"  - id={record.id}, param_id={record.parameter_id}, value={record.value}, synced={record.synced}")
        except Exception as e:
            logger.error(f"Error querying records: {e}", exc_info=True)
            return False
        
        # 6. Test JSON serialization
        logger.info("\n6. Testing JSON serialization...")
        try:
            record = db.session.query(ParameterStream).first()
            if record:
                record_dict = record.to_dict()
                logger.info(f"✓ Record serialized: {json.dumps(record_dict, indent=2)}")
            else:
                logger.warning("  No records to serialize")
        except Exception as e:
            logger.error(f"Error serializing record: {e}", exc_info=True)
            return False
        
        logger.info("\n" + "=" * 60)
        logger.info("ALL TESTS PASSED ✓")
        logger.info("=" * 60)
        return True

if __name__ == '__main__':
    success = test_parameter_stream()
    sys.exit(0 if success else 1)

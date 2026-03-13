#!/usr/bin/env python3
"""
Verification script to check if data duplication issue is fixed
Compares record counts between SQLite and PostgreSQL
"""

import sys
import os
import sqlite3

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def get_sqlite_count():
    """Get record count from SQLite"""
    db_path = '/home/saniyachavani/Documents/Precision_Pulse/dspl-precision-pulse-desktop/data/precision_pulse.db'
    
    if not os.path.exists(db_path):
        logger.error(f"SQLite database not found at {db_path}")
        return None
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM parameter_stream')
        count = cursor.fetchone()[0]
        conn.close()
        return count
    except Exception as e:
        logger.error(f"Error reading SQLite: {e}")
        return None

def get_postgresql_count():
    """Get record count from PostgreSQL"""
    try:
        from app import create_app
        from app.models.parameter_stream import ParameterStream
        from app.models import db
        
        app = create_app()
        with app.app_context():
            count = db.session.query(ParameterStream).count()
            return count
    except Exception as e:
        logger.error(f"Error reading PostgreSQL: {e}")
        return None

def main():
    """Main verification function"""
    logger.info("=" * 80)
    logger.info("DATA DUPLICATION VERIFICATION")
    logger.info("=" * 80)
    
    # Get counts
    logger.info("\nFetching record counts...")
    sqlite_count = get_sqlite_count()
    pg_count = get_postgresql_count()
    
    if sqlite_count is None or pg_count is None:
        logger.error("Could not fetch record counts")
        return False
    
    # Display results
    logger.info("\n" + "-" * 80)
    logger.info("RESULTS:")
    logger.info("-" * 80)
    logger.info(f"SQLite records:      {sqlite_count}")
    logger.info(f"PostgreSQL records:  {pg_count}")
    
    # Check for duplication
    logger.info("\n" + "-" * 80)
    logger.info("ANALYSIS:")
    logger.info("-" * 80)
    
    if sqlite_count == pg_count:
        logger.info(f"✓ PASS: Record counts match ({sqlite_count} records)")
        logger.info("✓ No data duplication detected")
        return True
    elif pg_count == sqlite_count * 2:
        logger.error(f"✗ FAIL: PostgreSQL has 2x records (duplication detected)")
        logger.error(f"  SQLite: {sqlite_count}, PostgreSQL: {pg_count}")
        logger.error("  This indicates data is being sent twice")
        return False
    else:
        logger.warning(f"⚠ WARNING: Record counts don't match")
        logger.warning(f"  SQLite: {sqlite_count}, PostgreSQL: {pg_count}")
        logger.warning(f"  Ratio: {pg_count / sqlite_count if sqlite_count > 0 else 'N/A'}")
        return False

if __name__ == '__main__':
    logger.info("\nThis script verifies that the data duplication issue is fixed.")
    logger.info("It compares record counts between SQLite and PostgreSQL.\n")
    
    success = main()
    
    logger.info("\n" + "=" * 80)
    if success:
        logger.info("VERIFICATION PASSED ✓")
        logger.info("Data duplication issue is FIXED")
    else:
        logger.info("VERIFICATION FAILED ✗")
        logger.info("Data duplication issue still exists")
    logger.info("=" * 80)
    
    sys.exit(0 if success else 1)

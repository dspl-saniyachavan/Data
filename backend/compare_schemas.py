#!/usr/bin/env python
"""
Schema comparison script to verify PostgreSQL and SQLite parameter_stream tables match
"""

import sys
import os
import sqlite3

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.models import db
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_sqlite_schema():
    """Get SQLite parameter_stream table schema"""
    sqlite_db_path = os.path.expanduser('~/.precision_pulse/precision_pulse.db')
    
    if not os.path.exists(sqlite_db_path):
        logger.warning(f"SQLite database not found at {sqlite_db_path}")
        return None
    
    try:
        conn = sqlite3.connect(sqlite_db_path)
        cursor = conn.cursor()
        
        # Get table info
        cursor.execute("PRAGMA table_info(parameter_stream)")
        columns = cursor.fetchall()
        
        conn.close()
        
        return columns
    except Exception as e:
        logger.error(f"Error reading SQLite schema: {e}")
        return None

def get_postgresql_schema():
    """Get PostgreSQL parameter_stream table schema"""
    app = create_app()
    
    with app.app_context():
        try:
            inspector = db.inspect(db.engine)
            columns = inspector.get_columns('parameter_stream')
            return columns
        except Exception as e:
            logger.error(f"Error reading PostgreSQL schema: {e}")
            return None

def compare_schemas():
    """Compare SQLite and PostgreSQL schemas"""
    logger.info("=" * 80)
    logger.info("PARAMETER_STREAM TABLE SCHEMA COMPARISON")
    logger.info("=" * 80)
    
    # Get SQLite schema
    logger.info("\n1. SQLite Schema (Desktop):")
    logger.info("-" * 80)
    sqlite_schema = get_sqlite_schema()
    
    if sqlite_schema:
        logger.info("  Columns:")
        for col in sqlite_schema:
            cid, name, type_, notnull, dflt_value, pk = col
            logger.info(f"    - {name}: {type_} (pk={pk}, notnull={notnull}, default={dflt_value})")
    else:
        logger.warning("  Could not read SQLite schema")
    
    # Get PostgreSQL schema
    logger.info("\n2. PostgreSQL Schema (Backend):")
    logger.info("-" * 80)
    pg_schema = get_postgresql_schema()
    
    if pg_schema:
        logger.info("  Columns:")
        for col in pg_schema:
            logger.info(f"    - {col['name']}: {col['type']} (nullable={col['nullable']})")
    else:
        logger.warning("  Could not read PostgreSQL schema")
    
    # Compare
    logger.info("\n3. Schema Comparison:")
    logger.info("-" * 80)
    
    if sqlite_schema and pg_schema:
        sqlite_cols = {col[1]: col for col in sqlite_schema}
        pg_cols = {col['name']: col for col in pg_schema}
        
        # Check required columns
        required_columns = ['id', 'parameter_id', 'value', 'timestamp', 'synced']
        
        all_match = True
        for col_name in required_columns:
            if col_name in sqlite_cols and col_name in pg_cols:
                logger.info(f"  ✓ {col_name}: Present in both")
            else:
                logger.error(f"  ✗ {col_name}: Missing in {'PostgreSQL' if col_name not in pg_cols else 'SQLite'}")
                all_match = False
        
        if all_match:
            logger.info("\n✓ SCHEMAS MATCH - Tables are compatible")
            return True
        else:
            logger.error("\n✗ SCHEMAS DO NOT MATCH - Tables are incompatible")
            return False
    else:
        logger.error("\n✗ Could not compare schemas")
        return False

def show_expected_schema():
    """Show the expected schema"""
    logger.info("\n4. Expected Schema (SQLite):")
    logger.info("-" * 80)
    logger.info("  CREATE TABLE parameter_stream (")
    logger.info("    id INTEGER PRIMARY KEY AUTOINCREMENT,")
    logger.info("    parameter_id INTEGER NOT NULL,")
    logger.info("    value REAL NOT NULL,")
    logger.info("    timestamp TIMESTAMP DEFAULT (datetime('now', 'localtime')),")
    logger.info("    synced BOOLEAN DEFAULT 0")
    logger.info("  )")
    logger.info("\n  Indexes:")
    logger.info("    - idx_parameter_stream_param_id ON parameter_stream(parameter_id)")
    logger.info("    - idx_parameter_stream_timestamp ON parameter_stream(timestamp)")

if __name__ == '__main__':
    show_expected_schema()
    success = compare_schemas()
    
    logger.info("\n" + "=" * 80)
    if success:
        logger.info("RESULT: Schemas are compatible ✓")
    else:
        logger.info("RESULT: Schemas need to be synchronized ✗")
        logger.info("\nTo fix, run:")
        logger.info("  python migrate_parameter_stream.py")
    logger.info("=" * 80)
    
    sys.exit(0 if success else 1)

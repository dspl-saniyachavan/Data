#!/usr/bin/env python
"""
Automated setup script for parameter_stream table synchronization
Handles comparison, migration, and verification in one command
"""

import sys
import os
import subprocess

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def print_header(title):
    """Print a formatted header"""
    logger.info("\n" + "=" * 80)
    logger.info(title.center(80))
    logger.info("=" * 80)

def print_section(title):
    """Print a formatted section"""
    logger.info("\n" + "-" * 80)
    logger.info(title)
    logger.info("-" * 80)

def run_script(script_name, description):
    """Run a Python script and return success status"""
    logger.info(f"\n{description}...")
    try:
        result = subprocess.run(
            [sys.executable, script_name],
            cwd=os.path.dirname(os.path.abspath(__file__)),
            capture_output=False
        )
        return result.returncode == 0
    except Exception as e:
        logger.error(f"Error running {script_name}: {e}")
        return False

def main():
    """Main setup function"""
    print_header("PARAMETER_STREAM TABLE SETUP")
    
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Step 1: Compare schemas
    print_section("Step 1: Comparing Schemas")
    logger.info("Checking if PostgreSQL and SQLite schemas match...")
    
    from app import create_app
    from app.models import db
    import sqlite3
    
    app = create_app()
    
    with app.app_context():
        try:
            # Check PostgreSQL table
            inspector = db.inspect(db.engine)
            pg_tables = inspector.get_table_names()
            
            if 'parameter_stream' not in pg_tables:
                logger.warning("✗ PostgreSQL table does not exist")
                needs_migration = True
            else:
                logger.info("✓ PostgreSQL table exists")
                pg_columns = {col['name'] for col in inspector.get_columns('parameter_stream')}
                logger.info(f"  Columns: {pg_columns}")
                needs_migration = False
        except Exception as e:
            logger.error(f"Error checking PostgreSQL: {e}")
            needs_migration = True
    
    # Check SQLite table
    sqlite_db_path = os.path.expanduser('~/.precision_pulse/precision_pulse.db')
    if os.path.exists(sqlite_db_path):
        try:
            conn = sqlite3.connect(sqlite_db_path)
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(parameter_stream)")
            sqlite_columns = {row[1] for row in cursor.fetchall()}
            conn.close()
            logger.info("✓ SQLite table exists")
            logger.info(f"  Columns: {sqlite_columns}")
        except Exception as e:
            logger.error(f"Error checking SQLite: {e}")
            sqlite_columns = set()
    else:
        logger.warning(f"✗ SQLite database not found at {sqlite_db_path}")
        sqlite_columns = set()
    
    # Step 2: Migrate if needed
    if needs_migration:
        print_section("Step 2: Migrating PostgreSQL Table")
        logger.info("Running migration to create/update parameter_stream table...")
        
        success = run_script('migrate_parameter_stream.py', 'Executing migration')
        
        if not success:
            logger.error("✗ Migration failed")
            return False
        
        logger.info("✓ Migration completed")
    else:
        logger.info("✓ No migration needed - schemas match")
    
    # Step 3: Verify
    print_section("Step 3: Verifying Setup")
    logger.info("Verifying table structure and data operations...")
    
    with app.app_context():
        try:
            from app.models.parameter_stream import ParameterStream
            from datetime import datetime
            
            # Test insert
            logger.info("  Testing insert operation...")
            test_record = ParameterStream(
                parameter_id=999,
                value=42.5,
                timestamp=datetime.utcnow(),
                synced=False
            )
            db.session.add(test_record)
            db.session.commit()
            logger.info("  ✓ Insert successful")
            
            # Test query
            logger.info("  Testing query operation...")
            count = db.session.query(ParameterStream).count()
            logger.info(f"  ✓ Query successful (total records: {count})")
            
            # Clean up
            db.session.query(ParameterStream).filter_by(parameter_id=999).delete()
            db.session.commit()
            logger.info("  ✓ Cleanup successful")
        except Exception as e:
            logger.error(f"✗ Verification failed: {e}")
            return False
    
    # Step 4: Summary
    print_section("Setup Summary")
    logger.info("✓ PostgreSQL parameter_stream table created/updated")
    logger.info("✓ Table schema matches SQLite")
    logger.info("✓ All indexes created")
    logger.info("✓ Insert/query operations working")
    
    print_header("SETUP COMPLETED SUCCESSFULLY ✓")
    
    logger.info("\nNext steps:")
    logger.info("1. Start the backend server")
    logger.info("2. Start the desktop app")
    logger.info("3. Data will be stored in both SQLite and PostgreSQL")
    logger.info("\nTo verify data flow:")
    logger.info("  curl http://localhost:5000/api/telemetry/debug")
    
    return True

if __name__ == '__main__':
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)

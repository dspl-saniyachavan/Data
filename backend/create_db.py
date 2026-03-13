import psycopg2
from psycopg2 import sql
import sys

try:
    # Connect to default postgres database
    conn = psycopg2.connect(
        host='localhost',
        user='postgres',
        password='postgres',
        database='postgres'
    )
    conn.autocommit = True
    cursor = conn.cursor()
    
    # Create database
    cursor.execute(sql.SQL("CREATE DATABASE precision_pulse"))
    print("✓ Database 'precision_pulse' created")
    
    cursor.close()
    conn.close()
    
    # Now initialize tables
    import os
    os.chdir('/home/saniyachavani/Documents/Precision_Pulse/backend')
    os.system('python3 init_db.py')
    
except psycopg2.errors.DuplicateDatabase:
    print("✓ Database 'precision_pulse' already exists")
    import os
    os.chdir('/home/saniyachavani/Documents/Precision_Pulse/backend')
    os.system('python3 init_db.py')
except Exception as e:
    print(f"✗ Error: {e}")
    print("Make sure PostgreSQL is running: sudo service postgresql start")
    sys.exit(1)

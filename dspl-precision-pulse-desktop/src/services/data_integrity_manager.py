"""
Data integrity module for buffering and replay
Guarantees: No data loss, no duplication, no reordering
"""

import sqlite3
import hashlib
from datetime import datetime
from typing import List, Dict, Optional
from threading import Lock


class DataIntegrityManager:
    """Manages data integrity for buffering and replay"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.lock = Lock()
        self._initialize_integrity_tables()
    
    def _initialize_integrity_tables(self):
        """Create tables for data integrity tracking"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Sequence table for ordering guarantee
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS buffer_sequence (
                    sequence_num INTEGER PRIMARY KEY AUTOINCREMENT,
                    parameter_id TEXT NOT NULL,
                    value REAL NOT NULL,
                    unit TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    data_hash TEXT UNIQUE NOT NULL,
                    synced BOOLEAN DEFAULT 0,
                    sync_timestamp TEXT,
                    created_at TIMESTAMP DEFAULT (datetime('now', 'localtime'))
                )
            ''')
            
            # Deduplication table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS buffer_dedup (
                    data_hash TEXT PRIMARY KEY,
                    sequence_num INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT (datetime('now', 'localtime')),
                    FOREIGN KEY(sequence_num) REFERENCES buffer_sequence(sequence_num)
                )
            ''')
            
            # Sync checkpoint table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sync_checkpoint (
                    id INTEGER PRIMARY KEY,
                    last_synced_sequence INTEGER,
                    last_sync_time TEXT,
                    total_synced INTEGER DEFAULT 0,
                    updated_at TIMESTAMP DEFAULT (datetime('now', 'localtime'))
                )
            ''')
            
            # Create index for faster queries
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_buffer_synced 
                ON buffer_sequence(synced, sequence_num)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_buffer_timestamp 
                ON buffer_sequence(timestamp)
            ''')
            
            conn.commit()
    
    def _calculate_hash(self, parameter_id: str, value: float, timestamp: str) -> str:
        """Calculate hash for deduplication"""
        data = f"{parameter_id}:{value}:{timestamp}"
        return hashlib.sha256(data.encode()).hexdigest()
    
    def buffer_data(self, parameter_id: str, value: float, unit: str, timestamp: str) -> bool:
        """Buffer data with deduplication and sequence guarantee"""
        with self.lock:
            data_hash = self._calculate_hash(parameter_id, value, timestamp)
            
            try:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    
                    # Check for duplicate
                    cursor.execute('SELECT sequence_num FROM buffer_dedup WHERE data_hash = ?', (data_hash,))
                    if cursor.fetchone():
                        print(f"[INTEGRITY] Duplicate detected: {parameter_id}={value}")
                        return False
                    
                    # Insert with auto-incrementing sequence
                    cursor.execute('''
                        INSERT INTO buffer_sequence 
                        (parameter_id, value, unit, timestamp, data_hash)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (parameter_id, value, unit, timestamp, data_hash))
                    
                    sequence_num = cursor.lastrowid
                    
                    # Record in dedup table
                    cursor.execute('''
                        INSERT INTO buffer_dedup (data_hash, sequence_num)
                        VALUES (?, ?)
                    ''', (data_hash, sequence_num))
                    
                    conn.commit()
                    print(f"[INTEGRITY] Buffered: seq={sequence_num}, {parameter_id}={value}")
                    return True
                    
            except sqlite3.IntegrityError as e:
                print(f"[INTEGRITY] Error buffering data: {e}")
                return False
    
    def get_unsynced_data(self, limit: Optional[int] = None) -> List[Dict]:
        """Get unsynced data in order, guaranteed no reordering"""
        with self.lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                query = '''
                    SELECT sequence_num, parameter_id, value, unit, timestamp, data_hash
                    FROM buffer_sequence
                    WHERE synced = 0
                    ORDER BY sequence_num ASC
                '''
                
                if limit:
                    query += f' LIMIT {limit}'
                
                cursor.execute(query)
                
                return [
                    {
                        'sequence_num': row[0],
                        'parameter_id': row[1],
                        'value': row[2],
                        'unit': row[3],
                        'timestamp': row[4],
                        'data_hash': row[5]
                    }
                    for row in cursor.fetchall()
                ]
    
    def mark_synced(self, sequence_nums: List[int]) -> bool:
        """Mark data as synced with checkpoint"""
        if not sequence_nums:
            return True
        
        with self.lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    
                    # Mark as synced
                    placeholders = ','.join('?' * len(sequence_nums))
                    cursor.execute(f'''
                        UPDATE buffer_sequence
                        SET synced = 1, sync_timestamp = ?
                        WHERE sequence_num IN ({placeholders})
                    ''', [datetime.now().isoformat()] + sequence_nums)
                    
                    # Update checkpoint
                    max_seq = max(sequence_nums)
                    cursor.execute('''
                        INSERT OR REPLACE INTO sync_checkpoint
                        (id, last_synced_sequence, last_sync_time, total_synced)
                        VALUES (1, ?, ?, (SELECT COUNT(*) FROM buffer_sequence WHERE synced = 1))
                    ''', (max_seq, datetime.now().isoformat()))
                    
                    conn.commit()
                    print(f"[INTEGRITY] Marked {len(sequence_nums)} records as synced")
                    return True
                    
            except Exception as e:
                print(f"[INTEGRITY] Error marking synced: {e}")
                return False
    
    def get_sync_checkpoint(self) -> Optional[Dict]:
        """Get last sync checkpoint"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT last_synced_sequence, last_sync_time, total_synced
                FROM sync_checkpoint WHERE id = 1
            ''')
            
            result = cursor.fetchone()
            if result:
                return {
                    'last_synced_sequence': result[0],
                    'last_sync_time': result[1],
                    'total_synced': result[2]
                }
            return None
    
    def get_buffer_stats(self) -> Dict:
        """Get buffer statistics"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM buffer_sequence WHERE synced = 0')
            unsynced = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM buffer_sequence WHERE synced = 1')
            synced = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM buffer_sequence')
            total = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM buffer_dedup')
            unique = cursor.fetchone()[0]
            
            return {
                'total_records': total,
                'synced_records': synced,
                'unsynced_records': unsynced,
                'unique_hashes': unique,
                'sync_rate': f"{(synced/total*100):.1f}%" if total > 0 else "0%"
            }
    
    def cleanup_synced_data(self, days: int = 1) -> int:
        """Delete old synced data, keeping integrity"""
        with self.lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    
                    # Get hashes to delete (synced records older than specified days)
                    if days == 0:
                        # Delete all synced records
                        cursor.execute('''
                            SELECT data_hash FROM buffer_sequence
                            WHERE synced = 1
                        ''')
                    else:
                        cursor.execute(f'''
                            SELECT data_hash FROM buffer_sequence
                            WHERE synced = 1 
                            AND datetime(sync_timestamp) < datetime('now', '-{days} days')
                        ''')
                    
                    hashes = [row[0] for row in cursor.fetchall()]
                    
                    if hashes:
                        # Delete from dedup table
                        placeholders = ','.join('?' * len(hashes))
                        cursor.execute(f'''
                            DELETE FROM buffer_dedup WHERE data_hash IN ({placeholders})
                        ''', hashes)
                        
                        # Delete from sequence table
                        cursor.execute(f'''
                            DELETE FROM buffer_sequence WHERE data_hash IN ({placeholders})
                        ''', hashes)
                        
                        conn.commit()
                        print(f"[INTEGRITY] Cleaned up {len(hashes)} old records")
                        return len(hashes)
                    
                    return 0
                    
            except Exception as e:
                print(f"[INTEGRITY] Error cleaning up: {e}")
                return 0
    
    def verify_integrity(self) -> bool:
        """Verify data integrity"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Check for orphaned dedup entries
            cursor.execute('''
                SELECT COUNT(*) FROM buffer_dedup
                WHERE sequence_num NOT IN (SELECT sequence_num FROM buffer_sequence)
            ''')
            orphaned = cursor.fetchone()[0]
            
            # Check for duplicate hashes
            cursor.execute('''
                SELECT COUNT(*) FROM buffer_sequence
                GROUP BY data_hash HAVING COUNT(*) > 1
            ''')
            duplicates = len(cursor.fetchall())
            
            # Check sequence continuity
            cursor.execute('''
                SELECT COUNT(*) FROM buffer_sequence
                WHERE sequence_num NOT IN (
                    SELECT ROW_NUMBER() OVER (ORDER BY sequence_num) 
                    FROM buffer_sequence
                )
            ''')
            gaps = cursor.fetchone()[0]
            
            is_valid = orphaned == 0 and duplicates == 0 and gaps == 0
            
            print(f"[INTEGRITY] Verification: orphaned={orphaned}, duplicates={duplicates}, gaps={gaps}, valid={is_valid}")
            return is_valid

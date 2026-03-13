"""
Unit tests for data integrity manager
Tests: No data loss, no duplication, no reordering
"""

import unittest
import tempfile
import os
from datetime import datetime
from src.services.data_integrity_manager import DataIntegrityManager


class TestDataIntegrity(unittest.TestCase):
    """Test data integrity guarantees"""
    
    def setUp(self):
        """Setup test database"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.db_path = self.temp_db.name
        self.temp_db.close()
        
        self.manager = DataIntegrityManager(self.db_path)
    
    def tearDown(self):
        """Cleanup test database"""
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
    
    def test_no_data_loss(self):
        """Test no data is lost during buffering"""
        # Buffer 100 records
        for i in range(100):
            timestamp = datetime.now().isoformat()
            result = self.manager.buffer_data(f'param_{i%5}', float(i), 'unit', timestamp)
            self.assertTrue(result)
        
        # Verify all records exist
        unsynced = self.manager.get_unsynced_data()
        self.assertEqual(len(unsynced), 100)
    
    def test_no_duplication(self):
        """Test duplicate data is rejected"""
        timestamp = datetime.now().isoformat()
        
        # Buffer same data twice
        result1 = self.manager.buffer_data('param_1', 25.5, '°C', timestamp)
        result2 = self.manager.buffer_data('param_1', 25.5, '°C', timestamp)
        
        self.assertTrue(result1)
        self.assertFalse(result2)  # Duplicate rejected
        
        # Verify only one record exists
        unsynced = self.manager.get_unsynced_data()
        self.assertEqual(len(unsynced), 1)
    
    def test_no_reordering(self):
        """Test data maintains insertion order"""
        timestamps = []
        for i in range(10):
            timestamp = datetime.now().isoformat()
            timestamps.append(timestamp)
            self.manager.buffer_data(f'param_{i}', float(i), 'unit', timestamp)
        
        # Retrieve data
        unsynced = self.manager.get_unsynced_data()
        
        # Verify sequence numbers are in order
        sequences = [record['sequence_num'] for record in unsynced]
        self.assertEqual(sequences, sorted(sequences))
        
        # Verify order matches insertion
        for i, record in enumerate(unsynced):
            self.assertEqual(record['parameter_id'], f'param_{i}')
    
    def test_sequence_guarantee(self):
        """Test sequence numbers are unique and continuous"""
        for i in range(20):
            timestamp = datetime.now().isoformat()
            self.manager.buffer_data(f'param_{i}', float(i), 'unit', timestamp)
        
        unsynced = self.manager.get_unsynced_data()
        sequences = [record['sequence_num'] for record in unsynced]
        
        # Check uniqueness
        self.assertEqual(len(sequences), len(set(sequences)))
        
        # Check continuity
        self.assertEqual(sequences, list(range(1, 21)))
    
    def test_sync_checkpoint(self):
        """Test sync checkpoint tracking"""
        # Buffer data
        for i in range(5):
            timestamp = datetime.now().isoformat()
            self.manager.buffer_data(f'param_{i}', float(i), 'unit', timestamp)
        
        # Get unsynced data
        unsynced = self.manager.get_unsynced_data()
        sequences = [r['sequence_num'] for r in unsynced]
        
        # Mark as synced
        self.manager.mark_synced(sequences)
        
        # Check checkpoint
        checkpoint = self.manager.get_sync_checkpoint()
        self.assertIsNotNone(checkpoint)
        self.assertEqual(checkpoint['last_synced_sequence'], 5)
        self.assertEqual(checkpoint['total_synced'], 5)
    
    def test_partial_sync(self):
        """Test partial sync doesn't lose data"""
        # Buffer 10 records
        for i in range(10):
            timestamp = datetime.now().isoformat()
            self.manager.buffer_data(f'param_{i}', float(i), 'unit', timestamp)
        
        # Get first 5
        unsynced = self.manager.get_unsynced_data(limit=5)
        self.assertEqual(len(unsynced), 5)
        
        # Mark first 5 as synced
        sequences = [r['sequence_num'] for r in unsynced]
        self.manager.mark_synced(sequences)
        
        # Verify remaining 5 are still unsynced
        remaining = self.manager.get_unsynced_data()
        self.assertEqual(len(remaining), 5)
        
        # Verify they're the correct ones
        remaining_sequences = [r['sequence_num'] for r in remaining]
        self.assertEqual(remaining_sequences, [6, 7, 8, 9, 10])
    
    def test_buffer_stats(self):
        """Test buffer statistics"""
        # Buffer 10 records
        for i in range(10):
            timestamp = datetime.now().isoformat()
            self.manager.buffer_data(f'param_{i}', float(i), 'unit', timestamp)
        
        stats = self.manager.get_buffer_stats()
        
        self.assertEqual(stats['total_records'], 10)
        self.assertEqual(stats['unsynced_records'], 10)
        self.assertEqual(stats['synced_records'], 0)
        self.assertEqual(stats['unique_hashes'], 10)
    
    def test_integrity_verification(self):
        """Test integrity verification"""
        # Buffer data
        for i in range(5):
            timestamp = datetime.now().isoformat()
            self.manager.buffer_data(f'param_{i}', float(i), 'unit', timestamp)
        
        # Verify integrity
        is_valid = self.manager.verify_integrity()
        self.assertTrue(is_valid)
    
    def test_cleanup_old_data(self):
        """Test cleanup of old synced data"""
        # Buffer and sync data
        for i in range(5):
            timestamp = datetime.now().isoformat()
            self.manager.buffer_data(f'param_{i}', float(i), 'unit', timestamp)
        
        unsynced = self.manager.get_unsynced_data()
        sequences = [r['sequence_num'] for r in unsynced]
        self.manager.mark_synced(sequences)
        
        # Verify synced
        stats = self.manager.get_buffer_stats()
        self.assertEqual(stats['synced_records'], 5)
        
        # Cleanup with 0 days (should delete all synced)
        deleted = self.manager.cleanup_synced_data(days=0)
        self.assertGreater(deleted, 0)
    
    def test_concurrent_buffering(self):
        """Test thread-safe buffering"""
        import threading
        
        results = []
        
        def buffer_data(param_id, value):
            timestamp = datetime.now().isoformat()
            result = self.manager.buffer_data(param_id, value, 'unit', timestamp)
            results.append(result)
        
        # Create threads
        threads = []
        for i in range(10):
            t = threading.Thread(target=buffer_data, args=(f'param_{i}', float(i)))
            threads.append(t)
            t.start()
        
        # Wait for all threads
        for t in threads:
            t.join()
        
        # Verify all succeeded
        self.assertEqual(len(results), 10)
        self.assertTrue(all(results))
        
        # Verify all records exist
        unsynced = self.manager.get_unsynced_data()
        self.assertEqual(len(unsynced), 10)


if __name__ == '__main__':
    unittest.main()

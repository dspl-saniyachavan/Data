"""
Conflict Resolution Service using timestamp-based strategy
Resolves conflicts by comparing updated_at timestamps to determine authoritative changes
"""

from datetime import datetime
from typing import Dict, Any, List, Tuple
import logging

logger = logging.getLogger(__name__)


class ConflictResolver:
    """Resolves data conflicts using updated_at timestamp"""
    
    @staticmethod
    def resolve_conflict(local_data: Dict[str, Any], remote_data: Dict[str, Any]) -> Tuple[Dict[str, Any], str]:
        """
        Resolve conflict between local and remote data using timestamps
        
        Args:
            local_data: Local version of the data (must have updated_at)
            remote_data: Remote version of the data (must have updated_at)
        
        Returns:
            Tuple of (resolved_data, resolution_strategy)
            resolution_strategy: 'local', 'remote', or 'merged'
        """
        if not local_data or not remote_data:
            return (remote_data or local_data, 'default')
        
        local_timestamp = ConflictResolver._get_timestamp(local_data)
        remote_timestamp = ConflictResolver._get_timestamp(remote_data)
        
        if not local_timestamp or not remote_timestamp:
            logger.warning("Missing timestamps in conflict data")
            return (remote_data, 'default')
        
        # Compare timestamps
        if remote_timestamp > local_timestamp:
            logger.info(f"Remote data is newer (remote: {remote_timestamp}, local: {local_timestamp})")
            return (remote_data, 'remote')
        elif local_timestamp > remote_timestamp:
            logger.info(f"Local data is newer (local: {local_timestamp}, remote: {remote_timestamp})")
            return (local_data, 'local')
        else:
            logger.info("Timestamps are equal, using remote data")
            return (remote_data, 'remote')
    
    @staticmethod
    def resolve_conflicts_batch(conflicts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Resolve multiple conflicts
        
        Args:
            conflicts: List of conflict dictionaries with 'local' and 'remote' keys
        
        Returns:
            List of resolved data with resolution metadata
        """
        resolved = []
        for conflict in conflicts:
            local = conflict.get('local')
            remote = conflict.get('remote')
            conflict_id = conflict.get('id')
            
            resolved_data, strategy = ConflictResolver.resolve_conflict(local, remote)
            
            resolved.append({
                'id': conflict_id,
                'data': resolved_data,
                'strategy': strategy,
                'local_timestamp': ConflictResolver._get_timestamp(local),
                'remote_timestamp': ConflictResolver._get_timestamp(remote),
                'resolved_at': datetime.utcnow().isoformat()
            })
        
        return resolved
    
    @staticmethod
    def _get_timestamp(data: Dict[str, Any]) -> datetime:
        """Extract and parse updated_at timestamp from data"""
        if not data:
            return None
        
        timestamp_str = data.get('updated_at')
        if not timestamp_str:
            return None
        
        try:
            if isinstance(timestamp_str, datetime):
                return timestamp_str
            
            # Try ISO format
            if 'T' in str(timestamp_str):
                return datetime.fromisoformat(str(timestamp_str).replace('Z', '+00:00'))
            
            # Try other common formats
            for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M:%S.%f']:
                try:
                    return datetime.strptime(str(timestamp_str), fmt)
                except ValueError:
                    continue
            
            logger.warning(f"Could not parse timestamp: {timestamp_str}")
            return None
        except Exception as e:
            logger.error(f"Error parsing timestamp {timestamp_str}: {e}")
            return None
    
    @staticmethod
    def merge_field_changes(local_data: Dict[str, Any], remote_data: Dict[str, Any], 
                           field_timestamps: Dict[str, Dict[str, str]]) -> Dict[str, Any]:
        """
        Merge changes field-by-field using per-field timestamps
        
        Args:
            local_data: Local version
            remote_data: Remote version
            field_timestamps: Dict mapping field names to {'local': timestamp, 'remote': timestamp}
        
        Returns:
            Merged data with most recent values for each field
        """
        merged = dict(local_data)
        
        for field, timestamps in field_timestamps.items():
            local_ts = ConflictResolver._parse_timestamp(timestamps.get('local'))
            remote_ts = ConflictResolver._parse_timestamp(timestamps.get('remote'))
            
            if not local_ts or not remote_ts:
                continue
            
            if remote_ts > local_ts and field in remote_data:
                merged[field] = remote_data[field]
                logger.info(f"Using remote value for field '{field}' (remote: {remote_ts}, local: {local_ts})")
            elif local_ts > remote_ts and field in local_data:
                merged[field] = local_data[field]
                logger.info(f"Using local value for field '{field}' (local: {local_ts}, remote: {remote_ts})")
        
        # Update merged timestamp
        merged['updated_at'] = datetime.utcnow().isoformat()
        merged['conflict_resolved'] = True
        
        return merged
    
    @staticmethod
    def _parse_timestamp(timestamp_str: str) -> datetime:
        """Parse timestamp string to datetime"""
        if not timestamp_str:
            return None
        
        try:
            if isinstance(timestamp_str, datetime):
                return timestamp_str
            
            if 'T' in str(timestamp_str):
                return datetime.fromisoformat(str(timestamp_str).replace('Z', '+00:00'))
            
            for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M:%S.%f']:
                try:
                    return datetime.strptime(str(timestamp_str), fmt)
                except ValueError:
                    continue
            
            return None
        except Exception as e:
            logger.error(f"Error parsing timestamp {timestamp_str}: {e}")
            return None
    
    @staticmethod
    def detect_conflicts(local_records: List[Dict[str, Any]], 
                        remote_records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Detect conflicts between local and remote records
        
        Args:
            local_records: List of local records
            remote_records: List of remote records
        
        Returns:
            List of detected conflicts with metadata
        """
        conflicts = []
        local_map = {r.get('id'): r for r in local_records}
        remote_map = {r.get('id'): r for r in remote_records}
        
        # Check for conflicts in records that exist in both
        for record_id in set(local_map.keys()) & set(remote_map.keys()):
            local = local_map[record_id]
            remote = remote_map[record_id]
            
            local_ts = ConflictResolver._get_timestamp(local)
            remote_ts = ConflictResolver._get_timestamp(remote)
            
            # Conflict if timestamps differ and data differs
            if local_ts != remote_ts and local != remote:
                conflicts.append({
                    'id': record_id,
                    'local': local,
                    'remote': remote,
                    'local_timestamp': local_ts,
                    'remote_timestamp': remote_ts,
                    'detected_at': datetime.utcnow().isoformat()
                })
        
        return conflicts
    
    @staticmethod
    def get_conflict_summary(conflicts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate summary of conflicts
        
        Args:
            conflicts: List of conflicts
        
        Returns:
            Summary statistics
        """
        total = len(conflicts)
        local_wins = sum(1 for c in conflicts if ConflictResolver._get_timestamp(c.get('local')) > 
                        ConflictResolver._get_timestamp(c.get('remote')))
        remote_wins = total - local_wins
        
        return {
            'total_conflicts': total,
            'local_wins': local_wins,
            'remote_wins': remote_wins,
            'local_win_percentage': (local_wins / total * 100) if total > 0 else 0,
            'remote_win_percentage': (remote_wins / total * 100) if total > 0 else 0
        }

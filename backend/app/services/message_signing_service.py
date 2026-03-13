"""
Message Signing Service for MQTT messages
Provides digital signatures and replay attack prevention
"""

import hmac
import hashlib
import json
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, Tuple, Optional

class MessageSigningService:
    """Service for signing and verifying MQTT messages"""
    
    # Sensitive message types that require signing
    SENSITIVE_COMMANDS = {
        'force_sync', 'update_config', 'restart', 'clear_buffer',
        'password_change', 'user_sync', 'role_change', 'permission_change'
    }
    
    # Replay attack prevention
    NONCE_CACHE_TTL = 3600  # 1 hour
    TIMESTAMP_TOLERANCE = 300  # 5 minutes
    
    def __init__(self, signing_key: str):
        """
        Initialize signing service
        
        Args:
            signing_key: Secret key for HMAC signing (should be stored securely)
        """
        self.signing_key = signing_key.encode() if isinstance(signing_key, str) else signing_key
        self.nonce_cache = {}  # In-memory cache for replay prevention
        self._cleanup_nonce_cache()
    
    def sign_message(self, payload: Dict, message_type: str = None) -> Dict:
        """
        Sign a message with HMAC-SHA256 and add anti-replay fields
        
        Args:
            payload: Message payload to sign
            message_type: Type of message (for logging)
        
        Returns:
            Signed payload with signature and anti-replay fields
        """
        # Add anti-replay fields
        timestamp = datetime.utcnow().isoformat() + 'Z'
        nonce = str(uuid.uuid4())
        
        # Create signature payload (exclude signature field itself)
        sig_payload = {
            'payload': payload,
            'timestamp': timestamp,
            'nonce': nonce
        }
        
        # Generate signature
        sig_string = json.dumps(sig_payload, sort_keys=True, separators=(',', ':'))
        signature = hmac.new(
            self.signing_key,
            sig_string.encode(),
            hashlib.sha256
        ).hexdigest()
        
        # Return signed message
        signed_message = {
            'payload': payload,
            'signature': signature,
            'timestamp': timestamp,
            'nonce': nonce,
            'version': '1.0'
        }
        
        print(f"[SIGNING] Message signed (type: {message_type}, nonce: {nonce[:8]}...)")
        return signed_message
    
    def verify_message(self, signed_message: Dict, message_type: str = None) -> Tuple[bool, Optional[str], Optional[Dict]]:
        """
        Verify message signature and check for replay attacks
        
        Args:
            signed_message: Signed message to verify
            message_type: Type of message (for logging)
        
        Returns:
            Tuple of (is_valid, error_message, payload)
        """
        try:
            # Extract fields
            payload = signed_message.get('payload')
            signature = signed_message.get('signature')
            timestamp = signed_message.get('timestamp')
            nonce = signed_message.get('nonce')
            version = signed_message.get('version', '1.0')
            
            # Validate required fields
            if not all([payload, signature, timestamp, nonce]):
                return False, "Missing required signature fields", None
            
            # Validate version
            if version != '1.0':
                return False, f"Unsupported signature version: {version}", None
            
            # Check timestamp (prevent old messages)
            if not self._validate_timestamp(timestamp):
                return False, "Message timestamp outside acceptable range", None
            
            # Check for replay attack
            if not self._check_nonce(nonce):
                return False, "Duplicate nonce detected - possible replay attack", None
            
            # Verify signature
            sig_payload = {
                'payload': payload,
                'timestamp': timestamp,
                'nonce': nonce
            }
            sig_string = json.dumps(sig_payload, sort_keys=True, separators=(',', ':'))
            expected_signature = hmac.new(
                self.signing_key,
                sig_string.encode(),
                hashlib.sha256
            ).hexdigest()
            
            if not hmac.compare_digest(signature, expected_signature):
                return False, "Signature verification failed", None
            
            print(f"[SIGNING] Message verified successfully (type: {message_type}, nonce: {nonce[:8]}...)")
            return True, None, payload
        
        except Exception as e:
            return False, f"Verification error: {str(e)}", None
    
    def _validate_timestamp(self, timestamp_str: str) -> bool:
        """
        Validate that timestamp is within acceptable range
        
        Args:
            timestamp_str: ISO format timestamp string
        
        Returns:
            True if timestamp is valid, False otherwise
        """
        try:
            # Parse timestamp
            if timestamp_str.endswith('Z'):
                timestamp_str = timestamp_str[:-1]
            
            msg_time = datetime.fromisoformat(timestamp_str)
            current_time = datetime.utcnow()
            
            # Check if message is too old or too far in future
            time_diff = abs((current_time - msg_time).total_seconds())
            
            if time_diff > self.TIMESTAMP_TOLERANCE:
                print(f"[SIGNING] Timestamp validation failed: {time_diff}s difference")
                return False
            
            return True
        except Exception as e:
            print(f"[SIGNING] Timestamp parsing error: {e}")
            return False
    
    def _check_nonce(self, nonce: str) -> bool:
        """
        Check if nonce has been seen before (replay attack prevention)
        
        Args:
            nonce: Nonce to check
        
        Returns:
            True if nonce is new, False if duplicate
        """
        current_time = time.time()
        
        # Clean up expired nonces
        self.nonce_cache = {
            n: t for n, t in self.nonce_cache.items()
            if current_time - t < self.NONCE_CACHE_TTL
        }
        
        # Check if nonce exists
        if nonce in self.nonce_cache:
            print(f"[SIGNING] Replay attack detected: duplicate nonce {nonce[:8]}...")
            return False
        
        # Add nonce to cache
        self.nonce_cache[nonce] = current_time
        return True
    
    def _cleanup_nonce_cache(self):
        """Periodically clean up expired nonces"""
        import threading
        
        def cleanup():
            while True:
                time.sleep(self.NONCE_CACHE_TTL)
                current_time = time.time()
                self.nonce_cache = {
                    n: t for n, t in self.nonce_cache.items()
                    if current_time - t < self.NONCE_CACHE_TTL
                }
                print(f"[SIGNING] Cleaned up nonce cache (remaining: {len(self.nonce_cache)})")
        
        cleanup_thread = threading.Thread(target=cleanup, daemon=True)
        cleanup_thread.start()
    
    def should_sign_message(self, command_type: str) -> bool:
        """
        Determine if a message should be signed based on command type
        
        Args:
            command_type: Type of command
        
        Returns:
            True if message should be signed
        """
        return command_type in self.SENSITIVE_COMMANDS
    
    def get_signing_stats(self) -> Dict:
        """Get statistics about signing operations"""
        return {
            'nonce_cache_size': len(self.nonce_cache),
            'nonce_cache_ttl': self.NONCE_CACHE_TTL,
            'timestamp_tolerance': self.TIMESTAMP_TOLERANCE,
            'sensitive_commands': list(self.SENSITIVE_COMMANDS)
        }


# Global instance
_signing_service = None


def get_message_signing_service(signing_key: str = None) -> MessageSigningService:
    """
    Get or create message signing service instance
    
    Args:
        signing_key: Secret key for signing (required on first call)
    
    Returns:
        MessageSigningService instance
    """
    global _signing_service
    
    if _signing_service is None:
        if not signing_key:
            raise ValueError("signing_key required for first initialization")
        _signing_service = MessageSigningService(signing_key)
    
    return _signing_service


def init_message_signing_service(signing_key: str) -> MessageSigningService:
    """
    Initialize message signing service with signing key
    
    Args:
        signing_key: Secret key for HMAC signing
    
    Returns:
        MessageSigningService instance
    """
    global _signing_service
    _signing_service = MessageSigningService(signing_key)
    return _signing_service

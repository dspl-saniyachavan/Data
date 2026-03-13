"""
Message Verification Service for Desktop Client
Verifies digital signatures and prevents replay attacks
"""

import hmac
import hashlib
import json
import time
from datetime import datetime
from typing import Dict, Tuple, Optional


class MessageVerificationService:
    """Service for verifying signed MQTT messages on desktop client"""
    
    # Replay attack prevention
    NONCE_CACHE_TTL = 3600  # 1 hour
    TIMESTAMP_TOLERANCE = 300  # 5 minutes
    
    def __init__(self, signing_key: str):
        """
        Initialize verification service
        
        Args:
            signing_key: Secret key for HMAC verification (must match backend)
        """
        self.signing_key = signing_key.encode() if isinstance(signing_key, str) else signing_key
        self.nonce_cache = {}
        self.verification_stats = {
            'total_verified': 0,
            'total_failed': 0,
            'replay_attacks_detected': 0
        }
    
    def verify_message(self, message: Dict) -> Tuple[bool, Optional[str], Optional[Dict]]:
        """
        Verify message signature and check for replay attacks
        
        Args:
            message: Message to verify (may be signed or unsigned)
        
        Returns:
            Tuple of (is_valid, error_message, payload)
        """
        try:
            # Check if message is signed
            if 'signature' not in message:
                # Unsigned message - accept but log
                print(f"[VERIFY] Unsigned message received")
                return True, None, message
            
            # Extract fields
            payload = message.get('payload')
            signature = message.get('signature')
            timestamp = message.get('timestamp')
            nonce = message.get('nonce')
            version = message.get('version', '1.0')
            
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
                self.verification_stats['replay_attacks_detected'] += 1
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
                self.verification_stats['total_failed'] += 1
                return False, "Signature verification failed", None
            
            self.verification_stats['total_verified'] += 1
            print(f"[VERIFY] Message verified successfully (nonce: {nonce[:8]}...)")
            return True, None, payload
        
        except Exception as e:
            self.verification_stats['total_failed'] += 1
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
                print(f"[VERIFY] Timestamp validation failed: {time_diff}s difference")
                return False
            
            return True
        except Exception as e:
            print(f"[VERIFY] Timestamp parsing error: {e}")
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
            print(f"[VERIFY] Replay attack detected: duplicate nonce {nonce[:8]}...")
            return False
        
        # Add nonce to cache
        self.nonce_cache[nonce] = current_time
        return True
    
    def get_verification_stats(self) -> Dict:
        """Get verification statistics"""
        return {
            'total_verified': self.verification_stats['total_verified'],
            'total_failed': self.verification_stats['total_failed'],
            'replay_attacks_detected': self.verification_stats['replay_attacks_detected'],
            'nonce_cache_size': len(self.nonce_cache)
        }


# Global instance
_verification_service = None


def get_message_verification_service(signing_key: str = None) -> MessageVerificationService:
    """
    Get or create message verification service instance
    
    Args:
        signing_key: Secret key for verification (required on first call)
    
    Returns:
        MessageVerificationService instance
    """
    global _verification_service
    
    if _verification_service is None:
        if not signing_key:
            raise ValueError("signing_key required for first initialization")
        _verification_service = MessageVerificationService(signing_key)
    
    return _verification_service


def init_message_verification_service(signing_key: str) -> MessageVerificationService:
    """
    Initialize message verification service with signing key
    
    Args:
        signing_key: Secret key for HMAC verification
    
    Returns:
        MessageVerificationService instance
    """
    global _verification_service
    _verification_service = MessageVerificationService(signing_key)
    return _verification_service

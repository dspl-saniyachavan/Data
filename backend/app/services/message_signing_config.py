"""
Message Signing Configuration
Initializes signing and verification services with secure keys
"""

import os
from typing import Optional


class MessageSigningConfig:
    """Configuration for message signing and verification"""
    
    # Get signing key from environment or use default (should be changed in production)
    SIGNING_KEY = os.getenv(
        'MQTT_SIGNING_KEY',
        'precision-pulse-default-signing-key-change-in-production'
    )
    
    # Sensitive message types that require signing
    SENSITIVE_COMMANDS = {
        'force_sync',
        'update_config',
        'restart',
        'clear_buffer',
        'password_change',
        'user_sync',
        'role_change',
        'permission_change'
    }
    
    # Replay attack prevention settings
    NONCE_CACHE_TTL = 3600  # 1 hour
    TIMESTAMP_TOLERANCE = 300  # 5 minutes
    
    @classmethod
    def get_signing_key(cls) -> str:
        """Get the signing key"""
        return cls.SIGNING_KEY
    
    @classmethod
    def is_sensitive_command(cls, command_type: str) -> bool:
        """Check if command type requires signing"""
        return command_type in cls.SENSITIVE_COMMANDS
    
    @classmethod
    def validate_config(cls) -> bool:
        """Validate signing configuration"""
        if not cls.SIGNING_KEY:
            print("[SIGNING_CONFIG] WARNING: No signing key configured")
            return False
        
        if cls.SIGNING_KEY == 'precision-pulse-default-signing-key-change-in-production':
            print("[SIGNING_CONFIG] WARNING: Using default signing key - change in production!")
            return False
        
        return True


def init_signing_services():
    """
    Initialize both signing and verification services
    Should be called during application startup
    """
    from app.services.message_signing_service import init_message_signing_service
    
    try:
        signing_key = MessageSigningConfig.get_signing_key()
        signing_service = init_message_signing_service(signing_key)
        print(f"[SIGNING_CONFIG] Backend signing service initialized")
        print(f"[SIGNING_CONFIG] Signing stats: {signing_service.get_signing_stats()}")
        return signing_service
    except Exception as e:
        print(f"[SIGNING_CONFIG] Error initializing signing service: {e}")
        return None


def init_verification_services():
    """
    Initialize verification service for desktop client
    Should be called during application startup
    """
    from src.services.message_verification_service import init_message_verification_service
    
    try:
        signing_key = MessageSigningConfig.get_signing_key()
        verification_service = init_message_verification_service(signing_key)
        print(f"[SIGNING_CONFIG] Desktop verification service initialized")
        print(f"[SIGNING_CONFIG] Verification stats: {verification_service.get_verification_stats()}")
        return verification_service
    except Exception as e:
        print(f"[SIGNING_CONFIG] Error initializing verification service: {e}")
        return None

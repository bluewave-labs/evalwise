import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from typing import str

class APIKeyEncryption:
    """Utility for encrypting/decrypting API keys"""
    
    def __init__(self, master_key: str = None):
        """Initialize with master key from environment or parameter"""
        if master_key is None:
            # Require encryption key - no default for security
            master_key = os.getenv("API_ENCRYPTION_KEY")
            if not master_key:
                raise ValueError("API_ENCRYPTION_KEY environment variable is required. Generate with: openssl rand -hex 32")
        
        self.master_key = master_key.encode()
        self.salt = b'stable_salt_for_consistency'  # In production, use per-key salts
        
        # Derive key from master key
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self.salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(self.master_key))
        self.fernet = Fernet(key)
    
    def encrypt_api_key(self, api_key: str) -> str:
        """Encrypt an API key and return base64 encoded result"""
        if not api_key:
            raise ValueError("API key cannot be empty")
        
        encrypted_key = self.fernet.encrypt(api_key.encode())
        return base64.urlsafe_b64encode(encrypted_key).decode()
    
    def decrypt_api_key(self, encrypted_key: str) -> str:
        """Decrypt an API key from base64 encoded encrypted string"""
        if not encrypted_key:
            raise ValueError("Encrypted key cannot be empty")
        
        try:
            encrypted_data = base64.urlsafe_b64decode(encrypted_key.encode())
            decrypted_key = self.fernet.decrypt(encrypted_data)
            return decrypted_key.decode()
        except Exception as e:
            raise ValueError(f"Failed to decrypt API key: {str(e)}")

# Global encryption instance
encryption = APIKeyEncryption()
"""
API Key Management Utility for Pyunto Intelligence.

This module provides utilities for securely managing API keys for Pyunto Intelligence.
"""

import os
import json
import time
import uuid
import base64
import hashlib
import datetime
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class APIKeyManager:
    """
    Manages API keys for Pyunto Intelligence securely.
    
    Features:
    - Secure storage of API keys
    - Key rotation
    - Key revocation
    - Access tracking
    - Expiry management
    """
    
    def __init__(self, storage_path=None, master_password=None):
        """
        Initialize the API Key Manager.
        
        Args:
            storage_path: Path to store the encrypted API keys
            master_password: Master password for encryption/decryption
        """
        self.storage_path = storage_path or os.path.join(os.path.expanduser("~"), ".pyunto", "apikeys.enc")
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        
        # Initialize encryption
        self.master_password = master_password or os.environ.get("PYUNTO_MASTER_PASSWORD")
        if not self.master_password:
            raise ValueError("Master password required. Set it in constructor or PYUNTO_MASTER_PASSWORD env var.")
        
        # Initialize Fernet cipher
        self.cipher = self._create_cipher(self.master_password)
        
        # Load existing keys or create empty storage
        self.keys = self._load_keys()
    
    def _create_cipher(self, password):
        """Create a Fernet cipher from the master password."""
        # Generate a key from the password
        password_bytes = password.encode()
        salt = b'pyunto_salt_value'  # In production, use a secure random salt and store it
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password_bytes))
        return Fernet(key)
    
    def _load_keys(self):
        """Load and decrypt the API keys from storage."""
        if not os.path.exists(self.storage_path):
            return {}
        
        try:
            with open(self.storage_path, 'rb') as f:
                encrypted_data = f.read()
            
            decrypted_data = self.cipher.decrypt(encrypted_data)
            return json.loads(decrypted_data)
        except Exception as e:
            print(f"Error loading API keys: {e}")
            return {}
    
    def _save_keys(self):
        """Encrypt and save the API keys to storage."""
        try:
            json_data = json.dumps(self.keys)
            encrypted_data = self.cipher.encrypt(json_data.encode())
            
            with open(self.storage_path, 'wb') as f:
                f.write(encrypted_data)
                
            # Set secure permissions
            os.chmod(self.storage_path, 0o600)
            
            return True
        except Exception as e:
            print(f"Error saving API keys: {e}")
            return False
    
    def add_key(self, name, api_key, expires_at=None, metadata=None):
        """
        Add a new API key.
        
        Args:
            name: Friendly name for the key
            api_key: The actual API key
            expires_at: Expiry timestamp (optional)
            metadata: Additional metadata (dict)
            
        Returns:
            key_id: The ID of the newly added key
        """
        key_id = str(uuid.uuid4())
        
        # Set expiry to 1 year by default if not specified
        if expires_at is None:
            expires_at = int(time.time()) + (365 * 24 * 60 * 60)
        
        # Store key info
        self.keys[key_id] = {
            'name': name,
            'api_key': api_key,
            'created_at': int(time.time()),
            'expires_at': expires_at,
            'last_used': None,
            'metadata': metadata or {},
            'active': True
        }
        
        self._save_keys()
        return key_id
    
    def get_key(self, key_id):
        """
        Get an API key by ID.
        
        Args:
            key_id: The ID of the key to retrieve
            
        Returns:
            dict: Key data or None if not found
        """
        key_data = self.keys.get(key_id)
        
        if key_data and key_data.get('active'):
            # Update last used timestamp
            key_data['last_used'] = int(time.time())
            self._save_keys()
            return key_data
        
        return None
    
    def get_active_keys(self):
        """
        Get all active API keys.
        
        Returns:
            dict: All active keys with their IDs
        """
        now = int(time.time())
        active_keys = {
            key_id: key_data
            for key_id, key_data in self.keys.items()
            if key_data.get('active') and key_data.get('expires_at', 0) > now
        }
        return active_keys
    
    def revoke_key(self, key_id):
        """
        Revoke an API key.
        
        Args:
            key_id: The ID of the key to revoke
            
        Returns:
            bool: Success status
        """
        if key_id in self.keys:
            self.keys[key_id]['active'] = False
            return self._save_keys()
        return False
    
    def rotate_key(self, key_id, new_api_key, extend_expiry=True):
        """
        Rotate an API key.
        
        Args:
            key_id: The ID of the key to rotate
            new_api_key: The new API key value
            extend_expiry: Whether to extend the expiry
            
        Returns:
            bool: Success status
        """
        if key_id not in self.keys:
            return False
        
        # Keep original data but update key
        key_data = self.keys[key_id]
        key_data['api_key'] = new_api_key
        
        # Extend expiry if requested
        if extend_expiry:
            key_data['expires_at'] = int(time.time()) + (365 * 24 * 60 * 60)
        
        # Add rotation history
        if 'rotation_history' not in key_data:
            key_data['rotation_history'] = []
        
        key_data['rotation_history'].append({
            'rotated_at': int(time.time()),
            'previous_expires_at': key_data.get('expires_at')
        })
        
        return self._save_keys()
    
    def is_expired(self, key_id):
        """
        Check if a key is expired.
        
        Args:
            key_id: The ID of the key to check
            
        Returns:
            bool: True if expired, False otherwise
        """
        key_data = self.keys.get(key_id)
        if not key_data:
            return True
        
        now = int(time.time())
        return key_data.get('expires_at', 0) <= now
    
    def get_expiring_keys(self, days=30):
        """
        Get keys that are expiring soon.
        
        Args:
            days: Number of days threshold
            
        Returns:
            dict: Keys expiring within the threshold
        """
        now = int(time.time())
        threshold = now + (days * 24 * 60 * 60)
        
        expiring_keys = {
            key_id: key_data
            for key_id, key_data in self.keys.items()
            if key_data.get('active') and 
               key_data.get('expires_at', 0) > now and
               key_data.get('expires_at', 0) <= threshold
        }
        return expiring_keys
    
    def export_keys(self, include_revoked=False):
        """
        Export keys for backup (without sensitive data).
        
        Args:
            include_revoked: Whether to include revoked keys
            
        Returns:
            dict: Exported keys data
        """
        export_data = {}
        
        for key_id, key_data in self.keys.items():
            if not include_revoked and not key_data.get('active'):
                continue
            
            # Create a copy without the actual API key
            export_entry = key_data.copy()
            export_entry['api_key'] = '********'  # Redact actual key
            
            # Add human-readable dates
            for timestamp_field in ['created_at', 'expires_at', 'last_used']:
                if export_entry.get(timestamp_field):
                    export_entry[f"{timestamp_field}_formatted"] = datetime.datetime.fromtimestamp(
                        export_entry[timestamp_field]
                    ).strftime('%Y-%m-%d %H:%M:%S')
            
            export_data[key_id] = export_entry
        
        return export_data


# Example usage
if __name__ == "__main__":
    # Set a master password or use environment variable
    # os.environ["PYUNTO_MASTER_PASSWORD"] = "your-secure-password"
    
    # Example with password provided explicitly
    manager = APIKeyManager(master_password="your-secure-password")
    
    # Add a new API key
    key_id = manager.add_key(
        name="Production API Key",
        api_key="pyunto_api_12345",
        metadata={
            "environment": "production",
            "owner": "john.doe@example.com"
        }
    )
    print(f"Added new key with ID: {key_id}")
    
    # Get all active keys
    active_keys = manager.get_active_keys()
    print(f"Active keys: {len(active_keys)}")
    
    # Export keys for backup
    exported = manager.export_keys()
    print(json.dumps(exported, indent=2))

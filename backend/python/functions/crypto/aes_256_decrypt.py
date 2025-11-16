"""
AES-256 Decryption Utility

This module provides AES-256 decryption functionality using a secret key
loaded from environment variables (local.env or production.env).
"""

import os
import base64
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding
import sys

# Add parent directories to path to import utils
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from utils.env_loader import get_env_variable


def get_aes_secret_key() -> bytes:
    """
    Get the AES secret key from environment variables.
    
    Returns:
        32-byte key for AES-256 decryption
        
    Raises:
        ValueError: If AES_SECRET_KEY is not found in environment variables
    """
    secret_key = get_env_variable('AES_SECRET_KEY')
    if not secret_key:
        raise ValueError(
            "AES_SECRET_KEY not found in environment variables. "
            "Please add AES_SECRET_KEY to your .env file."
        )
    
    # Ensure the key is exactly 32 bytes (256 bits) for AES-256
    key_bytes = secret_key.encode('utf-8')
    if len(key_bytes) < 32:
        # Pad with zeros if too short
        key_bytes = key_bytes.ljust(32, b'\0')
    elif len(key_bytes) > 32:
        # Truncate if too long
        key_bytes = key_bytes[:32]
    
    return key_bytes


def decrypt(encrypted_string: str) -> str:
    """
    Decrypt an encrypted string using AES-256-CBC.
    
    Args:
        encrypted_string: Base64-encoded encrypted string (includes IV)
        
    Returns:
        The decrypted plaintext string
        
    Raises:
        ValueError: If decryption fails (invalid key, corrupted data, etc.)
        
    Example:
        from functions.crypto.aes_256_decrypt import decrypt
        
        decrypted = decrypt(encrypted_string)
        print(decrypted)  # Original plaintext
    """
    try:
        # Get the secret key
        key = get_aes_secret_key()
        
        # Decode from base64
        encrypted_data = base64.b64decode(encrypted_string.encode('utf-8'))
        
        # Extract IV (first 16 bytes) and ciphertext (rest)
        iv = encrypted_data[:16]
        ciphertext = encrypted_data[16:]
        
        # Create cipher
        cipher = Cipher(
            algorithms.AES(key),
            modes.CBC(iv),
            backend=default_backend()
        )
        decryptor = cipher.decryptor()
        
        # Decrypt
        padded_data = decryptor.update(ciphertext) + decryptor.finalize()
        
        # Unpad
        unpadder = padding.PKCS7(128).unpadder()
        plaintext_data = unpadder.update(padded_data)
        plaintext_data += unpadder.finalize()
        
        # Convert to string
        plaintext = plaintext_data.decode('utf-8')
        
        return plaintext
        
    except Exception as e:
        raise ValueError(f"Decryption failed: {str(e)}")


"""
AES-256 Encryption Utility

This module provides AES-256 encryption functionality using a secret key
loaded from environment variables (local.env or production.env).
"""

import os
import base64
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding
import secrets
import sys

# Add parent directories to path to import utils
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from utils.env_loader import get_env_variable


def get_aes_secret_key() -> bytes:
    """
    Get the AES secret key from environment variables.
    
    Returns:
        32-byte key for AES-256 encryption
        
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


def encrypt(plaintext: str) -> str:
    """
    Encrypt a plaintext string using AES-256-CBC.
    
    Args:
        plaintext: The string to encrypt
        
    Returns:
        Base64-encoded encrypted string (includes IV)
        
    Example:
        from functions.crypto.aes_256_encrypt import encrypt
        
        encrypted = encrypt("sensitive data")
        print(encrypted)  # Base64 encoded encrypted string
    """
    # Get the secret key
    key = get_aes_secret_key()
    
    # Generate a random IV (Initialization Vector)
    iv = secrets.token_bytes(16)
    
    # Create cipher
    cipher = Cipher(
        algorithms.AES(key),
        modes.CBC(iv),
        backend=default_backend()
    )
    encryptor = cipher.encryptor()
    
    # Pad the plaintext to be a multiple of 16 bytes (AES block size)
    padder = padding.PKCS7(128).padder()
    padded_data = padder.update(plaintext.encode('utf-8'))
    padded_data += padder.finalize()
    
    # Encrypt
    ciphertext = encryptor.update(padded_data) + encryptor.finalize()
    
    # Combine IV and ciphertext, then base64 encode
    encrypted_data = iv + ciphertext
    encrypted_string = base64.b64encode(encrypted_data).decode('utf-8')
    
    return encrypted_string


def generate_api_key() -> str:
    """
    Generate a random API access key.
    
    Returns:
        A random 32-byte API key encoded as hexadecimal string (64 characters)
        
    Example:
        from functions.crypto.aes_256_encrypt import generate_api_key
        
        api_key = generate_api_key()
        print(api_key)  # e.g., "a1b2c3d4e5f6..."
    """
    # Generate 32 random bytes (256 bits)
    api_key_bytes = secrets.token_bytes(32)
    # Convert to hexadecimal string (64 characters)
    api_key = api_key_bytes.hex()
    return api_key


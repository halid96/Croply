"""
Password Hashing and Validation Utility

This module provides secure password hashing and validation using bcrypt.
"""

import bcrypt


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.
    
    Args:
        password: The plaintext password to hash
        
    Returns:
        The hashed password as a string
        
    Example:
        from functions.crypto.password_hash import hash_password
        
        password_hash = hash_password("my_secure_password")
        print(password_hash)  # bcrypt hash string
    """
    # Generate salt and hash the password
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def validate_password_hash(password: str, password_hash: str) -> bool:
    """
    Validate a password against a hash.
    
    Args:
        password: The plaintext password to validate
        password_hash: The stored password hash to compare against
        
    Returns:
        True if the password matches the hash, False otherwise
        
    Example:
        from functions.crypto.password_hash import validate_password_hash
        
        is_valid = validate_password_hash("my_secure_password", stored_hash)
        if is_valid:
            print("Password is correct!")
    """
    try:
        # Check if the password matches the hash
        return bcrypt.checkpw(
            password.encode('utf-8'),
            password_hash.encode('utf-8')
        )
    except Exception:
        return False


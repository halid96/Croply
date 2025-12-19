"""
Password Hashing and Validation Utility

This module provides secure password hashing and validation using bcrypt.
Provides a PHP-like API: hash_password() and validate_password_hash().

Note: Uses python_bcrypt 0.3.2 which doesn't have checkpw() like standard bcrypt.
We work around this by hashing with the stored hash (contains salt) and comparing.
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
    # Handle both bcrypt implementations (some expect str, others bytes)
    pwd = password if isinstance(password, str) else password.decode("utf-8")
    salt = bcrypt.gensalt()
    if isinstance(salt, bytes):
        hashed = bcrypt.hashpw(pwd.encode("utf-8"), salt)
    else:
        hashed = bcrypt.hashpw(pwd, salt)
    return hashed.decode("utf-8") if isinstance(hashed, (bytes, bytearray)) else hashed


def validate_password_hash(password: str, password_hash: str) -> bool:
    """
    Validate a password against a hash.
    
    PHP-like API similar to password_verify($password, $hash).
    
    Args:
        password: The plaintext password to validate
        password_hash: The stored password hash to compare against
        
    Returns:
        True if the password matches the hash, False otherwise
        
    Example:
        from functions.crypto.password_hash import validate_password_hash
        
        # Similar to PHP: password_verify($password, $hash)
        is_valid = validate_password_hash("my_secure_password", stored_hash)
        if is_valid:
            print("Password is correct!")
    """
    if not password or not password_hash:
        print("validate_password_hash: Missing password or password_hash")
        return False
    
    try:
        # Ensure both are strings (python_bcrypt expects strings, not bytes)
        if not isinstance(password, str):
            password = str(password)
        if not isinstance(password_hash, str):
            password_hash = str(password_hash)
        
        # python_bcrypt doesn't have checkpw, so we need to hash the password
        # with the stored hash (which contains the salt) and compare
        # If the password is correct, the result will match the stored hash
        hashed = bcrypt.hashpw(password, password_hash)
        
        # Compare the hashed result with the stored hash
        # Use constant-time comparison to prevent timing attacks
        if len(hashed) != len(password_hash):
            return False
        result = 0
        for x, y in zip(hashed.encode('utf-8'), password_hash.encode('utf-8')):
            result |= x ^ y
        return result == 0
            
    except ValueError as e:
        print(f"validate_password_hash: Invalid hash format - {e}")
        return False
    except Exception as e:
        print(f"validate_password_hash: Unexpected error - {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False

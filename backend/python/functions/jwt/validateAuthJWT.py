"""
Validate Authentication JWT

Validates a JWT token and checks if it's expired or blacklisted.
"""

import os
import sys
import jwt
from typing import Optional, Dict, Any

# Add parent directories to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from utils.env_loader import get_env_variable
from utils.db_connector import get_db_connection


def get_jwt_secret() -> str:
    """
    Get JWT secret key from environment variables.
    
    Returns:
        JWT secret key string
        
    Raises:
        ValueError: If JWT_SECRET_KEY is not found
    """
    secret = get_env_variable('JWT_SECRET_KEY')
    if not secret:
        raise ValueError(
            "JWT_SECRET_KEY not found in environment variables. "
            "Please add JWT_SECRET_KEY to your .env file."
        )
    return secret


def is_token_blacklisted(token: str) -> bool:
    """
    Check if a JWT token is blacklisted (deleted/logged out).
    
    Args:
        token: JWT token string to check
        
    Returns:
        True if token is blacklisted, False otherwise
    """
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        # Check if token exists in blacklist
        query = "SELECT COUNT(*) FROM jwt_blacklist WHERE token = %s"
        cursor.execute(query, (token,))
        result = cursor.fetchone()
        
        return result[0] > 0 if result else False
        
    except Exception:
        return False
    finally:
        if conn:
            cursor.close()
            conn.close()


def validateAuthJWT(token: str) -> bool:
    """
    Validate a JWT token.
    
    Checks:
    - Token signature is valid
    - Token is not expired
    - Token is not blacklisted
    
    Args:
        token: JWT token string to validate
        
    Returns:
        True if token is valid, False otherwise
        
    Example:
        from functions.jwt.validateAuthJWT import validateAuthJWT
        
        is_valid = validateAuthJWT(token)
        if is_valid:
            print("Token is valid")
    """
    try:
        secret = get_jwt_secret()
        
        # Decode and verify token
        jwt.decode(token, secret, algorithms=['HS256'])
        
        # Check if token is blacklisted
        if is_token_blacklisted(token):
            return False
        
        return True
        
    except jwt.ExpiredSignatureError:
        return False
    except jwt.InvalidTokenError:
        return False
    except Exception:
        return False


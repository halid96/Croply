"""
Set Authentication JWT

Creates a JWT token with user_id payload for authentication.
"""

import os
import sys
from datetime import datetime, timedelta
import jwt

# Add parent directories to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from utils.env_loader import get_env_variable


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


def get_jwt_expiration_hours() -> int:
    """
    Get JWT expiration time in hours from environment variables.
    
    Returns:
        Expiration hours (default: 24)
    """
    hours = get_env_variable('JWT_EXPIRATION_HOURS', '24')
    try:
        return int(hours)
    except ValueError:
        return 24


def setAuthJWT(user_id: int) -> str:
    """
    Create a JWT token with user_id payload.
    
    Args:
        user_id: The user ID to include in the JWT payload
        
    Returns:
        JWT token string
        
    Example:
        from functions.jwt.setAuthJWT import setAuthJWT
        
        token = setAuthJWT(123)
        print(token)  # JWT token string
    """
    secret = get_jwt_secret()
    expiration_hours = get_jwt_expiration_hours()
    
    # Create payload
    payload = {
        'user_id': user_id,
        'iat': datetime.utcnow(),  # Issued at
        'exp': datetime.utcnow() + timedelta(hours=expiration_hours)  # Expiration
    }
    
    # Generate JWT token
    token = jwt.encode(payload, secret, algorithm='HS256')
    
    return token


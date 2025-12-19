"""
Get Payload from Authentication JWT

Extracts the payload (user_id) from a JWT token.
"""

import os
import sys
import jwt
from typing import Optional, Dict, Any

# Add parent directories to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from utils.env_loader import get_env_variable
from functions.jwt.validateAuthJWT import validateAuthJWT


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


def getPayloadAuthJWT(token: str) -> Optional[Dict[str, Any]]:
    """
    Get the payload from a JWT token.
    
    Args:
        token: JWT token string
        
    Returns:
        Dictionary containing the payload (including user_id), or None if invalid
        
    Example:
        from functions.jwt.getPayloadAuthJWT import getPayloadAuthJWT
        
        payload = getPayloadAuthJWT(token)
        if payload:
            user_id = payload['user_id']
            print(f"User ID: {user_id}")
    """
    try:
        # First validate the token
        if not validateAuthJWT(token):
            return None
        
        secret = get_jwt_secret()
        
        # Decode token (without verification since we already validated)
        payload = jwt.decode(token, secret, algorithms=['HS256'])
        
        return payload
        
    except Exception:
        return None


def get_user_id_from_token(token: str) -> Optional[int]:
    """
    Convenience function to get user_id directly from JWT token.
    
    Args:
        token: JWT token string
        
    Returns:
        User ID if token is valid, None otherwise
        
    Example:
        from functions.jwt.getPayloadAuthJWT import get_user_id_from_token
        
        user_id = get_user_id_from_token(token)
        if user_id:
            print(f"Current user ID: {user_id}")
    """
    payload = getPayloadAuthJWT(token)
    if payload and 'user_id' in payload:
        return payload['user_id']
    return None


"""
Delete Authentication JWT

Blacklists a JWT token to invalidate it (for logout functionality).
"""

import os
import sys
import jwt
from datetime import datetime
from typing import Optional

# Add parent directories to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from utils.env_loader import get_env_variable
from utils.db_connector import get_db_connection
from functions.jwt.getPayloadAuthJWT import getPayloadAuthJWT


def deleteAuthJWT(token: str) -> bool:
    """
    Blacklist a JWT token to invalidate it (logout).
    
    This adds the token to a blacklist table in the database.
    The token will be considered invalid even if it hasn't expired.
    
    Args:
        token: JWT token string to blacklist
        
    Returns:
        True if token was successfully blacklisted, False otherwise
        
    Example:
        from functions.jwt.deleteAuthJWT import deleteAuthJWT
        
        success = deleteAuthJWT(token)
        if success:
            print("Token invalidated successfully")
    """
    # First verify the token is valid before blacklisting
    payload = getPayloadAuthJWT(token)
    if not payload:
        return False
    
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        # Get expiration time from token
        secret = get_env_variable('JWT_SECRET_KEY')
        decoded = jwt.decode(token, secret, algorithms=['HS256'], options={"verify_exp": False})
        expires_at = decoded.get('exp', 0)
        
        # Insert token into blacklist
        query = """
            INSERT INTO jwt_blacklist (token, expires_at, created_at)
            VALUES (%s, FROM_UNIXTIME(%s), NOW())
            ON DUPLICATE KEY UPDATE created_at = NOW()
        """
        
        cursor.execute(query, (token, expires_at))
        conn.commit()
        
        return True
        
    except Exception as e:
        conn.rollback()
        print(f"Error blacklisting token: {e}")
        return False
        
    finally:
        cursor.close()
        conn.close()


"""
Login API Endpoint

This endpoint authenticates users by validating their email and password,
then returns a JWT token and user information.
"""

import os
import sys
from typing import Dict, Any

# Add parent directories to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr
from utils.db_connector import get_db_connection
from functions.crypto.password_hash import validate_password_hash
from functions.crypto.email_hash import hash_email
from functions.jwt.setAuthJWT import setAuthJWT

router = APIRouter()


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


def get_user_by_email(email: str) -> Dict[str, Any]:
    """
    Get user by email hash.
    
    Uses email_hash (SHA-256) for lookup since AES encryption produces
    different results each time due to random IV.
    
    Args:
        email: User's email address
        
    Returns:
        Dictionary with user data (id, display_name, encrypted_email, password_hash, api_credits)
        or None if user not found
    """
    conn = get_db_connection()
    if not conn:
        return None
    
    try:
        # Hash email for lookup (one-way hash, same result every time)
        email_hash = hash_email(email)
        
        cursor = conn.cursor()
        query = """
            SELECT id, display_name, encrypted_email, password_hash, api_credits
            FROM users
            WHERE email_hash = %s
            LIMIT 1
        """
        
        cursor.execute(query, (email_hash,))
        result = cursor.fetchone()
        
        if not result:
            return None
        
        return {
            'id': result[0],
            'display_name': result[1],
            'encrypted_email': result[2],
            'password_hash': result[3],
            'api_credits': result[4] or 0
        }
        
    except Exception as e:
        print(f"Error getting user by email: {e}")
        return None
    finally:
        cursor.close()
        conn.close()


@router.post("/login")
async def login(request: LoginRequest) -> Dict[str, Any]:
    """
    Login endpoint.
    
    Validates user credentials (email and password) and returns JWT token
    along with user information.
    
    Args:
        request: LoginRequest containing email and password
        
    Returns:
        JSON response with success status, JWT token, and user data
        
    Raises:
        HTTPException: If authentication fails
    """
    email = request.email
    password = request.password
    
    # Get user by email
    user = get_user_by_email(email)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    # Validate password
    if not validate_password_hash(password, user['password_hash']):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    # Generate JWT token
    try:
        jwt_token = setAuthJWT(user['id'])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate JWT token: {str(e)}")
    
    return JSONResponse(content={
        "success": True,
        "token": jwt_token,
        "user": {
            "id": user['id'],
            "email": email,
            "display_name": user['display_name']
        }
    }, status_code=200)


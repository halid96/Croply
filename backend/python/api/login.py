"""
Login API Endpoint

This endpoint authenticates users by validating their email and password,
then returns a JWT token and user information.
"""

import os
import sys
import traceback
from typing import Any, Dict, Optional

# Add parent directories to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr

from functions.crypto.email_hash import hash_email
from functions.crypto.password_hash import validate_password_hash
from functions.jwt.setAuthJWT import setAuthJWT
from utils.db_connector import get_db_connection

router = APIRouter()


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
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
        print("Error: Failed to get database connection")
        return None

    cursor = None
    try:
        # Hash email for lookup (one-way hash, same result every time)
        email_hash = hash_email(email)
        print(f"Looking up user with email hash: {email_hash[:16]}...")

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
            print(f"No user found with email hash: {email_hash[:16]}...")
            return None

        print(f"User found: ID={result[0]}, Display Name={result[1]}")
        return {
            "id": result[0],
            "display_name": result[1],
            "encrypted_email": result[2],
            "password_hash": result[3],
            "api_credits": float(result[4]) if result[4] is not None else 0.0,
        }

    except Exception as e:
        print(f"Error getting user by email: {e}")
        traceback.print_exc()
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@router.post("/login")
async def login(request: LoginRequest) -> JSONResponse:
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
        print(f"Login attempt failed: User not found for email: {email}")
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    # Validate password
    if not user.get("password_hash"):
        print(f"Login attempt failed: No password hash found for user ID: {user['id']}")
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    try:
        password_valid = validate_password_hash(password, user["password_hash"])
        if not password_valid:
            print(f"Login attempt failed: Invalid password for user ID: {user['id']}")
            raise HTTPException(status_code=401, detail="Invalid email or password")
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error during password validation: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Internal server error during authentication")
    
    # Generate JWT token
    try:
        jwt_token = setAuthJWT(user["id"])
    except Exception as e:
        print(f"Error generating JWT token: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate JWT token: {str(e)}")
    
    return JSONResponse(
        content={
            "success": True,
            "token": jwt_token,
            "user": {
                "id": user["id"],
                "email": email,
                "display_name": user["display_name"],
            },
        },
        status_code=200,
    )

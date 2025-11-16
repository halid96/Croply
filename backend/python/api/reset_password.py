"""
Reset Password API Endpoint

This endpoint validates a password reset token, checks expiration,
and updates the user's password.
"""

import os
import sys
from datetime import datetime
from typing import Dict, Any

# Add parent directories to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from utils.db_connector import get_db_connection
from functions.crypto.password_hash import hash_password

router = APIRouter()


class ResetPasswordRequest(BaseModel):
    token: str
    password: str


def validate_reset_token(token: str) -> Dict[str, Any]:
    """
    Validate password reset token and get user_id.
    
    Args:
        token: Password reset token
        
    Returns:
        Dictionary with user_id if token is valid, None otherwise
    """
    conn = get_db_connection()
    if not conn:
        return None
    
    try:
        cursor = conn.cursor()
        
        # Check if token exists and hasn't expired
        current_unix = int(datetime.now().timestamp())
        query = """
            SELECT user_id, expires_unix
            FROM password_reset_tokens
            WHERE token = %s AND expires_unix > %s
            LIMIT 1
        """
        
        cursor.execute(query, (token, current_unix))
        result = cursor.fetchone()
        
        if not result:
            return None
        
        return {
            'user_id': result[0],
            'expires_unix': result[1]
        }
        
    except Exception as e:
        print(f"Error validating reset token: {e}")
        return None
    finally:
        cursor.close()
        conn.close()


def delete_reset_token(token: str) -> bool:
    """
    Delete password reset token from database after use.
    
    Args:
        token: Token to delete
        
    Returns:
        True if deleted successfully, False otherwise
    """
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        query = "DELETE FROM password_reset_tokens WHERE token = %s"
        cursor.execute(query, (token,))
        conn.commit()
        return cursor.rowcount > 0
        
    except Exception as e:
        print(f"Error deleting reset token: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()


@router.post("/reset_password")
async def reset_password(request: ResetPasswordRequest) -> Dict[str, Any]:
    """
    Reset password endpoint.
    
    Validates the reset token, checks expiration, updates the user's password,
    and deletes the token.
    
    Args:
        request: ResetPasswordRequest containing token and new password
        
    Returns:
        JSON response with success status and user data (for auto-login)
        
    Raises:
        HTTPException: If token is invalid, expired, or password update fails
    """
    token = request.token
    password = request.password
    
    # Validate password
    if not password or len(password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
    
    # Validate reset token
    token_data = validate_reset_token(token)
    if not token_data:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")
    
    user_id = token_data['user_id']
    
    # Hash the new password
    password_hash = hash_password(password)
    
    # Update user password
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Failed to connect to database")
    
    cursor = None
    try:
        cursor = conn.cursor()
        
        # Update password
        query = "UPDATE users SET password_hash = %s WHERE id = %s"
        cursor.execute(query, (password_hash, user_id))
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="User not found")
        
        conn.commit()
        
        # Delete the reset token
        delete_reset_token(token)
        
        # Get user info for response
        user_query = "SELECT display_name FROM users WHERE id = %s LIMIT 1"
        cursor.execute(user_query, (user_id,))
        user_result = cursor.fetchone()
        
        return JSONResponse(content={
            "success": True,
            "message": "Password has been reset successfully",
            "user_id": user_id,
            "display_name": user_result[0] if user_result else None
        }, status_code=200)
        
    except HTTPException:
        raise
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"Error resetting password: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Error resetting password: {str(e)}"
        )
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


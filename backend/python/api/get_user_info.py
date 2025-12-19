"""
Get User Info API Endpoint

This endpoint returns user information including API credits and decrypted API key.
Requires JWT authentication.
"""

import os
import sys
from typing import Dict, Any, Optional

# Add parent directories to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from fastapi import APIRouter, HTTPException, Header
from fastapi.responses import JSONResponse
from utils.db_connector import get_db_connection
from functions.jwt.validateAuthJWT import validateAuthJWT
from functions.jwt.getPayloadAuthJWT import get_user_id_from_token
from functions.crypto.aes_256_decrypt import decrypt

router = APIRouter()


@router.get("/get_user_info")
async def get_user_info(authorization: str = Header(None)) -> Dict[str, Any]:
    """
    Get user information endpoint.
    
    Returns user's API credits and decrypted API access key.
    Requires JWT authentication via Authorization header.
    
    Args:
        authorization: Bearer token in Authorization header (format: "Bearer <token>")
        
    Returns:
        JSON response with user info including credits and API key
        
    Raises:
        HTTPException: If authentication fails or user not found
    """
    # Extract token from Authorization header
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")
    
    # Check if it's a Bearer token
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization format. Use 'Bearer <token>'")
    
    token = authorization.replace("Bearer ", "").strip()
    
    # Validate JWT token
    if not validateAuthJWT(token):
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    # Get user_id from token
    user_id = get_user_id_from_token(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Unable to extract user_id from token")
    
    # Get user info from database
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Failed to connect to database")
    
    cursor = None
    try:
        cursor = conn.cursor()
        
        # Get user's API credits and encrypted API key
        query = """
            SELECT api_credits, encrypted_api_key
            FROM users
            WHERE id = %s
            LIMIT 1
        """
        
        cursor.execute(query, (user_id,))
        result = cursor.fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail="User not found")
        
        api_credits = float(result[0]) if result[0] is not None else 0.00
        encrypted_api_key = result[1]
        
        # Decrypt API key
        api_key = None
        if encrypted_api_key:
            try:
                api_key = decrypt(encrypted_api_key)
            except Exception as e:
                print(f"Error decrypting API key: {e}")
                # Return None if decryption fails
                api_key = None
        
        return JSONResponse(content={
            "success": True,
            "balance": api_credits,  # Return as 'balance' for frontend consistency
            "api_key": api_key
        }, status_code=200)
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting user info: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving user info: {str(e)}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


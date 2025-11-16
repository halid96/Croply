"""
Regenerate API Key API Endpoint

This endpoint allows authenticated users to regenerate their API access key.
"""

import os
import sys
from typing import Dict
from fastapi import APIRouter, HTTPException, Header

# Add parent directories to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from utils.db_connector import get_db_connection
from functions.jwt.validateAuthJWT import validateAuthJWT
from functions.jwt.getPayloadAuthJWT import get_user_id_from_token
from functions.crypto.aes_256_encrypt import encrypt, generate_api_key

router = APIRouter()


@router.post("/regenerate_api_key")
async def regenerate_api_key(authorization: str = Header(None)) -> Dict[str, bool]:
    """
    Regenerate API key endpoint.
    
    Validates JWT token, extracts user_id, generates a new API key,
    encrypts it, and updates it in the database.
    
    Args:
        authorization: Bearer token in Authorization header (format: "Bearer <token>")
        
    Returns:
        JSON response with success status
        
    Raises:
        HTTPException: If authentication fails or database update fails
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
    
    # Generate new API key
    api_key = generate_api_key()
    
    # Encrypt the API key
    encrypted_api_key = encrypt(api_key)
    
    # Update in database
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Failed to connect to database")
    
    try:
        cursor = conn.cursor()
        
        # Update encrypted_api_key for the user
        query = """
            UPDATE users
            SET encrypted_api_key = %s
            WHERE id = %s
        """
        
        cursor.execute(query, (encrypted_api_key, user_id))
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="User not found")
        
        conn.commit()
        
        # Note: In production, you might want to return the new API key
        # to the user once, but for security, we're not returning it here.
        # The user should retrieve it through a secure channel if needed.
        
        return {"success": True}
        
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Error regenerating API key: {str(e)}")
        
    finally:
        cursor.close()
        conn.close()


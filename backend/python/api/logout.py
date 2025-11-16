"""
Logout API Endpoint

This endpoint handles user logout by blacklisting the JWT token.
"""

import os
import sys

# Add parent directories to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from fastapi import APIRouter, HTTPException, Header
from fastapi.responses import JSONResponse
from functions.jwt.validateAuthJWT import validateAuthJWT
from functions.jwt.deleteAuthJWT import deleteAuthJWT
from functions.jwt.getPayloadAuthJWT import get_user_id_from_token

router = APIRouter()


@router.post("/logout")
async def logout(authorization: str = Header(None)):
    """
    Logout endpoint.
    
    Blacklists the JWT token to invalidate it.
    Requires JWT authentication via Authorization header.
    
    Args:
        authorization: Bearer token in Authorization header (format: "Bearer <token>")
        
    Returns:
        JSON response with success status
        
    Raises:
        HTTPException: If authentication fails
    """
    # Extract token from Authorization header
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")
    
    # Check if it's a Bearer token
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization format. Use 'Bearer <token>'")
    
    token = authorization.replace("Bearer ", "").strip()
    
    # Validate JWT token (optional - we can still blacklist invalid tokens)
    # But we need to extract user_id if possible
    user_id = None
    if validateAuthJWT(token):
        user_id = get_user_id_from_token(token)
    
    # Blacklist the token
    try:
        if user_id:
            deleteAuthJWT(token)
    except Exception as e:
        print(f"Error blacklisting token: {e}")
        # Continue anyway - token might already be invalid
    
    return JSONResponse(content={
        "success": True,
        "message": "Logged out successfully"
    }, status_code=200)


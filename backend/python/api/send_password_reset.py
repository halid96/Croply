"""
Send Password Reset Token API Endpoint

This endpoint generates a password reset token, stores it in the database,
and sends a password reset URL via email.
"""

import os
import sys
import secrets
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import Dict

# Add parent directories to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr
from utils.db_connector import get_db_connection
from utils.env_loader import get_env_variable
from functions.crypto.email_hash import hash_email

router = APIRouter()


class PasswordResetRequest(BaseModel):
    email: EmailStr


def generate_reset_token() -> str:
    """
    Generate a secure random token for password reset.
    
    Returns:
        Random token string (32 characters)
    """
    return secrets.token_urlsafe(32)


def get_smtp_config() -> Dict[str, str]:
    """
    Get SMTP configuration from environment variables.
    
    Returns:
        Dictionary with SMTP configuration
        
    Raises:
        ValueError: If required SMTP credentials are missing
    """
    smtp_host = get_env_variable('SMTP_HOST')
    smtp_port = get_env_variable('SMTP_PORT', '587')
    smtp_user = get_env_variable('SMTP_USER')
    smtp_password = get_env_variable('SMTP_PASSWORD')
    smtp_from_email = get_env_variable('SMTP_FROM_EMAIL', smtp_user)
    smtp_from_name = get_env_variable('SMTP_FROM_NAME', 'Croply')
    smtp_use_tls = get_env_variable('SMTP_USE_TLS', 'true').lower() == 'true'
    
    if not all([smtp_host, smtp_user, smtp_password]):
        raise ValueError(
            "Missing required SMTP credentials in .env file. "
            "Required: SMTP_HOST, SMTP_USER, SMTP_PASSWORD"
        )
    
    return {
        'host': smtp_host,
        'port': int(smtp_port),
        'user': smtp_user,
        'password': smtp_password,
        'from_email': smtp_from_email,
        'from_name': smtp_from_name,
        'use_tls': smtp_use_tls
    }


def get_user_id_by_email(email: str) -> int:
    """
    Get user ID by email hash.
    
    Args:
        email: User's email address
        
    Returns:
        User ID if found, None otherwise
    """
    conn = get_db_connection()
    if not conn:
        return None
    
    try:
        email_hash = hash_email(email)
        cursor = conn.cursor()
        query = "SELECT id FROM users WHERE email_hash = %s LIMIT 1"
        cursor.execute(query, (email_hash,))
        result = cursor.fetchone()
        
        return result[0] if result else None
        
    except Exception as e:
        print(f"Error getting user ID by email: {e}")
        return None
    finally:
        cursor.close()
        conn.close()


def send_password_reset_email(email: str, token: str) -> bool:
    """
    Send password reset email with reset URL.
    
    Args:
        email: Recipient email address
        token: Password reset token
        
    Returns:
        True if email sent successfully, False otherwise
    """
    try:
        smtp_config = get_smtp_config()
        
        # Get base URL from environment or use default
        base_url = get_env_variable('BASE_URL', 'https://croply.uk')
        reset_url = f"{base_url}/?reset_token={token}"
        
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = 'Password Reset Request'
        msg['From'] = f"{smtp_config['from_name']} <{smtp_config['from_email']}>"
        msg['To'] = email
        
        # Create email body
        text = f"""
You requested a password reset for your Croply account.

Click the following link to reset your password:
{reset_url}

This link will expire in 1 hour.

If you didn't request this password reset, please ignore this email.
        """
        
        html = f"""
<html>
  <body>
    <h2>Password Reset Request</h2>
    <p>You requested a password reset for your Croply account.</p>
    <p><a href="{reset_url}" style="background: #6366f1; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block;">Reset Password</a></p>
    <p>Or copy and paste this link into your browser:</p>
    <p style="word-break: break-all; color: #64748b;">{reset_url}</p>
    <p>This link will expire in 1 hour.</p>
    <p>If you didn't request this password reset, please ignore this email.</p>
  </body>
</html>
        """
        
        # Attach parts
        part1 = MIMEText(text, 'plain')
        part2 = MIMEText(html, 'html')
        msg.attach(part1)
        msg.attach(part2)
        
        # Send email
        with smtplib.SMTP(smtp_config['host'], smtp_config['port'], timeout=10) as server:
            if smtp_config['use_tls']:
                server.starttls()
            server.login(smtp_config['user'], smtp_config['password'])
            server.send_message(msg)
        
        return True
        
    except Exception as e:
        print(f"Error sending password reset email: {e}")
        import traceback
        traceback.print_exc()
        return False


@router.post("/send_password_reset")
async def send_password_reset(request: PasswordResetRequest) -> JSONResponse:
    """
    Send password reset token endpoint.
    
    Generates a secure token, stores it in the database with expiration time (1 hour),
    and sends a password reset URL via email.
    
    Args:
        request: PasswordResetRequest containing the email address
        
    Returns:
        JSON response with success status
        
    Raises:
        HTTPException: If user not found or email sending fails
    """
    email = request.email
    
    # Get user ID by email
    user_id = get_user_id_by_email(email)
    if not user_id:
        # Don't reveal if email exists or not (security best practice)
        # Return success even if user doesn't exist
        return JSONResponse(content={
            "success": True,
            "message": "If the email exists, a password reset link has been sent."
        }, status_code=200)
    
    # Generate reset token
    token = generate_reset_token()
    
    # Calculate expiration time (1 hour from now)
    expires_unix = int((datetime.now() + timedelta(hours=1)).timestamp())
    
    # Store in database
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Failed to connect to database")
    
    cursor = None
    try:
        cursor = conn.cursor()
        
        # Insert password reset token
        query = """
            INSERT INTO password_reset_tokens (user_id, token, expires_unix)
            VALUES (%s, %s, %s)
        """
        
        cursor.execute(query, (user_id, token, expires_unix))
        conn.commit()
        
        # Send email
        email_sent = send_password_reset_email(email, token)
        
        if not email_sent:
            # Rollback if email failed
            conn.rollback()
            raise HTTPException(
                status_code=500,
                detail="Failed to send password reset email. Please try again later."
            )
        
        return JSONResponse(content={
            "success": True,
            "message": "If the email exists, a password reset link has been sent."
        }, status_code=200)
        
    except HTTPException:
        raise
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"Error in send_password_reset: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Error processing request: {str(e)}"
        )
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


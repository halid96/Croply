"""
Register User API Endpoint

This endpoint validates email verification code, creates a new user,
generates JWT token, and sends welcome email.
"""

import os
import sys
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Dict, Any

# Add parent directories to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from utils.db_connector import get_db_connection
from utils.env_loader import get_env_variable
from functions.db.add_new_user import add_new_user
from functions.jwt.setAuthJWT import setAuthJWT
from functions.crypto.email_hash import hash_email

router = APIRouter()


class RegisterUserRequest(BaseModel):
    email: EmailStr
    code: str
    display_name: str
    password: str


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


def validate_verification_code(code: str) -> bool:
    """
    Validate email verification code.
    
    Checks if the code exists and hasn't expired.
    
    Args:
        code: Verification code to validate
        
    Returns:
        True if code is valid, False otherwise
    """
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        # Check if code exists and hasn't expired
        current_unix = int(datetime.now().timestamp())
        query = """
            SELECT id, expires_unix
            FROM email_verification_codes
            WHERE code = %s AND expires_unix > %s
            LIMIT 1
        """
        
        cursor.execute(query, (code, current_unix))
        result = cursor.fetchone()
        
        return result is not None
        
    except Exception as e:
        print(f"Error validating verification code: {e}")
        return False
    finally:
        cursor.close()
        conn.close()


def delete_verification_code(code: str) -> bool:
    """
    Delete email verification code from database after successful use.
    
    Args:
        code: Verification code to delete
        
    Returns:
        True if code was deleted successfully, False otherwise
    """
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        # Delete the verification code
        query = "DELETE FROM email_verification_codes WHERE code = %s"
        cursor.execute(query, (code,))
        conn.commit()
        
        return cursor.rowcount > 0
        
    except Exception as e:
        print(f"Error deleting verification code: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()


def is_email_registered(email: str) -> bool:
    """
    Check if email is already registered.
    
    Uses email_hash for lookup since AES encryption produces different
    results each time due to random IV.
    
    Args:
        email: User's email address to check
        
    Returns:
        True if email is already registered, False otherwise
    """
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        # Hash email for lookup (one-way hash, same result every time)
        email_hash = hash_email(email)
        
        cursor = conn.cursor()
        query = "SELECT COUNT(*) FROM users WHERE email_hash = %s"
        cursor.execute(query, (email_hash,))
        result = cursor.fetchone()
        
        return result[0] > 0 if result else False
        
    except Exception as e:
        print(f"Error checking email registration: {e}")
        return False
    finally:
        cursor.close()
        conn.close()


def get_user_id_by_email(email: str) -> int:
    """
    Get user ID by email hash.
    
    Uses email_hash for lookup since AES encryption produces different
    results each time due to random IV.
    
    Args:
        email: User's email address
        
    Returns:
        User ID if found
        
    Raises:
        ValueError: If user not found
    """
    conn = get_db_connection()
    if not conn:
        raise ValueError("Failed to connect to database")
    
    try:
        # Hash email for lookup (one-way hash, same result every time)
        email_hash = hash_email(email)
        
        cursor = conn.cursor()
        query = "SELECT id FROM users WHERE email_hash = %s LIMIT 1"
        cursor.execute(query, (email_hash,))
        result = cursor.fetchone()
        
        if not result:
            raise ValueError("User not found")
        
        return result[0]
        
    except Exception as e:
        raise ValueError(f"Error getting user ID: {str(e)}")
    finally:
        cursor.close()
        conn.close()


def send_welcome_email(email: str, display_name: str) -> bool:
    """
    Send welcome email to newly registered user.
    
    Args:
        email: Recipient email address
        display_name: User's display name
        
    Returns:
        True if email sent successfully, False otherwise
    """
    try:
        smtp_config = get_smtp_config()
        
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = 'Welcome to Croply!'
        msg['From'] = f"{smtp_config['from_name']} <{smtp_config['from_email']}>"
        msg['To'] = email
        
        # Create email body
        text = f"""
Welcome to Croply, {display_name}!

Thank you for registering. Your account has been successfully created.

We're excited to have you on board!

Best regards,
The Croply Team
        """
        
        html = f"""
<html>
  <body>
    <h2>Welcome to Croply, {display_name}!</h2>
    <p>Thank you for registering. Your account has been successfully created.</p>
    <p>We're excited to have you on board!</p>
    <p>Best regards,<br>The Croply Team</p>
  </body>
</html>
        """
        
        # Attach parts
        part1 = MIMEText(text, 'plain')
        part2 = MIMEText(html, 'html')
        msg.attach(part1)
        msg.attach(part2)
        
        # Send email
        with smtplib.SMTP(smtp_config['host'], smtp_config['port']) as server:
            if smtp_config['use_tls']:
                server.starttls()
            server.login(smtp_config['user'], smtp_config['password'])
            server.send_message(msg)
        
        return True
        
    except Exception as e:
        print(f"Error sending welcome email: {e}")
        return False


@router.post("/register_user")
async def register_user(request: RegisterUserRequest) -> Dict[str, Any]:
    """
    Register user endpoint.
    
    This endpoint:
    1. Validates the email verification code
    2. Creates a new user account
    3. Generates JWT token
    4. Sends welcome email
    5. Returns success response
    
    Args:
        request: RegisterUserRequest containing email, code, display_name, and password
        
    Returns:
        JSON response with success status
        
    Raises:
        HTTPException: If validation fails or registration fails
    """
    email = request.email
    code = request.code
    display_name = request.display_name
    password = request.password
    
    # Check if email is already registered
    if is_email_registered(email):
        raise HTTPException(status_code=409, detail="Email is already registered")
    
    # Validate verification code
    if not validate_verification_code(code):
        raise HTTPException(status_code=400, detail="Invalid or expired verification code")
    
    # Create new user
    user_id = add_new_user(display_name, email, password)
    if not user_id:
        raise HTTPException(status_code=500, detail="Failed to create user account")
    
    # Generate JWT token
    try:
        jwt_token = setAuthJWT(user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate JWT token: {str(e)}")
    
    # Delete verification code after successful registration
    try:
        delete_verification_code(code)
    except Exception as e:
        print(f"Warning: Failed to delete verification code: {e}")
        # Continue even if deletion fails - code will expire anyway
    
    # Send welcome email (non-blocking - don't fail registration if email fails)
    try:
        send_welcome_email(email, display_name)
    except Exception as e:
        print(f"Warning: Failed to send welcome email: {e}")
        # Continue even if email fails
    
    return {
        "success": True,
        "token": jwt_token,
        "user": {
            "id": user_id,
            "email": email,
            "display_name": display_name
        }
    }


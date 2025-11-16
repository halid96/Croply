"""
Send Email Verification Code API Endpoint

This endpoint generates a verification code, stores it in the database,
and sends it via email using SMTP.
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

router = APIRouter()


class EmailRequest(BaseModel):
    email: EmailStr


def generate_verification_code() -> str:
    """
    Generate a random 6-digit verification code.
    
    Returns:
        6-digit code as string
    """
    return ''.join([str(secrets.randbelow(10)) for _ in range(6)])


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


def send_verification_email(email: str, code: str) -> bool:
    """
    Send verification code via email.
    
    Args:
        email: Recipient email address
        code: Verification code to send
        
    Returns:
        True if email sent successfully, False otherwise
    """
    try:
        print(f"[DEBUG] Getting SMTP configuration...")
        smtp_config = get_smtp_config()
        print(f"[DEBUG] SMTP config loaded: host={smtp_config['host']}, port={smtp_config['port']}")
        
        # Create message
        print("[DEBUG] Creating email message...")
        msg = MIMEMultipart('alternative')
        msg['Subject'] = 'Email Verification Code'
        msg['From'] = f"{smtp_config['from_name']} <{smtp_config['from_email']}>"
        msg['To'] = email
        
        # Create email body
        text = f"""
Your email verification code is: {code}

This code will expire in 10 minutes.

If you didn't request this code, please ignore this email.
        """
        
        html = f"""
<html>
  <body>
    <h2>Email Verification Code</h2>
    <p>Your email verification code is: <strong>{code}</strong></p>
    <p>This code will expire in 10 minutes.</p>
    <p>If you didn't request this code, please ignore this email.</p>
  </body>
</html>
        """
        
        # Attach parts
        part1 = MIMEText(text, 'plain')
        part2 = MIMEText(html, 'html')
        msg.attach(part1)
        msg.attach(part2)
        
        # Send email
        print(f"[DEBUG] Connecting to SMTP server {smtp_config['host']}:{smtp_config['port']}...")
        with smtplib.SMTP(smtp_config['host'], smtp_config['port'], timeout=10) as server:
            if smtp_config['use_tls']:
                print("[DEBUG] Starting TLS...")
                server.starttls()
            print("[DEBUG] Logging in to SMTP server...")
            server.login(smtp_config['user'], smtp_config['password'])
            print("[DEBUG] Sending email message...")
            server.send_message(msg)
            print("[DEBUG] Email sent successfully")
        
        return True
        
    except ValueError as ve:
        print(f"[ERROR] ValueError in send_verification_email: {ve}")
        import traceback
        traceback.print_exc()
        return False
    except smtplib.SMTPException as smtp_e:
        print(f"[ERROR] SMTP error in send_verification_email: {smtp_e}")
        import traceback
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"[ERROR] Unexpected error in send_verification_email: {e}")
        import traceback
        traceback.print_exc()
        return False


@router.post("/send_email_verification_code")
async def send_email_verification_code(request: EmailRequest) -> JSONResponse:
    """
    Send email verification code endpoint.
    
    Generates a 6-digit verification code, stores it in the database
    with expiration time (10 minutes), and sends it via email.
    
    Args:
        request: EmailRequest containing the email address
        
    Returns:
        JSON response with success status
        
    Raises:
        HTTPException: If database or email sending fails
    """
    print(f"[DEBUG] ====== ENDPOINT CALLED ======")
    print(f"[DEBUG] Received request to send verification code")
    
    # Immediate response test - return early to verify endpoint works
    try:
        email = request.email
        print(f"[DEBUG] Email extracted: {email}")
    except Exception as e:
        print(f"[ERROR] Failed to extract email: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            content={"success": False, "detail": f"Invalid request: {str(e)}"},
            status_code=400
        )
    
    conn = None
    cursor = None
    
    try:
        # Generate verification code
        print("[DEBUG] Generating verification code...")
        code = generate_verification_code()
        print(f"[DEBUG] Generated code: {code}")
        
        # Calculate expiration time (10 minutes from now)
        expires_unix = int((datetime.now() + timedelta(minutes=10)).timestamp())
        print(f"[DEBUG] Code expires at: {expires_unix}")
        
        # Store in database
        print("[DEBUG] Connecting to database...")
        conn = get_db_connection()
        if not conn:
            print("[ERROR] Failed to connect to database")
            return JSONResponse(
                content={"success": False, "detail": "Failed to connect to database"},
                status_code=500
            )
        
        print("[DEBUG] Database connection successful")
        cursor = conn.cursor()
        
        # Insert verification code
        print("[DEBUG] Inserting verification code into database...")
        query = """
            INSERT INTO email_verification_codes (code, expires_unix)
            VALUES (%s, %s)
        """
        
        cursor.execute(query, (code, expires_unix))
        conn.commit()
        print("[DEBUG] Verification code stored in database")
        
        # Send email (non-blocking - don't fail if email fails)
        print("[DEBUG] Attempting to send verification email...")
        email_sent = False
        try:
            email_sent = send_verification_email(email, code)
            print(f"[DEBUG] Email sending result: {email_sent}")
        except Exception as email_error:
            print(f"[ERROR] Exception in send_verification_email: {email_error}")
            import traceback
            traceback.print_exc()
            email_sent = False
        
        # Always return success if code was stored, even if email failed
        # (Email failure is logged but doesn't block registration)
        print("[DEBUG] Preparing response...")
        response_data = {
            "success": True,
            "message": "Verification code sent successfully" if email_sent else "Verification code generated (email may not have been sent)"
        }
        print(f"[DEBUG] Response data: {response_data}")
        
        response = JSONResponse(content=response_data, status_code=200)
        print(f"[DEBUG] Response created: {response_data}")
        print("[DEBUG] Returning response...")
        return response
        
    except HTTPException as http_ex:
        print(f"[ERROR] HTTPException: {http_ex.detail}")
        if conn:
            try:
                conn.rollback()
            except:
                pass
        # Return JSONResponse instead of raising HTTPException
        return JSONResponse(
            content={"success": False, "detail": http_ex.detail},
            status_code=http_ex.status_code
        )
    except Exception as e:
        print(f"[ERROR] Unexpected error in send_email_verification_code: {e}")
        import traceback
        traceback.print_exc()
        if conn:
            try:
                conn.rollback()
            except:
                pass
        # Return JSONResponse instead of raising HTTPException
        return JSONResponse(
            content={"success": False, "detail": f"Error processing request: {str(e)}"},
            status_code=500
        )
    finally:
        if cursor:
            try:
                cursor.close()
            except:
                pass
        if conn:
            try:
                conn.close()
            except:
                pass
        print("[DEBUG] Cleaned up database connections")


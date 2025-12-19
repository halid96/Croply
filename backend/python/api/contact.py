"""
Contact Form API Endpoint
"""

import os
import sys
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict

# Add parent directories to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr
from utils.env_loader import get_env_variable

router = APIRouter()

class ContactRequest(BaseModel):
    email: EmailStr
    title: str
    subject: str

def get_smtp_config() -> Dict[str, str]:
    """
    Get SMTP configuration from environment variables.
    """
    smtp_host = get_env_variable('SMTP_HOST')
    smtp_port = get_env_variable('SMTP_PORT', '587')
    smtp_user = get_env_variable('SMTP_USER')
    smtp_password = get_env_variable('SMTP_PASSWORD')
    smtp_from_email = get_env_variable('SMTP_FROM_EMAIL', smtp_user)
    smtp_from_name = get_env_variable('SMTP_FROM_NAME', 'Croply')
    smtp_use_tls = get_env_variable('SMTP_USE_TLS', 'true').lower() == 'true'
    
    if not all([smtp_host, smtp_user, smtp_password]):
        raise ValueError("Missing required SMTP credentials")
    
    return {
        'host': smtp_host,
        'port': int(smtp_port),
        'user': smtp_user,
        'password': smtp_password,
        'from_email': smtp_from_email,
        'from_name': smtp_from_name,
        'use_tls': smtp_use_tls
    }

def send_contact_email(user_email: str, title: str, subject: str) -> bool:
    """
    Send contact email to admin.
    """
    try:
        smtp_config = get_smtp_config()
        admin_email = get_env_variable('ADMIN_EMAIL')
        
        if not admin_email:
            print("ADMIN_EMAIL not set in .env")
            return False

        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"New Contact: {title}"
        msg['From'] = f"{smtp_config['from_name']} <{smtp_config['from_email']}>"
        msg['To'] = admin_email
        msg['Reply-To'] = user_email

        text = f"""
New contact form submission from Croply.

From: {user_email}
Title: {title}
Subject: {subject}
        """
        
        html = f"""
<html>
  <body>
    <h2>New Contact Form Submission</h2>
    <p><strong>From:</strong> {user_email}</p>
    <p><strong>Title:</strong> {title}</p>
    <p><strong>Subject/Message:</strong></p>
    <p>{subject}</p>
  </body>
</html>
        """

        part1 = MIMEText(text, 'plain')
        part2 = MIMEText(html, 'html')
        msg.attach(part1)
        msg.attach(part2)

        with smtplib.SMTP(smtp_config['host'], smtp_config['port'], timeout=10) as server:
            if smtp_config['use_tls']:
                server.starttls()
            server.login(smtp_config['user'], smtp_config['password'])
            server.send_message(msg)
            
        return True
    except Exception as e:
        print(f"Error sending contact email: {e}")
        return False

@router.post("/contact")
async def contact_form(request: ContactRequest) -> JSONResponse:
    """
    Handle contact form submission.
    """
    email_sent = send_contact_email(request.email, request.title, request.subject)
    
    if not email_sent:
        raise HTTPException(status_code=500, detail="Failed to send message")
        
    return JSONResponse(content={
        "success": True,
        "message": "Your message sent successfully"
    })

"""
Email utilities for sending password reset and other notifications
"""

import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from config import settings
from utils.logging import get_logger

logger = get_logger(__name__)

def send_email(to_email: str, subject: str, html_body: str, text_body: Optional[str] = None) -> bool:
    """
    Send an email using SMTP configuration from settings
    Returns True if sent successfully, False otherwise
    """
    try:
        # Create message
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = settings.from_email
        message["To"] = to_email
        
        # Add text version if provided
        if text_body:
            text_part = MIMEText(text_body, "plain")
            message.attach(text_part)
        
        # Add HTML version
        html_part = MIMEText(html_body, "html")
        message.attach(html_part)
        
        # Create SMTP connection
        context = ssl.create_default_context()
        
        # For development/testing, we'll log the email instead of sending
        if settings.environment == "development" and settings.smtp_server == "localhost":
            logger.info(f"""
            ================== EMAIL (DEV MODE) ==================
            To: {to_email}
            From: {settings.from_email}
            Subject: {subject}
            
            {text_body or 'No text body'}
            
            HTML Body:
            {html_body}
            =====================================================
            """)
            return True
        
        # Send email in production
        with smtplib.SMTP(settings.smtp_server, settings.smtp_port) as server:
            if settings.smtp_use_tls:
                server.starttls(context=context)
            
            if settings.smtp_username and settings.smtp_password:
                server.login(settings.smtp_username, settings.smtp_password)
            
            server.sendmail(settings.from_email, to_email, message.as_string())
        
        logger.info(f"Email sent successfully to {to_email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {str(e)}")
        return False

def send_password_reset_email(user_email: str, user_name: str, reset_token: str) -> bool:
    """
    Send password reset email with token
    """
    reset_url = f"{settings.frontend_url}/reset-password?token={reset_token}"
    
    subject = f"{settings.app_name} - Password Reset Request"
    
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Password Reset</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 600px;
                margin: 0 auto;
                padding: 20px;
            }}
            .header {{
                background-color: #4f46e5;
                color: white;
                padding: 20px;
                text-align: center;
                border-radius: 8px 8px 0 0;
            }}
            .content {{
                background-color: #f9fafb;
                padding: 30px;
                border-radius: 0 0 8px 8px;
                border: 1px solid #e5e7eb;
            }}
            .button {{
                display: inline-block;
                background-color: #4f46e5;
                color: white;
                padding: 12px 24px;
                text-decoration: none;
                border-radius: 6px;
                margin: 20px 0;
                font-weight: bold;
            }}
            .warning {{
                background-color: #fef3cd;
                border: 1px solid #faebcd;
                padding: 15px;
                border-radius: 6px;
                margin: 20px 0;
            }}
            .footer {{
                text-align: center;
                margin-top: 30px;
                font-size: 14px;
                color: #6b7280;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>{settings.app_name}</h1>
            <h2>Password Reset Request</h2>
        </div>
        
        <div class="content">
            <p>Hello {user_name},</p>
            
            <p>We received a request to reset your password for your {settings.app_name} account.</p>
            
            <p>Click the button below to reset your password:</p>
            
            <div style="text-align: center;">
                <a href="{reset_url}" class="button">Reset Password</a>
            </div>
            
            <div class="warning">
                <strong>Important:</strong>
                <ul>
                    <li>This link expires in 1 hour for security reasons</li>
                    <li>If you didn't request this reset, you can safely ignore this email</li>
                    <li>Your password won't change until you create a new one</li>
                </ul>
            </div>
            
            <p>If the button doesn't work, you can copy and paste this link into your browser:</p>
            <p style="word-break: break-all; background-color: #f3f4f6; padding: 10px; border-radius: 4px;">
                {reset_url}
            </p>
            
            <p>If you need help, please contact our support team.</p>
            
            <p>Best regards,<br>The {settings.app_name} Team</p>
        </div>
        
        <div class="footer">
            <p>This is an automated message. Please do not reply to this email.</p>
        </div>
    </body>
    </html>
    """
    
    text_body = f"""
    {settings.app_name} - Password Reset Request
    
    Hello {user_name},
    
    We received a request to reset your password for your {settings.app_name} account.
    
    To reset your password, visit the following link:
    {reset_url}
    
    Important:
    - This link expires in 1 hour for security reasons
    - If you didn't request this reset, you can safely ignore this email
    - Your password won't change until you create a new one
    
    If you need help, please contact our support team.
    
    Best regards,
    The {settings.app_name} Team
    
    ---
    This is an automated message. Please do not reply to this email.
    """
    
    return send_email(user_email, subject, html_body, text_body)
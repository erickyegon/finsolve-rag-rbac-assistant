"""
Email Service for FinSolve Technologies AI Assistant
Handles email notifications and communications

Author: Dr. Erick K. Yegon
Email: keyegon@gmail.com
Version: 1.0.0
"""

import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import List, Optional, Dict, Any
from pathlib import Path
import logging
from datetime import datetime

from ..core.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """
    Professional email service for FinSolve Technologies
    Handles SMTP configuration and email sending functionality
    """
    
    def __init__(self):
        """Initialize email service with configuration from settings"""
        self.smtp_server = settings.smtp_server
        self.smtp_port = settings.smtp_port
        self.email = settings.system_email
        self.password = settings.email_password
        self.use_tls = settings.email_use_tls
        
    def _create_smtp_connection(self) -> smtplib.SMTP:
        """Create and configure SMTP connection"""
        try:
            # Create SMTP connection
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            
            if self.use_tls:
                # Create secure context and start TLS
                context = ssl.create_default_context()
                server.starttls(context=context)
            
            # Login to email account
            server.login(self.email, self.password)
            
            return server
            
        except Exception as e:
            logger.error(f"Failed to create SMTP connection: {str(e)}")
            raise
    
    def send_email(
        self,
        to_emails: List[str],
        subject: str,
        body: str,
        html_body: Optional[str] = None,
        cc_emails: Optional[List[str]] = None,
        bcc_emails: Optional[List[str]] = None,
        attachments: Optional[List[Path]] = None
    ) -> bool:
        """
        Send email with optional HTML content and attachments
        
        Args:
            to_emails: List of recipient email addresses
            subject: Email subject line
            body: Plain text email body
            html_body: Optional HTML email body
            cc_emails: Optional CC recipients
            bcc_emails: Optional BCC recipients
            attachments: Optional list of file paths to attach
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        try:
            # Create message
            message = MIMEMultipart("alternative")
            message["From"] = self.email
            message["To"] = ", ".join(to_emails)
            message["Subject"] = subject
            
            if cc_emails:
                message["Cc"] = ", ".join(cc_emails)
            
            # Add timestamp
            message["Date"] = datetime.now().strftime("%a, %d %b %Y %H:%M:%S %z")
            
            # Add plain text part
            text_part = MIMEText(body, "plain")
            message.attach(text_part)
            
            # Add HTML part if provided
            if html_body:
                html_part = MIMEText(html_body, "html")
                message.attach(html_part)
            
            # Add attachments if provided
            if attachments:
                for attachment_path in attachments:
                    if attachment_path.exists():
                        with open(attachment_path, "rb") as attachment:
                            part = MIMEBase("application", "octet-stream")
                            part.set_payload(attachment.read())
                        
                        encoders.encode_base64(part)
                        part.add_header(
                            "Content-Disposition",
                            f"attachment; filename= {attachment_path.name}",
                        )
                        message.attach(part)
            
            # Prepare recipient list
            all_recipients = to_emails.copy()
            if cc_emails:
                all_recipients.extend(cc_emails)
            if bcc_emails:
                all_recipients.extend(bcc_emails)
            
            # Send email
            with self._create_smtp_connection() as server:
                server.sendmail(self.email, all_recipients, message.as_string())
            
            logger.info(f"Email sent successfully to {len(all_recipients)} recipients")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")
            return False
    
    def send_notification(
        self,
        recipient: str,
        notification_type: str,
        data: Dict[str, Any]
    ) -> bool:
        """
        Send system notification email
        
        Args:
            recipient: Recipient email address
            notification_type: Type of notification (alert, info, error, etc.)
            data: Notification data dictionary
            
        Returns:
            bool: True if notification sent successfully
        """
        try:
            # Generate subject based on notification type
            subject_map = {
                "alert": "🚨 FinSolve AI Assistant Alert",
                "info": "ℹ️ FinSolve AI Assistant Information",
                "error": "❌ FinSolve AI Assistant Error",
                "success": "✅ FinSolve AI Assistant Success",
                "warning": "⚠️ FinSolve AI Assistant Warning"
            }
            
            subject = subject_map.get(notification_type, "📧 FinSolve AI Assistant Notification")
            
            # Generate email body
            body = self._generate_notification_body(notification_type, data)
            html_body = self._generate_notification_html(notification_type, data)
            
            return self.send_email(
                to_emails=[recipient],
                subject=subject,
                body=body,
                html_body=html_body
            )
            
        except Exception as e:
            logger.error(f"Failed to send notification: {str(e)}")
            return False
    
    def _generate_notification_body(self, notification_type: str, data: Dict[str, Any]) -> str:
        """Generate plain text notification body"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        body = f"""
FinSolve Technologies AI Assistant Notification

Type: {notification_type.upper()}
Timestamp: {timestamp}

"""
        
        for key, value in data.items():
            body += f"{key.replace('_', ' ').title()}: {value}\n"
        
        body += f"""

---
This is an automated message from FinSolve AI Assistant.
For support, contact: {self.email}

Best regards,
Dr. Erick K. Yegon
FinSolve Technologies AI Assistant
"""
        
        return body
    
    def _generate_notification_html(self, notification_type: str, data: Dict[str, Any]) -> str:
        """Generate HTML notification body"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Color scheme based on notification type
        color_map = {
            "alert": "#F44336",
            "info": "#2196F3", 
            "error": "#F44336",
            "success": "#4CAF50",
            "warning": "#FF9800"
        }
        
        color = color_map.get(notification_type, "#0D1B2A")
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>FinSolve AI Assistant Notification</title>
</head>
<body style="font-family: 'Roboto', Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="background: linear-gradient(135deg, #0D1B2A 0%, #1a2332 100%); padding: 20px; border-radius: 12px; margin-bottom: 20px;">
        <h1 style="color: #00F5D4; margin: 0; font-size: 24px;">FinSolve Technologies</h1>
        <p style="color: #FFFFFF; margin: 5px 0 0 0; font-size: 16px;">AI Assistant Notification</p>
    </div>
    
    <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; border-left: 4px solid {color};">
        <h2 style="color: {color}; margin-top: 0;">{notification_type.upper()} Notification</h2>
        <p style="margin: 10px 0;"><strong>Timestamp:</strong> {timestamp}</p>
        
        <div style="margin: 20px 0;">
"""
        
        for key, value in data.items():
            html += f"            <p style='margin: 8px 0;'><strong>{key.replace('_', ' ').title()}:</strong> {value}</p>\n"
        
        html += f"""
        </div>
    </div>
    
    <div style="margin-top: 30px; padding: 20px; background: #f1f1f1; border-radius: 8px; text-align: center;">
        <p style="margin: 0; color: #666; font-size: 14px;">
            This is an automated message from FinSolve AI Assistant.<br>
            For support, contact: <a href="mailto:{self.email}" style="color: #00F5D4;">{self.email}</a>
        </p>
        <hr style="border: none; border-top: 1px solid #ddd; margin: 15px 0;">
        <p style="margin: 0; color: #666; font-size: 12px;">
            <strong>Dr. Erick K. Yegon</strong><br>
            FinSolve Technologies AI Assistant<br>
            <a href="mailto:{self.email}" style="color: #00F5D4;">{self.email}</a>
        </p>
    </div>
</body>
</html>
"""
        
        return html


# Global email service instance
email_service = EmailService()

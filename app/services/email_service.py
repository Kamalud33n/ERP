"""
Email Service - SMTP integration for notifications, approvals, and alerts
Supports async email delivery with retry logic
"""
import asyncio
import logging
from typing import List, Optional
from datetime import datetime
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
import os

load_dotenv()

logger = logging.getLogger(__name__)

class EmailConfig:
    """Email configuration from environment variables"""
    SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
    SMTP_FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL", "noreply@mednova.com")
    SMTP_FROM_NAME = os.getenv("SMTP_FROM_NAME", "MedNova ERP")
    
    @classmethod
    def is_configured(cls):
        """Check if SMTP is properly configured"""
        return bool(cls.SMTP_USER and cls.SMTP_PASSWORD)


class EmailService:
    """Send emails via SMTP with retry and templating support"""
    
    @staticmethod
    def _build_email_message(
        to_email: str,
        subject: str,
        html_content: str,
        reply_to: Optional[str] = None
    ) -> MIMEMultipart:
        """Build MIME email message"""
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{EmailConfig.SMTP_FROM_NAME} <{EmailConfig.SMTP_FROM_EMAIL}>"
        msg["To"] = to_email
        if reply_to:
            msg["Reply-To"] = reply_to
        
        # Plain text fallback
        text_content = html_content.replace("<br>", "\n").replace("<p>", "").replace("</p>", "\n")
        msg.attach(MIMEText(text_content, "plain", "utf-8"))
        
        # HTML version
        msg.attach(MIMEText(html_content, "html", "utf-8"))
        
        return msg

    @staticmethod
    async def send_email(
        to_email: str,
        subject: str,
        html_content: str,
        reply_to: Optional[str] = None
    ) -> bool:
        """
        Send a single email via SMTP
        Returns: True if successful, False otherwise
        """
        if not EmailConfig.is_configured():
            logger.warning(f"SMTP not configured. Email to {to_email} not sent.")
            return False
        
        try:
            msg = EmailService._build_email_message(to_email, subject, html_content, reply_to)
            
            async with aiosmtplib.SMTP(hostname=EmailConfig.SMTP_HOST, port=EmailConfig.SMTP_PORT) as smtp:
                await smtp.login(EmailConfig.SMTP_USER, EmailConfig.SMTP_PASSWORD)
                await smtp.send_message(msg)
            
            logger.info(f"✉️ Email sent to {to_email}: {subject}")
            return True
        
        except Exception as e:
            logger.error(f"❌ Failed to send email to {to_email}: {str(e)}")
            return False

    @staticmethod
    async def send_bulk_emails(
        recipients: List[str],
        subject: str,
        html_content: str
    ) -> dict:
        """
        Send emails to multiple recipients
        Returns: {success: int, failed: int}
        """
        results = {"success": 0, "failed": 0}
        
        for email in recipients:
            success = await EmailService.send_email(email, subject, html_content)
            if success:
                results["success"] += 1
            else:
                results["failed"] += 1
        
        return results


# ─────────────────────────────────────────────────────────────────
# Email Templates
# ─────────────────────────────────────────────────────────────────

class EmailTemplates:
    """Pre-built email templates for common workflows"""
    
    @staticmethod
    def approval_notification(
        approver_name: str,
        request_type: str,  # "Leave", "Purchase Request", "Expense Claim"
        requester_name: str,
        amount: Optional[float] = None,
        description: str = "",
        action_link: str = ""
    ) -> str:
        """Notification email for pending approvals"""
        amount_html = f"<p><strong>Amount:</strong> ${amount:,.2f}</p>" if amount else ""
        
        return f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; border: 1px solid #e0e0e0; border-radius: 8px; padding: 20px;">
                    <div style="background: #3b82f6; color: white; padding: 20px; border-radius: 8px 8px 0 0; text-align: center;">
                        <h2 style="margin: 0;">🏥 MedNova ERP</h2>
                        <p style="margin: 5px 0 0 0; font-size: 14px;">Pending Approval Required</p>
                    </div>
                    
                    <div style="padding: 20px;">
                        <p>Hello <strong>{approver_name}</strong>,</p>
                        
                        <p>A new <strong>{request_type}</strong> requires your approval:</p>
                        
                        <div style="background: #f0f9ff; border-left: 4px solid #3b82f6; padding: 15px; margin: 15px 0; border-radius: 4px;">
                            <p><strong>Requester:</strong> {requester_name}</p>
                            <p><strong>Type:</strong> {request_type}</p>
                            {amount_html}
                            {f'<p><strong>Description:</strong> {description}</p>' if description else ''}
                        </div>
                        
                        {f'<p><a href="{action_link}" style="display: inline-block; background: #10b981; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px; font-weight: bold;">Review & Approve →</a></p>' if action_link else ''}
                        
                        <p style="color: #666; font-size: 12px; margin-top: 20px;">
                            This is an automated notification from MedNova ERP. Please do not reply to this email.
                        </p>
                    </div>
                </div>
            </body>
        </html>
        """

    @staticmethod
    def approval_decision(
        requester_name: str,
        request_type: str,
        status: str,  # "approved", "rejected"
        approved_by: str = "",
        comments: str = "",
        amount: Optional[float] = None
    ) -> str:
        """Notification email for approval decision (approved/rejected)"""
        status_color = "#10b981" if status == "approved" else "#ef4444"
        status_emoji = "✅" if status == "approved" else "❌"
        amount_html = f"<p><strong>Amount:</strong> ${amount:,.2f}</p>" if amount else ""
        
        return f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; border: 1px solid #e0e0e0; border-radius: 8px; padding: 20px;">
                    <div style="background: {status_color}; color: white; padding: 20px; border-radius: 8px 8px 0 0; text-align: center;">
                        <h2 style="margin: 0;">{status_emoji} {status.title()}</h2>
                    </div>
                    
                    <div style="padding: 20px;">
                        <p>Hello <strong>{requester_name}</strong>,</p>
                        
                        <p>Your <strong>{request_type}</strong> has been <strong style="color: {status_color};">{status.upper()}</strong>.</p>
                        
                        <div style="background: #f9fafb; border-left: 4px solid {status_color}; padding: 15px; margin: 15px 0; border-radius: 4px;">
                            <p><strong>Request Type:</strong> {request_type}</p>
                            {amount_html}
                            {f'<p><strong>Approved By:</strong> {approved_by}</p>' if approved_by else ''}
                            {f'<p><strong>Comments:</strong> {comments}</p>' if comments else ''}
                        </div>
                        
                        <p style="color: #666; font-size: 12px; margin-top: 20px;">
                            For more details, please log in to your MedNova ERP account.
                        </p>
                    </div>
                </div>
            </body>
        </html>
        """

    @staticmethod
    def alert_notification(
        recipient_name: str,
        alert_type: str,  # "low_stock", "budget_exceeded", "contract_expiry"
        title: str,
        details: str,
        action_required: bool = False
    ) -> str:
        """Alert notification email"""
        alert_color = "#f59e0b"  # Amber for alerts
        
        return f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; border: 1px solid #e0e0e0; border-radius: 8px; padding: 20px;">
                    <div style="background: {alert_color}; color: white; padding: 20px; border-radius: 8px 8px 0 0; text-align: center;">
                        <h2 style="margin: 0;">⚠️ Alert</h2>
                    </div>
                    
                    <div style="padding: 20px;">
                        <p>Hello <strong>{recipient_name}</strong>,</p>
                        
                        <p><strong>{title}</strong></p>
                        
                        <div style="background: #fef3c7; border-left: 4px solid {alert_color}; padding: 15px; margin: 15px 0; border-radius: 4px;">
                            <p>{details}</p>
                        </div>
                        
                        {f'<p style="color: #dc2626; font-weight: bold;">⚠️ Action Required: Please log in to MedNova ERP to review this alert.</p>' if action_required else ''}
                        
                        <p style="color: #666; font-size: 12px; margin-top: 20px;">
                            This is an automated alert from MedNova ERP.
                        </p>
                    </div>
                </div>
            </body>
        </html>
        """

    @staticmethod
    def welcome_email(
        user_name: str,
        email: str,
        role: str,
        temporary_password: str = ""
    ) -> str:
        """Welcome email for new users"""
        return f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; border: 1px solid #e0e0e0; border-radius: 8px; padding: 20px;">
                    <div style="background: #3b82f6; color: white; padding: 20px; border-radius: 8px 8px 0 0; text-align: center;">
                        <h2 style="margin: 0;">🏥 Welcome to MedNova ERP!</h2>
                    </div>
                    
                    <div style="padding: 20px;">
                        <p>Hello <strong>{user_name}</strong>,</p>
                        
                        <p>Your account has been successfully created in <strong>MedNova ERP</strong>.</p>
                        
                        <div style="background: #f0f9ff; border-left: 4px solid #3b82f6; padding: 15px; margin: 15px 0; border-radius: 4px;">
                            <p><strong>Email:</strong> {email}</p>
                            <p><strong>Role:</strong> {role.replace('_', ' ').title()}</p>
                            {f'<p><strong>Temporary Password:</strong> <code style="background: #e0e7ff; padding: 4px 8px; border-radius: 4px;">{temporary_password}</code></p>' if temporary_password else ''}
                        </div>
                        
                        <p>You can now log in at: <strong>https://mednova.yourdomain.com</strong></p>
                        
                        <p style="color: #666; font-size: 12px; margin-top: 20px;">
                            If you did not request this account, please contact your administrator.
                        </p>
                    </div>
                </div>
            </body>
        </html>
        """

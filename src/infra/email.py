"""Email utility functions for sending emails."""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from src.config import settings


def load_email_template(template_name: str) -> str:
    """Load email template from file."""
    template_path = Path(__file__).parent.parent / "email_templates" / template_name
    with open(template_path, "r", encoding="utf-8") as f:
        return f.read()


def send_email(
    to_email: str,
    subject: str,
    html_body: str,
    text_body: str | None = None,
) -> bool:
    """
    Send email using SMTP.
    
    Args:
        to_email: Recipient email address
        subject: Email subject
        html_body: HTML email body
        text_body: Plain text email body (optional)
    
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        # Create message
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = settings.email_sender
        msg["To"] = to_email
        
        # Add text and HTML parts
        if text_body:
            text_part = MIMEText(text_body, "plain")
            msg.attach(text_part)
        
        html_part = MIMEText(html_body, "html")
        msg.attach(html_part)
        
        # Send email
        with smtplib.SMTP(settings.email_smtp_server, settings.email_smtp_port) as server:
            server.starttls()
            server.login(settings.email_sender, settings.email_app_password)
            server.send_message(msg)
        
        return True
    except Exception as e:
        print(f"Error sending email to {to_email}: {str(e)}")
        return False


def send_invitation_email(
    to_email: str,
    invitation_token: str,
    family_name: str | None = None,
) -> bool:
    """
    Send invitation email with activation link.
    
    Args:
        to_email: Recipient email address
        invitation_token: Invitation token for activation
        family_name: Optional family name to include in email
    
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    # Build activation URL
    activation_url = f"{settings.frontend_url}/invitations/activate/{invitation_token}"
    
    # Load template
    template = load_email_template("invitation.html")
    
    # Replace template variables
    html_body = template.replace("{{ activation_url }}", activation_url)
    if family_name:
        html_body = html_body.replace("{{ family_name }}", family_name)
    else:
        html_body = html_body.replace("{{ family_name }}", "our organization")
    
    # Create plain text version
    text_body = f"""
You have been invited to join {family_name or "our organization"}.

Click the link below to activate your account:
{activation_url}

This invitation will expire in 24 hours.

If you did not request this invitation, please ignore this email.
"""
    
    subject = f"Invitation to join {family_name or 'our organization'}"
    
    return send_email(to_email, subject, html_body, text_body)


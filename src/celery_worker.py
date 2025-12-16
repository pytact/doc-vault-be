"""Celery task definitions."""
from src.celery_app import celery_app
from src.infra.email import send_invitation_email, send_email, load_email_template


@celery_app.task(name="send_welcome_email")
def send_welcome_email(user_email: str, user_name: str):
    """Send welcome email to new user"""
    try:
        template = load_email_template("welcome.html")
        html_body = template.replace("{{ user_name }}", user_name)
        
        text_body = f"""
Welcome {user_name}!

Thank you for joining us. We're excited to have you on board.

If you have any questions, please don't hesitate to reach out.
"""
        
        send_email(
            to_email=user_email,
            subject="Welcome!",
            html_body=html_body,
            text_body=text_body,
        )
    except Exception as e:
        print(f"Error sending welcome email: {str(e)}")
        raise


@celery_app.task(name="send_password_reset_email")
def send_password_reset_email(user_email: str, reset_token: str):
    """Send password reset email"""
    try:
        from src.config import settings
        
        reset_url = f"{settings.frontend_url}/reset-password?token={reset_token}"
        template = load_email_template("reset_password.html")
        html_body = template.replace("{{ reset_url }}", reset_url)
        
        text_body = f"""
Password Reset Request

Click the link below to reset your password:
{reset_url}

This link will expire in 1 hour.

If you did not request this password reset, please ignore this email.
"""
        
        send_email(
            to_email=user_email,
            subject="Password Reset Request",
            html_body=html_body,
            text_body=text_body,
        )
    except Exception as e:
        print(f"Error sending password reset email: {str(e)}")
        raise


@celery_app.task(name="send_invitation_email")
def send_invitation_email_task(
    user_email: str,
    invitation_token: str,
    family_name: str | None = None,
):
    """Send invitation email with activation link"""
    try:
        send_invitation_email(
            to_email=user_email,
            invitation_token=invitation_token,
            family_name=family_name,
        )
    except Exception as e:
        print(f"Error sending invitation email: {str(e)}")
        raise


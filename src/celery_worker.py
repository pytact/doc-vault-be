"""Celery task definitions."""
import asyncio
from src.celery_app import celery_app
from src.config import settings
from src.infra.email import send_invitation_email, send_email, load_email_template
from src.database import AsyncSessionLocal
from src.notification.service import NotificationService


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


@celery_app.task(name="process_expiry_reminders")
def process_expiry_reminders_task():
    """Daily task to process pending reminder schedules and send notifications.
    
    Runs daily at 00:00 UTC to:
    - Query pending ReminderSchedule records where send_at <= NOW()
    - Create InAppNotification records
    - Send email notifications
    - Mark schedules as sent
    
    Returns:
        dict: Processing statistics
    """
    async def _process_reminders():
        """Async helper to process reminders with database session."""
        async with AsyncSessionLocal() as session:
            notification_service = NotificationService(session)
            stats = await notification_service.process_pending_reminders()
            return stats
    
    try:
        # Run async function in Celery task
        stats = asyncio.run(_process_reminders())
        
        # Log statistics
        print(f"Expiry reminders processed: {stats}")
        print(f"  - Processed: {stats.get('processed', 0)}")
        print(f"  - Notifications created: {stats.get('created_notifications', 0)}")
        print(f"  - Emails sent: {stats.get('sent_emails', 0)}")
        print(f"  - Errors: {stats.get('errors', 0)}")
        print(f"  - Skipped: {stats.get('skipped', 0)}")
        
        return stats
    except Exception as e:
        print(f"Error processing expiry reminders: {str(e)}")
        raise


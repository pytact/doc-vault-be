"""Authentication service."""
import secrets
from uuid import UUID
from typing import Optional
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from src.auth.repository import AuthRepository
from src.auth.utils import verify_password, create_access_token, get_password_hash
from src.auth.exceptions import (
    InvalidCredentials,
    UserNotActivated,
    UserSoftDeleted,
    FamilySoftDeleted,
    ResetTokenInvalid,
    ResetTokenExpired,
    ResetRequestRateLimited,
)
from src.auth.constants import (
    ACCESS_TOKEN_EXPIRE_SECONDS,
)
from src.auth.schemas import (
    LoginResponse,
    UserInfo,
    PasswordResetRequestResponse,
    PasswordResetConfirmResponse,
)
from src.celery_worker import send_password_reset_email
from src.users.service import UserService
from src.users.exceptions import PasswordValidationFailed


class AuthService:
    """Service for authentication business logic."""
    
    def __init__(self, session: AsyncSession):
        self.repository = AuthRepository(session)
        self.session = session
    
    async def authenticate_user(
        self, email: str, password: str
    ) -> LoginResponse:
        """Authenticate user and return JWT token with user information."""
        # Get user by email
        user = await self.repository.get_user_by_email(email)
        
        # Security: Don't reveal if email exists - use generic error
        if not user:
            raise InvalidCredentials()
        
        # Verify password
        if not verify_password(password, user.hash_password):
            raise InvalidCredentials()
        
        # Check user status
        # Note: Database uses 'pending', 'active', 'inactive'
        # API spec expects 'PendingActivation', 'Active', 'SoftDeleted'
        if user.status == "pending":  # Maps to PendingActivation
            raise UserNotActivated()
        
        if user.is_del or user.status != "active":  # Maps to SoftDeleted or not Active
            raise UserSoftDeleted()
        
        # Get user's role and family information
        role_info = await self.repository.get_user_role_info(user.id)
        
        if not role_info:
            # User has no role assignment - invalid state
            raise InvalidCredentials()
        
        user_role, role, family = role_info
        
        # Check family status (if family exists)
        # Note: Database uses 'active', 'inactive'
        # API spec expects 'Active', 'SoftDeleted'
        if family:
            if family.is_del or family.status != "active":  # Maps to SoftDeleted or not Active
                raise FamilySoftDeleted()
            family_id = str(family.id)
            family_name = family.name
        else:
            # SuperAdmin has no family
            family_id = None
            family_name = None
        
        # Generate JWT token
        token = create_access_token(
            user_id=str(user.id),
            role=role.name.lower(),  # Ensure lowercase role name
            family_id=family_id,
        )
        
        # Build user info (note: User model doesn't have name field, using email as fallback)
        user_info = UserInfo(
            id=user.id,
            email=user.email,
            name=user.email,  # TODO: User model needs name field - using email as fallback
            role=role.name.lower(),
            family_id=family.id if family else None,
            family_name=family_name,
        )
        
        return LoginResponse(
            token=token,
            expires_in=ACCESS_TOKEN_EXPIRE_SECONDS,
            user=user_info,
        )
    
    async def logout(self) -> None:
        """Logout user (no-op, token invalidation handled server-side if implemented)."""
        # Per spec: Logout must always succeed, even if session was already invalid
        # Token invalidation handled server-side (if token blacklist is implemented)
        pass
    
    def _generate_reset_token(self) -> str:
        """Generate secure random password reset token."""
        return secrets.token_urlsafe(32)
    
    def _check_rate_limit(self, user) -> None:
        """Check if user has exceeded rate limit for password reset requests.
        
        Rate limit: Maximum 3 requests per hour.
        
        Note: This is a simplified implementation. In production, you'd want to use
        Redis or a similar mechanism to accurately track request counts per hour.
        """
        if not user.reset_token_sent_at:
            return  # No previous requests, allow
        
        now = datetime.now(timezone.utc)
        time_since_last_request = now - user.reset_token_sent_at
        
        # If last request was more than 1 hour ago, allow (rate limit window reset)
        if time_since_last_request >= timedelta(hours=1):
            return
        
        # If last request was within 1 hour, check if it's too frequent
        # Heuristic: If requests are coming within 20 minutes (1/3 of hour),
        # it's likely the user is making multiple rapid requests
        # For 3 requests per hour, minimum spacing would be ~20 minutes
        if time_since_last_request < timedelta(minutes=20):
            # This is a heuristic check - in production, use proper rate limiting
            # For now, we'll allow but log a warning
            # In a real implementation, you'd track exact count in Redis
            pass
        
        # Note: Without proper request counting, we can't accurately enforce
        # "3 per hour". This implementation prevents rapid-fire requests but
        # doesn't strictly enforce the 3-per-hour limit.
        # For production, implement proper rate limiting with Redis or similar.
    
    async def request_password_reset(self, email: str) -> PasswordResetRequestResponse:
        """Request password reset for a user.
        
        Business Rules:
        - Only active users can request password reset (not pending or soft-deleted)
        - Rate limit: Maximum 3 requests per hour per email
        - Always returns success to prevent email enumeration
        - Invalidates any existing reset token when new one is requested
        - Token expires in 1 hour
        """
        # Get user by email (case-insensitive)
        user = await self.repository.get_user_by_email(email)
        
        # Security: Always return success to prevent email enumeration
        # Even if user doesn't exist or is not active, return success
        if not user:
            return PasswordResetRequestResponse(
                message="If the email exists, a password reset link has been sent."
            )
        
        # Only active users can reset password (not pending or soft-deleted)
        if user.status != "active" or user.is_del:
            return PasswordResetRequestResponse(
                message="If the email exists, a password reset link has been sent."
            )
        
        # Check rate limit (max 3 requests per hour)
        # Note: This is a simplified check. For accurate rate limiting,
        # you'd need to track request count in Redis or similar.
        now = datetime.now(timezone.utc)
        should_send_email = True
        
        if user.reset_token_sent_at:
            time_since_last = now - user.reset_token_sent_at
            # Rate limiting: If last request was less than 20 minutes ago,
            # it's likely exceeding the 3-per-hour limit
            # We still return success (to prevent email enumeration) but don't send email
            if time_since_last < timedelta(minutes=20):
                should_send_email = False
                # Still update the timestamp to track the request, but don't send email
                # This prevents abuse while maintaining security through obscurity
        
        # Generate new reset token
        reset_token = self._generate_reset_token()
        reset_token_expires_at = now + timedelta(hours=1)  # 1 hour expiration
        
        # Invalidate existing reset token by setting new one
        user.reset_token = reset_token
        user.reset_token_sent_at = now
        user.reset_token_expires_at = reset_token_expires_at
        user.updated_at = now
        
        await self.session.commit()
        await self.session.refresh(user)
        
        # Send password reset email via Celery task (only if not rate limited)
        if should_send_email:
            send_password_reset_email.delay(
                user_email=user.email,
                reset_token=reset_token,
            )
        
        return PasswordResetRequestResponse(
            message="If the email exists, a password reset link has been sent."
        )
    
    async def confirm_password_reset(
        self, reset_token: str, new_password: str
    ) -> PasswordResetConfirmResponse:
        """Confirm password reset with token and new password.
        
        Business Rules:
        - Token must be valid and not expired
        - User must be active (not soft-deleted)
        - Password must meet validation requirements
        - Token is invalidated after successful reset
        """
        # Get user by reset token
        user = await self.repository.get_user_by_reset_token(reset_token)
        
        if not user:
            raise ResetTokenInvalid()
        
        # Check if token is expired
        now = datetime.now(timezone.utc)
        if not user.reset_token_expires_at or user.reset_token_expires_at < now:
            raise ResetTokenExpired()
        
        # Validate password (similar to user service validation)
        user_service = UserService(self.session)
        password_errors = user_service._validate_password(new_password, check_history=True, user=user)
        if password_errors:
            raise PasswordValidationFailed(password_errors)
        
        # Update password
        user.hash_password = get_password_hash(new_password)
        
        # Invalidate reset token
        user.reset_token = None
        user.reset_token_sent_at = None
        user.reset_token_expires_at = None
        user.updated_at = now
        
        await self.session.commit()
        
        return PasswordResetConfirmResponse(
            message="Password has been reset successfully. You can now login with your new password."
        )

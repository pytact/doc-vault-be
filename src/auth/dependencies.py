"""Authentication dependencies."""
import logging
from uuid import UUID
from typing import Optional
from fastapi import Depends, status
from fastapi.security import OAuth2PasswordBearer
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import get_session
from src.auth.utils import decode_token
from src.auth.exceptions import InvalidToken, TokenExpired
from src.auth.repository import AuthRepository
from src.users.models import User

logger = logging.getLogger(__name__)


# OAuth2 scheme for token extraction
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/v1/auth/token",  # OAuth2-compatible token endpoint
    auto_error=False,  # Don't auto-raise if token missing
)


async def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_session),
) -> User:
    """Get current authenticated user from JWT token."""
    # CRITICAL: Check if token is None before decoding
    if not token:
        logger.error("get_current_user: Token is None")
        raise InvalidToken()
    
    # Decode token
    payload = decode_token(token)
    if not payload:
        logger.error("get_current_user: Failed to decode token")
        raise InvalidToken()
    
    # Log the full payload for debugging
    logger.info(f"get_current_user: Token payload = {payload}")
    
    # Validate required claims
    user_id = payload.get("sub")
    role = payload.get("role")
    family_id = payload.get("family_id")
    
    logger.info(f"get_current_user: Token decoded - user_id={user_id}, role={role}, family_id={family_id}")
    
    if not user_id or not role:
        logger.error(f"get_current_user: Missing required claims - user_id={user_id}, role={role}")
        raise InvalidToken()
    
    # Get user from database
    repository = AuthRepository(session)
    try:
        user_uuid = UUID(user_id)
        user = await repository.get_user_by_id(user_uuid)
    except (ValueError, TypeError) as e:
        logger.error(f"get_current_user: Invalid UUID format - user_id={user_id}, error={e}")
        raise InvalidToken()
    
    if not user:
        # Log for debugging: token claims vs what was found
        error_msg = f"get_current_user: User not found in database. Token claims: user_id={user_id}, role={role}, family_id={family_id}"
        logger.error(error_msg)
        raise InvalidToken()
    
    # CRITICAL: Verify the user ID from database matches the token user ID
    token_user_id_str = str(user_id)
    db_user_id_str = str(user.id)
    
    if db_user_id_str != token_user_id_str:
        error_msg = (
            f"get_current_user: User ID mismatch! Token user_id={token_user_id_str}, "
            f"but database returned user_id={db_user_id_str}, email={user.email}"
        )
        logger.error(error_msg)
        raise InvalidToken()
    
    # Verify user is still active
    if user.is_del or user.status != "active":
        # Log for debugging: user found but not active
        logger.error(
            f"get_current_user: User found but not active. user_id={user.id}, email={user.email}, "
            f"is_del={user.is_del}, status={user.status}"
        )
        raise InvalidToken()
    
    # Log for debugging: verify we're returning the correct user
    logger.info(
        f"get_current_user: Successfully returning user_id={user.id}, email={user.email} (token user_id={token_user_id_str})"
    )
    
    return user


async def get_current_user_optional(
    token: Optional[str] = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_session),
) -> Optional[User]:
    """Get current user if token is provided, otherwise return None."""
    if not token:
        return None
    
    try:
        return await get_current_user(token=token, session=session)
    except (InvalidToken, TokenExpired):
        return None


# API Dependency Pattern (RULE 8.6.7)
class AuthApiDep:
    """API dependency for authentication endpoints."""
    
    def __init__(self, session: AsyncSession):
        from src.auth.service import AuthService
        self.service = AuthService(session)
        self.session = session
    
    async def login(self, email: str, password: str):
        """Login user and return JWT token."""
        return await self.service.authenticate_user(email, password)
    
    async def logout(self):
        """Logout user."""
        return await self.service.logout()
    
    async def request_password_reset(self, email: str):
        """Request password reset."""
        return await self.service.request_password_reset(email)
    
    async def confirm_password_reset(self, reset_token: str, new_password: str):
        """Confirm password reset."""
        return await self.service.confirm_password_reset(reset_token, new_password)


def get_auth_api(session: AsyncSession = Depends(get_session)) -> AuthApiDep:
    """Dependency function to get AuthApiDep instance."""
    return AuthApiDep(session)



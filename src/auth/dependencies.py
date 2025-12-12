"""Authentication dependencies."""
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
        raise InvalidToken()
    
    # Decode token
    payload = decode_token(token)
    if not payload:
        raise InvalidToken()
    
    # Validate required claims
    user_id = payload.get("sub")
    role = payload.get("role")
    family_id = payload.get("family_id")
    
    if not user_id or not role:
        raise InvalidToken()
    
    # Get user from database
    repository = AuthRepository(session)
    user = await repository.get_user_by_id(UUID(user_id))
    
    if not user:
        raise InvalidToken()
    
    # Verify user is still active
    if user.is_del or user.status != "active":
        raise InvalidToken()
    
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


def get_auth_api(session: AsyncSession = Depends(get_session)) -> AuthApiDep:
    """Dependency function to get AuthApiDep instance."""
    return AuthApiDep(session)



"""Authentication service."""
from uuid import UUID
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from src.auth.repository import AuthRepository
from src.auth.utils import verify_password, create_access_token
from src.auth.exceptions import (
    InvalidCredentials,
    UserNotActivated,
    UserSoftDeleted,
    FamilySoftDeleted,
)
from src.auth.constants import (
    ACCESS_TOKEN_EXPIRE_SECONDS,
)
from src.auth.schemas import LoginResponse, UserInfo


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

"""Invitations router."""
from uuid import UUID
from typing import Optional
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import get_session
from src.schemas import StandardResponse
from src.users.schemas import (
    InvitationCreate,
    InvitationCreateResponse,
    InvitationValidationResponse,
    InvitationActivateRequest,
    InvitationActivateResponse,
    InvitationResendRequest,
    InvitationResendResponse,
)
from src.users.dependencies import (
    get_user_api,
    UserApiDep,
)
from src.users.documentations.user_api_doc import UserApiDocs
from src.auth.dependencies import get_current_user, oauth2_scheme
from src.auth.utils import decode_token
from src.auth.exceptions import InvalidToken
from src.exceptions import ForbiddenError
from src.users.models import User


# Router for invitation creation (requires auth)
invite_router = APIRouter(
    prefix="/invite",
    tags=["Invitations"],
)


# Router for public invitation endpoints (no auth)
invitations_router = APIRouter(
    prefix="/invitations",
    tags=["Invitations"],
)


async def verify_invitation_authorization(
    data: InvitationCreate,
    token: Optional[str],
    session: AsyncSession,
) -> tuple[User, bool]:
    """Verify authorization for invitation creation.
    
    Returns:
        tuple: (current_user, is_superadmin)
    """
    if not token:
        raise InvalidToken()
    
    # Decode token to get role and family_id
    payload = decode_token(token)
    if not payload:
        raise InvalidToken()
    
    role = payload.get("role", "").lower()
    token_family_id = payload.get("family_id")
    
    # Get current user
    current_user = await get_current_user(token=token, session=session)
    
    # SuperAdmin: Can set any family_id or null (for SuperAdmin user creation)
    if role == "superadmin" and token_family_id is None:
        return (current_user, True)
    
    # FamilyAdmin: Can only set their own family_id (from token), cannot set null
    if role == "familyadmin" and token_family_id:
        # If family_id is provided in request, it must match token's family_id
        if data.family_id is None:
            raise ForbiddenError(
                message="FamilyAdmin cannot create SuperAdmin users. family_id is required.",
                error_code="INSUFFICIENT_PERMISSIONS",
                details=[{"field": "family_id", "issue": "FamilyAdmin must provide their own family_id"}],
            )
        
        if str(data.family_id) != str(token_family_id):
            raise ForbiddenError(
                message="FamilyAdmin can only invite users to their own family.",
                error_code="INSUFFICIENT_PERMISSIONS",
                details=[{"field": "family_id", "issue": "FamilyAdmin can only use their own family_id"}],
            )
        
        return (current_user, False)
    
    # Member cannot invite (403)
    raise ForbiddenError(
        message="Insufficient permissions. SuperAdmin or FamilyAdmin access required.",
        error_code="INSUFFICIENT_PERMISSIONS",
        details=[{"field": "role", "issue": "SuperAdmin or FamilyAdmin access required"}],
    )


@invite_router.post(
    "",
    response_model=StandardResponse[InvitationCreateResponse],
    status_code=status.HTTP_201_CREATED,
    summary=UserApiDocs.create_invitation["summary"],
    description=UserApiDocs.create_invitation["description"],
)
async def create_invitation(
    data: InvitationCreate,
    api: UserApiDep = Depends(get_user_api),
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_session),
) -> StandardResponse[InvitationCreateResponse]:
    """Create user invitation."""
    # Verify authorization (SuperAdmin or FamilyAdmin)
    current_user, is_superadmin = await verify_invitation_authorization(data, token, session)
    
    # Determine family_id: use from body, or for SuperAdmin creating SuperAdmin user, use None
    family_id = data.family_id
    
    result = await api.create_invitation(
        family_id, data, current_user.id, is_superadmin
    )
    return StandardResponse(
        data=result,
        message="Invitation sent successfully",
    )


@invitations_router.get(
    "/{token}",
    response_model=StandardResponse[InvitationValidationResponse],
    status_code=status.HTTP_200_OK,
    summary=UserApiDocs.validate_invitation["summary"],
    description=UserApiDocs.validate_invitation["description"],
)
async def validate_invitation(
    token: str,
    api: UserApiDep = Depends(get_user_api),
) -> StandardResponse[InvitationValidationResponse]:
    """Validate invitation token (public endpoint)."""
    result = await api.validate_invitation(token)
    return StandardResponse(
        data=result,
        message="Invitation token is valid" if result.is_token_valid else "Invitation token is invalid or expired",
    )


@invitations_router.post(
    "/activate/{token}",
    response_model=StandardResponse[InvitationActivateResponse],
    status_code=status.HTTP_200_OK,
    summary=UserApiDocs.activate_invitation["summary"],
    description=UserApiDocs.activate_invitation["description"],
)
async def activate_invitation(
    token: str,
    data: InvitationActivateRequest,
    api: UserApiDep = Depends(get_user_api),
) -> StandardResponse[InvitationActivateResponse]:
    """Activate user account with password (public endpoint)."""
    result = await api.activate_account(token, data)
    return StandardResponse(
        data=result,
        message="Account activated successfully",
    )


async def verify_resend_authorization(
    user_id: UUID,
    token: Optional[str],
    session: AsyncSession,
) -> tuple[User, bool, Optional[UUID]]:
    """Verify authorization for resending invitation.
    
    Returns:
        tuple: (current_user, is_superadmin, current_user_family_id)
    """
    if not token:
        raise InvalidToken()
    
    # Decode token to get role and family_id
    payload = decode_token(token)
    if not payload:
        raise InvalidToken()
    
    role = payload.get("role", "").lower()
    token_family_id = payload.get("family_id")
    
    # Get current user
    current_user = await get_current_user(token=token, session=session)
    
    # SuperAdmin: Can resend for any user
    if role == "superadmin" and token_family_id is None:
        return (current_user, True, None)
    
    # FamilyAdmin: Can only resend for users in their own family
    if role == "familyadmin" and token_family_id:
        return (current_user, False, UUID(token_family_id))
    
    # Member cannot resend (403)
    raise ForbiddenError(
        message="Insufficient permissions. SuperAdmin or FamilyAdmin access required.",
        error_code="INSUFFICIENT_PERMISSIONS",
        details=[{"field": "role", "issue": "SuperAdmin or FamilyAdmin access required"}],
    )


@invite_router.post(
    "/resend",
    response_model=StandardResponse[InvitationResendResponse],
    status_code=status.HTTP_200_OK,
    summary=UserApiDocs.resend_invitation["summary"],
    description=UserApiDocs.resend_invitation["description"],
)
async def resend_invitation(
    data: InvitationResendRequest,
    api: UserApiDep = Depends(get_user_api),
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_session),
) -> StandardResponse[InvitationResendResponse]:
    """Resend invitation email to a user."""
    # Verify authorization (SuperAdmin or FamilyAdmin)
    current_user, is_superadmin, current_user_family_id = await verify_resend_authorization(
        data.user_id, token, session
    )
    
    result = await api.resend_invitation(
        data.user_id, current_user.id, is_superadmin, current_user_family_id
    )
    return StandardResponse(
        data=result,
        message="Invitation resent successfully",
    )


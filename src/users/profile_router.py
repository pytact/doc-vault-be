"""Profile management router."""
from uuid import UUID
from typing import Optional
from fastapi import APIRouter, Depends, status, Header, Response
from fastapi.responses import Response as FastAPIResponse
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import get_session
from src.schemas import StandardResponse
from src.users.schemas import (
    UserProfileRead,
    UserProfileUpdate,
    PasswordChangeRequest,
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


router = APIRouter(
    prefix="/users",
    tags=["Profile Management"],
)


async def verify_profile_access(
    user_id: UUID,
    token: Optional[str] = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_session),
) -> User:
    """Verify user can access the profile.
    
    Authorization rules:
    - Users can access their own profile (user_id matches JWT sub)
    - SuperAdmin can access any user's profile
    - FamilyAdmin can access users in their own family only
    - Member can only access their own profile
    """
    if not token:
        raise InvalidToken()
    
    # Decode token to get role and family_id
    payload = decode_token(token)
    if not payload:
        raise InvalidToken()
    
    current_user_id = payload.get("sub")
    role = payload.get("role", "").lower()
    token_family_id = payload.get("family_id")
    
    if not current_user_id:
        raise InvalidToken()
    
    # Get current user
    current_user = await get_current_user(token=token, session=session)
    
    # Users can access their own profile
    if str(user_id) == str(current_user_id):
        return current_user
    
    # SuperAdmin can access any user's profile
    if role == "superadmin" and token_family_id is None:
        return current_user
    
    # FamilyAdmin and Member: need to check if target user is in same family
    if token_family_id:
        # Get target user's family
        from src.users.repository import UserRepository
        user_repo = UserRepository(session)
        role_info = await user_repo.get_user_role_info(user_id)
        
        if role_info:
            user_role, _, _ = role_info
            if user_role and str(user_role.family_id) == str(token_family_id):
                # FamilyAdmin can access users in their own family
                if role == "familyadmin":
                    return current_user
                # Member can only access their own profile (already checked above)
        
        raise ForbiddenError(
            message="Insufficient permissions. You can only access your own profile or users in your family (FamilyAdmin only).",
            error_code="INSUFFICIENT_PERMISSIONS",
            details=[{"field": "user_id", "issue": "You cannot access this user's profile"}],
        )
    
    raise ForbiddenError(
        message="Insufficient permissions. You can only access your own profile.",
        error_code="INSUFFICIENT_PERMISSIONS",
        details=[{"field": "user_id", "issue": "You cannot access this user's profile"}],
    )


@router.get(
    "/{user_id}",
    response_model=StandardResponse[UserProfileRead],
    status_code=status.HTTP_200_OK,
    summary=UserApiDocs.get_profile["summary"],
    description=UserApiDocs.get_profile["description"],
)
async def get_profile(
    user_id: UUID,
    current_user: User = Depends(verify_profile_access),
    api: UserApiDep = Depends(get_user_api),
    if_none_match: str | None = Header(None, alias="If-None-Match"),
    response: Response = None,
) -> StandardResponse[UserProfileRead] | FastAPIResponse:
    """Get user profile by user_id."""
    # Pass If-None-Match to service (service handles all ETag logic)
    service_response = await api.get_current_user_profile(
        user_id, if_none_match=if_none_match
    )
    
    # Router only sets headers and returns response (no business logic, no conditionals)
    for key, value in service_response.headers.items():
        response.headers[key] = value
    
    # Router mechanically returns response based on service response_type (no business logic)
    if service_response.response_type == "fastapi":
        return service_response.to_fastapi_response()
    
    return StandardResponse(
        data=service_response.data,
        message="Profile retrieved successfully",
    )


@router.patch(
    "/{user_id}",
    response_model=StandardResponse[UserProfileRead],
    status_code=status.HTTP_200_OK,
    summary=UserApiDocs.update_profile["summary"],
    description=UserApiDocs.update_profile["description"],
)
async def update_profile(
    user_id: UUID,
    data: UserProfileUpdate,
    current_user: User = Depends(verify_profile_access),
    api: UserApiDep = Depends(get_user_api),
    if_match: str | None = Header(None, alias="If-Match"),
    response: Response = None,
) -> StandardResponse[UserProfileRead]:
    """Update user profile by user_id."""
    # Pass If-Match to service (service handles ETag validation)
    result = await api.update_current_user_profile(
        user_id, data, if_match=if_match
    )
    
    # Router only sets headers from service result (no business logic)
    if hasattr(result, '_etag'):
        response.headers["ETag"] = result._etag
        response.headers["Last-Modified"] = result._last_modified
    
    return StandardResponse(
        data=result,
        message="Profile updated successfully",
    )




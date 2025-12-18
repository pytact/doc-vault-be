"""User router."""
from uuid import UUID
from fastapi import APIRouter, Depends, status, Header, Response
from fastapi.responses import Response as FastAPIResponse
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import get_session
from src.schemas import StandardResponse
from src.users.schemas import (
    UserListQuery,
    UserListRead,
    UserDetailRead,
    UserPaginatedResponse,
)
from src.users.dependencies import (
    get_current_admin,
    get_user_api,
    UserApiDep,
)
from src.users.documentations.user_api_doc import UserApiDocs
from src.auth.dependencies import oauth2_scheme


router = APIRouter(
    prefix="/families/{family_id}/users",
    tags=["Users"],
)


@router.get(
    "",
    response_model=StandardResponse[UserPaginatedResponse],
    status_code=status.HTTP_200_OK,
    summary=UserApiDocs.list["summary"],
    description=UserApiDocs.list["description"],
)
async def list_users(
    family_id: UUID,
    query: UserListQuery = Depends(UserListQuery),
    api: UserApiDep = Depends(get_user_api),
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_session),
) -> StandardResponse[UserPaginatedResponse]:
    """List users within a family."""
    # Verify authorization (SuperAdmin or FamilyAdmin)
    current_user, current_user_role, current_user_is_superadmin = await get_current_admin(
        family_id, token, session
    )
    
    result = await api.list_users(family_id, query)
    return StandardResponse(
        data=result,
        message="Users retrieved successfully",
    )


@router.get(
    "/{user_id}",
    response_model=StandardResponse[UserDetailRead],
    status_code=status.HTTP_200_OK,
    summary=UserApiDocs.get["summary"],
    description=UserApiDocs.get["description"],
)
async def get_user(
    family_id: UUID,
    user_id: UUID,
    api: UserApiDep = Depends(get_user_api),
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_session),
    if_none_match: str | None = Header(None, alias="If-None-Match"),
    response: Response = None,
) -> StandardResponse[UserDetailRead] | FastAPIResponse:
    """Get user details within a family."""
    # Verify authorization (SuperAdmin or FamilyAdmin)
    current_user, current_user_role, current_user_is_superadmin = await get_current_admin(
        family_id, token, session
    )
    
    # Service handles all business logic including ETag logic
    service_response = await api.get_user_by_id(
        family_id, user_id, current_user_role, current_user_is_superadmin,
        if_none_match=if_none_match
    )
    
    # Router mechanically returns response based on service response_type (no business logic)
    if service_response.response_type == "fastapi":
        return service_response.to_fastapi_response()
    
    # Router only returns the formatted response (no header manipulation)
    return service_response.to_standard_response("User retrieved successfully")


@router.delete(
    "/{user_id}",
    response_model=StandardResponse[UserDetailRead],
    status_code=status.HTTP_200_OK,
    summary=UserApiDocs.soft_delete["summary"],
    description=UserApiDocs.soft_delete["description"],
)
async def soft_delete_user(
    family_id: UUID,
    user_id: UUID,
    api: UserApiDep = Depends(get_user_api),
    if_match: str | None = Header(None, alias="If-Match"),
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_session),
    response: Response = None,
) -> StandardResponse[UserDetailRead]:
    """Soft delete user."""
    # Verify authorization (SuperAdmin or FamilyAdmin)
    current_user, current_user_role, current_user_is_superadmin = await get_current_admin(
        family_id, token, session
    )
    
    # Service handles all business logic including ETag validation and headers
    service_response = await api.soft_delete_user(
        family_id, user_id, current_user.id,
        current_user_role, current_user_is_superadmin,
        if_match=if_match
    )
    
    # Router only returns the formatted response (no header manipulation)
    return service_response.to_standard_response("User soft-deleted successfully")

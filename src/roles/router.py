"""Role router."""
from uuid import UUID
from fastapi import APIRouter, Depends, status, Header, Response
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import get_session
from src.schemas import StandardResponse
from src.roles.schemas import (
    RoleListResponse,
    UserRoleUpdateRequest,
    UserRoleUpdateResponse,
)
from src.roles.dependencies import (
    get_role_api,
    RoleApiDep,
)
from src.roles.documentations.role_api_doc import RoleApiDocs
from src.auth.dependencies import get_current_user, oauth2_scheme
from src.users.models import User
from src.users.dependencies import get_current_admin


router = APIRouter(
    prefix="/roles",
    tags=["Roles"],
)


@router.get(
    "",
    response_model=StandardResponse[RoleListResponse],
    status_code=status.HTTP_200_OK,
    summary=RoleApiDocs.list["summary"],
    description=RoleApiDocs.list["description"],
)
async def list_roles(
    current_user: User = Depends(get_current_user),
    api: RoleApiDep = Depends(get_role_api),
) -> StandardResponse[RoleListResponse]:
    """List all available roles."""
    result = await api.list_roles()
    return StandardResponse(
        data=result,
        message="Roles retrieved successfully",
    )


@router.patch(
    "/families/{family_id}/users/{user_id}/",
    response_model=StandardResponse[UserRoleUpdateResponse],
    status_code=status.HTTP_200_OK,
    summary=RoleApiDocs.update_user_roles["summary"],
    description=RoleApiDocs.update_user_roles["description"],
)
async def update_user_roles(
    family_id: UUID,
    user_id: UUID,
    data: UserRoleUpdateRequest,
    api: RoleApiDep = Depends(get_role_api),
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_session),
    if_match: str | None = Header(None, alias="If-Match"),
    response: Response = None,
) -> StandardResponse[UserRoleUpdateResponse]:
    """Update user roles within a family."""
    # Verify authorization (SuperAdmin or FamilyAdmin)
    current_user, current_user_role, current_user_is_superadmin = await get_current_admin(
        family_id, token, session
    )
    
    # Pass If-Match to service (service handles ETag validation)
    result = await api.update_user_roles(
        family_id, user_id, data, current_user.id, current_user_is_superadmin,
        if_match=if_match
    )
    
    # Router only sets headers from service result (no business logic)
    # Note: Service doesn't attach ETag for this endpoint per spec, but we can set it if needed
    
    return StandardResponse(
        data=result,
        message="User roles updated successfully",
    )

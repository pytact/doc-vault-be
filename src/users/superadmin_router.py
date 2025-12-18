"""SuperAdmin user management router."""
from uuid import UUID
from typing import Optional
from fastapi import APIRouter, Depends, status, Header, Response
from src.schemas import StandardResponse
from src.users.schemas import (
    UserReassignRequest,
    BulkDeleteRequest,
    BulkDeleteResponse,
    UserDetailRead,
)
from src.users.dependencies import (
    get_user_api,
    UserApiDep,
)
from src.families.dependencies import get_current_superadmin
from src.users.documentations.user_api_doc import UserApiDocs
from src.users.constants import (
    SUCCESS_USER_REASSIGNED,
    SUCCESS_USER_REACTIVATED,
    SUCCESS_BULK_DELETE_COMPLETED,
)
from src.users.models import User
from src.families.dependencies import get_current_superadmin as get_superadmin_user


router = APIRouter(
    prefix="/users",
    tags=["Users"],
)


@router.post(
    "/{user_id}/reassign",
    response_model=StandardResponse[UserDetailRead],
    status_code=status.HTTP_200_OK,
    summary=UserApiDocs.reassign_user["summary"],
    description=UserApiDocs.reassign_user["description"],
)
async def reassign_user(
    user_id: UUID,
    data: UserReassignRequest,
    current_user: User = Depends(get_current_superadmin),
    api: UserApiDep = Depends(get_user_api),
    if_match: str | None = Header(None, alias="If-Match"),
    response: Response = None,
) -> StandardResponse[UserDetailRead]:
    """Reassign user to different family."""
    # Delegate to service (business logic in service)
    result = await api.reassign_user(
        user_id, data, current_user.id, if_match=if_match
    )
    
    # Router sets headers from service result (no business logic)
    if hasattr(result, '_etag'):
        response.headers["ETag"] = result._etag
    if hasattr(result, '_last_modified'):
        response.headers["Last-Modified"] = result._last_modified
    
    return StandardResponse(
        data=result,
        message=SUCCESS_USER_REASSIGNED,
    )


@router.post(
    "/{user_id}/reactivate",
    response_model=StandardResponse[UserDetailRead],
    status_code=status.HTTP_200_OK,
    summary=UserApiDocs.reactivate_user["summary"],
    description=UserApiDocs.reactivate_user["description"],
)
async def reactivate_user(
    user_id: UUID,
    current_user: User = Depends(get_current_superadmin),
    api: UserApiDep = Depends(get_user_api),
    if_match: str | None = Header(None, alias="If-Match"),
    response: Response = None,
) -> StandardResponse[UserDetailRead]:
    """Reactivate soft-deleted user."""
    # Delegate to service (business logic in service)
    result = await api.reactivate_user(
        user_id, current_user.id, if_match=if_match
    )
    
    # Router sets headers from service result (no business logic)
    if hasattr(result, '_etag'):
        response.headers["ETag"] = result._etag
    if hasattr(result, '_last_modified'):
        response.headers["Last-Modified"] = result._last_modified
    
    return StandardResponse(
        data=result,
        message=SUCCESS_USER_REACTIVATED,
    )


@router.post(
    "/bulk-delete",
    response_model=StandardResponse[BulkDeleteResponse],
    status_code=status.HTTP_200_OK,
    summary=UserApiDocs.bulk_delete_users["summary"],
    description=UserApiDocs.bulk_delete_users["description"],
)
async def bulk_delete_users(
    data: BulkDeleteRequest,
    current_user: User = Depends(get_current_superadmin),
    api: UserApiDep = Depends(get_user_api),
) -> StandardResponse[BulkDeleteResponse]:
    """Bulk delete multiple users."""
    # Delegate to service (business logic in service)
    result = await api.bulk_delete_users(data, current_user.id)
    
    return StandardResponse(
        data=result,
        message=SUCCESS_BULK_DELETE_COMPLETED,
    )


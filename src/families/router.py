"""Family router."""
from uuid import UUID
from fastapi import APIRouter, Depends, status, Header, Response
from fastapi.responses import Response as FastAPIResponse
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import get_session
from src.schemas import StandardResponse
from src.families.schemas import (
    FamilyCreate,
    FamilyUpdate,
    FamilyRead,
    FamilyListQuery,
    FamilyPaginatedResponse,
)
from src.families.dependencies import (
    get_current_superadmin,
    get_family_api,
    FamilyApiDep,
    verify_family_access,
)
from src.families.documentations.family_api_doc import FamilyApiDocs
from src.users.models import User
from src.auth.dependencies import oauth2_scheme


router = APIRouter(
    prefix="/families",
    tags=["Families"],
)


@router.get(
    "",
    response_model=StandardResponse[FamilyPaginatedResponse],
    status_code=status.HTTP_200_OK,
    summary=FamilyApiDocs.list["summary"],
    description=FamilyApiDocs.list["description"],
)
async def list_families(
    query: FamilyListQuery = Depends(FamilyListQuery),
    current_user: User = Depends(get_current_superadmin),
    api: FamilyApiDep = Depends(get_family_api),
) -> StandardResponse[FamilyPaginatedResponse]:
    """List all families with pagination and filtering."""
    result = await api.list_families(query)
    return StandardResponse(
        data=result,
        message="Families retrieved successfully",
    )


@router.post(
    "",
    response_model=StandardResponse[FamilyRead],
    status_code=status.HTTP_201_CREATED,
    summary=FamilyApiDocs.create["summary"],
    description=FamilyApiDocs.create["description"],
)
async def create_family(
    data: FamilyCreate,
    current_user: User = Depends(get_current_superadmin),
    api: FamilyApiDep = Depends(get_family_api),
) -> StandardResponse[FamilyRead]:
    """Create a new family."""
    result = await api.create_family(data, current_user.id)
    return StandardResponse(
        data=result,
        message="Family created successfully",
    )


@router.get(
    "/{family_id}",
    response_model=StandardResponse[FamilyRead],
    status_code=status.HTTP_200_OK,
    summary=FamilyApiDocs.get["summary"],
    description=FamilyApiDocs.get["description"],
)
async def get_family(
    family_id: UUID,
    api: FamilyApiDep = Depends(get_family_api),
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_session),
    if_none_match: str | None = Header(None, alias="If-None-Match"),
    response: Response = None,
) -> StandardResponse[FamilyRead] | FastAPIResponse:
    """Get family details."""
    # Verify authorization (SuperAdmin or member of family)
    current_user = await verify_family_access(family_id, token=token, session=session)
    
    # Pass If-None-Match to service (service handles all ETag logic)
    service_response = await api.get_family_by_id(family_id, if_none_match=if_none_match)
    
    # Router only sets headers and returns response (no business logic, no conditionals)
    for key, value in service_response.headers.items():
        response.headers[key] = value
    
    # Router mechanically returns response based on service response_type (no business logic)
    if service_response.response_type == "fastapi":
        return service_response.to_fastapi_response()
    
    return StandardResponse(
        data=service_response.data,
        message="Family retrieved successfully",
    )


@router.patch(
    "/{family_id}",
    response_model=StandardResponse[FamilyRead],
    status_code=status.HTTP_200_OK,
    summary=FamilyApiDocs.update["summary"],
    description=FamilyApiDocs.update["description"],
)
async def update_family(
    family_id: UUID,
    data: FamilyUpdate,
    current_user: User = Depends(get_current_superadmin),
    if_match: str | None = Header(None, alias="If-Match"),
    api: FamilyApiDep = Depends(get_family_api),
    response: Response = None,
) -> StandardResponse[FamilyRead]:
    """Update family name."""
    # Pass If-Match to service (service handles all ETag validation)
    family_read = await api.update_family(family_id, data, current_user.id, if_match=if_match)
    
    # Router only sets headers from service result (no business logic)
    if hasattr(family_read, '_etag'):
        response.headers["ETag"] = family_read._etag
    
    return StandardResponse(
        data=family_read,
        message="Family updated successfully",
    )


@router.delete(
    "/{family_id}",
    response_model=StandardResponse[FamilyRead],
    status_code=status.HTTP_200_OK,
    summary=FamilyApiDocs.soft_delete["summary"],
    description=FamilyApiDocs.soft_delete["description"],
)
async def soft_delete_family(
    family_id: UUID,
    current_user: User = Depends(get_current_superadmin),
    if_match: str | None = Header(None, alias="If-Match"),
    api: FamilyApiDep = Depends(get_family_api),
    response: Response = None,
) -> StandardResponse[FamilyRead]:
    """Soft delete family."""
    # Pass If-Match to service (service handles all ETag validation)
    family_read = await api.soft_delete_family(family_id, current_user.id, if_match=if_match)
    
    # Router only sets headers from service result (no business logic)
    if hasattr(family_read, '_etag'):
        response.headers["ETag"] = family_read._etag
    
    return StandardResponse(
        data=family_read,
        message="Family soft-deleted successfully",
    )

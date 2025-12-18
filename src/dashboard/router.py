"""Dashboard analytics router."""
from typing import Optional
from fastapi import APIRouter, Depends, status, Header, Response
from src.schemas import StandardResponse
from src.dashboard.schemas import AnalyticsDashboardResponse
from src.dashboard.dependencies import (
    get_current_superadmin,
    get_dashboard_api,
    DashboardApiDep,
)
from src.dashboard.documentations.dashboard_api_doc import DashboardApiDocs
from src.dashboard.constants import SUCCESS_DASHBOARD_RETRIEVED
from src.users.models import User


router = APIRouter(
    prefix="/analytics",
    tags=["Analytics"],
)


@router.get(
    "/dashboard",
    response_model=StandardResponse[AnalyticsDashboardResponse],
    status_code=status.HTTP_200_OK,
    summary=DashboardApiDocs.get_dashboard_analytics["summary"],
    description=DashboardApiDocs.get_dashboard_analytics["description"],
)
async def get_dashboard_analytics(
    current_user: User = Depends(get_current_superadmin),
    api: DashboardApiDep = Depends(get_dashboard_api),
    if_none_match: str | None = Header(None, alias="If-None-Match"),
    response: Response = None,
) -> StandardResponse[AnalyticsDashboardResponse]:
    """Get platform-wide dashboard analytics."""
    # Delegate to service (business logic in service)
    # Note: Analytics endpoint may not support ETag (implementation-dependent)
    # Service will ignore if_none_match if not supported
    result = await api.get_dashboard_analytics(if_none_match=if_none_match)
    
    # Router sets headers if service attaches ETag (optional for analytics)
    if hasattr(result, '_etag'):
        response.headers["ETag"] = result._etag
    if hasattr(result, '_last_modified'):
        response.headers["Last-Modified"] = result._last_modified
    
    return StandardResponse(
        data=result,
        message=SUCCESS_DASHBOARD_RETRIEVED,
    )


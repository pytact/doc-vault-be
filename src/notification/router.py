"""Notification router."""
from uuid import UUID
from typing import Optional
from fastapi import APIRouter, Depends, status, Header, Response
from fastapi.responses import Response as FastAPIResponse
from src.schemas import StandardResponse
from src.notification.schemas import (
    NotificationListQuery,
    NotificationRead,
    NotificationPaginatedResponse,
    NotificationMarkReadResponse,
    NotificationMarkAllReadResponse,
    NotificationStatusUpdateRequest,
    UpcomingExpiriesResponse,
)
from src.notification.dependencies import (
    get_notification_api,
    NotificationApiDep,
)
from src.notification.documentations.notification_api_doc import NotificationApiDocs
from src.notification.constants import (
    SUCCESS_NOTIFICATIONS_RETRIEVED,
    SUCCESS_NOTIFICATION_MARKED_READ,
    SUCCESS_NOTIFICATION_MARKED_UNREAD,
    SUCCESS_ALL_NOTIFICATIONS_MARKED_READ,
    SUCCESS_ALL_NOTIFICATIONS_MARKED_UNREAD,
    SUCCESS_UPCOMING_EXPIRIES_RETRIEVED,
)
from src.users.models import User
from src.auth.dependencies import get_current_user, oauth2_scheme


router = APIRouter(
    prefix="/notifications",
    tags=["Notifications"],
)


@router.get(
    "",
    response_model=StandardResponse[NotificationPaginatedResponse],
    summary=NotificationApiDocs.list["summary"],
    description=NotificationApiDocs.list["description"],
)
async def list_notifications(
    query: NotificationListQuery = Depends(NotificationListQuery),
    current_user: User = Depends(get_current_user),
    api: NotificationApiDep = Depends(get_notification_api),
    token: str = Depends(oauth2_scheme),
    if_none_match: Optional[str] = Header(None, alias="If-None-Match"),
    response: Response = None,
) -> StandardResponse[NotificationPaginatedResponse] | FastAPIResponse:
    """List notifications with pagination and sorting."""
    # Delegate to service (business logic in service)
    service_response = await api.list_notifications(
        user=current_user, query=query, token=token, if_none_match=if_none_match
    )
    
    # Set headers from service response (HTTP concern - header setting)
    for key, value in service_response.headers.items():
        response.headers[key] = value
    
    # Router mechanically returns response based on service response_type (no business logic)
    if service_response.response_type == "fastapi":
        return service_response.to_fastapi_response()
    
    return StandardResponse(
        data=service_response.data,
        message=SUCCESS_NOTIFICATIONS_RETRIEVED,
    )


@router.patch(
    "/{notification_id}/read",
    response_model=StandardResponse[NotificationMarkReadResponse],
    summary=NotificationApiDocs.mark_read["summary"],
    description=NotificationApiDocs.mark_read["description"],
)
async def update_notification_read_status(
    notification_id: UUID,
    status_request: NotificationStatusUpdateRequest,
    current_user: User = Depends(get_current_user),
    api: NotificationApiDep = Depends(get_notification_api),
    token: str = Depends(oauth2_scheme),
    if_match: Optional[str] = Header(None, alias="If-Match"),
    response: Response = None,
) -> StandardResponse[NotificationMarkReadResponse]:
    """Update notification read status (mark as read or unread)."""
    # Delegate to service (business logic in service, including If-Match validation)
    service_response = await api.update_notification_read_status(
        notification_id=notification_id,
        user=current_user,
        status_request=status_request,
        token=token,
        if_match=if_match,
    )
    
    # Set headers from service response (HTTP concern - header setting)
    for key, value in service_response.headers.items():
        response.headers[key] = value
    
    # Determine success message based on status (presentation concern - selecting constant)
    message = (
        SUCCESS_NOTIFICATION_MARKED_READ
        if status_request.is_read
        else SUCCESS_NOTIFICATION_MARKED_UNREAD
    )
    
    return StandardResponse(
        data=service_response.data,
        message=message,
    )


@router.patch(
    "/read-all",
    response_model=StandardResponse[NotificationMarkAllReadResponse],
    summary=NotificationApiDocs.mark_all_read["summary"],
    description=NotificationApiDocs.mark_all_read["description"],
)
async def update_all_notifications_read_status(
    status_request: NotificationStatusUpdateRequest,
    current_user: User = Depends(get_current_user),
    api: NotificationApiDep = Depends(get_notification_api),
    token: str = Depends(oauth2_scheme),
) -> StandardResponse[NotificationMarkAllReadResponse]:
    """Update read status for all notifications (mark all as read or unread)."""
    result = await api.update_all_notifications_read_status(
        user=current_user,
        status_request=status_request,
        token=token,
    )
    
    # Determine success message based on status
    message = (
        SUCCESS_ALL_NOTIFICATIONS_MARKED_READ
        if status_request.is_read
        else SUCCESS_ALL_NOTIFICATIONS_MARKED_UNREAD
    )
    
    return StandardResponse(
        data=result,
        message=message,
    )


@router.get(
    "/upcoming-expiries",
    response_model=StandardResponse[UpcomingExpiriesResponse],
    summary=NotificationApiDocs.upcoming_expiries["summary"],
    description=NotificationApiDocs.upcoming_expiries["description"],
)
async def get_upcoming_expiries(
    current_user: User = Depends(get_current_user),
    api: NotificationApiDep = Depends(get_notification_api),
    token: str = Depends(oauth2_scheme),
) -> StandardResponse[UpcomingExpiriesResponse]:
    """Get upcoming expiries for dashboard widget."""
    result = await api.get_upcoming_expiries(
        user=current_user,
        token=token,
    )
    
    return StandardResponse(
        data=result,
        message=SUCCESS_UPCOMING_EXPIRIES_RETRIEVED,
    )


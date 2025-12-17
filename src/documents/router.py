"""Document router."""
from uuid import UUID
from typing import Optional
from fastapi import APIRouter, Depends, status, Header, Response, File, UploadFile, Form
from fastapi.responses import Response as FastAPIResponse
from src.schemas import StandardResponse
from src.documents.utils import parse_expiry_date, parse_details_json
from src.documents.schemas import (
    DocumentCreate,
    DocumentUpdate,
    DocumentRead,
    DocumentListQuery,
    DocumentFileQuery,
    DocumentPaginatedResponse,
    FileUploadResponse,
    DocumentAssignmentListQuery,
    DocumentAssignmentCreate,
    DocumentAssignmentUpdate,
    DocumentAssignmentRead,
    DocumentAssignmentPaginatedResponse,
    BulkAssignmentResponse,
)
from src.documents.dependencies import (
    get_document_api,
    DocumentApiDep,
    get_document_assignment_api,
    DocumentAssignmentApiDep,
)
from src.documents.documentations.document_api_doc import DocumentApiDocs
from src.documents.documentations.document_assignment_api_doc import DocumentAssignmentApiDocs
from src.users.models import User
from src.auth.dependencies import get_current_user, oauth2_scheme
from src.documents.constants import (
    SUCCESS_DOCUMENT_CREATED,
    SUCCESS_DOCUMENT_RETRIEVED,
    SUCCESS_DOCUMENTS_RETRIEVED,
    SUCCESS_DOCUMENT_UPDATED,
    SUCCESS_DOCUMENT_DELETED,
    SUCCESS_FILE_REPLACED,
    SUCCESS_ASSIGNMENTS_RETRIEVED,
    SUCCESS_ASSIGNMENTS_PROCESSED,
    SUCCESS_ASSIGNMENT_UPDATED,
    SUCCESS_ASSIGNMENT_DELETED,
)


router = APIRouter(
    prefix="/documents",
    tags=["Documents"],
)


@router.post(
    "",
    response_model=StandardResponse[DocumentRead],
    status_code=status.HTTP_201_CREATED,
    summary=DocumentApiDocs.create["summary"],
    description=DocumentApiDocs.create["description"],
)
async def create_document(
    # multipart/form-data fields
    title: str = Form(..., description="Document title (required)"),
    category_id: UUID = Form(..., description="Category ID (UUID, required)"),
    subcategory_id: UUID = Form(..., description="Subcategory ID (UUID, required)"),
    family_id: Optional[UUID] = Form(
        None, description="Family ID (UUID, optional - auto-filled from token if not provided)"
    ),
    expiry_date: Optional[str] = Form(
        None, description="Optional expiry date (YYYY-MM-DD)"
    ),
    details_json: Optional[str] = Form(
        None,
        description='Optional JSON metadata (e.g. {"key": "value"})',
    ),

    file: UploadFile = File(
        None,
        description="Optional PDF file (max 5MB, application/pdf)",
    ),

    # dependencies
    current_user: User = Depends(get_current_user),
    api: DocumentApiDep = Depends(get_document_api),
    token: str = Depends(oauth2_scheme),
    response: Response = None,
) -> StandardResponse[DocumentRead]:
    """Create document with metadata and optionally upload a PDF file."""
    # Parse and validate input using utility functions (HTTP concern - input validation)
    parsed_expiry_date = parse_expiry_date(expiry_date)
    parsed_details_json = parse_details_json(details_json)

    # Create schema (HTTP concern - input validation)
    data = DocumentCreate(
        title=title,
        category_id=category_id,
        subcategory_id=subcategory_id,
        expiry_date=parsed_expiry_date,
        details_json=parsed_details_json,
    )

    # Read file content if provided (HTTP concern - file handling)
    file_content = None
    content_type = None
    if file:
        file_content = await file.read()
        content_type = file.content_type

    # Delegate to service (business logic in service)
    service_response = await api.create_document(
        data=data,
        user=current_user,
        token=token,
        family_id=family_id,
        file_content=file_content,
        content_type=content_type,
    )

    # Set headers from service response (HTTP concern - header setting)
    for key, value in service_response.headers.items():
        response.headers[key] = value

    return StandardResponse(
        data=service_response.data,
        message=SUCCESS_DOCUMENT_CREATED,
    )


@router.get(
    "",
    response_model=StandardResponse[DocumentPaginatedResponse],
    status_code=status.HTTP_200_OK,
    summary=DocumentApiDocs.list["summary"],
    description=DocumentApiDocs.list["description"],
)
async def list_documents(
    query: DocumentListQuery = Depends(DocumentListQuery),
    current_user: User = Depends(get_current_user),
    api: DocumentApiDep = Depends(get_document_api),
    token: str = Depends(oauth2_scheme),
) -> StandardResponse[DocumentPaginatedResponse]:
    """List documents with pagination, filtering, search, and sorting."""
    # Delegate to service (business logic in service, including URL construction)
    service_response = await api.list_documents(query, current_user, token=token)
    
    return StandardResponse(
        data=service_response.data,
        message=SUCCESS_DOCUMENTS_RETRIEVED,
    )


@router.get(
    "/{document_id}",
    response_model=StandardResponse[DocumentRead],
    status_code=status.HTTP_200_OK,
    summary=DocumentApiDocs.get["summary"],
    description=DocumentApiDocs.get["description"],
)
async def get_document(
    document_id: UUID,
    current_user: User = Depends(get_current_user),
    api: DocumentApiDep = Depends(get_document_api),
    token: str = Depends(oauth2_scheme),
    if_none_match: str | None = Header(None, alias="If-None-Match"),
    response: Response = None,
) -> StandardResponse[DocumentRead] | FastAPIResponse:
    """Get single document with full metadata."""
    # Delegate to service (business logic in service)
    service_response = await api.get_document_by_id(
        document_id, current_user, token=token, if_none_match=if_none_match
    )
    
    # Set headers from service response (HTTP concern - header setting)
    for key, value in service_response.headers.items():
        response.headers[key] = value
    
    # Router mechanically returns response based on service response_type (no business logic)
    if service_response.response_type == "fastapi":
        return service_response.to_fastapi_response()
    
    return StandardResponse(
        data=service_response.data,
        message=SUCCESS_DOCUMENT_RETRIEVED,
    )


@router.patch(
    "/{document_id}",
    response_model=StandardResponse[DocumentRead],
    status_code=status.HTTP_200_OK,
    summary=DocumentApiDocs.update["summary"],
    description=DocumentApiDocs.update["description"],
)
async def update_document(
    document_id: UUID,
    data: DocumentUpdate,
    current_user: User = Depends(get_current_user),
    api: DocumentApiDep = Depends(get_document_api),
    token: str = Depends(oauth2_scheme),
    if_match: str | None = Header(None, alias="If-Match"),
    response: Response = None,
) -> StandardResponse[DocumentRead]:
    """Update document metadata."""
    # Delegate to service (business logic in service)
    service_response = await api.update_document(
        document_id, data, current_user, token=token, if_match=if_match
    )
    
    # Set headers from service response (HTTP concern - header setting)
    for key, value in service_response.headers.items():
        response.headers[key] = value
    
    return StandardResponse(
        data=service_response.data,
        message=SUCCESS_DOCUMENT_UPDATED,
    )


@router.delete(
    "/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary=DocumentApiDocs.delete["summary"],
    description=DocumentApiDocs.delete["description"],
)
async def delete_document(
    document_id: UUID,
    current_user: User = Depends(get_current_user),
    api: DocumentApiDep = Depends(get_document_api),
    token: str = Depends(oauth2_scheme),
    if_match: str | None = Header(None, alias="If-Match"),
) -> None:
    """Soft delete document."""
    # Delegate to service (business logic in service)
    await api.delete_document(
        document_id, current_user, token=token, if_match=if_match
    )


@router.put(
    "/{document_id}/file",
    response_model=StandardResponse[FileUploadResponse],
    status_code=status.HTTP_200_OK,
    summary=DocumentApiDocs.replace_file["summary"],
    description=DocumentApiDocs.replace_file["description"],
)
async def replace_file(
    document_id: UUID,
    file: UploadFile = File(..., description="PDF file to replace (max 5MB, application/pdf)"),
    current_user: User = Depends(get_current_user),
    api: DocumentApiDep = Depends(get_document_api),
    token: str = Depends(oauth2_scheme),
    if_match: str | None = Header(None, alias="If-Match"),
    response: Response = None,
) -> StandardResponse[FileUploadResponse]:
    """Replace existing PDF file."""
    # Read file content (HTTP concern - file handling)
    file_content = await file.read()
    content_type = file.content_type or "application/pdf"
    
    # Delegate to service (business logic in service)
    service_response = await api.replace_file(
        document_id, file_content, content_type, current_user, token=token,
        if_match=if_match
    )
    
    # Set headers from service response (HTTP concern - header setting)
    for key, value in service_response.headers.items():
        response.headers[key] = value
    
    return StandardResponse(
        data=service_response.data,
        message=SUCCESS_FILE_REPLACED,
    )


@router.get(
    "/{document_id}/file",
    summary=DocumentApiDocs.get_file["summary"],
    description=DocumentApiDocs.get_file["description"],
)
async def get_file(
    document_id: UUID,
    query: DocumentFileQuery = Depends(DocumentFileQuery),
    current_user: User = Depends(get_current_user),
    api: DocumentApiDep = Depends(get_document_api),
    token: str = Depends(oauth2_scheme),
    if_none_match: str | None = Header(None, alias="If-None-Match"),
) -> FastAPIResponse:
    """Preview or download PDF file."""
    # Delegate to service (business logic in service)
    service_response = await api.get_file(
        document_id, current_user, token=token, if_none_match=if_none_match,
        mode=query.mode
    )
    
    # Router mechanically returns response based on service response_type (no business logic)
    if service_response.response_type == "fastapi":
        return service_response.to_fastapi_response()
    
    # Unpack file data from service response
    file_content, mime_type, updated_at = service_response.data
    
    # Set Content-Disposition based on mode (HTTP concern - header setting)
    filename = "document.pdf"
    if query.mode == "download":
        content_disposition = f'attachment; filename="{filename}"'
    else:
        content_disposition = f'inline; filename="{filename}"'
    
    # Merge service headers with Content-Disposition and Content-Length
    headers = dict(service_response.headers)
    headers["Content-Length"] = str(len(file_content))
    headers["Content-Disposition"] = content_disposition
    
    # Return Response with binary content (HTTP concern - response formatting)
    return FastAPIResponse(
        content=file_content,
        media_type=mime_type,
        headers=headers,
    )


# ==================== Document Assignment Endpoints ====================

@router.get(
    "/{document_id}/assignments",
    response_model=StandardResponse[DocumentAssignmentPaginatedResponse],
    status_code=status.HTTP_200_OK,
    summary=DocumentAssignmentApiDocs.list["summary"],
    description=DocumentAssignmentApiDocs.list["description"],
)
async def list_assignments(
    document_id: UUID,
    query: DocumentAssignmentListQuery = Depends(DocumentAssignmentListQuery),
    current_user: User = Depends(get_current_user),
    api: DocumentAssignmentApiDep = Depends(get_document_assignment_api),
    token: str = Depends(oauth2_scheme),
    if_none_match: str | None = Header(None, alias="If-None-Match"),
    response: Response = None,
) -> StandardResponse[DocumentAssignmentPaginatedResponse] | FastAPIResponse:
    """List assignments for a document."""
    # Delegate to service (business logic in service, including URL construction)
    service_response = await api.list_assignments(
        document_id, query, current_user, token=token, if_none_match=if_none_match
    )
    
    # Router mechanically returns response based on service response_type (no business logic)
    if service_response.response_type == "fastapi":
        return service_response.to_fastapi_response()
    
    # Set headers from service response (HTTP concern - header setting)
    for key, value in service_response.headers.items():
        response.headers[key] = value
    
    return StandardResponse(
        data=service_response.data,
        message=SUCCESS_ASSIGNMENTS_RETRIEVED,
    )


@router.post(
    "/{document_id}/assignments/bulk",
    response_model=StandardResponse[BulkAssignmentResponse],
    status_code=status.HTTP_201_CREATED,
    summary=DocumentAssignmentApiDocs.create["summary"],
    description=DocumentAssignmentApiDocs.create["description"],
)
async def create_assignments_bulk(
    document_id: UUID,
    data: DocumentAssignmentCreate,
    current_user: User = Depends(get_current_user),
    api: DocumentAssignmentApiDep = Depends(get_document_assignment_api),
    token: str = Depends(oauth2_scheme),
) -> StandardResponse[BulkAssignmentResponse]:
    """Create or update bulk assignments."""
    # Delegate to service (business logic in service)
    service_response = await api.create_assignments_bulk(
        document_id, data, current_user, token=token
    )
    
    return StandardResponse(
        data=service_response.data,
        message=SUCCESS_ASSIGNMENTS_PROCESSED,
    )


@router.put(
    "/{document_id}/assignments/{user_id}",
    response_model=StandardResponse[DocumentAssignmentRead],
    status_code=status.HTTP_200_OK,
    summary=DocumentAssignmentApiDocs.update["summary"],
    description=DocumentAssignmentApiDocs.update["description"],
)
async def update_assignment(
    document_id: UUID,
    user_id: UUID,
    data: DocumentAssignmentUpdate,
    current_user: User = Depends(get_current_user),
    api: DocumentAssignmentApiDep = Depends(get_document_assignment_api),
    token: str = Depends(oauth2_scheme),
    if_match: str | None = Header(None, alias="If-Match"),
    response: Response = None,
) -> StandardResponse[DocumentAssignmentRead]:
    """Update assignment."""
    # Delegate to service (business logic in service)
    service_response = await api.update_assignment(
        document_id, user_id, data, current_user, token=token, if_match=if_match
    )
    
    # Set headers from service response (HTTP concern - header setting)
    for key, value in service_response.headers.items():
        response.headers[key] = value
    
    return StandardResponse(
        data=service_response.data,
        message=SUCCESS_ASSIGNMENT_UPDATED,
    )


@router.delete(
    "/{document_id}/assignments/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary=DocumentAssignmentApiDocs.delete["summary"],
    description=DocumentAssignmentApiDocs.delete["description"],
)
async def delete_assignment(
    document_id: UUID,
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    api: DocumentAssignmentApiDep = Depends(get_document_assignment_api),
    token: str = Depends(oauth2_scheme),
    if_match: str | None = Header(None, alias="If-Match"),
) -> None:
    """Delete assignment."""
    # Delegate to service (business logic in service)
    await api.delete_assignment(
        document_id, user_id, current_user, token=token, if_match=if_match
    )

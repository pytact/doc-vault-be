"""Document service."""
from uuid import UUID
from typing import Optional, List, Tuple
from datetime import datetime, date
from fastapi import status
from fastapi.responses import Response as FastAPIResponse
from sqlalchemy.ext.asyncio import AsyncSession
from src.response import ServiceResponse
from src.documents.repository import DocumentRepository, DocumentAssignmentRepository
from src.documents.models import Document, DocumentAssign
from src.documents.schemas import (
    DocumentCreate,
    DocumentUpdate,
    DocumentRead,
    DocumentListQuery,
    DocumentPaginatedResponse,
    FileUploadResponse,
    DocumentAssignmentListQuery,
    DocumentAssignmentCreate,
    DocumentAssignmentUpdate,
    DocumentAssignmentRead,
    DocumentAssignmentPaginatedResponse,
    BulkAssignmentResponse,
    UserSummary,
)
from src.documents.exceptions import (
    DocumentNotFound,
    DocumentPermissionDenied,
    CategorySubcategoryMismatch,
    DocumentAlreadyExists,
    FileTooLarge,
    UnsupportedMediaType,
    FileNotUploaded,
    ETagMismatch,
    ETagRequired,
    AssignmentNotFound,
    SelfAssignmentBlocked,
    UserNotInFamily,
    AssignmentPermissionDenied,
)
from src.documents.constants import (
    MAX_FILE_SIZE_BYTES,
    ALLOWED_MIME_TYPE,
    PERMISSION_OWNER,
    PERMISSION_EDITOR,
    PERMISSION_VIEWER,
    ACCESS_TYPE_VIEWER,
    ACCESS_TYPE_EDITOR,
)
from src.documents.utils import (
    generate_etag,
    format_last_modified,
    validate_file_size,
    validate_mime_type,
    generate_file_path,
    save_file,
    delete_file,
    read_file as read_file_from_disk,
    build_pagination_urls,
)
from src.pagination import calculate_total_pages
from src.users.models import User
from src.auth.utils import decode_token


class DocumentService:
    """Service for document business logic."""
    
    def __init__(self, session: AsyncSession):
        self.repository = DocumentRepository(session)
        self.assignment_repository = DocumentAssignmentRepository(session)
        self.session = session
    
    def _get_user_role_and_family(self, token: Optional[str]) -> tuple[Optional[str], Optional[UUID]]:
        """Extract role and family_id from JWT token (business logic in service)."""
        if not token:
            return None, None
        
        payload = decode_token(token)
        if not payload:
            return None, None
        
        role = payload.get("role", "").lower()
        family_id_str = payload.get("family_id")
        family_id = UUID(family_id_str) if family_id_str else None
        
        return role, family_id
    
    def _validate_family_access(self, user_role: Optional[str], family_id: Optional[UUID]) -> UUID:
        """Validate family access and return family_id (business logic in service)."""
        # SuperAdmin is not allowed to access documents
        if user_role == "superadmin" or family_id is None:
            from src.exceptions import ForbiddenError
            raise ForbiddenError(
                message="SuperAdmin is not allowed to access documents. Only FamilyAdmin and Member can access documents.",
                error_code="INSUFFICIENT_PERMISSIONS",
                details=[{"field": "role", "issue": "SuperAdmin access is not permitted"}],
            )
        return family_id
    
    def _determine_permission(
        self, document: Document, user_id: UUID, user_role: str, user_family_id: Optional[UUID]
    ) -> str:
        """Determine user's permission level for document.
        
        Business Rules:
        - Owner: Always has owner permission
        - FamilyAdmin: Full access ONLY if they belong to document's family
        - Member: Only their own documents OR assigned documents
        
        Returns: "owner", "editor", "viewer", or None
        """
        # Check if user is owner
        if document.owner_id == user_id:
            return PERMISSION_OWNER
        
        # Check if user is FamilyAdmin - MUST belong to document's family
        if user_role == "familyadmin":
            # FamilyAdmin gets full access ONLY if they belong to the document's family
            if user_family_id and document.family_id == user_family_id:
                return PERMISSION_OWNER  # FamilyAdmin has owner-level access for their family
            # If FamilyAdmin doesn't belong to document's family, no access
            return None
        
        # For Member role: Only their own documents OR assigned documents
        # Member cannot access other members' documents unless assigned
        # This will be checked in _check_permission via DocumentAssign table
        
        return None
    
    async def _check_permission(
        self, document: Document, user_id: UUID, user_role: str, required_permission: str, user_family_id: Optional[UUID]
    ) -> str:
        """Check if user has required permission for document.
        
        Business Rules:
        - Owner: Always has owner permission
        - FamilyAdmin: Full access ONLY if they belong to document's family
        - Member: Only their own documents OR assigned documents (via document_assign table)
          - editor: view and edit access
          - viewer: view only access
        
        Returns permission level if access granted, raises exception otherwise.
        """
        permission = self._determine_permission(document, user_id, user_role, user_family_id)
        
        # For Member: Check DocumentAssign table for editor/viewer permissions
        # Member can only access:
        # 1. Their own documents (already checked above - returns PERMISSION_OWNER)
        # 2. Documents assigned to them via document_assign table
        if not permission and user_role == "member":
            assign = await self.repository.get_document_assign(document.id, user_id)
            if assign:
                if assign.access_type == ACCESS_TYPE_EDITOR:
                    permission = PERMISSION_EDITOR
                elif assign.access_type == ACCESS_TYPE_VIEWER:
                    permission = PERMISSION_VIEWER
            # If Member is not owner and not assigned, no access (permission remains None)
        
        if not permission:
            raise DocumentPermissionDenied()
        
        # Check if permission meets requirement
        permission_hierarchy = {
            PERMISSION_VIEWER: 1,
            PERMISSION_EDITOR: 2,
            PERMISSION_OWNER: 3,
        }
        required_level = permission_hierarchy.get(required_permission, 0)
        user_level = permission_hierarchy.get(permission, 0)
        
        if user_level < required_level:
            raise DocumentPermissionDenied()
        
        return permission
    
    async def _get_permission_for_document(
        self, document: Document, user_id: UUID, user_role: str, user_family_id: Optional[UUID]
    ) -> str:
        """Get user's permission level for document (without raising exception)."""
        permission = self._determine_permission(document, user_id, user_role, user_family_id)
        
        # For Member: Check DocumentAssign table for editor/viewer permissions
        if not permission and user_role == "member":
            assign = await self.repository.get_document_assign(document.id, user_id)
            if assign:
                if assign.access_type == ACCESS_TYPE_EDITOR:
                    permission = PERMISSION_EDITOR
                elif assign.access_type == ACCESS_TYPE_VIEWER:
                    permission = PERMISSION_VIEWER
        
        return permission or None  # Return None if no permission found (don't default)
    
    async def create_document(
        self, data: DocumentCreate, user: User, token: Optional[str] = None,
        family_id: Optional[UUID] = None, file_content: Optional[bytes] = None,
        content_type: Optional[str] = None
    ) -> ServiceResponse[DocumentRead]:
        """Create document with metadata and optionally upload file in one operation (business logic in service)."""
        # Extract role and family_id from token (business logic)
        user_role, token_family_id = self._get_user_role_and_family(token)
        
        # Determine family_id to use (default to token family_id)
        if not family_id:
            family_id = token_family_id
        
        # Validate family access (business logic)
        if not family_id:
            from src.exceptions import ForbiddenError
            raise ForbiddenError(
                message="Family ID is required. Please provide family_id in the request.",
                error_code="INSUFFICIENT_PERMISSIONS",
                details=[{"field": "family_id", "issue": "Family ID is required"}],
            )
        
        # Validate that user belongs to the specified family (business logic)
        if str(family_id) != str(token_family_id):
            from src.exceptions import ForbiddenError
            raise ForbiddenError(
                message="You can only create documents in your own family.",
                error_code="INSUFFICIENT_PERMISSIONS",
                details=[{"field": "family_id", "issue": f"You do not belong to family {family_id}"}],
            )
        
        # Validate SuperAdmin cannot create documents (business logic)
        if user_role == "superadmin":
            from src.exceptions import ForbiddenError
            raise ForbiddenError(
                message="SuperAdmin is not allowed to create documents. Only FamilyAdmin and Member can create documents.",
                error_code="INSUFFICIENT_PERMISSIONS",
                details=[{"field": "role", "issue": "SuperAdmin access is not permitted"}],
            )
        # Check if document already exists for this user in the same category and subcategory
        document_exists = await self.repository.document_exists_for_user(
            owner_id=user.id,
            family_id=family_id,
            category_id=data.category_id,
            subcategory_id=data.subcategory_id,
        )
        if document_exists:
            raise DocumentAlreadyExists(data.category_id, data.subcategory_id)
        
        # Validate category-subcategory pairing
        is_valid = await self.repository.check_category_subcategory_pair(
            data.category_id, data.subcategory_id
        )
        if not is_valid:
            raise CategorySubcategoryMismatch()
        
        # If file is provided, validate it
        file_path = None
        file_size = None
        mime_type = None
        
        if file_content:
            file_size = len(file_content)
            if not validate_file_size(file_size):
                raise FileTooLarge(file_size, MAX_FILE_SIZE_BYTES)
            
            if not validate_mime_type(content_type):
                raise UnsupportedMediaType(content_type)
            
            # Generate file path (will be set after document creation)
            mime_type = content_type
        
        # Create document first
        document = Document(
            family_id=family_id,
            owner_id=user.id,
            title=data.title,
            category_id=data.category_id,
            subcategory_id=data.subcategory_id,
            expiry_date=data.expiry_date,
            details=data.details_json,
            created_by=user.id,
            updated_by=user.id,
        )
        
        document = await self.repository.create(document)
        
        # If file provided, save file and update document with file metadata
        if file_content:
            file_path = generate_file_path(str(document.id), str(document.family_id))
            
            # Save file to disk
            save_file(file_content, file_path)
            
            # Update document with file metadata
            document.file_path = file_path
            document.file_size = file_size
            document.mime_type = mime_type
            document.updated_by = user.id
            document = await self.repository.update(document)
        
        # Create reminder schedules if expiry_date is set
        if document.expiry_date:
            try:
                from src.notification.service import NotificationService
                notification_service = NotificationService(self.session)
                await notification_service.create_reminder_schedules_for_document(
                    document_id=document.id,
                    expiry_date=document.expiry_date,
                )
            except Exception as e:
                # Log error but don't fail document creation
                # Reminder schedules are not critical for document creation
                print(f"Warning: Failed to create reminder schedules for document {document.id}: {str(e)}")
        
        # Convert to response schema
        result = DocumentRead.model_validate(document)
        result.permission = PERMISSION_OWNER
        
        # Generate ETag and Last-Modified (business logic in service)
        etag = generate_etag(document.updated_at)
        last_modified = format_last_modified(document.updated_at)
        
        # Return ServiceResponse with ETag headers (business logic in service)
        return ServiceResponse(
            data=result,
            status_code=status.HTTP_201_CREATED,
            headers={
                "ETag": etag,
                "Last-Modified": last_modified,
            },
        )
    
    async def get_document_by_id(
        self, document_id: UUID, user: User, token: Optional[str] = None,
        if_none_match: Optional[str] = None
    ) -> ServiceResponse[DocumentRead]:
        """Get document by ID with ETag support (business logic in service)."""
        # Extract role and family_id from token (business logic)
        user_role, family_id = self._get_user_role_and_family(token)
        
        # Validate family access (business logic)
        family_id = self._validate_family_access(user_role, family_id)
        
        document = await self.repository.get_by_id(document_id)
        if not document:
            raise DocumentNotFound(str(document_id))
        
        # Check family access (business logic)
        if document.family_id != family_id:
            raise DocumentNotFound(str(document_id))
        
        # Check permission (view access) - business logic
        permission = await self._check_permission(
            document, user.id, user_role, PERMISSION_VIEWER, family_id
        )
        
        # Generate ETag (business logic in service)
        etag = generate_etag(document.updated_at)
        last_modified = format_last_modified(document.updated_at)
        
        # Check If-None-Match (business logic validation in service)
        if if_none_match and if_none_match == etag:
            # Return 304 Not Modified (business logic decision in service)
            return ServiceResponse(
                data=None,  # 304 has no body
                status_code=status.HTTP_304_NOT_MODIFIED,
                headers={
                    "ETag": etag,
                    "Last-Modified": last_modified,
                },
                response_type="fastapi",  # Router uses this to return FastAPI Response
            )
        
        # Convert to response schema
        result = DocumentRead.model_validate(document)
        result.permission = permission
        
        # Return ServiceResponse with ETag headers (business logic in service)
        return ServiceResponse(
            data=result,
            status_code=status.HTTP_200_OK,
            headers={
                "ETag": etag,
                "Last-Modified": last_modified,
            },
        )
    
    async def update_document(
        self, document_id: UUID, data: DocumentUpdate, user: User,
        token: Optional[str] = None, if_match: Optional[str] = None
    ) -> ServiceResponse[DocumentRead]:
        """Update document metadata with ETag validation (business logic in service)."""
        # Extract role and family_id from token (business logic)
        user_role, family_id = self._get_user_role_and_family(token)
        
        # Validate family access (business logic)
        family_id = self._validate_family_access(user_role, family_id)
        
        document = await self.repository.get_by_id(document_id)
        if not document:
            raise DocumentNotFound(str(document_id))
        
        # Check family access (business logic)
        if document.family_id != family_id:
            raise DocumentNotFound(str(document_id))
        
        # Check permission (edit access) - business logic
        await self._check_permission(document, user.id, user_role, PERMISSION_EDITOR, family_id)
        
        # Validate ETag (business logic validation in service)
        current_etag = generate_etag(document.updated_at)
        if not if_match:
            raise ETagRequired()
        if if_match != current_etag:
            raise ETagMismatch()
        
        # Validate category-subcategory if both are being updated
        if data.category_id and data.subcategory_id:
            is_valid = await self.repository.check_category_subcategory_pair(
                data.category_id, data.subcategory_id
            )
            if not is_valid:
                raise CategorySubcategoryMismatch()
        elif data.subcategory_id:
            # If only subcategory is updated, validate against existing category
            is_valid = await self.repository.check_category_subcategory_pair(
                document.category_id, data.subcategory_id
            )
            if not is_valid:
                raise CategorySubcategoryMismatch()
        
        # Update fields
        # Use model_dump(exclude_unset=True) to only update fields that were explicitly provided
        update_data = data.model_dump(exclude_unset=True)
        
        # Track if expiry_date changed for reminder schedule update
        expiry_date_changed = False
        old_expiry_date = document.expiry_date
        new_expiry_date = None
        
        if "title" in update_data:
            document.title = update_data["title"]
        if "category_id" in update_data:
            document.category_id = update_data["category_id"]
        if "subcategory_id" in update_data:
            document.subcategory_id = update_data["subcategory_id"]
        if "expiry_date" in update_data:
            expiry_date_changed = True
            new_expiry_date = update_data["expiry_date"]
            document.expiry_date = update_data["expiry_date"]
        if "details_json" in update_data:
            # This allows clearing by setting to None/null
            document.details = update_data["details_json"]
        
        document.updated_by = user.id
        
        document = await self.repository.update(document)
        
        # Update reminder schedules if expiry_date changed
        if expiry_date_changed:
            try:
                from src.notification.service import NotificationService
                notification_service = NotificationService(self.session)
                
                if new_expiry_date:
                    # Create new reminder schedules for new expiry_date
                    await notification_service.create_reminder_schedules_for_document(
                        document_id=document.id,
                        expiry_date=new_expiry_date,
                    )
                else:
                    # expiry_date was set to None - cancel all pending schedules
                    from src.notification.repository import NotificationRepository
                    notification_repo = NotificationRepository(self.session)
                    await notification_repo.cancel_pending_schedules_for_document(
                        document.id
                    )
            except Exception as e:
                # Log error but don't fail document update
                # Reminder schedules are not critical for document update
                print(f"Warning: Failed to update reminder schedules for document {document.id}: {str(e)}")
        
        # Convert to response schema
        result = DocumentRead.model_validate(document)
        result.permission = await self._get_permission_for_document(
            document, user.id, user_role, family_id
        )
        
        # Generate ETag (business logic in service)
        etag = generate_etag(document.updated_at)
        
        # Return ServiceResponse with ETag headers (business logic in service)
        return ServiceResponse(
            data=result,
            status_code=status.HTTP_200_OK,
            headers={
                "ETag": etag,
            },
        )
    
    async def delete_document(
        self, document_id: UUID, user: User, token: Optional[str] = None,
        if_match: Optional[str] = None
    ) -> None:
        """Soft delete document with ETag validation (business logic in service)."""
        # Extract role and family_id from token (business logic)
        user_role, family_id = self._get_user_role_and_family(token)
        
        # Validate family access (business logic)
        family_id = self._validate_family_access(user_role, family_id)
        
        document = await self.repository.get_by_id(document_id)
        if not document:
            raise DocumentNotFound(str(document_id))
        
        # Check family access (business logic)
        if document.family_id != family_id:
            raise DocumentNotFound(str(document_id))
        
        # Check permission (delete access - owner or familyadmin only) - business logic
        await self._check_permission(document, user.id, user_role, PERMISSION_OWNER, family_id)
        
        # Validate ETag (business logic validation in service)
        current_etag = generate_etag(document.updated_at)
        if not if_match:
            raise ETagRequired()
        if if_match != current_etag:
            raise ETagMismatch()
        
        # Soft delete
        await self.repository.soft_delete(document_id, user.id)
    
    async def list_documents(
        self, query: DocumentListQuery, user: User, token: Optional[str] = None
    ) -> ServiceResponse[DocumentPaginatedResponse]:
        """List documents with pagination, filtering, search, and sorting (business logic in service)."""
        # Extract role and family_id from token (business logic)
        user_role, family_id = self._get_user_role_and_family(token)
        
        # Validate family access (business logic)
        family_id = self._validate_family_access(user_role, family_id)
        
        documents, total = await self.repository.list_with_pagination(
            family_id=family_id,
            user_id=user.id,
            user_role=user_role,
            page=query.page,
            page_size=query.page_size,
            category_id=query.category_id,
            subcategory_id=query.subcategory_id,
            owner_user_id=query.owner_user_id,
            expiry_date=query.expiry_date,
            search=query.search,
            sort_by=query.sort_by,
            sort_order=query.sort_order,
        )
        
        # Convert to response schemas with permission info
        items = []
        for doc in documents:
            doc_read = DocumentRead.model_validate(doc)
            doc_read.permission = await self._get_permission_for_document(doc, user.id, user_role, family_id)
            items.append(doc_read)
        
        total_pages = calculate_total_pages(total, query.page_size)
        
        # Build pagination URLs (business logic in service)
        base_url = "/v1/documents"
        query_params = {
            "category_id": str(query.category_id) if query.category_id else None,
            "subcategory_id": str(query.subcategory_id) if query.subcategory_id else None,
            "owner_user_id": str(query.owner_user_id) if query.owner_user_id else None,
            "expiry_date": str(query.expiry_date) if query.expiry_date else None,
            "search": query.search,
            "sort_by": query.sort_by,
            "sort_order": query.sort_order,
            "page_size": str(query.page_size),
        }
        next_page, prev_page = build_pagination_urls(
            base_url, query.page, total_pages, query_params
        )
        
        result = DocumentPaginatedResponse(
            items=items,
            total=total,
            page=query.page,
            page_size=query.page_size,
            total_pages=total_pages,
            next_page=next_page,
            prev_page=prev_page,
        )
        
        # Return ServiceResponse (business logic in service)
        return ServiceResponse(
            data=result,
            status_code=status.HTTP_200_OK,
        )
    
    async def replace_file(
        self, document_id: UUID, file_content: bytes, content_type: str,
        user: User, token: Optional[str] = None, if_match: Optional[str] = None
    ) -> ServiceResponse[FileUploadResponse]:
        """Replace existing PDF file with ETag validation (business logic in service)."""
        # Extract role and family_id from token (business logic)
        user_role, family_id = self._get_user_role_and_family(token)
        
        # Validate family access (business logic)
        family_id = self._validate_family_access(user_role, family_id)
        
        # Validate file size (business logic)
        file_size = len(file_content)
        if not validate_file_size(file_size):
            raise FileTooLarge(file_size, MAX_FILE_SIZE_BYTES)
        
        # Validate MIME type (business logic)
        if not validate_mime_type(content_type):
            raise UnsupportedMediaType(content_type)
        
        # Get document
        document = await self.repository.get_by_id(document_id)
        if not document:
            raise DocumentNotFound(str(document_id))
        
        # Check family access (business logic)
        if document.family_id != family_id:
            raise DocumentNotFound(str(document_id))
        
        # Check permission (replace access - owner, editor, or familyadmin) - business logic
        await self._check_permission(document, user.id, user_role, PERMISSION_EDITOR, family_id)
        
        # Validate ETag (business logic validation in service)
        current_etag = generate_etag(document.updated_at)
        if not if_match:
            raise ETagRequired()
        if if_match != current_etag:
            raise ETagMismatch()
        
        # Generate file path (reuse existing or generate new)
        file_path = document.file_path or generate_file_path(
            str(document.id), str(document.family_id)
        )
        
        # Delete old file if path changed
        if document.file_path and document.file_path != file_path:
            delete_file(document.file_path)
        
        # Save new file to disk
        save_file(file_content, file_path)
        
        # Update document
        document.file_path = file_path
        document.file_size = file_size
        document.mime_type = content_type
        document.updated_by = user.id
        
        document = await self.repository.update(document)
        
        result = FileUploadResponse(
            file_path=file_path,
            file_url=None,  # TODO: Generate CDN URL if configured
            file_size=file_size,
            content_type=content_type,
            uploaded_at=document.updated_at,
        )
        
        # Generate ETag (business logic in service)
        etag = generate_etag(document.updated_at)
        
        # Return ServiceResponse with ETag headers (business logic in service)
        return ServiceResponse(
            data=result,
            status_code=status.HTTP_200_OK,
            headers={
                "ETag": etag,
            },
        )
    
    async def get_file(
        self, document_id: UUID, user: User, token: Optional[str] = None,
        if_none_match: Optional[str] = None, mode: str = "preview"
    ) -> ServiceResponse[Tuple[bytes, str, datetime]] | ServiceResponse[None]:
        """Get document file with ETag support (business logic in service).
        
        Returns: ServiceResponse with file data or 304 Not Modified
        """
        # Extract role and family_id from token (business logic)
        user_role, family_id = self._get_user_role_and_family(token)
        
        # Validate family access (business logic)
        family_id = self._validate_family_access(user_role, family_id)
        
        document = await self.repository.get_by_id(document_id)
        if not document:
            raise DocumentNotFound(str(document_id))
        
        # Check family access (business logic)
        if document.family_id != family_id:
            raise DocumentNotFound(str(document_id))
        
        # Check permission (view access) - business logic
        await self._check_permission(document, user.id, user_role, PERMISSION_VIEWER, family_id)
        
        # Check if file exists (business logic)
        if not document.file_path:
            raise FileNotUploaded(str(document_id))
        
        # Generate ETag (business logic in service)
        etag = generate_etag(document.updated_at)
        last_modified = format_last_modified(document.updated_at)
        
        # Check If-None-Match (business logic validation in service)
        if if_none_match and if_none_match == etag:
            # Return 304 Not Modified (business logic decision in service)
            return ServiceResponse(
                data=None,  # 304 has no body
                status_code=status.HTTP_304_NOT_MODIFIED,
                headers={
                    "ETag": etag,
                    "Last-Modified": last_modified,
                },
                response_type="fastapi",  # Router uses this to return FastAPI Response
            )
        
        # Load file from disk
        file_content = read_file_from_disk(document.file_path)
        mime_type = document.mime_type or ALLOWED_MIME_TYPE
        
        # Return ServiceResponse with file data and headers (business logic in service)
        # Note: For binary file responses, router will handle conversion to FastAPIResponse
        return ServiceResponse(
            data=(file_content, mime_type, document.updated_at),
            status_code=status.HTTP_200_OK,
            headers={
                "ETag": etag,
                "Last-Modified": last_modified,
            },
        )
    
    # ==================== Document Assignment Service Methods ====================
    
    async def _check_assignment_permission(
        self, document: Document, user_id: UUID, user_role: Optional[str]
    ) -> None:
        """Check if user can manage assignments (owner or familyadmin) - business logic."""
        # Check if user is document owner
        is_owner = document.owner_id == user_id
        
        # Check if user is FamilyAdmin
        is_familyadmin = user_role == "familyadmin"
        
        if not (is_owner or is_familyadmin):
            raise AssignmentPermissionDenied()
    
    def _normalize_assignments(
        self, assignments: List[Tuple[DocumentAssign, User, Optional[UUID]]]
    ) -> List[Tuple[DocumentAssign, User, Optional[UUID]]]:
        """Normalize assignments - editor overrides viewer (business logic).
        
        Returns one assignment per user with effective access_type (editor overrides viewer).
        """
        # Group by user_id
        user_assignments: dict[UUID, Tuple[DocumentAssign, User, Optional[UUID]]] = {}
        
        for assignment, user, family_id in assignments:
            user_id = assignment.assign_to
            
            # If user already has an assignment, check if we should override
            if user_id in user_assignments:
                existing_assignment, _, _ = user_assignments[user_id]
                
                # Editor overrides viewer
                if assignment.access_type == ACCESS_TYPE_EDITOR:
                    user_assignments[user_id] = (assignment, user, family_id)
                # If existing is editor and new is viewer, keep editor (no change)
                elif existing_assignment.access_type == ACCESS_TYPE_EDITOR:
                    pass  # Keep existing editor assignment
                # Both viewer - keep the one with latest updated_at
                elif assignment.updated_at > existing_assignment.updated_at:
                    user_assignments[user_id] = (assignment, user, family_id)
            else:
                # First assignment for this user
                user_assignments[user_id] = (assignment, user, family_id)
        
        return list(user_assignments.values())
    
    def _map_user_to_user_summary(
        self, user: User, family_id: Optional[UUID]
    ) -> UserSummary:
        """Map User model to UserSummary schema (business logic transformation)."""
        # Map user status to API format
        if user.is_del:
            status_str = "SoftDeleted"
        elif user.status == "active":
            status_str = "Active"
        elif user.status == "pending":
            status_str = "PendingActivation"
        else:
            status_str = "Active"  # Default
        
        # Use email as name (User model doesn't have name field)
        return UserSummary(
            id=user.id,
            name=user.email,  # Using email as name
            email=user.email,
            family_id=family_id or user.id,  # Fallback to user.id if no family_id
            status=status_str,
        )
    
    def _map_assignment_to_read(
        self, assignment: DocumentAssign, user: User, family_id: Optional[UUID]
    ) -> DocumentAssignmentRead:
        """Map DocumentAssign model to DocumentAssignmentRead schema."""
        user_summary = self._map_user_to_user_summary(user, family_id)
        
        return DocumentAssignmentRead(
            id=assignment.id,
            document_id=assignment.document_id,
            assign_to_user_id=assignment.assign_to,
            owner_id=assignment.owner_id,
            user=user_summary,
            access_type=assignment.access_type,
            assigned_at=assignment.created_at,
            updated_at=assignment.updated_at,
            is_del=assignment.is_del,
        )
    
    async def list_assignments(
        self,
        document_id: UUID,
        query: DocumentAssignmentListQuery,
        user: User,
        token: Optional[str] = None,
        if_none_match: Optional[str] = None,
    ) -> ServiceResponse[DocumentAssignmentPaginatedResponse]:
        """List assignments for a document with normalization (business logic in service)."""
        # Extract role and family_id from token (business logic)
        user_role, family_id = self._get_user_role_and_family(token)
        
        # Validate family access (business logic)
        family_id = self._validate_family_access(user_role, family_id)
        
        # Get document (business logic)
        document = await self.repository.get_by_id(document_id)
        if not document:
            raise DocumentNotFound(str(document_id))
        
        # Check family access (business logic)
        if document.family_id != family_id:
            raise DocumentNotFound(str(document_id))
        
        # Check assignment permission (owner or familyadmin) - business logic
        await self._check_assignment_permission(document, user.id, user_role)
        
        # Get all assignments for normalization (business logic)
        all_assignments = await self.assignment_repository.get_all_by_document(document_id)
        
        # Normalize assignments (editor overrides viewer) - business logic
        normalized_assignments = self._normalize_assignments(all_assignments)
        
        # Apply access_type filter after normalization (business logic)
        if query.access_type:
            normalized_assignments = [
                (a, u, f) for a, u, f in normalized_assignments
                if a.access_type == query.access_type
            ]
        
        # Count total after filtering
        total = len(normalized_assignments)
        
        # Apply sorting (business logic)
        sort_key = None
        if query.sort_by == "assigned_at" or query.sort_by == "created_at":
            sort_key = lambda x: x[0].created_at
        elif query.sort_by == "updated_at":
            sort_key = lambda x: x[0].updated_at
        elif query.sort_by == "access_type":
            sort_key = lambda x: x[0].access_type
        
        if sort_key:
            normalized_assignments.sort(key=sort_key, reverse=(query.sort_order.lower() == "desc"))
        else:
            # Default sort by created_at desc
            normalized_assignments.sort(key=lambda x: x[0].created_at, reverse=True)
        
        # Apply pagination (business logic)
        offset = (query.page - 1) * query.page_size
        paginated_assignments = normalized_assignments[offset:offset + query.page_size]
        
        # Convert to response schemas (business logic transformation)
        items = [
            self._map_assignment_to_read(assignment, user_obj, family_id_val)
            for assignment, user_obj, family_id_val in paginated_assignments
        ]
        
        total_pages = calculate_total_pages(total, query.page_size)
        
        # Build pagination URLs (business logic in service)
        base_url = f"/v1/documents/{document_id}/assignments"
        query_params = {
            "access_type": query.access_type,
            "sort_by": query.sort_by,
            "sort_order": query.sort_order,
            "page_size": str(query.page_size),
        }
        next_page, prev_page = build_pagination_urls(
            base_url, query.page, total_pages, query_params
        )
        
        result = DocumentAssignmentPaginatedResponse(
            items=items,
            total=total,
            page=query.page,
            page_size=query.page_size,
            total_pages=total_pages,
            next_page=next_page,
            prev_page=prev_page,
        )
        
        # Generate ETag from document's updated_at (business logic)
        etag = generate_etag(document.updated_at)
        last_modified = format_last_modified(document.updated_at)
        
        # Check If-None-Match (business logic validation in service)
        if if_none_match and if_none_match == etag:
            # Return 304 Not Modified (business logic decision in service)
            return ServiceResponse(
                data=None,  # 304 has no body
                status_code=status.HTTP_304_NOT_MODIFIED,
                headers={
                    "ETag": etag,
                    "Last-Modified": last_modified,
                },
                response_type="fastapi",  # Router uses this to return FastAPI Response
            )
        
        # Return ServiceResponse with ETag headers (business logic in service)
        return ServiceResponse(
            data=result,
            status_code=status.HTTP_200_OK,
            headers={
                "ETag": etag,
                "Last-Modified": last_modified,
            },
        )
    
    async def create_assignments_bulk(
        self,
        document_id: UUID,
        data: DocumentAssignmentCreate,
        user: User,
        token: Optional[str] = None,
    ) -> ServiceResponse[BulkAssignmentResponse]:
        """Create bulk assignments with business rules validation (business logic in service)."""
        # Extract role and family_id from token (business logic)
        user_role, family_id = self._get_user_role_and_family(token)
        
        # Validate family access (business logic)
        family_id = self._validate_family_access(user_role, family_id)
        
        # Get document (business logic)
        document = await self.repository.get_by_id(document_id)
        if not document:
            raise DocumentNotFound(str(document_id))
        
        # Check family access (business logic)
        if document.family_id != family_id:
            raise DocumentNotFound(str(document_id))
        
        # Check assignment permission (owner or familyadmin) - business logic
        await self._check_assignment_permission(document, user.id, user_role)
        
        # Check document is not soft-deleted (business logic)
        if document.is_del:
            from src.documents.exceptions import ValidationError
            from src.documents.constants import (
                ERROR_CANNOT_ASSIGN_TO_DELETED_DOCUMENT,
                ERROR_CODE_VALIDATION_ERROR,
            )
            raise ValidationError(
                message=ERROR_CANNOT_ASSIGN_TO_DELETED_DOCUMENT,
                error_code=ERROR_CODE_VALIDATION_ERROR,
                details=[{"field": "document", "issue": ERROR_CANNOT_ASSIGN_TO_DELETED_DOCUMENT}],
            )
        
        # Import UserRepository to check user existence and family membership
        from src.users.repository import UserRepository
        from src.users.exceptions import UserNotFound as UserNotFoundException
        user_repository = UserRepository(self.session)
        
        created_assignments = []
        updated_assignments = []
        failed_assignments = []
        
        # Process each assignment (business logic)
        for assignment_item in data.assignments:
            try:
                # Check if user exists and is active (business logic)
                target_user = await user_repository.get_by_id(assignment_item.user_id)
                if not target_user or target_user.is_del:
                    failed_assignments.append({
                        "user_id": str(assignment_item.user_id),
                        "error": "User not found or has been deleted",
                    })
                    continue
                
                # Check self-assignment (business logic)
                if assignment_item.user_id == document.owner_id:
                    failed_assignments.append({
                        "user_id": str(assignment_item.user_id),
                        "error": "Cannot assign access to document owner",
                    })
                    continue
                
                # Check user is in same family (business logic)
                # Get user's role in the document's family
                from src.roles.repository import RoleRepository
                role_repository = RoleRepository(self.session)
                user_role_info = await role_repository.get_user_role_by_user_and_family(
                    assignment_item.user_id, family_id
                )
                
                if not user_role_info:
                    raise UserNotInFamily(str(assignment_item.user_id))
                
                # Check if assignment already exists (business logic)
                existing_assignment = await self.assignment_repository.get_by_document_and_user(
                    document_id, assignment_item.user_id
                )
                
                if existing_assignment:
                    # Update existing assignment (business logic)
                    # Editor overrides viewer, viewer doesn't downgrade editor
                    if assignment_item.access_type == ACCESS_TYPE_EDITOR:
                        # Always upgrade to editor
                        existing_assignment.access_type = ACCESS_TYPE_EDITOR
                    elif assignment_item.access_type == ACCESS_TYPE_VIEWER:
                        # Only update if current is viewer (don't downgrade editor)
                        if existing_assignment.access_type == ACCESS_TYPE_VIEWER:
                            existing_assignment.access_type = ACCESS_TYPE_VIEWER
                        # If current is editor, keep editor (no change)
                    
                    existing_assignment.owner_id = user.id
                    existing_assignment.updated_by = user.id
                    
                    assignment, user_obj, family_id_val = await self.assignment_repository.update(existing_assignment)
                    assignment_read = self._map_assignment_to_read(assignment, user_obj, family_id_val)
                    updated_assignments.append(assignment_read)
                else:
                    # Create new assignment (business logic)
                    new_assignment = DocumentAssign(
                        document_id=document_id,
                        owner_id=user.id,
                        assign_to=assignment_item.user_id,
                        access_type=assignment_item.access_type,
                        created_by=user.id,
                        updated_by=user.id,
                    )
                    
                    assignment, user_obj, family_id_val = await self.assignment_repository.create(new_assignment)
                    assignment_read = self._map_assignment_to_read(assignment, user_obj, family_id_val)
                    created_assignments.append(assignment_read)
            
            except UserNotInFamily:
                failed_assignments.append({
                    "user_id": str(assignment_item.user_id),
                    "error": "User is not in the same Family as the document",
                })
            except Exception as e:
                failed_assignments.append({
                    "user_id": str(assignment_item.user_id),
                    "error": str(e),
                })
        
        # Return ServiceResponse with bulk result (business logic)
        result = BulkAssignmentResponse(
            created=created_assignments,
            updated=updated_assignments,
            failed=failed_assignments,
        )
        
        return ServiceResponse(
            data=result,
            status_code=status.HTTP_201_CREATED,
        )
    
    async def update_assignment(
        self,
        document_id: UUID,
        user_id: UUID,
        data: DocumentAssignmentUpdate,
        user: User,
        token: Optional[str] = None,
        if_match: Optional[str] = None,
    ) -> ServiceResponse[DocumentAssignmentRead]:
        """Update assignment with ETag validation (business logic in service)."""
        # Extract role and family_id from token (business logic)
        user_role, family_id = self._get_user_role_and_family(token)
        
        # Validate family access (business logic)
        family_id = self._validate_family_access(user_role, family_id)
        
        # Get document (business logic)
        document = await self.repository.get_by_id(document_id)
        if not document:
            raise DocumentNotFound(str(document_id))
        
        # Check family access (business logic)
        if document.family_id != family_id:
            raise DocumentNotFound(str(document_id))
        
        # Check assignment permission (owner or familyadmin) - business logic
        await self._check_assignment_permission(document, user.id, user_role)
        
        # Check self-assignment (business logic)
        if user_id == document.owner_id:
            raise SelfAssignmentBlocked()
        
        # Get existing assignment (business logic)
        assignment_tuple = await self.assignment_repository.get_by_document_and_user_with_user(
            document_id, user_id
        )
        if not assignment_tuple:
            raise AssignmentNotFound(str(user_id))
        
        assignment, user_obj, family_id_val = assignment_tuple
        
        # Validate ETag (business logic validation in service)
        current_etag = generate_etag(assignment.updated_at)
        if if_match and if_match != current_etag:
            raise ETagMismatch()
        
        # Update assignment (business logic)
        # Editor overrides viewer, viewer doesn't downgrade editor
        if data.access_type == ACCESS_TYPE_EDITOR:
            # Always upgrade to editor
            assignment.access_type = ACCESS_TYPE_EDITOR
        elif data.access_type == ACCESS_TYPE_VIEWER:
            # Only update if current is viewer (don't downgrade editor)
            if assignment.access_type == ACCESS_TYPE_VIEWER:
                assignment.access_type = ACCESS_TYPE_VIEWER
            # If current is editor, keep editor (no change - idempotent)
        
        assignment.owner_id = user.id
        assignment.updated_by = user.id
        
        # Save update
        updated_assignment, updated_user, updated_family_id = await self.assignment_repository.update(assignment)
        
        # Convert to response schema
        result = self._map_assignment_to_read(updated_assignment, updated_user, updated_family_id)
        
        # Generate ETag from updated assignment (business logic)
        etag = generate_etag(updated_assignment.updated_at)
        
        # Return ServiceResponse with ETag headers (business logic in service)
        return ServiceResponse(
            data=result,
            status_code=status.HTTP_200_OK,
            headers={
                "ETag": etag,
            },
        )
    
    async def delete_assignment(
        self,
        document_id: UUID,
        user_id: UUID,
        user: User,
        token: Optional[str] = None,
        if_match: Optional[str] = None,
    ) -> None:
        """Delete assignment with ETag validation (business logic in service)."""
        # Extract role and family_id from token (business logic)
        user_role, family_id = self._get_user_role_and_family(token)
        
        # Validate family access (business logic)
        family_id = self._validate_family_access(user_role, family_id)
        
        # Get document (business logic)
        document = await self.repository.get_by_id(document_id)
        if not document:
            raise DocumentNotFound(str(document_id))
        
        # Check family access (business logic)
        if document.family_id != family_id:
            raise DocumentNotFound(str(document_id))
        
        # Check assignment permission (owner or familyadmin) - business logic
        await self._check_assignment_permission(document, user.id, user_role)
        
        # Get existing assignment (business logic)
        assignment = await self.assignment_repository.get_by_document_and_user(
            document_id, user_id
        )
        if not assignment:
            raise AssignmentNotFound(str(user_id))
        
        # Validate ETag if provided (business logic validation in service)
        if if_match:
            current_etag = generate_etag(assignment.updated_at)
            if if_match != current_etag:
                raise ETagMismatch()
        
        # Soft delete assignment (business logic)
        await self.assignment_repository.delete(assignment, user.id)

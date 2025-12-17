"""Family service."""
from uuid import UUID
from typing import Optional
from datetime import datetime, timezone
from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession
from src.response import ServiceResponse
from src.families.repository import FamilyRepository
from src.families.schemas import (
    FamilyCreate,
    FamilyUpdate,
    FamilyRead,
    FamilyListQuery,
    FamilyPaginatedResponse,
)
from src.families.exceptions import (
    FamilyNotFound,
    DuplicateFamilyName,
    FamilySoftDeleted,
    FamilyAlreadySoftDeleted,
    CannotUpdateSoftDeletedFamily,
)
from src.families.constants import (
    FAMILY_STATUS_API_ACTIVE,
    FAMILY_STATUS_API_SOFT_DELETED,
)
from src.pagination import calculate_total_pages
from src.families.models import Family
from src.utils import generate_etag, format_last_modified
from src.exceptions import PreconditionRequiredError, PreconditionFailedError


class FamilyService:
    """Service for family business logic."""
    
    def __init__(self, session: AsyncSession):
        self.repository = FamilyRepository(session)
        self.session = session
    
    def _map_status_to_api(self, family: Family) -> str:
        """Map database status to API status format."""
        if family.is_del:
            return FAMILY_STATUS_API_SOFT_DELETED
        return FAMILY_STATUS_API_ACTIVE
    
    def _family_to_read_schema(self, family: Family) -> FamilyRead:
        """Convert Family model to FamilyRead schema."""
        result = FamilyRead(
            id=family.id,
            name=family.name,
            status=self._map_status_to_api(family),
            is_del=family.is_del,
            created_at=family.created_at,
            created_by=family.created_by,
            updated_at=family.updated_at,
            updated_by=family.updated_by,
            deleted_at=family.deleted_at,
            deleted_by=family.deleted_by,
        )
        # Attach ETag and Last-Modified for router to set headers
        result._etag = generate_etag(family.updated_at)
        result._last_modified = format_last_modified(family.updated_at)
        return result
    
    async def list_families(
        self,
        query: FamilyListQuery,
    ) -> FamilyPaginatedResponse:
        """List families with pagination, filtering, and sorting."""
        items, total = await self.repository.list_with_pagination(
            page=query.page,
            page_size=query.page_size,
            status_filter=query.status,
            sort_by=query.sort_by,
            sort_order=query.sort_order,
        )
        
        # Convert to response schemas
        family_reads = [self._family_to_read_schema(family) for family in items]
        
        # Calculate pagination metadata
        total_pages = calculate_total_pages(total, query.page_size)
        
        # Build next_page and prev_page URLs
        next_page = None
        if query.page < total_pages:
            next_page = f"/v1/families?page={query.page + 1}&page_size={query.page_size}&sort_by={query.sort_by}&sort_order={query.sort_order}"
            if query.status:
                next_page += f"&status={query.status}"
        
        prev_page = None
        if query.page > 1:
            prev_page = f"/v1/families?page={query.page - 1}&page_size={query.page_size}&sort_by={query.sort_by}&sort_order={query.sort_order}"
            if query.status:
                prev_page += f"&status={query.status}"
        
        return FamilyPaginatedResponse(
            items=family_reads,
            total=total,
            page=query.page,
            page_size=query.page_size,
            total_pages=total_pages,
            next_page=next_page,
            prev_page=prev_page,
        )
    
    async def create_family(
        self,
        data: FamilyCreate,
        current_user_id: UUID,
    ) -> FamilyRead:
        """Create a new family."""
        # Check for duplicate name (case-insensitive)
        existing = await self.repository.get_by_name(data.name)
        if existing:
            raise DuplicateFamilyName(data.name)
        
        # Create family
        family = Family(
            name=data.name,
            status="active",  # Database uses lowercase
            is_del=False,
            created_by=current_user_id,
            updated_by=current_user_id,
        )
        
        family = await self.repository.create(family)
        return self._family_to_read_schema(family)
    
    async def get_family_by_id(
        self,
        family_id: UUID,
        if_none_match: Optional[str] = None,
    ) -> ServiceResponse[FamilyRead]:
        """Get family by ID with ETag support (business logic in service)."""
        family = await self.repository.get_by_id(family_id)
        
        if not family:
            raise FamilyNotFound(str(family_id))
        
        # If soft-deleted, return 404 (not accessible)
        if family.is_del:
            raise FamilyNotFound(str(family_id))
        
        # Generate ETag (business logic in service)
        etag = generate_etag(family.updated_at)
        last_modified = format_last_modified(family.updated_at)
        
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
        
        # Return resource with ETag attached for router to set headers
        family_read = self._family_to_read_schema(family)
        return ServiceResponse(
            data=family_read,
            status_code=status.HTTP_200_OK,
            headers={
                "ETag": family_read._etag,
                "Last-Modified": family_read._last_modified,
            },
            response_type="standard",  # Router uses this to return StandardResponse
        )
    
    async def update_family(
        self,
        family_id: UUID,
        data: FamilyUpdate,
        current_user_id: UUID,
        if_match: Optional[str] = None,
    ) -> ServiceResponse[FamilyRead]:
        """Update family name with ETag validation (business logic in service)."""
        # Get current resource for ETag validation
        current_family = await self.repository.get_by_id(family_id)
        
        if not current_family:
            raise FamilyNotFound(str(family_id))
        
        # Cannot update if soft-deleted
        if current_family.is_del:
            raise CannotUpdateSoftDeletedFamily()
        
        # ETag validation (business logic in service)
        if not if_match:
            raise PreconditionRequiredError(
                message="If-Match header required for update operations.",
                details=[{"field": "If-Match", "issue": "If-Match header is required"}],
            )
        
        current_etag = generate_etag(current_family.updated_at)
        if if_match != current_etag:
            raise PreconditionFailedError(
                message="Resource version mismatch. The resource was modified by another user.",
                details=[{"field": "etag", "issue": "Resource has been modified since retrieval. Please fetch the latest version and retry."}],
            )
        
        # Check for duplicate name (case-insensitive, excluding current family)
        existing = await self.repository.get_by_name(data.name)
        if existing and existing.id != family_id:
            raise DuplicateFamilyName(data.name)
        
        # Update family
        current_family.name = data.name
        current_family.updated_by = current_user_id
        # updated_at is set automatically by onupdate=func.now()
        
        family = await self.repository.update(current_family)
        family_read = self._family_to_read_schema(family)
        
        # Return ServiceResponse with ETag headers (business logic in service)
        return ServiceResponse(
            data=family_read,
            status_code=status.HTTP_200_OK,
            headers={
                "ETag": family_read._etag,
                "Last-Modified": family_read._last_modified,
            },
        )
    
    async def soft_delete_family(
        self,
        family_id: UUID,
        current_user_id: UUID,
        if_match: Optional[str] = None,
    ) -> ServiceResponse[FamilyRead]:
        """Soft delete family with cascade to users and ETag validation (business logic in service)."""
        # Get current resource for ETag validation
        current_family = await self.repository.get_by_id(family_id)
        
        if not current_family:
            raise FamilyNotFound(str(family_id))
        
        # Cannot soft-delete if already soft-deleted
        if current_family.is_del:
            raise FamilyAlreadySoftDeleted()
        
        # ETag validation (business logic in service)
        if not if_match:
            raise PreconditionRequiredError(
                message="If-Match header required for delete operations.",
                details=[{"field": "If-Match", "issue": "If-Match header is required"}],
            )
        
        current_etag = generate_etag(current_family.updated_at)
        if if_match != current_etag:
            raise PreconditionFailedError(
                message="Resource version mismatch. The resource was modified by another user.",
                details=[{"field": "etag", "issue": "Resource has been modified since retrieval. Please fetch the latest version and retry."}],
            )
        
        # Soft delete family
        current_family.is_del = True
        current_family.status = "inactive"  # Database uses lowercase
        current_family.deleted_at = datetime.now(timezone.utc)
        current_family.deleted_by = current_user_id
        current_family.updated_by = current_user_id
        # updated_at is set automatically by onupdate=func.now()
        
        # TODO: Cascade soft-delete to users and documents
        # This will be handled by the document feature (F-003) and user management
        # For now, we just soft-delete the family
        
        family = await self.repository.soft_delete(current_family)
        family_read = self._family_to_read_schema(family)
        
        # Return ServiceResponse with ETag headers (business logic in service)
        return ServiceResponse(
            data=family_read,
            status_code=status.HTTP_200_OK,
            headers={
                "ETag": family_read._etag,
                "Last-Modified": family_read._last_modified,
            },
        )

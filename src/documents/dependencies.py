"""Document dependencies."""
from uuid import UUID
from typing import Optional
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import get_session
from src.documents.service import DocumentService
from src.users.models import User


# API Dependency Pattern (RULE 8.6.7)
class DocumentApiDep:
    """API dependency for document endpoints."""

    def __init__(self, session: AsyncSession):
        self.service = DocumentService(session)
        self.session = session
    
    async def create_document(
        self, data, user: User, token: Optional[str] = None,
        family_id: Optional[UUID] = None,
        file_content: Optional[bytes] = None, content_type: Optional[str] = None
    ):
        """Create document with metadata and optionally upload file."""
        return await self.service.create_document(
            data, user, token=token, family_id=family_id,
            file_content=file_content,
            content_type=content_type
        )
    
    async def get_document_by_id(
        self,
        document_id: UUID,
        user: User,
        token: Optional[str] = None,
        if_none_match: Optional[str] = None,
    ):
        """Get document by ID with ETag support."""
        return await self.service.get_document_by_id(
            document_id, user, token=token, if_none_match=if_none_match
        )
    
    async def update_document(
        self,
        document_id: UUID,
        data,
        user: User,
        token: Optional[str] = None,
        if_match: Optional[str] = None,
    ):
        """Update document metadata with ETag validation."""
        return await self.service.update_document(
            document_id, data, user, token=token, if_match=if_match
        )
    
    async def delete_document(
        self,
        document_id: UUID,
        user: User,
        token: Optional[str] = None,
        if_match: Optional[str] = None,
    ):
        """Soft delete document with ETag validation."""
        return await self.service.delete_document(
            document_id, user, token=token, if_match=if_match
        )
    
    async def list_documents(self, query, user: User, token: Optional[str] = None):
        """List documents with pagination, filtering, search, and sorting."""
        return await self.service.list_documents(query, user, token=token)
    
    async def replace_file(
        self,
        document_id: UUID,
        file_content: bytes,
        content_type: str,
        user: User,
        token: Optional[str] = None,
        if_match: Optional[str] = None,
    ):
        """Replace existing PDF file with ETag validation."""
        return await self.service.replace_file(
            document_id, file_content, content_type, user, token=token,
            if_match=if_match
        )
    
    async def get_file(
        self,
        document_id: UUID,
        user: User,
        token: Optional[str] = None,
        if_none_match: Optional[str] = None,
        mode: str = "preview",
    ):
        """Get document file with ETag support."""
        return await self.service.get_file(
            document_id, user, token=token, if_none_match=if_none_match, mode=mode
        )


def get_document_api(session: AsyncSession = Depends(get_session)) -> DocumentApiDep:
    """Dependency function to get DocumentApiDep instance."""
    return DocumentApiDep(session)


# ==================== Document Assignment Dependencies ====================

class DocumentAssignmentApiDep:
    """API dependency for document assignment endpoints."""

    def __init__(self, session: AsyncSession):
        self.service = DocumentService(session)
        self.session = session
    
    async def list_assignments(
        self,
        document_id: UUID,
        query,
        user: User,
        token: Optional[str] = None,
        if_none_match: Optional[str] = None,
    ):
        """List assignments for a document with normalization."""
        return await self.service.list_assignments(
            document_id, query, user, token=token, if_none_match=if_none_match
        )
    
    async def create_assignments_bulk(
        self,
        document_id: UUID,
        data,
        user: User,
        token: Optional[str] = None,
    ):
        """Create bulk assignments with business rules validation."""
        return await self.service.create_assignments_bulk(
            document_id, data, user, token=token
        )
    
    async def update_assignment(
        self,
        document_id: UUID,
        user_id: UUID,
        data,
        user: User,
        token: Optional[str] = None,
        if_match: Optional[str] = None,
    ):
        """Update assignment with ETag validation."""
        return await self.service.update_assignment(
            document_id, user_id, data, user, token=token, if_match=if_match
        )
    
    async def delete_assignment(
        self,
        document_id: UUID,
        user_id: UUID,
        user: User,
        token: Optional[str] = None,
        if_match: Optional[str] = None,
    ):
        """Delete assignment with ETag validation."""
        return await self.service.delete_assignment(
            document_id, user_id, user, token=token, if_match=if_match
        )


def get_document_assignment_api(
    session: AsyncSession = Depends(get_session)
) -> DocumentAssignmentApiDep:
    """Dependency function to get DocumentAssignmentApiDep instance."""
    return DocumentAssignmentApiDep(session)

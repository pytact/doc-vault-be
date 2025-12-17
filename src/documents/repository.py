"""Document repository."""
from uuid import UUID
from typing import Optional, List, Tuple
from datetime import date, datetime, timezone
from sqlalchemy import select, func, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from src.documents.models import Document, DocumentAssign
from src.taxonomy.models import Category, Subcategory
from src.users.models import User
from src.roles.models import UserRole


class DocumentRepository:
    """Repository for document database operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_by_id(
        self, document_id: UUID
    ) -> Optional[Document]:
        """Get document by ID (excludes soft-deleted)."""
        result = await self.session.execute(
            select(Document)
            .where(
                Document.id == document_id,
                Document.is_del == False,
            )
        )
        return result.scalar_one_or_none()
    
    async def get_by_id_with_taxonomy(
        self, document_id: UUID
    ) -> Optional[Document]:
        """Get document by ID (taxonomy can be joined if needed)."""
        # Note: Category and Subcategory can be joined in queries when needed
        # For now, return basic document - taxonomy validation happens in service
        return await self.get_by_id(document_id)
    
    async def create(self, document: Document) -> Document:
        """Create document."""
        self.session.add(document)
        await self.session.commit()
        await self.session.refresh(document)
        return document
    
    async def update(self, document: Document) -> Document:
        """Update document."""
        await self.session.commit()
        await self.session.refresh(document)
        return document
    
    async def soft_delete(self, document_id: UUID, deleted_by: UUID) -> None:
        """Soft delete document."""
        document = await self.get_by_id(document_id)
        if document:
            document.is_del = True
            document.deleted_at = datetime.now(timezone.utc)
            document.deleted_by = deleted_by
            await self.session.commit()
    
    async def get_document_assign(
        self, document_id: UUID, assign_to: UUID
    ) -> Optional[DocumentAssign]:
        """Get active document assignment for user."""
        result = await self.session.execute(
            select(DocumentAssign)
            .where(
                DocumentAssign.document_id == document_id,
                DocumentAssign.assign_to == assign_to,
                DocumentAssign.is_del == False,
                DocumentAssign.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()
    
    async def check_category_subcategory_pair(
        self, category_id: UUID, subcategory_id: UUID
    ) -> bool:
        """Check if subcategory belongs to category."""
        result = await self.session.execute(
            select(Subcategory)
            .where(
                Subcategory.id == subcategory_id,
                Subcategory.category_id == category_id,
                Subcategory.is_del == False,
                Subcategory.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none() is not None
    
    async def document_exists_for_user(
        self, owner_id: UUID, family_id: UUID, category_id: UUID, subcategory_id: UUID
    ) -> bool:
        """Check if a document already exists for the user in the specified category and subcategory."""
        result = await self.session.execute(
            select(Document)
            .where(
                Document.owner_id == owner_id,
                Document.family_id == family_id,
                Document.category_id == category_id,
                Document.subcategory_id == subcategory_id,
                Document.is_del == False,
            )
        )
        return result.scalar_one_or_none() is not None
    
    async def list_with_pagination(
        self,
        family_id: UUID,
        user_id: UUID,
        user_role: str,
        page: int,
        page_size: int,
        category_id: Optional[UUID] = None,
        subcategory_id: Optional[UUID] = None,
        owner_user_id: Optional[UUID] = None,
        expiry_date: Optional[date] = None,
        search: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> Tuple[List[Document], int]:
        """List documents with pagination, filtering, search, and sorting.
        
        Returns documents accessible to the user:
        - FamilyAdmin: All documents in family
        - Owner: Own documents + shared documents
        - Editor/Viewer: Assigned documents only
        """
        # Build base query
        query = select(Document).where(
            Document.family_id == family_id,
            Document.is_del == False,
        )
        
        # Apply permission filtering based on user role
        if user_role == "familyadmin":
            # FamilyAdmin sees all documents in family (no additional filter)
            pass
        else:
            # Member/Editor/Viewer: Own documents OR shared documents
            # Get list of document IDs where user is assigned
            assigned_doc_ids_query = select(DocumentAssign.document_id).where(
                DocumentAssign.assign_to == user_id,
                DocumentAssign.is_del == False,
                DocumentAssign.deleted_at.is_(None),
            )
            
            # Filter: owner_id == user_id OR document_id IN assigned_doc_ids
            query = query.where(
                or_(
                    Document.owner_id == user_id,
                    Document.id.in_(assigned_doc_ids_query),
                )
            )
        
        # Apply filters
        if category_id:
            query = query.where(Document.category_id == category_id)
        
        if subcategory_id:
            query = query.where(Document.subcategory_id == subcategory_id)
        
        if owner_user_id:
            query = query.where(Document.owner_id == owner_user_id)
        
        if expiry_date:
            query = query.where(Document.expiry_date == expiry_date)
        
        # Apply search (title + category/subcategory names)
        if search:
            # Create subqueries for category and subcategory names
            # Join with Category and Subcategory for search
            query = query.join(
                Category, Document.category_id == Category.id
            ).join(
                Subcategory, Document.subcategory_id == Subcategory.id
            ).where(
                or_(
                    Document.title.ilike(f"%{search}%"),
                    Category.name.ilike(f"%{search}%"),
                    Subcategory.name.ilike(f"%{search}%"),
                )
            )
        
        # Count total (before pagination)
        count_query = select(func.count()).select_from(query.subquery())
        count_result = await self.session.execute(count_query)
        total = count_result.scalar() or 0
        
        # Apply sorting
        sort_column = None
        if sort_by == "created_at":
            sort_column = Document.created_at
        elif sort_by == "updated_at":
            sort_column = Document.updated_at
        elif sort_by == "title":
            sort_column = Document.title
        elif sort_by == "expiry_date":
            sort_column = Document.expiry_date
        
        if sort_column:
            if sort_order.lower() == "asc":
                query = query.order_by(sort_column.asc())
            else:
                query = query.order_by(sort_column.desc())
        else:
            # Default sort
            query = query.order_by(Document.created_at.desc())
        
        # Apply pagination
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)
        
        # Execute query
        result = await self.session.execute(query)
        documents = result.scalars().all()
        
        return list(documents), total


class DocumentAssignmentRepository:
    """Repository for document assignment database operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_by_document_and_user(
        self, document_id: UUID, user_id: UUID
    ) -> Optional[DocumentAssign]:
        """Get active assignment by document ID and user ID."""
        result = await self.session.execute(
            select(DocumentAssign)
            .where(
                DocumentAssign.document_id == document_id,
                DocumentAssign.assign_to == user_id,
                DocumentAssign.is_del == False,
                DocumentAssign.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()
    
    async def list_by_document(
        self,
        document_id: UUID,
        page: int,
        page_size: int,
        access_type: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> Tuple[List[Tuple[DocumentAssign, User, Optional[UUID]]], int]:
        """List all active assignments for a document with pagination and filtering.
        
        Returns tuples of (DocumentAssign, User, Optional[family_id]) for each assignment.
        Raw assignments (not normalized - editor overrides viewer logic in service).
        family_id comes from UserRole.
        """
        # Build base query with join to User and UserRole (to get family_id)
        query = (
            select(DocumentAssign, User, UserRole.family_id)
            .join(User, DocumentAssign.assign_to == User.id)
            .outerjoin(UserRole, and_(
                User.id == UserRole.user_id,
                UserRole.is_del == False,
                UserRole.deleted_at.is_(None),
            ))
            .where(
                DocumentAssign.document_id == document_id,
                DocumentAssign.is_del == False,
                DocumentAssign.deleted_at.is_(None),
                User.is_del == False,  # Only active users
            )
        )
        
        # Apply access_type filter
        if access_type:
            query = query.where(DocumentAssign.access_type == access_type)
        
        # Count total (before pagination)
        count_query = select(func.count()).select_from(query.subquery())
        count_result = await self.session.execute(count_query)
        total = count_result.scalar() or 0
        
        # Apply sorting
        sort_column = None
        if sort_by == "assigned_at" or sort_by == "created_at":
            sort_column = DocumentAssign.created_at
        elif sort_by == "updated_at":
            sort_column = DocumentAssign.updated_at
        elif sort_by == "access_type":
            sort_column = DocumentAssign.access_type
        
        if sort_column:
            if sort_order.lower() == "asc":
                query = query.order_by(sort_column.asc())
            else:
                query = query.order_by(sort_column.desc())
        else:
            # Default sort
            query = query.order_by(DocumentAssign.created_at.desc())
        
        # Apply pagination
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)
        
        # Execute query
        result = await self.session.execute(query)
        rows = result.all()
        
        # Return list of tuples (DocumentAssign, User, Family)
        assignments = [(row[0], row[1], row[2]) for row in rows]
        
        return assignments, total
    
    async def create(self, assignment: DocumentAssign) -> Tuple[DocumentAssign, User, Optional[UUID]]:
        """Create assignment and return with user and family_id."""
        self.session.add(assignment)
        await self.session.commit()
        await self.session.refresh(assignment)
        
        # Get user and family_id (via UserRole)
        user_result = await self.session.execute(
            select(User, UserRole.family_id)
            .outerjoin(UserRole, and_(
                User.id == UserRole.user_id,
                UserRole.is_del == False,
                UserRole.deleted_at.is_(None),
            ))
            .where(
                User.id == assignment.assign_to,
                User.is_del == False,
            )
        )
        user_row = user_result.first()
        if user_row:
            return (assignment, user_row[0], user_row[1])
        # Fallback: get user only
        user = await self.session.get(User, assignment.assign_to)
        return (assignment, user, None)
    
    async def update(self, assignment: DocumentAssign) -> Tuple[DocumentAssign, User, Optional[UUID]]:
        """Update assignment and return with user and family_id."""
        await self.session.commit()
        await self.session.refresh(assignment)
        
        # Get user and family_id (via UserRole)
        user_result = await self.session.execute(
            select(User, UserRole.family_id)
            .outerjoin(UserRole, and_(
                User.id == UserRole.user_id,
                UserRole.is_del == False,
                UserRole.deleted_at.is_(None),
            ))
            .where(
                User.id == assignment.assign_to,
                User.is_del == False,
            )
        )
        user_row = user_result.first()
        if user_row:
            return (assignment, user_row[0], user_row[1])
        # Fallback: get user only
        user = await self.session.get(User, assignment.assign_to)
        return (assignment, user, None)
    
    async def delete(self, assignment: DocumentAssign, deleted_by: UUID) -> None:
        """Soft delete assignment."""
        assignment.is_del = True
        assignment.deleted_at = datetime.now(timezone.utc)
        assignment.deleted_by = deleted_by
        await self.session.commit()
    
    async def get_all_by_document(
        self, document_id: UUID
    ) -> List[Tuple[DocumentAssign, User, Optional[UUID]]]:
        """Get all active assignments for a document with user and family_id (for normalization logic)."""
        result = await self.session.execute(
            select(DocumentAssign, User, UserRole.family_id)
            .join(User, DocumentAssign.assign_to == User.id)
            .outerjoin(UserRole, and_(
                User.id == UserRole.user_id,
                UserRole.is_del == False,
                UserRole.deleted_at.is_(None),
            ))
            .where(
                DocumentAssign.document_id == document_id,
                DocumentAssign.is_del == False,
                DocumentAssign.deleted_at.is_(None),
                User.is_del == False,  # Only active users
            )
        )
        rows = result.all()
        return [(row[0], row[1], row[2]) for row in rows]
    
    async def get_by_document_and_user_with_user(
        self, document_id: UUID, user_id: UUID
    ) -> Optional[Tuple[DocumentAssign, User, Optional[UUID]]]:
        """Get active assignment by document ID and user ID with user and family_id."""
        result = await self.session.execute(
            select(DocumentAssign, User, UserRole.family_id)
            .join(User, DocumentAssign.assign_to == User.id)
            .outerjoin(UserRole, and_(
                User.id == UserRole.user_id,
                UserRole.is_del == False,
                UserRole.deleted_at.is_(None),
            ))
            .where(
                DocumentAssign.document_id == document_id,
                DocumentAssign.assign_to == user_id,
                DocumentAssign.is_del == False,
                DocumentAssign.deleted_at.is_(None),
                User.is_del == False,  # Only active users
            )
        )
        row = result.first()
        if row:
            return (row[0], row[1], row[2])
        return None

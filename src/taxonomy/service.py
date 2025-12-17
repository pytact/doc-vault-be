"""Taxonomy service."""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import status
from src.taxonomy.repository import TaxonomyRepository
from src.taxonomy.schemas import (
    SubcategoryRead,
    CategoryRead,
    TaxonomyData,
    TaxonomyContainer,
)
from src.taxonomy.exceptions import TaxonomyEmpty
from src.taxonomy.constants import SUCCESS_TAXONOMY_RETRIEVED
from src.response import ServiceResponse
from src.utils import generate_etag, format_last_modified


class TaxonomyService:
    """Service for taxonomy business logic."""
    
    def __init__(self, session: AsyncSession):
        self.repository = TaxonomyRepository(session)
        self.session = session
    
    async def get_taxonomy(
        self,
        if_none_match: Optional[str] = None,
    ) -> ServiceResponse[TaxonomyData]:
        """Get complete taxonomy including all categories and subcategories with ETag support.
        
        Args:
            if_none_match: Optional If-None-Match header value for cache validation.
        
        Returns:
            ServiceResponse containing TaxonomyData with ETag headers, or 304 Not Modified.
        
        Raises:
            TaxonomyEmpty: If taxonomy is empty (critical system error).
        """
        # Fetch all categories with subcategories (already ordered alphabetically by repository)
        categories = await self.repository.get_all_categories_with_subcategories()
        
        # Business rule: Taxonomy should never be empty (critical system error)
        if not categories:
            raise TaxonomyEmpty()
        
        # Find the latest updated_at from all categories and subcategories for ETag
        latest_updated_at = None
        for category in categories:
            if latest_updated_at is None or category.updated_at > latest_updated_at:
                latest_updated_at = category.updated_at
            for subcategory in category.subcategories:
                if latest_updated_at is None or subcategory.updated_at > latest_updated_at:
                    latest_updated_at = subcategory.updated_at
        
        # Generate ETag from latest updated_at (business logic in service)
        etag = generate_etag(latest_updated_at) if latest_updated_at else None
        last_modified = format_last_modified(latest_updated_at) if latest_updated_at else None
        
        # Check If-None-Match (business logic validation in service)
        if if_none_match and etag:
            # Remove quotes if present
            if_none_match_clean = if_none_match.strip('"')
            if if_none_match_clean == etag:
                # Return 304 Not Modified (business logic decision in service)
                return ServiceResponse(
                    data=None,  # 304 has no body
                    status_code=status.HTTP_304_NOT_MODIFIED,
                    headers={
                        "ETag": f'"{etag}"',
                        "Last-Modified": last_modified,
                    } if last_modified else {
                        "ETag": f'"{etag}"',
                    },
                    response_type="fastapi",  # Router uses this to return FastAPI Response
                )
        
        # Convert to response schemas
        category_reads = []
        for category in categories:
            subcategory_reads = [
                SubcategoryRead(
                    id=subcategory.id,
                    name=subcategory.name,
                )
                for subcategory in category.subcategories
            ]
            
            category_reads.append(
                CategoryRead(
                    id=category.id,
                    name=category.name,
                    subcategories=subcategory_reads,
                )
            )
        
        # Return nested structure matching UI contract with ETag headers
        taxonomy_data = TaxonomyData(
            taxonomy=TaxonomyContainer(
                categories=category_reads
            )
        )
        
        # Return ServiceResponse with ETag headers (business logic in service)
        return ServiceResponse(
            data=taxonomy_data,
            status_code=status.HTTP_200_OK,
            headers={
                "ETag": f'"{etag}"',
                "Last-Modified": last_modified,
            } if last_modified else {
                "ETag": f'"{etag}"',
            },
        )

"""Taxonomy service."""
from sqlalchemy.ext.asyncio import AsyncSession
from src.taxonomy.repository import TaxonomyRepository
from src.taxonomy.schemas import (
    SubcategoryRead,
    CategoryRead,
    TaxonomyData,
    TaxonomyContainer,
)
from src.taxonomy.exceptions import TaxonomyEmpty
from src.taxonomy.constants import SUCCESS_TAXONOMY_RETRIEVED


class TaxonomyService:
    """Service for taxonomy business logic."""
    
    def __init__(self, session: AsyncSession):
        self.repository = TaxonomyRepository(session)
        self.session = session
    
    async def get_taxonomy(
        self,
    ) -> TaxonomyData:
        """Get complete taxonomy including all categories and subcategories.
        
        Returns:
            TaxonomyData containing all categories with their subcategories,
            ordered alphabetically.
        
        Raises:
            TaxonomyEmpty: If taxonomy is empty (critical system error).
        """
        # Fetch all categories with subcategories (already ordered alphabetically by repository)
        categories = await self.repository.get_all_categories_with_subcategories()
        
        # Business rule: Taxonomy should never be empty (critical system error)
        if not categories:
            raise TaxonomyEmpty()
        
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
        
        # Return nested structure matching UI contract
        return TaxonomyData(
            taxonomy=TaxonomyContainer(
                categories=category_reads
            )
        )

"""Taxonomy dependencies."""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import get_session


# API Dependency Pattern (RULE 8.6.7)
class TaxonomyApiDep:
    """API dependency for taxonomy endpoints."""
    
    def __init__(self, session: AsyncSession):
        from src.taxonomy.service import TaxonomyService
        self.service = TaxonomyService(session)
        self.session = session
    
    async def get_taxonomy(self):
        """Get complete taxonomy."""
        return await self.service.get_taxonomy()


def get_taxonomy_api(session: AsyncSession = Depends(get_session)) -> TaxonomyApiDep:
    """Dependency function to get TaxonomyApiDep instance."""
    return TaxonomyApiDep(session)

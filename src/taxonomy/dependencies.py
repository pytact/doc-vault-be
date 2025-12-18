"""Taxonomy dependencies."""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import get_session
from src.taxonomy.service import TaxonomyService


# API Dependency Pattern (RULE 8.6.7)
class TaxonomyApiDep:
    """API dependency for taxonomy endpoints."""
    
    def __init__(self, session: AsyncSession):
        self.service = TaxonomyService(session)
        self.session = session
    
    async def get_taxonomy(self, if_none_match: str | None = None):
        """Get complete taxonomy with ETag support."""
        return await self.service.get_taxonomy(if_none_match=if_none_match)


def get_taxonomy_api(session: AsyncSession = Depends(get_session)) -> TaxonomyApiDep:
    """Dependency function to get TaxonomyApiDep instance."""
    return TaxonomyApiDep(session)

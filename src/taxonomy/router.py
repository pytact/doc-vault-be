"""Taxonomy router."""
from fastapi import APIRouter, Depends, status, Header, Response
from fastapi.responses import Response as FastAPIResponse
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import get_session
from src.schemas import StandardResponse
from src.taxonomy.schemas import TaxonomyData
from src.taxonomy.dependencies import (
    get_taxonomy_api,
    TaxonomyApiDep,
)
from src.taxonomy.documentations.taxonomy_api_doc import TaxonomyApiDocs
from src.auth.dependencies import get_current_user, oauth2_scheme
from src.users.models import User


router = APIRouter(
    prefix="/taxonomy",
    tags=["Taxonomy"],
)


@router.get(
    "",
    response_model=StandardResponse[TaxonomyData],
    status_code=status.HTTP_200_OK,
    summary=TaxonomyApiDocs.get_taxonomy["summary"],
    description=TaxonomyApiDocs.get_taxonomy["description"],
)
async def get_taxonomy(
    current_user: User = Depends(get_current_user),
    api: TaxonomyApiDep = Depends(get_taxonomy_api),
    if_none_match: str | None = Header(None, alias="If-None-Match"),
    response: Response = None,
) -> StandardResponse[TaxonomyData]:
    """Get complete taxonomy including all categories and subcategories."""
    # Delegate to service - business logic in service.py
    result = await api.get_taxonomy()
    
    # TODO: ETag support can be added later if needed for cache validation
    # For now, taxonomy is immutable so ETag is optional
    
    return StandardResponse(
        data=result,
        message="Taxonomy retrieved successfully",
    )

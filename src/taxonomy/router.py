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
) -> StandardResponse[TaxonomyData] | FastAPIResponse:
    """Get complete taxonomy including all categories and subcategories."""
    # Delegate to service - business logic in service.py
    service_response = await api.get_taxonomy(if_none_match=if_none_match)
    
    # Set headers from service response (HTTP concern - header setting)
    for key, value in service_response.headers.items():
        response.headers[key] = value
    
    # Router mechanically returns response based on service response_type (no business logic)
    if service_response.response_type == "fastapi":
        return service_response.to_fastapi_response()
    
    return StandardResponse(
        data=service_response.data,
        message="Taxonomy retrieved successfully",
    )

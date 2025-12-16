"""Taxonomy exceptions."""
from src.exceptions import NotFoundError, InternalServerError
from src.taxonomy.constants import (
    ERROR_CODE_TAXONOMY_NOT_FOUND,
    ERROR_CODE_TAXONOMY_EMPTY,
    ERROR_TAXONOMY_NOT_FOUND,
    ERROR_TAXONOMY_EMPTY,
)


class TaxonomyNotFound(NotFoundError):
    """Taxonomy not found exception."""
    
    def __init__(self):
        super().__init__(
            resource="Taxonomy",
            resource_id=None,
        )


class TaxonomyEmpty(InternalServerError):
    """Taxonomy is empty exception (critical system error)."""
    
    def __init__(self):
        super().__init__(
            message=ERROR_TAXONOMY_EMPTY,
            error_code=ERROR_CODE_TAXONOMY_EMPTY,
            details=[{"field": "taxonomy", "issue": "Taxonomy is empty. This is a critical system error."}],
        )

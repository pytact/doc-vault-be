"""Taxonomy API documentation."""
from typing import ClassVar


class TaxonomyApiDocs:
    """API documentation for Taxonomy endpoints."""
    
    get_taxonomy: ClassVar[dict] = {
        "summary": "Purpose of this API is to retrieve the complete taxonomy of categories and subcategories",
        "description": "Retrieves the full immutable taxonomy including all 15 categories and 78 subcategories. Categories and subcategories are returned in alphabetical order. All authenticated users can access this endpoint. The taxonomy is immutable and shared across all families."
    }

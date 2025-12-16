"""Taxonomy schemas."""
from uuid import UUID
from typing import Optional
from pydantic import BaseModel, ConfigDict


class SubcategoryRead(BaseModel):
    """Subcategory read response schema."""
    id: UUID
    name: str
    
    model_config = ConfigDict(from_attributes=True)


class CategoryRead(BaseModel):
    """Category read response schema."""
    id: UUID
    name: str
    subcategories: list[SubcategoryRead]
    
    model_config = ConfigDict(from_attributes=True)


class TaxonomyContainer(BaseModel):
    """Taxonomy container with categories."""
    categories: list[CategoryRead]
    
    model_config = ConfigDict(from_attributes=True)


class TaxonomyData(BaseModel):
    """Taxonomy data container."""
    taxonomy: TaxonomyContainer
    
    model_config = ConfigDict(from_attributes=True)

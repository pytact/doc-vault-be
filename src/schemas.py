"""Global response schemas."""
from typing import Generic, TypeVar, Optional
from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class ErrorDetail(BaseModel):
    """Error detail item."""
    field: str
    issue: str


class ErrorInfo(BaseModel):
    """Error information."""
    code: str
    details: list[ErrorDetail]


class StandardResponse(BaseModel, Generic[T]):
    """Standard API response wrapper."""
    data: T
    message: str
    
    model_config = ConfigDict(from_attributes=True)


class PagedCollection(BaseModel, Generic[T]):
    """Paginated collection response."""
    items: list[T]
    total: int
    page: int
    page_size: int
    total_pages: int
    
    model_config = ConfigDict(from_attributes=True)


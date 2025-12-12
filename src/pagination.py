"""Pagination utilities."""
from typing import TypeVar
from pydantic import BaseModel

T = TypeVar("T")


class PaginationParams(BaseModel):
    """Pagination parameters."""
    page: int = 1
    page_size: int = 20
    
    def offset(self) -> int:
        """Calculate offset for database query."""
        return (self.page - 1) * self.page_size
    
    def limit(self) -> int:
        """Get limit for database query."""
        return self.page_size


def calculate_total_pages(total: int, page_size: int) -> int:
    """Calculate total number of pages."""
    if total == 0:
        return 0
    return (total + page_size - 1) // page_size


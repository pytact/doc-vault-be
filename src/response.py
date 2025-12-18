"""Response wrapper for service layer to return data with HTTP metadata."""
from typing import Generic, TypeVar, Optional, Union
from fastapi import status
from fastapi.responses import Response as FastAPIResponse, JSONResponse

T = TypeVar('T')


class ServiceResponse(Generic[T]):
    """Service response wrapper that includes HTTP metadata.
    
    This allows service layer to return data with HTTP status codes and headers
    without the router needing business logic to determine response format.
    """
    
    def __init__(
        self,
        data: Optional[T],
        status_code: int = status.HTTP_200_OK,
        headers: Optional[dict[str, str]] = None,
        response_type: str = "standard",  # "standard" or "fastapi"
    ):
        self.data = data
        self.status_code = status_code
        self.headers = headers or {}
        self.response_type = response_type  # Router uses this to decide response format
    
    def to_fastapi_response(self) -> FastAPIResponse:
        """Convert to FastAPI Response for special status codes (e.g., 304)."""
        response = FastAPIResponse(status_code=self.status_code)
        for key, value in self.headers.items():
            response.headers[key] = value
        return response

    def to_standard_response(self, message: str) -> JSONResponse:
        """Convert to StandardResponse format with headers for normal responses."""
        from src.schemas import StandardResponse

        response = JSONResponse(
            status_code=self.status_code,
            content=StandardResponse(data=self.data, message=message).model_dump(mode="json")
        )
        for key, value in self.headers.items():
            response.headers[key] = value
        return response


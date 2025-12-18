"""Global exception classes and handlers."""
import re
from typing import Any
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError, ResponseValidationError
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from asyncpg.exceptions import (
    UniqueViolationError,
    ForeignKeyViolationError,
    NotNullViolationError,
    CheckViolationError,
)
from src.utils import generate_request_id


class AppException(HTTPException):
    """Base application exception."""
    
    def __init__(
        self,
        status_code: int,
        message: str,
        error_code: str | None = None,
        details: list[dict[str, Any]] | None = None,
    ):
        super().__init__(status_code=status_code, detail=message)
        self.message = message
        self.error_code = error_code or "APPLICATION_ERROR"
        self.details = details or []


class BadRequestError(AppException):
    """400 Bad Request error."""
    
    def __init__(
        self,
        message: str,
        error_code: str = "BAD_REQUEST",
        details: list[dict[str, Any]] | None = None,
    ):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            message=message,
            error_code=error_code,
            details=details,
        )


class UnauthenticatedError(AppException):
    """401 Unauthenticated error."""
    
    def __init__(
        self,
        message: str = "Authentication required",
        error_code: str = "UNAUTHENTICATED",
        details: list[dict[str, Any]] | None = None,
    ):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            message=message,
            error_code=error_code,
            details=details,
        )


class ForbiddenError(AppException):
    """403 Forbidden error."""
    
    def __init__(
        self,
        message: str = "Insufficient permissions",
        error_code: str = "FORBIDDEN",
        details: list[dict[str, Any]] | None = None,
    ):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            message=message,
            error_code=error_code,
            details=details,
        )


class NotFoundError(AppException):
    """404 Not Found error."""
    
    def __init__(
        self,
        resource: str,
        resource_id: str | None = None,
        message: str | None = None,
    ):
        if message is None:
            if resource_id:
                message = f"{resource} with id {resource_id} not found"
            else:
                message = f"{resource} not found"
        
        error_code = f"{resource.upper().replace(' ', '_')}_NOT_FOUND"
        details = []
        if resource_id:
            details.append({"field": "id", "issue": resource_id})
        
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            message=message,
            error_code=error_code,
            details=details,
        )


class ConflictError(AppException):
    """409 Conflict error."""
    
    def __init__(
        self,
        message: str,
        error_code: str = "CONFLICT",
        details: list[dict[str, Any]] | None = None,
    ):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            message=message,
            error_code=error_code,
            details=details,
        )


class ValidationError(AppException):
    """422 Validation error."""
    
    def __init__(
        self,
        message: str,
        error_code: str = "VALIDATION_ERROR",
        details: list[dict[str, Any]] | None = None,
    ):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            message=message,
            error_code=error_code,
            details=details,
        )


class PreconditionRequiredError(AppException):
    """428 Precondition Required error."""
    
    def __init__(
        self,
        message: str = "Precondition required",
        error_code: str = "PRECONDITION_REQUIRED",
        details: list[dict[str, Any]] | None = None,
    ):
        super().__init__(
            status_code=status.HTTP_428_PRECONDITION_REQUIRED,
            message=message,
            error_code=error_code,
            details=details,
        )


class PreconditionFailedError(AppException):
    """412 Precondition Failed error."""
    
    def __init__(
        self,
        message: str = "Precondition failed",
        error_code: str = "PRECONDITION_FAILED",
        details: list[dict[str, Any]] | None = None,
    ):
        super().__init__(
            status_code=status.HTTP_412_PRECONDITION_FAILED,
            message=message,
            error_code=error_code,
            details=details,
        )


class InternalServerError(AppException):
    """500 Internal Server error."""
    
    def __init__(
        self,
        message: str = "Internal server error",
        error_code: str = "INTERNAL_ERROR",
        details: list[dict[str, Any]] | None = None,
    ):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=message,
            error_code=error_code,
            details=details,
        )


# Exception Handlers
async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """Handle application exceptions."""
    # Get X-Request-ID from request state (set by middleware) or generate new one
    request_id = getattr(request.state, "request_id", None)
    if not request_id:
        request_id = generate_request_id()
    
    response = JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.error_code,
                "details": exc.details,
            },
            "message": exc.message,
        },
    )
    response.headers["X-Request-ID"] = request_id
    return response


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handle request validation errors."""
    # Get X-Request-ID from request state (set by middleware) or generate new one
    request_id = getattr(request.state, "request_id", None)
    if not request_id:
        request_id = generate_request_id()
    
    details = [
        {"field": ".".join(str(loc) for loc in error["loc"]), "issue": error["msg"]}
        for error in exc.errors()
    ]
    response = JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "details": details,
            },
            "message": "Validation failed",
        },
    )
    response.headers["X-Request-ID"] = request_id
    return response


async def response_validation_exception_handler(
    request: Request, exc: ResponseValidationError
) -> JSONResponse:
    """Handle response validation errors (usually occurs when exception is raised but response model validation still runs)."""
    # Get X-Request-ID from request state (set by middleware) or generate new one
    request_id = getattr(request.state, "request_id", None)
    if not request_id:
        request_id = generate_request_id()
    
    # Extract validation error details (ResponseValidationError has errors() method like RequestValidationError)
    details = []
    try:
        for error in exc.errors():
            error_loc = ".".join(str(loc) for loc in error.get("loc", []))
            error_msg = error.get("msg", "Validation error")
            details.append({"field": error_loc, "issue": error_msg})
    except (AttributeError, TypeError):
        # Fallback if errors() method doesn't exist or returns unexpected format
        details.append({"field": "response", "issue": "Response validation failed"})
    
    # If this is a response validation error, it usually means an exception was raised
    # but FastAPI still tried to validate the response model. Return a 500 error.
    response = JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "RESPONSE_VALIDATION_ERROR",
                "details": details,
            },
            "message": "Response validation failed. This may occur when an exception is raised during request processing.",
        },
    )
    response.headers["X-Request-ID"] = request_id
    return response


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle HTTP exceptions."""
    # Get X-Request-ID from request state (set by middleware) or generate new one
    request_id = getattr(request.state, "request_id", None)
    if not request_id:
        request_id = generate_request_id()
    
    response = JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": "HTTP_ERROR",
                "details": [],
            },
            "message": exc.detail,
        },
    )
    response.headers["X-Request-ID"] = request_id
    return response


async def database_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handler for database constraint violations."""
    
    def extract_field_name(error_msg: str, constraint_name: str = None) -> str:
        """Extract field name from constraint name or error message."""
        if constraint_name:
            field = constraint_name
            # Remove prefixes: ix_, fk_, pk_, uq_, ck_
            for prefix in ['ix_', 'fk_', 'pk_', 'uq_', 'ck_']:
                if field.startswith(prefix):
                    field = field[len(prefix):]
            # Remove table prefix (e.g., "users_" from "users_email")
            if '_' in field:
                parts = field.split('_', 1)
                if len(parts) > 1:
                    field = parts[1]
            # Remove suffixes: _key, _idx, _constraint
            for suffix in ['_key', '_idx', '_constraint']:
                if field.endswith(suffix):
                    field = field[:-len(suffix)]
            return field
        
        # Extract from error message: "Key (field_name)=(value)"
        match = re.search(r'Key \(([^)]+)\)', error_msg)
        if match:
            return match.group(1)
        
        # Extract constraint name and recurse
        match = re.search(r'constraint "([^"]+)"', error_msg)
        if match:
            return extract_field_name(error_msg, match.group(1))
        
        return "field"
    
    def extract_constraint_info(error_msg: str) -> tuple[str, str]:
        """Extract constraint name and field from error message."""
        constraint_name = None
        match = re.search(r'constraint "([^"]+)"', error_msg)
        if match:
            constraint_name = match.group(1)
        field_name = extract_field_name(error_msg, constraint_name)
        return constraint_name, field_name
    
    def create_error_response(
        status_code: int,
        error_code: str,
        message: str,
        details: list[dict],
    ) -> JSONResponse:
        """Helper to create standardized error response."""
        # Get X-Request-ID from request state (set by middleware) or generate new one
        request_id = getattr(request.state, "request_id", None)
        if not request_id:
            request_id = generate_request_id()
        
        response = JSONResponse(
            status_code=status_code,
            content={
                "error": {
                    "code": error_code,
                    "details": details,
                },
                "message": message,
            },
        )
        response.headers["X-Request-ID"] = request_id
        return response
    
    # Handle IntegrityError (wraps asyncpg exceptions)
    if isinstance(exc, IntegrityError):
        orig_exc = exc.orig if hasattr(exc, 'orig') else exc
        
        if isinstance(orig_exc, UniqueViolationError):
            _, field_name = extract_constraint_info(str(orig_exc))
            return create_error_response(
                status_code=status.HTTP_409_CONFLICT,
                error_code=f"DUPLICATE_{field_name.upper()}",
                message=f"A record with this {field_name} already exists. Please use a different value.",
                details=[{"field": field_name, "issue": f"{field_name} must be unique"}],
            )
        elif isinstance(orig_exc, ForeignKeyViolationError):
            error_msg = str(orig_exc)
            match = re.search(
                r'Key \(([^)]+)\)=\(([^)]+)\) is not present in table "([^"]+)"',
                error_msg
            )
            if match:
                field_name, key_value, table_name = match.group(1), match.group(2), match.group(3)
                resource_name = table_name.replace('_', ' ').title().replace(' ', '')
                return create_error_response(
                    status_code=status.HTTP_404_NOT_FOUND,
                    error_code=f"{resource_name.upper()}_NOT_FOUND",
                    message=f"The referenced {resource_name} does not exist.",
                    details=[{"field": field_name, "issue": f"Referenced {resource_name} with ID '{key_value}' not found"}],
                )
            return create_error_response(
                status_code=status.HTTP_404_NOT_FOUND,
                error_code="FOREIGN_KEY_VIOLATION",
                message="The referenced record does not exist.",
                details=[{"field": "reference", "issue": "Referenced record not found"}],
            )
        elif isinstance(orig_exc, NotNullViolationError):
            error_msg = str(orig_exc)
            match = re.search(r'column "([^"]+)"', error_msg)
            field_name = match.group(1) if match else "field"
            return create_error_response(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                error_code="REQUIRED_FIELD_MISSING",
                message=f"The field '{field_name}' is required and cannot be null.",
                details=[{"field": field_name, "issue": f"{field_name} is required"}],
            )
        elif isinstance(orig_exc, CheckViolationError):
            _, field_name = extract_constraint_info(str(orig_exc))
            return create_error_response(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                error_code="CHECK_CONSTRAINT_VIOLATION",
                message=f"The value provided for '{field_name}' violates a validation rule.",
                details=[{"field": field_name, "issue": "Value violates check constraint"}],
            )
    
    # Handle direct asyncpg exceptions (fallback)
    if isinstance(exc, UniqueViolationError):
        _, field_name = extract_constraint_info(str(exc))
        return create_error_response(
            status_code=status.HTTP_409_CONFLICT,
            error_code=f"DUPLICATE_{field_name.upper()}",
            message=f"A record with this {field_name} already exists. Please use a different value.",
            details=[{"field": field_name, "issue": f"{field_name} must be unique"}],
        )
    elif isinstance(exc, ForeignKeyViolationError):
        error_msg = str(exc)
        match = re.search(
            r'Key \(([^)]+)\)=\(([^)]+)\) is not present in table "([^"]+)"',
            error_msg
        )
        if match:
            field_name, key_value, table_name = match.group(1), match.group(2), match.group(3)
            resource_name = table_name.replace('_', ' ').title().replace(' ', '')
            return create_error_response(
                status_code=status.HTTP_404_NOT_FOUND,
                error_code=f"{resource_name.upper()}_NOT_FOUND",
                message=f"The referenced {resource_name} does not exist.",
                details=[{"field": field_name, "issue": f"Referenced {resource_name} with ID '{key_value}' not found"}],
            )
        return create_error_response(
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="FOREIGN_KEY_VIOLATION",
            message="The referenced record does not exist.",
            details=[{"field": "reference", "issue": "Referenced record not found"}],
        )
    elif isinstance(exc, NotNullViolationError):
        error_msg = str(exc)
        match = re.search(r'column "([^"]+)"', error_msg)
        field_name = match.group(1) if match else "field"
        return create_error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error_code="REQUIRED_FIELD_MISSING",
            message=f"The field '{field_name}' is required and cannot be null.",
            details=[{"field": field_name, "issue": f"{field_name} is required"}],
        )
    elif isinstance(exc, CheckViolationError):
        _, field_name = extract_constraint_info(str(exc))
        return create_error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error_code="CHECK_CONSTRAINT_VIOLATION",
            message=f"The value provided for '{field_name}' violates a validation rule.",
            details=[{"field": field_name, "issue": "Value violates check constraint"}],
        )
    
    # If we get here, it's an unhandled database exception
    # Let it fall through to catch-all handler
    raise exc


async def catch_all_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle all unhandled exceptions."""
    # Get X-Request-ID from request state (set by middleware) or generate new one
    request_id = getattr(request.state, "request_id", None)
    if not request_id:
        request_id = generate_request_id()
    
    response = JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "details": [],
            },
            "message": "An unexpected error occurred",
        },
    )
    response.headers["X-Request-ID"] = request_id
    return response


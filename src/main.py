"""FastAPI application entry point."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError, ResponseValidationError, HTTPException
from src.config import settings
from src.exceptions import (
    AppException,
    app_exception_handler,
    validation_exception_handler,
    response_validation_exception_handler,
    http_exception_handler,
    database_exception_handler,
    catch_all_exception_handler,
)
from sqlalchemy.exc import IntegrityError
from asyncpg.exceptions import (
    UniqueViolationError,
    ForeignKeyViolationError,
    NotNullViolationError,
    CheckViolationError,
)
from src.api.router import api_router
from src.middleware import RequestIDMiddleware
from src.infra.cache_redis import close_redis

# Create FastAPI application
app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    debug=settings.debug,
    swagger_ui_parameters={
        "persistAuthorization": False,  # Don't persist authorization token - users must re-authenticate on page refresh
    },
)

# Register middleware (order matters - middleware runs in reverse order)
# CORS middleware should be added first (will run last in reverse order)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)
app.add_middleware(RequestIDMiddleware)

# Register exception handlers (order matters - most specific first)
app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(ResponseValidationError, response_validation_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
# Database handlers (BEFORE catch-all)
app.add_exception_handler(IntegrityError, database_exception_handler)
app.add_exception_handler(UniqueViolationError, database_exception_handler)
app.add_exception_handler(ForeignKeyViolationError, database_exception_handler)
app.add_exception_handler(NotNullViolationError, database_exception_handler)
app.add_exception_handler(CheckViolationError, database_exception_handler)
app.add_exception_handler(Exception, catch_all_exception_handler)  # Last

# Include API router
app.include_router(api_router, prefix=settings.api_prefix)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on application shutdown."""
    await close_redis()


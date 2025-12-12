"""Global utility functions."""
from datetime import datetime, timezone
from uuid import uuid4
from typing import Optional


def generate_request_id() -> str:
    """Generate unique request ID."""
    # Format: req_<uuid>
    return f"req_{uuid4().hex[:12]}"


def generate_etag(updated_at: datetime) -> str:
    """Generate ETag from updated_at timestamp.
    
    Format: "20240120T103000Z" (ISO 8601 format, UTC)
    """
    # Ensure UTC timezone
    if updated_at.tzinfo is None:
        updated_at = updated_at.replace(tzinfo=timezone.utc)
    else:
        updated_at = updated_at.astimezone(timezone.utc)
    
    # Format: YYYYMMDDTHHMMSSZ
    return updated_at.strftime("%Y%m%dT%H%M%SZ")


def format_last_modified(updated_at: datetime) -> str:
    """Format datetime for Last-Modified header (RFC 7231 format).
    
    Format: "Wed, 20 Jan 2024 10:30:00 GMT"
    """
    # Ensure UTC timezone
    if updated_at.tzinfo is None:
        updated_at = updated_at.replace(tzinfo=timezone.utc)
    else:
        updated_at = updated_at.astimezone(timezone.utc)
    
    # Format: RFC 7231 format (e.g., "Wed, 20 Jan 2024 10:30:00 GMT")
    return updated_at.strftime("%a, %d %b %Y %H:%M:%S GMT")


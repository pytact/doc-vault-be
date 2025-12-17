"""Document utilities."""
import os
import json
from pathlib import Path
from datetime import datetime, date
from typing import Optional, Any
from src.documents.constants import MAX_FILE_SIZE_BYTES, ALLOWED_MIME_TYPE
from src.documents.config import document_settings
from src.exceptions import ValidationError


def generate_etag(updated_at: datetime) -> str:
    """Generate ETag from updated_at timestamp.
    
    Format: YYYYMMDDTHHMMSSZ (e.g., "20240120T103000Z")
    """
    return updated_at.strftime("%Y%m%dT%H%M%SZ")


def format_last_modified(updated_at: datetime) -> str:
    """Format datetime for Last-Modified header (RFC 1123 format).
    
    Format: Wed, 20 Jan 2024 10:30:00 GMT
    """
    return updated_at.strftime("%a, %d %b %Y %H:%M:%S GMT")


def validate_file_size(file_size: int) -> bool:
    """Validate file size against maximum allowed size.
    
    Args:
        file_size: File size in bytes
        
    Returns:
        True if file size is valid, False otherwise
    """
    return file_size <= MAX_FILE_SIZE_BYTES


def validate_mime_type(mime_type: str) -> bool:
    """Validate MIME type against allowed types.
    
    Args:
        mime_type: MIME type string
        
    Returns:
        True if MIME type is valid, False otherwise
    """
    return mime_type == ALLOWED_MIME_TYPE


def generate_file_path(document_id: str, family_id: str) -> str:
    """Generate relative file path for document storage.
    
    Args:
        document_id: Document UUID (as string)
        family_id: Family UUID (as string)
        
    Returns:
        Relative file path string (e.g., "uploads/f12/d88/document_id.pdf")
    """
    # Extract first 2 characters from family_id and document_id for directory structure
    family_prefix = family_id[:2] if len(family_id) >= 2 else "f0"
    doc_prefix = document_id[:2] if len(document_id) >= 2 else "d0"
    
    # Generate relative path: uploads/{family_prefix}{doc_prefix}/{document_id}.pdf
    return f"uploads/{family_prefix}{doc_prefix}/{document_id}.pdf"


def get_upload_base_path() -> Path:
    """Get the base upload directory path.
    
    Returns:
        Path object for the upload base directory
    """
    # Get upload path from config (default: "uploads" or "/uploads")
    upload_path = document_settings.UPLOAD_PATH
    
    # If absolute path, use it directly
    if os.path.isabs(upload_path):
        return Path(upload_path)
    
    # Otherwise, use relative to project root
    # Get project root (assuming this file is in src/documents/)
    project_root = Path(__file__).parent.parent.parent
    return project_root / upload_path


def save_file(file_content: bytes, relative_path: str) -> str:
    """Save file to disk.
    
    Args:
        file_content: Binary file content
        relative_path: Relative path from upload base directory (e.g., "uploads/f12/d88/doc.pdf")
        
    Returns:
        Absolute path where file was saved
        
    Raises:
        OSError: If file cannot be saved
    """
    base_path = get_upload_base_path()
    full_path = base_path / relative_path
    
    # Create parent directories if they don't exist
    full_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write file
    with open(full_path, "wb") as f:
        f.write(file_content)
    
    # Return absolute path as string
    return str(full_path.absolute())


def delete_file(relative_path: str) -> bool:
    """Delete file from disk.
    
    Args:
        relative_path: Relative path from upload base directory
        
    Returns:
        True if file was deleted, False if file didn't exist
    """
    base_path = get_upload_base_path()
    full_path = base_path / relative_path
    
    if full_path.exists():
        full_path.unlink()
        return True
    return False


def file_exists(relative_path: str) -> bool:
    """Check if file exists.
    
    Args:
        relative_path: Relative path from upload base directory
        
    Returns:
        True if file exists, False otherwise
    """
    base_path = get_upload_base_path()
    full_path = base_path / relative_path
    return full_path.exists()


def read_file(relative_path: str) -> bytes:
    """Read file from disk.
    
    Args:
        relative_path: Relative path from upload base directory
        
    Returns:
        Binary file content
        
    Raises:
        FileNotFoundError: If file does not exist
        OSError: If file cannot be read
    """
    base_path = get_upload_base_path()
    full_path = base_path / relative_path
    
    if not full_path.exists():
        raise FileNotFoundError(f"File not found: {relative_path}")
    
    with open(full_path, "rb") as f:
        return f.read()


def parse_expiry_date(date_str: Optional[str]) -> Optional[date]:
    """Parse expiry date string to date object.
    
    Args:
        date_str: Date string in YYYY-MM-DD format
        
    Returns:
        Parsed date object or None if date_str is None
        
    Raises:
        ValidationError: If date format is invalid
    """
    if not date_str:
        return None
    
    try:
        return date.fromisoformat(date_str)
    except ValueError:
        raise ValidationError(
            message="Invalid expiry_date format. Use YYYY-MM-DD.",
            error_code="VALIDATION_ERROR",
            details=[{"field": "expiry_date", "issue": "Invalid date format"}],
        )


def parse_details_json(json_str: Optional[str]) -> Optional[dict[str, Any]]:
    """Parse details JSON string to dictionary.
    
    Args:
        json_str: JSON string
        
    Returns:
        Parsed dictionary or None if json_str is None
        
    Raises:
        ValidationError: If JSON format is invalid
    """
    if not json_str:
        return None
    
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        raise ValidationError(
            message="Invalid details_json format.",
            error_code="VALIDATION_ERROR",
            details=[{"field": "details_json", "issue": "Invalid JSON"}],
        )


def build_pagination_urls(
    base_url: str,
    page: int,
    total_pages: int,
    query_params: dict[str, Any],
) -> tuple[Optional[str], Optional[str]]:
    """Build next_page and prev_page URLs for pagination.
    
    Args:
        base_url: Base URL path (e.g., "/v1/documents")
        page: Current page number
        total_pages: Total number of pages
        query_params: Dictionary of query parameters (None values are filtered out)
        
    Returns:
        Tuple of (next_page_url, prev_page_url)
    """
    # Build query string from parameters (filter out None values)
    query_parts = []
    for key, value in query_params.items():
        if value is not None:
            query_parts.append(f"{key}={value}")
    
    query_string = "&".join(query_parts)
    
    # Build next_page URL
    next_page = None
    if page < total_pages:
        if query_string:
            next_page = f"{base_url}?{query_string}&page={page + 1}"
        else:
            next_page = f"{base_url}?page={page + 1}"
    
    # Build prev_page URL
    prev_page = None
    if page > 1:
        if query_string:
            prev_page = f"{base_url}?{query_string}&page={page - 1}"
        else:
            prev_page = f"{base_url}?page={page - 1}"
    
    return next_page, prev_page

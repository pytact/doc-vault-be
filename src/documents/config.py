"""Document configuration."""
from typing import Optional
from pydantic_settings import BaseSettings


class DocumentSettings(BaseSettings):
    """Document-specific configuration."""
    
    # File upload settings
    MAX_FILE_SIZE_MB: int = 5
    MAX_FILE_SIZE_BYTES: int = 5 * 1024 * 1024  # 5 MB
    ALLOWED_MIME_TYPES: list[str] = ["application/pdf"]
    DEFAULT_MIME_TYPE: str = "application/pdf"
    
    # File storage settings
    UPLOAD_PATH: str = "uploads"  # Relative to project root, or absolute path
    CDN_BASE_URL: Optional[str] = None  # Optional CDN URL for file access
    
    # Pagination defaults
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": False,
        "env_prefix": "DOCUMENT_",  # Optional: prefix for env vars
    }


document_settings = DocumentSettings()

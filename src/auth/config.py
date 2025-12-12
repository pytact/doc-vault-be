"""Authentication configuration."""
from pydantic_settings import BaseSettings
from src.config import settings


class AuthSettings(BaseSettings):
    """Authentication-specific configuration."""
    
    # JWT Configuration
    SECRET_KEY: str = settings.secret_key
    ALGORITHM: str = settings.algorithm
    ACCESS_TOKEN_EXPIRE_SECONDS: int = settings.access_token_expire_minutes * 60  # Convert minutes to seconds
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": False,
        "env_prefix": "AUTH_",
    }


auth_settings = AuthSettings()

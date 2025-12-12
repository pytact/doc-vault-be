"""Application configuration using Pydantic BaseSettings."""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database Configuration
    database_url: str = "postgresql+asyncpg://postgres:1112@db:5432/fastapi_boilerplate"
    
    # API Configuration
    api_title: str = "FastAPI Boilerplate"
    api_version: str = "1.0.0"
    api_prefix: str = "/v1"
    
    # Environment Configuration
    environment: str = "local"
    debug: bool = True
    
    # Security Configuration
    secret_key: str = "your-secret-key-here-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": False,
    }


settings = Settings()


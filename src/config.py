"""Application configuration using Pydantic BaseSettings."""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database Configuration
    database_url: str = "postgresql+asyncpg://postgres:1112@db:5432/fastapi_boilerplate"
    
    # Redis Configuration
    redis_url: str = "redis://redis:6379/0"
    
    # Celery Configuration
    celery_broker_url: str = "redis://redis:6379/0"
    celery_result_backend: str = "redis://redis:6379/0"
    
    # Email Configuration
    email_sender: str = "shahidm@pytact.com"
    email_app_password: str = "pnkd sowf pghx tiqq"
    email_smtp_server: str = "smtp.gmail.com"
    email_smtp_port: int = 587
    frontend_url: str = "http://localhost:3000"  # Frontend URL for invitation links
    
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
    
    # CORS Configuration
    cors_origins: list[str] = ["*"]  # Allow all origins by default. For production, specify exact origins like ["http://localhost:3000", "https://yourdomain.com"]
    cors_allow_credentials: bool = False  # Must be False when using ["*"] for origins. Set to True and specify exact origins if needed
    cors_allow_methods: list[str] = ["*"]  # Allow all methods
    cors_allow_headers: list[str] = ["*"]  # Allow all headers
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": False,
    }


settings = Settings()


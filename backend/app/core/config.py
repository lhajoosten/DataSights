"""
Application configuration using Pydantic settings.
Similar to IOptions<T> pattern in .NET for strongly-typed configuration.
"""

from functools import lru_cache
from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable binding."""
    
    # Application
    environment: str = Field(default="development", description="Application environment")
    log_level: str = Field(default="INFO", description="Logging level")
    
    # API Configuration
    api_title: str = Field(default="DataSights API", description="API title")
    api_version: str = Field(default="1.0.0", description="API version")
    
    # CORS
    allowed_origins: List[str] = Field(
        default=["http://localhost:5173", "http://localhost:3000"],
        description="Allowed CORS origins"
    )
    
    # File Upload
    max_file_size_mb: int = Field(default=10, description="Maximum file size in MB")
    upload_dir: str = Field(default="/tmp/uploads", description="Upload directory")
    
    # LLM Configuration
    openai_api_key: str = Field(default="", description="OpenAI API key")
    openai_model: str = Field(default="gpt-3.5-turbo", description="OpenAI model to use")
    llm_timeout_seconds: int = Field(default=30, description="LLM request timeout")
    
    # Rate Limiting
    rate_limit_requests: int = Field(default=10, description="Requests per minute per IP")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    Similar to dependency injection pattern in .NET.
    """
    return Settings()
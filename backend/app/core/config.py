"""
Application configuration management.
Similar to IOptions<T> pattern in .NET applications.
"""

from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Application
    environment: str = "development"
    debug: bool = False
    
    # API Configuration
    api_title: str = "Talk to Your Data API"
    api_version: str = "1.0.0"
    allowed_origins: List[str] = ["http://localhost:3000", "http://localhost:5173"]
    
    # File Upload
    max_file_size_mb: int = 10
    upload_dir: str = "/tmp/uploads"
    
    # LLM Configuration
    openai_api_key: str = ""
    openai_model: str = "gpt-3.5-turbo"
    llm_timeout_seconds: int = 30
    
    # Logging
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


def get_settings() -> Settings:
    """Get application settings instance."""
    return Settings()
"""
Application configuration management using Pydantic Settings.

This module handles all configuration loading from environment variables,
providing type-safe access to configuration values throughout the application.
"""

from pydantic_settings import BaseSettings
from typing import List
from functools import lru_cache


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    All settings can be overridden via environment variables or .env file.
    Settings are validated at startup to ensure correct types and required values.
    """

    # API Configuration
    api_title: str = "Eduverse API"
    api_version: str = "1.0.0"
    api_description: str = "AI-powered interactive learning platform for children aged 6-10"

    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_reload: bool = True

    # Anthropic API
    anthropic_api_key: str
    anthropic_model: str = "claude-sonnet-4-20250514"
    anthropic_max_tokens: int = 4000

    # Security
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # CORS
    allowed_origins: List[str] = ["http://localhost:3000", "http://localhost:8000"]

    # Environment
    environment: str = "development"

    # Logging
    log_level: str = "INFO"

    # File Upload Limits
    max_upload_size_mb: int = 10
    allowed_file_types: List[str] = [".pdf"]

    # AI Processing
    ai_temperature: float = 0.7
    ai_timeout_seconds: int = 60

    class Config:
        """Pydantic configuration"""
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields in .env


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.

    Uses LRU cache to ensure settings are only loaded once,
    improving performance and ensuring consistency.

    Returns:
        Settings: Cached settings instance
    """
    return Settings()


# Global settings instance for easy import
settings = get_settings()

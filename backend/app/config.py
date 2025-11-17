"""
Configuration module for the Timeline Thinker application.
Loads environment variables and provides application-wide settings.
"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    """
    # Database
    database_url: str

    # LLM Configuration
    llm_provider: str = "openai"  # "openai" or "anthropic"
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    llm_model: str = "gpt-4-turbo-preview"

    # Embedding Configuration
    embedding_model: str = "text-embedding-3-small"
    embedding_dimension: int = 1536

    # Redis/Celery
    redis_url: str = "redis://localhost:6379/0"

    # Application
    debug: bool = False
    api_v1_prefix: str = "/api/v1"
    secret_key: str

    # Chunking
    chunk_size: int = 500
    chunk_overlap: int = 50

    # Timeline
    default_lookback_days: int = 30

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    Using lru_cache ensures we only load environment variables once.
    """
    return Settings()

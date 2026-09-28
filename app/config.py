"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    model_config = SettingsConfigDict(env_file=".env", extra="allow")

    # Application
    APP_NAME: str = "The Drama Verse Shorts Analytics"
    DEBUG: bool = True

    # Database
    DATABASE_URL: str = "sqlite:///./page_analytics.db"

    # Security
    SECRET_KEY: str = "change-this-to-a-random-secret-key-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours

    # Demo Mode
    DEMO_MODE: bool = False

    # Redis (optional)
    REDIS_URL: Optional[str] = None

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60

    # File Upload
    MAX_UPLOAD_SIZE_MB: int = 10

    # Performance Score Weights (customizable)
    WEIGHT_VIEW_GROWTH: float = 0.25
    WEIGHT_ENGAGEMENT: float = 0.25
    WEIGHT_FOLLOWER_GROWTH: float = 0.20
    WEIGHT_CONSISTENCY: float = 0.15
    WEIGHT_SHARE_RATE: float = 0.15

settings = Settings()


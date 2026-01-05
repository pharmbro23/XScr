"""Configuration management for the Twitter Signal Monitor."""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Twitter credentials
    twitter_username: str
    twitter_password: str
    
    # Telegram credentials
    telegram_bot_token: str
    telegram_chat_id: str
    
    # Google AI (Gemini) credentials
    google_api_key: str
    llm_model: str = "gemini-1.5-flash"
    
    # Database configuration
    database_path: str = "./data/app.db"
    
    # Polling configuration
    poll_interval_seconds: int = 60
    
    # HTTP client configuration
    request_timeout_seconds: int = 30
    max_retries: int = 3
    
    # Logging
    log_level: str = "INFO"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    @property
    def database_dir(self) -> Path:
        """Get the database directory path."""
        return Path(self.database_path).parent


# Global settings instance
settings = Settings()

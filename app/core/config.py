"""Platform configuration — owned by Contributor E."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables or .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    database_url: str = "sqlite:///./data/decisions.db"
    log_level: str = "INFO"
    app_env: str = "local"


settings = Settings()

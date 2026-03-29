from functools import lru_cache
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    # GitHub App
    github_app_id: str = Field(default="", env="GITHUB_APP_ID")
    github_private_key_path: str = Field(default="", env="GITHUB_PRIVATE_KEY_PATH")
    github_webhook_secret: str = Field(default="", env="GITHUB_WEBHOOK_SECRET")
    github_client_id: str = Field(default="", env="GITHUB_CLIENT_ID")
    github_client_secret: str = Field(default="", env="GITHUB_CLIENT_SECRET")

    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://user:password@localhost:5432/codeintel",
        env="DATABASE_URL",
    )

    # Redis
    redis_url: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")

    # OpenRouter
    openrouter_api_key: str = Field(default="", env="OPENROUTER_API_KEY")
    openrouter_model: str = Field(
        default="deepseek/deepseek-r1", env="OPENROUTER_MODEL"
    )

    # Slack
    slack_webhook_url: str = Field(default="", env="SLACK_WEBHOOK_URL")

    # App
    app_env: str = Field(default="development", env="APP_ENV")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")

    # CORS
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

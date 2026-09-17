from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Job Scraper API"
    api_prefix: str = "/api/v1"
    database_url: str = "sqlite:///./jobs.db"
    secret_key: str = "change-this-secret-before-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    request_timeout_seconds: float = 20.0
    scraper_user_agent: str = "JobScraperPortfolioBot/1.0"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

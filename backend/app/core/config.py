from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Finlens API"
    environment: str = "development"

    database_url: str = "postgresql+psycopg://finlens:finlens@localhost:5432/finlens"
    redis_url: str = "redis://localhost:6379/0"

    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 7

    # Fernet key encrypting saved statement passwords at rest. Rotating this
    # invalidates every saved password (accounts fall back to prompting again).
    statement_encryption_key: str = "AggGCewtgGlqkmTrMdr-2d10QuitQOiq40WFHScgccQ="

    cors_origins: list[str] = ["http://localhost:5173"]


@lru_cache
def get_settings() -> Settings:
    return Settings()

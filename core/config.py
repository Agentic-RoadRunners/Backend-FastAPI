"""
Application settings loaded from environment variables.
Uses Pydantic BaseSettings for validation and .env file support.
"""

from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application configuration from environment variables."""

    # Supabase (PostgreSQL)
    supabase_db_url: str = Field(..., alias="SUPABASE_DB_URL")

    # Neo4j
    neo4j_uri: str = Field(default="bolt://localhost:7687", alias="NEO4J_URI")
    neo4j_user: str = Field(default="neo4j", alias="NEO4J_USER")
    neo4j_password: str = Field(default="saferoad_local", alias="NEO4J_PASSWORD")

    # OpenAI
    openai_api_key: str = Field(..., alias="OPENAI_API_KEY")
    crew_model: str = Field(default="gpt-4o-mini", alias="CREW_MODEL")
    chat_model: str = Field(default="gpt-4o-mini", alias="CHAT_MODEL")

    # .NET API
    dotnet_api_url: str = Field(
        default="https://localhost:9001/api", alias="DOTNET_API_URL"
    )

    # JWT — must match .NET backend
    jwt_secret: str = Field(..., alias="JWT_SECRET")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    jwt_issuer: str = Field(default="SafeRoad", alias="JWT_ISSUER")
    jwt_audience: str = Field(default="SafeRoad", alias="JWT_AUDIENCE")

    # App
    debug: bool = Field(default=False, alias="DEBUG")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "populate_by_name": True,
    }


# Lazy singleton — avoids import-time crash when .env is missing (e.g. in tests)
_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


class _SettingsProxy:
    """Proxy that lazily resolves to the real Settings instance."""
    def __getattr__(self, name: str):
        return getattr(get_settings(), name)


settings = _SettingsProxy()  # type: ignore[assignment]

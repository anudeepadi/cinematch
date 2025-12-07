from pydantic_settings import BaseSettings
from functools import lru_cache
import os


class Settings(BaseSettings):
    # App settings
    app_name: str = "CineMatch - AI Movie Recommender"
    debug: bool = os.getenv("DEBUG", "true").lower() == "true"

    # Database - Railway provides DATABASE_URL
    database_url: str = "sqlite+aiosqlite:///./cinematch.db"

    # Frontend URL for CORS (set in Railway)
    frontend_url: str = "http://localhost:5173"

    @property
    def async_database_url(self) -> str:
        """Convert database URL to async version"""
        url = self.database_url
        # Railway/Heroku provides postgres:// but SQLAlchemy needs postgresql://
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return url

    # JWT Auth
    secret_key: str = "your-super-secret-key-change-in-production-min-32-chars"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 7  # 7 days

    # AI API Keys
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    google_api_key: str = ""

    # TMDB API for movie data
    tmdb_api_key: str = ""
    tmdb_base_url: str = "https://api.themoviedb.org/3"

    # Supabase Configuration
    supabase_url: str = ""
    supabase_key: str = ""
    supabase_secret_key: str = ""

    # Recommendation settings
    recommendation_batch_size: int = 20
    min_history_for_collab: int = 5

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

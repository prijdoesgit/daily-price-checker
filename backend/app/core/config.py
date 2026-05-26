from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://medprice:medprice_secret@localhost:5432/medprice"
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    ENVIRONMENT: str = "development"

    SCRAPING_DELAY_MIN: float = 1.5
    SCRAPING_DELAY_MAX: float = 4.0
    MAX_RETRIES: int = 3
    REQUEST_TIMEOUT: int = 30

    PROXY_LIST: Optional[str] = None
    BRIGHTDATA_USERNAME: Optional[str] = None
    BRIGHTDATA_PASSWORD: Optional[str] = None
    BRIGHTDATA_HOST: Optional[str] = None

    KIMI_API_KEY: Optional[str] = None

    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:3001", "http://localhost:4000"]

    class Config:
        env_file = ".env"
        extra = "ignore"

    @property
    def proxy_list_parsed(self) -> list[str]:
        if not self.PROXY_LIST:
            return []
        return [p.strip() for p in self.PROXY_LIST.split(",") if p.strip()]


settings = Settings()

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Настройки приложения."""

    APP_NAME: str = "Hitalent Test Assignment"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    DATABASE_URL: str = "postgresql+asyncpg://user:password@db:5432/hitalent"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()

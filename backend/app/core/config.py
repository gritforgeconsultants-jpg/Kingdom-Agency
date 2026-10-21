from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "Kingdom Agency"
    APP_ENV: str = "development"
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    DATABASE_URL: str = "postgresql+asyncpg://kingdom:changeme@db:5432/kingdom_agency"
    DATABASE_URL_SYNC: str = "postgresql://kingdom:changeme@db:5432/kingdom_agency"
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"
    RATE_LIMIT_AUTH: str = "10/minute"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",")]

    @property
    def is_dev(self) -> bool:
        return self.APP_ENV == "development"

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()

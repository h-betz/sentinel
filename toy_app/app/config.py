from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = (
        "postgresql+asyncpg://sentinel:sentinel_secret@localhost:5432/sentinel"  # pragma: allowlist secret
    )
    database_url_sync: str = (
        "postgresql://sentinel:sentinel_secret@localhost:5432/sentinel"  # pragma: allowlist secret
    )
    db_pool_size: int = 5
    db_max_overflow: int = 0
    payment_service_url: str = "http://localhost:8001"
    debug: bool = False

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()

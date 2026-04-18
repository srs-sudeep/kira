"""KIRA Identity Service — configuration via environment variables."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", ".env.local"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    SERVICE_NAME: str = "kira-identity"
    ENVIRONMENT: str = "development"

    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/kira"
    REDIS_URL: str = "redis://:redis-local-dev@localhost:6379/0"
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"

    SECRET_KEY: str = "change-me-in-production-use-openssl-rand-hex-32"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    MFA_ISSUER: str = "KIRA Hotel Manager"

    # SendGrid — leave blank in development; emails are logged instead
    SENDGRID_API_KEY: str = ""
    FROM_EMAIL: str = "no-reply@kirahms.com"

    ALLOWED_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    LOG_LEVEL: str = "INFO"


settings = Settings()

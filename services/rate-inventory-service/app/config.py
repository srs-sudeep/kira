"""KIRA Rate & Inventory Service — configuration."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", ".env.local"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    service_name: str = "kira-rate-inventory"
    port: int = 8002
    environment: str = "development"
    debug: bool = False

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/kira"
    redis_url: str = "redis://:redis-local-dev@localhost:6379/1"
    kafka_bootstrap_servers: str = "localhost:9092"

    secret_key: str = "change-me-in-production-use-openssl-rand-hex-32"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    # Topics
    kafka_topic_ari_updated: str = "ari.updated"

    allowed_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]
    log_level: str = "INFO"


settings = Settings()

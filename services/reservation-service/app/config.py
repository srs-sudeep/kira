from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", ".env.local"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    service_name: str = "reservation-service"
    port: int = 8003
    debug: bool = False
    environment: str = "development"

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/kira"
    redis_url: str = "redis://:redis-local-dev@localhost:6379/2"
    kafka_bootstrap_servers: str = "localhost:9092"

    secret_key: str = "change-me-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # AES-256-GCM key for guest PII encryption — 64-char hex or 32-byte raw
    encryption_key: str = "0" * 64

    # URL of rate-inventory-service (for ARI availability checks)
    rate_inventory_service_url: str = "http://localhost:8002"

    # Email
    sendgrid_api_key: str = ""
    from_email: str = "noreply@yourdomain.com"

    allowed_origins: list[str] = ["http://localhost:5173"]
    log_level: str = "INFO"


settings = Settings()

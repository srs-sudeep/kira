from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    service_name: str = "channel-engine"
    port: int = 8004
    debug: bool = False
    environment: str = "development"

    database_url: str = "postgresql+asyncpg://kira:kira@localhost:5432/kira_channel_engine"
    redis_url: str = "redis://localhost:6379/3"
    kafka_bootstrap_servers: str = "localhost:9092"

    secret_key: str = "change-me-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # AES-256-GCM key for encrypting OTA credentials — 64-char hex
    encryption_key: str = "0" * 64

    # Kafka topics
    kafka_topic_ari_updated: str = "ari.updated"
    kafka_topic_sync_result: str = "channel.sync.result"
    kafka_topic_booking_raw: str = "channel.booking.raw"

    # Kafka consumer group
    kafka_consumer_group: str = "channel-engine"

    # Circuit breaker: failures before marking channel as error
    circuit_breaker_threshold: int = 5

    # Booking pull interval (seconds) — Celery beat
    booking_pull_interval: int = 60

    allowed_origins: list[str] = ["http://localhost:5173"]
    log_level: str = "INFO"


settings = Settings()

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    service_name: str = "notification-service"
    port: int = 8005
    debug: bool = False
    environment: str = "development"

    database_url: str = "postgresql+asyncpg://kira:kira@localhost:5432/kira_notification_service"
    redis_url: str = "redis://localhost:6379/4"
    kafka_bootstrap_servers: str = "localhost:9092"

    secret_key: str = "change-me-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # Email
    sendgrid_api_key: str = ""
    from_email: str = "noreply@yourdomain.com"

    # Kafka topics consumed
    kafka_topic_reservation_created: str = "reservation.created"
    kafka_topic_reservation_cancelled: str = "reservation.cancelled"
    kafka_topic_channel_sync_failed: str = "channel.sync.failed"

    kafka_consumer_group: str = "notification-service"

    allowed_origins: list[str] = ["http://localhost:5173"]
    log_level: str = "INFO"


settings = Settings()

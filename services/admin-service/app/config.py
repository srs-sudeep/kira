from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    service_name: str = "admin-service"
    port: int = 8006
    debug: bool = False
    environment: str = "development"

    database_url: str = "postgresql+asyncpg://kira:kira@localhost:5432/kira_admin_service"
    redis_url: str = "redis://localhost:6379/5"
    kafka_bootstrap_servers: str = "localhost:9092"

    secret_key: str = "change-me-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    allowed_origins: list[str] = ["http://localhost:5173"]
    log_level: str = "INFO"


settings = Settings()

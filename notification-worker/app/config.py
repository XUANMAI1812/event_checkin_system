from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "sqlite:///./notification_worker.db"
    redis_url: str = "redis://localhost:6379/0"
    ticket_stream_name: str = "ticket_created"
    consumer_group: str = "notification_workers"
    consumer_name: str = "worker-1"
    smtp_host: str = "localhost"
    smtp_port: int = 1025
    smtp_from: str = "no-reply@event-checkin.local"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()

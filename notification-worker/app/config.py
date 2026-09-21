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

    read_block_ms: int = 5000
    reclaim_min_idle_ms: int = 60000  # pending qua nguong nay -> lay lai
    reclaim_interval_seconds: int = 30
    max_deliveries: int = 5
    dead_letter_stream_name: str = "ticket_created_dead"
    heartbeat_path: str = "/tmp/worker_heartbeat"  # healthcheck doc mtime file nay
    smtp_timeout_seconds: int = 10
    redis_socket_timeout_seconds: int = 15  # phai > readblockms/ 1000

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()

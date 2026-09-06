from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "sqlite:///./registration.db"
    jwt_private_key_path: str = "keys/private_key.pem"
    jwt_public_key_path: str = "keys/public_key.pem"
    jwt_algorithm: str = "RS256"
    ticket_qr_dir: str = "qrcodes"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()

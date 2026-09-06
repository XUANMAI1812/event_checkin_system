from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "sqlite:///./checkin.db"
    jwt_public_key_path: str = "keys/public_key.pem"
    jwt_algorithm: str = "RS256"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()

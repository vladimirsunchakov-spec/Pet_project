from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    service2_port: int = 8001
    service2_host: str = "0.0.0.0"

    database_url: str = "sqlite+aiosqlite:///./service.db"

    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
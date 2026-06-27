from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import PostgresDsn

class Settings(BaseSettings):
    postgres_url: PostgresDsn

    redis_url: str = "redis://localhost:6379/0"
    cache_ttl_seconds: int = 3600

    bio_service_url: str = "http://localhost:8001"

    circuit_breaker_failure_threshold: int = 5
    circuit_breaker_recovery_timeout: int = 30
    circuit_breaker_half_open_max_attempts: int = 1

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
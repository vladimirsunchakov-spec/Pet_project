from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import PostgresDsn
from typing import Set

SUCCESS_STATUS_CODE = (200, 201,204)
RETRYABLE_HTTP_STATUS_MIN = 500

class Settings(BaseSettings):
    postgres_url: PostgresDsn

    redis_url: str = "redis://localhost:6379/0"
    cache_ttl_seconds: int = 3600

    bio_service_url: str = "http://localhost:8001"
    bio_client_timeout: float = 10.0

    circuit_breaker_failure_threshold: int = 5
    circuit_breaker_recovery_timeout: int = 30
    circuit_breaker_half_open_max_attempts: int = 1

    retry_max_attempts: int = 3
    retry_wait_multiplier: int = 1
    retry_wait_min: int = 1
    retry_wait_max: int = 10

    non_retryable_statuses: Set[int] = {
        400,
        401,
        403,
        404,
        409,
        422,
    }

    retryable_statuses: Set[int] = {
        500,
        502,
        503,
        504,
    }

    success_statuses: Set[int] = {
        200,
        201,
        204,
    }

    debug: bool = False

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
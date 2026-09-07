from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import PostgresDsn
from typing import Set
from http import HTTPStatus

SUCCESS_STATUS_CODE = (200, 201,204)
RETRYABLE_HTTP_STATUS_MIN = 500

class Settings(BaseSettings):
    app_name: str = "PythonProject"
    app_env: str = "development"
    debug: bool = False

    postgres_url: PostgresDsn

    redis_url: str = "redis://localhost:6379/0"
    cache_ttl_seconds: int = 3600

    bio_service_url: str = "http://localhost:8001"
    bio_client_timeout: float = 10.0

    retry_max_attempts: int = 3
    retry_wait_multiplier: int = 1
    retry_wait_min: int = 1
    retry_wait_max: int = 10

    retryable_statuses: Set[int] = {
        HTTPStatus.INTERNAL_SERVER_ERROR,
        HTTPStatus.BAD_GATEWAY,
        HTTPStatus.SERVICE_UNAVAILABLE,
        HTTPStatus.GATEWAY_TIMEOUT,
    }



    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()

SUCCESS_STATUS_CODE = (
    HTTPStatus.OK,
    HTTPStatus.CREATED,
    HTTPStatus.NO_CONTENT,
)
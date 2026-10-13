from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import PostgresDsn
from http import HTTPStatus


class Settings(BaseSettings):
    app_name: str = "PythonProject"
    app_env: str = "development"
    debug: bool = False

    postgres_url: PostgresDsn

    redis_url: str = "redis://localhost:6379/0"
    cache_ttl_seconds: int = 3600

    bio_service_url: str = "http://localhost:8001"
    bio_client_timeout: float = 10.0
    bio_max_keepalive_connections: int = 10
    bio_max_connections: int = 20
    bio_get_path: str = "/bio/{author_id}"
    bio_create_path: str = "/bio/"
    bio_default_rating: float = 0.0
    bio_default_awards_count: int = 0

    retry_max_attempts: int = 3
    retry_wait_multiplier: int = 1
    retry_wait_min: int = 1
    retry_wait_max: int = 10

    retryable_statuses: set[int] = {
        HTTPStatus.INTERNAL_SERVER_ERROR,
        HTTPStatus.BAD_GATEWAY,
        HTTPStatus.SERVICE_UNAVAILABLE,
        HTTPStatus.GATEWAY_TIMEOUT,
    }

    bio_worker_claim_limit: int = 10
    bio_worker_poll_interval_seconds: float = 5.0
    bio_worker_retry_backoff_seconds: int = 60
    bio_worker_processing_timeout_seconds: int = 300
    bio_worker_max_concurrency: int = 5

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()

SUCCESS_STATUS_CODE = (
    HTTPStatus.OK,
    HTTPStatus.CREATED,
    HTTPStatus.NO_CONTENT,
)

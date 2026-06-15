import httpx
from typing import Optional
from uuid import UUID
from src.config import settings
from src.core.retry import with_retry, RetryConfig
from enum import Enum
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class CircuitState(str, Enum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"

class CircuitBreaker:
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 30,
        half_open_max_attempts: int = 1
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_attempts = half_open_max_attempts

        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._half_open_attempts = 0
        self._last_failure_time: Optional[datetime] = None

    @property
    def state(self) -> CircuitState:
        if self._state == CircuitState.OPEN:
            if self._last_failure_time and datetime.now() >= self._last_failure_time + timedelta(seconds=self.recovery_timeout):
                self._state = CircuitState.HALF_OPEN
                self._half_open_attempts = 0
        return self._state

    def record_success(self) -> None:
        logger.info(f"Circuit Breaker: recording SUCCESS, current state={self._state}")
        if self._state == CircuitState.HALF_OPEN:
            self._state = CircuitState.CLOSED
            self._failure_count = 0
            self._half_open_attempts = 0
        else:
            self._failure_count = 0

    def record_failure(self) -> None:
        logger.warning(f"Circuit Breaker: recording FAILURE, current state={self._state}, failure_count={self._failure_count}")
        if self._state == CircuitState.HALF_OPEN:
            self._half_open_attempts += 1
            if self._half_open_attempts >= self.half_open_max_attempts:
                self._state = CircuitState.OPEN
                self._last_failure_time = datetime.now()
                logger.warning(f"Circuit Breaker: OPEN after {self._half_open_attempts} failures in HALF_OPEN")
        elif self._state == CircuitState.CLOSED:
            self._failure_count += 1
            if self._failure_count >= self.failure_threshold:
                self._state = CircuitState.OPEN
                self._last_failure_time = datetime.now()
                logger.warning(f"Circuit Breaker: OPEN after {self._failure_count} failures")

    def is_allowed(self) -> bool:
        allowed = self.state in (CircuitState.CLOSED, CircuitState.HALF_OPEN)
        if not allowed:
            logger.warning(f"Circuit Breaker: REQUEST BLOCKED, state={self.state}")
        return allowed

class BioServiceClient:
    def __init__(self):
        self._base_url = settings.bio_service_url
        self._circuit_breaker = CircuitBreaker(
            failure_threshold=5,
            recovery_timeout=30,
            half_open_max_attempts=1
        )
    def _is_circuit_open(self) -> bool:
        return not self._circuit_breaker.is_allowed()

    @with_retry(RetryConfig(
        exceptions=(httpx.TimeoutException, httpx.HTTPStatusError),
        attempts=3,
        base_delay=1.0,
        max_delay=10.0,
        jitter=True
    ))
    async def _make_request(self, method: str, url: str, **kwargs) -> Optional[dict]:
        if self._is_circuit_open():
            logger.warning(f"Circuit breaker is OPEN for {url}")
            return None

        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.request(method, url, **kwargs)

                if response.status_code in (200, 201, 204):
                    self._circuit_breaker.record_success()
                    if response.status_code == 204:
                        return {"success": True}
                    return response.json()
                elif response.status_code == 404:
                    return None
                else:
                    self._circuit_breaker.record_failure()
                    response.raise_for_status()

        except (httpx.TimeoutException, httpx.HTTPStatusError) as e:
            self._circuit_breaker.record_failure()
            raise e

        return None

    async def get_bio_by_author_id(self, author_id: UUID) -> Optional[dict]:
        return await self._make_request(
            "GET",
            f"{self._base_url}/bio/{author_id}",
            headers={"Content-Type": "application/json"}
        )

    async def create_bio(self, author_id: UUID, rating: float = 0.0, awards_count: int = 0 ) -> Optional[dict]:
        return await self._make_request(
            "POST",
            f"{self._base_url}/bio/",
            json={
                "author_id": str(author_id),
                "rating": rating,
                "awards_count": awards_count,
                "biography": None
            },
            headers={"Content-Type": "application/json"}
        )

    async def update_bio(self, author_id: UUID, rating: Optional[float] = None, awards_count: Optional[int] = None ) -> Optional[dict]:
        data ={}
        if rating is not None:
            data["rating"] = rating
        if awards_count is not None:
            data["awards_count"] = awards_count

        if not data:
            return None

        return await self._make_request(
            "PUT",
            f"{self._base_url}/bio/{author_id}",
            json=data,
            headers={"Content-Type": "application/json"}
        )

    async def delete_bio(self, author_id: UUID) -> bool:
        result = await self._make_request(
            "DELETE",
            f"{self._base_url}/bio/{author_id}",
            headers={"Content-Type": "application/json"}
        )
        return result is not None



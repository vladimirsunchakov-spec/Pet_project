import httpx
from typing import Optional
from uuid import UUID
from src.config import settings
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception
from src.utils.circuit_breaker import CircuitBreaker
import logging
from src.exceptions import NotFoundError
from src.schemas.bio import BioCreateRequest

logger = logging.getLogger(__name__)

SUCCESS_STATUS_CODE = (200, 201, 204)

class CircuitBreakerOpenError(Exception):
    pass

def is_retryable_exception(exception: Exception) -> bool:
    if isinstance(exception, httpx.TimeoutException):
        return True

    if isinstance(exception, httpx.HTTPStatusError):
        status_code = exception.response.status_code
        return 500 <= status_code < 600

    return False

class BioServiceClient:
    def __init__(self):
        self._base_url = settings.bio_service_url
        self._timeout = settings.bio_client_timeout
        self._circuit_breaker = CircuitBreaker(
            failure_threshold=settings.circuit_breaker_failure_threshold,
            recovery_timeout=settings.circuit_breaker_recovery_timeout,
            half_open_max_attempts=settings.circuit_breaker_half_open_max_attempts
        )
    def _is_circuit_open(self) -> bool:
        return not self._circuit_breaker.is_allowed()

    @retry(
        retry=retry_if_exception(is_retryable_exception),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True
    )
    async def _execute_request(self, method: str, url: str, **kwargs) -> httpx.Response:
        if self._is_circuit_open():
            logger.warning(f"Circuit Breaker is OPEN for {url}")
            raise CircuitBreakerOpenError(f"Circuit Breaker is OPEN for {url}")

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            return await client.request(method, url, **kwargs)

    async def _make_request(self, method: str, url: str, resource_type: str = "Bio", **kwargs) -> Optional[dict]:

        try:
            response = await self._execute_request(method, url, **kwargs)

            if response.status_code in SUCCESS_STATUS_CODE:
                self._circuit_breaker.record_success()
                if response.status_code == 204:
                    return {"success": True}
                return response.json()
            elif response.status_code == 404:
                raise NotFoundError(resource_type, f"url={url}")
            elif 400 <= response.status_code < 500:
                self._circuit_breaker.record_failure()
                response.raise_for_status()
            else:
                self._circuit_breaker.record_failure()
                response.raise_for_status()

        except (httpx.TimeoutException, httpx.HTTPStatusError) as e:
            self._circuit_breaker.record_failure()
            raise e
        except CircuitBreakerOpenError:
            return None

    async def get_bio_by_author_id(self, author_id: UUID) -> Optional[dict]:
        return await self._make_request(
            "GET",
            f"{self._base_url}/bio/{author_id}",
            resource_type="Bio",
            headers={"Content-Type": "application/json"}
        )

    async def create_bio(self, author_id: UUID, rating: float = 0.0, awards_count: int = 0 ) -> Optional[dict]:
        request_data = BioCreateRequest(
            author_id=author_id,
            rating=rating,
            awards_count=awards_count,
            biography= None
        )

        return await self._make_request(
            "POST",
            f"{self._base_url}/bio/",
            resource_type="Bio",
            json=request_data.model_dump(),
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
            resource_type="Bio",
            json=data,
            headers={"Content-Type": "application/json"}
        )

    async def delete_bio(self, author_id: UUID) -> bool:
        result = await self._make_request(
            "DELETE",
            f"{self._base_url}/bio/{author_id}",
            resource_type="Bio",
            headers={"Content-Type": "application/json"}
        )
        return result is not None



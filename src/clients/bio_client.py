import httpx
from typing import Optional
from uuid import UUID
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception
import logging
from src.exceptions import NotFoundError
from src.schemas.bio import BioCreateRequest, BioSuccessResponse, BioResponse
from src.config import settings, RETRYABLE_HTTP_STATUS_MIN

logger = logging.getLogger(__name__)

def is_retryable_exception(exception: Exception) -> bool:
    if isinstance(exception, httpx.TimeoutException):
        return True

    if isinstance(exception, httpx.HTTPStatusError):
        status_code = exception.response.status_code
        return status_code >= RETRYABLE_HTTP_STATUS_MIN

    return False

class BioServiceClient:
    def __init__(self):
        self._base_url = settings.bio_service_url
        self._timeout = settings.bio_client_timeout

    @retry(
        retry=retry_if_exception(is_retryable_exception),
        stop=stop_after_attempt(settings.retry_max_attempts),
        wait=wait_exponential(
            multiplier=settings.retry_wait_multiplier,
            min=settings.retry_wait_min,
            max=settings.retry_wait_max
        ),
        reraise=True
    )
    async def _execute_request(self, method: str, url: str, **kwargs) -> httpx.Response:

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            return await client.request(method, url, **kwargs)

    async def _get(self, url: str) -> Optional[dict]:
        try:
            response = await self._execute_request("GET", url)

            if response.status_code == 200:
                return BioResponse.model_validate(response.json()).model_dump()

            if response.status_code == 404:
                logger.info(f"Resource not found: {url}")
                raise NotFoundError("Bio", f"url={url}")

            if 400 <= response.status_code < 500:
                logger.error(f"Client error: {response.status_code}: {response.text}")
                raise ValueError(f"Client error {response.status_code}: {response.text}")

            if response.status_code >= 500:
                logger.error(f"Server error {response.status_code}: {response.text}")
                response.raise_for_status()

        except httpx.TimeoutException as e:
            logger.error(f"Timeout error for {url}: {e}")
            raise e

        except httpx.HTTPStatusError as e:
            status_code = e.response.status_code
            if status_code >= 500:
                logger.error(f"HTTP error {status_code} for {url}: {e}")
            else:
                logger.warning(f"HTTP client error {status_code} for {url}: {e}")
            raise e

        except Exception as e:
            logger.error(f"Unexpected error for {url}: {e}")
            raise e

    async def _post(self, url: str, data: dict) -> Optional[dict]:
        try:
            response = await self._execute_request("POST", url, json=data)

            if response.status_code == 201:
                return BioResponse.model_validate(response.json()).model_dump()

            if 400 <= response.status_code < 500:
                logger.error(f"Client error: {response.status_code}: {response.text}")
                raise ValueError(f"Client error {response.status_code}: {response.text}")

            if response.status_code >= 500:
                logger.error(f"Server error {response.status_code}: {response.text}")
                raise ValueError(f"Server error {response.status_code}: {response.text}")

        except httpx.TimeoutException as e:
            logger.error(f"Timeout error for {url}: {e}")
            raise e

        except httpx.HTTPStatusError as e:
            status_code = e.response.status_code
            if status_code >= 500:
                logger.error(f"HTTP error {status_code} for {url}: {e}")
            else:
                logger.warning(f"HTTP client error {status_code} for {url}: {e}")
            raise e

        except Exception as e:
            logger.error(f"Unexpected error for {url}: {e}")
            raise e

    async def get_bio_by_author_id(self, author_id: UUID) -> Optional[dict]:
        return await self._get(f"{self._base_url}/bio/{author_id}")

    async def create_bio(self, author_id: UUID, rating: float = 0.0, awards_count: int = 0 ) -> Optional[dict]:
        request_data = BioCreateRequest(
            author_id=author_id,
            rating=rating,
            awards_count=awards_count,
        )
        return await self._post(f"{self._base_url}/bio/", request_data.model_dump())



from typing import Optional, Set
from uuid import UUID
from httpx import TimeoutException
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception
import logging
from src.exceptions import NotFoundError, BioServiceUnavailableError, BioServiceError
from src.schemas.bio import BioCreateRequest, BioResponse, BioStatusUpdate
from src.config import settings
from http import HTTPStatus
import httpx

logger = logging.getLogger(__name__)

class BioStatusHandler:
    RETRYABLE_STATUSES: Set[int] = settings.retryable_statuses

    @classmethod
    def is_retryable(cls, status_code: int) -> bool:
        return status_code not in cls.RETRYABLE_STATUSES

    @classmethod
    def is_success(cls, status_code: int) -> bool:
        return httpx.codes.is_success(status_code)

    @classmethod
    def is_non_retryable(cls, status_code: int) -> bool:
        return not cls.is_retryable(status_code) and not cls.is_success(status_code)

    @classmethod
    def get_status_type(cls, status_code: int) -> str:
        if cls.is_success(status_code):
            return "success"
        if cls.is_retryable(status_code):
            return "retryable"
        return "non_retryable"

def is_retryable_exception(exception: Exception) -> bool:
    if isinstance(exception, httpx.RequestError):
        logger.warning(f"Network error, will retry: {exception}")
        return True

    if isinstance(exception,TimeoutException):
        return True

    if isinstance(exception, BioServiceUnavailableError):
        return True

    return False

class BioServiceClient:
    def __init__(self):
        self._base_url = settings.bio_service_url
        self._timeout = settings.bio_client_timeout
        self._client = httpx.AsyncClient(timeout=self._timeout, limits=httpx.Limits(max_keepalive_connections=10, max_connections=20))

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def close(self):
        await self._client.aclose()
        logger.info(f"BioClientService clised")


    async def _execute_request(self, method: str, url: str, **kwargs) -> httpx.Response:
        return await self._client.request(method, url, **kwargs)

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

    async def _handle_response(
        self,
        response: httpx.Response,
        url: str,
    ) -> BioResponse:
        status_code = response.status_code
        status_type = BioStatusHandler.get_status_type(status_code)

        if status_type == "success":
            try:
                return BioResponse.model_validate(response.json())
            except Exception as e:
                logger.error(f"Failed to parse response from {url}: {e}")
                raise BioServiceError(
                    message=f"Invalid response format from {url}",
                    status_code=status_code,
                    details={"url": url, "error": str(e)},
                )

        if status_code == 404:
            logger.info(f"Response not found: {url}")
            raise NotFoundError("Bio", f"url={url}")

        if status_type == "non_retryable":
            logger.error(f"Client error {status_code} from {url}: {response.text}")
            raise BioServiceError(
                message=f"Client error {status_code}: {response.text}",
                status_code=status_code,
                details={"url": url, "retryable": False}
            )

        if status_type == "retryable":
            logger.warning(f"Retryable error {status_code} from {url}: {response.text}")
            raise BioServiceUnavailableError(
                message=f"Server error {status_code}: {response.text}",
                status_code=status_code,
                details={"url": url, "retryable": True}
            )

        logger.error(f"Unexpected status {status_code} from {url}: {response.text}")
        raise BioServiceError(
            message=f"Unexpected status {status_code}",
            status_code=status_code,
            details={"url": url}
        )

    async def _get(self, url: str) -> BioResponse:
        try:
            response = await self._execute_request("GET", url)
            return await self._handle_response(response, url)
        except (BioServiceError, BioServiceUnavailableError, NotFoundError):
            raise
        except Exception as e:
            logger.error(f"Unexpected error for {url}: {e}")
            raise BioServiceError(
                message=f"Unexpected error: {e}",
                status_code=500,
                details={"url": url}
            )

    async def _post(self, url: str, data: dict) -> BioResponse:
        try:
            response = await self._execute_request("POST", url, json=data)
            return await self._handle_response(response, url)
        except (BioServiceError, BioServiceUnavailableError, NotFoundError):
            raise
        except Exception as e:
            logger.error(f"Unexpected error for {url}: {e}")
            raise BioServiceError(
                message=f"Unexpected error: {e}",
                status_code=500,
                details={"url": url}
            )

    async def get_bio_by_author_id(self, author_id: UUID) -> BioResponse:
        return await self._get(f"{self._base_url}/bio/{author_id}")

    async def create_bio(self, author_id: UUID, rating: float = 0.0, awards_count: int = 0 ) -> BioResponse:
        request_data = BioCreateRequest(
            author_id=author_id,
            rating=rating,
            awards_count=awards_count,
        )
        return await self._post(f"{self._base_url}/bio/", request_data.model_dump())

    async def update_bio_status(self, author_id: UUID, status: str) -> BioResponse:
        url = f"{self._base_url}/bio/{author_id}/status"
        data = {"status": status}
        return await self._patch(url, data)

    async def _patch(self, url: str, data: dict) -> BioResponse:
        try:
            response = await self._execute_request("PATCH", url, json=data)
            return await self._handle_response(response, url)
        except (BioServiceError, BioServiceUnavailableError, NotFoundError):
            raise
        except Exception as e:
            logger.error(f"Unexpected error for {url}: {e}")
            raise BioServiceError(
                message=f"Unexpected error: {e}",
                status_code=500,
                details={"url": url}
            )


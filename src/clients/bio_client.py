import httpx
from typing import Optional, Set
from uuid import UUID
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception
import logging
from src.exceptions import NotFoundError, BioServiceClientError, BioServiceUnavailableError, BioServiceError
from src.schemas.bio import BioCreateRequest, BioResponse
from src.config import settings

logger = logging.getLogger(__name__)

class BioStatusHandler:
    NON_RETRYABLE_STATUSES: Set[int] = settings.non_retryable_statuses

    @classmethod
    def is_retryable(cls, status_code: int) -> bool:
        return status_code not in cls.NON_RETRYABLE_STATUSES

    @classmethod
    def is_success(cls, status_code: int) -> bool:
        return 200 <= status_code < 300

    @classmethod
    def get_status_type(cls, status_code: int) -> str:
        if cls.is_success(status_code):
            return "success"
        if cls.is_retryable(status_code):
            return "retryable"
        return "non_retryable"

def is_retryable_exception(exception: Exception) -> bool:
    if isinstance(exception, httpx.TimeoutException):
        return True

    if isinstance(exception, BioServiceUnavailableError):
        return True

    if isinstance(exception, httpx.HTTPStatusError):
        return BioStatusHandler.is_retryable(exception.response.status_code)
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

    async def _handle_response(
        self,
        response: httpx.Response,
        url: str,
    ) -> Optional[dict]:
        status_code = response.status_code
        status_type = BioStatusHandler.get_status_type(status_code)

        if status_type == "success":
            try:
                return BioResponse.model_validate(response.json()).model_dump()
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
            raise BioServiceClientError(
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

    async def _get(self, url: str) -> Optional[dict]:
        try:
            response = await self._execute_request("GET", url)
            return await self._handler_response(response, url)
        except (BioServiceError, BioServiceUnavailableError, NotFoundError):
            raise
        except Exception as e:
            logger.error(f"Unexpected error for {url}: {e}")
            raise BioServiceError(
                message=f"Unexpected error: {e}",
                status_code=500,
                details={"url": url}
            )

    async def _post(self, url: str, data: dict) -> Optional[dict]:
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

    async def get_bio_by_author_id(self, author_id: UUID) -> Optional[dict]:
        return await self._get(f"{self._base_url}/bio/{author_id}")

    async def create_bio(self, author_id: UUID, rating: float = 0.0, awards_count: int = 0 ) -> Optional[dict]:
        request_data = BioCreateRequest(
            author_id=author_id,
            rating=rating,
            awards_count=awards_count,
        )
        return await self._post(f"{self._base_url}/bio/", request_data.model_dump())


import httpx
from typing import Optional, Dict, Set
from uuid import UUID
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception
import logging
from src.exceptions import NotFoundError
from src.schemas.bio import BioCreateRequest, BioResponse
from src.config import settings, RETRYABLE_HTTP_STATUS_MIN

logger = logging.getLogger(__name__)

class BioServiceError(Exception):
    pass

class BioStatusHandler:
    NON_RETRYABLE_STATUSES: Set[int] = {
        400,
        401,
        403,
        404,
        409,
        422,
    }

    RETRYABLE_STATUSES: Set[int] = {
        500,
        502,
        503,
        504,
    }

    SUCCESS_STATUSES: Set[int] = {
        200,
        201,
    }

    @classmethod
    def is_retryable(cls, status_code: int) -> bool:
        return status_code in cls.RETRYABLE_STATUSES

    @classmethod
    def is_success(cls, status_code: int) -> bool:
        return status_code in cls.SUCCESS_STATUSES


def is_retryable_exception(exception: Exception) -> bool:
    if isinstance(exception, httpx.TimeoutException):
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

        if BioStatusHandler.is_success(status_code):
            try:
                return BioResponse.model_validate(response.json()).model_dump()
            except Exception as e:
                logger.error(f"Failed to parse response from {url}: {e}")
                raise BioServiceError(f"Invalid response format from {url}")

        if status_code == 404:
            logger.info(f"Response not found: {url}")
            raise NotFoundError("Bio", f"url={url}")

        error_msg = f"Bio service error: {status_code}: {response.text}"
        logger.error(f"{error_msg} from {url}")
        raise BioServiceError(error_msg)

    async def _get(self, url: str) -> Optional[dict]:
        try:
            response = await self._execute_request("GET", url)
            return await self._handler_response(response, url)

        except (BioServiceError, NotFoundError):
            raise

        except Exception as e:
            logger.error(f"Unexpected error for {url}: {e}")
            raise BioServiceError(f"Unexpected error: {e}")

    async def _post(self, url: str, data: dict) -> Optional[dict]:
        try:
            response = await self._execute_request("POST", url, json=data)
            return await self._handle_response(response, url)
        except (BioServiceError, NotFoundError):
            raise
        except Exception as e:
            logger.error(f"Unexpected error for {url}: {e}")
            raise BioServiceError(f"Unexpected error: {e}")

    async def get_bio_by_author_id(self, author_id: UUID) -> Optional[dict]:
        return await self._get(f"{self._base_url}/bio/{author_id}")

    async def create_bio(self, author_id: UUID, rating: float = 0.0, awards_count: int = 0 ) -> Optional[dict]:
        request_data = BioCreateRequest(
            author_id=author_id,
            rating=rating,
            awards_count=awards_count,
        )
        return await self._post(f"{self._base_url}/bio/", request_data.model_dump())


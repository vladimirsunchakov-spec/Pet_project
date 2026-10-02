from uuid import UUID
import json
import logging

import httpx
from http import HTTPStatus
from pydantic import ValidationError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception

from src.config import settings
from src.exceptions import (
    NotFoundError,
    ExternalServiceUnavailableError,
    ExternalServiceError,
    BioResponseParseError,
)
from src.schemas.bio import BioCreateRequest, BioResponse
from src.schemas.exceptions import ErrorDetails
from src.utils.bio_http import BioStatusHandler, is_retryable_exception

logger = logging.getLogger(__name__)

_RETRY = dict(
    retry=retry_if_exception(is_retryable_exception),
    stop=stop_after_attempt(settings.retry_max_attempts),
    wait=wait_exponential(
        multiplier=settings.retry_wait_multiplier,
        min=settings.retry_wait_min,
        max=settings.retry_wait_max,
    ),
    reraise=True,
)


class BioServiceClient:
    def __init__(self) -> None:
        self._base_url = settings.bio_service_url
        self._timeout = settings.bio_client_timeout
        self._client = httpx.AsyncClient(
            timeout=self._timeout,
            limits=httpx.Limits(
                max_keepalive_connections=settings.bio_max_keepalive_connections,
                max_connections=settings.bio_max_connections,
            ),
        )

    async def __aenter__(self) -> "BioServiceClient":
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close()

    async def close(self) -> None:
        await self._client.aclose()
        logger.info("BioServiceClient closed")

    async def _execute_request(self, method: str, url: str, **kwargs) -> httpx.Response:
        return await self._client.request(method, url, **kwargs)

    def _handle_response(self, response: httpx.Response, url: str) -> BioResponse:
        status_code = response.status_code

        if BioStatusHandler.is_success(status_code):
            try:
                return BioResponse.model_validate(response.json())
            except (ValidationError, ValueError, json.JSONDecodeError) as e:
                logger.error("Failed to parse response from %s: %s", url, e)
                raise BioResponseParseError(
                    message=f"Invalid response format from {url}",
                    status_code=status_code,
                    details=ErrorDetails(url=url, error=str(e)),
                )

        if status_code == HTTPStatus.NOT_FOUND:
            raise NotFoundError("Bio", f"url={url}")

        if BioStatusHandler.is_retryable(status_code):
            raise ExternalServiceUnavailableError(
                message=f"Server error {status_code}: {response.text}",
                status_code=status_code,
                details=ErrorDetails(url=url, error=response.text, retryable=True),
            )

        raise ExternalServiceError(
            message=f"Client error {status_code}: {response.text}",
            status_code=status_code,
            details=ErrorDetails(url=url, error=response.text, retryable=False),
        )

    @retry(**_RETRY)
    async def _get(self, url: str) -> BioResponse:
        response = await self._execute_request("GET", url)
        return self._handle_response(response, url)

    @retry(**_RETRY)
    async def _post(self, url: str, data: dict, headers: dict) -> BioResponse:
        response = await self._execute_request("POST", url, json=data, headers=headers)
        return self._handle_response(response, url)

    async def get_bio_by_author_id(self, author_id: UUID) -> BioResponse:
        return await self._get(f"{self._base_url}/bio/{author_id}")

    async def create_bio(
        self,
        author_id: UUID,
        idempotency_key: str,
        rating: float = 0.0,
        awards_count: int = 0,
    ) -> BioResponse:
        request_data = BioCreateRequest(
            author_id=author_id,
            rating=rating,
            awards_count=awards_count,
        )
        headers = {"Idempotency-Key": idempotency_key}
        return await self._post(
            f"{self._base_url}/bio/",
            request_data.model_dump(mode="json"),
            headers=headers,
        )

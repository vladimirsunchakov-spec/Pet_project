from uuid import UUID
import logging

import httpx
from http import HTTPStatus
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception

from src.config import settings
from src.exceptions import (
    NotFoundError,
    ExternalServiceUnavailableError,
    ExternalServiceError,
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
        self._base_url = settings.bio_service_url.rstrip("/")
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

    def _url(self, path_template: str, **params: object) -> str:
        return f"{self._base_url}{path_template.format(**params)}"

    def _handle_response(self, response: httpx.Response, url: str) -> BioResponse:
        status_code = response.status_code

        if BioStatusHandler.is_success(status_code):
            return BioResponse.model_validate(response.json())

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
        response = await self._client.get(url)
        return self._handle_response(response, url)

    @retry(**_RETRY)
    async def _post(self, url: str, data: dict, headers: dict) -> BioResponse:
        response = await self._client.post(url, json=data, headers=headers)
        return self._handle_response(response, url)

    async def get_bio_by_author_id(self, author_id: UUID) -> BioResponse:
        url = self._url(settings.bio_get_path, author_id=author_id)
        return await self._get(url)

    async def create_bio(
        self,
        request: BioCreateRequest,
        idempotency_key: str,
    ) -> BioResponse:
        headers = {"Idempotency-Key": idempotency_key}
        url = self._url(settings.bio_create_path)
        return await self._post(
            url,
            request.model_dump(mode="json"),
            headers=headers,
        )

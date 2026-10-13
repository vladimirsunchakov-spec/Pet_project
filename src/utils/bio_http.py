from typing import Set
import logging
import httpx
from src.config import settings
from src.exceptions import ExternalServiceUnavailableError

logger = logging.getLogger(__name__)

class BioStatusHandler:
    RETRYABLE_STATUSES: Set[int] = settings.retryable_statuses

    @classmethod
    def is_retryable(cls, status_code: int) -> bool:
        return status_code in cls.RETRYABLE_STATUSES

    @classmethod
    def is_success(cls, status_code: int) -> bool:
        return httpx.codes.is_success(status_code)

def is_retryable_exception(exception: BaseException) -> bool:
    if isinstance(exception, httpx.RequestError):
        logger.warning("Network error, will retry: %s", exception)
        return True
    if isinstance(exception, ExternalServiceUnavailableError):
        return True
    return False
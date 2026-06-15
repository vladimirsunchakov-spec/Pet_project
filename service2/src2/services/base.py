import logging
from typing import Optional, Any, Dict
from service2.src2.core.logger import get_request_id

class BaseService:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def _log_info(self, message: str, **kwargs: Any) -> None:
        log_data = self._prepare_log_data(message, kwargs)
        self.logger.info(log_data, extra={"props": kwargs})

    def _log_warning(self, message: str, **kwargs: Any) -> None:
        log_data = self._prepare_log_data(message, kwargs)
        self.logger.warning(log_data, extra={"props": kwargs})

    def _log_error(self, message: str, **kwargs: Any) -> None:
        log_data = self._prepare_log_data(message, kwargs)
        self.logger.error(log_data, extra={"props": kwargs})

    def _prepare_log_data(self, message: str, kwargs: Dict[str, Any]) -> str:
        requests_id = get_request_id()
        if requests_id:
            kwargs["request_id"] = requests_id

        if kwargs:
            params = " | ".join([f"{k}={v}" for k, v in kwargs.items()])
            return f"{message} | {params}"
        return message

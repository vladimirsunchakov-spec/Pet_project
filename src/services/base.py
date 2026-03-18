import logging
from typing import Optional
from uuid import UUID

class BaseService:

    @classmethod
    def _get_logger(cls):
        return logging.getLogger(cls.__name__)

    @classmethod
    def _log_error(cls, message: str, entity_id: Optional[UUID] = None, **kwargs):
        extra = {"entity_id": str(entity_id) if entity_id else None, **kwargs}
        cls._get_logger().error(message, extra={"extra": extra})

    @classmethod
    def _log_info(cls, message: str, entity_id: Optional[UUID] = None, **kwargs):
        extra = {"entity_id": str(entity_id) if entity_id else None, **kwargs}
        cls._get_logger().info(message, extra={"extra": extra})

    @classmethod
    def _log_warning(cls, message: str, entity_id: Optional[UUID] = None, **kwargs):
        extra = {"entity_id": str(entity_id) if entity_id else None, **kwargs}
        cls._get_logger().warning(message, extra={"extra": extra})

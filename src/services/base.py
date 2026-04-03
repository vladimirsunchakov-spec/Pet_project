import logging
from typing import Type, Any
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.exceptions import ConflictError

class BaseService:

    @classmethod
    def _get_logger(cls):
        return logging.getLogger(cls.__name__)

    @classmethod
    def _log_error(cls, message: str, entity_id: UUID | None = None, **kwargs):
        extra = {"entity_id": str(entity_id) if entity_id else None, **kwargs}
        cls._get_logger().error(message, extra={"extra": extra})

    @classmethod
    def _log_info(cls, message: str, entity_id: UUID | None = None, **kwargs):
        extra = {"entity_id": str(entity_id) if entity_id else None, **kwargs}
        cls._get_logger().info(message, extra={"extra": extra})

    @classmethod
    def _log_warning(cls, message: str, entity_id: UUID | None = None, **kwargs):
        extra = {"entity_id": str(entity_id) if entity_id else None, **kwargs}
        cls._get_logger().warning(message, extra={"extra": extra})

    @classmethod
    async def _check_uniqueness(
        cls,
        db: AsyncSession,
        model: Type[Any],
        fields: dict[str, Any],
        exclude_id: UUID | None = None,
        request_id: str | None = None
    ) -> None:
        for field_name, field_value in fields.items():
            query = select(model).where(getattr(model, field_name) == field_value)
            if exclude_id:
                query = query.where(getattr(model, "id") != exclude_id)
            result = await db.execute(query)
            if result.scalar_one_or_none():
                cls._get_logger().error(
                    f"{field_name.capitalize()} already exist",
                    extra={"extra": {field_name: field_value, "request_id": request_id}}
                    )
            raise ConflictError(field_name.capitalize(), field_value)
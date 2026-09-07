import logging
from typing import Optional
from pydantic import BaseModel
import ujson
from datetime import datetime, timezone
import sys

class LogSchema(BaseModel):
    time: str
    level: str
    module: str
    function: str
    line: int
    message: str
    request_id: Optional[str] = None
    entity_id: Optional[str] = None
    user_id: Optional[str] = None
    author_id: Optional[str] = None
    country_id: Optional[str] = None

class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord):
        log_data = LogSchema(
            time=datetime.now(timezone.utc).isoformat(),
            level=record.levelname,
            module=record.module,
            function=record.funcName,
            line=record.lineno,
            message=record.getMessage(),
            request_id=getattr(record, 'request_id', None),
            entity_id=getattr(record, 'entity_id', None),
            user_id=getattr(record, 'user_id', None),
        )

        extra_fields = getattr(record, 'extra', {})
        if extra_fields:
            for key, value in extra_fields.items():
                if hasattr(log_data, key):
                    setattr(log_data, key, value)

        return log_data.model_dump_json()

def setup_logging():
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())
    root_logger.addHandler(handler)

    return root_logger

logger = logging.getLogger(__name__)
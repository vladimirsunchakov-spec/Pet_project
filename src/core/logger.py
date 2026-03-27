import logging
import sys
import ujson
from datetime import datetime

class JSONEFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "time": datetime.now().isoformat(),
            "level": record.levelname,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "message": record.getMessage(),
        }
        if hasattr(record, "request_id"):
            log_record["request_id"] = record.request_id
        if hasattr(record, "extra"):
            log_record.update(record.extra)
        return ujson.dumps(log_record)

def setup_logging():
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONEFormatter())
    root_logger.addHandler(handler)

    return root_logger

logger = logging.getLogger(__name__)
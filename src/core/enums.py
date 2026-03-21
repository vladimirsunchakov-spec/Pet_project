from enum import Enum

class StatusEnum(str, Enum):
    OK = "ok"
    DELETED = "deleted"
    CREATED = "created"
    UPDATED = "updated"
    ERROR = "error"

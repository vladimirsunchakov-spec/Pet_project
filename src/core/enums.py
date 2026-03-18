from enum import Enum

class StatusEnum(str, Enum):
    OK = "oк"
    DELETED = "deleted"
    CREATED = "created"
    UPDATED = "updated"
    ERROR = "error"

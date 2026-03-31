from enum import Enum

class StatusEnum(str, Enum):
    OK = "OK"
    DELETED = "DELETED"
    CREATED = "CREATED"
    UPDATED = "UPDATED"
    ERROR = "ERROR"

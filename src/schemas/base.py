from pydantic import BaseModel
from src.core.enums import StatusEnum

class StatusResponse(BaseModel):
    status: StatusEnum

    class Config:
        from_attributes = True
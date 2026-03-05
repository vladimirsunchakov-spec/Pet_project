from pydantic import BaseModel


class StatusResponse(BaseModel):
    status: str

    class Config:
        from_attributes = True
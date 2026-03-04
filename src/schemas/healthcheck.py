from pydantic import BaseModel


class HealthCheckResponse(BaseModel):
    status: str

    class Config:
        from_attributes = True
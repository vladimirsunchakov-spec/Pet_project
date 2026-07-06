from pydantic import BaseModel, Field
from uuid import UUID
from typing import Optional

class BioCreateRequest(BaseModel):
    author_id: UUID
    rating: float = Field(default=0.0, ge=0, le=10.0, description="Рейтинг автора от 0 до 10")
    awards_count: int = Field(default=0, ge=0, description="Количество наград")
    biography: Optional[str] = Field(None, max_length=1000, description="Биография автора")

class BioSuccessResponse(BaseModel):
    success:bool = True

class BioResponse(BaseModel):
    id: UUID
    author_id: UUID
    rating: float
    awards_count: int
    biography: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class BioUpdateRequest(BaseModel):
    rating: Optional[float] = Field(None, ge=0, le=10.0)
    awards_count: Optional[int] = Field(None, ge=0)
    biography: Optional[str] = Field(None, max_length=1000)

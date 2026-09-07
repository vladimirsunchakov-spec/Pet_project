from pydantic import BaseModel, Field
from uuid import UUID
from typing import Optional
from datetime import datetime

class BioCreateRequest(BaseModel):
    author_id: UUID
    rating: float = Field(default=0.0, ge=0, le=10.0, description="Рейтинг автора от 0 до 10")
    awards_count: int = Field(default=0, ge=0, description="Количество наград")
    biography: Optional[str] = Field(None, max_length=1000, description="Биография автора")

class BioResponse(BaseModel):
    id: UUID
    author_id: UUID
    rating: float
    awards_count: int
    biography: Optional[str]
    status: str = Field(default="active", description="Статус bio: active или deleted")
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class BioStatusUpdate(BaseModel):
    status: str = Field(..., description="Статус: active или deleted")
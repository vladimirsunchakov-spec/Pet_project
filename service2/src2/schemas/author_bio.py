from pydantic import BaseModel, Field, field_validator
from uuid import UUID
from typing import Optional
from service2.src2.exceptions import ValidationError

class BioCreate(BaseModel):
    author_id: UUID = Field(..., description="ID автора из основного списка")
    rating: float = Field(default=0.0, ge=0.0, le=10.0, description="Рейтинг от 0 до 10")
    awards_count: int = Field(default=0, ge=0, description="Количество наград")
    biography: Optional[str] = Field(None, max_length=1000, description="Биография")

    @field_validator("rating")
    @classmethod
    def validate_rating(cls, v: float) -> float:
        if v < 0 or v > 10:
            raise ValidationError("Rating must be between 0 and 10")
        return v

    @field_validator("awards_count")
    @classmethod
    def validate_awards_count(cls, v: int) -> int:
        if v < 0:
            raise ValidationError("Awards count cannot be negative")
        return v

class BioUpdate(BaseModel):
    rating: Optional[float] = Field(None, ge=0.0, le=10.0, description="Рейтинг от 0 до 10")
    awards_count: Optional[int] = Field(None, ge=0, description="Количество наград")
    biography: Optional[str] = Field(None, max_length=1000, description="Биография")

    @field_validator("rating")
    @classmethod
    def validate_rating(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and (v < 0 or v > 10):
            raise ValidationError("Rating must be between 0 and 10")
        return v

    @field_validator("awards_count")
    @classmethod
    def validate_awards_count(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and v < 0:
            raise ValidationError("Awards count cannot be negative")
        return v

class BioResponse(BaseModel):
    id: UUID
    author_id: UUID
    rating: float
    awards_count: int
    biography: Optional[str] = None

    class Config:
        from_attributes = True



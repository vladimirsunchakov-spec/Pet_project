from pydantic import BaseModel, Field
from uuid import UUID
from typing import Optional

class BioCreateRequest(BaseModel):
    author_id: UUID
    rating: float = Field(default=0.0, ge=0, le=10.0)
    awards_count: int = Field(default=0, ge=0)
    biography: Optional[str] = None
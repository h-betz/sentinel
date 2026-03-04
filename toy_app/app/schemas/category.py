from datetime import datetime

from pydantic import BaseModel


class CategoryResponse(BaseModel):
    id: int
    name: str
    description: str | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel

from ..models.call import CallStatus


class CallCreate(BaseModel):
    service_level: str = "standard"
    filename: str
    metadata: dict | None = None


class CallOut(BaseModel):
    id: UUID
    filename: str
    storage_path: str
    status: CallStatus
    service_level: str
    created_at: datetime

    class Config:
        orm_mode = True


class CallList(BaseModel):
    items: list[CallOut]

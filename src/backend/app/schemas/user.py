from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, EmailStr


class UserOut(BaseModel):
    id: UUID
    email: EmailStr
    company_id: UUID
    role: str
    created_at: datetime

    class Config:
        orm_mode = True

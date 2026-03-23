from pydantic import BaseModel, EmailStr


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    email: str | None = None
    company_id: str | None = None


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    company: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str

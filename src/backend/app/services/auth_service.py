from datetime import timedelta
from sqlalchemy.orm import Session

from ..models.company import Company
from ..models.user import User
from ..schemas.auth import UserCreate, UserLogin
from ..auth.security import get_password_hash, verify_password, create_access_token
from ..config import get_settings

settings = get_settings()


def register_user(db: Session, payload: UserCreate) -> User:
    company = db.query(Company).filter(Company.name == payload.company).first()
    if not company:
        company = Company(name=payload.company)
        db.add(company)
        db.flush()

    user = User(email=payload.email, hashed_password=get_password_hash(payload.password), company_id=company.id)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, payload: UserLogin) -> str | None:
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        return None
    token = create_access_token(
        {"sub": user.email, "company_id": str(user.company_id)},
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
    )
    return token

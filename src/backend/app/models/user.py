from datetime import datetime
import uuid
from sqlalchemy import Column, DateTime, String, ForeignKey, Uuid

from ..db import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    company_id = Column(Uuid, ForeignKey("companies.id"), nullable=False)
    role = Column(String, default="user")
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

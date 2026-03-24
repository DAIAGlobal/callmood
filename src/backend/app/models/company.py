from datetime import datetime
from sqlalchemy import Column, DateTime, String, Uuid
import uuid

from ..db import Base


class Company(Base):
    __tablename__ = "companies"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False, unique=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

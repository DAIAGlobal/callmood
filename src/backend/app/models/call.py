from datetime import datetime
import uuid
from sqlalchemy import Column, DateTime, Enum, Float, ForeignKey, String, Text, Uuid, JSON
import enum

from ..db import Base


class CallStatus(str, enum.Enum):
    pending = "pending"
    processing = "processing"
    completed = "completed"
    error = "error"


class Call(Base):
    __tablename__ = "calls_api"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    company_id = Column(Uuid, ForeignKey("companies.id"), nullable=False)
    user_id = Column(Uuid, ForeignKey("users.id"), nullable=True)
    filename = Column(String, nullable=False)
    storage_path = Column(String, nullable=False)
    duration_seconds = Column(Float)
    status = Column(Enum(CallStatus), default=CallStatus.pending, nullable=False)
    service_level = Column(String, default="standard")
    error_message = Column(Text)
    call_metadata = Column(JSON)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

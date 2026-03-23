from datetime import datetime
import uuid
from sqlalchemy import Column, DateTime, Enum, Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
import enum

from ..db import Base


class CallStatus(str, enum.Enum):
    pending = "pending"
    processing = "processing"
    completed = "completed"
    error = "error"


class Call(Base):
    __tablename__ = "calls_api"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    filename = Column(String, nullable=False)
    storage_path = Column(String, nullable=False)
    duration_seconds = Column(Float)
    status = Column(Enum(CallStatus), default=CallStatus.pending, nullable=False)
    service_level = Column(String, default="standard")
    error_message = Column(Text)
    call_metadata = Column(JSONB)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

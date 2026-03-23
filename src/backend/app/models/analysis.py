from datetime import datetime
import uuid
from sqlalchemy import Column, DateTime, Enum, Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
import enum

from ..db import Base


class AnalysisStatus(str, enum.Enum):
    pending = "pending"
    completed = "completed"
    error = "error"


class Analysis(Base):
    __tablename__ = "analysis_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    call_id = Column(UUID(as_uuid=True), ForeignKey("calls_api.id", ondelete="CASCADE"), nullable=False)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    status = Column(Enum(AnalysisStatus), default=AnalysisStatus.pending)
    qa = Column(JSONB)
    sentiment = Column(JSONB)
    risk = Column(JSONB)
    kpis = Column(JSONB)
    transcript = Column(Text)
    artifacts = Column(JSONB)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

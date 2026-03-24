from datetime import datetime
import uuid
from sqlalchemy import Column, DateTime, Enum, ForeignKey, String, Text, Uuid, JSON
import enum

from ..db import Base


class AnalysisStatus(str, enum.Enum):
    pending = "pending"
    completed = "completed"
    error = "error"


class Analysis(Base):
    __tablename__ = "analysis_results"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    call_id = Column(Uuid, ForeignKey("calls_api.id", ondelete="CASCADE"), nullable=False)
    company_id = Column(Uuid, ForeignKey("companies.id"), nullable=False)
    status = Column(Enum(AnalysisStatus), default=AnalysisStatus.pending)
    qa = Column(JSON)
    sentiment = Column(JSON)
    risk = Column(JSON)
    kpis = Column(JSON)
    transcript = Column(Text)
    artifacts = Column(JSON)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

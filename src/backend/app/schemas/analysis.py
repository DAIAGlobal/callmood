from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import UUID
from pydantic import BaseModel

from ..models.analysis import AnalysisStatus


class AnalysisOut(BaseModel):
    id: UUID
    call_id: UUID
    status: AnalysisStatus
    qa: dict | None = None
    sentiment: dict | None = None
    risk: dict | None = None
    kpis: dict | None = None
    transcript: str | None = None
    artifacts: dict | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


# ============================================================================
# NEW CLEAN API SCHEMAS (Step 2 - Clean Architecture)
# ============================================================================

class AnalysisRequest(BaseModel):
    """Request to analyze a call audio file"""
    file_path: str
    level: str = "STANDARD"  # BASIC, STANDARD, ADVANCED


class AnalysisResult(BaseModel):
    """Analysis result from core engine"""
    status: str
    filename: str
    service_level: str
    duration: Optional[float] = None
    qa_score: Optional[float] = None
    qa_percentage: Optional[float] = None
    sentiment: Optional[Dict[str, Any]] = None
    transcription: Optional[Dict[str, Any]] = None
    kpis: Optional[Dict[str, Any]] = None
    findings: Optional[List[Dict[str, Any]]] = None
    errors: Optional[List[str]] = None
    processing_time_seconds: float
    data: Dict[str, Any]


class AnalysisUploadRequest(BaseModel):
    """Request to upload and analyze a file"""
    level: str = "STANDARD"


class AnalysisBatchRequest(BaseModel):
    """Request to analyze multiple files"""
    directory_path: str
    level: str = "STANDARD"


class AnalysisBatchResult(BaseModel):
    """Batch analysis result"""
    total_calls: int
    passed_calls: int
    failed_calls: int
    avg_qa_score: Optional[float] = None
    critical_findings_count: int
    processing_time_seconds: float
    results: List[AnalysisResult]


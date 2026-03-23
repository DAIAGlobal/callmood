import shutil
from pathlib import Path
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session
from fastapi import UploadFile

from ..config import get_settings
from ..models.call import Call, CallStatus
from ..models.analysis import Analysis, AnalysisStatus

settings = get_settings()


def store_upload(company_id: UUID, file: UploadFile) -> Path:
    storage_root = Path(settings.storage_dir) / "uploads" / str(company_id)
    storage_root.mkdir(parents=True, exist_ok=True)
    dest = storage_root / file.filename
    with dest.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return dest


def create_call(db: Session, user_id: UUID, company_id: UUID, file: UploadFile, service_level: str = "standard", metadata: dict | None = None) -> Call:
    path = store_upload(company_id, file)
    call = Call(
        company_id=company_id,
        user_id=user_id,
        filename=file.filename,
        storage_path=str(path),
        status=CallStatus.pending,
        service_level=service_level,
        call_metadata=metadata or {},
    )
    db.add(call)
    db.commit()
    db.refresh(call)
    return call


def create_analysis_placeholder(db: Session, call: Call) -> Analysis:
    analysis = Analysis(
        call_id=call.id,
        company_id=call.company_id,
        status=AnalysisStatus.pending,
    )
    db.add(analysis)
    db.commit()
    db.refresh(analysis)
    return analysis


def list_calls(db: Session, company_id: UUID):
    return db.query(Call).filter(Call.company_id == company_id).order_by(Call.created_at.desc()).all()


def get_call(db: Session, company_id: UUID, call_id: UUID) -> Optional[Call]:
    return db.query(Call).filter(Call.company_id == company_id, Call.id == call_id).first()


def get_analysis(db: Session, company_id: UUID, call_id: UUID) -> Optional[Analysis]:
    return db.query(Analysis).filter(Analysis.company_id == company_id, Analysis.call_id == call_id).first()

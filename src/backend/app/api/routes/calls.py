from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
import logging

from ...db import get_db
from ...schemas.call import CallOut, CallList
from ...schemas.analysis import AnalysisOut
from ...services import call_service
from ...auth.deps import get_current_user
from ...config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Try to import RQ, but handle Windows fork limitation
try:
    from redis import Redis
    from rq import Queue
    redis_conn = Redis.from_url(settings.redis_url)
    queue = Queue("callmood", connection=redis_conn, default_timeout=3600)
except (ValueError, Exception) as e:
    logger.warning(f"RQ initialization failed (may be Windows): {e}")
    redis_conn = None
    queue = None

router = APIRouter(prefix="/calls", tags=["calls"])


@router.post("/upload", response_model=CallOut, status_code=status.HTTP_202_ACCEPTED)
def upload_call(
    file: UploadFile = File(...),
    service_level: str = "standard",
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    call = call_service.create_call(
        db=db,
        user_id=current_user.id,
        company_id=current_user.company_id,
        file=file,
        service_level=service_level,
    )
    analysis = call_service.create_analysis_placeholder(db, call)
    
    # Enqueue worker job if RQ is available
    if queue:
        queue.enqueue("workers.worker.process_call", str(call.id), str(current_user.company_id), str(call.storage_path), service_level)
    else:
        logger.warning(f"RQ queue not available, skipping async processing for call {call.id}")
    
    return call


@router.get("", response_model=CallList)
def list_calls(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    calls = call_service.list_calls(db, current_user.company_id)
    return {"items": calls}


@router.get("/{call_id}", response_model=CallOut)
def get_call(call_id: UUID, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    call = call_service.get_call(db, current_user.company_id, call_id)
    if not call:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Call not found")
    return call


@router.get("/{call_id}/analysis", response_model=AnalysisOut)
def get_call_analysis(call_id: UUID, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    analysis = call_service.get_analysis(db, current_user.company_id, call_id)
    if not analysis:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis not found")
    return analysis

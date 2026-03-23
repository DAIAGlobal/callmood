from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ...db import get_db
from ...services.metrics_service import get_overview, get_operator_metrics
from ...auth.deps import get_current_user

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get("/overview")
def overview(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return get_overview(db, current_user.company_id)


@router.get("/operators")
def operators(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return get_operator_metrics(db, current_user.company_id)

from sqlalchemy.orm import Session
from sqlalchemy import func
from uuid import UUID

from ..models.analysis import Analysis
from ..models.call import Call


def get_overview(db: Session, company_id: UUID) -> dict:
    total_calls = db.query(func.count(Call.id)).filter(Call.company_id == company_id).scalar() or 0
    completed = db.query(func.count(Call.id)).filter(Call.company_id == company_id, Call.status == "completed").scalar() or 0
    failed = db.query(func.count(Call.id)).filter(Call.company_id == company_id, Call.status == "error").scalar() or 0
    avg_qa = db.query(func.avg(Analysis.qa["compliance_percentage"].as_float())).filter(Analysis.company_id == company_id).scalar()
    return {
        "total_calls": total_calls,
        "completed": completed,
        "failed": failed,
        "avg_qa": float(avg_qa) if avg_qa is not None else None,
    }


def get_operator_metrics(db: Session, company_id: UUID):
    rows = (
        db.query(Call.user_id, func.count(Call.id).label("calls"))
        .filter(Call.company_id == company_id)
        .group_by(Call.user_id)
        .all()
    )
    return [{"user_id": str(r.user_id), "calls": r.calls} for r in rows]

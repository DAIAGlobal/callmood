import os
import sys
from pathlib import Path
from typing import Any, Dict
from uuid import UUID

from sqlalchemy.orm import Session

# Ensure engine and backend packages are importable
ROOT_DIR = Path(__file__).resolve().parents[1]
ENGINE_SRC = ROOT_DIR / "src" / "engine"
BACKEND_SRC = ROOT_DIR / "src" / "backend"
for p in (ENGINE_SRC, BACKEND_SRC):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from backend.app.config import get_settings  # type: ignore  # noqa: E402
from backend.app.db import SessionLocal  # type: ignore  # noqa: E402
from backend.app.models.call import Call, CallStatus  # type: ignore  # noqa: E402
from backend.app.models.analysis import Analysis, AnalysisStatus  # type: ignore  # noqa: E402
from daia.application.services.batch_audit_service import BatchAuditService  # type: ignore  # noqa: E402
from daia.infrastructure.pipeline import PipelineOrchestrator  # type: ignore  # noqa: E402
from daia.infrastructure.reporting.report_saver import save_json_report, save_text_report  # type: ignore  # noqa: E402

settings = get_settings()


def _persist_artifacts(raw_result: Dict[str, Any]) -> Dict[str, str]:
    """Genera reportes JSON/TXT opcionales y devuelve paths."""
    reports_dir = Path(settings.artifacts_dir) / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    paths = {}
    json_path = save_json_report(raw_result, output_dir=str(reports_dir))
    txt_path = save_text_report(raw_result, output_dir=str(reports_dir))
    if json_path:
        paths["json"] = json_path
    if txt_path:
        paths["txt"] = txt_path
    return paths


def process_call(call_id: str, company_id: str, audio_path: str, service_level: str = "standard") -> None:
    """Job RQ: procesa un audio y persiste resultados."""
    db: Session = SessionLocal()
    try:
        call = db.query(Call).filter(Call.id == UUID(call_id)).first()
        if not call:
            return
        call.status = CallStatus.processing
        db.commit()

        config_path = os.getenv("CONFIG_PATH", str(ROOT_DIR / "config.yaml"))

        with PipelineOrchestrator(config_path=config_path) as orchestrator:
            service = BatchAuditService(orchestrator)
            audit_result, raw_result = service.process_file(audio_path, service_level=service_level, include_raw=True)

        artifacts = _persist_artifacts(raw_result)

        analysis = db.query(Analysis).filter(Analysis.call_id == call.id).first()
        if analysis:
            analysis.status = AnalysisStatus.completed
            analysis.qa = raw_result["data"].get("qa")
            analysis.sentiment = raw_result["data"].get("sentiment")
            analysis.risk = raw_result["data"].get("risk")
            analysis.kpis = raw_result["data"].get("kpis")
            analysis.transcript = raw_result["data"].get("transcription", {}).get("text")
            analysis.artifacts = artifacts
        call.status = CallStatus.completed
        call.duration_seconds = raw_result.get("duration")
        db.commit()

    except Exception as exc:  # noqa: BLE001
        db.rollback()
        call = db.query(Call).filter(Call.id == UUID(call_id)).first()
        if call:
            call.status = CallStatus.error
            call.error_message = str(exc)
            db.commit()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    # Helper to run a single job locally
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("call_id")
    parser.add_argument("company_id")
    parser.add_argument("audio_path")
    parser.add_argument("--service-level", default="standard")
    args = parser.parse_args()
    process_call(args.call_id, args.company_id, args.audio_path, args.service_level)

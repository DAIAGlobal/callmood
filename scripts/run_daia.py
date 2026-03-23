#!/usr/bin/env python
"""
CallMood unified entrypoint (paquete `daia`).

Usage:
    python run_daia.py <audio_file_or_directory> [--service-level standard]
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path
from typing import List

# Ensure engine package is importable
ROOT_DIR = Path(__file__).resolve().parents[1]
ENGINE_SRC = ROOT_DIR / "src" / "engine"
if str(ENGINE_SRC) not in sys.path:
    sys.path.insert(0, str(ENGINE_SRC))

from daia.application.services.batch_audit_service import BatchAuditService
from daia.infrastructure.pipeline import PipelineOrchestrator
from daia.infrastructure.reporting.report_generator import ReportGenerator, ReportConfig
from daia.infrastructure.reporting.report_saver import save_json_report, save_text_report


def _configure_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    )


def _ensure_runtime_dirs(reports_dir: Path, db_path: Path) -> None:
    """Create standard runtime folders if they do not exist."""
    folders = [
        Path("audio_in"),
        Path("artifacts/analysis"),
        Path("artifacts/transcripts/raw"),
        Path("artifacts/transcripts/clean"),
        reports_dir,
        db_path.parent,
        Path("data"),  # rulesets.json vive aquí
    ]
    for folder in folders:
        folder.mkdir(parents=True, exist_ok=True)


def _parse_args(argv: List[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="CallMood - Call Audit runner")
    parser.add_argument(
        "path",
        help="Ruta de archivo de audio o carpeta a procesar",
    )
    parser.add_argument(
        "--service-level",
        default="standard",
        choices=["basic", "standard", "advanced"],
        help="Nivel de auditoría",
    )
    parser.add_argument(
        "--config",
        default="config.yaml",
        help="Ruta al archivo de configuración YAML",
    )
    parser.add_argument(
        "--db-path",
        default="var/db/daia_audit.db",
        help="Ruta del archivo SQLite",
    )
    parser.add_argument(
        "--reports-dir",
        default="artifacts/reports",
        help="Carpeta destino para reportes JSON/TXT/PDF",
    )
    parser.add_argument(
        "--no-json",
        action="store_true",
        help="No generar reporte JSON",
    )
    parser.add_argument(
        "--no-txt",
        action="store_true",
        help="No generar reporte TXT",
    )
    parser.add_argument(
        "--batch-pdf",
        action="store_true",
        help="Generar reporte PDF consolidado cuando se procesa una carpeta",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Log detallado",
    )
    return parser.parse_args(argv)


def _summarize_single(audit_result) -> None:
    logger = logging.getLogger("run_daia.summary")
    qa = audit_result.qa_score or 0
    logger.info("Archivo: %s", audit_result.audited_call.filename)
    logger.info("QA score: %.1f%%", qa)
    logger.info("Hallazgos: %s (críticos=%s)", audit_result.total_findings, len(audit_result.critical_findings))
    logger.info("Estado: %s | Revisión: %s", audit_result.overall_status, audit_result.requires_review)


def _persist_reports(raw_result: dict, reports_dir: str, generate_json: bool, generate_txt: bool) -> None:
    if raw_result.get("status") != "completed":
        logging.warning("Resultado no completado; se omite generación de reportes.")
        return

    if generate_json:
        save_json_report(raw_result, output_dir=reports_dir)
    if generate_txt:
        save_text_report(raw_result, output_dir=reports_dir)


def run(argv: List[str] | None = None) -> int:
    args = _parse_args(argv)
    _configure_logging(args.verbose)

    # Windows fixes for torch/whisper DLLs
    if sys.platform == "win32":
        os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
        os.environ["TORCH_ALLOW_TF32_CUBLAS_OVERRIDE"] = "1"

    project_root = Path(__file__).resolve().parents[1]
    os.chdir(project_root)

    target_path = Path(args.path).expanduser().resolve()
    if not target_path.exists():
        logging.error("Ruta no encontrada: %s", target_path)
        return 1

    config_path = Path(args.config)
    if not config_path.is_absolute():
        config_path = project_root / config_path
    db_path = Path(args.db_path)
    if not db_path.is_absolute():
        db_path = project_root / db_path
    reports_dir = Path(args.reports_dir)
    if not reports_dir.is_absolute():
        reports_dir = project_root / reports_dir
    _ensure_runtime_dirs(reports_dir=reports_dir, db_path=db_path)

    with PipelineOrchestrator(config_path=str(config_path), db_path=str(db_path)) as orchestrator:
        service = BatchAuditService(orchestrator)

        if target_path.is_file():
            audit_result, raw_result = service.process_file(
                str(target_path),
                service_level=args.service_level,
                include_raw=True,
            )
            _summarize_single(audit_result)
            _persist_reports(raw_result, str(reports_dir), not args.no_json, not args.no_txt)
            return 0

        if target_path.is_dir():
            batch_result, raw_results = service.process_folder(
                str(target_path),
                service_level=args.service_level,
                include_raw=True,
            )

            logging.info(
                "Batch: %s llamadas | Aprobadas=%s | QA promedio=%.1f%% | Críticas=%s | Tiempo=%.1fs",
                batch_result.total_calls,
                batch_result.passed_calls,
                batch_result.avg_qa_score,
                batch_result.critical_findings_count,
                batch_result.processing_time_seconds,
            )

            for raw_result in raw_results:
                _persist_reports(raw_result, str(reports_dir), not args.no_json, not args.no_txt)

            if args.batch_pdf:
                try:
                    generator = ReportGenerator(ReportConfig(output_dir=str(reports_dir)))
                    generator.generate_batch_report(batch_result, format="pdf")
                except Exception as exc:  # noqa: BLE001
                    logging.warning("No se pudo generar PDF consolidado: %s", exc)

            return 0

    logging.error("Ruta no es archivo ni carpeta: %s", target_path)
    return 1


def main() -> None:
    sys.exit(run())


if __name__ == "__main__":
    main()

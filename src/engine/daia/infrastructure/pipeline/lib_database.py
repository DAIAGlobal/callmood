"""
DAIA - Database Module (PostgreSQL via SQLAlchemy)
Infraestructura de persistencia para el motor de análisis.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    create_engine,
    select,
    update,
    func,
)
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

logger = logging.getLogger(__name__)


class DAIADatabase:
    """
    Gestor de base de datos para DAIA usando PostgreSQL.
    Mantiene la interfaz usada por el pipeline original, pero la implementación
    usa SQLAlchemy para soportar SaaS multi-tenant.
    """

    def __init__(self, db_path: str = "postgresql://callmood:callmood@db:5432/callmood", default_company_id: str | None = None):
        """
        Args:
            db_path: URL de conexión (se ignora si existe DATABASE_URL en entorno)
            default_company_id: Empresa por defecto cuando el pipeline no provee contexto
        """
        candidate = os.getenv("DATABASE_URL", db_path)
        if "://" not in candidate:
            candidate = f"sqlite:///{candidate}"
        self.database_url = candidate
        self.default_company_id = default_company_id or os.getenv("DEFAULT_COMPANY_ID", "default")

        self.metadata = MetaData()

        self.calls = Table(
            "calls",
            self.metadata,
            Column("id", Integer, primary_key=True, autoincrement=True),
            Column("company_id", String, nullable=False, default=self.default_company_id),
            Column("filename", String, unique=True, nullable=False),
            Column("original_filename", String),
            Column("processing_date", DateTime(timezone=True), server_default=func.now()),
            Column("duration_seconds", Float),
            Column("status", String, default="pending"),
            Column("error_message", Text),
            Column("service_level", String),
            Column("created_at", DateTime(timezone=True), server_default=func.now()),
        )

        self.transcripts = Table(
            "transcripts",
            self.metadata,
            Column("id", Integer, primary_key=True),
            Column("call_id", Integer, ForeignKey("calls.id", ondelete="CASCADE")),
            Column("raw_text", Text),
            Column("cleaned_text", Text),
            Column("language", String),
            Column("model_used", String),
            Column("device_used", String),
            Column("processing_time_seconds", Float),
            Column("created_at", DateTime(timezone=True), server_default=func.now()),
        )

        self.qa_scores = Table(
            "qa_scores",
            self.metadata,
            Column("id", Integer, primary_key=True),
            Column("call_id", Integer, ForeignKey("calls.id", ondelete="CASCADE")),
            Column("level", String),
            Column("score", Float),
            Column("max_score", Float),
            Column("compliance_percentage", Float),
            Column("classification", String),
            Column("details", JSON),
            Column("created_at", DateTime(timezone=True), server_default=func.now()),
        )

        self.risk_assessments = Table(
            "risk_assessments",
            self.metadata,
            Column("id", Integer, primary_key=True),
            Column("call_id", Integer, ForeignKey("calls.id", ondelete="CASCADE")),
            Column("risk_level", String),
            Column("risk_score", Float),
            Column("critical_keywords", Text),
            Column("warning_keywords", Text),
            Column("sentiment_factor", Float),
            Column("details", JSON),
            Column("created_at", DateTime(timezone=True), server_default=func.now()),
        )

        self.kpi_results = Table(
            "kpi_results",
            self.metadata,
            Column("id", Integer, primary_key=True),
            Column("call_id", Integer, ForeignKey("calls.id", ondelete="CASCADE")),
            Column("metric_name", String),
            Column("metric_value", Float),
            Column("metric_unit", String),
            Column("classification", String),
            Column("details", JSON),
            Column("created_at", DateTime(timezone=True), server_default=func.now()),
        )

        self.sentiment_analysis = Table(
            "sentiment_analysis",
            self.metadata,
            Column("id", Integer, primary_key=True),
            Column("call_id", Integer, ForeignKey("calls.id", ondelete="CASCADE")),
            Column("sentiment_overall", String),
            Column("sentiment_score", Float),
            Column("operator_sentiment", String),
            Column("client_sentiment", String),
            Column("segments", JSON),
            Column("created_at", DateTime(timezone=True), server_default=func.now()),
        )

        self.audit_logs = Table(
            "audit_logs",
            self.metadata,
            Column("id", Integer, primary_key=True),
            Column("call_id", Integer, ForeignKey("calls.id", ondelete="SET NULL")),
            Column("company_id", String, nullable=False, default=self.default_company_id),
            Column("level", String),
            Column("message", Text),
            Column("error_type", String),
            Column("timestamp", DateTime(timezone=True), server_default=func.now()),
        )

        self.engine = create_engine(self.database_url, future=True, pool_pre_ping=True)
        self._create_tables()
        logger.info("✓ Database inicializada en %s", self.database_url)

    # --- Infra helpers -----------------------------------------------------
    def _create_tables(self) -> None:
        """Crea tablas si no existen."""
        try:
            self.metadata.create_all(self.engine)
        except SQLAlchemyError as exc:
            logger.error("❌ Error creando tablas: %s", exc)
            raise

    # --- Public API compatible con pipeline -------------------------------
    def insert_call(self, filename: str, duration: float | None = None, service_level: str = "standard", audio_path: str | None = None, company_id: str | None = None) -> Optional[int]:
        company = company_id or self.default_company_id
        try:
            with self.engine.begin() as conn:
                result = conn.execute(
                    self.calls.insert().values(
                        filename=filename,
                        original_filename=audio_path or filename,
                        duration_seconds=duration,
                        service_level=service_level,
                        company_id=company,
                    )
                )
                call_id = result.inserted_primary_key[0]
                logger.debug("✓ Llamada %s registrada (%s)", call_id, filename)
                return call_id
        except IntegrityError:
            logger.warning("⚠️ Llamada '%s' ya existe, recuperando ID", filename)
            with self.engine.begin() as conn:
                res = conn.execute(select(self.calls.c.id).where(self.calls.c.filename == filename)).first()
                return res.id if res else None
        except SQLAlchemyError as exc:
            logger.error("❌ Error BD insertando llamada: %s", exc)
            return None

    def insert_transcript(self, call_id: int, transcript_data: Dict[str, Any]) -> None:
        try:
            with self.engine.begin() as conn:
                conn.execute(
                    self.transcripts.insert().values(
                        call_id=call_id,
                        raw_text=transcript_data.get("text"),
                        cleaned_text=transcript_data.get("cleaned"),
                        language=transcript_data.get("language"),
                        model_used=transcript_data.get("model"),
                        device_used=transcript_data.get("device"),
                        processing_time_seconds=transcript_data.get("processing_time"),
                    )
                )
        except SQLAlchemyError as exc:
            logger.error("❌ Error guardando transcripción: %s", exc)

    def insert_qa_score(self, call_id: int, qa_result: Dict[str, Any]) -> None:
        try:
            with self.engine.begin() as conn:
                conn.execute(
                    self.qa_scores.insert().values(
                        call_id=call_id,
                        level=qa_result.get("level"),
                        score=qa_result.get("score"),
                        max_score=qa_result.get("max_score"),
                        compliance_percentage=qa_result.get("compliance_percentage"),
                        classification=qa_result.get("classification"),
                        details=qa_result,
                    )
                )
        except SQLAlchemyError as exc:
            logger.error("❌ Error guardando QA: %s", exc)

    def insert_risk_assessment(self, call_id: int, risk_result: Dict[str, Any]) -> None:
        try:
            with self.engine.begin() as conn:
                conn.execute(
                    self.risk_assessments.insert().values(
                        call_id=call_id,
                        risk_level=risk_result.get("level"),
                        risk_score=risk_result.get("score"),
                        critical_keywords=", ".join(risk_result.get("critical_keywords", []) or []),
                        warning_keywords=", ".join(risk_result.get("warning_keywords", []) or []),
                        sentiment_factor=risk_result.get("sentiment_factor"),
                        details=risk_result,
                    )
                )
        except SQLAlchemyError as exc:
            logger.error("❌ Error guardando riesgo: %s", exc)

    def insert_kpi_metrics(self, call_id: int, kpi_result: Dict[str, Any]) -> None:
        try:
            metrics: List[Dict[str, Any]] = kpi_result.get("metrics", [])
            with self.engine.begin() as conn:
                for metric in metrics:
                    conn.execute(
                        self.kpi_results.insert().values(
                            call_id=call_id,
                            metric_name=metric.get("name"),
                            metric_value=metric.get("value"),
                            metric_unit=metric.get("unit"),
                            classification=metric.get("classification"),
                            details=metric,
                        )
                    )
        except SQLAlchemyError as exc:
            logger.error("❌ Error guardando KPIs: %s", exc)

    def insert_sentiment_analysis(self, call_id: int, sentiment_result: Dict[str, Any]) -> None:
        try:
            with self.engine.begin() as conn:
                conn.execute(
                    self.sentiment_analysis.insert().values(
                        call_id=call_id,
                        sentiment_overall=sentiment_result.get("overall"),
                        sentiment_score=sentiment_result.get("score"),
                        operator_sentiment=(sentiment_result.get("operator") if isinstance(sentiment_result.get("operator"), dict) else None),
                        client_sentiment=(sentiment_result.get("client") if isinstance(sentiment_result.get("client"), dict) else None),
                        segments=sentiment_result.get("segments"),
                    )
                )
        except SQLAlchemyError as exc:
            logger.error("❌ Error guardando sentimiento: %s", exc)

    def log_event(self, call_id: Optional[int], level: str, message: str, error_type: str | None = None, company_id: str | None = None) -> None:
        try:
            with self.engine.begin() as conn:
                conn.execute(
                    self.audit_logs.insert().values(
                        call_id=call_id,
                        company_id=company_id or self.default_company_id,
                        level=level,
                        message=message,
                        error_type=error_type,
                    )
                )
        except SQLAlchemyError as exc:
            logger.error("❌ Error registrando audit log: %s", exc)

    def update_call_status(self, call_id: int, status: str, error_message: str | None = None) -> None:
        try:
            with self.engine.begin() as conn:
                conn.execute(
                    update(self.calls)
                    .where(self.calls.c.id == call_id)
                    .values(status=status, error_message=error_message, processing_date=datetime.utcnow())
                )
        except SQLAlchemyError as exc:
            logger.error("❌ Error actualizando estado: %s", exc)

    def get_call_analysis(self, call_id: int) -> Dict[str, Any]:
        """Recupera agregados básicos; usado en tests/diagnóstico."""
        with self.engine.begin() as conn:
            call = conn.execute(select(self.calls).where(self.calls.c.id == call_id)).mappings().first()
            transcript = conn.execute(select(self.transcripts).where(self.transcripts.c.call_id == call_id)).mappings().first()
            qa = conn.execute(select(self.qa_scores).where(self.qa_scores.c.call_id == call_id)).mappings().first()
            risk = conn.execute(select(self.risk_assessments).where(self.risk_assessments.c.call_id == call_id)).mappings().first()
            sentiment = conn.execute(select(self.sentiment_analysis).where(self.sentiment_analysis.c.call_id == call_id)).mappings().first()
            kpis = conn.execute(select(self.kpi_results).where(self.kpi_results.c.call_id == call_id)).mappings().all()

        return {
            "call": dict(call) if call else None,
            "transcript": dict(transcript) if transcript else None,
            "qa": dict(qa) if qa else None,
            "risk": dict(risk) if risk else None,
            "sentiment": dict(sentiment) if sentiment else None,
            "kpis": [dict(k) for k in kpis] if kpis else [],
        }

    def close(self) -> None:
        """Compatibilidad con contexto."""
        self.engine.dispose()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

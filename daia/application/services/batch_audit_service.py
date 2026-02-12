"""
DAIA Application Layer - Batch Audit Service

Servicio para procesar múltiples audios y generar reportes consolidados.
Enfoque comercial: multiplicar tickets automáticamente.
"""

import sys
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass

# Agregar paths necesarios
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from daia.domain.models import (
    AuditedCall,
    AuditResult,
    Finding,
    Metric,
    CallStatus,
    ServiceLevel,
    FindingSeverity,
    FindingCategory,
    MetricType,
    MetricCategory,
    MetricStatus,
    create_completed_call,
    create_completed_result,
    create_qa_score_metric,
)

# Importar código existente
from pipeline import PipelineOrchestrator

logger = logging.getLogger(__name__)


@dataclass
class BatchAuditResult:
    """
    Resultado de una auditoría batch
    
    Attributes:
        results: Lista de AuditResults individuales
        total_calls: Total de llamadas procesadas
        passed_calls: Llamadas que aprobaron
        failed_calls: Llamadas que fallaron
        avg_qa_score: Promedio de QA score
        critical_findings_count: Total de findings críticos
        processing_time_seconds: Tiempo total de procesamiento
        generated_at: Timestamp de generación
    """
    results: List[AuditResult]
    total_calls: int
    passed_calls: int
    failed_calls: int
    avg_qa_score: float
    critical_findings_count: int
    processing_time_seconds: float
    generated_at: datetime
    
    @property
    def approval_rate(self) -> float:
        """Tasa de aprobación (%)"""
        if self.total_calls == 0:
            return 0.0
        return (self.passed_calls / self.total_calls) * 100
    
    @property
    def critical_rate(self) -> float:
        """Tasa de hallazgos críticos por llamada"""
        if self.total_calls == 0:
            return 0.0
        return self.critical_findings_count / self.total_calls
    
    @property
    def requires_attention(self) -> List[AuditResult]:
        """Llamadas que requieren atención"""
        return [r for r in self.results if r.requires_review or not r.is_passing]
    
    def summary_dict(self) -> Dict[str, Any]:
        """Resumen ejecutivo del batch"""
        return {
            'total_calls': self.total_calls,
            'passed_calls': self.passed_calls,
            'failed_calls': self.failed_calls,
            'approval_rate': f"{self.approval_rate:.1f}%",
            'avg_qa_score': f"{self.avg_qa_score:.1f}%",
            'critical_findings': self.critical_findings_count,
            'calls_requiring_attention': len(self.requires_attention),
            'processing_time': f"{self.processing_time_seconds:.1f}s",
            'generated_at': self.generated_at.isoformat()
        }


class BatchAuditService:
    """
    Servicio de auditoría batch - procesa carpetas completas
    
    Enfoque comercial:
    - 1 audio = 1 reporte individual
    - N audios = N reportes + 1 consolidado
    - Multiplica el ticket automáticamente
    """
    
    def __init__(self, orchestrator: Optional[PipelineOrchestrator] = None):
        """
        Inicializa el servicio batch
        
        Args:
            orchestrator: Pipeline existente (si no se provee, se crea uno nuevo)
        """
        self.orchestrator = orchestrator or PipelineOrchestrator()
        logger.info("✓ BatchAuditService inicializado")
    
    def process_folder(
        self,
        folder_path: str,
        service_level: str = "standard"
    ) -> BatchAuditResult:
        """
        Procesa todos los audios en una carpeta
        
        Args:
            folder_path: Ruta de la carpeta con audios
            service_level: Nivel de auditoría (basic/standard/advanced)
            
        Returns:
            BatchAuditResult con todos los resultados
        """
        start_time = datetime.now()
        
        folder = Path(folder_path)
        if not folder.exists():
            raise ValueError(f"Carpeta no existe: {folder_path}")
        
        # Buscar archivos de audio
        audio_extensions = ['.wav', '.mp3', '.m4a', '.ogg', '.flac']
        audio_files = []
        for ext in audio_extensions:
            audio_files.extend(folder.glob(f"*{ext}"))
        
        if not audio_files:
            raise ValueError(f"No se encontraron archivos de audio en: {folder_path}")
        
        logger.info(f"📊 Procesando {len(audio_files)} archivos en batch...")
        
        # Procesar cada archivo
        results = []
        for i, audio_file in enumerate(audio_files, 1):
            logger.info(f"[{i}/{len(audio_files)}] Procesando: {audio_file.name}")
            
            try:
                # Procesar con pipeline existente
                result = self._process_single_audio(audio_file, service_level)
                results.append(result)
                
                status_icon = "✅" if result.is_passing else "⚠️"
                logger.info(
                    f"  {status_icon} QA: {result.qa_score:.1f}% | "
                    f"Findings: {result.total_findings} | "
                    f"Status: {result.overall_status}"
                )
                
            except Exception as e:
                logger.error(f"  ❌ Error procesando {audio_file.name}: {e}")
                # Continuar con el siguiente archivo
        
        # Calcular estadísticas
        total = len(results)
        passed = sum(1 for r in results if r.is_passing)
        failed = total - passed
        
        avg_qa = sum(r.qa_score or 0 for r in results) / total if total > 0 else 0
        
        critical_count = sum(len(r.critical_findings) for r in results)
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        batch_result = BatchAuditResult(
            results=results,
            total_calls=total,
            passed_calls=passed,
            failed_calls=failed,
            avg_qa_score=avg_qa,
            critical_findings_count=critical_count,
            processing_time_seconds=processing_time,
            generated_at=datetime.now()
        )
        
        logger.info(f"\n✅ Batch completado: {total} audios procesados")
        logger.info(f"   Aprobados: {passed} | Rechazados: {failed}")
        logger.info(f"   QA Promedio: {avg_qa:.1f}%")
        logger.info(f"   Findings críticos: {critical_count}")
        
        return batch_result
    
    def _process_single_audio(
        self,
        audio_path: Path,
        service_level: str
    ) -> AuditResult:
        """
        Procesa un audio individual y convierte a AuditResult
        
        Args:
            audio_path: Ruta del archivo
            service_level: Nivel de auditoría
            
        Returns:
            AuditResult con el resultado completo
        """
        # Procesar con pipeline existente
        raw_result = self.orchestrator.process_audio_file(
            str(audio_path),
            service_level=service_level
        )
        
        if not raw_result or raw_result.get('status') != 'completed':
            raise RuntimeError(f"Error procesando: {raw_result.get('error', 'Unknown')}")
        
        # Convertir a domain models
        return self._convert_to_domain_model(raw_result, audio_path, service_level)
    
    def _convert_to_domain_model(
        self,
        raw_result: Dict[str, Any],
        audio_path: Path,
        service_level: str
    ) -> AuditResult:
        """
        Convierte resultado del pipeline a AuditResult domain model
        
        Args:
            raw_result: Dict del pipeline existente
            audio_path: Ruta del archivo
            service_level: Nivel aplicado
            
        Returns:
            AuditResult
        """
        # Crear AuditedCall
        service_level_enum = {
            'basic': ServiceLevel.BASIC,
            'standard': ServiceLevel.STANDARD,
            'advanced': ServiceLevel.ADVANCED
        }.get(service_level, ServiceLevel.STANDARD)
        
        # Obtener duración del audio (del file o fallback)
        duration = raw_result.get('duration', 0)
        if duration == 0:
            # Fallback: obtener del audio_file
            try:
                import subprocess
                result = subprocess.run(
                    ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', 
                     '-of', 'default=noprint_wrappers=1:nokey=1', str(audio_path)],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                duration = float(result.stdout.strip())
            except:
                # Si no se puede obtener, usar 60s como default
                duration = 60.0
        
        audited_call = create_completed_call(
            call_id=raw_result.get('call_id'),
            filename=audio_path.name,
            audio_path=str(audio_path),
            duration_seconds=duration,
            service_level=service_level_enum
        )
        
        # Extraer datos
        data = raw_result.get('data', {})
        
        # Crear métricas business-focused
        metrics = self._extract_business_metrics(data, raw_result)
        
        # Crear findings
        findings = self._extract_findings(data)
        
        # Obtener transcripción
        transcript_text = data.get('transcription', {}).get('text', '')
        
        # Crear AuditResult
        return create_completed_result(
            audited_call=audited_call,
            findings=findings,
            metrics=metrics,
            transcript_text=transcript_text,
            processing_time_seconds=raw_result.get('processing_time', 0)
        )
    
    def _extract_business_metrics(
        self,
        data: Dict[str, Any],
        raw_result: Dict[str, Any]
    ) -> List[Metric]:
        """
        Extrae métricas enfocadas en negocio (no técnicas)
        
        Métricas que importan al cliente:
        1. QA Score (cumplimiento)
        2. Duración real vs esperada
        3. % silencio
        4. % interrupciones
        5. Distribución emocional
        6. Severidad promedio
        """
        metrics = []
        
        # 1. QA Score (principal métrica)
        qa_data = data.get('qa', {})
        qa_score = qa_data.get('compliance_percentage', 0)
        metrics.append(create_qa_score_metric(score=qa_score))
        
        # 2. Duración
        duration = raw_result.get('duration', 0)
        metrics.append(
            Metric(
                name="call_duration",
                value=duration,
                metric_type=MetricType.SECONDS,
                category=MetricCategory.PERFORMANCE,
                unit="s",
                threshold_min=30.0,
                threshold_max=600.0,
                description="Duración de la llamada"
            )
        )
        
        # 3-6. Métricas de KPIs (si están disponibles)
        kpis_data = data.get('kpis', {})
        if kpis_data:
            kpi_metrics = kpis_data.get('metrics', {})
            
            # % Silencio
            if 'silence_percentage' in kpi_metrics:
                silence = kpi_metrics['silence_percentage']
                metrics.append(
                    Metric(
                        name="silence_rate",
                        value=silence.get('value', 0),
                        metric_type=MetricType.PERCENTAGE,
                        category=MetricCategory.QUALITY,
                        unit="%",
                        threshold_max=30.0,
                        description="Porcentaje de silencio en la llamada"
                    )
                )
            
            # Interrupciones
            if 'interruption_count' in kpi_metrics:
                interruptions = kpi_metrics['interruption_count']
                metrics.append(
                    Metric(
                        name="interruptions",
                        value=interruptions.get('value', 0),
                        metric_type=MetricType.COUNT,
                        category=MetricCategory.QUALITY,
                        threshold_max=5.0,
                        description="Cantidad de interrupciones"
                    )
                )
        
        # Sentimiento
        sentiment_data = data.get('sentiment', {})
        if sentiment_data:
            overall = sentiment_data.get('overall', {})
            if isinstance(overall, dict):
                sentiment_label = overall.get('label', 'neutral')
                confidence = overall.get('confidence', 0.5)
            else:
                sentiment_label = str(overall)
                confidence = sentiment_data.get('confidence', 0.5)
            
            # Determinar status
            status = MetricStatus.GOOD
            if 'negative' in sentiment_label.lower():
                status = MetricStatus.POOR
            elif 'positive' in sentiment_label.lower():
                status = MetricStatus.EXCELLENT
            
            metrics.append(
                Metric(
                    name="emotional_tone",
                    value=confidence,
                    metric_type=MetricType.RATIO,
                    category=MetricCategory.SENTIMENT,
                    status=status,
                    description=f"Tono emocional: {sentiment_label}"
                )
            )
        
        return metrics
    
    def _extract_findings(self, data: Dict[str, Any]) -> List[Finding]:
        """
        Extrae findings del resultado raw
        
        Args:
            data: Datos del pipeline
            
        Returns:
            Lista de Finding domain objects
        """
        findings = []
        
        # Findings de QA
        qa_data = data.get('qa', {})
        qa_details = qa_data.get('details', [])
        
        for detail in qa_details:
            if not detail.get('passed', True):
                # Determinar severidad
                check_type = detail.get('check_type', 'unknown')
                severity = FindingSeverity.MEDIUM
                
                if 'mandatory' in check_type.lower() or 'required' in check_type.lower():
                    severity = FindingSeverity.HIGH
                
                finding = Finding(
                    category=FindingCategory.COMPLIANCE,
                    severity=severity,
                    title=f"{check_type} - No cumplido",
                    description=detail.get('reason', 'Verificar protocolo de atención'),
                    evidence=detail.get('evidence', ''),
                    recommendation="Reforzar cumplimiento del protocolo estándar"
                )
                findings.append(finding)
        
        # Findings de riesgo
        risk_data = data.get('risk', {})
        if risk_data:
            risk_level = risk_data.get('level', 'LOW')
            critical_keywords = risk_data.get('critical_found', [])
            
            if risk_level in ['CRITICAL', 'HIGH'] or critical_keywords:
                severity = FindingSeverity.CRITICAL if risk_level == 'CRITICAL' else FindingSeverity.HIGH
                
                finding = Finding(
                    category=FindingCategory.RISK,
                    severity=severity,
                    title=f"Riesgo {risk_level} detectado",
                    description=f"Se detectaron elementos de riesgo en la llamada",
                    evidence=f"Keywords: {', '.join(critical_keywords)}" if critical_keywords else "",
                    recommendation="Revisión inmediata por supervisor. Evaluar protocolo de manejo de situaciones críticas."
                )
                findings.append(finding)
        
        return findings


# Función helper para uso directo
def process_audio_folder(
    folder_path: str,
    service_level: str = "standard"
) -> BatchAuditResult:
    """
    Helper function: Procesa una carpeta de audios
    
    Args:
        folder_path: Ruta de la carpeta
        service_level: Nivel de auditoría
        
    Returns:
        BatchAuditResult
        
    Example:
        >>> result = process_audio_folder("audio_in/", "standard")
        >>> print(f"Aprobados: {result.passed_calls}/{result.total_calls}")
        >>> print(f"QA Promedio: {result.avg_qa_score:.1f}%")
    """
    service = BatchAuditService()
    return service.process_folder(folder_path, service_level)

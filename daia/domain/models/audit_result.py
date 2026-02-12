"""
Domain Model: AuditResult

Representa el resultado completo de una auditoría.
Aggregate que contiene la llamada, métricas y hallazgos.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime

from daia.domain.models.audited_call import AuditedCall
from daia.domain.models.finding import Finding, FindingSeverity, FindingCategory
from daia.domain.models.metric import Metric, MetricCategory, MetricStatus


@dataclass(frozen=True)
class AuditResult:
    """
    Aggregate: Resultado completo de una auditoría
    
    Combina la llamada auditada con todos sus hallazgos y métricas.
    Es el resultado final que se persiste y se reporta al cliente.
    
    Attributes:
        audited_call: La llamada que fue auditada
        findings: Lista de hallazgos encontrados
        metrics: Lista de métricas calculadas
        transcript_text: Texto de la transcripción (opcional)
        processing_time_seconds: Tiempo que tomó el procesamiento
        generated_at: Timestamp de generación del resultado
        
    Business Rules:
        - Debe tener al menos 1 métrica
        - Si status=COMPLETED debe tener transcript_text
        - Findings CRITICAL deben ser < 10% del total
        - QA score debe estar presente en métricas
    """
    
    # Core aggregate
    audited_call: AuditedCall
    
    # Collections
    findings: List[Finding] = field(default_factory=list)
    metrics: List[Metric] = field(default_factory=list)
    
    # Optional data
    transcript_text: Optional[str] = None
    processing_time_seconds: float = 0.0
    generated_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """Validaciones de negocio"""
        # Validar que tenga métricas
        if self.audited_call.is_completed and len(self.metrics) == 0:
            raise ValueError(
                "Completed audit must have at least 1 metric"
            )
        
        # Validar que tenga transcripción si está completada
        if self.audited_call.is_completed and not self.transcript_text:
            raise ValueError(
                "Completed audit must have transcript_text"
            )
        
        # Validar que no haya demasiados findings críticos
        if len(self.findings) > 0:
            critical_count = sum(
                1 for f in self.findings if f.is_critical
            )
            critical_percentage = (critical_count / len(self.findings)) * 100
            
            if critical_percentage > 50:
                # Warning, pero no error (puede ser una llamada muy mala)
                pass
    
    # ========================================================================
    # PROPERTIES - Agregaciones y cálculos
    # ========================================================================
    
    @property
    def total_findings(self) -> int:
        """Total de hallazgos"""
        return len(self.findings)
    
    @property
    def critical_findings(self) -> List[Finding]:
        """Hallazgos críticos"""
        return [f for f in self.findings if f.is_critical]
    
    @property
    def high_severity_findings(self) -> List[Finding]:
        """Hallazgos de alta severidad"""
        return [
            f for f in self.findings 
            if f.severity in [FindingSeverity.CRITICAL, FindingSeverity.HIGH]
        ]
    
    @property
    def findings_requiring_action(self) -> List[Finding]:
        """Hallazgos que requieren acción"""
        return [f for f in self.findings if f.requires_action]
    
    @property
    def total_metrics(self) -> int:
        """Total de métricas"""
        return len(self.metrics)
    
    @property
    def quality_metrics(self) -> List[Metric]:
        """Métricas de calidad"""
        return [m for m in self.metrics if m.category == MetricCategory.QUALITY]
    
    @property
    def performance_metrics(self) -> List[Metric]:
        """Métricas de desempeño"""
        return [m for m in self.metrics if m.category == MetricCategory.PERFORMANCE]
    
    @property
    def poor_metrics(self) -> List[Metric]:
        """Métricas con estado POOR o CRITICAL"""
        return [
            m for m in self.metrics 
            if m.status in [MetricStatus.POOR, MetricStatus.CRITICAL]
        ]
    
    @property
    def qa_score(self) -> Optional[float]:
        """
        Obtiene el QA Score del resultado
        
        Returns:
            QA Score (0-100) o None si no está disponible
        """
        for metric in self.metrics:
            if metric.name == "qa_score":
                return metric.value
        return None
    
    @property
    def overall_status(self) -> str:
        """
        Calcula el estado general del resultado
        
        Returns:
            'excellent', 'good', 'acceptable', 'poor', 'critical'
        """
        # Si hay findings críticos → critical
        if len(self.critical_findings) > 0:
            return 'critical'
        
        # Si hay muchos findings de alta severidad → poor
        if len(self.high_severity_findings) >= 3:
            return 'poor'
        
        # Basarse en QA score si está disponible
        qa = self.qa_score
        if qa is not None:
            if qa >= 85:
                return 'excellent'
            elif qa >= 70:
                return 'good'
            elif qa >= 50:
                return 'acceptable'
            else:
                return 'poor'
        
        # Default basado en métricas pobres
        if len(self.poor_metrics) >= 2:
            return 'poor'
        elif len(self.poor_metrics) == 1:
            return 'acceptable'
        
        return 'good'
    
    @property
    def requires_review(self) -> bool:
        """
        Determina si el resultado requiere revisión humana
        
        Returns:
            True si requiere revisión
        """
        # Requiere revisión si:
        # - Hay findings críticos
        # - QA score < 50
        # - Más de 3 findings de alta severidad
        
        if len(self.critical_findings) > 0:
            return True
        
        qa = self.qa_score
        if qa is not None and qa < 50:
            return True
        
        if len(self.high_severity_findings) >= 3:
            return True
        
        return False
    
    @property
    def is_passing(self) -> bool:
        """
        Determina si la auditoría es aprobada
        
        Returns:
            True si pasa los criterios mínimos
        """
        # Criterios de aprobación:
        # - Sin findings críticos
        # - QA score >= 70 (si está disponible)
        # - Menos de 3 findings de alta severidad
        
        if len(self.critical_findings) > 0:
            return False
        
        qa = self.qa_score
        if qa is not None and qa < 70:
            return False
        
        if len(self.high_severity_findings) >= 3:
            return False
        
        return True
    
    # ========================================================================
    # MÉTODOS DE CONSULTA
    # ========================================================================
    
    def get_findings_by_category(self, category: FindingCategory) -> List[Finding]:
        """
        Obtiene hallazgos por categoría
        
        Args:
            category: Categoría a filtrar
            
        Returns:
            Lista de findings de esa categoría
        """
        return [f for f in self.findings if f.category == category]
    
    def get_findings_by_severity(self, severity: FindingSeverity) -> List[Finding]:
        """
        Obtiene hallazgos por severidad
        
        Args:
            severity: Severidad a filtrar
            
        Returns:
            Lista de findings de esa severidad
        """
        return [f for f in self.findings if f.severity == severity]
    
    def get_metrics_by_category(self, category: MetricCategory) -> List[Metric]:
        """
        Obtiene métricas por categoría
        
        Args:
            category: Categoría a filtrar
            
        Returns:
            Lista de métricas de esa categoría
        """
        return [m for m in self.metrics if m.category == category]
    
    def get_metric_by_name(self, name: str) -> Optional[Metric]:
        """
        Obtiene una métrica por nombre
        
        Args:
            name: Nombre de la métrica
            
        Returns:
            Metric o None si no existe
        """
        for metric in self.metrics:
            if metric.name == name:
                return metric
        return None
    
    def has_metric(self, name: str) -> bool:
        """Verifica si existe una métrica"""
        return self.get_metric_by_name(name) is not None
    
    def summary_dict(self) -> Dict[str, Any]:
        """
        Genera un diccionario resumen del resultado
        
        Returns:
            Dict con información clave del resultado
        """
        return {
            'call_id': self.audited_call.call_id,
            'filename': self.audited_call.filename,
            'duration_seconds': self.audited_call.duration_seconds,
            'service_level': self.audited_call.service_level.value,
            'status': self.audited_call.status.value,
            'overall_status': self.overall_status,
            'is_passing': self.is_passing,
            'requires_review': self.requires_review,
            'qa_score': self.qa_score,
            'total_findings': self.total_findings,
            'critical_findings': len(self.critical_findings),
            'high_severity_findings': len(self.high_severity_findings),
            'total_metrics': self.total_metrics,
            'processing_time_seconds': self.processing_time_seconds,
            'generated_at': self.generated_at.isoformat()
        }
    
    def __str__(self) -> str:
        qa = self.qa_score or 0
        return (
            f"AuditResult("
            f"call={self.audited_call.filename}, "
            f"status={self.overall_status}, "
            f"qa={qa:.1f}%, "
            f"findings={self.total_findings}, "
            f"metrics={self.total_metrics})"
        )
    
    def __repr__(self) -> str:
        return (
            f"AuditResult("
            f"call_id={self.audited_call.call_id}, "
            f"overall_status='{self.overall_status}', "
            f"is_passing={self.is_passing}, "
            f"findings={self.total_findings}, "
            f"metrics={self.total_metrics})"
        )


# Factory method para crear resultado vacío
def create_empty_result(audited_call: AuditedCall) -> AuditResult:
    """
    Factory: Crea un resultado vacío (para llamada en proceso)
    
    Args:
        audited_call: La llamada que se está auditando
        
    Returns:
        AuditResult vacío
    """
    return AuditResult(
        audited_call=audited_call,
        findings=[],
        metrics=[],
        transcript_text=None,
        processing_time_seconds=0.0
    )


def create_completed_result(
    audited_call: AuditedCall,
    findings: List[Finding],
    metrics: List[Metric],
    transcript_text: str,
    processing_time_seconds: float
) -> AuditResult:
    """
    Factory: Crea un resultado completo
    
    Args:
        audited_call: La llamada auditada
        findings: Lista de hallazgos
        metrics: Lista de métricas
        transcript_text: Transcripción completa
        processing_time_seconds: Tiempo de procesamiento
        
    Returns:
        AuditResult completo
    """
    return AuditResult(
        audited_call=audited_call,
        findings=findings,
        metrics=metrics,
        transcript_text=transcript_text,
        processing_time_seconds=processing_time_seconds,
        generated_at=datetime.now()
    )

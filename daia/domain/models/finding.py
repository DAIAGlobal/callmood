"""
Domain Model: Finding

Representa un hallazgo o descubrimiento durante la auditoría.
Value Object (sin identidad propia, se identifica por sus atributos).
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class FindingSeverity(Enum):
    """Severidad de un hallazgo"""
    CRITICAL = "critical"    # Requiere acción inmediata
    HIGH = "high"            # Problema grave, atención prioritaria
    MEDIUM = "medium"        # Requiere corrección
    LOW = "low"              # Observación menor
    INFO = "info"            # Informativo


class FindingCategory(Enum):
    """Categorías de hallazgos"""
    COMPLIANCE = "compliance"              # Cumplimiento normativo
    QUALITY = "quality"                    # Calidad del servicio
    SENTIMENT = "sentiment"                # Análisis emocional
    RISK = "risk"                          # Riesgos identificados
    PERFORMANCE = "performance"            # Métricas de desempeño
    PATTERN = "pattern"                    # Patrones detectados
    ANOMALY = "anomaly"                    # Anomalías encontradas
    BEST_PRACTICE = "best_practice"        # Buenas prácticas
    IMPROVEMENT = "improvement"            # Oportunidades de mejora


@dataclass(frozen=True)
class Finding:
    """
    Value Object: Hallazgo en la auditoría
    
    Representa un descubrimiento específico durante el análisis.
    Inmutable - dos findings con mismo contenido son equivalentes.
    
    Attributes:
        category: Categoría del hallazgo
        severity: Nivel de severidad
        title: Título breve del hallazgo
        description: Descripción detallada
        evidence: Evidencia que respalda el hallazgo (ej: texto de transcripción)
        recommendation: Recomendación de acción
        location: Ubicación en la llamada (timestamp, segmento, etc.)
        confidence: Nivel de confianza (0.0 - 1.0)
        
    Business Rules:
        - Title debe ser conciso (<100 chars)
        - Confidence debe estar entre 0 y 1
        - CRITICAL findings deben tener recommendation
    """
    
    category: FindingCategory
    severity: FindingSeverity
    title: str
    description: str
    
    # Optional attributes
    evidence: Optional[str] = None
    recommendation: Optional[str] = None
    location: Optional[str] = None
    confidence: float = 1.0
    
    def __post_init__(self):
        """Validaciones de negocio"""
        # Validar título
        if len(self.title) > 100:
            raise ValueError(
                f"Finding title must be ≤100 chars, got {len(self.title)}"
            )
        
        # Validar confidence
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(
                f"Confidence must be between 0 and 1, got {self.confidence}"
            )
        
        # CRITICAL findings deben tener recomendación
        if self.severity == FindingSeverity.CRITICAL and not self.recommendation:
            raise ValueError(
                "CRITICAL findings must have a recommendation"
            )
    
    @property
    def is_critical(self) -> bool:
        """Verifica si el hallazgo es crítico"""
        return self.severity == FindingSeverity.CRITICAL
    
    @property
    def requires_action(self) -> bool:
        """Verifica si requiere acción"""
        return self.severity in [
            FindingSeverity.CRITICAL,
            FindingSeverity.HIGH,
            FindingSeverity.MEDIUM
        ]
    
    @property
    def is_high_confidence(self) -> bool:
        """Verifica si tiene alta confianza (>80%)"""
        return self.confidence >= 0.8
    
    def __str__(self) -> str:
        return f"[{self.severity.value.upper()}] {self.title}"
    
    def __repr__(self) -> str:
        return (
            f"Finding("
            f"category={self.category.value}, "
            f"severity={self.severity.value}, "
            f"title='{self.title[:30]}...', "
            f"confidence={self.confidence:.2f})"
        )


# Factory methods para crear findings comunes
def create_compliance_finding(
    title: str,
    description: str,
    severity: FindingSeverity,
    evidence: Optional[str] = None,
    recommendation: Optional[str] = None
) -> Finding:
    """
    Factory: Crea un hallazgo de cumplimiento
    
    Args:
        title: Título del hallazgo
        description: Descripción detallada
        severity: Nivel de severidad
        evidence: Evidencia que respalda
        recommendation: Acción recomendada
        
    Returns:
        Finding de categoría COMPLIANCE
    """
    return Finding(
        category=FindingCategory.COMPLIANCE,
        severity=severity,
        title=title,
        description=description,
        evidence=evidence,
        recommendation=recommendation
    )


def create_quality_finding(
    title: str,
    description: str,
    severity: FindingSeverity,
    evidence: Optional[str] = None
) -> Finding:
    """
    Factory: Crea un hallazgo de calidad
    
    Args:
        title: Título del hallazgo
        description: Descripción detallada
        severity: Nivel de severidad
        evidence: Evidencia que respalda
        
    Returns:
        Finding de categoría QUALITY
    """
    return Finding(
        category=FindingCategory.QUALITY,
        severity=severity,
        title=title,
        description=description,
        evidence=evidence
    )


def create_risk_finding(
    title: str,
    description: str,
    severity: FindingSeverity,
    evidence: str,
    recommendation: str,
    confidence: float = 1.0
) -> Finding:
    """
    Factory: Crea un hallazgo de riesgo
    
    Args:
        title: Título del hallazgo
        description: Descripción del riesgo
        severity: Nivel de severidad
        evidence: Evidencia del riesgo (keywords, frases)
        recommendation: Acción correctiva
        confidence: Nivel de confianza
        
    Returns:
        Finding de categoría RISK
    """
    return Finding(
        category=FindingCategory.RISK,
        severity=severity,
        title=title,
        description=description,
        evidence=evidence,
        recommendation=recommendation,
        confidence=confidence
    )


def create_sentiment_finding(
    title: str,
    description: str,
    sentiment_label: str,
    confidence: float,
    location: Optional[str] = None
) -> Finding:
    """
    Factory: Crea un hallazgo de sentimiento
    
    Args:
        title: Título del hallazgo
        description: Descripción del sentimiento
        sentiment_label: Etiqueta de sentimiento (positive, negative, etc.)
        confidence: Confianza del modelo
        location: Ubicación en la llamada
        
    Returns:
        Finding de categoría SENTIMENT
    """
    # Determinar severidad basada en sentimiento
    severity = FindingSeverity.INFO
    if "negative" in sentiment_label.lower():
        severity = FindingSeverity.MEDIUM
    elif "very_negative" in sentiment_label.lower():
        severity = FindingSeverity.HIGH
    
    return Finding(
        category=FindingCategory.SENTIMENT,
        severity=severity,
        title=title,
        description=description,
        location=location,
        confidence=confidence
    )


def create_improvement_finding(
    title: str,
    description: str,
    recommendation: str
) -> Finding:
    """
    Factory: Crea una oportunidad de mejora
    
    Args:
        title: Título de la oportunidad
        description: Descripción de la mejora
        recommendation: Cómo implementarla
        
    Returns:
        Finding de categoría IMPROVEMENT
    """
    return Finding(
        category=FindingCategory.IMPROVEMENT,
        severity=FindingSeverity.LOW,
        title=title,
        description=description,
        recommendation=recommendation
    )

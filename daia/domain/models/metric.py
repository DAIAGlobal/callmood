"""
Domain Model: Metric

Representa una métrica medida durante la auditoría.
Value Object (sin identidad propia).
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Any


class MetricType(Enum):
    """Tipos de métricas"""
    PERCENTAGE = "percentage"        # 0-100%
    SECONDS = "seconds"              # Tiempo en segundos
    COUNT = "count"                  # Conteo
    RATIO = "ratio"                  # Proporción 0-1
    SCORE = "score"                  # Puntuación (escala variable)
    BOOLEAN = "boolean"              # True/False


class MetricCategory(Enum):
    """Categorías de métricas"""
    QUALITY = "quality"              # Métricas de calidad
    PERFORMANCE = "performance"      # Métricas de desempeño
    EFFICIENCY = "efficiency"        # Métricas de eficiencia
    COMPLIANCE = "compliance"        # Métricas de cumplimiento
    SENTIMENT = "sentiment"          # Métricas emocionales
    RISK = "risk"                    # Métricas de riesgo


class MetricStatus(Enum):
    """Estado de una métrica vs. threshold"""
    EXCELLENT = "excellent"          # Por encima del objetivo
    GOOD = "good"                    # Cumple objetivo
    ACCEPTABLE = "acceptable"        # Cerca del mínimo
    POOR = "poor"                    # Por debajo del mínimo
    CRITICAL = "critical"            # Muy por debajo


@dataclass(frozen=True)
class Metric:
    """
    Value Object: Métrica medida
    
    Representa una métrica específica calculada durante la auditoría.
    Inmutable - dos métricas con mismo contenido son equivalentes.
    
    Attributes:
        name: Nombre de la métrica (ej: "qa_score", "avg_response_time")
        value: Valor medido
        metric_type: Tipo de métrica
        category: Categoría de la métrica
        unit: Unidad de medida (ej: "segundos", "%", "count")
        status: Estado vs. threshold
        threshold_min: Valor mínimo aceptable
        threshold_max: Valor máximo aceptable
        threshold_target: Valor objetivo/ideal
        description: Descripción de qué mide
        
    Business Rules:
        - Percentage debe estar entre 0-100
        - Ratio debe estar entre 0-1
        - Status se calcula automáticamente basado en thresholds
    """
    
    name: str
    value: float
    metric_type: MetricType
    category: MetricCategory
    
    # Optional attributes
    unit: str = ""
    status: Optional[MetricStatus] = None
    threshold_min: Optional[float] = None
    threshold_max: Optional[float] = None
    threshold_target: Optional[float] = None
    description: str = ""
    
    def __post_init__(self):
        """Validaciones de negocio"""
        # Validar percentage
        if self.metric_type == MetricType.PERCENTAGE:
            if not 0 <= self.value <= 100:
                raise ValueError(
                    f"Percentage must be between 0-100, got {self.value}"
                )
        
        # Validar ratio
        if self.metric_type == MetricType.RATIO:
            if not 0 <= self.value <= 1:
                raise ValueError(
                    f"Ratio must be between 0-1, got {self.value}"
                )
        
        # Validar que min < max
        if self.threshold_min is not None and self.threshold_max is not None:
            if self.threshold_min > self.threshold_max:
                raise ValueError(
                    f"threshold_min ({self.threshold_min}) must be ≤ threshold_max ({self.threshold_max})"
                )
    
    @property
    def formatted_value(self) -> str:
        """Retorna el valor formateado con su unidad"""
        if self.metric_type == MetricType.PERCENTAGE:
            return f"{self.value:.1f}%"
        elif self.metric_type == MetricType.SECONDS:
            return f"{self.value:.1f}s"
        elif self.metric_type == MetricType.COUNT:
            return f"{int(self.value)}"
        elif self.metric_type == MetricType.RATIO:
            return f"{self.value:.2f}"
        else:
            return f"{self.value:.2f}{self.unit}"
    
    @property
    def is_within_acceptable_range(self) -> bool:
        """Verifica si el valor está dentro del rango aceptable"""
        if self.threshold_min is None and self.threshold_max is None:
            return True
        
        within_min = self.threshold_min is None or self.value >= self.threshold_min
        within_max = self.threshold_max is None or self.value <= self.threshold_max
        
        return within_min and within_max
    
    @property
    def is_above_target(self) -> bool:
        """Verifica si el valor supera el objetivo"""
        if self.threshold_target is None:
            return False
        return self.value >= self.threshold_target
    
    @property
    def distance_from_target(self) -> Optional[float]:
        """Calcula la distancia del valor al objetivo"""
        if self.threshold_target is None:
            return None
        return self.value - self.threshold_target
    
    @property
    def distance_from_min(self) -> Optional[float]:
        """Calcula la distancia del valor al mínimo"""
        if self.threshold_min is None:
            return None
        return self.value - self.threshold_min
    
    def calculate_status(self) -> MetricStatus:
        """
        Calcula el estado de la métrica basado en thresholds
        
        Lógica:
        - EXCELLENT: >= target (si existe)
        - GOOD: >= min && cerca de target
        - ACCEPTABLE: >= min
        - POOR: < min pero no crítico
        - CRITICAL: muy por debajo de min
        """
        if self.threshold_target and self.value >= self.threshold_target:
            return MetricStatus.EXCELLENT
        
        if self.threshold_min:
            if self.value >= self.threshold_min:
                # Entre min y target
                if self.threshold_target:
                    distance = (self.threshold_target - self.threshold_min)
                    if distance > 0:
                        position = (self.value - self.threshold_min) / distance
                        if position >= 0.7:
                            return MetricStatus.GOOD
                return MetricStatus.ACCEPTABLE
            else:
                # Por debajo del mínimo
                distance = self.threshold_min - self.value
                if self.threshold_min > 0:
                    percentage_below = (distance / self.threshold_min) * 100
                    if percentage_below > 50:
                        return MetricStatus.CRITICAL
                return MetricStatus.POOR
        
        # Sin thresholds definidos
        return MetricStatus.ACCEPTABLE
    
    def __str__(self) -> str:
        status_str = f" ({self.status.value})" if self.status else ""
        return f"{self.name}: {self.formatted_value}{status_str}"
    
    def __repr__(self) -> str:
        return (
            f"Metric("
            f"name='{self.name}', "
            f"value={self.value}, "
            f"type={self.metric_type.value}, "
            f"status={self.status.value if self.status else 'N/A'})"
        )


# Factory methods para crear métricas comunes
def create_qa_score_metric(
    score: float,
    threshold_min: float = 70.0,
    threshold_target: float = 85.0
) -> Metric:
    """
    Factory: Crea métrica de QA Score
    
    Args:
        score: Puntuación QA (0-100)
        threshold_min: Mínimo aceptable (default: 70)
        threshold_target: Objetivo (default: 85)
        
    Returns:
        Metric de tipo PERCENTAGE categoría QUALITY
    """
    metric = Metric(
        name="qa_score",
        value=score,
        metric_type=MetricType.PERCENTAGE,
        category=MetricCategory.QUALITY,
        unit="%",
        threshold_min=threshold_min,
        threshold_target=threshold_target,
        description="Puntuación de calidad de la llamada"
    )
    
    # Calcular y asignar status
    status = metric.calculate_status()
    return Metric(
        name=metric.name,
        value=metric.value,
        metric_type=metric.metric_type,
        category=metric.category,
        unit=metric.unit,
        status=status,
        threshold_min=metric.threshold_min,
        threshold_target=metric.threshold_target,
        description=metric.description
    )


def create_duration_metric(
    duration_seconds: float,
    threshold_min: float = 30.0,
    threshold_max: float = 600.0
) -> Metric:
    """
    Factory: Crea métrica de duración
    
    Args:
        duration_seconds: Duración en segundos
        threshold_min: Duración mínima esperada
        threshold_max: Duración máxima esperada
        
    Returns:
        Metric de tipo SECONDS categoría PERFORMANCE
    """
    metric = Metric(
        name="call_duration",
        value=duration_seconds,
        metric_type=MetricType.SECONDS,
        category=MetricCategory.PERFORMANCE,
        unit="s",
        threshold_min=threshold_min,
        threshold_max=threshold_max,
        description="Duración de la llamada"
    )
    
    status = metric.calculate_status()
    return Metric(
        name=metric.name,
        value=metric.value,
        metric_type=metric.metric_type,
        category=metric.category,
        unit=metric.unit,
        status=status,
        threshold_min=metric.threshold_min,
        threshold_max=metric.threshold_max,
        description=metric.description
    )


def create_sentiment_score_metric(
    sentiment_score: float,
    sentiment_label: str
) -> Metric:
    """
    Factory: Crea métrica de sentimiento
    
    Args:
        sentiment_score: Score del modelo (0-1)
        sentiment_label: Etiqueta de sentimiento
        
    Returns:
        Metric de tipo RATIO categoría SENTIMENT
    """
    # Determinar status basado en sentimiento
    status = MetricStatus.GOOD
    if "negative" in sentiment_label.lower():
        status = MetricStatus.POOR
    elif "very_negative" in sentiment_label.lower():
        status = MetricStatus.CRITICAL
    elif "positive" in sentiment_label.lower():
        status = MetricStatus.EXCELLENT
    
    return Metric(
        name="sentiment_score",
        value=sentiment_score,
        metric_type=MetricType.RATIO,
        category=MetricCategory.SENTIMENT,
        status=status,
        threshold_min=0.5,
        threshold_target=0.8,
        description=f"Análisis de sentimiento: {sentiment_label}"
    )


def create_compliance_metric(
    compliance_percentage: float,
    threshold_min: float = 80.0
) -> Metric:
    """
    Factory: Crea métrica de cumplimiento
    
    Args:
        compliance_percentage: Porcentaje de cumplimiento (0-100)
        threshold_min: Mínimo aceptable
        
    Returns:
        Metric de tipo PERCENTAGE categoría COMPLIANCE
    """
    metric = Metric(
        name="compliance_rate",
        value=compliance_percentage,
        metric_type=MetricType.PERCENTAGE,
        category=MetricCategory.COMPLIANCE,
        unit="%",
        threshold_min=threshold_min,
        threshold_target=100.0,
        description="Tasa de cumplimiento normativo"
    )
    
    status = metric.calculate_status()
    return Metric(
        name=metric.name,
        value=metric.value,
        metric_type=metric.metric_type,
        category=metric.category,
        unit=metric.unit,
        status=status,
        threshold_min=metric.threshold_min,
        threshold_target=metric.threshold_target,
        description=metric.description
    )

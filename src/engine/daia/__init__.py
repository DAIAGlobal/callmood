"""
CallMood - Sistema de Auditoría de Llamadas (paquete `daia` por compatibilidad)
Enterprise-grade call audit framework (DDD + Clean Architecture).

Capas:
- Domain: Modelos de negocio (AuditedCall, Finding, Metric, AuditResult)
- Application: Servicios (BatchAuditService)
- Infrastructure: Implementaciones técnicas (pipeline, reporting, drive) — importar explícitamente.
- Presentation: CLI (`run_daia.py`) y GUI opcional.
"""

__version__ = "2.0.0"
__author__ = "CallMood Team"

# Domain Layer
from .domain.models import (
    AuditedCall,
    Finding,
    Metric,
    AuditResult,
    CallStatus,
    ServiceLevel,
    FindingSeverity,
    FindingCategory,
    MetricType,
    MetricCategory,
    MetricStatus,
)

# Application Layer
from .application.services import (
    BatchAuditService,
    BatchAuditResult,
    process_audio_folder,
)

__all__ = [
    # Version
    '__version__',
    '__author__',
    
    # Domain Models
    'AuditedCall',
    'Finding',
    'Metric',
    'AuditResult',
    
    # Enums
    'CallStatus',
    'ServiceLevel',
    'FindingSeverity',
    'FindingCategory',
    'MetricType',
    'MetricCategory',
    'MetricStatus',
    
    # Services
    'BatchAuditService',
    'BatchAuditResult',
    'process_audio_folder',
    
]

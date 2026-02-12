"""
DAIA - Sistema de Auditoría de Llamadas
Enterprise-grade call audit framework

Version: 2.0.0
Architecture: Clean Architecture + DDD Lite

Capas:
- Domain: Modelos de negocio (AuditedCall, Finding, Metric, AuditResult)
- Application: Servicios (BatchAuditService)
- Infrastructure: Reportes (ReportGenerator)
- Presentation: GUI/CLI

Uso rápido:
    >>> from daia import process_audio_folder, generate_batch_reports
    >>> batch = process_audio_folder("audio_in/")
    >>> reports = generate_batch_reports(batch)
"""

__version__ = "2.0.0"
__author__ = "DAIA Data & Analytics"

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

# Infrastructure Layer
from .infrastructure.reporting import (
    ReportGenerator,
    ReportConfig,
    generate_batch_reports,
    generate_individual_reports,
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
    
    # Reporting
    'ReportGenerator',
    'ReportConfig',
    'generate_batch_reports',
    'generate_individual_reports',
]

"""
DAIA Infrastructure Layer

Capa de infraestructura - Implementaciones técnicas.
"""

from .reporting import (
    ReportGenerator,
    ReportConfig,
    generate_batch_reports,
    generate_individual_reports,
)

__all__ = [
    'ReportGenerator',
    'ReportConfig',
    'generate_batch_reports',
    'generate_individual_reports',
]

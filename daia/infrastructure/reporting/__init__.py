"""
DAIA Infrastructure - Reporting

Generación de reportes profesionales.
"""

from .report_generator import (
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

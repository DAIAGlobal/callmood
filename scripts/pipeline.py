"""
Compatibility shim.

The canonical location for PipelineOrchestrator is now
daia.infrastructure.pipeline. This module is kept to avoid
breaking existing scripts while the migration completes.
"""

from daia.infrastructure.pipeline.pipeline import PipelineOrchestrator

__all__ = ["PipelineOrchestrator"]

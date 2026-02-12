"""
DAIA Domain Models

Core business entities and value objects.
All models are immutable (frozen=True) for consistency.

Imports:
    - AuditedCall: Entity representing an audited phone call
    - AuditResult: Aggregate containing complete audit results
    - Finding: Value object representing a discovery/issue
    - Metric: Value object representing a measured metric
    
Enums:
    - CallStatus: States of a call
    - ServiceLevel: Audit service levels
    - FindingSeverity: Severity levels for findings
    - FindingCategory: Categories of findings
    - MetricType: Types of metrics
    - MetricCategory: Categories of metrics
    - MetricStatus: Status of metrics vs thresholds
"""

# Core models
from daia.domain.models.audited_call import (
    AuditedCall,
    CallStatus,
    ServiceLevel,
    create_new_call,
    create_completed_call,
    create_failed_call,
)

from daia.domain.models.audit_result import (
    AuditResult,
    create_empty_result,
    create_completed_result,
)

from daia.domain.models.finding import (
    Finding,
    FindingSeverity,
    FindingCategory,
    create_compliance_finding,
    create_quality_finding,
    create_risk_finding,
    create_sentiment_finding,
    create_improvement_finding,
)

from daia.domain.models.metric import (
    Metric,
    MetricType,
    MetricCategory,
    MetricStatus,
    create_qa_score_metric,
    create_duration_metric,
    create_sentiment_score_metric,
    create_compliance_metric,
)

# Export all public APIs
__all__ = [
    # Core entities
    "AuditedCall",
    "AuditResult",
    "Finding",
    "Metric",
    
    # Enums - Call
    "CallStatus",
    "ServiceLevel",
    
    # Enums - Finding
    "FindingSeverity",
    "FindingCategory",
    
    # Enums - Metric
    "MetricType",
    "MetricCategory",
    "MetricStatus",
    
    # Factory methods - Call
    "create_new_call",
    "create_completed_call",
    "create_failed_call",
    
    # Factory methods - Result
    "create_empty_result",
    "create_completed_result",
    
    # Factory methods - Finding
    "create_compliance_finding",
    "create_quality_finding",
    "create_risk_finding",
    "create_sentiment_finding",
    "create_improvement_finding",
    
    # Factory methods - Metric
    "create_qa_score_metric",
    "create_duration_metric",
    "create_sentiment_score_metric",
    "create_compliance_metric",
]

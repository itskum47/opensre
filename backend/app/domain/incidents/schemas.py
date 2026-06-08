from pydantic import BaseModel, Field
from typing import List, Dict, Any

class ConfidenceFactors(BaseModel):
    temporal_alignment: float = Field(..., description="Temporal alignment scoring (0-100)")
    evidence_strength: float = Field(..., description="Evidence strength scoring (0-100)")
    source_reliability: float = Field(..., description="Source reliability scoring (0-100)")
    historical_similarity: float = Field(..., description="Historical similarity scoring (0-100)")

class EvidenceSource(BaseModel):
    source_type: str = Field(..., description="e.g. Prometheus metric, Loki log, GitHub commit, K8s event")
    source_id: str = Field(..., description="Identifier of the specific target source")
    collected_at: str = Field(..., description="ISO 8601 collected timestamp")
    reliability_score: float = Field(..., description="Reliability weighting (0-100)")

class IncidentReportV1(BaseModel):
    schema_version: str = Field("1.0", description="Schema version of this report")
    summary: str = Field(..., description="A brief narrative summary of the incident")
    root_cause: str = Field(..., description="Identified root cause of the incident")
    confidence: float = Field(..., description="Overall calculated confidence percentage (0-100)")
    confidence_factors: ConfidenceFactors = Field(..., description="Breakdown of factors explaining the confidence score")
    timeline: List[Dict[str, Any]] = Field(default_factory=list, description="Chronological event sequence")
    evidence: List[EvidenceSource] = Field(default_factory=list, description="Explicit links to raw evidence")
    blast_radius: List[str] = Field(default_factory=list, description="Affected services or systems")
    remediation: Dict[str, Any] = Field(default_factory=dict, description="Recommended remediation actions")
    similar_incidents: List[str] = Field(default_factory=list, description="References to matching historical runs")
    service_owners: List[str] = Field(default_factory=list, description="Owners of the affected services")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional context info")

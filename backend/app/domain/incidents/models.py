import enum
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Float, Enum
from backend.app.database import Base

class InvestigationStatus(str, enum.Enum):
    QUEUED = "QUEUED"
    COLLECTING = "COLLECTING"
    NORMALIZING = "NORMALIZING"
    CORRELATING = "CORRELATING"
    TIMELINE = "TIMELINE"
    GRAPHING = "GRAPHING"
    HYPOTHESIZING = "HYPOTHESIZING"
    RANKING = "RANKING"
    REPORTING = "REPORTING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class Investigation(Base):
    __tablename__ = "investigations"

    id = Column(String, primary_key=True, index=True)
    status = Column(Enum(InvestigationStatus), default=InvestigationStatus.QUEUED, nullable=False)
    started_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    completed_at = Column(DateTime, nullable=True)
    duration = Column(Float, nullable=True)
    pipeline_version = Column(String, default="1.0", nullable=False)
    report_id = Column(String, nullable=True)

class HistoricalIncident(Base):
    __tablename__ = "historical_incidents"

    id = Column(String, primary_key=True, index=True)
    investigation_id = Column(String, nullable=True)
    keys = Column(String, nullable=False)  # JSON representation of keys list
    alerts = Column(String, nullable=False)  # JSON representation of alerts list
    error_tokens = Column(String, nullable=False)  # JSON representation of log error tokens list
    remediation_action = Column(String, nullable=True)  # JSON representation of remediation action dict

class RemediationStatus(str, enum.Enum):
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EXECUTING = "EXECUTING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class RemediationAction(Base):
    __tablename__ = "remediation_actions"

    id = Column(String, primary_key=True, index=True)
    investigation_id = Column(String, nullable=False)
    status = Column(Enum(RemediationStatus), default=RemediationStatus.PENDING_APPROVAL, nullable=False)
    action_name = Column(String, nullable=False)
    target_resource = Column(String, nullable=False)
    params = Column(String, nullable=True)  # JSON representation of dict
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)



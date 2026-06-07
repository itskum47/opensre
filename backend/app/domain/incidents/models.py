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

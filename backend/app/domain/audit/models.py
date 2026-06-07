from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, JSON, event
from backend.app.database import Base

class AuditRecord(Base):
    __tablename__ = "audit_records"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    action = Column(String, nullable=False)
    investigation_id = Column(String, index=True, nullable=True)
    payload = Column(JSON, nullable=True)

# Enforce Audit Trail immutability using SQLAlchemy event listeners
@event.listens_for(AuditRecord, 'before_update')
def block_update(mapper, connection, target):
    raise RuntimeError("Audit Trail records are immutable and cannot be updated")

@event.listens_for(AuditRecord, 'before_delete')
def block_delete(mapper, connection, target):
    raise RuntimeError("Audit Trail records are immutable and cannot be deleted")

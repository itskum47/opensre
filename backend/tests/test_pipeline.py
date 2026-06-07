import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.app.database import Base
from backend.app.domain.incidents.models import Investigation, InvestigationStatus
from backend.app.domain.incidents.pipeline import InvestigationPipeline
from backend.app.domain.audit.models import AuditRecord

@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Session = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)
    session = Session()
    yield session
    session.close()

@pytest.mark.asyncio
async def test_investigation_pipeline_flow(db_session):
    investigation_id = "test-inv-pipeline-id"
    inv = Investigation(id=investigation_id, status=InvestigationStatus.QUEUED)
    db_session.add(inv)
    db_session.commit()
    
    pipeline = InvestigationPipeline(db_session)
    await pipeline.execute(investigation_id)
    
    # Assert investigation status completed
    db_session.refresh(inv)
    assert inv.status == InvestigationStatus.COMPLETED
    assert inv.completed_at is not None
    assert inv.duration is not None
    
    # Check status transition audits were written
    audits = db_session.query(AuditRecord).filter(AuditRecord.investigation_id == investigation_id).all()
    actions = [a.action for a in audits]
    assert "status_transition" in actions
    assert "pipeline_completed" in actions

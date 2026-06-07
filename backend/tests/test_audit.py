import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.app.database import Base
from backend.app.domain.audit.models import AuditRecord

@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Session = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)
    session = Session()
    yield session
    session.close()

def test_audit_record_immutable(db_session):
    record = AuditRecord(action="investigation_created", investigation_id="123", payload={"user": "sre"})
    db_session.add(record)
    db_session.commit()
    
    # Assert update raises RuntimeError
    record.action = "investigation_updated"
    db_session.add(record)
    with pytest.raises(RuntimeError) as excinfo:
        db_session.commit()
    assert "Audit Trail records are immutable" in str(excinfo.value)
    
    db_session.rollback()
    
    # Assert delete raises RuntimeError
    db_session.delete(record)
    with pytest.raises(RuntimeError) as excinfo:
        db_session.commit()
    assert "Audit Trail records are immutable" in str(excinfo.value)

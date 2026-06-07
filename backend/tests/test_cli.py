import os
import shutil
import pytest
from unittest.mock import patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.app.database import Base
from backend.app.domain.incidents.models import Investigation, InvestigationStatus
from backend.app.domain.incidents.cli import run_investigate, run_explain
from backend.app.events.store import EventStore

@pytest.fixture(scope="module")
def db_engine():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    return engine

@pytest.fixture
def db_session(db_engine):
    Session = sessionmaker(bind=db_engine)
    session = Session()
    yield session
    session.close()

@pytest.mark.asyncio
async def test_cli_commands(db_session):
    investigation_id = "test-cli-inv-id"
    
    with patch("backend.app.domain.incidents.cli.SessionLocal", return_value=db_session):
        # 1. Test run_investigate
        await run_investigate(investigation_id)
        
        # Verify db status
        inv = db_session.query(Investigation).filter(Investigation.id == investigation_id).first()
        assert inv is not None
        assert inv.status == InvestigationStatus.COMPLETED
        assert inv.report_id is not None
        
        # Verify EventStore files were created
        store = EventStore()
        inv_dir = os.path.join(store.base_dir, investigation_id)
        assert os.path.exists(os.path.join(inv_dir, "report.json"))
        
        # 2. Test run_explain
        with patch("builtins.print") as mock_print:
            await run_explain(investigation_id)
            mock_print.assert_any_call("\n=== Root Cause Explanation Narrative ===")
            
        # Clean up
        if os.path.exists(inv_dir):
            shutil.rmtree(inv_dir)

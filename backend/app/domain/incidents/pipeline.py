import logging
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from backend.app.domain.incidents.models import Investigation, InvestigationStatus
from backend.app.domain.audit.models import AuditRecord
from backend.app.events.store import EventStore
from backend.app.providers.prometheus import PrometheusDataSource
from backend.app.providers.loki import LokiDataSource
from backend.app.providers.kubernetes import KubernetesDataSource
from backend.app.providers.github import GitHubDataSource


logger = logging.getLogger(__name__)

class InvestigationPipeline:
    def __init__(self, db: Session, pipeline_version: str = "1.0"):
        self.db = db
        self.pipeline_version = pipeline_version

    def _update_status(self, investigation_id: str, status: InvestigationStatus):
        investigation = self.db.query(Investigation).filter(Investigation.id == investigation_id).first()
        if not investigation:
            raise ValueError(f"Investigation {investigation_id} not found in database")
        
        old_status = investigation.status
        investigation.status = status
        
        # Log to Audit Trail
        audit = AuditRecord(
            action="status_transition",
            investigation_id=investigation_id,
            payload={"from": old_status.value, "to": status.value}
        )
        self.db.add(audit)
        self.db.commit()
        logger.info(f"Investigation {investigation_id} transitioned from {old_status} to {status}")

    async def execute(self, investigation_id: str):
        """Executes the full pipeline stages sequentially."""
        try:
            start_time = datetime.now(timezone.utc)
            
            # 1. Collect
            self._update_status(investigation_id, InvestigationStatus.COLLECTING)
            await self.collect(investigation_id)
            
            # 2. Normalize
            self._update_status(investigation_id, InvestigationStatus.NORMALIZING)
            await self.normalize(investigation_id)
            
            # 3. Correlate
            self._update_status(investigation_id, InvestigationStatus.CORRELATING)
            await self.correlate(investigation_id)
            
            # 4. Timeline
            self._update_status(investigation_id, InvestigationStatus.TIMELINE)
            await self.timeline(investigation_id)
            
            # 5. Graph
            self._update_status(investigation_id, InvestigationStatus.GRAPHING)
            await self.graph(investigation_id)
            
            # 6. Hypothesize
            self._update_status(investigation_id, InvestigationStatus.HYPOTHESIZING)
            await self.hypothesize(investigation_id)
            
            # 7. Rank
            self._update_status(investigation_id, InvestigationStatus.RANKING)
            await self.rank(investigation_id)
            
            # 8. Report
            self._update_status(investigation_id, InvestigationStatus.REPORTING)
            await self.report(investigation_id)
            
            # Completed
            investigation = self.db.query(Investigation).filter(Investigation.id == investigation_id).first()
            investigation.status = InvestigationStatus.COMPLETED
            investigation.completed_at = datetime.now(timezone.utc)
            investigation.duration = (investigation.completed_at - start_time).total_seconds()
            
            audit = AuditRecord(
                action="pipeline_completed",
                investigation_id=investigation_id,
                payload={"duration_seconds": investigation.duration}
            )
            self.db.add(audit)
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Investigation {investigation_id} failed: {e}", exc_info=True)
            investigation = self.db.query(Investigation).filter(Investigation.id == investigation_id).first()
            if investigation:
                investigation.status = InvestigationStatus.FAILED
                investigation.completed_at = datetime.now(timezone.utc)
                
            audit = AuditRecord(
                action="pipeline_failed",
                investigation_id=investigation_id,
                payload={"error": str(e)}
            )
            self.db.add(audit)
            self.db.commit()
            raise e

    async def collect(self, investigation_id: str):
        logger.info(f"Pipeline {investigation_id}: collect stage running")
        
        # 1. Fetch investigation details to bound queries
        investigation = self.db.query(Investigation).filter(Investigation.id == investigation_id).first()
        start_time = investigation.started_at if investigation else datetime.now(timezone.utc)
        
        # Format timestamps for different data sources
        start_unix = int(start_time.timestamp())
        end_unix = int(datetime.now(timezone.utc).timestamp())
        
        start_ns = str(start_unix * 1000000000)
        end_ns = str(end_unix * 1000000000)
        
        since_iso = start_time.isoformat()
        until_iso = datetime.now(timezone.utc).isoformat()

        # 2. Define data sources
        sources = [
            PrometheusDataSource(),
            LokiDataSource(),
            KubernetesDataSource(),
            GitHubDataSource()
        ]
        
        # 3. Query params map for each source type
        query_params_map = {
            "prometheus": {
                "query": "sum(rate(container_cpu_usage_seconds_total[5m])) by (pod)",
                "start": str(start_unix),
                "end": str(end_unix),
                "step": "15s"
            },
            "loki": {
                "query": '{app="redis"}',
                "start": start_ns,
                "end": end_ns,
                "limit": 1000
            },
            "kubernetes": {
                "namespace": "default"
            },
            "github": {
                "since": since_iso,
                "until": until_iso
            }
        }
        
        store = EventStore()
        
        # 4. Asynchronously gather evidence from all plugins and write to EventStore
        for source in sources:
            source_type = source.get_source_type()
            params = query_params_map.get(source_type, {})
            try:
                events = await source.collect_evidence(investigation_id, params)
                for event in events:
                    source_id = event.get("source_id", "default")
                    payload = event.get("payload", {})
                    store.write_event(
                        investigation_id=investigation_id,
                        source_type=source_type,
                        source_id=source_id,
                        payload=payload
                    )
                logger.info(f"Successfully collected and stored evidence for source type: {source_type}")
            except Exception as e:
                logger.error(f"Failed to collect evidence for source type {source_type}: {e}")
                raise e


    async def normalize(self, investigation_id: str):
        logger.info(f"Pipeline {investigation_id}: normalize stage running")
        pass

    async def correlate(self, investigation_id: str):
        logger.info(f"Pipeline {investigation_id}: correlate stage running")
        pass

    async def timeline(self, investigation_id: str):
        logger.info(f"Pipeline {investigation_id}: timeline stage running")
        pass

    async def graph(self, investigation_id: str):
        logger.info(f"Pipeline {investigation_id}: graph stage running")
        pass

    async def hypothesize(self, investigation_id: str):
        logger.info(f"Pipeline {investigation_id}: hypothesize stage running")
        pass

    async def rank(self, investigation_id: str):
        logger.info(f"Pipeline {investigation_id}: rank stage running")
        pass

    async def report(self, investigation_id: str):
        logger.info(f"Pipeline {investigation_id}: report stage running")
        pass

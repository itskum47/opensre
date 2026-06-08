import os
import json
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
from backend.app.domain.incidents.timeline import TimelineBuilder, CorrelationEngine
from backend.app.domain.incidents.graph import GraphProvider
from backend.app.domain.incidents.ranker import RootCauseRanker




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
        store = EventStore()
        builder = TimelineBuilder(store)
        raw_timeline = builder.build_raw_timeline(investigation_id)
        
        timeline_path = os.path.join(store.base_dir, investigation_id, "timeline.json")
        with open(timeline_path, "w", encoding="utf-8") as f:
            json.dump(raw_timeline, f, indent=2)
        logger.info(f"Pipeline {investigation_id}: normalized timeline persisted with {len(raw_timeline)} events")

    async def correlate(self, investigation_id: str):
        logger.info(f"Pipeline {investigation_id}: correlate stage running")
        store = EventStore()
        timeline_path = os.path.join(store.base_dir, investigation_id, "timeline.json")
        try:
            with open(timeline_path, "r", encoding="utf-8") as f:
                raw_timeline = json.load(f)
        except Exception:
            builder = TimelineBuilder(store)
            raw_timeline = builder.build_raw_timeline(investigation_id)
            
        engine = CorrelationEngine()
        groups = engine.correlate_events(raw_timeline)
        
        groups_path = os.path.join(store.base_dir, investigation_id, "correlated_groups.json")
        with open(groups_path, "w", encoding="utf-8") as f:
            json.dump(groups, f, indent=2)
        logger.info(f"Pipeline {investigation_id}: correlation completed with {len(groups)} groups")

    async def timeline(self, investigation_id: str):
        logger.info(f"Pipeline {investigation_id}: timeline stage running")
        store = EventStore()
        timeline_path = os.path.join(store.base_dir, investigation_id, "timeline.json")
        try:
            with open(timeline_path, "r", encoding="utf-8") as f:
                raw_timeline = json.load(f)
            logger.info(f"Pipeline {investigation_id} Timeline Summary:")
            for ev in raw_timeline[:10]:
                logger.info(f"  [{ev['timestamp']}] {ev['source_type']} | {ev['event_type']} - {ev['description']}")
            if len(raw_timeline) > 10:
                logger.info(f"  ... and {len(raw_timeline) - 10} more events")
        except Exception as e:
            logger.error(f"Failed to generate timeline log: {e}")


    async def graph(self, investigation_id: str):
        logger.info(f"Pipeline {investigation_id}: graph stage running")
        store = EventStore()
        groups_path = os.path.join(store.base_dir, investigation_id, "correlated_groups.json")
        
        try:
            with open(groups_path, "r", encoding="utf-8") as f:
                groups = json.load(f)
        except Exception:
            groups = []

        provider = GraphProvider(investigation_id=investigation_id)
        all_keys = set()
        for g in groups:
            all_keys.update(g.get("keys", []))
            
        for k in all_keys:
            node_type = "database" if "db" in k or "postgres" in k else ("cache" if "redis" in k or "memcached" in k else "service")
            provider.add_node(k, node_type=node_type)
            
        if "auth-service" in all_keys:
            if "db-service" in all_keys:
                provider.add_edge("auth-service", "db-service")
            if "redis" in all_keys:
                provider.add_edge("auth-service", "redis")

        topology_path = os.path.join(store.base_dir, investigation_id, "topology.json")
        with open(topology_path, "w", encoding="utf-8") as f:
            json.dump(provider.to_dict(), f, indent=2)
        logger.info(f"Pipeline {investigation_id}: graph topology persisted with {len(all_keys)} nodes")

    async def hypothesize(self, investigation_id: str):
        logger.info(f"Pipeline {investigation_id}: hypothesize stage running")
        pass

    async def rank(self, investigation_id: str):
        logger.info(f"Pipeline {investigation_id}: rank stage running")
        store = EventStore()
        
        investigation = self.db.query(Investigation).filter(Investigation.id == investigation_id).first()
        started_at = investigation.started_at if investigation else datetime.now(timezone.utc)
        if started_at.tzinfo is None:
            started_at = started_at.replace(tzinfo=timezone.utc)

        groups_path = os.path.join(store.base_dir, investigation_id, "correlated_groups.json")
        try:
            with open(groups_path, "r", encoding="utf-8") as f:
                groups = json.load(f)
        except Exception:
            groups = []

        topology_path = os.path.join(store.base_dir, investigation_id, "topology.json")
        try:
            with open(topology_path, "r", encoding="utf-8") as f:
                topology_data = json.load(f)
            graph_provider = GraphProvider.from_dict(topology_data)
        except Exception:
            graph_provider = GraphProvider(investigation_id=investigation_id)

        ranker = RootCauseRanker(graph_provider)
        candidates = ranker.rank_hypotheses(started_at, groups)

        hypotheses_path = os.path.join(store.base_dir, investigation_id, "hypotheses.json")
        with open(hypotheses_path, "w", encoding="utf-8") as f:
            json.dump(candidates, f, indent=2)
            
        logger.info(f"Pipeline {investigation_id}: ranked {len(candidates)} hypotheses")

    async def report(self, investigation_id: str):
        logger.info(f"Pipeline {investigation_id}: report stage running")
        store = EventStore()
        
        # 1. Load timeline
        timeline_path = os.path.join(store.base_dir, investigation_id, "timeline.json")
        try:
            with open(timeline_path, "r", encoding="utf-8") as f:
                raw_timeline = json.load(f)
        except Exception:
            raw_timeline = []

        # 2. Load hypotheses
        hypotheses_path = os.path.join(store.base_dir, investigation_id, "hypotheses.json")
        try:
            with open(hypotheses_path, "r", encoding="utf-8") as f:
                hypotheses = json.load(f)
        except Exception:
            hypotheses = []

        top_hyp = hypotheses[0] if hypotheses else {}
        metrics = top_hyp.get("metrics", {})
        
        # 3. Extract root cause, confidence, etc.
        root_cause = "Unknown"
        confidence_score = 0.0
        if top_hyp:
            keys = top_hyp.get("keys", [])
            root_cause = f"Failure in service dependencies matching keys: {', '.join(keys)}" if keys else "Unknown resource failure"
            confidence_score = top_hyp.get("confidence_score", 0.0) * 100.0

        # Construct ConfidenceFactors
        from backend.app.domain.incidents.schemas import IncidentReportV1, ConfidenceFactors, EvidenceSource
        
        factors = ConfidenceFactors(
            temporal_alignment=metrics.get("temporal_score", 0.0) * 100.0,
            evidence_strength=metrics.get("evidence_density", 0.0) * 100.0,
            source_reliability=metrics.get("source_reliability", 0.0) * 100.0,
            historical_similarity=metrics.get("change_history", 0.0) * 100.0
        )

        # Generate EvidenceSources
        evidence_sources = []
        for e in raw_timeline[:5]:
            evidence_sources.append(EvidenceSource(
                source_type=e.get("source_type", "unknown"),
                source_id=e.get("source_id", "unknown"),
                collected_at=e.get("timestamp", datetime.now(timezone.utc).isoformat()),
                reliability_score=80.0
            ))

        # Blast radius (affected systems)
        blast_radius = top_hyp.get("keys", [])

        # Build IncidentReportV1
        report_payload = IncidentReportV1(
            summary=f"Automated incident investigation {investigation_id} completed.",
            root_cause=root_cause,
            confidence=confidence_score,
            confidence_factors=factors,
            timeline=raw_timeline,
            evidence=evidence_sources,
            blast_radius=blast_radius,
            remediation={"action": "Rollback deployment or restart affected pods"},
            metadata={"pipeline_version": self.pipeline_version}
        )

        # Write to report.json
        report_path = os.path.join(store.base_dir, investigation_id, "report.json")
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report_payload.model_dump_json(indent=2))

        # Update db Investigation entry with report_id
        investigation = self.db.query(Investigation).filter(Investigation.id == investigation_id).first()
        if investigation:
            investigation.report_id = f"report_{investigation_id}"
            self.db.commit()
            
        logger.info(f"Pipeline {investigation_id}: report persisted successfully")


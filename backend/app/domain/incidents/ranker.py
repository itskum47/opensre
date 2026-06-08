from datetime import datetime, timezone
import logging
from typing import Dict, Any, List
from backend.app.domain.incidents.graph import GraphProvider

logger = logging.getLogger(__name__)

class RootCauseRanker:
    def __init__(self, graph_provider: GraphProvider = None, memory_engine = None):
        self.graph_provider = graph_provider or GraphProvider()
        self.memory_engine = memory_engine

    def _parse_iso(self, ts_str: str) -> datetime:
        cleaned = ts_str.replace("Z", "+00:00")
        dt = datetime.fromisoformat(cleaned)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt

    def rank_hypotheses(self, started_at: datetime, correlated_groups: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Evaluates and ranks root cause hypotheses from correlated event groups."""
        candidates = []

        for group in correlated_groups:
            group_id = group.get("group_id")
            events = group.get("events", [])
            keys = group.get("keys", [])

            if not events:
                continue

            # 1. Temporal Proximity Factor
            event_times = [self._parse_iso(e["timestamp"]) for e in events]
            earliest_time = min(event_times)
            time_diff = abs((earliest_time - started_at).total_seconds())
            temporal_score = max(0.0, 1.0 - (time_diff / 3600.0))

            # 2. Evidence Density Factor
            anomalies = 0
            for e in events:
                desc = e.get("description", "").lower()
                event_type = e.get("event_type", "")
                if (
                    event_type == "k8s_event" or 
                    any(word in desc for word in ["error", "fail", "exception", "unhealthy", "warning", "critical"])
                ):
                    anomalies += 1
            evidence_density = anomalies / len(events) if events else 0.0

            # 3. Source Reliability Factor
            source_reliability = 0.5
            has_warning = False
            has_error_log = False
            for e in events:
                e_type = e.get("event_type", "")
                desc = e.get("description", "").lower()
                if e_type == "k8s_event" and "warning" in desc:
                    has_warning = True
                elif e_type == "log_entry" and any(w in desc for w in ["error", "exception", "fail"]):
                    has_error_log = True

            if has_warning:
                source_reliability = 1.0
            elif has_error_log:
                source_reliability = 0.9

            # 4. Change History Factor
            has_commit = any(e.get("event_type") == "git_commit" for e in events)
            change_history = 1.0 if has_commit else 0.0

            # Query memory engine for historical incidents similarity
            similar_incidents_list = []
            historical_remediation = None
            if self.memory_engine:
                try:
                    from backend.app.domain.incidents.memory import extract_features_from_report
                    act_keys, act_alerts, act_tokens = extract_features_from_report({
                        "blast_radius": keys,
                        "timeline": events
                    })
                    similar = self.memory_engine.find_similar_incidents(
                        active_keys=act_keys,
                        active_alerts=act_alerts,
                        active_tokens=act_tokens,
                        threshold=0.2
                    )
                    if similar:
                        # Set change_history metric to best match similarity score
                        change_history = similar[0]["similarity"]
                        historical_remediation = similar[0].get("remediation_action")
                        similar_incidents_list = [s["investigation_id"] for s in similar]
                except Exception as me_err:
                    logger.warning(f"Error querying memory engine in ranker: {me_err}")

            # Compute weighted confidence score
            confidence = (0.25 * temporal_score + 
                          0.25 * evidence_density + 
                          0.25 * source_reliability + 
                          0.25 * change_history)

            evidence_snippets = [
                f"[{e.get('source_type')}] {e.get('description')}"
                for e in events if e.get("event_type") in ["k8s_event", "git_commit", "log_entry"] or "error" in e.get("description", "").lower()
            ][:5]

            explanation = (
                f"Temporal Score: {temporal_score:.2f} (diff: {time_diff/60.0:.1f}m), "
                f"Evidence Density: {evidence_density:.2f} ({anomalies}/{len(events)} anomalies), "
                f"Source Reliability: {source_reliability:.2f}, "
                f"Change History: {change_history:.2f}."
            )

            candidates.append({
                "group_id": group_id,
                "confidence_score": round(confidence, 4),
                "keys": keys,
                "evidence": evidence_snippets,
                "explanation": explanation,
                "metrics": {
                    "temporal_score": temporal_score,
                    "evidence_density": evidence_density,
                    "source_reliability": source_reliability,
                    "change_history": change_history
                },
                "similar_incidents": similar_incidents_list,
                "remediation": historical_remediation
            })

        candidates.sort(key=lambda x: x["confidence_score"], reverse=True)
        return candidates

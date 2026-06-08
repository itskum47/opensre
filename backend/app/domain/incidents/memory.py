import json
import logging
import re
from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from backend.app.domain.incidents.models import HistoricalIncident

logger = logging.getLogger(__name__)

def jaccard_similarity(set_a: set, set_b: set) -> float:
    """Calculates Jaccard similarity between two sets."""
    union_len = len(set_a.union(set_b))
    if union_len == 0:
        return 0.0
    return len(set_a.intersection(set_b)) / union_len

def extract_features_from_report(report_data: dict) -> Tuple[List[str], List[str], List[str]]:
    """Extracts keys, alerts, and error tokens from an incident report dict."""
    # 1. Extract resource keys
    keys = list(report_data.get("blast_radius", []))
    if not keys:
        # Fallback to key extraction if blast_radius is empty
        root_cause = report_data.get("root_cause", "")
        if root_cause and "keys:" in root_cause:
            try:
                extracted = root_cause.split("keys:")[-1].strip()
                keys = [k.strip() for k in extracted.split(",") if k.strip()]
            except Exception:
                pass

    # 2. Extract alerts and error tokens from timeline
    alerts = []
    error_tokens = []
    
    timeline = report_data.get("timeline", []) or []
    for event in timeline:
        if not isinstance(event, dict):
            continue
        desc = event.get("description", "").lower()
        metadata = event.get("metadata", {}) or {}
        source_type = event.get("source_type", "")
        event_type = event.get("event_type", "")
        
        # Extract alert identifiers
        if source_type == "prometheus":
            metric_name = metadata.get("metric")
            if metric_name:
                alerts.append(metric_name)
        elif source_type == "kubernetes" and event_type == "k8s_event":
            reason = metadata.get("reason")
            if reason:
                alerts.append(reason)
                
        # Extract general alert/warning/critical mentions
        if "alert" in desc or "warning" in desc:
            # If the description contains alert/warning and details, try to get keywords
            words = re.findall(r"[a-zA-Z0-9_\-]+", desc)
            for w in words:
                if len(w) >= 4 and w.lower() in ("alert", "warning", "critical", "fail", "failed"):
                    alerts.append(w.lower())

        # Extract error tokens
        is_error = False
        if event_type in ("k8s_event", "log_entry"):
            if any(w in desc for w in ["error", "fail", "exception", "unhealthy", "warning", "critical", "killed"]):
                is_error = True
        
        if is_error:
            words = re.findall(r"[a-zA-Z0-9_\-]+", desc)
            for w in words:
                w_lower = w.lower()
                if len(w_lower) >= 3 and not w_lower.isdigit():
                    if w_lower not in {"the", "and", "for", "with", "was", "has", "not", "but", "this", "that", "from", "error", "failed"}:
                        error_tokens.append(w_lower)

    # Unique sorted lists
    keys = sorted(list(set(keys)))
    alerts = sorted(list(set(alerts)))
    error_tokens = sorted(list(set(error_tokens)))
    
    return keys, alerts, error_tokens

class IncidentMemoryEngine:
    def __init__(self, db: Session):
        self.db = db

    def index_incident(self, investigation_id: str, report_data: dict) -> bool:
        """Serializes and indexes completed investigation profile into database memory."""
        try:
            keys, alerts, error_tokens = extract_features_from_report(report_data)
            remediation = report_data.get("remediation", {})
            
            hist_id = f"hist_{investigation_id}"
            
            existing = self.db.query(HistoricalIncident).filter(
                HistoricalIncident.investigation_id == investigation_id
            ).first()
            
            if existing:
                existing.keys = json.dumps(keys)
                existing.alerts = json.dumps(alerts)
                existing.error_tokens = json.dumps(error_tokens)
                existing.remediation_action = json.dumps(remediation)
            else:
                hist_record = HistoricalIncident(
                    id=hist_id,
                    investigation_id=investigation_id,
                    keys=json.dumps(keys),
                    alerts=json.dumps(alerts),
                    error_tokens=json.dumps(error_tokens),
                    remediation_action=json.dumps(remediation)
                )
                self.db.add(hist_record)
                
            self.db.commit()
            logger.info(f"Successfully indexed incident {investigation_id} in memory.")
            return True
        except Exception as e:
            logger.error(f"Failed to index incident in memory: {e}", exc_info=True)
            self.db.rollback()
            return False

    def find_similar_incidents(
        self, 
        active_keys: List[str], 
        active_alerts: List[str], 
        active_tokens: List[str], 
        threshold: float = 0.2
    ) -> List[Dict[str, Any]]:
        """Finds historical incidents matching active features using Jaccard similarity."""
        try:
            records = self.db.query(HistoricalIncident).all()
            matches = []
            
            active_keys_set = set(active_keys)
            active_alerts_set = set(active_alerts)
            active_tokens_set = set(active_tokens)
            
            for rec in records:
                try:
                    rec_keys = set(json.loads(rec.keys or "[]"))
                    rec_alerts = set(json.loads(rec.alerts or "[]"))
                    rec_tokens = set(json.loads(rec.error_tokens or "[]"))
                except Exception as je:
                    logger.warning(f"Failed to parse historical record JSON fields for {rec.id}: {je}")
                    continue
                
                # Calculate Jaccard similarity for each attribute
                sim_keys = jaccard_similarity(active_keys_set, rec_keys)
                sim_alerts = jaccard_similarity(active_alerts_set, rec_alerts)
                sim_tokens = jaccard_similarity(active_tokens_set, rec_tokens)
                
                # Combine Jaccard similarity using only non-empty feature categories
                valid_scores = []
                if len(active_keys_set) > 0 or len(rec_keys) > 0:
                    valid_scores.append(sim_keys)
                if len(active_alerts_set) > 0 or len(rec_alerts) > 0:
                    valid_scores.append(sim_alerts)
                if len(active_tokens_set) > 0 or len(rec_tokens) > 0:
                    valid_scores.append(sim_tokens)
                    
                similarity = sum(valid_scores) / len(valid_scores) if valid_scores else 0.0
                
                if similarity >= threshold:
                    remediation = json.loads(rec.remediation_action or "{}")
                    matches.append({
                        "id": rec.id,
                        "investigation_id": rec.investigation_id,
                        "similarity": round(similarity, 4),
                        "keys": list(rec_keys),
                        "alerts": list(rec_alerts),
                        "error_tokens": list(rec_tokens),
                        "remediation_action": remediation
                    })
            
            # Sort by similarity score descending
            matches.sort(key=lambda x: x["similarity"], reverse=True)
            return matches
        except Exception as e:
            logger.error(f"Failed to query similar incidents: {e}", exc_info=True)
            return []

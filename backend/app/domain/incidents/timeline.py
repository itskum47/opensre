from datetime import datetime, timezone
import json
import logging
from typing import Dict, Any, List
from backend.app.events.store import EventStore

logger = logging.getLogger(__name__)

class TimelineBuilder:
    def __init__(self, event_store: EventStore = None):
        self.event_store = event_store or EventStore()

    def _parse_timestamp(self, ts_val: Any) -> datetime:
        """Helper to parse various timestamp formats to timezone-aware UTC datetime."""
        dt = None
        if not ts_val:
            dt = datetime.now(timezone.utc)
        elif isinstance(ts_val, (int, float)):
            if ts_val > 2e11:
                dt = datetime.fromtimestamp(ts_val / 1e9, tz=timezone.utc)
            else:
                dt = datetime.fromtimestamp(ts_val, tz=timezone.utc)
        elif isinstance(ts_val, str):
            try:
                num = float(ts_val)
                if num > 2e11:
                    dt = datetime.fromtimestamp(num / 1e9, tz=timezone.utc)
                else:
                    dt = datetime.fromtimestamp(num, tz=timezone.utc)
            except ValueError:
                pass
            
            if dt is None:
                try:
                    cleaned = ts_val.replace("Z", "+00:00")
                    dt = datetime.fromisoformat(cleaned)
                except ValueError:
                    pass
                    
        if dt is None:
            dt = datetime.now(timezone.utc)
            
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        else:
            dt = dt.astimezone(timezone.utc)
        return dt

    def build_raw_timeline(self, investigation_id: str) -> List[Dict[str, Any]]:
        """Reads all events for investigation_id, normalizes and sorts them."""
        raw_events = self.event_store.get_events(investigation_id)
        normalized_events = []

        for raw in raw_events:
            if not isinstance(raw, dict):
                continue
            source_type = raw.get("source_type")
            source_id = raw.get("source_id")
            payload = raw.get("payload", {})


            if source_type == "prometheus":
                data = payload.get("data", {})
                result = data.get("result", [])
                for item in result:
                    metric_info = item.get("metric", {})
                    values = item.get("values", [])
                    pod_name = metric_info.get("pod", "unknown")
                    metric_name = metric_info.get("__name__", source_id)
                    
                    for val_coord in values:
                        ts_val = val_coord[0]
                        metric_val = val_coord[1]
                        dt = self._parse_timestamp(ts_val)
                        
                        normalized_events.append({
                            "timestamp": dt.isoformat(),
                            "source_type": source_type,
                            "source_id": source_id,
                            "event_type": "metric_datapoint",
                            "description": f"Metric {metric_name} for pod {pod_name} is {metric_val}",
                            "metadata": {
                                "metric": metric_name,
                                "pod": pod_name,
                                "value": float(metric_val) if "." in metric_val or metric_val.isdigit() else metric_val,
                                "labels": metric_info
                            }
                        })

            elif source_type == "loki":
                data = payload.get("data", {})
                result = data.get("result", [])
                for item in result:
                    stream_info = item.get("stream", {})
                    values = item.get("values", [])
                    pod_name = stream_info.get("pod") or stream_info.get("app") or "unknown"
                    
                    for val_coord in values:
                        ts_val = val_coord[0]
                        log_line = val_coord[1]
                        dt = self._parse_timestamp(ts_val)
                        
                        normalized_events.append({
                            "timestamp": dt.isoformat(),
                            "source_type": source_type,
                            "source_id": source_id,
                            "event_type": "log_entry",
                            "description": log_line,
                            "metadata": {
                                "pod": pod_name,
                                "stream": stream_info
                            }
                        })

            elif source_type == "kubernetes":
                events = payload.get("events", [])
                for ev in events:
                    ts_val = ev.get("timestamp")
                    dt = self._parse_timestamp(ts_val)
                    
                    normalized_events.append({
                        "timestamp": dt.isoformat(),
                        "source_type": source_type,
                        "source_id": source_id,
                        "event_type": "k8s_event",
                        "description": f"[{ev.get('type')}] {ev.get('reason')} on {ev.get('object')}: {ev.get('message')}",
                        "metadata": {
                            "type": ev.get("type"),
                            "reason": ev.get("reason"),
                            "object": ev.get("object"),
                            "message": ev.get("message")
                        }
                    })

                started_dt = self._parse_timestamp(raw.get("timestamp"))
                for pod in payload.get("pods", []):
                    normalized_events.append({
                        "timestamp": started_dt.isoformat(),
                        "source_type": source_type,
                        "source_id": source_id,
                        "event_type": "k8s_resource_state",
                        "description": f"Pod {pod.get('name')} is in state {pod.get('status')}",
                        "metadata": {
                            "resource": "pod",
                            "name": pod.get("name"),
                            "status": pod.get("status"),
                            "ip": pod.get("ip")
                        }
                    })

            elif source_type == "github":
                if isinstance(payload, list):
                    for commit_obj in payload:
                        commit_meta = commit_obj.get("commit", {})
                        author = commit_meta.get("author", {})
                        ts_val = author.get("date")
                        dt = self._parse_timestamp(ts_val)
                        sha = commit_obj.get("sha", "")
                        msg = commit_meta.get("message", "")
                        
                        normalized_events.append({
                            "timestamp": dt.isoformat(),
                            "source_type": source_type,
                            "source_id": source_id,
                            "event_type": "git_commit",
                            "description": f"GitHub commit {sha[:7]} by {author.get('name')}: {msg.splitlines()[0] if msg else ''}",
                            "metadata": {
                                "sha": sha,
                                "message": msg,
                                "author": author.get("name"),
                                "email": author.get("email"),
                                "html_url": commit_obj.get("html_url")
                            }
                        })

        # Sort chronologically by timestamp
        normalized_events.sort(key=lambda x: x["timestamp"])
        return normalized_events


class CorrelationEngine:
    def __init__(self, window_seconds: int = 300):
        self.window_seconds = window_seconds

    def _extract_resource_keys(self, event: Dict[str, Any]) -> set:
        keys = set()
        metadata = event.get("metadata", {})
        
        for field in ["pod", "app", "container", "name", "object"]:
            val = metadata.get(field)
            if val and isinstance(val, str):
                cleaned = val.split("/")[-1]
                keys.add(cleaned)
                parts = cleaned.split("-")
                if len(parts) > 1:
                    keys.add("-".join(parts[:-1]))
                    if len(parts) > 2:
                        keys.add("-".join(parts[:-2]))

        for dict_field in ["labels", "stream"]:
            sub_dict = metadata.get(dict_field, {})
            if isinstance(sub_dict, dict):
                for k in ["pod", "app", "container", "service"]:
                    v = sub_dict.get(k)
                    if v and isinstance(v, str):
                        keys.add(v)
                        parts = v.split("-")
                        if len(parts) > 1:
                            keys.add("-".join(parts[:-1]))

        # For git commits, extract potential resource keys from the message or description
        if event.get("event_type") == "git_commit":
            import re
            text = (event.get("description", "") + " " + metadata.get("message", "")).lower()
            words = re.findall(r"[a-zA-Z0-9\-]+", text)
            for w in words:
                if len(w) >= 2:
                    keys.add(w)
                    parts = w.split("-")
                    if len(parts) > 1:
                        keys.add("-".join(parts[:-1]))
                        if len(parts) > 2:
                            keys.add("-".join(parts[:-2]))
                            
        return keys

    def correlate_events(self, timeline_events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Groups related timeline events into correlated groups."""
        groups = []
        
        for event in timeline_events:
            ev_time = datetime.fromisoformat(event["timestamp"])
            ev_keys = self._extract_resource_keys(event)
            
            matched_group_idx = -1
            
            for idx, group in enumerate(groups):
                group_events = group["events"]
                last_ev = group_events[-1]
                last_time = datetime.fromisoformat(last_ev["timestamp"])
                
                time_diff = abs((ev_time - last_time).total_seconds())
                if time_diff <= self.window_seconds:
                    group_keys = group["keys"]
                    if ev_keys & group_keys:
                        matched_group_idx = idx
                        break
                        
            if matched_group_idx != -1:
                groups[matched_group_idx]["events"].append(event)
                groups[matched_group_idx]["keys"].update(ev_keys)
            else:
                groups.append({
                    "group_id": f"group_{len(groups) + 1}",
                    "keys": ev_keys,
                    "events": [event]
                })

        for group in groups:
            group["keys"] = list(group["keys"])
            
        return groups

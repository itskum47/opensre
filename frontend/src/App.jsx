import React, { useState, useEffect } from "react";
import { 
  Play, RefreshCw, AlertCircle, CheckCircle2, Server, GitBranch, 
  HelpCircle, ShieldAlert, Activity, ChevronRight, Sparkles 
} from "lucide-react";
import GraphExplorer from "./components/GraphExplorer";
import TimelineView from "./components/TimelineView";
import RemediationPanel from "./components/RemediationPanel";

// Pipeline stages in order
const PIPELINE_STAGES = [
  { id: "QUEUED", label: "Queued" },
  { id: "COLLECTING", label: "Evidence Collection" },
  { id: "NORMALIZING", label: "Normalizing" },
  { id: "CORRELATING", label: "Correlation" },
  { id: "TIMELINE", label: "Timeline Building" },
  { id: "GRAPHING", label: "Dependency Graph" },
  { id: "HYPOTHESIZING", label: "Hypothesis" },
  { id: "RANKING", label: "Root Cause Ranking" },
  { id: "REPORTING", label: "Reporting" }
];

export default function App() {
  const [investigations, setInvestigations] = useState([]);
  const [selectedId, setSelectedId] = useState(null);
  const [snapshot, setSnapshot] = useState(null);
  const [loadingList, setLoadingList] = useState(true);
  const [loadingSnapshot, setLoadingSnapshot] = useState(false);
  const [triggering, setTriggering] = useState(false);
  const [selectedInvestigation, setSelectedInvestigation] = useState(null);

  // Fetch all investigations
  const fetchInvestigations = async (selectFirst = false) => {
    try {
      const res = await fetch("http://localhost:8000/investigations");
      if (res.ok) {
        const data = await res.json();
        setInvestigations(data);
        if (selectFirst && data.length > 0) {
          setSelectedId(data[0].id);
        }
      }
    } catch (err) {
      console.error("Failed to fetch investigations:", err);
    } finally {
      setLoadingList(false);
    }
  };

  useEffect(() => {
    fetchInvestigations(true);
  }, []);

  // Poll current selected investigation if not completed/failed
  useEffect(() => {
    if (!selectedId) return;

    // Fetch investigation object first
    const fetchInvInfo = async () => {
      try {
        const res = await fetch(`http://localhost:8000/investigations/${selectedId}`);
        if (res.ok) {
          const inv = await res.json();
          setSelectedInvestigation(inv);

          // If completed, fetch snapshot
          if (inv.status === "COMPLETED") {
            fetchSnapshot(selectedId);
          } else {
            setSnapshot(null);
          }
        }
      } catch (err) {
        console.error("Failed to fetch investigation status:", err);
      }
    };

    fetchInvInfo();

    const interval = setInterval(async () => {
      try {
        const res = await fetch(`http://localhost:8000/investigations/${selectedId}`);
        if (res.ok) {
          const inv = await res.json();
          setSelectedInvestigation(inv);

          // If transitioning to completed, stop polling and load snapshot
          if (inv.status === "COMPLETED") {
            clearInterval(interval);
            fetchSnapshot(selectedId);
            fetchInvestigations(); // refresh sidebar statuses
          } else if (inv.status === "FAILED") {
            clearInterval(interval);
            fetchInvestigations();
          }
        }
      } catch (err) {
        console.error("Failed to poll investigation status:", err);
      }
    }, 2000);

    return () => clearInterval(interval);
  }, [selectedId]);

  // Fetch snapshot data
  const fetchSnapshot = async (id) => {
    setLoadingSnapshot(true);
    try {
      const res = await fetch(`http://localhost:8000/investigations/${id}/snapshot`);
      if (res.ok) {
        const snap = await res.json();
        setSnapshot(snap);
      } else {
        setSnapshot(null);
      }
    } catch (err) {
      console.error("Failed to fetch snapshot:", err);
      setSnapshot(null);
    } finally {
      setLoadingSnapshot(false);
    }
  };

  // Trigger new investigation
  const triggerNewInvestigation = async () => {
    setTriggering(true);
    try {
      const res = await fetch("http://localhost:8000/investigations", {
        method: "POST",
      });
      if (res.ok) {
        const data = await res.json();
        const newJobId = data.job_id;
        // Refresh list immediately and select the new job
        await fetchInvestigations();
        setSelectedId(newJobId);
      }
    } catch (err) {
      console.error("Failed to trigger investigation:", err);
    } finally {
      setTriggering(false);
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case "COMPLETED":
        return <CheckCircle2 className="w-4 h-4 text-emerald-400" />;
      case "FAILED":
        return <AlertCircle className="w-4 h-4 text-red-400" />;
      default:
        return <RefreshCw className="w-4 h-4 text-amber-400 animate-spin" />;
    }
  };

  const getPipelineStageIndex = (status) => {
    return PIPELINE_STAGES.findIndex((s) => s.id === status);
  };

  const currentStageIndex = selectedInvestigation 
    ? getPipelineStageIndex(selectedInvestigation.status)
    : -1;

  return (
    <div className="min-h-screen flex flex-col font-sans bg-[#080c14] text-[#f3f4f6]">
      {/* Header */}
      <header className="h-16 border-b border-white/5 bg-slate-950/40 backdrop-blur-md flex items-center justify-between px-6 z-20 sticky top-0">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-purple-600 to-blue-500 flex items-center justify-center shadow-lg shadow-purple-500/20">
            <Activity className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="font-display font-bold text-lg leading-tight tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-white via-gray-200 to-gray-400">
              OpenSRE Dashboard
            </h1>
            <p className="text-[10px] text-gray-500 uppercase tracking-widest font-semibold">
              Evidence-Based Incident RCA
            </p>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <button
            onClick={triggerNewInvestigation}
            disabled={triggering}
            className="btn btn-primary text-xs py-2 px-4 flex items-center gap-2"
          >
            {triggering ? (
              <RefreshCw className="w-3.5 h-3.5 animate-spin" />
            ) : (
              <Play className="w-3.5 h-3.5 fill-current" />
            )}
            Trigger Investigation
          </button>
        </div>
      </header>

      {/* Main Container */}
      <div className="flex-1 flex min-h-0 relative">
        {/* Sidebar */}
        <aside className="w-80 border-r border-white/5 bg-slate-950/20 flex flex-col shrink-0">
          <div className="p-4 border-b border-white/5 bg-slate-950/10">
            <h2 className="font-display font-semibold text-xs text-gray-400 uppercase tracking-wider">
              Investigation Logs
            </h2>
          </div>

          <div className="flex-1 overflow-y-auto p-2.5 space-y-1">
            {loadingList ? (
              <div className="text-center py-8 text-gray-500 text-sm">Loading runs...</div>
            ) : investigations.length === 0 ? (
              <div className="text-center py-8 text-gray-500 text-sm">No investigations found</div>
            ) : (
              investigations.map((inv) => {
                const isSelected = inv.id === selectedId;
                return (
                  <button
                    key={inv.id}
                    onClick={() => setSelectedId(inv.id)}
                    className={`w-full text-left p-3 rounded-xl border flex items-center justify-between gap-3 transition-all ${
                      isSelected
                        ? "bg-purple-500/10 border-purple-500/30 text-white shadow-[0_4px_16px_rgba(139,92,246,0.15)]"
                        : "bg-transparent border-transparent hover:bg-white/5 text-gray-400 hover:text-gray-200"
                    }`}
                  >
                    <div className="min-w-0 flex-1">
                      <p className="font-mono text-[10px] text-gray-500 truncate mb-1">
                        ID: {inv.id.substring(0, 8)}...
                      </p>
                      <p className="text-xs font-semibold font-display truncate">
                        {inv.status === "COMPLETED" 
                          ? "RCA Completed" 
                          : inv.status === "FAILED"
                          ? "Execution Failed"
                          : `Stage: ${inv.status.toLowerCase()}`
                        }
                      </p>
                      <p className="text-[10px] text-gray-500 mt-1">
                        {new Date(inv.started_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </p>
                    </div>
                    {getStatusIcon(inv.status)}
                  </button>
                );
              })
            )}
          </div>
        </aside>

        {/* Details Panel */}
        <main className="flex-1 overflow-y-auto p-6 min-w-0">
          {selectedId ? (
            <div className="flex flex-col gap-6 max-w-6xl mx-auto">
              
              {/* Top Summary Banner */}
              <div className="glass-panel p-5 flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                  <div className="flex items-center gap-2 mb-1.5">
                    <span className="font-mono text-xs text-gray-500 bg-slate-950/40 px-2 py-0.5 rounded border border-white/5">
                      RUN ID: {selectedId}
                    </span>
                    {selectedInvestigation && (
                      <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full uppercase ${
                        selectedInvestigation.status === "COMPLETED" 
                          ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                          : selectedInvestigation.status === "FAILED"
                          ? "bg-red-500/10 text-red-400 border border-red-500/20"
                          : "bg-amber-500/10 text-amber-400 border border-amber-500/20 animate-pulse"
                      }`}>
                        {selectedInvestigation.status}
                      </span>
                    )}
                  </div>
                  <h2 className="font-display font-bold text-xl text-white">
                    Incident Root Cause Analysis
                  </h2>
                </div>

                <div className="flex items-center gap-4 text-xs text-gray-400 border-l border-white/10 pl-4">
                  <div>
                    <p className="text-[10px] text-gray-500 uppercase font-semibold">Pipeline Ver</p>
                    <p className="text-white font-mono mt-0.5">v{selectedInvestigation?.pipeline_version || "1.0"}</p>
                  </div>
                  {selectedInvestigation?.duration && (
                    <div>
                      <p className="text-[10px] text-gray-500 uppercase font-semibold">Exec Duration</p>
                      <p className="text-white font-mono mt-0.5">{selectedInvestigation.duration.toFixed(2)}s</p>
                    </div>
                  )}
                </div>
              </div>

              {/* Progress Pipeline Stages Tracker (shown when not completed/failed) */}
              {selectedInvestigation && 
               selectedInvestigation.status !== "COMPLETED" && 
               selectedInvestigation.status !== "FAILED" && (
                <div className="glass-panel p-6">
                  <h3 className="font-display font-semibold text-sm text-white mb-4">
                    Pipeline Execution Progress
                  </h3>
                  <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3.5">
                    {PIPELINE_STAGES.map((stage, idx) => {
                      const isPast = idx < currentStageIndex;
                      const isCurrent = idx === currentStageIndex;
                      return (
                        <div
                          key={stage.id}
                          className={`p-3 rounded-xl border flex flex-col gap-1 transition-all ${
                            isCurrent
                              ? "bg-purple-500/10 border-purple-500/40 text-purple-200 animate-pulse"
                              : isPast
                              ? "bg-emerald-500/5 border-emerald-500/20 text-emerald-400/90"
                              : "bg-slate-950/20 border-white/5 text-gray-500"
                          }`}
                        >
                          <div className="flex items-center justify-between">
                            <span className="text-[10px] font-mono">Stage 0{idx + 1}</span>
                            {isPast && <CheckCircle2 className="w-3.5 h-3.5" />}
                          </div>
                          <span className="text-xs font-semibold truncate">{stage.label}</span>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}

              {/* Failed Banner */}
              {selectedInvestigation?.status === "FAILED" && (
                <div className="glass-panel p-5 bg-red-500/5 border border-red-500/15 flex items-center gap-3">
                  <AlertCircle className="w-8 h-8 text-red-500 shrink-0" />
                  <div>
                    <h4 className="font-semibold text-red-400 font-display">Investigation Aborted</h4>
                    <p className="text-xs text-red-300/80 leading-relaxed mt-0.5">
                      The execution pipeline crashed during event normalization or rank analysis. Verify details in worker console output logs.
                    </p>
                  </div>
                </div>
              )}

              {/* Snapshot Content (shown when completed) */}
              {snapshot ? (
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                  
                  {/* Left Column: Metrics & D3 Graph */}
                  <div className="lg:col-span-2 flex flex-col gap-6">
                    
                    {/* Root Cause Card */}
                    <div className="glass-panel p-5 relative overflow-hidden">
                      <div className="absolute top-0 right-0 p-4 opacity-5 pointer-events-none">
                        <Sparkles className="w-24 h-24 text-purple-400" />
                      </div>
                      
                      <div className="flex items-center gap-2 text-xs font-semibold text-purple-400 mb-2">
                        <Sparkles className="w-4 h-4" />
                        SUSPECTED ROOT CAUSE
                      </div>
                      
                      <h3 className="font-display font-bold text-lg text-white mb-2 leading-snug">
                        {snapshot.report?.root_cause || "Analyzing..."}
                      </h3>
                      
                      <p className="text-xs text-gray-400 leading-relaxed mb-4">
                        {snapshot.report?.summary || "Incident explanation is being compiled by reasoning model."}
                      </p>

                      {/* Confidence Score Grid */}
                      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 pt-4 border-t border-white/5">
                        <div className="bg-slate-950/20 rounded-xl p-3 border border-white/5 flex flex-col">
                          <span className="text-[10px] text-gray-500 font-semibold uppercase">Confidence</span>
                          <span className="text-lg font-bold text-purple-400 font-display mt-0.5">
                            {snapshot.report?.confidence?.toFixed(1) || 0}%
                          </span>
                        </div>
                        <div className="bg-slate-950/20 rounded-xl p-3 border border-white/5 flex flex-col">
                          <span className="text-[10px] text-gray-500 font-semibold uppercase">Temp Align</span>
                          <span className="text-sm font-bold text-gray-200 mt-1">
                            {snapshot.report?.confidence_factors?.temporal_alignment?.toFixed(1) || 0}%
                          </span>
                        </div>
                        <div className="bg-slate-950/20 rounded-xl p-3 border border-white/5 flex flex-col">
                          <span className="text-[10px] text-gray-500 font-semibold uppercase">Evidence Den</span>
                          <span className="text-sm font-bold text-gray-200 mt-1">
                            {snapshot.report?.confidence_factors?.evidence_strength?.toFixed(1) || 0}%
                          </span>
                        </div>
                        <div className="bg-slate-950/20 rounded-xl p-3 border border-white/5 flex flex-col">
                          <span className="text-[10px] text-gray-500 font-semibold uppercase">Similarity</span>
                          <span className="text-sm font-bold text-gray-200 mt-1">
                            {snapshot.report?.confidence_factors?.historical_similarity?.toFixed(1) || 0}%
                          </span>
                        </div>
                      </div>
                    </div>

                    {/* D3 Topology Dependency Graph */}
                    <div className="glass-panel p-5 flex flex-col gap-3">
                      <h3 className="font-display font-semibold text-sm text-white">
                        Dependency Graph & Blast Radius
                      </h3>
                      <GraphExplorer 
                        graphData={snapshot.graph} 
                        rootCauseKeys={snapshot.report?.blast_radius || []} 
                      />
                    </div>

                    {/* Similar Incidents (Memory RCA) */}
                    {snapshot.report?.similar_incidents && snapshot.report.similar_incidents.length > 0 && (
                      <div className="glass-panel p-5 flex flex-col gap-3">
                        <h3 className="font-display font-semibold text-sm text-white flex items-center gap-2">
                          <Clock className="w-4 h-4 text-purple-400" />
                          Similar Historical Incidents (Cosine Memory RCA)
                        </h3>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                          {snapshot.report.similar_incidents.map((histId, hIdx) => (
                            <button
                              key={hIdx}
                              onClick={() => setSelectedId(histId)}
                              className="text-left p-3 rounded-xl border border-white/5 bg-slate-950/20 hover:bg-slate-900/40 hover:border-white/10 transition-all flex items-center justify-between"
                            >
                              <div className="font-mono text-xs text-gray-300">
                                {histId}
                              </div>
                              <ChevronRight className="w-4 h-4 text-gray-500" />
                            </button>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Right Column: Remediation & Evidence Timeline */}
                  <div className="lg:col-span-1 flex flex-col gap-6">
                    
                    {/* Remediation Panel */}
                    <RemediationPanel 
                      investigationId={selectedId} 
                      remediationData={snapshot.report?.remediation}
                    />

                    {/* Scrollable Timeline */}
                    <div className="h-[500px]">
                      <TimelineView events={snapshot.report?.timeline} />
                    </div>
                  </div>

                </div>
              ) : selectedInvestigation?.status === "COMPLETED" ? (
                <div className="text-center py-20 text-gray-500">
                  <RefreshCw className="w-8 h-8 animate-spin mx-auto mb-4 text-purple-500" />
                  Loading unified incident snapshot...
                </div>
              ) : selectedInvestigation?.status !== "FAILED" ? (
                <div className="text-center py-20 text-gray-500">
                  Waiting for active pipeline execution stages to finalize...
                </div>
              ) : null}

            </div>
          ) : (
            <div className="h-full flex flex-col items-center justify-center text-center p-8">
              <Server className="w-16 h-16 text-gray-700 mb-4" />
              <h3 className="font-display font-bold text-xl text-gray-400 mb-1">
                No active run selected
              </h3>
              <p className="text-sm text-gray-500 max-w-sm">
                Select a completed incident run from the log history or trigger a new real-time SRE analysis.
              </p>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}

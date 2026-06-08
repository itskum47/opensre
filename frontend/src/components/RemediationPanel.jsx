import React, { useState, useEffect } from "react";
import { Play, X, ShieldAlert, CheckCircle, Clock, AlertTriangle, Cpu } from "lucide-react";

export default function RemediationPanel({ investigationId, remediationData, onRemediationUpdated }) {
  const [remediation, setRemediation] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchRemediationStatus = async () => {
    try {
      const remedId = `remed_${investigationId}`;
      const res = await fetch(`http://localhost:8000/api/v1/remediations/${remedId}`);
      if (!res.ok) {
        throw new Error("No database remediation action created for this run yet.");
      }
      const data = await res.json();
      setRemediation(data);
      setError(null);
    } catch (err) {
      // If db record doesn't exist, we can fallback to the mock/spec details passed from App
      if (remediationData) {
        setRemediation({
          id: `remed_${investigationId}`,
          investigation_id: investigationId,
          status: "PENDING_APPROVAL",
          action_name: remediationData.action || "restart",
          target_resource: remediationData.resource || "auth-service",
          params: remediationData.params || {},
        });
      } else {
        setRemediation(null);
      }
    }
  };

  useEffect(() => {
    if (investigationId) {
      fetchRemediationStatus();
    }
  }, [investigationId, remediationData]);

  // Poll remediation status if executing to update completed/failed state
  useEffect(() => {
    if (!remediation || remediation.status !== "EXECUTING") return;

    const interval = setInterval(async () => {
      try {
        const res = await fetch(`http://localhost:8000/api/v1/remediations/${remediation.id}`);
        if (res.ok) {
          const data = await res.json();
          setRemediation(data);
          if (onRemediationUpdated) {
            onRemediationUpdated(data);
          }
          if (data.status === "COMPLETED" || data.status === "FAILED") {
            clearInterval(interval);
          }
        }
      } catch (err) {
        console.error("Failed to poll remediation action:", err);
      }
    }, 3000);

    return () => clearInterval(interval);
  }, [remediation]);

  const handleAction = async (decision) => {
    setLoading(true);
    setError(null);
    try {
      const remedId = remediation.id;
      const res = await fetch(`http://localhost:8000/api/v1/remediations/${remedId}/${decision}`, {
        method: "POST",
      });
      if (!res.ok) {
        const errJson = await res.json();
        throw new Error(errJson.detail || `Failed to ${decision} remediation.`);
      }
      // Refresh status immediately
      await fetchRemediationStatus();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (!remediation) {
    return (
      <div className="p-5 text-center text-gray-500 bg-slate-900/20 border border-white/5 rounded-2xl backdrop-blur-md">
        No remediation suggestions generated for this investigation.
      </div>
    );
  }

  const getStatusBadge = (status) => {
    switch (status) {
      case "PENDING_APPROVAL":
        return (
          <span className="flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/20">
            <Clock className="w-3.5 h-3.5" />
            Pending Approval
          </span>
        );
      case "APPROVED":
      case "EXECUTING":
        return (
          <span className="flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-blue-500/10 text-blue-400 border border-blue-500/20 animate-pulse">
            <Cpu className="w-3.5 h-3.5 animate-spin" />
            Executing...
          </span>
        );
      case "COMPLETED":
        return (
          <span className="flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            <CheckCircle className="w-3.5 h-3.5" />
            Completed
          </span>
        );
      case "REJECTED":
        return (
          <span className="flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-red-500/10 text-red-400 border border-red-500/20">
            <X className="w-3.5 h-3.5" />
            Rejected
          </span>
        );
      case "FAILED":
        return (
          <span className="flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-red-500/10 text-red-400 border border-red-500/20">
            <ShieldAlert className="w-3.5 h-3.5" />
            Failed / Cooldown-Blocked
          </span>
        );
      default:
        return (
          <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-gray-500/10 text-gray-400">
            {status}
          </span>
        );
    }
  };

  return (
    <div className="bg-slate-900/40 border border-white/5 rounded-2xl p-5 flex flex-col gap-4 backdrop-blur-md relative overflow-hidden">
      {/* Background radial highlight */}
      <div className="absolute -right-20 -top-20 w-40 h-40 bg-purple-500/5 blur-3xl pointer-events-none rounded-full" />

      <div className="flex items-center justify-between gap-4">
        <h3 className="font-display font-semibold text-lg text-white flex items-center gap-2">
          <ShieldAlert className="w-5 h-5 text-amber-400" />
          Remediation Advisor
        </h3>
        {getStatusBadge(remediation.status)}
      </div>

      <div className="bg-slate-950/30 border border-white/5 rounded-xl p-4 flex flex-col gap-3 font-sans">
        <div className="grid grid-cols-2 gap-y-2.5 gap-x-4 text-sm">
          <span className="text-gray-500">Action:</span>
          <span className="text-white font-mono uppercase text-xs">{remediation.action_name}</span>
          
          <span className="text-gray-500">Target Resource:</span>
          <span className="text-teal-400 font-mono text-xs">{remediation.target_resource}</span>

          <span className="text-gray-500">Parameters:</span>
          <span className="text-gray-300 font-mono text-xs">
            {remediation.params 
              ? (typeof remediation.params === 'string' ? remediation.params : JSON.stringify(remediation.params))
              : "{}"
            }
          </span>
        </div>
      </div>

      {remediation.status === "PENDING_APPROVAL" && (
        <div className="flex flex-col gap-3">
          {/* Safety Warning */}
          <div className="flex gap-2.5 p-3 rounded-xl bg-amber-500/5 border border-amber-500/15 text-xs text-amber-300">
            <AlertTriangle className="w-4 h-4 shrink-0 text-amber-400" />
            <div>
              <p className="font-semibold mb-0.5">Human-in-the-Loop Safety Gate</p>
              <p className="opacity-80">Approving this will invoke execution on the resource. A 5-minute safety cooldown is automatically enforced for identical resources.</p>
            </div>
          </div>

          {error && (
            <div className="p-3 bg-red-500/10 border border-red-500/20 text-xs text-red-400 rounded-xl">
              {error}
            </div>
          )}

          <div className="flex items-center gap-3 mt-1">
            <button
              onClick={() => handleAction("approve")}
              disabled={loading}
              className="flex-1 btn-success py-2.5 font-display text-sm font-semibold flex items-center justify-center gap-2 disabled:opacity-50"
            >
              <Play className="w-4 h-4 fill-current" />
              Approve Action
            </button>
            <button
              onClick={() => handleAction("reject")}
              disabled={loading}
              className="flex-1 btn-danger py-2.5 font-display text-sm font-semibold flex items-center justify-center gap-2 disabled:opacity-50"
            >
              <X className="w-4 h-4" />
              Reject Action
            </button>
          </div>
        </div>
      )}

      {remediation.status === "COMPLETED" && (
        <div className="p-3 bg-emerald-500/10 border border-emerald-500/15 text-xs text-emerald-400 rounded-xl flex gap-2">
          <CheckCircle className="w-4 h-4 shrink-0 text-emerald-400" />
          <div>
            <p className="font-semibold mb-0.5">Execution Succeeded</p>
            <p className="opacity-80">Remediation completed successfully and target resource passed post-execution health validation check.</p>
          </div>
        </div>
      )}

      {remediation.status === "FAILED" && (
        <div className="p-3 bg-red-500/10 border border-red-500/15 text-xs text-red-400 rounded-xl flex gap-2">
          <ShieldAlert className="w-4 h-4 shrink-0 text-red-400" />
          <div>
            <p className="font-semibold mb-0.5">Remediation Failed</p>
            <p className="opacity-80">Action was aborted, failed to execute, did not pass health validation, or was blocked by active cooldown rules.</p>
          </div>
        </div>
      )}

      {remediation.status === "EXECUTING" && (
        <div className="flex items-center justify-center py-4 text-xs text-blue-400 gap-2">
          <div className="w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
          Running remediation playbook tasks...
        </div>
      )}
    </div>
  );
}

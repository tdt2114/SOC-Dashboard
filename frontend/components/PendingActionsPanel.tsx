"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

import { PendingActionItem } from "@/lib/types";

function formatDate(value: string | null) {
  if (!value) {
    return "—";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return new Intl.DateTimeFormat("en-GB", {
    dateStyle: "medium",
    timeStyle: "short",
    timeZone: "UTC"
  }).format(date);
}

export function PendingActionsPanel({
  actions,
  canApprove
}: {
  actions: PendingActionItem[];
  canApprove: boolean;
}) {
  const router = useRouter();
  const [busyToken, setBusyToken] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function decide(token: string, decision: "approve" | "reject") {
    setError(null);
    setMessage(null);
    setBusyToken(token);
    try {
      const init: RequestInit = { method: "POST" };
      if (decision === "reject") {
        init.headers = { "Content-Type": "application/json" };
        init.body = JSON.stringify({ reason: "Rejected from dashboard" });
      }
      const response = await fetch(`/api/actions/${encodeURIComponent(token)}/${decision}`, init);
      const payload = (await response.json()) as { detail?: string; execution_status?: string };
      if (!response.ok) {
        throw new Error(payload.detail || `Unable to ${decision} action`);
      }
      setMessage(
        decision === "approve"
          ? `Action approved (execution: ${payload.execution_status ?? "unknown"}).`
          : "Action rejected."
      );
      router.refresh();
    } catch (decisionError) {
      setError(decisionError instanceof Error ? decisionError.message : `Unable to ${decision} action`);
    } finally {
      setBusyToken(null);
    }
  }

  if (actions.length === 0) {
    return <p className="inline-empty">No response actions requested for this case.</p>;
  }

  return (
    <div className="pending-actions stack">
      {actions.map((action) => {
        const isPending = action.status === "pending";
        const isBusy = busyToken === action.token;
        return (
          <article key={action.id} className="note-card">
            <div className="note-meta">
              <strong>{action.action_type}</strong>
              <span>agent {action.target_agent_id}</span>
              <span className={`case-pill case-status-${action.status}`}>{action.status}</span>
              <span>requested by {action.requested_by}</span>
              <span>{formatDate(action.created_at)}</span>
            </div>
            <p>{action.reason || "No reason provided."}</p>
            {action.decided_by_username ? (
              <p className="muted">
                Decided by {action.decided_by_username} at {formatDate(action.decided_at)}
                {action.execution_status ? ` · execution: ${action.execution_status}` : ""}
              </p>
            ) : null}
            {action.execution_detail ? <p className="muted">{action.execution_detail}</p> : null}
            {isPending && canApprove ? (
              <div className="alert-detail-actions">
                <button type="button" disabled={isBusy} onClick={() => decide(action.token, "approve")}>
                  {isBusy ? "Working..." : "Approve"}
                </button>
                <button
                  type="button"
                  className="link-button danger-link"
                  disabled={isBusy}
                  onClick={() => decide(action.token, "reject")}
                >
                  Reject
                </button>
              </div>
            ) : null}
            {isPending && !canApprove ? (
              <p className="muted">Awaiting admin approval.</p>
            ) : null}
          </article>
        );
      })}

      {error ? <p className="form-error">{error}</p> : null}
      {message ? <p className="form-success">{message}</p> : null}
    </div>
  );
}

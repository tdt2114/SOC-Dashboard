"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";

import { CaseDetail } from "@/lib/types";

export function CaseDetailActions({ item }: { item: CaseDetail }) {
  const router = useRouter();
  const [statusValue, setStatusValue] = useState(item.status);
  const [severity, setSeverity] = useState(item.severity);
  const [comment, setComment] = useState("");
  const [isUpdating, setIsUpdating] = useState(false);
  const [isCommenting, setIsCommenting] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleUpdate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setMessage(null);
    setIsUpdating(true);
    try {
      const response = await fetch(`/api/cases/${item.id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: statusValue, severity })
      });
      const payload = (await response.json()) as { detail?: string };
      if (!response.ok) {
        throw new Error(payload.detail || "Unable to update case");
      }
      setMessage("Case updated.");
      router.refresh();
    } catch (updateError) {
      setError(updateError instanceof Error ? updateError.message : "Unable to update case");
    } finally {
      setIsUpdating(false);
    }
  }

  async function handleComment(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setMessage(null);
    setIsCommenting(true);
    try {
      const response = await fetch(`/api/cases/${item.id}/comments`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ body: comment })
      });
      const payload = (await response.json()) as { detail?: string };
      if (!response.ok) {
        throw new Error(payload.detail || "Unable to add comment");
      }
      setComment("");
      setMessage("Comment added.");
      router.refresh();
    } catch (commentError) {
      setError(commentError instanceof Error ? commentError.message : "Unable to add comment");
    } finally {
      setIsCommenting(false);
    }
  }

  async function handleRemoveAlert(alertId: string) {
    setError(null);
    setMessage(null);
    try {
      const response = await fetch(`/api/cases/${item.id}/alerts/${encodeURIComponent(alertId)}`, {
        method: "DELETE"
      });
      const payload = (await response.json()) as { detail?: string };
      if (!response.ok) {
        throw new Error(payload.detail || "Unable to remove alert");
      }
      setMessage("Alert removed from case.");
      router.refresh();
    } catch (removeError) {
      setError(removeError instanceof Error ? removeError.message : "Unable to remove alert");
    }
  }

  return (
    <div className="case-detail-actions">
      <form className="case-inline-form" onSubmit={handleUpdate}>
        <label>
          <span>Status</span>
          <select value={statusValue} onChange={(event) => setStatusValue(event.target.value)}>
            <option value="open">Open</option>
            <option value="investigating">Investigating</option>
            <option value="closed">Closed</option>
          </select>
        </label>
        <label>
          <span>Severity</span>
          <select value={severity} onChange={(event) => setSeverity(event.target.value)}>
            <option value="low">Low</option>
            <option value="medium">Medium</option>
            <option value="high">High</option>
            <option value="critical">Critical</option>
          </select>
        </label>
        <button type="submit" disabled={isUpdating}>
          {isUpdating ? "Updating..." : "Update Case"}
        </button>
      </form>

      <form className="stack-form" onSubmit={handleComment}>
        <label>
          <span>Add Comment</span>
          <textarea
            className="note-textarea"
            value={comment}
            onChange={(event) => setComment(event.target.value)}
            maxLength={4000}
            required
          />
        </label>
        <button type="submit" disabled={isCommenting}>
          {isCommenting ? "Saving..." : "Add Comment"}
        </button>
      </form>

      {error ? <p className="form-error">{error}</p> : null}
      {message ? <p className="form-success">{message}</p> : null}

      <div className="case-remove-alerts" data-case-id={item.id}>
        {item.alerts.map((alert) => (
          <button key={alert.id} type="button" className="link-button danger-link" onClick={() => handleRemoveAlert(alert.alert_id)}>
            Remove alert {alert.alert_id}
          </button>
        ))}
      </div>
    </div>
  );
}

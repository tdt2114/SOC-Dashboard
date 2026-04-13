"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";

import { AlertWorkflowResponse, AuthUser } from "@/lib/types";

function formatDate(value: string | null) {
  if (!value) {
    return "N/A";
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

export function AlertWorkflowPanel({
  alertId,
  currentUser,
  initialWorkflow
}: {
  alertId: string;
  currentUser: AuthUser;
  initialWorkflow: AlertWorkflowResponse;
}) {
  const router = useRouter();
  const canManageWorkflow =
    currentUser.is_superuser || currentUser.roles.some((role) => role === "admin" || role === "analyst");
  const [workflow, setWorkflow] = useState(initialWorkflow);
  const [assignedUserId, setAssignedUserId] = useState(
    initialWorkflow.assignee.user_id ? String(initialWorkflow.assignee.user_id) : ""
  );
  const [noteBody, setNoteBody] = useState("");
  const [assignError, setAssignError] = useState<string | null>(null);
  const [noteError, setNoteError] = useState<string | null>(null);
  const [assignMessage, setAssignMessage] = useState<string | null>(null);
  const [noteMessage, setNoteMessage] = useState<string | null>(null);
  const [isAssigning, setIsAssigning] = useState(false);
  const [isSavingNote, setIsSavingNote] = useState(false);

  async function handleAssign(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setAssignError(null);
    setAssignMessage(null);
    setIsAssigning(true);

    try {
      const response = await fetch(`/api/alerts/${encodeURIComponent(alertId)}/workflow/assignment`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          assigned_user_id: assignedUserId ? Number(assignedUserId) : null
        })
      });
      const payload = (await response.json()) as AlertWorkflowResponse | { detail?: string };
      if (!response.ok) {
        throw new Error("detail" in payload ? payload.detail || "Unable to assign alert" : "Unable to assign alert");
      }

      const nextWorkflow = payload as AlertWorkflowResponse;
      setWorkflow(nextWorkflow);
      setAssignedUserId(nextWorkflow.assignee.user_id ? String(nextWorkflow.assignee.user_id) : "");
      setAssignMessage(nextWorkflow.assignee.user_id ? "Assignee updated." : "Alert unassigned.");
      router.refresh();
    } catch (error) {
      setAssignError(error instanceof Error ? error.message : "Unable to assign alert");
    } finally {
      setIsAssigning(false);
    }
  }

  async function handleAddNote(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setNoteError(null);
    setNoteMessage(null);
    setIsSavingNote(true);

    try {
      const response = await fetch(`/api/alerts/${encodeURIComponent(alertId)}/workflow/notes`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ body: noteBody })
      });
      const payload = (await response.json()) as AlertWorkflowResponse | { detail?: string };
      if (!response.ok) {
        throw new Error("detail" in payload ? payload.detail || "Unable to add note" : "Unable to add note");
      }

      const nextWorkflow = payload as AlertWorkflowResponse;
      setWorkflow(nextWorkflow);
      setNoteBody("");
      setNoteMessage("Note added.");
      router.refresh();
    } catch (error) {
      setNoteError(error instanceof Error ? error.message : "Unable to add note");
    } finally {
      setIsSavingNote(false);
    }
  }

  return (
    <section className="subpanel">
      <div className="panel-header">
        <div>
          <h3>Analyst Workflow</h3>
          <p>Assign ownership and capture investigation notes directly on the alert.</p>
        </div>
      </div>

      <div className="workflow-grid">
        <div className="workflow-card">
          <div className="workflow-card-header">
            <h4>Assignee</h4>
            <p>Route this alert to the analyst who will own the investigation.</p>
          </div>

          <div className="workflow-assignee-summary">
            <span className="summary-label">Current Assignee</span>
            <strong className="summary-value workflow-assignee-name">
              {workflow.assignee.full_name || workflow.assignee.username || "Unassigned"}
            </strong>
            <span className="workflow-assignee-meta">
              {workflow.assignee.username ? `@${workflow.assignee.username}` : "No analyst currently owns this alert"}
            </span>
            {workflow.assignee.updated_at ? (
              <span className="workflow-assignee-meta">Updated {formatDate(workflow.assignee.updated_at)}</span>
            ) : null}
          </div>

          <form className="stack-form" onSubmit={handleAssign}>
            <label>
              <span>Assign To</span>
              <select
                value={assignedUserId}
                onChange={(event) => setAssignedUserId(event.target.value)}
                disabled={!canManageWorkflow}
              >
                <option value="">Unassigned</option>
                {workflow.assignee_options.map((option) => (
                  <option key={option.id} value={option.id}>
                    {option.full_name ? `${option.full_name} (@${option.username})` : option.username}
                  </option>
                ))}
              </select>
            </label>
            {!canManageWorkflow ? (
              <p className="inline-empty">Analyst or admin access is required to change alert ownership.</p>
            ) : null}
            {assignError ? <p className="form-error">{assignError}</p> : null}
            {assignMessage ? <p className="form-success">{assignMessage}</p> : null}
            <button type="submit" disabled={isAssigning || !canManageWorkflow}>
              {isAssigning ? "Saving..." : "Save Assignee"}
            </button>
          </form>
        </div>

        <div className="workflow-card">
          <div className="workflow-card-header">
            <h4>Investigation Notes</h4>
            <p>Capture analyst context, findings, and next steps for this alert.</p>
          </div>

          <form className="stack-form" onSubmit={handleAddNote}>
            <label>
              <span>Add Note</span>
              <textarea
                className="note-textarea"
                value={noteBody}
                onChange={(event) => setNoteBody(event.target.value)}
                placeholder="Write a concise investigation note..."
                minLength={1}
                maxLength={4000}
                disabled={!canManageWorkflow}
                required
              />
            </label>
            {!canManageWorkflow ? (
              <p className="inline-empty">Analyst or admin access is required to add investigation notes.</p>
            ) : null}
            {noteError ? <p className="form-error">{noteError}</p> : null}
            {noteMessage ? <p className="form-success">{noteMessage}</p> : null}
            <button type="submit" disabled={isSavingNote || !canManageWorkflow}>
              {isSavingNote ? "Saving..." : "Add Note"}
            </button>
          </form>

          <div className="note-list">
            <div className="workflow-card-header">
              <h4>Recent Notes</h4>
              <p>{workflow.notes.length} notes logged on this alert.</p>
            </div>
            {workflow.notes.length === 0 ? (
              <p className="inline-empty">No notes yet. Add the first analyst note for this alert.</p>
            ) : (
              workflow.notes.map((note) => (
                <article key={note.id} className="note-card">
                  <div className="note-meta">
                    <strong>{note.author_full_name || note.author_username}</strong>
                    <span>@{note.author_username}</span>
                    <span>{formatDate(note.created_at)}</span>
                    {note.author_user_id === currentUser.id ? <span className="badge severity-low">you</span> : null}
                  </div>
                  <p>{note.body}</p>
                </article>
              ))
            )}
          </div>
        </div>
      </div>
    </section>
  );
}

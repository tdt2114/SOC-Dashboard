"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";

export function CaseCreateForm({ alertId }: { alertId?: string }) {
  const router = useRouter();
  const [title, setTitle] = useState(alertId ? `Investigate alert ${alertId}` : "");
  const [description, setDescription] = useState("");
  const [severity, setSeverity] = useState("medium");
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setIsSaving(true);
    try {
      const response = await fetch("/api/cases", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          title,
          description: description || null,
          severity,
          status: "open",
          alert_id: alertId || null
        })
      });
      const payload = (await response.json()) as { id?: number; detail?: string };
      if (!response.ok || !payload.id) {
        throw new Error(payload.detail || "Unable to create case");
      }
      router.push(`/cases/${payload.id}`);
      router.refresh();
    } catch (saveError) {
      setError(saveError instanceof Error ? saveError.message : "Unable to create case");
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <form className="case-form" onSubmit={handleSubmit}>
      <label>
        <span>Title</span>
        <input value={title} onChange={(event) => setTitle(event.target.value)} maxLength={255} required />
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
      <label className="case-form-wide">
        <span>Description</span>
        <textarea
          className="note-textarea"
          value={description}
          onChange={(event) => setDescription(event.target.value)}
          placeholder="Initial triage context..."
        />
      </label>
      {error ? <p className="form-error case-form-wide">{error}</p> : null}
      <button type="submit" disabled={isSaving}>
        {isSaving ? "Creating..." : alertId ? "Create Case With Alert" : "Create Case"}
      </button>
    </form>
  );
}

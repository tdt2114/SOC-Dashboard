"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";

import { SavedSearchListResponse } from "@/lib/types";

const FILTER_LABELS: Record<string, string> = {
  q: "Search",
  severity: "Severity",
  agent_name: "Agent",
  agent_id: "Agent ID",
  rule_id: "Rule ID",
  time_range: "Time Range"
};

function buildHref(filters: Record<string, string>) {
  const query = new URLSearchParams();
  for (const [key, value] of Object.entries(filters)) {
    if (value) {
      query.set(key, value);
    }
  }
  const suffix = query.toString();
  return suffix ? `/alerts?${suffix}` : "/alerts";
}

function filterSummary(filters: Record<string, string>) {
  const items = Object.entries(filters).filter(([, value]) => value);
  if (items.length === 0) {
    return "No filters";
  }
  return items.map(([key, value]) => `${FILTER_LABELS[key] || key}: ${value}`).join(" | ");
}

export function SavedSearchPanel({
  initialData,
  currentFilters
}: {
  initialData: SavedSearchListResponse;
  currentFilters: Record<string, string>;
}) {
  const router = useRouter();
  const [name, setName] = useState("");
  const [isSaving, setIsSaving] = useState(false);
  const [deletingId, setDeletingId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  async function handleSave(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setMessage(null);
    setIsSaving(true);

    try {
      const response = await fetch("/api/saved-searches", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, filters: currentFilters })
      });
      const payload = (await response.json()) as { detail?: string };
      if (!response.ok) {
        throw new Error(payload.detail || "Unable to save search");
      }
      setName("");
      setMessage("Saved search created.");
      router.refresh();
    } catch (saveError) {
      setError(saveError instanceof Error ? saveError.message : "Unable to save search");
    } finally {
      setIsSaving(false);
    }
  }

  async function handleDelete(savedSearchId: number) {
    setError(null);
    setMessage(null);
    setDeletingId(savedSearchId);

    try {
      const response = await fetch(`/api/saved-searches/${savedSearchId}`, {
        method: "DELETE"
      });
      if (!response.ok) {
        const payload = (await response.json()) as { detail?: string };
        throw new Error(payload.detail || "Unable to delete saved search");
      }
      setMessage("Saved search deleted.");
      router.refresh();
    } catch (deleteError) {
      setError(deleteError instanceof Error ? deleteError.message : "Unable to delete saved search");
    } finally {
      setDeletingId(null);
    }
  }

  return (
    <section className="panel saved-search-panel">
      <div className="panel-header">
        <div>
          <h3>Saved Searches</h3>
          <p>Keep frequently used alert filters ready for analyst triage.</p>
        </div>
      </div>

      <form className="saved-search-form" onSubmit={handleSave}>
        <label>
          <span>Search Name</span>
          <input
            type="text"
            value={name}
            onChange={(event) => setName(event.target.value)}
            placeholder="High severity from SOC-Server-Dev"
            maxLength={100}
            required
          />
        </label>
        <button type="submit" disabled={isSaving}>
          {isSaving ? "Saving..." : "Save Current Filters"}
        </button>
      </form>

      <p className="saved-search-current">{filterSummary(currentFilters)}</p>
      {error ? <p className="form-error">{error}</p> : null}
      {message ? <p className="form-success">{message}</p> : null}

      {initialData.items.length === 0 ? (
        <p className="inline-empty">No saved searches yet.</p>
      ) : (
        <div className="saved-search-list">
          {initialData.items.map((item) => (
            <article key={item.id} className="saved-search-item">
              <div>
                <strong>{item.name}</strong>
                <p>{filterSummary(item.filters)}</p>
              </div>
              <div className="saved-search-actions">
                <Link href={buildHref(item.filters)} className="text-link">
                  Apply
                </Link>
                <button
                  type="button"
                  className="link-button danger-link"
                  onClick={() => handleDelete(item.id)}
                  disabled={deletingId === item.id}
                >
                  {deletingId === item.id ? "Deleting..." : "Delete"}
                </button>
              </div>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}

"use client";

import { useMemo, useState } from "react";
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
  const [selectedId, setSelectedId] = useState(initialData.items[0]?.id ? String(initialData.items[0].id) : "");
  const [isSaving, setIsSaving] = useState(false);
  const [deletingId, setDeletingId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const selectedSearch = useMemo(
    () => initialData.items.find((item) => String(item.id) === selectedId) || null,
    [initialData.items, selectedId]
  );

  async function handleSave() {
    const defaultName = filterSummary(currentFilters);
    const name = window.prompt("Name this saved search", defaultName === "No filters" ? "" : defaultName);
    if (!name?.trim()) {
      return;
    }

    setError(null);
    setMessage(null);
    setIsSaving(true);

    try {
      const response = await fetch("/api/saved-searches", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: name.trim(), filters: currentFilters })
      });
      const payload = (await response.json()) as { detail?: string };
      if (!response.ok) {
        throw new Error(payload.detail || "Unable to save search");
      }
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
      if (String(savedSearchId) === selectedId) {
        setSelectedId("");
      }
      router.refresh();
    } catch (deleteError) {
      setError(deleteError instanceof Error ? deleteError.message : "Unable to delete saved search");
    } finally {
      setDeletingId(null);
    }
  }

  return (
    <div className="saved-search-inline">
      <label>
        <span>Saved search</span>
        <select
          value={selectedId}
          onChange={(event) => setSelectedId(event.target.value)}
          disabled={initialData.items.length === 0}
        >
          {initialData.items.length === 0 ? (
            <option value="">No saved searches</option>
          ) : (
            initialData.items.map((item) => (
              <option key={item.id} value={item.id}>
                {item.name}
              </option>
            ))
          )}
        </select>
      </label>
      <button
        type="button"
        className="secondary-button"
        onClick={() => {
          if (selectedSearch) {
            router.push(buildHref(selectedSearch.filters));
          }
        }}
        disabled={!selectedSearch}
      >
        Apply
      </button>
      <button type="button" className="secondary-button" onClick={handleSave} disabled={isSaving}>
        {isSaving ? "Saving..." : "Save current"}
      </button>
      <button
        type="button"
        className="secondary-button danger-button"
        onClick={() => {
          if (selectedSearch) {
            void handleDelete(selectedSearch.id);
          }
        }}
        disabled={!selectedSearch || deletingId === selectedSearch.id}
      >
        {selectedSearch && deletingId === selectedSearch.id ? "Deleting..." : "Delete"}
      </button>
      {error ? <p className="form-error">{error}</p> : null}
      {message ? <p className="form-success">{message}</p> : null}
    </div>
  );
}

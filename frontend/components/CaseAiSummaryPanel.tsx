"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

import { AiAnalysis } from "@/lib/types";

export function CaseAiSummaryPanel({
  caseId,
  initial
}: {
  caseId: number;
  initial: AiAnalysis | null;
}) {
  const router = useRouter();
  const [summary, setSummary] = useState<AiAnalysis | null>(initial);
  const [isRunning, setIsRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function run() {
    setError(null);
    setIsRunning(true);
    try {
      const response = await fetch(`/api/cases/${caseId}/ai-summary`, { method: "POST" });
      const payload = (await response.json()) as AiAnalysis & { detail?: string };
      if (!response.ok) {
        throw new Error(payload.detail || "Unable to run AI summary");
      }
      setSummary(payload);
      router.refresh();
    } catch (runError) {
      setError(runError instanceof Error ? runError.message : "Unable to run AI summary");
    } finally {
      setIsRunning(false);
    }
  }

  return (
    <div className="stack">
      <div className="alert-detail-actions">
        <button type="button" onClick={run} disabled={isRunning}>
          {isRunning ? "Summarizing..." : summary ? "Re-summarize" : "Run AI summary"}
        </button>
        {summary ? <span className="case-pill">model: {summary.model}</span> : null}
      </div>
      {error ? <p className="form-error">{error}</p> : null}
      {summary ? (
        <div className="note-card stack">
          <p>{summary.summary}</p>
          {summary.attacker_intent ? (
            <p className="muted"><strong>Assessment:</strong> {summary.attacker_intent}</p>
          ) : null}
          <p className="muted">Advisory only — generated from linked alerts and comments.</p>
        </div>
      ) : (
        <p className="inline-empty">No AI summary yet.</p>
      )}
    </div>
  );
}

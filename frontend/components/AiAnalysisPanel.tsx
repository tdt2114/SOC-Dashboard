"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

import { AiAnalysis } from "@/lib/types";

export function AiAnalysisPanel({
  alertId,
  initial,
  canRun
}: {
  alertId: string;
  initial: AiAnalysis | null;
  canRun: boolean;
}) {
  const router = useRouter();
  const [analysis, setAnalysis] = useState<AiAnalysis | null>(initial);
  const [isRunning, setIsRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function run() {
    setError(null);
    setIsRunning(true);
    try {
      const response = await fetch(`/api/alerts/${encodeURIComponent(alertId)}/ai-analyze`, {
        method: "POST"
      });
      const payload = (await response.json()) as AiAnalysis & { detail?: string };
      if (!response.ok) {
        throw new Error(payload.detail || "Unable to run AI analysis");
      }
      setAnalysis(payload);
      router.refresh();
    } catch (runError) {
      setError(runError instanceof Error ? runError.message : "Unable to run AI analysis");
    } finally {
      setIsRunning(false);
    }
  }

  return (
    <div className="stack">
      <div className="alert-detail-actions">
        {canRun ? (
          <button type="button" onClick={run} disabled={isRunning}>
            {isRunning ? "Analyzing..." : analysis ? "Re-analyze" : "Run AI analysis"}
          </button>
        ) : null}
        {analysis ? <span className="case-pill">model: {analysis.model}</span> : null}
      </div>

      {error ? <p className="form-error">{error}</p> : null}

      {analysis ? (
        <div className="note-card stack">
          <p>{analysis.summary}</p>
          {analysis.attacker_intent ? (
            <p className="muted"><strong>Intent:</strong> {analysis.attacker_intent}</p>
          ) : null}
          <div className="alert-detail-actions">
            {analysis.recommended_action ? (
              <span className="case-pill">action: {analysis.recommended_action}</span>
            ) : null}
            {analysis.should_block !== null ? (
              <span className={`case-pill case-severity-${analysis.should_block ? "high" : "low"}`}>
                {analysis.should_block ? "block" : "no block"}
              </span>
            ) : null}
            {analysis.confidence !== null ? (
              <span className="case-pill">confidence: {analysis.confidence}%</span>
            ) : null}
            {analysis.mitre && analysis.mitre.length > 0 ? (
              <span className="case-pill">MITRE: {analysis.mitre.join(", ")}</span>
            ) : null}
          </div>
          <p className="muted">Advisory only — a human still approves any response action.</p>
        </div>
      ) : (
        <p className="inline-empty">No AI analysis yet.</p>
      )}
    </div>
  );
}

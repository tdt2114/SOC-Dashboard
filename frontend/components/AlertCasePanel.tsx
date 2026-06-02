"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";

import { CaseCreateForm } from "@/components/CaseCreateForm";
import { CaseListResponse } from "@/lib/types";

export function AlertCasePanel({
  alertId,
  cases
}: {
  alertId: string;
  cases: CaseListResponse;
}) {
  const router = useRouter();
  const [caseId, setCaseId] = useState(cases.items[0] ? String(cases.items[0].id) : "");
  const [isAdding, setIsAdding] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  async function handleAdd(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!caseId) {
      setError("Select a case first");
      return;
    }
    setError(null);
    setMessage(null);
    setIsAdding(true);
    try {
      const response = await fetch(`/api/cases/${caseId}/alerts`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ alert_id: alertId })
      });
      const payload = (await response.json()) as { detail?: string };
      if (!response.ok) {
        throw new Error(payload.detail || "Unable to add alert to case");
      }
      setMessage("Alert added to case.");
      router.refresh();
    } catch (addError) {
      setError(addError instanceof Error ? addError.message : "Unable to add alert to case");
    } finally {
      setIsAdding(false);
    }
  }

  return (
    <section className="subpanel">
      <div className="panel-header">
        <div>
          <h3>Cases</h3>
          <p>Attach this alert to an investigation case, or create a new case from it.</p>
        </div>
        <Link href="/cases" className="text-link">
          Open cases
        </Link>
      </div>

      <div className="case-workflow-grid">
        <div className="workflow-card">
          <div className="workflow-card-header">
            <h4>Add To Existing Case</h4>
            <p>{cases.total} cases available.</p>
          </div>
          {cases.items.length === 0 ? (
            <p className="inline-empty">No cases exist yet.</p>
          ) : (
            <form className="stack-form" onSubmit={handleAdd}>
              <label>
                <span>Case</span>
                <select value={caseId} onChange={(event) => setCaseId(event.target.value)}>
                  {cases.items.map((item) => (
                    <option key={item.id} value={item.id}>
                      #{item.id} {item.title}
                    </option>
                  ))}
                </select>
              </label>
              {error ? <p className="form-error">{error}</p> : null}
              {message ? <p className="form-success">{message}</p> : null}
              <button type="submit" disabled={isAdding}>
                {isAdding ? "Adding..." : "Add Alert To Case"}
              </button>
            </form>
          )}
        </div>

        <div className="workflow-card">
          <div className="workflow-card-header">
            <h4>Create New Case</h4>
            <p>Start a new investigation with this alert already linked.</p>
          </div>
          <CaseCreateForm alertId={alertId} />
        </div>
      </div>
    </section>
  );
}

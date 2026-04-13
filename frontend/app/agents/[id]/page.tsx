import Link from "next/link";
import { redirect } from "next/navigation";

import { AppShell } from "@/components/AppShell";
import { EmptyState } from "@/components/EmptyState";
import { ErrorState } from "@/components/ErrorState";
import { KeyValueGrid } from "@/components/KeyValueGrid";
import { SeverityBadge } from "@/components/SeverityBadge";
import { getCurrentUserFromCookies } from "@/lib/auth";
import { getAgent } from "@/lib/api";

export default async function AgentDetailPage({
  params
}: {
  params: { id: string };
}) {
  const currentUser = await getCurrentUserFromCookies();
  if (!currentUser) {
    redirect("/login");
  }

  try {
    const result = await getAgent(params.id);
    const { agent, recent_alerts, monitoring_context } = result;

    return (
      <AppShell title="Agent Detail" eyebrow="Monitoring Context" currentUser={currentUser}>
        <section className="panel stack">
          <div className="panel-header">
            <div>
              <h3>{agent.name || agent.id}</h3>
              <p>Agent-centric view for host status and recent alerts tied to this monitored machine.</p>
            </div>
            <span className={`status-pill status-${(agent.status || "unknown").toLowerCase()}`}>
              {agent.status || "unknown"}
            </span>
          </div>

          <KeyValueGrid
            items={[
              { label: "Agent ID", value: agent.id },
              { label: "Agent Name", value: agent.name },
              { label: "Status", value: agent.status },
              { label: "Last Keepalive", value: agent.last_keepalive },
              { label: "Platform / OS", value: agent.platform },
              { label: "High or Critical Alerts (24h)", value: monitoring_context.high_or_critical_alerts_24h }
            ]}
          />
        </section>

        <section className="panel">
          <div className="panel-header">
            <div>
              <h3>Monitoring Context</h3>
              <p>Quick view of the host state and alert volume in the last 24 hours.</p>
            </div>
            <Link href="/agents" className="text-link">
              Back to agents
            </Link>
          </div>

          <div className="summary-grid">
            <div className="summary-card">
              <span className="summary-label">Alerts in last 24h</span>
              <strong className="summary-value">{monitoring_context.total_alerts_24h}</strong>
            </div>
            <div className="summary-card">
              <span className="summary-label">High or Critical</span>
              <strong className="summary-value">{monitoring_context.high_or_critical_alerts_24h}</strong>
            </div>
            <div className="summary-card">
              <span className="summary-label">Current Status</span>
              <strong className="summary-value">{monitoring_context.status || "unknown"}</strong>
            </div>
          </div>
        </section>

        <section className="panel">
          <div className="panel-header">
            <div>
              <h3>Recent Alerts For This Agent</h3>
              <p>Use this table to jump from the host view into the exact alert event.</p>
            </div>
          </div>

          {recent_alerts.length === 0 ? (
            <EmptyState
              title="No alerts are currently tied to this agent"
              description="This host is enrolled, but no recent alerts matched the current monitoring window."
            />
          ) : (
            <div className="table-scroll">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Timestamp</th>
                    <th>Severity</th>
                    <th>Rule ID</th>
                    <th>Description</th>
                  </tr>
                </thead>
                <tbody>
                  {recent_alerts.map((alert) => (
                    <tr key={alert.id}>
                      <td>
                        <Link href={`/alerts/${encodeURIComponent(alert.id)}`} className="table-row-link">
                          {alert.timestamp || "N/A"}
                        </Link>
                      </td>
                      <td>
                        <Link href={`/alerts/${encodeURIComponent(alert.id)}`} className="table-row-link">
                          <SeverityBadge value={alert.severity_label} />
                        </Link>
                      </td>
                      <td>
                        <Link href={`/alerts/${encodeURIComponent(alert.id)}`} className="table-row-link">
                          {alert.rule.id || "N/A"}
                        </Link>
                      </td>
                      <td>
                        <Link href={`/alerts/${encodeURIComponent(alert.id)}`} className="table-row-link">
                          {alert.rule.description || "N/A"}
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      </AppShell>
    );
  } catch (error) {
    const message = error instanceof Error ? error.message : "Unknown agent detail error";
    return (
      <AppShell title="Agent Detail" eyebrow="Monitoring Context" currentUser={currentUser}>
        <section className="panel">
          <ErrorState
            title="Agent detail is unavailable"
            description={`${message}. Enable MOCK_MODE=true for standalone testing or start Repo A for live data.`}
          />
        </section>
      </AppShell>
    );
  }
}

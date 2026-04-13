import Link from "next/link";
import { redirect } from "next/navigation";

import { AlertWorkflowPanel } from "@/components/AlertWorkflowPanel";
import { AppShell } from "@/components/AppShell";
import { ErrorState } from "@/components/ErrorState";
import { KeyValueGrid } from "@/components/KeyValueGrid";
import { SeverityBadge } from "@/components/SeverityBadge";
import { getAlertWorkflowFromCookies, getCurrentUserFromCookies } from "@/lib/auth";
import { getAlert, getAlerts } from "@/lib/api";

export default async function AlertDetailPage({
  params
}: {
  params: { id: string };
}) {
  const currentUser = await getCurrentUserFromCookies();
  if (!currentUser) {
    redirect("/login");
  }
  try {
    const alert = await getAlert(params.id);
    const relatedAlerts =
      alert.agent.id || alert.agent.name
        ? await getAlerts({
            page: 1,
            page_size: 5,
            time_range: "24h",
            agent_id: alert.agent.id || undefined,
            agent_name: alert.agent.id ? undefined : alert.agent.name || undefined
          })
        : null;
    const workflow = await getAlertWorkflowFromCookies(params.id);
    const moreAlertsFromAgent = (relatedAlerts?.items || []).filter((item) => item.id !== alert.id);

    return (
      <AppShell title="Alert Detail" eyebrow="MVP Screen 2" currentUser={currentUser}>
        <section className="panel stack">
          <div className="panel-header">
            <div>
              <h3>Alert {alert.rule.id || alert.id}</h3>
              <p>Normalized view for Repo B. Raw payload remains available below.</p>
            </div>
            <SeverityBadge value={alert.severity_label} />
          </div>

          <KeyValueGrid
            items={[
              { label: "Timestamp", value: alert.timestamp },
              { label: "Rule ID", value: alert.rule.id },
              { label: "Rule Level", value: alert.rule.level },
              { label: "Description", value: alert.rule.description },
              {
                label: "Agent Name",
                value:
                  alert.agent.id && alert.agent.name ? (
                    <Link href={`/agents/${encodeURIComponent(alert.agent.id)}`} className="text-link">
                      {alert.agent.name}
                    </Link>
                  ) : (
                    alert.agent.name
                  )
              },
              {
                label: "Agent ID",
                value:
                  alert.agent.id ? (
                    <Link href={`/agents/${encodeURIComponent(alert.agent.id)}`} className="text-link">
                      {alert.agent.id}
                    </Link>
                  ) : (
                    alert.agent.id
                  )
              },
              { label: "Source IP", value: alert.source.srcip },
              { label: "Path", value: alert.file.path }
            ]}
          />

          <section className="subpanel">
            <div className="panel-header">
              <div>
                <h3>Related Agent</h3>
                <p>Move from the event view back to the monitored host that generated this alert.</p>
              </div>
              {alert.agent.id ? (
                <Link href={`/agents/${encodeURIComponent(alert.agent.id)}`} className="text-link">
                  Open agent detail
                </Link>
              ) : null}
            </div>
            <KeyValueGrid
              items={[
                { label: "Agent Name", value: alert.agent.name },
                { label: "Agent ID", value: alert.agent.id },
                { label: "Current Alert", value: alert.rule.description }
              ]}
            />
          </section>

          <section className="subpanel">
            <div className="panel-header">
              <div>
                <h3>More Alerts From This Agent</h3>
                <p>Continue investigation by reviewing other alerts tied to the same monitored host.</p>
              </div>
            </div>

            {moreAlertsFromAgent.length === 0 ? (
              <EmptyNotice message="No additional recent alerts were found for this agent." />
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
                    {moreAlertsFromAgent.map((item) => (
                      <tr key={item.id}>
                        <td>
                          <Link href={`/alerts/${encodeURIComponent(item.id)}`} className="table-row-link">
                            {item.timestamp || "N/A"}
                          </Link>
                        </td>
                        <td>
                          <Link href={`/alerts/${encodeURIComponent(item.id)}`} className="table-row-link">
                            <SeverityBadge value={item.severity_label} />
                          </Link>
                        </td>
                        <td>
                          <Link href={`/alerts/${encodeURIComponent(item.id)}`} className="table-row-link">
                            {item.rule.id || "N/A"}
                          </Link>
                        </td>
                        <td>
                          <Link href={`/alerts/${encodeURIComponent(item.id)}`} className="table-row-link">
                            {item.rule.description || "N/A"}
                          </Link>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>

          <AlertWorkflowPanel alertId={params.id} currentUser={currentUser} initialWorkflow={workflow} />

          <div className="code-panel">
            <div className="panel-header">
              <h3>Raw JSON</h3>
              <Link href="/alerts" className="text-link">
                Back to alerts
              </Link>
            </div>
            <pre>{JSON.stringify(alert.raw, null, 2)}</pre>
          </div>
        </section>
      </AppShell>
    );
  } catch (error) {
    const message = error instanceof Error ? error.message : "Unknown alert detail error";
    return (
      <AppShell title="Alert Detail" eyebrow="MVP Screen 2" currentUser={currentUser}>
        <section className="panel">
          <ErrorState
            title="Alert detail is unavailable"
            description={`${message}. Enable MOCK_MODE=true for standalone testing or start Repo A for live data.`}
          />
        </section>
      </AppShell>
    );
  }
}

function EmptyNotice({ message }: { message: string }) {
  return <p className="inline-empty">{message}</p>;
}

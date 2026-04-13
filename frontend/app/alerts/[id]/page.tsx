import Link from "next/link";
import { redirect } from "next/navigation";

import { AppShell } from "@/components/AppShell";
import { ErrorState } from "@/components/ErrorState";
import { KeyValueGrid } from "@/components/KeyValueGrid";
import { SeverityBadge } from "@/components/SeverityBadge";
import { getCurrentUserFromCookies } from "@/lib/auth";
import { getAlert } from "@/lib/api";

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
              { label: "Agent Name", value: alert.agent.name },
              { label: "Agent ID", value: alert.agent.id },
              { label: "Source IP", value: alert.source.srcip },
              { label: "Path", value: alert.file.path }
            ]}
          />

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

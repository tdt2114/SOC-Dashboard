import Link from "next/link";
import { redirect } from "next/navigation";

import { AppShell } from "@/components/AppShell";
import { CaseCreateForm } from "@/components/CaseCreateForm";
import { EmptyState } from "@/components/EmptyState";
import { ErrorState } from "@/components/ErrorState";
import { getCasesFromCookies, getCurrentUserFromCookies } from "@/lib/auth";

function formatDate(value: string) {
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

export default async function CasesPage() {
  const currentUser = await getCurrentUserFromCookies();
  if (!currentUser) {
    redirect("/login");
  }

  try {
    const cases = await getCasesFromCookies();

    return (
      <AppShell title="Cases" eyebrow="Analyst Workflow" currentUser={currentUser}>
        <section className="panel">
          <div className="panel-header">
            <div>
              <h3>Create Case</h3>
              <p>Open a new investigation case for related alerts and analyst comments.</p>
            </div>
          </div>
          <CaseCreateForm />
        </section>

        <section className="panel">
          <div className="panel-header">
            <div>
              <h3>Case List</h3>
              <p>{cases.total} active records in the case workspace.</p>
            </div>
          </div>

          {cases.items.length === 0 ? (
            <EmptyState title="No cases yet" description="Create a case from here or directly from an alert detail page." />
          ) : (
            <div className="table-scroll">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Case</th>
                    <th>Status</th>
                    <th>Severity</th>
                    <th>Owner</th>
                    <th>Alerts</th>
                    <th>Updated</th>
                  </tr>
                </thead>
                <tbody>
                  {cases.items.map((item) => (
                    <tr key={item.id}>
                      <td>
                        <Link href={`/cases/${item.id}`} className="table-link">
                          #{item.id} {item.title}
                        </Link>
                      </td>
                      <td><span className={`case-pill case-status-${item.status}`}>{item.status}</span></td>
                      <td><span className={`case-pill case-severity-${item.severity}`}>{item.severity}</span></td>
                      <td>{item.owner_full_name || item.owner_username || "Unassigned"}</td>
                      <td>{item.alert_count}</td>
                      <td>{formatDate(item.updated_at)}</td>
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
    return (
      <AppShell title="Cases" eyebrow="Analyst Workflow" currentUser={currentUser}>
        <section className="panel">
          <ErrorState
            title="Cases are unavailable"
            description={error instanceof Error ? error.message : "Unknown case loading error"}
          />
        </section>
      </AppShell>
    );
  }
}

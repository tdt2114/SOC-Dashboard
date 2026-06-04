import Link from "next/link";
import { redirect } from "next/navigation";

import { AccessDeniedState } from "@/components/AccessDeniedState";
import { AppShell } from "@/components/AppShell";
import { CaseDetailActions } from "@/components/CaseDetailActions";
import { ErrorState } from "@/components/ErrorState";
import { KeyValueGrid } from "@/components/KeyValueGrid";
import { getCaseFromCookies, getCurrentUserFromCookies } from "@/lib/auth";

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

function canUseCases(currentUser: NonNullable<Awaited<ReturnType<typeof getCurrentUserFromCookies>>>) {
  return currentUser.is_superuser || currentUser.roles.some((role) => role === "admin" || role === "analyst");
}

export default async function CaseDetailPage({ params }: { params: { id: string } }) {
  const currentUser = await getCurrentUserFromCookies();
  if (!currentUser) {
    redirect("/login");
  }

  if (!canUseCases(currentUser)) {
    return (
      <AppShell title="Case Detail" eyebrow="Analyst Workflow" currentUser={currentUser}>
        <section className="panel">
          <AccessDeniedState
            requiredRole="Analyst or admin"
            description="Case details include investigation notes and workflow actions, so they are limited to analyst and admin roles."
          />
        </section>
      </AppShell>
    );
  }

  try {
    const item = await getCaseFromCookies(Number(params.id));

    return (
      <AppShell title="Case Detail" eyebrow="Analyst Workflow" currentUser={currentUser}>
        <section className="panel stack">
          <div className="panel-header">
            <div>
              <h3>#{item.id} {item.title}</h3>
              <p>{item.description || "No description provided."}</p>
            </div>
            <div className="alert-detail-actions">
              <span className={`case-pill case-status-${item.status}`}>{item.status}</span>
              <span className={`case-pill case-severity-${item.severity}`}>{item.severity}</span>
            </div>
          </div>

          <KeyValueGrid
            items={[
              { label: "Owner", value: item.owner_full_name || item.owner_username },
              { label: "Created By", value: item.created_by_username },
              { label: "Created", value: formatDate(item.created_at) },
              { label: "Updated", value: formatDate(item.updated_at) },
              { label: "Alerts", value: item.alert_count },
              { label: "Comments", value: item.comment_count }
            ]}
          />

          <CaseDetailActions item={item} />
        </section>

        <section className="panel">
          <div className="panel-header">
            <div>
              <h3>Linked Alerts</h3>
              <p>Alerts grouped under this investigation.</p>
            </div>
            <Link href="/cases" className="text-link">Back to cases</Link>
          </div>

          {item.alerts.length === 0 ? (
            <p className="inline-empty">No alerts have been added to this case yet.</p>
          ) : (
            <div className="table-scroll">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Alert ID</th>
                    <th>Added</th>
                  </tr>
                </thead>
                <tbody>
                  {item.alerts.map((alert) => (
                    <tr key={alert.id}>
                      <td>
                        <Link href={`/alerts/${encodeURIComponent(alert.alert_id)}`} className="table-link">
                          {alert.alert_id}
                        </Link>
                      </td>
                      <td>{formatDate(alert.created_at)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>

        <section className="panel">
          <div className="panel-header">
            <div>
              <h3>Comments</h3>
              <p>Investigation notes for this case.</p>
            </div>
          </div>

          {item.comments.length === 0 ? (
            <p className="inline-empty">No case comments yet.</p>
          ) : (
            <div className="note-list">
              {item.comments.map((comment) => (
                <article key={comment.id} className="note-card">
                  <div className="note-meta">
                    <strong>{comment.author_full_name || comment.author_username}</strong>
                    <span>@{comment.author_username}</span>
                    <span>{formatDate(comment.created_at)}</span>
                  </div>
                  <p>{comment.body}</p>
                </article>
              ))}
            </div>
          )}
        </section>
      </AppShell>
    );
  } catch (error) {
    return (
      <AppShell title="Case Detail" eyebrow="Analyst Workflow" currentUser={currentUser}>
        <section className="panel">
          <ErrorState
            title="Case detail is unavailable"
            description={error instanceof Error ? error.message : "Unknown case detail error"}
            actionHref="/cases"
            actionLabel="Back to cases"
          />
        </section>
      </AppShell>
    );
  }
}

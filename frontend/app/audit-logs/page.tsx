import { redirect } from "next/navigation";

import { AppShell } from "@/components/AppShell";
import { EmptyState } from "@/components/EmptyState";
import { ErrorState } from "@/components/ErrorState";
import { getAuditLogsFromCookies, getCurrentUserFromCookies } from "@/lib/auth";
import { AuditLogItem } from "@/lib/types";

function formatActor(actorUsername: string | null, targetUsername: string | null) {
  const actor = actorUsername || "system";
  const target = targetUsername || "n/a";
  return `${actor} -> ${target}`;
}

function getActionMeta(action: string) {
  const mapping: Record<string, { label: string; className: string }> = {
    "auth.login": { label: "Login", className: "audit-badge-auth" },
    "auth.logout": { label: "Logout", className: "audit-badge-auth" },
    "user.created": { label: "User Created", className: "audit-badge-create" },
    "user.updated": { label: "User Updated", className: "audit-badge-update" },
    "user.activated": { label: "User Activated", className: "audit-badge-activate" },
    "user.deactivated": { label: "User Deactivated", className: "audit-badge-deactivate" },
    "user.password_reset": { label: "Password Reset", className: "audit-badge-reset" }
  };

  return mapping[action] || { label: action, className: "audit-badge-default" };
}

function formatTimestamp(value: string) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return new Intl.DateTimeFormat("en-GB", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false
  }).format(date);
}

function formatDetailLabel(key: string) {
  const normalized = key.replace(/_/g, " ");
  return normalized.charAt(0).toUpperCase() + normalized.slice(1);
}

function formatDetailValue(key: string, value: unknown) {
  if (Array.isArray(value)) {
    return value.join(", ");
  }

  if (typeof value === "boolean") {
    if (key === "is_active") {
      return value ? "Active" : "Inactive";
    }
    if (key === "is_superuser") {
      return value ? "Yes" : "No";
    }
    return value ? "True" : "False";
  }

  if (value === null || value === undefined || value === "") {
    return "N/A";
  }

  return String(value);
}

function getDetailEntries(item: AuditLogItem) {
  const details = item.details || {};
  const priority = ["username", "email", "roles", "changed_fields", "department_id", "is_active", "is_superuser", "token_id"];
  const keys = Object.keys(details).filter((key) => {
    if (item.action.startsWith("auth.") && key === "username") {
      return details[key] !== item.actor_username;
    }
    return true;
  });

  keys.sort((left, right) => {
    const leftIndex = priority.indexOf(left);
    const rightIndex = priority.indexOf(right);

    if (leftIndex === -1 && rightIndex === -1) {
      return left.localeCompare(right);
    }
    if (leftIndex === -1) {
      return 1;
    }
    if (rightIndex === -1) {
      return -1;
    }
    return leftIndex - rightIndex;
  });

  return keys.map((key) => ({
    key,
    label: formatDetailLabel(key),
    value: formatDetailValue(key, details[key])
  }));
}

export default async function AuditLogsPage({
  searchParams
}: {
  searchParams?: {
    action?: string;
    q?: string;
    page?: string;
  };
}) {
  const currentUser = await getCurrentUserFromCookies();

  if (!currentUser) {
    redirect("/login");
  }

  if (!currentUser.is_superuser) {
    redirect("/alerts");
  }

  const action = searchParams?.action || "";
  const q = searchParams?.q || "";
  const page = Number(searchParams?.page || "1");

  try {
    const auditLogs = await getAuditLogsFromCookies({
      action: action || undefined,
      q: q || undefined,
      page,
      page_size: 25
    });

    return (
      <AppShell title="Audit Logs" eyebrow="Superadmin" currentUser={currentUser}>
        <section className="panel stack">
          <div className="panel-header">
            <div>
              <h3>System Audit Trail</h3>
              <p>Track recent authentication and account-management actions.</p>
            </div>
            <p>{auditLogs.total} records</p>
          </div>

          <form className="filter-grid filter-grid-agents audit-filter-form" action="/audit-logs">
            <label>
              <span>Search</span>
              <input name="q" defaultValue={q} placeholder="action, actor, target" />
            </label>
            <label>
              <span>Action</span>
              <select name="action" defaultValue={action}>
                <option value="">All actions</option>
                <option value="auth.login">auth.login</option>
                <option value="auth.logout">auth.logout</option>
                <option value="user.created">user.created</option>
                <option value="user.updated">user.updated</option>
                <option value="user.activated">user.activated</option>
                <option value="user.deactivated">user.deactivated</option>
                <option value="user.password_reset">user.password_reset</option>
              </select>
            </label>
            <button type="submit" className="audit-filter-button">Apply Filters</button>
          </form>

          {auditLogs.items.length === 0 ? (
            <EmptyState
              title="No audit logs found"
              description="Try a broader filter or generate a few auth or user-management actions first."
            />
          ) : (
            <div className="table-scroll">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Time</th>
                    <th>Action</th>
                    <th>Actor -> Target</th>
                    <th>Entity</th>
                    <th>Details</th>
                  </tr>
                </thead>
                <tbody>
                  {auditLogs.items.map((item) => (
                    <tr key={item.id}>
                      <td>{formatTimestamp(item.created_at)}</td>
                      <td>
                        <span className={`status-pill ${getActionMeta(item.action).className}`}>
                          {getActionMeta(item.action).label}
                        </span>
                      </td>
                      <td>{formatActor(item.actor_username, item.target_username)}</td>
                      <td>
                        {item.entity_type}
                        {item.entity_id ? ` #${item.entity_id}` : ""}
                      </td>
                      <td className="details-cell">
                        {getDetailEntries(item).length === 0 ? (
                          <span className="details-empty">No extra context</span>
                        ) : (
                          <div className="details-list">
                            {getDetailEntries(item).map((entry) => (
                              <div key={entry.key} className="detail-item">
                                <span className="detail-label">{entry.label}</span>
                                <span className="detail-value">{entry.value}</span>
                              </div>
                            ))}
                          </div>
                        )}
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
    return (
      <AppShell title="Audit Logs" eyebrow="Superadmin" currentUser={currentUser}>
        <div className="panel">
          <ErrorState
            title="Unable to load audit logs"
            description={error instanceof Error ? error.message : "Unknown audit log error"}
          />
        </div>
      </AppShell>
    );
  }
}

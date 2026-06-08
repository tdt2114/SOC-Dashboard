import Link from "next/link";
import { redirect } from "next/navigation";

import { AppShell } from "@/components/AppShell";
import { ErrorState } from "@/components/ErrorState";
import { SeverityBadge } from "@/components/SeverityBadge";
import { getAgentDisplayName } from "@/lib/agentDisplay";
import { getCurrentUserFromCookies, getDashboardSummaryFromCookies } from "@/lib/auth";
import {
  TIME_RANGE_OPTIONS,
  getTimeRangeLabel,
  getTimeRangeShortLabel,
  normalizeTimeRange
} from "@/lib/timeRanges";

type SearchParams = {
  time_range?: string | string[];
};

function formatNumber(value: number) {
  return new Intl.NumberFormat("en-US").format(value);
}

function getParam(value?: string | string[]) {
  return Array.isArray(value) ? value[0] : value;
}

export default async function DashboardPage({ searchParams }: { searchParams?: SearchParams }) {
  const currentUser = await getCurrentUserFromCookies();
  if (!currentUser) {
    redirect("/login");
  }
  const timeRange = normalizeTimeRange(getParam(searchParams?.time_range));
  const timeRangeLabel = getTimeRangeLabel(timeRange);
  const timeRangeShortLabel = getTimeRangeShortLabel(timeRange);

  try {
    const summary = await getDashboardSummaryFromCookies(timeRange);

    return (
      <AppShell title="Dashboard" eyebrow="Operations Summary" currentUser={currentUser}>
        <section className="panel">
          <div className="panel-header">
            <div>
              <h3>{timeRangeShortLabel} Operations</h3>
              <p>Current alert volume, agent coverage, open cases, and assigned workload.</p>
            </div>
            <form className="inline-filter-form" method="get">
              <label>
                <span>Time Range</span>
                <select name="time_range" defaultValue={timeRange}>
                  {TIME_RANGE_OPTIONS.map((option) => (
                    <option key={option.value} value={option.value}>{option.label}</option>
                  ))}
                </select>
              </label>
              <button type="submit">Apply</button>
            </form>
          </div>

          <div className="dashboard-summary-grid">
            <div className="summary-card">
              <span className="summary-label">Alerts {timeRangeShortLabel}</span>
              <strong className="summary-value">{formatNumber(summary.total_alerts_24h)}</strong>
            </div>
            <div className="summary-card">
              <span className="summary-label">High / Critical</span>
              <strong className="summary-value">{formatNumber(summary.high_or_critical_alerts_24h)}</strong>
            </div>
            <div className="summary-card">
              <span className="summary-label">Active Agents</span>
              <strong className="summary-value">{formatNumber(summary.active_agents)}</strong>
            </div>
            <div className="summary-card">
              <span className="summary-label">Disconnected</span>
              <strong className="summary-value">{formatNumber(summary.disconnected_agents)}</strong>
            </div>
            <div className="summary-card">
              <span className="summary-label">Open Cases</span>
              <strong className="summary-value">{formatNumber(summary.open_cases)}</strong>
            </div>
            <div className="summary-card">
              <span className="summary-label">Assigned To Me</span>
              <strong className="summary-value">{formatNumber(summary.assigned_to_me_alerts)}</strong>
            </div>
          </div>
        </section>

        <section className="panel">
          <div className="panel-header">
            <div>
              <h3>Recent High Severity Alerts</h3>
              <p>Newest high and critical alerts from {timeRangeLabel.toLowerCase()}.</p>
            </div>
            <Link href={`/alerts?severity=high&time_range=${encodeURIComponent(timeRange)}`} className="text-link">
              Open alerts
            </Link>
          </div>

          {summary.recent_high_alerts.length === 0 ? (
            <p className="inline-empty">No high or critical alerts were found in {timeRangeLabel.toLowerCase()}.</p>
          ) : (
            <div className="table-scroll">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Timestamp</th>
                    <th>Severity</th>
                    <th>Agent</th>
                    <th>Rule ID</th>
                    <th>Description</th>
                  </tr>
                </thead>
                <tbody>
                  {summary.recent_high_alerts.map((alert) => (
                    <tr key={alert.id}>
                      <td>
                        <Link href={`/alerts/${encodeURIComponent(alert.id)}`} className="table-link">
                          {alert.timestamp || "N/A"}
                        </Link>
                      </td>
                      <td><SeverityBadge value={alert.severity_label} /></td>
                      <td>{getAgentDisplayName(alert.agent)}</td>
                      <td>{alert.rule.id || "N/A"}</td>
                      <td>{alert.rule.description || "N/A"}</td>
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
      <AppShell title="Dashboard" eyebrow="Operations Summary" currentUser={currentUser}>
        <section className="panel">
          <ErrorState
            title="Dashboard summary is unavailable"
            description={error instanceof Error ? error.message : "Unknown dashboard loading error"}
            actionHref="/alerts"
            actionLabel="Open alerts"
          />
        </section>
      </AppShell>
    );
  }
}

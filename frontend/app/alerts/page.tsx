import Link from "next/link";
import { redirect } from "next/navigation";

import { AppShell } from "@/components/AppShell";
import { EmptyState } from "@/components/EmptyState";
import { ErrorState } from "@/components/ErrorState";
import { SeverityBadge } from "@/components/SeverityBadge";
import { getCurrentUserFromCookies } from "@/lib/auth";
import { getAlerts } from "@/lib/api";

type SearchParams = Record<string, string | string[] | undefined>;

function getParam(value: string | string[] | undefined) {
  return Array.isArray(value) ? value[0] : value;
}

export default async function AlertsPage({
  searchParams
}: {
  searchParams?: SearchParams;
}) {
  const currentUser = await getCurrentUserFromCookies();
  if (!currentUser) {
    redirect("/login");
  }
  const page = Number(getParam(searchParams?.page) || "1");
  const timeRange = getParam(searchParams?.time_range) || "24h";
  const severity = getParam(searchParams?.severity);
  const agentName = getParam(searchParams?.agent_name);
  const ruleId = getParam(searchParams?.rule_id);
  const query = getParam(searchParams?.q);

  let result = null;
  let loadError: string | null = null;

  try {
    result = await getAlerts({
      page,
      time_range: timeRange,
      severity,
      agent_name: agentName,
      rule_id: ruleId,
      q: query
    });
  } catch (error) {
    loadError = error instanceof Error ? error.message : "Unknown alert loading error";
  }

  return (
    <AppShell title="Alert List" eyebrow="MVP Screen 1" currentUser={currentUser}>
      <section className="panel">
        <form className="filter-grid" method="get">
          <label>
            <span>Search</span>
            <input type="text" name="q" defaultValue={query} placeholder="rule.id, agent.name, srcip, path" />
          </label>
          <label>
            <span>Severity</span>
            <select name="severity" defaultValue={severity || ""}>
              <option value="">All</option>
              <option value="critical">Critical</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
            </select>
          </label>
          <label>
            <span>Agent Name</span>
            <input type="text" name="agent_name" defaultValue={agentName} placeholder="SOC-Server-Dev" />
          </label>
          <label>
            <span>Rule ID</span>
            <input type="text" name="rule_id" defaultValue={ruleId} placeholder="100001" />
          </label>
          <label>
            <span>Time Range</span>
            <select name="time_range" defaultValue={timeRange}>
              <option value="1h">Last 1h</option>
              <option value="24h">Last 24h</option>
              <option value="7d">Last 7d</option>
            </select>
          </label>
          <button type="submit">Apply Filters</button>
        </form>
      </section>

      <section className="panel">
        <div className="panel-header">
          <h3>Indexed Alerts</h3>
          <p>{result ? `${result.total} results from Repo A data sources.` : "Alert data is currently unavailable."}</p>
        </div>

        {loadError ? (
          <ErrorState
            title="Alert feed is unavailable"
            description={`${loadError}. Use MOCK_MODE=true for standalone Repo B testing, or start Repo A for live integration.`}
          />
        ) : result && result.items.length === 0 ? (
          <EmptyState
            title="No alerts matched the current filter set"
            description="Confirm Repo A is producing alerts and that the backend env points to the correct Indexer."
          />
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
                  <th>Source IP</th>
                  <th>Path</th>
                </tr>
              </thead>
              <tbody>
                {result?.items.map((item) => (
                  <tr key={item.id}>
                    <td>
                      <Link href={`/alerts/${item.id}`} className="table-link">
                        {item.timestamp || "N/A"}
                      </Link>
                    </td>
                    <td>
                      <SeverityBadge value={item.severity_label} />
                    </td>
                    <td>{item.agent.name || "N/A"}</td>
                    <td>{item.rule.id || "N/A"}</td>
                    <td>{item.rule.description || "N/A"}</td>
                    <td>{item.source.srcip || "N/A"}</td>
                    <td>{item.file.path || "N/A"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </AppShell>
  );
}

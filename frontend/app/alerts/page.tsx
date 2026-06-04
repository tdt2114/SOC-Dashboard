import Link from "next/link";
import { redirect } from "next/navigation";

import { AppShell } from "@/components/AppShell";
import { EmptyState } from "@/components/EmptyState";
import { ErrorState } from "@/components/ErrorState";
import { SavedSearchPanel } from "@/components/SavedSearchPanel";
import { SeverityBadge } from "@/components/SeverityBadge";
import { getAgentDisplayName } from "@/lib/agentDisplay";
import { getCurrentUserFromCookies, getSavedSearchesFromCookies } from "@/lib/auth";
import { getAgents, getAlerts } from "@/lib/api";
import type { AgentListItem, SavedSearchListResponse } from "@/lib/types";

type SearchParams = Record<string, string | string[] | undefined>;

function getParam(value: string | string[] | undefined) {
  return Array.isArray(value) ? value[0] : value;
}

function buildExportHref(filters: Record<string, string>) {
  const queryParams = new URLSearchParams();
  for (const [key, value] of Object.entries(filters)) {
    if (value) {
      queryParams.set(key, value);
    }
  }
  const suffix = queryParams.toString();
  return `/api/exports/alerts.csv${suffix ? `?${suffix}` : ""}`;
}

function normalizePage(value: string | string[] | undefined) {
  const page = Number(getParam(value) || "1");
  return Number.isFinite(page) && page > 0 ? Math.floor(page) : 1;
}

function normalizePageSize(value: string | string[] | undefined) {
  const pageSize = Number(getParam(value) || "10");
  return pageSize === 15 ? 15 : 10;
}

function buildAlertsHref(filters: Record<string, string>, overrides: Record<string, string | number>) {
  const queryParams = new URLSearchParams();
  for (const [key, value] of Object.entries(filters)) {
    if (value) {
      queryParams.set(key, value);
    }
  }
  for (const [key, value] of Object.entries(overrides)) {
    queryParams.set(key, String(value));
  }
  const suffix = queryParams.toString();
  return `/alerts${suffix ? `?${suffix}` : ""}`;
}

function PaginationLink({
  href,
  disabled,
  children
}: {
  href: string;
  disabled: boolean;
  children: string;
}) {
  if (disabled) {
    return <span className="pagination-link pagination-link-disabled">{children}</span>;
  }
  return <Link href={href} className="pagination-link">{children}</Link>;
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
  const page = normalizePage(searchParams?.page);
  const pageSize = normalizePageSize(searchParams?.page_size);
  const timeRange = getParam(searchParams?.time_range) || "24h";
  const severity = getParam(searchParams?.severity);
  const agentName = getParam(searchParams?.agent_name);
  const ruleId = getParam(searchParams?.rule_id);
  const query = getParam(searchParams?.q);
  const currentFilters = {
    q: query || "",
    severity: severity || "",
    agent_name: agentName || "",
    rule_id: ruleId || "",
    time_range: timeRange
  };
  const canUseSavedSearches =
    currentUser.is_superuser || currentUser.roles.some((role) => role === "admin" || role === "analyst");

  let result = null;
  let loadError: string | null = null;
  let savedSearches: SavedSearchListResponse = { items: [], total: 0 };
  let agentOptions: AgentListItem[] = [];

  try {
    try {
      const agents = await getAgents({});
      agentOptions = agents.items;
    } catch {
      agentOptions = [];
    }

    result = await getAlerts({
      page,
      page_size: pageSize,
      time_range: timeRange,
      severity,
      agent_name: agentName,
      rule_id: ruleId,
      q: query
    });
    if (canUseSavedSearches) {
      savedSearches = await getSavedSearchesFromCookies();
    }
  } catch (error) {
    loadError = error instanceof Error ? error.message : "Unknown alert loading error";
  }

  return (
    <AppShell title="Alert List" eyebrow="Alert Search" currentUser={currentUser}>
      <section className="panel">
        <form className="filter-grid" method="get">
          <input type="hidden" name="page" value="1" />
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
            <select name="agent_name" defaultValue={agentName || ""}>
              <option value="">All agents</option>
              {agentOptions.map((agent) => (
                <option key={agent.id} value={agent.name || ""} disabled={!agent.name}>
                  {getAgentDisplayName(agent)}
                </option>
              ))}
            </select>
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
          <label>
            <span>Rows</span>
            <select name="page_size" defaultValue={String(pageSize)}>
              <option value="10">10 per page</option>
              <option value="15">15 per page</option>
            </select>
          </label>
          <button type="submit">Apply Filters</button>
        </form>

        {canUseSavedSearches ? (
          <SavedSearchPanel initialData={savedSearches} currentFilters={currentFilters} />
        ) : null}
      </section>

      <section className="panel">
        <div className="panel-header">
          <div>
            <h3>Indexed Alerts</h3>
            <p>
              {result
                ? `${result.total} results from Repo A data sources.`
                : "Alert data is currently unavailable."}
            </p>
          </div>
          <a href={buildExportHref(currentFilters)} className="text-link">
            Export CSV
          </a>
        </div>

        {loadError ? (
          <ErrorState
            title="Alert feed is unavailable"
            description={`${loadError}. Use MOCK_MODE=true for standalone Repo B testing, or start Repo A for live integration.`}
            actionHref="/dashboard"
            actionLabel="Back to dashboard"
          />
        ) : result && result.items.length === 0 ? (
          <EmptyState
            title="No alerts matched the current filter set"
            description="Confirm Repo A is producing alerts and that the backend env points to the correct Indexer."
            actionHref="/alerts"
            actionLabel="Reset filters"
          />
        ) : result ? (
          <>
            <AlertPagination result={result} filters={currentFilters} />
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
                  {result.items.map((item) => (
                    <tr key={item.id}>
                      <td>
                        <Link href={`/alerts/${item.id}`} className="table-link">
                          {item.timestamp || "N/A"}
                        </Link>
                      </td>
                      <td>
                        <SeverityBadge value={item.severity_label} />
                      </td>
                      <td>{getAgentDisplayName(item.agent)}</td>
                      <td>{item.rule.id || "N/A"}</td>
                      <td>{item.rule.description || "N/A"}</td>
                      <td>{item.source.srcip || "N/A"}</td>
                      <td>{item.file.path || "N/A"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <AlertPagination result={result} filters={currentFilters} />
          </>
        ) : null}
      </section>
    </AppShell>
  );
}

function AlertPagination({
  result,
  filters
}: {
  result: {
    page: number;
    page_size: number;
    total: number;
  };
  filters: Record<string, string>;
}) {
  const totalPages = Math.max(1, Math.ceil(result.total / result.page_size));
  const currentPage = Math.min(result.page, totalPages);
  const start = result.total === 0 ? 0 : (currentPage - 1) * result.page_size + 1;
  const end = Math.min(result.total, currentPage * result.page_size);
  const previousPage = Math.max(1, currentPage - 1);
  const nextPage = Math.min(totalPages, currentPage + 1);

  return (
    <div className="pagination-bar">
      <p>
        Showing {start}-{end} of {result.total} alerts
        <span>Page {currentPage} of {totalPages}</span>
      </p>
      <div className="pagination-actions">
        <PaginationLink
          href={buildAlertsHref(filters, { page: previousPage, page_size: result.page_size })}
          disabled={currentPage <= 1}
        >
          Previous
        </PaginationLink>
        <PaginationLink
          href={buildAlertsHref(filters, { page: nextPage, page_size: result.page_size })}
          disabled={currentPage >= totalPages}
        >
          Next
        </PaginationLink>
      </div>
    </div>
  );
}

import { AppShell } from "@/components/AppShell";
import { EmptyState } from "@/components/EmptyState";
import { ErrorState } from "@/components/ErrorState";
import { getCurrentUserFromCookies } from "@/lib/auth";
import { getAgents } from "@/lib/api";
import { redirect } from "next/navigation";

type SearchParams = Record<string, string | string[] | undefined>;

function getParam(value: string | string[] | undefined) {
  return Array.isArray(value) ? value[0] : value;
}

export default async function AgentsPage({
  searchParams
}: {
  searchParams?: SearchParams;
}) {
  const currentUser = await getCurrentUserFromCookies();
  if (!currentUser) {
    redirect("/login");
  }
  const status = getParam(searchParams?.status);
  const query = getParam(searchParams?.q);
  let result = null;
  let loadError: string | null = null;

  try {
    result = await getAgents({ status, q: query });
  } catch (error) {
    loadError = error instanceof Error ? error.message : "Unknown agent loading error";
  }

  return (
    <AppShell title="Agent Inventory" eyebrow="MVP Screen 3" currentUser={currentUser}>
      <section className="panel">
        <form className="filter-grid filter-grid-agents" method="get">
          <label>
            <span>Search</span>
            <input type="text" name="q" defaultValue={query} placeholder="agent name" />
          </label>
          <label>
            <span>Status</span>
            <select name="status" defaultValue={status || ""}>
              <option value="">All</option>
              <option value="active">Active</option>
              <option value="disconnected">Disconnected</option>
              <option value="never_connected">Never Connected</option>
            </select>
          </label>
          <button type="submit">Filter Agents</button>
        </form>
      </section>

      <section className="panel">
        <div className="panel-header">
          <h3>Agent or Host List</h3>
          <p>{result ? `${result.total} agents returned by the Wazuh API.` : "Agent data is currently unavailable."}</p>
        </div>

        {loadError ? (
          <ErrorState
            title="Agent list is unavailable"
            description={`${loadError}. Use MOCK_MODE=true for standalone Repo B testing, or start Repo A for live integration.`}
          />
        ) : result && result.items.length === 0 ? (
          <EmptyState
            title="No agents matched the current filters"
            description="Confirm Wazuh API credentials are valid and that at least one agent is enrolled."
          />
        ) : (
          <div className="table-scroll">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Agent ID</th>
                  <th>Name</th>
                  <th>Status</th>
                  <th>Last Keepalive</th>
                </tr>
              </thead>
              <tbody>
                {result?.items.map((item) => (
                  <tr key={item.id}>
                    <td>{item.id}</td>
                    <td>{item.name || "N/A"}</td>
                    <td>
                      <span className={`status-pill status-${(item.status || "unknown").toLowerCase()}`}>
                        {item.status || "unknown"}
                      </span>
                    </td>
                    <td>{item.last_keepalive || "N/A"}</td>
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

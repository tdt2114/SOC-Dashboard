import { AgentDetailResponse, AgentListResponse, AlertDetail, AlertListResponse } from "@/lib/types";

const API_BASE_URL =
  process.env.API_BASE_URL ||
  process.env.NEXT_PUBLIC_API_BASE_URL ||
  "http://localhost:8000";

function toSearchParams(input: Record<string, string | number | undefined>): string {
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(input)) {
    if (value === undefined || value === "") {
      continue;
    }
    params.set(key, String(value));
  }
  const output = params.toString();
  return output ? `?${output}` : "";
}

async function fetchJson<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    cache: "no-store"
  });

  if (!response.ok) {
    throw new Error(`Request failed for ${path} with status ${response.status}`);
  }

  return response.json() as Promise<T>;
}

export async function getAlerts(params: {
  page?: number;
  page_size?: number;
  time_range?: string;
  severity?: string;
  agent_id?: string;
  agent_name?: string;
  rule_id?: string;
  q?: string;
}): Promise<AlertListResponse> {
  return fetchJson<AlertListResponse>(`/api/alerts${toSearchParams(params)}`);
}

export async function getAlert(id: string): Promise<AlertDetail> {
  return fetchJson<AlertDetail>(`/api/alerts/${encodeURIComponent(id)}`);
}

export async function getAgents(params: {
  status?: string;
  q?: string;
}): Promise<AgentListResponse> {
  return fetchJson<AgentListResponse>(`/api/agents${toSearchParams(params)}`);
}

export async function getAgent(id: string): Promise<AgentDetailResponse> {
  return fetchJson<AgentDetailResponse>(`/api/agents/${encodeURIComponent(id)}`);
}

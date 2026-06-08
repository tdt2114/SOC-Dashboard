import { cookies } from "next/headers";

import {
  AiAnalysis,
  AlertBookmarkResponse,
  AlertWorkflowResponse,
  AuditLogListResponse,
  AuthLoginResponse,
  AuthUser,
  CaseDetail,
  CaseListResponse,
  DashboardSummaryResponse,
  NotificationListResponse,
  PendingActionItem,
  PendingActionListResponse,
  SavedSearchListResponse,
  SystemSettingsResponse,
  UserAdminListResponse
} from "@/lib/types";

const API_BASE_URL =
  process.env.API_BASE_URL ||
  process.env.NEXT_PUBLIC_API_BASE_URL ||
  "http://localhost:8000";

export const ACCESS_COOKIE_NAME = "soc_access_token";
export const REFRESH_COOKIE_NAME = "soc_refresh_token";

export async function loginAgainstBackend(payload: {
  username: string;
  password: string;
}): Promise<AuthLoginResponse> {
  const response = await fetch(`${API_BASE_URL}/api/auth/login`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload),
    cache: "no-store"
  });

  if (!response.ok) {
    const detail = await safeDetail(response);
    throw new Error(detail || "Login failed");
  }

  return response.json() as Promise<AuthLoginResponse>;
}

export async function refreshAgainstBackend(refreshToken: string): Promise<AuthLoginResponse> {
  const response = await fetch(`${API_BASE_URL}/api/auth/refresh`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ refresh_token: refreshToken }),
    cache: "no-store"
  });

  if (!response.ok) {
    const detail = await safeDetail(response);
    throw new Error(detail || "Refresh failed");
  }

  return response.json() as Promise<AuthLoginResponse>;
}

export async function logoutAgainstBackend(refreshToken: string): Promise<void> {
  await fetch(`${API_BASE_URL}/api/auth/logout`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ refresh_token: refreshToken }),
    cache: "no-store"
  });
}

export async function getCurrentUserFromCookies(): Promise<AuthUser | null> {
  const cookieStore = await cookies();
  const accessToken = cookieStore.get(ACCESS_COOKIE_NAME)?.value;

  if (!accessToken) {
    return null;
  }

  const response = await fetch(`${API_BASE_URL}/api/auth/me`, {
    headers: {
      Authorization: `Bearer ${accessToken}`
    },
    cache: "no-store"
  });

  if (response.ok) {
    return response.json() as Promise<AuthUser>;
  }
  return null;
}

export async function updateProfileAgainstBackend(payload: {
  email: string;
  full_name: string | null;
}): Promise<AuthUser> {
  return authorizedJsonFetch<AuthUser>("/api/auth/me", {
    method: "PATCH",
    body: JSON.stringify(payload)
  });
}

export async function changePasswordAgainstBackend(payload: {
  current_password: string;
  new_password: string;
}): Promise<void> {
  await authorizedVoidFetch("/api/auth/change-password", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export async function getUsersAdminDataFromCookies(): Promise<UserAdminListResponse> {
  return authorizedJsonFetch<UserAdminListResponse>("/api/users", {
    method: "GET"
  });
}

export async function createUserAgainstBackend(payload: {
  username: string;
  email: string;
  password: string;
  full_name: string | null;
  department_id: number | null;
  is_active: boolean;
  is_superuser: boolean;
  roles: string[];
}): Promise<void> {
  await authorizedVoidFetch("/api/users", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export async function updateUserAgainstBackend(
  userId: number,
  payload: {
    email?: string;
    full_name?: string | null;
    department_id?: number | null;
    is_active?: boolean;
    is_superuser?: boolean;
    roles?: string[];
  }
): Promise<void> {
  await authorizedVoidFetch(`/api/users/${userId}`, {
    method: "PATCH",
    body: JSON.stringify(payload)
  });
}

export async function resetUserPasswordAgainstBackend(userId: number, newPassword: string): Promise<void> {
  await authorizedVoidFetch(`/api/users/${userId}/reset-password`, {
    method: "POST",
    body: JSON.stringify({ new_password: newPassword })
  });
}

export async function getAuditLogsFromCookies(params: {
  action?: string;
  q?: string;
  page?: number;
  page_size?: number;
}): Promise<AuditLogListResponse> {
  const query = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value === undefined || value === "") {
      continue;
    }
    query.set(key, String(value));
  }

  const suffix = query.toString() ? `?${query.toString()}` : "";
  return authorizedJsonFetch<AuditLogListResponse>(`/api/audit-logs${suffix}`, {
    method: "GET"
  });
}

export async function getDashboardSummaryFromCookies(timeRange = "24h"): Promise<DashboardSummaryResponse> {
  const query = new URLSearchParams();
  query.set("time_range", timeRange);

  return authorizedJsonFetch<DashboardSummaryResponse>(`/api/dashboard/summary?${query.toString()}`, {
    method: "GET"
  });
}

export async function getSystemSettingsFromCookies(): Promise<SystemSettingsResponse> {
  return authorizedJsonFetch<SystemSettingsResponse>("/api/settings/system", {
    method: "GET"
  });
}

export async function getAlertWorkflowFromCookies(alertId: string): Promise<AlertWorkflowResponse> {
  return authorizedJsonFetch<AlertWorkflowResponse>(`/api/alerts/${encodeURIComponent(alertId)}/workflow`, {
    method: "GET"
  });
}

export async function getAlertBookmarkFromCookies(alertId: string): Promise<AlertBookmarkResponse> {
  return authorizedJsonFetch<AlertBookmarkResponse>(`/api/alerts/${encodeURIComponent(alertId)}/bookmark`, {
    method: "GET"
  });
}

export async function bookmarkAlertAgainstBackend(alertId: string): Promise<AlertBookmarkResponse> {
  return authorizedJsonFetch<AlertBookmarkResponse>(`/api/alerts/${encodeURIComponent(alertId)}/bookmark`, {
    method: "POST"
  });
}

export async function unbookmarkAlertAgainstBackend(alertId: string): Promise<AlertBookmarkResponse> {
  return authorizedJsonFetch<AlertBookmarkResponse>(`/api/alerts/${encodeURIComponent(alertId)}/bookmark`, {
    method: "DELETE"
  });
}

export async function assignAlertAgainstBackend(
  alertId: string,
  payload: {
    assigned_user_id: number | null;
  }
): Promise<AlertWorkflowResponse> {
  return authorizedJsonFetch<AlertWorkflowResponse>(
    `/api/alerts/${encodeURIComponent(alertId)}/workflow/assignment`,
    {
      method: "PATCH",
      body: JSON.stringify(payload)
    }
  );
}

export async function addAlertNoteAgainstBackend(
  alertId: string,
  payload: {
    body: string;
  }
): Promise<AlertWorkflowResponse> {
  return authorizedJsonFetch<AlertWorkflowResponse>(`/api/alerts/${encodeURIComponent(alertId)}/workflow/notes`, {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export async function getAlertAiAnalysisFromCookies(alertId: string): Promise<AiAnalysis | null> {
  try {
    return await authorizedJsonFetch<AiAnalysis>(`/api/alerts/${encodeURIComponent(alertId)}/ai-analysis`, {
      method: "GET"
    });
  } catch {
    return null; // 404 = no analysis yet
  }
}

export async function runAlertAiAnalysisAgainstBackend(alertId: string): Promise<AiAnalysis> {
  return authorizedJsonFetch<AiAnalysis>(`/api/alerts/${encodeURIComponent(alertId)}/ai-analyze`, {
    method: "POST"
  });
}

export async function runPendingActionAiAnalysisAgainstBackend(token: string): Promise<AiAnalysis> {
  return authorizedJsonFetch<AiAnalysis>(`/api/actions/${encodeURIComponent(token)}/ai-analyze`, {
    method: "POST"
  });
}

export async function getCaseAiSummaryFromCookies(caseId: number): Promise<AiAnalysis | null> {
  try {
    return await authorizedJsonFetch<AiAnalysis>(`/api/cases/${caseId}/ai-summary`, { method: "GET" });
  } catch {
    return null; // 404 = no summary yet
  }
}

export async function runCaseAiSummaryAgainstBackend(caseId: number): Promise<AiAnalysis> {
  return authorizedJsonFetch<AiAnalysis>(`/api/cases/${caseId}/ai-summary`, { method: "POST" });
}

export async function getNotificationsFromCookies(): Promise<NotificationListResponse> {
  return authorizedJsonFetch<NotificationListResponse>("/api/notifications", {
    method: "GET"
  });
}

export async function getSavedSearchesFromCookies(): Promise<SavedSearchListResponse> {
  return authorizedJsonFetch<SavedSearchListResponse>("/api/saved-searches", {
    method: "GET"
  });
}

export async function createSavedSearchAgainstBackend(payload: {
  name: string;
  filters: Record<string, string>;
}): Promise<void> {
  await authorizedVoidFetch("/api/saved-searches", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export async function deleteSavedSearchAgainstBackend(savedSearchId: number): Promise<void> {
  await authorizedVoidFetch(`/api/saved-searches/${savedSearchId}`, {
    method: "DELETE"
  });
}

export async function getCasesFromCookies(): Promise<CaseListResponse> {
  return authorizedJsonFetch<CaseListResponse>("/api/cases", {
    method: "GET"
  });
}

export async function getCaseFromCookies(caseId: number): Promise<CaseDetail> {
  return authorizedJsonFetch<CaseDetail>(`/api/cases/${caseId}`, {
    method: "GET"
  });
}

export async function createCaseAgainstBackend(payload: {
  title: string;
  description?: string | null;
  status?: string;
  severity?: string;
  owner_user_id?: number | null;
  alert_id?: string | null;
}): Promise<CaseDetail> {
  return authorizedJsonFetch<CaseDetail>("/api/cases", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export async function updateCaseAgainstBackend(
  caseId: number,
  payload: {
    title?: string;
    description?: string | null;
    status?: string;
    severity?: string;
    owner_user_id?: number | null;
  }
): Promise<CaseDetail> {
  return authorizedJsonFetch<CaseDetail>(`/api/cases/${caseId}`, {
    method: "PATCH",
    body: JSON.stringify(payload)
  });
}

export async function addAlertToCaseAgainstBackend(caseId: number, alertId: string): Promise<CaseDetail> {
  return authorizedJsonFetch<CaseDetail>(`/api/cases/${caseId}/alerts`, {
    method: "POST",
    body: JSON.stringify({ alert_id: alertId })
  });
}

export async function removeAlertFromCaseAgainstBackend(caseId: number, alertId: string): Promise<CaseDetail> {
  return authorizedJsonFetch<CaseDetail>(`/api/cases/${caseId}/alerts/${encodeURIComponent(alertId)}`, {
    method: "DELETE"
  });
}

export async function addCaseCommentAgainstBackend(caseId: number, body: string): Promise<CaseDetail> {
  return authorizedJsonFetch<CaseDetail>(`/api/cases/${caseId}/comments`, {
    method: "POST",
    body: JSON.stringify({ body })
  });
}

export async function getPendingActionsForCaseFromCookies(caseId: number): Promise<PendingActionListResponse> {
  return authorizedJsonFetch<PendingActionListResponse>(`/api/actions?case_id=${caseId}`, {
    method: "GET"
  });
}

export async function approvePendingActionAgainstBackend(token: string): Promise<PendingActionItem> {
  return authorizedJsonFetch<PendingActionItem>(`/api/actions/${encodeURIComponent(token)}/approve`, {
    method: "POST"
  });
}

export async function rejectPendingActionAgainstBackend(
  token: string,
  reason: string | null
): Promise<PendingActionItem> {
  return authorizedJsonFetch<PendingActionItem>(`/api/actions/${encodeURIComponent(token)}/reject`, {
    method: "POST",
    body: JSON.stringify({ reason })
  });
}

export async function exportCsvFromBackend(path: string): Promise<string> {
  return authorizedTextFetch(path, {
    method: "GET"
  });
}

export async function markNotificationReadAgainstBackend(notificationId: number): Promise<void> {
  await authorizedVoidFetch(`/api/notifications/${notificationId}/read`, {
    method: "POST"
  });
}

export async function markAllNotificationsReadAgainstBackend(): Promise<void> {
  await authorizedVoidFetch("/api/notifications/read-all", {
    method: "POST"
  });
}

async function safeDetail(response: Response): Promise<string | null> {
  try {
    const payload = (await response.json()) as { detail?: string };
    return payload.detail || null;
  } catch {
    return null;
  }
}

async function authorizedJsonFetch<T>(
  path: string,
  init: {
    method: string;
    body?: string;
  }
): Promise<T> {
  const response = await authorizedFetch(path, init);
  return response.json() as Promise<T>;
}

async function authorizedVoidFetch(
  path: string,
  init: {
    method: string;
    body?: string;
  }
): Promise<void> {
  await authorizedFetch(path, init);
}

async function authorizedTextFetch(
  path: string,
  init: {
    method: string;
    body?: string;
  }
): Promise<string> {
  const response = await authorizedFetch(path, init);
  return response.text();
}

async function authorizedFetch(
  path: string,
  init: {
    method: string;
    body?: string;
  }
): Promise<Response> {
  const cookieStore = await cookies();
  const accessToken = cookieStore.get(ACCESS_COOKIE_NAME)?.value;

  if (!accessToken) {
    throw new Error("Authentication required");
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: init.method,
    headers: {
      Authorization: `Bearer ${accessToken}`,
      "Content-Type": "application/json"
    },
    body: init.body,
    cache: "no-store"
  });

  if (!response.ok) {
    const detail = await safeDetail(response);
    throw new Error(detail || `Request failed for ${path}`);
  }

  return response;
}

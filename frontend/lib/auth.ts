import { cookies } from "next/headers";

import { AuditLogListResponse, AuthLoginResponse, AuthUser, UserAdminListResponse } from "@/lib/types";

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
  const cookieStore = cookies();
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

async function authorizedFetch(
  path: string,
  init: {
    method: string;
    body?: string;
  }
): Promise<Response> {
  const cookieStore = cookies();
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

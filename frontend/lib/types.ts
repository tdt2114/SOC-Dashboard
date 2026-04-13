export type SeverityLabel = "low" | "medium" | "high" | "critical" | "unknown";

export interface AlertListItem {
  id: string;
  timestamp: string | null;
  severity_label: SeverityLabel;
  agent: {
    id: string | null;
    name: string | null;
  };
  rule: {
    id: string | null;
    level: number | null;
    description: string | null;
  };
  source: {
    srcip: string | null;
  };
  file: {
    path: string | null;
  };
}

export interface AlertDetail extends AlertListItem {
  raw: Record<string, unknown>;
}

export interface AlertListResponse {
  items: AlertListItem[];
  page: number;
  page_size: number;
  total: number;
}

export interface AgentListItem {
  id: string;
  name: string | null;
  status: string | null;
  last_keepalive: string | null;
}

export interface AgentListResponse {
  items: AgentListItem[];
  total: number;
}

export interface AuthUser {
  id: number;
  username: string;
  email: string;
  full_name: string | null;
  is_active: boolean;
  is_superuser: boolean;
  department: string | null;
  roles: string[];
}

export interface AuthLoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: AuthUser;
}

export interface DepartmentOption {
  id: number;
  code: string;
  name: string;
  is_active: boolean;
}

export interface RoleOption {
  id: number;
  name: string;
  is_active: boolean;
}

export interface UserAdminItem {
  id: number;
  username: string;
  email: string;
  full_name: string | null;
  is_active: boolean;
  is_superuser: boolean;
  department: string | null;
  department_id: number | null;
  roles: string[];
  created_at: string;
}

export interface UserAdminListResponse {
  items: UserAdminItem[];
  total: number;
  departments: DepartmentOption[];
  roles: RoleOption[];
}

export interface AuditLogItem {
  id: number;
  action: string;
  entity_type: string;
  entity_id: number | null;
  actor_user_id: number | null;
  actor_username: string | null;
  target_user_id: number | null;
  target_username: string | null;
  details: Record<string, unknown> | null;
  created_at: string;
}

export interface AuditLogListResponse {
  items: AuditLogItem[];
  total: number;
}

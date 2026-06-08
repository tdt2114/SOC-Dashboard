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

export interface AlertWorkflowUserOption {
  id: number;
  username: string;
  full_name: string | null;
}

export interface AlertAssignmentInfo {
  user_id: number | null;
  username: string | null;
  full_name: string | null;
  updated_at: string | null;
}

export interface AlertNoteInfo {
  id: number;
  author_user_id: number;
  author_username: string;
  author_full_name: string | null;
  body: string;
  created_at: string;
}

export interface AlertWorkflowResponse {
  alert_id: string;
  assignee: AlertAssignmentInfo;
  assignee_options: AlertWorkflowUserOption[];
  notes: AlertNoteInfo[];
}

export interface AlertBookmarkResponse {
  alert_id: string;
  is_bookmarked: boolean;
  bookmark_id: number | null;
  created_at: string | null;
}

export interface NotificationItem {
  id: number;
  type: string;
  title: string;
  body: string;
  link_url: string | null;
  is_read: boolean;
  created_at: string;
  read_at: string | null;
}

export interface NotificationListResponse {
  items: NotificationItem[];
  unread_count: number;
}

export interface AlertListResponse {
  items: AlertListItem[];
  page: number;
  page_size: number;
  total: number;
}

export interface SavedSearchItem {
  id: number;
  name: string;
  filters: Record<string, string>;
  created_at: string;
  updated_at: string;
}

export interface SavedSearchListResponse {
  items: SavedSearchItem[];
  total: number;
}

export interface AgentListItem {
  id: string;
  name: string | null;
  status: string | null;
  last_keepalive: string | null;
  platform?: string | null;
}

export interface AgentListResponse {
  items: AgentListItem[];
  total: number;
}

export interface AgentMonitoringContext {
  total_alerts_24h: number;
  high_or_critical_alerts_24h: number;
  status: string | null;
}

export interface AgentDetailResponse {
  agent: AgentListItem;
  recent_alerts: AlertListItem[];
  monitoring_context: AgentMonitoringContext;
}

export interface DashboardSummaryResponse {
  total_alerts_24h: number;
  high_or_critical_alerts_24h: number;
  active_agents: number;
  disconnected_agents: number;
  total_agents: number;
  open_cases: number;
  assigned_to_me_alerts: number;
  recent_high_alerts: AlertListItem[];
}

export interface SystemSettingsResponse {
  app_env: string;
  mode: string;
  database: string;
  default_time_range: string;
  default_page_size: number;
  max_page_size: number;
  verify_tls: boolean;
  wazuh_api_base_url: string;
  wazuh_indexer_url: string;
  wazuh_alert_index_pattern: string;
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

export interface CaseAlertItem {
  id: number;
  alert_id: string;
  created_at: string;
}

export interface CaseCommentItem {
  id: number;
  author_user_id: number;
  author_username: string;
  author_full_name: string | null;
  body: string;
  created_at: string;
}

export interface CaseItem {
  id: number;
  title: string;
  description: string | null;
  status: string;
  severity: string;
  owner_user_id: number | null;
  owner_username: string | null;
  owner_full_name: string | null;
  created_by_user_id: number | null;
  created_by_username: string | null;
  alert_count: number;
  comment_count: number;
  created_at: string;
  updated_at: string;
}

export interface CaseDetail extends CaseItem {
  alerts: CaseAlertItem[];
  comments: CaseCommentItem[];
}

export interface CaseListResponse {
  items: CaseItem[];
  total: number;
}

export interface PendingActionItem {
  id: number;
  token: string;
  action_type: string;
  command: string;
  target_agent_id: string;
  arguments: string[] | null;
  reason: string | null;
  rule_id: string | null;
  alert_id: string | null;
  case_id: number | null;
  status: string;
  requested_by: string;
  decided_by_user_id: number | null;
  decided_by_username: string | null;
  decided_at: string | null;
  execution_status: string | null;
  execution_detail: string | null;
  created_at: string;
  updated_at: string;
}

export interface PendingActionListResponse {
  items: PendingActionItem[];
  total: number;
}

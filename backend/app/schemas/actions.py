from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


# action_type -> Wazuh active-response command name
ACTION_COMMANDS: dict[str, str] = {
    "isolate-host": "isolate-host",
    "kill-process": "kill-process",
    "block-ip-iptables": "block-ip-iptables",
}


class PendingActionCreateRequest(BaseModel):
    action_type: str = Field(min_length=1, max_length=50)
    target_agent_id: str = Field(min_length=1, max_length=50)
    arguments: list[str] | None = None
    reason: str | None = Field(default=None, max_length=2000)
    rule_id: str | None = Field(default=None, max_length=50)
    alert_id: str | None = Field(default=None, max_length=255)
    case_id: int | None = None
    requested_by: str | None = Field(default=None, max_length=100)


class PendingActionItemResponse(BaseModel):
    id: int
    token: str
    action_type: str
    command: str
    target_agent_id: str
    arguments: list[str] | None = None
    reason: str | None = None
    rule_id: str | None = None
    alert_id: str | None = None
    case_id: int | None = None
    status: str
    requested_by: str
    decided_by_user_id: int | None = None
    decided_by_username: str | None = None
    decided_at: datetime | None = None
    execution_status: str | None = None
    execution_detail: str | None = None
    created_at: datetime
    updated_at: datetime


class PendingActionCreatedResponse(PendingActionItemResponse):
    approval_path: str


class PendingActionListResponse(BaseModel):
    items: list[PendingActionItemResponse]
    total: int


class PendingActionRejectRequest(BaseModel):
    reason: str | None = Field(default=None, max_length=2000)

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class AlertAgent(BaseModel):
    id: str | None = None
    name: str | None = None


class AlertRule(BaseModel):
    id: str | None = None
    level: int | None = None
    description: str | None = None


class AlertSource(BaseModel):
    srcip: str | None = None


class AlertFile(BaseModel):
    path: str | None = None


class AlertListItem(BaseModel):
    id: str
    timestamp: str | None = None
    severity_label: str = "unknown"
    agent: AlertAgent = Field(default_factory=AlertAgent)
    rule: AlertRule = Field(default_factory=AlertRule)
    source: AlertSource = Field(default_factory=AlertSource)
    file: AlertFile = Field(default_factory=AlertFile)


class AlertDetail(AlertListItem):
    raw: dict[str, Any] = Field(default_factory=dict)


class AlertListResponse(BaseModel):
    items: list[AlertListItem]
    page: int
    page_size: int
    total: int

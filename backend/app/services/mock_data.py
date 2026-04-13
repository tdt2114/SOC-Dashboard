from __future__ import annotations

from datetime import UTC, datetime, timedelta

from app.core.severity import severity_label
from app.schemas.agents import AgentDetailResponse, AgentListItem, AgentListResponse, AgentMonitoringContext
from app.schemas.alerts import AlertAgent, AlertDetail, AlertFile, AlertListItem, AlertListResponse, AlertRule, AlertSource


def _now_utc() -> datetime:
    return datetime.now(UTC)


def _iso_utc(*, days: int = 0, hours: int = 0, minutes: int = 0) -> str:
    return (_now_utc() - timedelta(days=days, hours=hours, minutes=minutes)).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )


MOCK_ALERTS: list[AlertDetail] = [
    AlertDetail(
        id="mock-100001",
        timestamp=_iso_utc(minutes=30),
        severity_label=severity_label(10),
        agent=AlertAgent(id="001", name="SOC-Server-Dev"),
        rule=AlertRule(id="100001", level=10, description="Multiple authentication failures"),
        source=AlertSource(srcip="10.10.10.51"),
        file=AlertFile(path=None),
        raw={
            "timestamp": _iso_utc(minutes=30),
            "agent": {"id": "001", "name": "SOC-Server-Dev"},
            "rule": {"id": "100001", "level": 10, "description": "Multiple authentication failures"},
            "data": {"srcip": "10.10.10.51"},
        },
    ),
    AlertDetail(
        id="mock-100064",
        timestamp=_iso_utc(hours=6),
        severity_label=severity_label(7),
        agent=AlertAgent(id=None, name="wazuh-manager"),
        rule=AlertRule(id="100064", level=7, description="Dev FIM confirmation rule fired"),
        source=AlertSource(srcip=None),
        file=AlertFile(path="/etc/hosts"),
        raw={
            "timestamp": _iso_utc(hours=6),
            "rule": {"id": "100064", "level": 7, "description": "Dev FIM confirmation rule fired"},
            "syscheck": {"path": "/etc/hosts"},
        },
    ),
    AlertDetail(
        id="mock-550",
        timestamp=_iso_utc(days=3),
        severity_label=severity_label(5),
        agent=AlertAgent(id="001", name="SOC-Server-Dev"),
        rule=AlertRule(id="550", level=5, description="Integrity checksum changed"),
        source=AlertSource(srcip=None),
        file=AlertFile(path="/etc/hosts"),
        raw={
            "timestamp": _iso_utc(days=3),
            "agent": {"id": "001", "name": "SOC-Server-Dev"},
            "rule": {"id": "550", "level": 5, "description": "Integrity checksum changed"},
            "syscheck": {"path": "/etc/hosts"},
        },
    ),
]

MOCK_AGENTS: list[AgentListItem] = [
    AgentListItem(id="001", name="SOC-Server-Dev", status="active", last_keepalive=_iso_utc(minutes=5)),
    AgentListItem(id="002", name="Windows-Pilot-01", status="disconnected", last_keepalive=_iso_utc(hours=2)),
]


class MockDataService:
    async def search_alerts(
        self,
        *,
        page: int,
        page_size: int,
        time_range: str,
        severity: str | None,
        agent_id: str | None,
        agent_name: str | None,
        rule_id: str | None,
        query_text: str | None,
    ) -> AlertListResponse:
        items = list(MOCK_ALERTS)
        items = self._filter_alerts_by_time_range(items, time_range)

        if severity:
            items = [item for item in items if item.severity_label == severity]
        if agent_id:
            items = [item for item in items if item.agent.id == agent_id]
        if agent_name:
            needle = agent_name.lower()
            items = [item for item in items if (item.agent.name or "").lower() == needle]
        if rule_id:
            items = [item for item in items if item.rule.id == rule_id]
        if query_text:
            needle = query_text.lower()
            items = [
                item
                for item in items
                if needle in (item.agent.name or "").lower()
                or needle in (item.rule.id or "").lower()
                or needle in (item.rule.description or "").lower()
                or needle in (item.source.srcip or "").lower()
                or needle in (item.file.path or "").lower()
            ]

        items.sort(key=lambda item: item.timestamp or "", reverse=True)
        total = len(items)
        start = max(page - 1, 0) * page_size
        end = start + page_size
        page_items = [
            AlertListItem(
                id=item.id,
                timestamp=item.timestamp,
                severity_label=item.severity_label,
                agent=item.agent,
                rule=item.rule,
                source=item.source,
                file=item.file,
            )
            for item in items[start:end]
        ]
        return AlertListResponse(items=page_items, page=page, page_size=page_size, total=total)

    async def get_alert(self, alert_id: str) -> AlertDetail | None:
        for item in MOCK_ALERTS:
            if item.id == alert_id:
                return item
        return None

    async def list_agents(self, *, status: str | None, query_text: str | None) -> AgentListResponse:
        items = list(MOCK_AGENTS)
        if status:
            needle = status.lower()
            items = [item for item in items if (item.status or "").lower() == needle]
        if query_text:
            needle = query_text.lower()
            items = [item for item in items if needle in (item.name or "").lower()]
        return AgentListResponse(items=items, total=len(items))

    async def get_agent(self, agent_id: str) -> AgentListItem | None:
        for item in MOCK_AGENTS:
            if item.id == agent_id:
                return item
        return None

    async def get_agent_detail(self, agent_id: str) -> AgentDetailResponse | None:
        agent = await self.get_agent(agent_id)
        if agent is None:
            return None

        alerts = [item for item in MOCK_ALERTS if item.agent.id == agent_id]
        alerts_24h = self._filter_alerts_by_time_range(alerts, "24h")
        high_or_critical = [item for item in alerts_24h if item.severity_label in {"high", "critical"}]
        alerts.sort(key=lambda item: item.timestamp or "", reverse=True)
        recent_alerts = [
            AlertListItem(
                id=item.id,
                timestamp=item.timestamp,
                severity_label=item.severity_label,
                agent=item.agent,
                rule=item.rule,
                source=item.source,
                file=item.file,
            )
            for item in alerts[:5]
        ]
        return AgentDetailResponse(
            agent=agent,
            recent_alerts=recent_alerts,
            monitoring_context=AgentMonitoringContext(
                total_alerts_24h=len(alerts_24h),
                high_or_critical_alerts_24h=len(high_or_critical),
                status=agent.status,
            ),
        )

    def _filter_alerts_by_time_range(self, items: list[AlertDetail], time_range: str) -> list[AlertDetail]:
        hours = _time_range_to_hours(time_range)
        if hours is None:
            return items

        threshold = _now_utc() - timedelta(hours=hours)
        filtered_items: list[AlertDetail] = []
        for item in items:
            timestamp = _parse_timestamp(item.timestamp)
            if timestamp is None:
                continue
            if timestamp >= threshold:
                filtered_items.append(item)
        return filtered_items


def _parse_timestamp(value: str | None) -> datetime | None:
    if not value:
        return None
    normalized = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _time_range_to_hours(value: str | None) -> int | None:
    normalized = (value or "24h").strip().lower()
    mapping = {
        "1h": 1,
        "24h": 24,
        "7d": 24 * 7,
    }
    return mapping.get(normalized)

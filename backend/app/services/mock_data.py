from __future__ import annotations

from app.core.severity import severity_label
from app.schemas.agents import AgentDetailResponse, AgentListItem, AgentListResponse, AgentMonitoringContext
from app.schemas.alerts import AlertAgent, AlertDetail, AlertFile, AlertListItem, AlertListResponse, AlertRule, AlertSource


MOCK_ALERTS: list[AlertDetail] = [
    AlertDetail(
        id="mock-100001",
        timestamp="2026-04-11T10:00:00Z",
        severity_label=severity_label(10),
        agent=AlertAgent(id="001", name="SOC-Server-Dev"),
        rule=AlertRule(id="100001", level=10, description="Multiple authentication failures"),
        source=AlertSource(srcip="10.10.10.51"),
        file=AlertFile(path=None),
        raw={
            "timestamp": "2026-04-11T10:00:00Z",
            "agent": {"id": "001", "name": "SOC-Server-Dev"},
            "rule": {"id": "100001", "level": 10, "description": "Multiple authentication failures"},
            "data": {"srcip": "10.10.10.51"},
        },
    ),
    AlertDetail(
        id="mock-100064",
        timestamp="2026-04-11T10:05:00Z",
        severity_label=severity_label(7),
        agent=AlertAgent(id=None, name="wazuh-manager"),
        rule=AlertRule(id="100064", level=7, description="Dev FIM confirmation rule fired"),
        source=AlertSource(srcip=None),
        file=AlertFile(path="/etc/hosts"),
        raw={
            "timestamp": "2026-04-11T10:05:00Z",
            "rule": {"id": "100064", "level": 7, "description": "Dev FIM confirmation rule fired"},
            "syscheck": {"path": "/etc/hosts"},
        },
    ),
    AlertDetail(
        id="mock-550",
        timestamp="2026-04-11T10:07:00Z",
        severity_label=severity_label(5),
        agent=AlertAgent(id="001", name="SOC-Server-Dev"),
        rule=AlertRule(id="550", level=5, description="Integrity checksum changed"),
        source=AlertSource(srcip=None),
        file=AlertFile(path="/etc/hosts"),
        raw={
            "timestamp": "2026-04-11T10:07:00Z",
            "agent": {"id": "001", "name": "SOC-Server-Dev"},
            "rule": {"id": "550", "level": 5, "description": "Integrity checksum changed"},
            "syscheck": {"path": "/etc/hosts"},
        },
    ),
]

MOCK_AGENTS: list[AgentListItem] = [
    AgentListItem(id="001", name="SOC-Server-Dev", status="active", last_keepalive="2026-04-11T10:09:00Z"),
    AgentListItem(id="002", name="Windows-Pilot-01", status="disconnected", last_keepalive="2026-04-11T08:40:00Z"),
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
        del time_range
        items = list(MOCK_ALERTS)

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
        high_or_critical = [item for item in alerts if item.severity_label in {"high", "critical"}]
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
                total_alerts_24h=len(alerts),
                high_or_critical_alerts_24h=len(high_or_critical),
                status=agent.status,
            ),
        )

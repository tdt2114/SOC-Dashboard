from __future__ import annotations

from typing import Any

import httpx

from app.core.config import Settings
from app.core.exceptions import UpstreamServiceError
from app.core.severity import severity_label
from app.schemas.alerts import AlertAgent, AlertDetail, AlertFile, AlertListItem, AlertListResponse, AlertRule, AlertSource


class IndexerClient:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._auth = (settings.wazuh_indexer_username, settings.wazuh_indexer_password)
        self._timeout = settings.indexer_timeout_seconds
        self._verify = settings.verify_tls

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
        offset = max(page - 1, 0) * page_size
        body = self._build_search_body(
            time_range=time_range,
            severity=severity,
            agent_id=agent_id,
            agent_name=agent_name,
            rule_id=rule_id,
            query_text=query_text,
            from_=offset,
            size=page_size,
        )
        payload = await self._request(
            "POST",
            f"/{self._settings.wazuh_alert_index_pattern}/_search",
            json=body,
        )
        hits = payload.get("hits", {})
        total_obj = hits.get("total", {})
        total = total_obj.get("value", 0) if isinstance(total_obj, dict) else int(total_obj or 0)
        items = [self._normalize_alert_hit(hit) for hit in hits.get("hits", [])]
        return AlertListResponse(items=items, page=page, page_size=page_size, total=total)

    async def get_alert(self, alert_id: str) -> AlertDetail | None:
        payload = await self._request(
            "POST",
            f"/{self._settings.wazuh_alert_index_pattern}/_search",
            json={
                "size": 1,
                "query": {
                    "bool": {
                        "should": [
                            {"ids": {"values": [alert_id]}},
                            {"term": {"id": alert_id}},
                        ],
                        "minimum_should_match": 1,
                    }
                },
            },
        )
        hits = payload.get("hits", {}).get("hits", [])
        if not hits:
            return None
        return self._normalize_alert_hit(hits[0], include_raw=True)

    async def _request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        try:
            async with httpx.AsyncClient(
                base_url=self._settings.wazuh_indexer_url,
                auth=self._auth,
                timeout=self._timeout,
                verify=self._verify,
                headers={"Content-Type": "application/json"},
            ) as client:
                response = await client.request(method, path, **kwargs)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as exc:
            raise UpstreamServiceError("wazuh-indexer", str(exc)) from exc

    def _build_search_body(
        self,
        *,
        time_range: str,
        severity: str | None,
        agent_id: str | None,
        agent_name: str | None,
        rule_id: str | None,
        query_text: str | None,
        from_: int,
        size: int,
    ) -> dict[str, Any]:
        must_filters: list[dict[str, Any]] = [
            {
                "range": {
                    "timestamp": {
                        "gte": self._time_range_to_gte(time_range),
                        "lte": "now",
                    }
                }
            }
        ]

        if severity:
            range_filter = self._severity_to_range(severity)
            if range_filter:
                must_filters.append({"range": {"rule.level": range_filter}})

        if agent_name:
            must_filters.append(
                {
                    "bool": {
                        "should": [
                            {"term": {"agent.name.keyword": agent_name}},
                            {"match_phrase": {"agent.name": agent_name}},
                        ],
                        "minimum_should_match": 1,
                    }
                }
            )

        if agent_id:
            must_filters.append(
                {
                    "bool": {
                        "should": [
                            {"term": {"agent.id": agent_id}},
                            {"term": {"agent.id.keyword": agent_id}},
                            {"match_phrase": {"agent.id": agent_id}},
                        ],
                        "minimum_should_match": 1,
                    }
                }
            )

        if rule_id:
            must_filters.append(
                {
                    "bool": {
                        "should": [
                            {"term": {"rule.id": rule_id}},
                            {"match_phrase": {"rule.id": rule_id}},
                        ],
                        "minimum_should_match": 1,
                    }
                }
            )

        must_clause: list[dict[str, Any]] = [{"match_all": {}}]
        if query_text:
            must_clause = [
                {
                    "multi_match": {
                        "query": query_text,
                        "fields": [
                            "agent.name^3",
                            "rule.id^3",
                            "rule.description^2",
                            "data.srcip",
                            "syscheck.path",
                        ],
                        "type": "best_fields",
                    }
                }
            ]

        return {
            "from": from_,
            "size": size,
            "sort": [{"timestamp": {"order": "desc"}}],
            "query": {"bool": {"must": must_clause, "filter": must_filters}},
        }

    def _normalize_alert_hit(self, hit: dict[str, Any], include_raw: bool = False) -> AlertListItem | AlertDetail:
        source = hit.get("_source", {})
        agent = source.get("agent", {}) or {}
        rule = source.get("rule", {}) or {}
        data = source.get("data", {}) or {}
        syscheck = source.get("syscheck", {}) or {}

        payload = {
            "id": hit.get("_id") or str(source.get("id") or ""),
            "timestamp": source.get("timestamp"),
            "severity_label": severity_label(_to_int(rule.get("level"))),
            "agent": AlertAgent(id=_to_str(agent.get("id")), name=_to_str(agent.get("name"))),
            "rule": AlertRule(
                id=_to_str(rule.get("id")),
                level=_to_int(rule.get("level")),
                description=_to_str(rule.get("description")),
            ),
            "source": AlertSource(srcip=_to_str(data.get("srcip"))),
            "file": AlertFile(path=_to_str(syscheck.get("path"))),
        }

        if include_raw:
            return AlertDetail(**payload, raw=source)
        return AlertListItem(**payload)

    def _severity_to_range(self, severity: str) -> dict[str, int] | None:
        normalized = severity.strip().lower()
        mapping = {
            "low": {"gte": 0, "lte": 3},
            "medium": {"gte": 4, "lte": 6},
            "high": {"gte": 7, "lte": 9},
            "critical": {"gte": 10},
        }
        return mapping.get(normalized)

    def _time_range_to_gte(self, time_range: str) -> str:
        value = time_range.strip().lower()
        if value.endswith(("m", "h", "d")):
            return f"now-{value}"
        return "now-24h"


def _to_str(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


def _to_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None

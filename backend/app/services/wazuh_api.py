from __future__ import annotations

from typing import Any

import httpx

from app.core.config import Settings
from app.core.exceptions import UpstreamServiceError
from app.schemas.agents import AgentListItem, AgentListResponse


class WazuhApiClient:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._timeout = settings.api_timeout_seconds
        self._verify = settings.verify_tls

    async def list_agents(self, *, status: str | None, query_text: str | None) -> AgentListResponse:
        token = await self._authenticate()
        params: dict[str, str] = {"limit": "500"}
        if status:
            params["status"] = status
        if query_text:
            params["search"] = query_text

        payload = await self._request("GET", "/agents", token=token, params=params)
        data = payload.get("data", {})
        affected_items = data.get("affected_items", []) or []
        items = [
            AgentListItem(
                id=str(item.get("id", "")),
                name=item.get("name"),
                status=item.get("status"),
                last_keepalive=item.get("lastKeepAlive") or item.get("last_keepalive"),
            )
            for item in affected_items
        ]
        return AgentListResponse(items=items, total=len(items))

    async def get_agent(self, agent_id: str) -> AgentListItem | None:
        agents = await self.list_agents(status=None, query_text=None)
        for item in agents.items:
            if item.id == agent_id:
                return item
        return None

    async def _authenticate(self) -> str:
        try:
            async with httpx.AsyncClient(
                base_url=self._settings.wazuh_api_base_url,
                timeout=self._timeout,
                verify=self._verify,
                auth=(self._settings.wazuh_api_username, self._settings.wazuh_api_password),
            ) as client:
                response = await client.get("/security/user/authenticate?raw=true")
                response.raise_for_status()
                return response.text.strip().strip('"')
        except httpx.HTTPError as exc:
            raise UpstreamServiceError("wazuh-api", str(exc)) from exc

    async def _request(self, method: str, path: str, *, token: str, **kwargs: Any) -> dict[str, Any]:
        try:
            async with httpx.AsyncClient(
                base_url=self._settings.wazuh_api_base_url,
                timeout=self._timeout,
                verify=self._verify,
                headers={"Authorization": f"Bearer {token}"},
            ) as client:
                response = await client.request(method, path, **kwargs)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as exc:
            raise UpstreamServiceError("wazuh-api", str(exc)) from exc

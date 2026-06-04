from __future__ import annotations

from pydantic import BaseModel


class SystemSettingsResponse(BaseModel):
    app_env: str
    mode: str
    database: str
    default_time_range: str
    default_page_size: int
    max_page_size: int
    verify_tls: bool
    wazuh_api_base_url: str
    wazuh_indexer_url: str
    wazuh_alert_index_pattern: str

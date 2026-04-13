from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache


def _as_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    app_name: str
    app_env: str
    mock_mode: bool
    cors_origins: list[str]
    database_url: str
    postgres_db: str
    postgres_user: str
    postgres_password: str
    postgres_host: str
    postgres_port: int
    jwt_secret_key: str
    jwt_refresh_secret_key: str
    access_token_expire_minutes: int
    refresh_token_expire_days: int
    seed_default_department_code: str
    seed_default_department_name: str
    seed_admin_username: str
    seed_admin_email: str
    seed_admin_password: str
    seed_admin_full_name: str
    seed_superadmin_username: str
    seed_superadmin_email: str
    seed_superadmin_password: str
    seed_superadmin_full_name: str
    api_timeout_seconds: float
    indexer_timeout_seconds: float
    verify_tls: bool
    default_time_range: str
    default_page_size: int
    max_page_size: int
    wazuh_api_base_url: str
    wazuh_api_username: str
    wazuh_api_password: str
    wazuh_indexer_url: str
    wazuh_indexer_username: str
    wazuh_indexer_password: str
    wazuh_alert_index_pattern: str


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    cors = os.getenv("CORS_ORIGINS", "http://localhost:3000")
    postgres_db = os.getenv("POSTGRES_DB", "soc_dashboard")
    postgres_user = os.getenv("POSTGRES_USER", "soc_dashboard")
    postgres_password = os.getenv("POSTGRES_PASSWORD", "soc_dashboard_dev")
    postgres_host = os.getenv("POSTGRES_HOST", "soc-postgres")
    postgres_port = int(os.getenv("POSTGRES_PORT", "5432"))
    database_url = os.getenv(
        "DATABASE_URL",
        f"postgresql+asyncpg://{postgres_user}:{postgres_password}@{postgres_host}:{postgres_port}/{postgres_db}",
    )
    return Settings(
        app_name=os.getenv("APP_NAME", "soc-dashboard-api"),
        app_env=os.getenv("APP_ENV", "development"),
        mock_mode=_as_bool(os.getenv("MOCK_MODE"), default=False),
        cors_origins=[item.strip() for item in cors.split(",") if item.strip()],
        database_url=database_url,
        postgres_db=postgres_db,
        postgres_user=postgres_user,
        postgres_password=postgres_password,
        postgres_host=postgres_host,
        postgres_port=postgres_port,
        jwt_secret_key=os.getenv("JWT_SECRET_KEY", "change-this-dev-secret"),
        jwt_refresh_secret_key=os.getenv("JWT_REFRESH_SECRET_KEY", "change-this-dev-refresh-secret"),
        access_token_expire_minutes=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")),
        refresh_token_expire_days=int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7")),
        seed_default_department_code=os.getenv("SEED_DEFAULT_DEPARTMENT_CODE", "SOC"),
        seed_default_department_name=os.getenv("SEED_DEFAULT_DEPARTMENT_NAME", "Security Operations Center"),
        seed_admin_username=os.getenv("SEED_ADMIN_USERNAME", "admin"),
        seed_admin_email=os.getenv("SEED_ADMIN_EMAIL", "admin@local.test"),
        seed_admin_password=os.getenv("SEED_ADMIN_PASSWORD", "Admin123!ChangeMe"),
        seed_admin_full_name=os.getenv("SEED_ADMIN_FULL_NAME", "SOC Admin"),
        seed_superadmin_username=os.getenv("SEED_SUPERADMIN_USERNAME", "superadmin"),
        seed_superadmin_email=os.getenv("SEED_SUPERADMIN_EMAIL", "superadmin@local.test"),
        seed_superadmin_password=os.getenv("SEED_SUPERADMIN_PASSWORD", "SuperAdmin123!ChangeMe"),
        seed_superadmin_full_name=os.getenv("SEED_SUPERADMIN_FULL_NAME", "SOC Super Admin"),
        api_timeout_seconds=float(os.getenv("API_TIMEOUT_SECONDS", "10")),
        indexer_timeout_seconds=float(os.getenv("INDEXER_TIMEOUT_SECONDS", "10")),
        verify_tls=_as_bool(os.getenv("VERIFY_TLS"), default=False),
        default_time_range=os.getenv("DEFAULT_TIME_RANGE", "24h"),
        default_page_size=int(os.getenv("DEFAULT_PAGE_SIZE", "20")),
        max_page_size=int(os.getenv("MAX_PAGE_SIZE", "100")),
        wazuh_api_base_url=os.getenv("WAZUH_API_BASE_URL", "https://wazuh-manager:55000"),
        wazuh_api_username=os.getenv("WAZUH_API_USERNAME", "wazuh-wui"),
        wazuh_api_password=os.getenv("WAZUH_API_PASSWORD", ""),
        wazuh_indexer_url=os.getenv("WAZUH_INDEXER_URL", "https://wazuh-indexer:9200"),
        wazuh_indexer_username=os.getenv("WAZUH_INDEXER_USERNAME", "admin"),
        wazuh_indexer_password=os.getenv("WAZUH_INDEXER_PASSWORD", ""),
        wazuh_alert_index_pattern=os.getenv("WAZUH_ALERT_INDEX_PATTERN", "wazuh-alerts-*"),
    )

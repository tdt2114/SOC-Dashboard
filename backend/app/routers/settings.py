from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.db.session import check_database, get_db_session
from app.schemas.settings import SystemSettingsResponse
from app.services.auth import get_current_user_model_from_token
from app.services.users import require_superadmin_user

router = APIRouter(prefix="/api/settings", tags=["settings"])
bearer_scheme = HTTPBearer(auto_error=False)


@router.get("/system", response_model=SystemSettingsResponse)
async def get_system_settings(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> SystemSettingsResponse:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    current_user = await get_current_user_model_from_token(session, credentials.credentials)
    await require_superadmin_user(current_user)
    db_ok = await check_database()
    return SystemSettingsResponse(
        app_env=settings.app_env,
        mode="mock" if settings.mock_mode else "live",
        database="ok" if db_ok else "unavailable",
        default_time_range=settings.default_time_range,
        default_page_size=settings.default_page_size,
        max_page_size=settings.max_page_size,
        verify_tls=settings.verify_tls,
        wazuh_api_base_url=settings.wazuh_api_base_url,
        wazuh_indexer_url=settings.wazuh_indexer_url,
        wazuh_alert_index_pattern=settings.wazuh_alert_index_pattern,
    )

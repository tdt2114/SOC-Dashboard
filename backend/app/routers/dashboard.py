from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.exceptions import UpstreamServiceError
from app.db.session import get_db_session
from app.schemas.dashboard import DashboardSummaryResponse
from app.services.auth import get_current_user_model_from_token
from app.services.dashboard import get_dashboard_summary

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])
bearer_scheme = HTTPBearer(auto_error=False)


@router.get("/summary", response_model=DashboardSummaryResponse)
async def get_summary(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> DashboardSummaryResponse:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    current_user = await get_current_user_model_from_token(session, credentials.credentials)
    try:
        return await get_dashboard_summary(session, current_user, settings)
    except UpstreamServiceError as exc:
        raise HTTPException(status_code=502, detail=f"{exc.service} unavailable: {exc.message}") from exc

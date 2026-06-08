from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.schemas.ai import AiAnalysisResponse
from app.services.ai_analyst import analyze_alert, get_cached_alert_analysis
from app.services.auth import WORKFLOW_ROLES, get_current_user_model_from_token, require_user_roles

router = APIRouter(prefix="/api/alerts", tags=["ai"])
bearer_scheme = HTTPBearer(auto_error=False)


async def _workflow_user(credentials: HTTPAuthorizationCredentials | None, session: AsyncSession):
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    user = await get_current_user_model_from_token(session, credentials.credentials)
    return require_user_roles(user, WORKFLOW_ROLES, detail="AI analysis requires analyst or admin access")


@router.post("/{alert_id}/ai-analyze", response_model=AiAnalysisResponse)
async def analyze_alert_route(
    alert_id: str,
    force: bool = False,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    session: AsyncSession = Depends(get_db_session),
) -> AiAnalysisResponse:
    user = await _workflow_user(credentials, session)
    return await analyze_alert(session, user, alert_id, force=force)


@router.get("/{alert_id}/ai-analysis", response_model=AiAnalysisResponse)
async def get_alert_analysis_route(
    alert_id: str,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    session: AsyncSession = Depends(get_db_session),
) -> AiAnalysisResponse:
    await _workflow_user(credentials, session)
    return await get_cached_alert_analysis(session, alert_id)

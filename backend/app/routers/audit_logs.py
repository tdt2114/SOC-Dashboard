from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.schemas.audit import AuditLogListResponse
from app.services.audit_logs import list_audit_logs
from app.services.auth import get_current_user_model_from_token
from app.services.users import require_superadmin_user

router = APIRouter(prefix="/api/audit-logs", tags=["audit-logs"])
bearer_scheme = HTTPBearer(auto_error=False)


@router.get("", response_model=AuditLogListResponse)
async def get_audit_logs(
    action: str | None = Query(default=None),
    q: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    session: AsyncSession = Depends(get_db_session),
) -> AuditLogListResponse:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    current_user = await get_current_user_model_from_token(session, credentials.credentials)
    await require_superadmin_user(current_user)
    return await list_audit_logs(session, action=action, q=q, page=page, page_size=page_size)

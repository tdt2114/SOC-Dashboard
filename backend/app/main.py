from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.db.session import check_database
from app.routers import agents, alerts, audit_logs, auth, users

settings = get_settings()

app = FastAPI(
    title="SOC Dashboard API",
    version="0.1.0",
    description="Repo B backend for consuming Wazuh alerts and agent metadata.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(alerts.router)
app.include_router(agents.router)
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(audit_logs.router)


@app.get("/health")
async def health() -> dict[str, str]:
    db_ok = await check_database()
    return {
        "status": "ok" if db_ok else "degraded",
        "mode": "mock" if settings.mock_mode else "live",
        "database": "ok" if db_ok else "unavailable",
    }

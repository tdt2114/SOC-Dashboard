from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class AiAnalysisResponse(BaseModel):
    id: int
    entity_type: str
    entity_ref: str
    model: str
    prompt_version: str
    summary: str
    attacker_intent: str | None = None
    mitre: list[str] | None = None
    recommended_action: str | None = None
    should_block: bool | None = None
    confidence: int | None = None
    created_by_user_id: int | None = None
    created_at: datetime
    updated_at: datetime

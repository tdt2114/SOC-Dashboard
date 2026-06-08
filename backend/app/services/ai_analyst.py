from __future__ import annotations

import json

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.exceptions import UpstreamServiceError
from app.db.models import AiAnalysis, Case, PendingAction, User
from app.schemas.ai import AiAnalysisResponse
from app.schemas.alerts import AlertDetail
from app.schemas.cases import CaseDetailResponse
from app.services.ai_providers import get_provider
from app.services.audit import write_audit_log
from app.services.cases import get_case
from app.services.indexer import IndexerClient
from app.services.mock_data import MockDataService

PROMPT_VERSION = "v1"
MAX_LOG_CHARS = 1500
ALLOWED_ACTIONS = {"block_ip", "isolate_host", "kill_process", "monitor", "none"}

_JSON_SCHEMA_HINT = (
    "Trả về DUY NHẤT một JSON (không markdown, không giải thích) theo schema:\n"
    '{"summary": string (tiếng Việt, 2-3 câu), "attacker_intent": string, '
    '"mitre": string[] (mã ATT&CK), "recommended_action": '
    '"block_ip"|"isolate_host"|"kill_process"|"monitor"|"none", '
    '"should_block": boolean, "confidence": integer 0-100}\n\n'
)


def _alert_client(settings: Settings):
    return MockDataService() if settings.mock_mode else IndexerClient(settings)


def _serialize(item: AiAnalysis) -> AiAnalysisResponse:
    mitre = item.mitre if isinstance(item.mitre, list) else None
    return AiAnalysisResponse(
        id=item.id,
        entity_type=item.entity_type,
        entity_ref=item.entity_ref,
        model=item.model,
        prompt_version=item.prompt_version,
        summary=item.summary,
        attacker_intent=item.attacker_intent,
        mitre=mitre,
        recommended_action=item.recommended_action,
        should_block=item.should_block,
        confidence=item.confidence,
        created_by_user_id=item.created_by_user_id,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


def _build_alert_prompt(alert: AlertDetail) -> str:
    full_log = ""
    if isinstance(alert.raw, dict):
        full_log = str(alert.raw.get("full_log", ""))[:MAX_LOG_CHARS]
    return (
        "Bạn là chuyên gia SOC. Phân tích cảnh báo bảo mật dưới đây. " + _JSON_SCHEMA_HINT
        + "Cảnh báo:\n"
        f"- rule.id: {alert.rule.id}\n"
        f"- rule.level: {alert.rule.level}\n"
        f"- rule.description: {alert.rule.description}\n"
        f"- agent: {alert.agent.name} ({alert.agent.id})\n"
        f"- srcip: {alert.source.srcip}\n"
        f"- file.path: {alert.file.path}\n"
        f"- full_log: {full_log}\n"
    )


def _build_pending_action_prompt(action: PendingAction) -> str:
    return (
        "Bạn là chuyên gia SOC. Một hành động phản hồi (active response) đang chờ phê duyệt. "
        "Đánh giá rủi ro và đưa khuyến nghị nên duyệt (should_block) hay không. " + _JSON_SCHEMA_HINT
        + "Hành động chờ duyệt:\n"
        f"- action_type: {action.action_type}\n"
        f"- command: {action.command}\n"
        f"- target_agent_id: {action.target_agent_id}\n"
        f"- rule_id: {action.rule_id}\n"
        f"- alert_id: {action.alert_id}\n"
        f"- reason: {action.reason}\n"
    )


def _build_case_prompt(case: CaseDetailResponse) -> str:
    alert_ids = ", ".join(a.alert_id for a in case.alerts) or "none"
    comments = " | ".join(c.body for c in case.comments)[:1000]
    return (
        "Bạn là chuyên gia SOC. Tóm tắt và đánh giá hồ sơ điều tra (case) dưới đây. " + _JSON_SCHEMA_HINT
        + "Case:\n"
        f"- title: {case.title}\n"
        f"- status/severity: {case.status} / {case.severity}\n"
        f"- description: {case.description}\n"
        f"- linked alerts: {alert_ids}\n"
        f"- comments: {comments}\n"
    )


def _parse_json(text: str) -> dict:
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start, end = text.find("{"), text.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(text[start : end + 1])
            except json.JSONDecodeError:
                pass
    raise UpstreamServiceError("ai", "Could not parse AI JSON output")


def _coerce(parsed: dict) -> dict:
    action = parsed.get("recommended_action")
    if action not in ALLOWED_ACTIONS:
        action = None
    mitre = parsed.get("mitre")
    if not isinstance(mitre, list):
        mitre = None
    else:
        mitre = [str(m) for m in mitre][:10]
    confidence = parsed.get("confidence")
    try:
        confidence = max(0, min(100, int(confidence)))
    except (TypeError, ValueError):
        confidence = None
    return {
        "summary": str(parsed.get("summary") or "").strip() or "No summary returned.",
        "attacker_intent": (str(parsed.get("attacker_intent")).strip() or None)
        if parsed.get("attacker_intent") is not None
        else None,
        "mitre": mitre,
        "recommended_action": action,
        "should_block": bool(parsed["should_block"]) if "should_block" in parsed else None,
        "confidence": confidence,
    }


async def _get_cached(session: AsyncSession, entity_type: str, entity_ref: str) -> AiAnalysis | None:
    result = await session.execute(
        select(AiAnalysis).where(
            AiAnalysis.entity_type == entity_type, AiAnalysis.entity_ref == entity_ref
        )
    )
    return result.scalar_one_or_none()


def _require_enabled(settings: Settings) -> None:
    if not settings.ai_enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI analysis is disabled (set AI_ENABLED=true).",
        )


async def _run_and_store(
    session: AsyncSession,
    actor_user: User,
    *,
    entity_type: str,
    entity_ref: str,
    prompt: str,
    settings: Settings,
) -> AiAnalysisResponse:
    provider = get_provider(settings)
    try:
        fields = _coerce(_parse_json(await provider.generate(prompt)))
    except UpstreamServiceError as exc:
        raise HTTPException(status_code=502, detail=f"AI provider error: {exc.message}") from exc

    cached = await _get_cached(session, entity_type, entity_ref)
    if cached is None:
        cached = AiAnalysis(entity_type=entity_type, entity_ref=entity_ref)
        session.add(cached)
    cached.model = provider.model
    cached.prompt_version = PROMPT_VERSION
    cached.summary = fields["summary"]
    cached.attacker_intent = fields["attacker_intent"]
    cached.mitre = fields["mitre"]
    cached.recommended_action = fields["recommended_action"]
    cached.should_block = fields["should_block"]
    cached.confidence = fields["confidence"]
    cached.raw = {"provider": provider.name}
    cached.created_by_user_id = actor_user.id
    await session.flush()

    await write_audit_log(
        session,
        action="ai.analyzed",
        entity_type="ai_analysis",
        entity_id=cached.id,
        actor_user_id=actor_user.id,
        details={"entity": f"{entity_type}:{entity_ref}", "model": provider.model,
                 "recommended_action": fields["recommended_action"]},
    )
    await session.commit()
    return _serialize(await _get_cached(session, entity_type, entity_ref))


async def _get_cached_or_404(session: AsyncSession, entity_type: str, entity_ref: str) -> AiAnalysisResponse:
    item = await _get_cached(session, entity_type, entity_ref)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No AI analysis yet")
    return _serialize(item)


# ----- Alerts -----

async def analyze_alert(session: AsyncSession, actor_user: User, alert_id: str, *,
                        force: bool = False, settings: Settings | None = None) -> AiAnalysisResponse:
    settings = settings or get_settings()
    _require_enabled(settings)
    cached = await _get_cached(session, "alert", alert_id)
    if cached is not None and not force:
        return _serialize(cached)

    client = _alert_client(settings)
    try:
        alert = await client.get_alert(alert_id)
    except UpstreamServiceError as exc:
        raise HTTPException(status_code=502, detail=f"{exc.service} unavailable: {exc.message}") from exc
    if alert is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")

    return await _run_and_store(session, actor_user, entity_type="alert", entity_ref=alert_id,
                                prompt=_build_alert_prompt(alert), settings=settings)


async def get_cached_alert_analysis(session: AsyncSession, alert_id: str) -> AiAnalysisResponse:
    return await _get_cached_or_404(session, "alert", alert_id)


# ----- Pending actions (SOAR approval assist) -----

async def analyze_pending_action(session: AsyncSession, actor_user: User, token: str, *,
                                 force: bool = False, settings: Settings | None = None) -> AiAnalysisResponse:
    settings = settings or get_settings()
    _require_enabled(settings)
    cached = await _get_cached(session, "pending_action", token)
    if cached is not None and not force:
        return _serialize(cached)

    result = await session.execute(select(PendingAction).where(PendingAction.token == token))
    action = result.scalar_one_or_none()
    if action is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pending action not found")

    return await _run_and_store(session, actor_user, entity_type="pending_action", entity_ref=token,
                                prompt=_build_pending_action_prompt(action), settings=settings)


async def get_cached_pending_action_analysis(session: AsyncSession, token: str) -> AiAnalysisResponse:
    return await _get_cached_or_404(session, "pending_action", token)


# ----- Cases -----

async def summarize_case(session: AsyncSession, actor_user: User, case_id: int, *,
                         force: bool = False, settings: Settings | None = None) -> AiAnalysisResponse:
    settings = settings or get_settings()
    _require_enabled(settings)
    ref = str(case_id)
    cached = await _get_cached(session, "case", ref)
    if cached is not None and not force:
        return _serialize(cached)

    case = await get_case(session, case_id)  # raises 404 if missing
    return await _run_and_store(session, actor_user, entity_type="case", entity_ref=ref,
                                prompt=_build_case_prompt(case), settings=settings)


async def get_cached_case_analysis(session: AsyncSession, case_id: int) -> AiAnalysisResponse:
    return await _get_cached_or_404(session, "case", str(case_id))

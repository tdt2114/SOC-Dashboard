from __future__ import annotations

from app.core.config import Settings
from app.services.ai_providers.base import AiProvider
from app.services.ai_providers.gemini import GeminiProvider
from app.services.ai_providers.mock import MockProvider


def get_provider(settings: Settings) -> AiProvider:
    """Pick a provider: real Gemini when a key is set, otherwise the offline mock.

    The AI_ENABLED gate is enforced by the caller; this only selects the backend.
    """
    if settings.gemini_api_key:
        return GeminiProvider(settings)
    return MockProvider()


__all__ = ["AiProvider", "GeminiProvider", "MockProvider", "get_provider"]

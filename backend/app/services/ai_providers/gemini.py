from __future__ import annotations

import httpx

from app.core.config import Settings
from app.core.exceptions import UpstreamServiceError
from app.services.ai_providers.base import AiProvider


class GeminiProvider(AiProvider):
    """Google Gemini provider (default cloud model).

    Asks the model for JSON output; the caller parses it.
    """

    name = "gemini"

    def __init__(self, settings: Settings) -> None:
        self._key = settings.gemini_api_key
        self.model = settings.ai_model
        self._timeout = settings.ai_timeout_seconds

    async def generate(self, prompt: str) -> str:
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"
            f"?key={self._key}"
        )
        body = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"responseMimeType": "application/json", "temperature": 0.2},
        }
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.post(url, json=body)
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPError as exc:
            raise UpstreamServiceError("gemini", str(exc)) from exc

        try:
            return data["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError, TypeError) as exc:
            raise UpstreamServiceError("gemini", f"unexpected response shape: {data}") from exc

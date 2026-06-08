from __future__ import annotations

from abc import ABC, abstractmethod


class AiProvider(ABC):
    """Minimal provider interface: given a prompt, return the model's text output.

    JSON parsing is done by the caller (ai_analyst) so providers stay thin and
    swappable (Gemini, mock, or a future local/Ollama provider).
    """

    name: str = "base"
    model: str = "base"

    @abstractmethod
    async def generate(self, prompt: str) -> str:  # pragma: no cover - interface
        raise NotImplementedError

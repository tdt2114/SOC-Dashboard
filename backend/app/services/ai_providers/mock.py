from __future__ import annotations

import json
import re

from app.services.ai_providers.base import AiProvider


class MockProvider(AiProvider):
    """Deterministic, offline provider for tests and key-less environments.

    Derives a plausible structured analysis from the prompt via simple keyword
    heuristics so the feature is fully testable without an external API.
    """

    name = "mock"
    model = "mock"

    async def generate(self, prompt: str) -> str:
        text = prompt.lower()
        mitre = re.findall(r"t\d{4}(?:\.\d{3})?", text)
        mitre = [m.upper() for m in dict.fromkeys(mitre)][:5]

        if any(k in text for k in ("ransom", "encrypt", "shadow copy", "inhibit")):
            action, block, intent = "isolate_host", True, "Possible ransomware impact behaviour."
        elif any(k in text for k in ("brute", "failed password", "authentication failure")):
            action, block, intent = "block_ip", True, "Repeated authentication failures — likely brute force."
        elif any(k in text for k in ("mimikatz", "lsass", "credential")):
            action, block, intent = "isolate_host", True, "Credential access / dumping attempt."
        elif any(k in text for k in ("syscheck", "integrity", "fim", "modified")):
            action, block, intent = "monitor", False, "File integrity change — confirm whether expected."
        else:
            action, block, intent = "monitor", False, "Activity needs analyst review."

        payload = {
            "summary": "Mock analysis: cảnh báo được phân loại theo heuristic offline (chưa cấu hình GEMINI_API_KEY).",
            "attacker_intent": intent,
            "mitre": mitre,
            "recommended_action": action,
            "should_block": block,
            "confidence": 60,
        }
        return json.dumps(payload, ensure_ascii=False)

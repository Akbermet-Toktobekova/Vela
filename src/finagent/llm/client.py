"""Provider-independent text generation with deterministic disk caching."""

import hashlib
import json
import os
from pathlib import Path
from typing import Protocol


class LLMClient(Protocol):
    def complete(self, prompt: str) -> str: ...


class FakeLLMClient:
    def complete(self, prompt: str) -> str:
        data = json.loads(prompt)
        if data.get("task") == "select":
            return json.dumps(
                {
                    "id": data["candidates"][0]["candidate"]["id"],
                    "justification": "This supports your priority while preserving your chosen cash buffer.",
                }
            )
        return "I used your current plan to calculate the figures below. You can choose a smaller step or keep things as they are."


class AnthropicLLMClient:
    def __init__(self) -> None:
        import anthropic

        self.client = anthropic.Anthropic()
        self.model = os.getenv("LLM_MODEL", "claude-sonnet-4-20250514")

    def complete(self, prompt: str) -> str:
        import anthropic

        try:
            result = self.client.messages.create(
                model=self.model,
                max_tokens=600,
                temperature=0,
                system="You explain educational financial scenarios. Never calculate. Use only supplied facts. No blame or urgency. For task=select return JSON with id and justification only; select an id from candidates. Otherwise explain supplied tool results without adding numbers. Never provide investment, legal or tax advice.",
                messages=[{"role": "user", "content": prompt}],
            )
            return "".join(b.text for b in result.content if b.type == "text")
        except anthropic.APIError as exc:
            raise RuntimeError("Language provider unavailable") from exc


class CachedLLMClient:
    def __init__(self, client: LLMClient, namespace: str, root: str = ".llm-cache") -> None:
        self.client, self.namespace, self.root = client, namespace, Path(root)

    def complete(self, prompt: str) -> str:
        key = hashlib.sha256((self.namespace + "\n" + prompt).encode()).hexdigest()
        self.root.mkdir(exist_ok=True, parents=True)
        path = self.root / key
        if path.exists():
            return path.read_text()
        response = self.client.complete(prompt)
        path.write_text(response)
        return response


def get_client() -> LLMClient:
    provider = os.getenv("LLM_PROVIDER", "fake")
    if provider not in ("fake", "anthropic"):
        raise ValueError("Unknown LLM_PROVIDER")
    client = AnthropicLLMClient() if provider == "anthropic" else FakeLLMClient()
    return CachedLLMClient(client, provider + ":" + os.getenv("LLM_MODEL", "fake") + ":v1")

"""Opt-in paid provider smoke test. Excluded from normal offline CI."""

import os

import pytest

from finagent.llm.client import AnthropicLLMClient
from finagent.safety.checks import faithful, tone_ok


@pytest.mark.skipif(
    os.getenv("FINAGENT_LIVE_SMOKE") != "1", reason="Explicit live-provider opt-in required"
)
def test_live_provider_smoke():
    reply = AnthropicLLMClient().complete(
        '{"task":"explain","facts":{"amount":1000},"message":"Explain that this is only a scenario without adding numbers."}'
    )
    assert reply and tone_ok(reply) and faithful(reply, {"amount": 1000})

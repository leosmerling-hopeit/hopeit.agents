import sys
from unittest.mock import MagicMock

import pytest

from hopeit_agents.example_tool.api.generate_random import generate_random
from hopeit_agents.example_tool.models import RandomNumberRequest
from hopeit_agents.example_tool.tool import to_mcp_tool

generate_random_module = sys.modules[generate_random.__module__]


@pytest.mark.asyncio
async def test_generate_random_returns_expected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(generate_random_module.random, "randint", lambda *_args, **_kwargs: 7)

    context = MagicMock()
    result = await generate_random(RandomNumberRequest(minimum=0, maximum=10), context)

    assert result.value == 7


def test_to_mcp_tool_schema() -> None:
    tool = to_mcp_tool()

    assert tool.name == "generate-random"
    input_schema = tool.inputSchema or {}
    assert input_schema.get("properties", {}).get("minimum", {}).get("default") == 0
    output_schema = tool.outputSchema or {}
    value_schema = output_schema.get("properties", {}).get("value", {})
    assert value_schema.get("type") == "integer"

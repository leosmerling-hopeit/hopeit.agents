from __future__ import annotations

from collections.abc import AsyncIterator, Awaitable
from contextlib import asynccontextmanager
from types import SimpleNamespace
from typing import Any

import pytest

from hopeit.agents.mcp_bridge.client import MCPBridgeClient, MCPBridgeError
from hopeit.agents.mcp_bridge.models import (
    BridgeConfig,
    ToolDescriptor,
    ToolExecutionStatus,
    ToolInvocation,
)
from hopeit.agents.mcp_bridge.settings import build_environment


@pytest.mark.asyncio
async def test_list_tools_returns_descriptors(monkeypatch: pytest.MonkeyPatch) -> None:
    config = BridgeConfig(command="python")
    client = MCPBridgeClient(config=config)

    async def fake_wait_for(coro: Awaitable[Any], *_args: Any, **_kwargs: Any) -> Any:
        return await coro

    class _FakeTool:
        def __init__(self) -> None:
            self.name = "random"
            self.description = "Generate random"

            def _model_dump(*, mode: str = "json") -> dict[str, Any]:
                _ = mode
                return {"type": "object"}

            self.inputSchema = SimpleNamespace(model_dump=_model_dump)
            self.metadata = {"category": "demo"}

    class _FakeSession:
        async def list_tools(self) -> SimpleNamespace:
            return SimpleNamespace(tools=[_FakeTool()])

    @asynccontextmanager
    async def fake_session(_self: MCPBridgeClient) -> AsyncIterator[_FakeSession]:
        yield _FakeSession()

    monkeypatch.setattr(
        "hopeit.agents.mcp_bridge.client.asyncio.wait_for",
        fake_wait_for,
    )
    monkeypatch.setattr(MCPBridgeClient, "_session", fake_session)

    tools = await client.list_tools()

    assert tools[0].name == "random"
    assert tools[0].metadata["category"] == "demo"


@pytest.mark.asyncio
async def test_call_tool_returns_success(monkeypatch: pytest.MonkeyPatch) -> None:
    config = BridgeConfig(command="python")
    client = MCPBridgeClient(config=config)

    async def fake_wait_for(coro: Awaitable[Any], *_args: Any, **_kwargs: Any) -> Any:
        return await coro

    async def fake_list_tools(_self: MCPBridgeClient) -> list[ToolDescriptor]:
        return [ToolDescriptor(name="echo", description=None, input_schema=None)]

    class _FakeContent:
        def __init__(self, text: str) -> None:
            self.text = text

        def model_dump(self, mode: str = "json") -> dict[str, Any]:
            _ = mode
            return {"type": "text", "text": self.text}

    class _FakeResult:
        def __init__(self) -> None:
            self.content = [_FakeContent("ok")]
            self.structuredContent = {"value": 42}
            self.isError = False

        def model_dump(self, mode: str = "json") -> dict[str, Any]:
            _ = mode
            return {"content": [c.model_dump() for c in self.content]}

    class _FakeSession:
        async def call_tool(self, *_args: Any, **_kwargs: Any) -> _FakeResult:
            return _FakeResult()

    @asynccontextmanager
    async def fake_session(_self: MCPBridgeClient) -> AsyncIterator[_FakeSession]:
        yield _FakeSession()

    monkeypatch.setattr(
        "hopeit.agents.mcp_bridge.client.asyncio.wait_for",
        fake_wait_for,
    )
    monkeypatch.setattr(MCPBridgeClient, "_session", fake_session)
    monkeypatch.setattr(MCPBridgeClient, "list_tools", fake_list_tools)

    result = await client.call_tool(ToolInvocation(tool_name="echo"))

    assert result.status is ToolExecutionStatus.SUCCESS
    assert result.content[0]["text"] == "ok"
    assert result.structured_content == {"value": 42}


@pytest.mark.asyncio
async def test_call_tool_raises_when_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    config = BridgeConfig(command="python")
    client = MCPBridgeClient(config=config)

    async def fake_list_tools(_self: MCPBridgeClient) -> list[ToolDescriptor]:
        return []

    monkeypatch.setattr(MCPBridgeClient, "list_tools", fake_list_tools)

    with pytest.raises(MCPBridgeError) as err:
        await client.call_tool(ToolInvocation(tool_name="ghost"))

    assert err.value.details == {"status": 404}


def test_build_environment_resolves_placeholders() -> None:
    config = BridgeConfig(
        command="python",
        env={
            "API_KEY": "${SECRET_KEY}",
            "STATIC": "value",
        },
    )

    env = build_environment(config, {"SECRET_KEY": "super"})

    assert env["API_KEY"] == "super"
    assert env["STATIC"] == "value"

import sys
from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any

import pytest

from agent_example.events.run_agent import AgentRequest, run_agent
from hopeit.agents.mcp_bridge.models import ToolExecutionResult, ToolExecutionStatus
from hopeit.agents.model_client.models import (
    CompletionResponse,
    Message,
    Role,
    ToolCall,
    Usage,
)

run_agent_module = sys.modules[run_agent.__module__]


@pytest.mark.asyncio
async def test_run_agent_without_tools(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_generate(request: Any, context: Any) -> CompletionResponse:
        message = Message(role=Role.ASSISTANT, content="Hello!")
        conversation = request.conversation.with_message(message)
        return CompletionResponse(
            response_id="cmpl-1",
            model="mock",
            created_at=datetime.now(UTC),
            message=message,
            tool_calls=[],
            conversation=conversation,
            usage=Usage(prompt_tokens=10, completion_tokens=5, total_tokens=15),
            finish_reason="stop",
        )

    monkeypatch.setattr(run_agent_module.model_generate, "generate", fake_generate)

    context = SimpleNamespace(settings={"agent": {"system_prompt": "You help."}}, env={})

    response = await run_agent(
        AgentRequest(agent_id="a1", user_message="Hi"),
        context,  # type: ignore[arg-type]
    )

    assert response.assistant_message.content == "Hello!"
    assert len(response.tool_results) == 0
    assert response.conversation.messages[0].role is Role.SYSTEM


@pytest.mark.asyncio
async def test_run_agent_with_tool(monkeypatch: pytest.MonkeyPatch) -> None:
    tool_call = ToolCall(call_id="call-1", name="random", arguments={})

    async def fake_generate(request: Any, context: Any) -> CompletionResponse:
        assistant = Message(role=Role.ASSISTANT, content="Using tool")
        conversation = request.conversation.with_message(assistant)
        return CompletionResponse(
            response_id="cmpl-2",
            model="mock",
            created_at=datetime.now(UTC),
            message=assistant,
            tool_calls=[tool_call],
            conversation=conversation,
            usage=None,
            finish_reason="tool_calls",
        )

    async def fake_invoke(invocation: Any, context: Any) -> ToolExecutionResult:
        return ToolExecutionResult(
            tool_name=invocation.tool_name,
            status=ToolExecutionStatus.SUCCESS,
            content=[{"value": 42}],
            structured_content={"value": 42},
            error_message=None,
            raw_result={"content": [{"value": 42}]},
        )

    monkeypatch.setattr(run_agent_module.model_generate, "generate", fake_generate)
    monkeypatch.setattr(run_agent_module.bridge_invoke_tool, "invoke_tool", fake_invoke)

    context = SimpleNamespace(
        settings={"agent": {"system_prompt": "You help."}},
        env={},
    )

    response = await run_agent(
        AgentRequest(agent_id="a1", user_message="Hi"),
        context,  # type: ignore[arg-type]
    )

    assert response.tool_results[0].status is ToolExecutionStatus.SUCCESS
    assert response.conversation.messages[-1].role is Role.TOOL
    assert "42" in response.conversation.messages[-1].content

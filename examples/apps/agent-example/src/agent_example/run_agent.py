"""Run an agent conversation combining model completions and MCP tool calls."""

import json
from typing import Any

from hopeit.app.api import event_api
from hopeit.app.context import EventContext
from hopeit.app.logger import app_extra_logger
from hopeit.dataobjects import dataclass, dataobject, field

from agent_example.settings import AgentSettings
from hopeit_agents.mcp_bridge.api import invoke_tool as bridge_invoke_tool
from hopeit_agents.mcp_bridge.models import ToolExecutionResult, ToolInvocation
from hopeit_agents.model_client.api import generate as model_generate
from hopeit_agents.model_client.models import (
    CompletionRequest,
    Conversation,
    Message,
    Role,
    ToolCall,
)

logger, extra = app_extra_logger()


@dataobject
@dataclass
class AgentRequest:
    """Incoming agent instruction."""

    agent_id: str
    user_message: str
    conversation: Conversation | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataobject
@dataclass
class AgentResponse:
    """Agent execution output."""

    agent_id: str
    conversation: Conversation
    assistant_message: Message
    tool_results: list[ToolExecutionResult] = field(default_factory=list)


__steps__ = ["run_agent"]

__api__ = event_api(
    summary="agent-example: run agent",
    payload=(AgentRequest, "Agent task description"),
    responses={
        200: (AgentResponse, "Aggregated agent response"),
    },
)


async def run_agent(payload: AgentRequest, context: EventContext) -> AgentResponse:
    """Execute the agent loop: model completion, optional tool calls."""
    agent_settings = context.settings(key="agent", datatype=AgentSettings)
    conversation = _build_conversation(payload, agent_settings)

    model_request = CompletionRequest(conversation=conversation)
    completion = await model_generate.generate(model_request, context)
    conversation = completion.conversation

    tool_results: list[ToolExecutionResult] = []

    if agent_settings.enable_tools and completion.tool_calls:
        for tool_call in completion.tool_calls:
            result = await _execute_tool(tool_call, payload.agent_id, context)
            tool_results.append(result)
            conversation = conversation.with_message(
                Message(
                    role=Role.TOOL,
                    content=_format_tool_result(result),
                    tool_call_id=tool_call.call_id,
                ),
            )

    response = AgentResponse(
        agent_id=payload.agent_id,
        conversation=conversation,
        assistant_message=completion.message,
        tool_results=tool_results,
    )

    logger.info(
        context,
        "agent_run_completed",
        extra=extra(
            agent_id=payload.agent_id,
            tool_count=len(tool_results),
            finish_reason=completion.finish_reason,
        ),
    )
    return response


def _build_conversation(payload: AgentRequest, settings: AgentSettings) -> Conversation:
    base_messages = list(payload.conversation.messages) if payload.conversation else []
    if not base_messages and settings.system_prompt:
        base_messages.append(Message(role=Role.SYSTEM, content=settings.system_prompt))
    base_messages.append(Message(role=Role.USER, content=payload.user_message))
    return Conversation(messages=base_messages)


async def _execute_tool(
    tool_call: ToolCall,
    agent_id: str,
    context: EventContext,
) -> ToolExecutionResult:
    invocation = ToolInvocation(
        tool_name=tool_call.name,
        arguments=tool_call.arguments,
        session_id=agent_id,
    )
    result = await bridge_invoke_tool.invoke_tool(invocation, context)
    return result


def _format_tool_result(result: ToolExecutionResult) -> str:
    if result.raw_result is not None:
        return json.dumps(result.raw_result, indent=2)
    if result.structured_content is not None:
        return json.dumps(result.structured_content, indent=2)
    return json.dumps(result.content, indent=2)

"""Run an agent conversation combining model completions and MCP tool calls."""

import json
from typing import Any

from hopeit.app.api import event_api
from hopeit.app.context import EventContext
from hopeit.app.logger import app_extra_logger
from hopeit.dataobjects import dataclass, dataobject, field

from agent_example.settings import AgentSettings
from hopeit_agents.mcp_bridge.api import (
    invoke_tool as bridge_invoke_tool,
)
from hopeit_agents.mcp_bridge.api import (
    list_tools as bridge_list_tools,
)
from hopeit_agents.mcp_bridge.client import MCPBridgeError
from hopeit_agents.mcp_bridge.models import (
    ToolDescriptor,
    ToolExecutionResult,
    ToolInvocation,
)
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
    tool_prompt = await _resolve_tool_prompt(agent_settings, context, payload.agent_id)
    conversation = _build_conversation(payload, agent_settings, tool_prompt)

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


def _build_conversation(
    payload: AgentRequest,
    settings: AgentSettings,
    tool_prompt: str | None,
) -> Conversation:
    base_messages = list(payload.conversation.messages) if payload.conversation else []
    if not base_messages:
        system_parts: list[str] = []
        if settings.system_prompt:
            system_parts.append(settings.system_prompt.strip())
        if tool_prompt:
            system_parts.append(tool_prompt)
        if system_parts:
            base_messages.append(
                Message(
                    role=Role.SYSTEM, content="\n\n".join(part for part in system_parts if part)
                )
            )
    base_messages.append(Message(role=Role.USER, content=payload.user_message))
    return Conversation(messages=base_messages)


async def _resolve_tool_prompt(
    settings: AgentSettings,
    context: EventContext,
    agent_id: str,
) -> str | None:
    if not settings.enable_tools or not settings.tool_prompt_template:
        return None

    try:
        tools = await bridge_list_tools.list_tools(None, context)
    except MCPBridgeError as exc:
        logger.warning(
            context,
            "agent_tool_prompt_list_failed",
            extra=extra(agent_id=agent_id, error=str(exc), details=exc.details),
        )
        return None
    except Exception as exc:  # pragma: no cover - defensive guardrail
        logger.warning(
            context,
            "agent_tool_prompt_unexpected_error",
            extra=extra(agent_id=agent_id, error=repr(exc)),
        )
        return None

    prompt = _build_tool_prompt(tools, settings)
    return prompt


def _build_tool_prompt(tools: list[ToolDescriptor], settings: AgentSettings) -> str | None:
    if not tools:
        return None

    template = settings.tool_prompt_template
    if not template:
        return None

    tool_descriptions = _format_tool_descriptions(
        tools,
        include_schemas=settings.include_tool_schemas_in_prompt,
    )
    if not tool_descriptions:
        return None

    try:
        prompt = template.format(tool_descriptions=tool_descriptions)
    except (IndexError, KeyError, ValueError):
        prompt = f"{template}\n{tool_descriptions}"
    return prompt.strip()


def _format_tool_descriptions(
    tools: list[ToolDescriptor],
    *,
    include_schemas: bool,
) -> str:
    lines: list[str] = []
    for tool in tools:
        description = (tool.description or "No description provided.").strip()
        lines.append(f"- {tool.name}: {description}")
        if include_schemas and tool.input_schema:
            schema = json.dumps(tool.input_schema, indent=2, sort_keys=True)
            lines.append("  JSON schema:")
            lines.extend(f"    {schema_line}" for schema_line in schema.splitlines())
    return "\n".join(lines).strip()


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

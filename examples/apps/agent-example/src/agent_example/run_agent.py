"""Run an agent conversation combining model completions and MCP tool calls."""

import json
from typing import Any

from hopeit.app.api import event_api
from hopeit.app.context import EventContext
from hopeit.app.logger import app_extra_logger
from hopeit.dataobjects import dataclass, dataobject, field

from agent_example.settings import AgentSettings
from hopeit_agents.mcp_bridge.agent_tooling import (
    ToolCallRecord,
)
from hopeit_agents.mcp_bridge.agent_tooling import (
    execute_tool_calls as bridge_execute_tool_calls,
)
from hopeit_agents.mcp_bridge.agent_tooling import (
    resolve_tool_prompt as bridge_resolve_tool_prompt,
)
from hopeit_agents.mcp_bridge.models import ToolExecutionResult
from hopeit_agents.model_client.api import generate as model_generate
from hopeit_agents.model_client.conversation import build_conversation
from hopeit_agents.model_client.models import CompletionRequest, Conversation, Message, Role

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
    tool_calls: list[ToolCallRecord] = field(default_factory=list)


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
    tool_prompt = await bridge_resolve_tool_prompt(
        context,
        agent_id=payload.agent_id,
        enable_tools=agent_settings.enable_tools,
        template=agent_settings.tool_prompt_template,
        include_schemas=agent_settings.include_tool_schemas_in_prompt,
    )
    conversation = build_conversation(
        payload.conversation,
        user_message=payload.user_message,
        system_prompt=agent_settings.system_prompt,
        tool_prompt=tool_prompt,
    )

    model_request = CompletionRequest(conversation=conversation)
    completion = await model_generate.generate(model_request, context)
    conversation = completion.conversation

    tool_call_records: list[ToolCallRecord] = []

    if agent_settings.enable_tools and completion.tool_calls:
        tool_call_records = await bridge_execute_tool_calls(
            context,
            tool_calls=completion.tool_calls,
            session_id=payload.agent_id,
        )

        for record in tool_call_records:
            conversation = conversation.with_message(
                Message(
                    role=Role.TOOL,
                    content=_format_tool_result(record.response),
                    tool_call_id=record.request.tool_call_id,
                ),
            )

    response = AgentResponse(
        agent_id=payload.agent_id,
        conversation=conversation,
        assistant_message=completion.message,
        tool_calls=tool_call_records,
    )

    logger.info(
        context,
        "agent_run_completed",
        extra=extra(
            agent_id=payload.agent_id,
            tool_call_count=len(tool_call_records),
            tool_calls=[
                {
                    "tool_call_id": record.request.tool_call_id,
                    "tool_name": record.request.tool_name,
                    "status": record.response.status.value,
                }
                for record in tool_call_records
            ],
            finish_reason=completion.finish_reason,
        ),
    )
    return response


def _format_tool_result(result: ToolExecutionResult) -> str:
    if result.raw_result is not None:
        return json.dumps(result.raw_result, indent=2)
    if result.structured_content is not None:
        return json.dumps(result.structured_content, indent=2)
    return json.dumps(result.content, indent=2)

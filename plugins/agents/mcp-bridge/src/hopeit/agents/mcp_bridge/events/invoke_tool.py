"""Invoke an MCP tool and return its result."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, cast

from hopeit.app.api import event_api
from hopeit.app.context import EventContext
from hopeit.app.logger import app_extra_logger

from hopeit.agents.mcp_bridge.client import MCPBridgeClient, MCPBridgeError
from hopeit.agents.mcp_bridge.models import ToolExecutionResult, ToolInvocation
from hopeit.agents.mcp_bridge.settings import build_environment, load_settings

__steps__ = ["invoke_tool"]

__api__ = event_api(
    summary="hopeit.agents MCP bridge: invoke tool",
    payload=(ToolInvocation, "Tool invocation payload"),
    responses={
        200: (ToolExecutionResult, "Tool execution result"),
        404: (str, "Tool not found"),
        500: (str, "MCP bridge error"),
    },
)

logger, extra = app_extra_logger()


async def invoke_tool(payload: ToolInvocation, context: EventContext) -> ToolExecutionResult:
    """Invoke the requested tool using MCP."""
    settings_map = cast(Mapping[str, Any], context.settings)
    config = load_settings(settings_map)
    env = build_environment(config, context.env)
    client = MCPBridgeClient(config=config, env=env)

    try:
        result = await client.call_tool(payload)
    except MCPBridgeError as exc:
        logger.error(
            "mcp_invoke_tool_error",
            extra=extra(tool_name=payload.tool_name, details=exc.details),
        )
        raise

    logger.info(
        "mcp_invoke_tool_success",
        extra=extra(tool_name=payload.tool_name, status=result.status.value),
    )
    return result

"""List available MCP tools."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, cast

from hopeit.app.api import event_api
from hopeit.app.context import EventContext
from hopeit.app.logger import app_extra_logger

from hopeit.agents.mcp_bridge.client import MCPBridgeClient, MCPBridgeError
from hopeit.agents.mcp_bridge.models import ToolDescriptor
from hopeit.agents.mcp_bridge.settings import build_environment, load_settings

__steps__ = ["list_tools"]

__api__ = event_api(
    summary="hopeit.agents MCP bridge: list tools",
    responses={
        200: (list[ToolDescriptor], "Available tools"),
        500: (str, "MCP bridge error"),
    },
)

logger, extra = app_extra_logger()


async def list_tools(payload: None, context: EventContext) -> list[ToolDescriptor]:
    """Return tool descriptors using the configured MCP server."""
    settings_map = cast(Mapping[str, Any], context.settings)
    config = load_settings(settings_map)
    env = build_environment(config, context.env)
    client = MCPBridgeClient(config=config, env=env)

    try:
        tools = await client.list_tools()
    except MCPBridgeError as exc:
        logger.error("mcp_list_tools_error", extra=extra(details=exc.details))
        raise

    logger.info("mcp_list_tools_success", extra=extra(tool_count=len(tools)))
    return tools

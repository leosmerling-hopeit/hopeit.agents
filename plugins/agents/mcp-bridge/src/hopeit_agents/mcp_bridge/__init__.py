"""hopeit_agents MCP bridge plugin."""

from hopeit_agents.mcp_bridge.client import MCPBridgeClient, MCPBridgeError
from hopeit_agents.mcp_bridge.models import (
    BridgeConfig,
    ToolDescriptor,
    ToolExecutionResult,
    ToolExecutionStatus,
    ToolInvocation,
)

__all__ = [
    "BridgeConfig",
    "MCPBridgeClient",
    "MCPBridgeError",
    "ToolDescriptor",
    "ToolExecutionResult",
    "ToolExecutionStatus",
    "ToolInvocation",
]

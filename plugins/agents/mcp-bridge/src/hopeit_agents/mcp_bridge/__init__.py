"""hopeit_agents MCP bridge plugin."""

from hopeit_agents.mcp_bridge.client import MCPBridgeClient, MCPBridgeError
from hopeit_agents.mcp_bridge.models import (
    BridgeConfig,
    ToolCallRecord,
    ToolCallRequestLog,
    ToolDescriptor,
    ToolExecutionResult,
    ToolExecutionStatus,
    ToolInvocation,
)

__all__ = [
    "BridgeConfig",
    "MCPBridgeClient",
    "MCPBridgeError",
    "ToolCallRecord",
    "ToolCallRequestLog",
    "ToolDescriptor",
    "ToolExecutionResult",
    "ToolExecutionStatus",
    "ToolInvocation",
]

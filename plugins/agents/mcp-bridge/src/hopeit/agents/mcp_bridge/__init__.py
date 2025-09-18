"""hopeit.agents MCP bridge plugin."""

from .client import MCPBridgeClient, MCPBridgeError
from .models import (
    BridgeConfig,
    ToolDescriptor,
    ToolExecutionResult,
    ToolExecutionStatus,
    ToolInvocation,
)
from .settings import load_settings

__all__ = [
    "BridgeConfig",
    "MCPBridgeClient",
    "MCPBridgeError",
    "ToolDescriptor",
    "ToolExecutionResult",
    "ToolExecutionStatus",
    "ToolInvocation",
    "load_settings",
]

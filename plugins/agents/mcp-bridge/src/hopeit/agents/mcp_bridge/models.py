"""Typed data objects for the MCP bridge plugin."""

from __future__ import annotations

from enum import Enum
from typing import Any

from hopeit.dataobjects import dataclass, dataobject, field


class Transport(str, Enum):
    """Supported MCP transport mechanisms."""

    STDIO = "stdio"


class ToolExecutionStatus(str, Enum):
    """Outcome of a tool invocation."""

    SUCCESS = "success"
    ERROR = "error"


@dataobject
@dataclass
class ToolDescriptor:
    """Describes an MCP tool available in a server."""

    name: str
    description: str | None
    input_schema: dict[str, Any] | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataobject
@dataclass
class ToolInvocation:
    """Payload to invoke a tool."""

    tool_name: str
    arguments: dict[str, Any] = field(default_factory=dict)
    session_id: str | None = None


@dataobject
@dataclass
class ToolExecutionResult:
    """Result of calling a tool through MCP."""

    tool_name: str
    status: ToolExecutionStatus
    content: list[dict[str, Any]] = field(default_factory=list)
    structured_content: dict[str, Any] | list[Any] | None = None
    error_message: str | None = None
    raw_result: dict[str, Any] | None = None


@dataobject
@dataclass
class BridgeConfig:
    """Configuration required to communicate with an MCP server."""

    command: str
    args: list[str] = field(default_factory=list)
    transport: Transport = Transport.STDIO
    env: dict[str, str] = field(default_factory=dict)
    cwd: str | None = None
    tool_cache_seconds: float = 30.0
    list_timeout_seconds: float = 10.0
    call_timeout_seconds: float = 60.0

    def transport_enum(self) -> Transport:
        """Return the transport as enum."""
        if isinstance(self.transport, Transport):
            return self.transport
        return Transport(str(self.transport))

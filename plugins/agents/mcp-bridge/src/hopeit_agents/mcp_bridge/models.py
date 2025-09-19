"""Typed data objects for the MCP bridge plugin."""

from enum import Enum
from typing import Any

from hopeit.dataobjects import dataclass, dataobject, field


class Transport(str, Enum):
    """Supported MCP transport mechanisms."""

    STDIO = "stdio"
    HTTP = "http"


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
class ToolCallRequestLog:
    """Captured request details for a tool call."""

    tool_call_id: str
    tool_name: str
    arguments: dict[str, Any] = field(default_factory=dict)


@dataobject
@dataclass
class ToolCallRecord:
    """Aggregated tool call request and response for logging/telemetry."""

    request: ToolCallRequestLog
    response: ToolExecutionResult


@dataobject
@dataclass
class BridgeConfig:
    """Configuration required to communicate with an MCP server."""

    command: str | None = None
    args: list[str] = field(default_factory=list)
    transport: Transport = Transport.STDIO
    url: str | None = None
    host: str | None = None
    port: int | None = None
    env: dict[str, str] = field(default_factory=dict)
    cwd: str | None = None
    tool_cache_seconds: float = 30.0
    list_timeout_seconds: float = 10.0
    call_timeout_seconds: float = 60.0

    def transport_enum(self) -> Transport:
        """Return the transport as enum."""
        if isinstance(self.transport, Transport):
            return self.transport

        value = str(self.transport)
        if value == "tcp":  # Backwards compatibility for previous configs
            value = Transport.HTTP.value

        return Transport(value)

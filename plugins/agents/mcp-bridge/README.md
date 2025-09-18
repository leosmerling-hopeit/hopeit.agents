# hopeit.agents MCP bridge plugin

This plugin connects hopeit.engine events with tools exposed through the official [Model Context Protocol](https://modelcontextprotocol.io) (MCP) Python SDK by Anthropic.

## Features
- Typed data models mapping MCP tool descriptors and call results.
- Async bridge client that launches MCP servers via stdio using the official SDK.
- Ready-to-use events for listing tools and invoking a specific tool from agent apps.

## Settings example
```json
{
  "settings": {
    "mcp_bridge": {
      "transport": "stdio",
      "command": "uvx",
      "args": ["python", "-m", "my_mcp_server"],
      "env": {
        "PYTHONPATH": "/path/to/project"
      },
      "tool_cache_seconds": 30.0
    }
  }
}
```

## Event usage
```python
from hopeit.app.client import app_call
from hopeit.agents.mcp_bridge.models import ToolInvocation, ToolExecutionResult

result = await app_call(
    "mcp-bridge-conn",
    event="invoke-tool",
    datatype=ToolExecutionResult,
    payload=ToolInvocation(tool_name="random-number"),
    context=context,
)
```

> **Note:** the current implementation supports stdio transports. Additional transports (e.g., WebSocket, Streamable HTTP) can be added by extending `BridgeConfig`.

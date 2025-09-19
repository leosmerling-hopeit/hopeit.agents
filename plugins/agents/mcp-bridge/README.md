# hopeit_agents MCP bridge plugin

This plugin connects hopeit.engine events with tools exposed through the official [Model Context Protocol](https://modelcontextprotocol.io) (MCP) Python SDK by Anthropic.

## Features
- Typed data models mapping MCP tool descriptors and call results.
- Async bridge client that connects to MCP servers via stdio (subprocess) or the official Streamable HTTP transport.
- Ready-to-use events for listing tools and invoking a specific tool from agent apps.
- Sample MCP server at `examples/servers/my_mcp_server` that registers the example `generate-random` tool.

## Settings example
```json
{
  "settings": {
    "mcp_bridge": {
      "transport": "http",
      "url": "http://127.0.0.1:8765/mcp",
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
from hopeit_agents.mcp_bridge.models import ToolInvocation, ToolExecutionResult

result = await app_call(
    "mcp-bridge-conn",
    event="invoke-tool",
    datatype=ToolExecutionResult,
    payload=ToolInvocation(tool_name="random-number"),
    context=context,
)
```

> **Note:** Streamable HTTP and stdio transports are built in. Additional transports (e.g., WebSocket) can be added by extending `BridgeConfig`.

# hopeit.agents example tool plugin

A minimal hopeit.engine plugin exposing an MCP-compatible tool that returns a random integer within a given range. Use it as a template to build custom tools that can be registered in an MCP server and invoked by hopeit.agents apps.

## Tool contract
- **Event**: `generate-random` (POST)
- **Request**: `RandomNumberRequest` with optional `minimum`/`maximum` bounds
- **Response**: `RandomNumberResult` with the generated value

## MCP integration
The helper `example_tool.tool.to_mcp_tool()` returns an `mcp.types.Tool` descriptor ready to be registered in an MCP server implementation. The included tests show how to validate the schema.

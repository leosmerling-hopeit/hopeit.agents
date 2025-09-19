import random

import anyio
from mcp import types
from mcp.server.lowlevel.server import NotificationOptions, Server
from mcp.server.stdio import stdio_server

from hopeit_agents.example_tool.models import RandomNumberRequest
from hopeit_agents.example_tool.tool import to_mcp_tool

SERVER_INSTRUCTIONS = (
    "Expose the hopeit_agents example random number generator as an MCP tool."
)

server = Server(
    name="hopeit-example-tool-server",
    instructions=SERVER_INSTRUCTIONS,
)


@server.list_tools()
async def list_tools() -> list[types.Tool]:
    return [to_mcp_tool()]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, object] | None):
    if name != "generate-random":
        raise ValueError(f"Unknown tool: {name}")

    request = RandomNumberRequest(**(arguments or {}))
    minimum, maximum = request.minimum, request.maximum
    if minimum > maximum:
        minimum, maximum = maximum, minimum

    value = random.randint(minimum, maximum)
    return {"value": value}


async def main() -> None:
    init_options = server.create_initialization_options(
        notification_options=NotificationOptions(tools_changed=False)
    )
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, init_options)


if __name__ == "__main__":
    print("Starting MCP Server...")
    anyio.run(main)
    print("Stopped MCP Server.")

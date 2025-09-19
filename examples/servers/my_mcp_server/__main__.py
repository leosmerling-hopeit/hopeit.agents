import argparse
import random
from typing import Any

import anyio
import uvicorn
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import PlainTextResponse
from starlette.routing import Mount, Route

from mcp import types
from mcp.server.lowlevel.server import NotificationOptions, Server
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
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

# ServerInitializationOptions was removed in recent MCP releases; fall back to Any.
InitOptions = Any

HTTP_ENDPOINT = "/mcp"


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

async def _serve_stdio(init_options: InitOptions) -> None:
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, init_options)


def _create_http_app() -> Starlette:
    session_manager = StreamableHTTPSessionManager(server)

    async def lifespan(_: Starlette):
        async with session_manager.run():
            yield

    async def streamable_http_app(scope, receive, send):
        if scope["type"] == "lifespan":
            await send({"type": "lifespan.startup.complete"})
            await send({"type": "lifespan.shutdown.complete"})
            return

        if scope["type"] != "http":  # pragma: no cover - ignored during HTTP routing
            raise RuntimeError(f"Unsupported scope type: {scope['type']}")
        await session_manager.handle_request(scope, receive, send)

    async def health(_: Request) -> PlainTextResponse:
        return PlainTextResponse("hopeit-example-tool-server")

    return Starlette(
        routes=[
            Route("/", endpoint=health, methods=["GET"]),
            Mount(HTTP_ENDPOINT, app=streamable_http_app),
        ],
        lifespan=lifespan,
    )


def run_stdio() -> None:
    init_options = server.create_initialization_options(
        notification_options=NotificationOptions(tools_changed=False)
    )
    anyio.run(_serve_stdio, init_options)


def run_http(host: str, port: int) -> None:
    app = _create_http_app()
    uvicorn.run(app, host=host, port=port, log_level="info")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the sample MCP server.")
    parser.add_argument(
        "--transport",
        choices=["stdio", "http"],
        default="http",
        help="Transport to expose. Use 'stdio' for compatibility or 'http' for a hosted server.",
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host/IP to bind when using HTTP transport.",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8765,
        help="Port to bind when using HTTP transport.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    if args.transport == "stdio":
        print("Starting MCP Server (transport=stdio, endpoint=stdio).")
        try:
            run_stdio()
        except KeyboardInterrupt:  # pragma: no cover - manual interrupt
            print("Received interruption, shutting down...")
    else:
        endpoint = f"http://{args.host}:{args.port}{HTTP_ENDPOINT}"
        print(f"Starting MCP Server (transport=http, endpoint={endpoint}).")
        try:
            run_http(args.host, args.port)
        except KeyboardInterrupt:  # pragma: no cover - manual interrupt
            print("Received interruption, shutting down...")
    print("Stopped MCP Server.")

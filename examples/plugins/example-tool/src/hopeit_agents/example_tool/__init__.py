"""Example MCP tool plugin."""

from .models import RandomNumberRequest, RandomNumberResult
from .tool import to_mcp_tool

__all__ = ["RandomNumberRequest", "RandomNumberResult", "to_mcp_tool"]

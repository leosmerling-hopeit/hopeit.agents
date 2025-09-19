"""hopeit_agents model client plugin."""

from .client import AsyncModelClient, ModelClientError
from .models import (
    CompletionConfig,
    CompletionRequest,
    CompletionResponse,
    Conversation,
    Message,
    Role,
    ToolCall,
    ToolResult,
    Usage,
)
from .settings import ModelClientSettings

__all__ = [
    "AsyncModelClient",
    "CompletionConfig",
    "CompletionRequest",
    "CompletionResponse",
    "Conversation",
    "Message",
    "ModelClientError",
    "ModelClientSettings",
    "Role",
    "ToolCall",
    "ToolResult",
    "Usage",
]

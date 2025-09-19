"""hopeit_agents model client plugin."""

from .client import AsyncModelClient, ModelClientError
from .conversation import build_conversation
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
    "build_conversation",
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

"""Settings helpers for the agent example app."""

from collections.abc import Mapping
from typing import Any

from hopeit.dataobjects import dataclass, dataobject

SETTINGS_KEY = "agent"


@dataobject
@dataclass
class AgentSettings:
    """Configurable defaults for the example agent."""

    system_prompt: str = "You are a helpful agent built with hopeit_agents."
    enable_tools: bool = True


def load_agent_settings(settings: Mapping[str, Any]) -> AgentSettings:
    """Load agent settings from context settings mapping."""
    raw = settings.get(SETTINGS_KEY, {})
    if isinstance(raw, AgentSettings):
        return raw
    if isinstance(raw, Mapping):
        return AgentSettings(**raw)
    raise TypeError("Agent settings must be a mapping")

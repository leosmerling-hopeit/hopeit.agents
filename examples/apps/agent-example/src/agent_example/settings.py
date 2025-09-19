"""Settings helpers for the agent example app."""

from hopeit.dataobjects import dataclass, dataobject

SETTINGS_KEY = "agent"


@dataobject
@dataclass
class AgentSettings:
    """Configurable defaults for the example agent."""

    system_prompt: str = "You are a helpful agent built with hopeit_agents."
    enable_tools: bool = True

"""Settings helpers for the MCP bridge plugin."""

from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any

from hopeit.dataobjects import dataclass, dataobject

from .models import BridgeConfig

SETTINGS_KEY = "mcp_bridge"
_PLACEHOLDER_RE = re.compile(r"^\$\{(?P<name>[A-Z0-9_]+)\}$")


@dataobject
@dataclass
class MCPBridgeSettings:
    """Wrapper around BridgeConfig for compatibility with hopeit settings."""

    config: BridgeConfig


def load_settings(context_settings: Mapping[str, Any]) -> BridgeConfig:
    """Load configuration from context settings mapping."""
    try:
        raw_settings = context_settings[SETTINGS_KEY]
    except KeyError as exc:
        raise KeyError("Missing 'mcp_bridge' entry in context settings.") from exc

    if isinstance(raw_settings, BridgeConfig):
        return raw_settings
    if isinstance(raw_settings, MCPBridgeSettings):
        return raw_settings.config
    if not isinstance(raw_settings, Mapping):
        raise TypeError(
            f"mcp_bridge settings must be mapping-like, received {type(raw_settings).__name__}",
        )

    bridge_kwargs = dict(raw_settings)
    transport_value = bridge_kwargs.get("transport")
    if transport_value is not None:
        bridge_kwargs["transport"] = transport_value
    return BridgeConfig(**bridge_kwargs)


def build_environment(settings: BridgeConfig, context_env: Mapping[str, Any]) -> dict[str, str]:
    """Resolve environment variables combining config and context env."""
    resolved: dict[str, str] = {}
    for key, value in settings.env.items():
        if isinstance(value, str):
            match = _PLACEHOLDER_RE.match(value)
            if match:
                env_value = context_env.get(match.group("name"))
                if isinstance(env_value, str):
                    resolved[key] = env_value
                continue
        if isinstance(value, (str, int, float)):
            resolved[key] = str(value)
    return resolved

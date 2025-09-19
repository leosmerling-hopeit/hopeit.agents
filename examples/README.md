# hopeit_agents Examples

This repository ships a minimal agent application and a matching MCP-compatible tool to illustrate how to wire `hopeit.engine` plugins together. The steps below assume you have already read the [hopeit.engine tutorials](https://hopeitengine.readthedocs.io/en/latest/) and cover only the additional configuration required for the agents/plugins scenario.

## Prerequisites
- Python 3.12+
- [uv](https://docs.astral.sh/uv/) installed (`pipx install uv` or see the official docs)
- Local checkout of `hopeit_agents`

From the repository root:

```bash
uv sync --all-packages
make install-dev  # installs examples/plugins + examples/apps in editable mode
```

The examples expect `hopeit.engine` to be available in the environment (pulled in automatically through the workspace dependencies).

## Directory Overview
- `examples/plugins/example-tool`: random number MCP tool exposed as a hopeit.plugin
- `examples/apps/agent-example`: agent app demonstrating conversations + tool use

## Step 1 – Configure the Model Client
The agent example calls an OpenAI-compatible chat completion endpoint via `plugins/agents/model-client`.

1. Copy `examples/apps/agent-example/config/app-config.json` to a writable location or set overrides using environment variables.
2. Set the following in your environment (or via the `settings.model_client` section):
   - `AGENT_MODEL_API_BASE`: Base URL (`https://api.openai.com/v1`, `http://localhost:11434/v1` for Ollama, etc.).
   - `OPENAI_API_KEY`: API token accepted by the target service (for Ollama with no auth, leave blank and remove the header in config).
   - Optional headers can be configured in `extra_headers` if the provider expects additional flags (example includes `OpenAI-Beta`).

Example using environment variables:

```bash
export AGENT_MODEL_API_BASE="https://api.openai.com/v1"
export OPENAI_API_KEY="sk-..."
```

For Ollama:
```bash
export AGENT_MODEL_API_BASE="http://localhost:11434/v1"
# remove or comment the Authorization header block in config if credentials are not required
```

## Step 2 – Provide an MCP Server
The bridge plugin now talks to MCP servers using the official Streamable HTTP
transport, so the server can stay alive across requests without custom socket
adapters.

- Configure the connection in `settings.mcp_bridge` (set the `url` and, if
  needed, override `host`/`port` for convenience).
- Start the bundled sample server in a separate terminal:
  ```bash
  uvx python -m examples.servers.my_mcp_server --transport http --host 127.0.0.1 --port 8765
  ```
- If you prefer the legacy stdio behaviour, run the server with
  `--transport stdio` and switch the bridge transport back to `stdio` (restore
  the `command`/`args` in the settings).
- Customize the environment variables (API tokens, `PYTHONPATH`, etc.) using
  `settings.mcp_bridge.env`.

## Step 3 – Run the Example Tool (optional standalone test)
Outside of the full agent flow you can call the tool event directly:

```bash
PYTHONPATH=examples/plugins/example-tool/src uv run pytest examples/plugins/example-tool/test/test_random_tool.py -v
```

## Step 4 – Launch the Agent App
Create an application configuration referencing the plugin:

```bash
cat examples/apps/agent-example/config/app-config.json
```
Adjust the settings discussed above, then run the app using `hopeit.engine`’s CLI:

```bash
uv run hopeit_server run \
  --config-files=server-noauth.json,app-config.json \
  --port=8020 \
  --api-file=examples/apps/agent-example/api/openapi.json
```

The agent exposes a `POST` endpoint at `/agent-example/{version}/run-agent`. Send a JSON payload:

```bash
curl -X POST http://localhost:8020/agent-example/v1/run-agent \
  -H "Content-Type: application/json" \
  -d '{
        "agent_id": "demo-agent",
        "user_message": "Generate a random number"
      }'
```

The response will contain the assistant reply and any tool outputs.

## Troubleshooting
- **401/403 from model provider**: verify `AGENT_MODEL_API_BASE`, headers, and API key.
- **Tool not available**: ensure the MCP server command matches the one configured and that it lists the tool name requested by the model.
- **Connection errors**: check subprocess permissions (stdio transport) and that `uv` can execute the provided command.

For deeper details on app deployment, refer to the [hopeit.engine tutorials](https://hopeitengine.readthedocs.io/en/latest/tutorials/) (server setup, environment overrides, vscode integration, etc.).

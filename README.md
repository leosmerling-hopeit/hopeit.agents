# hopeit.agents

hopeit.engine async GenAI multi-agent framework

## Repository Layout
- `plugins/agents/model-client`: OpenAI-compatible model client plugin providing typed data objects and a `generate` event.
- `plugins/agents/mcp-bridge`: Anthropic MCP bridge for listing and invoking tools via stdio transport.
- `examples/plugins/example-tool`: Sample MCP-compatible tool (random number generator) implemented as a hopeit plugin.
- `examples/apps/agent-example`: Minimal agent app showcasing how to combine the model client and MCP bridge plugins.

## Development Workflow
This repository uses [uv](https://docs.astral.sh/uv/) for dependency management.

```bash
uv sync --all-packages
uv run ruff check
uv run mypy plugins apps
uv run pytest
```

## Continuous Integration
GitHub Actions (`.github/workflows/ci.yml`) runs ruff, mypy (strict mode), and pytest to guarantee code quality and typing coverage across plugins and examples.

## Next Steps
- Configure `config/app-config.json` in the agent example with your model endpoint and MCP server command.
- Use `examples/plugins/example-tool` as a template to expose custom MCP tools consumable by hopeit agents.

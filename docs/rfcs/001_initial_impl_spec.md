# Minimal Implementation Plan for hopeit_agents

## Context Recap
- Reviewed `hopeit.engine` docs, plugin layout, and root `pyproject.toml` to mirror packaging patterns (`pyproject` + `uv` configuration, tests under `test/`).
- Key conventions: use `@dataobject` dataclasses for payloads, async event steps, plugin-specific configuration via app settings, and comprehensive typing enforced by `mypy`.
- Goal: deliver two reusable plugins that let hopeit apps act as AI agents with model calls and MCP tool execution, plus examples showing agent orchestration and custom MCP tools.

## High-Level Milestones
1. **Repo scaffolding** – align project structure with hopeit.engine (`pyproject.toml` using `uv`, shared typing/test config, CI placeholders).
2. **Model client plugin** – minimal OpenAI-compatible client with fully-typed conversation data models and a callable event.
3. **MCP tools plugin** – minimal MCP bridge using Anthropic's official MCP Python library to list and invoke tools.
4. **Example agent app skeleton** – minimal app demonstrating how to compose both plugins (HTTP POST event returning model + tool call result).
5. **Example MCP tool plugin** – show how users can expose MCP-compatible tools as hopeit.engine plugins (e.g., random number generator).
6. **Typing, testing & docs** – enforce type hints everywhere, enable `mypy` (via `uv`) in CI alongside pytest/ruff, and document configuration and usage.

## Detailed Tasks

### 1. Repo Scaffolding
- Create root `pyproject.toml` modeled after hopeit.engine: define workspace metadata, configure `[tool.uv]` sources for each plugin/app, and list shared dev dependencies (include `mypy`, `pytest`, `ruff`, type stubs).
- Add root tooling config: `mypy.ini` or `[tool.mypy]` section with strict-ish settings, `ruff` config, `pytest` options; ensure type coverage expectations are documented.
- Generate `uv` lock/setup files if applicable and document usage commands in README (e.g., `uv run pytest`).
- Establish common `conftest.py` and utilities for tests; ensure type-check friendly fixtures.

### 2. Plugin: `hopeit_agents.model_client`
- **Layout**: `plugins/agents/model-client/{pyproject.toml, README.md, src/hopeit/agents/model_client/...}` plus `test/` mirroring hopeit.engine plugin packaging.
- **Data models** (`models.py`, using `@dataobject` with explicit typing):
  - `Role` enum (`system`, `user`, `assistant`, `tool`).
  - `Message` (role, content, optional `tool_call_id`, typed metadata map).
  - `ToolCall` / `ToolResult` for structured interactions.
  - `Conversation` (ordered `messages`, agent metadata, timestamps) and helper methods with type hints.
  - `CompletionConfig`, `CompletionRequest`, `CompletionResponse` for IO typing.
- **Client abstraction** (`client.py`):
  - Implement `AsyncModelClient` using `aiohttp`, fully typed, returning dataclasses.
  - Support configurable base URL, auth header, timeout, optional streaming; raise typed exceptions.
  - Provide request preparation helpers with clear typing for config merges.
- **hopeit.engine event module** (`events/generate.py`):
  - Steps (`build_request`, `call_model`, `format_response`) each typed, using dataclasses and `EventContext` type hints.
  - Expose POST event returning `CompletionResponse`, with logging/tracing consistent with hopeit.engine.
- **Configuration**: document settings path (`settings.model_client`), secrets resolution, and how defaults merge; ensure typed helpers for settings retrieval.
- **Tests**:
  - Unit tests using typed mocks for `aiohttp.ClientSession` verifying payloads/responses and error paths.
  - Event test with hopeit test utilities, ensuring type-safe fixtures.

### 3. Plugin: `hopeit_agents.mcp_bridge`
- **Layout**: `plugins/agents/mcp-bridge/{pyproject.toml, README.md, src/hopeit/agents/mcp_bridge/...}` plus `test/`.
- **Dependencies**: rely exclusively on Anthropic's official `mcp` Python library; specify extras in `pyproject.toml` / `uv` config.
- **Data models** (`models.py`, typed):
  - `ToolDescriptor`, `ToolInvocation`, `ToolExecutionResult`, `BridgeConfig` with precise types and validation via dataclasses.
- **Client wrapper** (`client.py`):
  - Async helper built atop official MCP APIs (e.g., websockets, stdio) with typed context managers.
  - Expose `list_tools` and `invoke_tool`, caching descriptors, mapping exceptions to custom typed errors.
- **hopeit.engine events**:
  - `list-tools` GET event returning `list[ToolDescriptor]`.
  - `invoke-tool` POST event returning `ToolExecutionResult`.
  - Typed steps for config loading, session management, error mapping to HTTP status codes.
- **Tests**:
  - Mock MCP client interfaces (typed stubs) to simulate responses and failures.
  - Event tests verifying payload validation, type correctness, and error mapping.

### 4. Example Agent App Skeleton
- Layout under `examples/apps/agent-example/` consistent with hopeit.engine examples (`pyproject.toml`, `src/agent_example/...`, `config/`, `test/`).
- Data objects (`AgentRequest`, `AgentResponse`, `AgentState`) defined with `@dataobject` and full typing.
- POST event `run-agent` flow:
  1. Accept typed `AgentRequest`.
  2. Compose `Conversation`, call model client event via `app_call` (typed).
  3. If tools required, call MCP bridge events, append typed `ToolResult`, optionally re-query model.
  4. Return `AgentResponse` capturing messages, tool results, status metadata.
- Provide config showing plugin wiring, with typed settings stubs and OpenAPI snippet.
- Integration test with typed mocks verifying event orchestration.

### 5. Example MCP Tool Plugin
- Layout `examples/plugins/example-tool/{pyproject.toml, README.md, src/hopeit/agents/example_tool/...}` mirroring official style.
- Implement dummy tool (e.g., `generate-random-number`) with typed data objects (`RandomNumberRequest`, `RandomNumberResult`).
- Provide `events/generate_random.py` exposing tool logic and registration helper aligning with MCP schema, ensuring type hints.
- Document how to register this plugin with an MCP server using Anthropic library, and how agent apps invoke it via bridge.
- Unit tests for event logic and schema registration contract.

### 6. Typing, Testing & Documentation
- Configure `uv`-driven CI workflow (GitHub Actions) running `uv run ruff`, `uv run mypy`, and `uv run pytest` across workspace components.
- Ensure `mypy` runs in strict or near-strict mode (`warn-redundant-casts`, `disallow-any-generics`, etc.) and all modules pass without ignores unless justified.
- Update root `README.md` with setup instructions using `uv` (`uv sync`, `uv run ...`), typing guarantees, and links to examples/plugins.
- Document configuration samples, secrets management, and testing commands in each plugin README.

## Open Questions / Assumptions
- Assume availability of OpenAI-compatible endpoint; client abstraction should allow overriding base URL and headers while remaining type-safe.
- Assume official Anthropic MCP library exposes async interfaces; if sync wrappers are required, use `asyncio.to_thread` with typed return values and document rationale.
- Secrets management will rely on existing hopeit.engine mechanisms (environment variables or config secrets) with typed helpers.
- Tests for examples and tools will mock external services to avoid network usage; plan includes typed fixtures/stubs for MCP and model client interactions.

## Minimal Deliverable Definition
- Two plugin packages (`model-client`, `mcp-bridge`) with typed code, `pyproject.toml` + `uv` configuration, README, events, and tests.
- Example agent app and example MCP tool plugin demonstrating end-to-end usage, each type-checked by `mypy`.
- Root workspace configured with `uv`, CI running `ruff`, `mypy`, and `pytest`, and documentation guiding users through setup and customization.

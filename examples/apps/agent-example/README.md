# hopeit.agents agent example app

Minimal hopeit.engine application demonstrating how to combine the `model-client` and `mcp-bridge` plugins to run an agent workflow.

## Flow
1. Build a conversation with a system prompt and the latest user message.
2. Call the `hopeit.agents.model_client` plugin to obtain a completion.
3. Execute requested MCP tool calls with `hopeit.agents.mcp_bridge` and append results to the conversation.

## Settings
`config/app-config.json` shows how to configure both plugins and the agent defaults. The example uses stdio transport to launch an MCP server command and an OpenAI-compatible endpoint for model completions.

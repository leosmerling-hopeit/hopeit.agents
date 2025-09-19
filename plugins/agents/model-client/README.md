# hopeit_agents model client plugin

This plugin exposes data objects and an event to interact with OpenAI-compatible chat completion APIs from hopeit.engine apps.

## Features
- Typed data models describing agent conversations, tool calls, and completion configuration.
- Async client wrapper built on `aiohttp` that can call OpenAI-compatible endpoints.
- `generate` event ready to be wired into hopeit apps, reading defaults from app settings.

## Settings example
```json
{
  "settings": {
    "model_client": {
      "api_base": "https://api.openai.com/v1",
      "api_key_env": "OPENAI_API_KEY",
      "default_model": "gpt-4o-mini",
      "timeout_seconds": 30.0,
      "extra_headers": {
        "OpenAI-Beta": "assistants=v1"
      }
    }
  }
}
```

## Event usage
```python
from hopeit.app.client import app_call
from hopeit_agents.model_client.models import CompletionRequest

response = await app_call(
    "model-client-conn",
    event="generate",
    datatype=CompletionResponse,
    payload=CompletionRequest(conversation=conversation),
    context=context,
)
```

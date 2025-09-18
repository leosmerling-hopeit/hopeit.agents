from datetime import UTC, datetime
from types import SimpleNamespace, TracebackType
from typing import Any, Self, cast

import pytest

from hopeit.agents.model_client.client import AsyncModelClient, ModelClientError
from hopeit.agents.model_client.events import generate as generate_event
from hopeit.agents.model_client.models import (
    CompletionConfig,
    CompletionRequest,
    CompletionResponse,
    Conversation,
    Message,
    Role,
    ToolCall,
    Usage,
)
from hopeit.agents.model_client.settings import ModelClientSettings, merge_config


class _FakeResponse:
    def __init__(self, status: int, payload: dict[str, Any]) -> None:
        self.status = status
        self._payload = payload

    async def json(self) -> dict[str, Any]:
        return self._payload

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        return None


class _FakeSession:
    def __init__(self, response: _FakeResponse) -> None:
        self._response = response

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        return None

    def post(self, *_args: Any, **_kwargs: Any) -> _FakeResponse:
        return self._response


@pytest.mark.asyncio
async def test_async_model_client_complete_success(monkeypatch: pytest.MonkeyPatch) -> None:
    conversation = Conversation(messages=[Message(role=Role.USER, content="Hello")])
    request = CompletionRequest(conversation=conversation)
    config = CompletionConfig(model="test-model")

    payload = {
        "id": "cmpl-123",
        "model": "test-model",
        "created": int(datetime.now(UTC).timestamp()),
        "choices": [
            {
                "index": 0,
                "finish_reason": "stop",
                "message": {
                    "role": "assistant",
                    "content": "Hi there!",
                },
            },
        ],
        "usage": {"prompt_tokens": 5, "completion_tokens": 7, "total_tokens": 12},
    }

    fake_response = _FakeResponse(status=200, payload=payload)
    fake_session = _FakeSession(fake_response)

    def fake_client_session(*_args: Any, **_kwargs: Any) -> _FakeSession:
        return fake_session

    monkeypatch.setattr(
        "hopeit.agents.model_client.client.aiohttp.ClientSession",
        fake_client_session,
    )

    client = AsyncModelClient(
        base_url="https://api.example.com/v1",
        api_key=None,
        timeout_seconds=5,
    )

    response = await client.complete(request, config)

    assert response.message.content == "Hi there!"
    assert response.conversation.messages[-1].content == "Hi there!"
    assert response.usage is not None
    assert response.usage.total_tokens == 12


@pytest.mark.asyncio
async def test_async_model_client_error_on_http_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    conversation = Conversation(messages=[Message(role=Role.USER, content="Hello")])
    request = CompletionRequest(conversation=conversation)
    config = CompletionConfig(model="test-model")

    payload = {"error": {"message": "bad request"}}
    fake_response = _FakeResponse(status=400, payload=payload)
    fake_session = _FakeSession(fake_response)

    def fake_client_session(*_args: Any, **_kwargs: Any) -> _FakeSession:
        return fake_session

    monkeypatch.setattr(
        "hopeit.agents.model_client.client.aiohttp.ClientSession",
        fake_client_session,
    )

    client = AsyncModelClient(
        base_url="https://api.example.com/v1",
        api_key=None,
        timeout_seconds=5,
    )

    with pytest.raises(ModelClientError) as err:
        await client.complete(request, config)

    assert err.value.status == 400


@pytest.mark.asyncio
async def test_generate_event_invokes_client(monkeypatch: pytest.MonkeyPatch) -> None:
    conversation = Conversation(messages=[Message(role=Role.USER, content="Ping")])
    request = CompletionRequest(conversation=conversation)

    async def fake_complete(
        _self: Any,
        payload: CompletionRequest,
        _config: CompletionConfig,
    ) -> CompletionResponse:
        message = Message(role=Role.ASSISTANT, content="Pong")
        return CompletionResponse(
            response_id="cmpl-xyz",
            model="mock-model",
            created_at=datetime.now(UTC),
            message=message,
            tool_calls=[ToolCall(call_id="tool-1", name="foo", arguments={})],
            conversation=payload.conversation.with_message(message),
            usage=Usage(prompt_tokens=5, completion_tokens=5, total_tokens=10),
            finish_reason="stop",
        )

    class _FakeClient:
        def __init__(self, **_kwargs: Any) -> None:
            self.called = True

        complete = fake_complete

    monkeypatch.setattr(
        "hopeit.agents.model_client.events.generate.AsyncModelClient",
        _FakeClient,
    )

    context = SimpleNamespace(
        settings={
            "model_client": {
                "api_base": "https://api.example.com/v1",
                "api_key_env": "API_KEY",
                "default_model": "mock-model",
                "timeout_seconds": 5.0,
            },
        },
        env={"API_KEY": "abc123"},
    )

    response = await generate_event.generate(request, cast("Any", context))

    assert response.message.content == "Pong"
    assert response.model == "mock-model"
    assert response.tool_calls[0].call_id == "tool-1"


def test_merge_config_prefers_override_values() -> None:
    settings = ModelClientSettings(
        api_base="https://api.example.com/v1",
        default_model="default-model",
        default_config=CompletionConfig(
            temperature=0.5,
            max_output_tokens=256,
            tool_choice="auto",
            enable_tool_expansion=True,
        ),
    )

    merged = merge_config(
        settings,
        CompletionConfig(model="custom", temperature=0.1, enable_tool_expansion=False),
    )

    assert merged.model == "custom"
    assert merged.temperature == 0.1
    assert merged.max_output_tokens == 256
    assert merged.enable_tool_expansion is False

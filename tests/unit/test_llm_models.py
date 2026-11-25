"""Unit tests for normalized LLM models."""

import pytest

from ai_agent_bench.llm.models import LLMMessage, LLMRequest, LLMResponse, LLMUsage


def test_message_accepts_valid_content():
    """Message should accept non-empty content."""

    message = LLMMessage(role="user", content="Hello")

    assert message.role == "user"
    assert message.content == "Hello"


def test_message_rejects_empty_content():
    """Message should reject empty content."""

    with pytest.raises(ValueError, match="content must not be empty"):
        LLMMessage(role="user", content="")


def test_message_rejects_whitespace_content():
    """Message should reject whitespace-only content."""

    with pytest.raises(ValueError, match="content must not be empty"):
        LLMMessage(role="user", content="   ")


def test_request_accepts_valid_data():
    """Request should accept valid messages and configuration."""

    request = LLMRequest(
        messages=(LLMMessage(role="user", content="Hello"),),
        model="test-model",
        temperature=0.5,
        max_tokens=100,
    )

    assert request.model == "test-model"
    assert request.temperature == 0.5
    assert request.max_tokens == 100


def test_request_rejects_empty_messages():
    """Request should require at least one message."""

    with pytest.raises(ValueError, match="at least one message"):
        LLMRequest(
            messages=(),
            model="test-model",
        )


def test_request_rejects_empty_model():
    """Request should reject an empty model name."""

    with pytest.raises(ValueError, match="Model name must not be empty"):
        LLMRequest(
            messages=(LLMMessage(role="user", content="Hello"),),
            model="   ",
        )


@pytest.mark.parametrize("temperature", [-0.1, 2.1, float("nan")])
def test_request_rejects_invalid_temperature(temperature):
    """Request should reject temperatures outside the allowed range."""

    with pytest.raises(ValueError, match="Temperature must be between 0 and 2"):
        LLMRequest(
            messages=(LLMMessage(role="user", content="Hello"),),
            model="test-model",
            temperature=temperature,
        )


@pytest.mark.parametrize("max_tokens", [0, -1])
def test_request_rejects_invalid_max_tokens(max_tokens):
    """Request should reject non-positive token limits."""

    with pytest.raises(ValueError, match="max_tokens must be greater than zero"):
        LLMRequest(
            messages=(LLMMessage(role="user", content="Hello"),),
            model="test-model",
            max_tokens=max_tokens,
        )


def test_usage_stores_token_counts():
    """Usage model should store token counts."""

    usage = LLMUsage(
        prompt_tokens=10,
        completion_tokens=20,
        total_tokens=30,
    )

    assert usage.prompt_tokens == 10
    assert usage.completion_tokens == 20
    assert usage.total_tokens == 30


def test_response_accepts_valid_content():
    """Response should accept non-empty content."""

    response = LLMResponse(
        content="Hello",
        model="test-model",
        provider="test-provider",
    )

    assert response.content == "Hello"
    assert response.model == "test-model"
    assert response.provider == "test-provider"


def test_response_rejects_empty_content():
    """Response should reject empty content."""

    with pytest.raises(ValueError, match="content must not be empty"):
        LLMResponse(
            content="",
            model="test-model",
            provider="test-provider",
        )

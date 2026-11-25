"""Unit tests for the OpenRouter LLM provider."""

from types import SimpleNamespace

import pytest

from ai_agent_bench.config import LLMConfig
from ai_agent_bench.llm.models import LLMMessage, LLMRequest
from ai_agent_bench.llm.openrouter import LLMProviderError, OpenRouterProvider


class MockCompletions:
    """Mock chat completions endpoint."""

    def __init__(self, response=None, error=None):
        self.response = response
        self.error = error
        self.call_arguments = None

    def create(self, **kwargs):
        self.call_arguments = kwargs

        if self.error is not None:
            raise self.error

        return self.response


def create_mock_client(completions):
    """Create a mock OpenAI-compatible client."""

    return SimpleNamespace(
        chat=SimpleNamespace(
            completions=completions,
        )
    )


@pytest.fixture
def config():
    """Return a test configuration."""

    return LLMConfig(
        provider="openrouter",
        model="particle-ai/particle-1:free",
        api_key="test-secret-key",
        max_steps=20,
        temperature=0.2,
        timeout_seconds=30,
    )


@pytest.fixture
def request_data():
    """Return a sample LLM request."""

    return LLMRequest(
        messages=(
            LLMMessage(role="system", content="You are a helpful assistant."),
            LLMMessage(role="user", content="Explain pagination."),
        ),
        model="particle-ai/particle-1:free",
        temperature=0.4,
        max_tokens=500,
    )


@pytest.fixture
def successful_response():
    """Return a mocked successful API response."""

    return SimpleNamespace(
        model="particle-ai/particle-1:free",
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(content="Pagination divides results into pages."),
                finish_reason="stop",
            )
        ],
        usage=SimpleNamespace(
            prompt_tokens=20,
            completion_tokens=10,
            total_tokens=30,
        ),
    )


def test_provider_name(config):
    """Provider should identify itself as OpenRouter."""

    provider = OpenRouterProvider(config, client=create_mock_client(MockCompletions()))

    assert provider.provider_name == "openrouter"


def test_generate_sends_correct_request(config, request_data, successful_response):
    """Provider should send the expected parameters to the client."""

    completions = MockCompletions(response=successful_response)
    provider = OpenRouterProvider(config, client=create_mock_client(completions))

    provider.generate(request_data)

    assert completions.call_arguments == {
        "model": "particle-ai/particle-1:free",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Explain pagination."},
        ],
        "temperature": 0.4,
        "max_tokens": 500,
    }


def test_generate_normalizes_response(config, request_data, successful_response):
    """Provider should convert the API response into LLMResponse."""

    provider = OpenRouterProvider(
        config,
        client=create_mock_client(MockCompletions(response=successful_response)),
    )

    result = provider.generate(request_data)

    assert result.content == "Pagination divides results into pages."
    assert result.model == "particle-ai/particle-1:free"
    assert result.provider == "openrouter"
    assert result.finish_reason == "stop"


def test_generate_extracts_token_usage(config, request_data, successful_response):
    """Provider should extract token usage."""

    provider = OpenRouterProvider(
        config,
        client=create_mock_client(MockCompletions(response=successful_response)),
    )

    result = provider.generate(request_data)

    assert result.usage is not None
    assert result.usage.prompt_tokens == 20
    assert result.usage.completion_tokens == 10
    assert result.usage.total_tokens == 30


def test_generate_handles_missing_usage(config, request_data):
    """Provider should support responses without usage information."""

    response = SimpleNamespace(
        model="particle-ai/particle-1:free",
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(content="A response."),
                finish_reason="stop",
            )
        ],
        usage=None,
    )

    provider = OpenRouterProvider(
        config,
        client=create_mock_client(MockCompletions(response=response)),
    )

    result = provider.generate(request_data)

    assert result.content == "A response."
    assert result.usage is None


def test_generate_safely_handles_api_error(config, request_data):
    """Provider should not expose raw exception messages."""

    secret_error = RuntimeError("Sensitive error details and secret information")

    provider = OpenRouterProvider(
        config,
        client=create_mock_client(MockCompletions(error=secret_error)),
    )

    with pytest.raises(LLMProviderError) as exc_info:
        provider.generate(request_data)

    assert "RuntimeError" in str(exc_info.value)
    assert "Sensitive error details" not in str(exc_info.value)
    assert "secret information" not in str(exc_info.value)


def test_generate_rejects_empty_choices(config, request_data):
    """Provider should reject responses without completion choices."""

    response = SimpleNamespace(
        model="particle-ai/particle-1:free",
        choices=[],
        usage=None,
    )

    provider = OpenRouterProvider(
        config,
        client=create_mock_client(MockCompletions(response=response)),
    )

    with pytest.raises(LLMProviderError, match="no completion choices"):
        provider.generate(request_data)


def test_generate_rejects_empty_content(config, request_data):
    """Provider should reject empty completion content."""

    response = SimpleNamespace(
        model="particle-ai/particle-1:free",
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(content="   "),
                finish_reason="stop",
            )
        ],
        usage=None,
    )

    provider = OpenRouterProvider(
        config,
        client=create_mock_client(MockCompletions(response=response)),
    )

    with pytest.raises(LLMProviderError, match="empty response"):
        provider.generate(request_data)

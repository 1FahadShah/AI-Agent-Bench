"""OpenRouter implementation of the LLM provider interface."""

from openai import OpenAI

from ai_agent_bench.config import LLMConfig
from ai_agent_bench.llm.base import LLMProvider
from ai_agent_bench.llm.models import LLMRequest, LLMResponse, LLMUsage


class LLMProviderError(Exception):
    """Raised when an LLM provider request fails."""


class OpenRouterProvider(LLMProvider):
    """LLM provider implementation using OpenRouter's OpenAI-compatible API."""

    BASE_URL = "https://openrouter.ai/api/v1"

    def __init__(self, config: LLMConfig, client: OpenAI | None = None) -> None:
        """Initialize the provider using application configuration."""

        self._config = config

        if client is None:
            self._client = OpenAI(
                api_key=config.api_key,
                base_url=self.BASE_URL,
                timeout=config.timeout_seconds,
            )
        else:
            self._client = client

    @property
    def provider_name(self) -> str:
        """Return the provider identifier."""
        return "openrouter"

    def generate(self, request: LLMRequest) -> LLMResponse:
        """Send a chat completion request to OpenRouter."""

        try:
            response = self._client.chat.completions.create(
                model=request.model,
                messages=[
                    {"role": message.role, "content": message.content}
                    for message in request.messages
                ],
                temperature=request.temperature,
                max_tokens=request.max_tokens,
            )

        except Exception as exc:
            # Do not expose raw provider exceptions because they may contain
            # request details, URLs, or sensitive information.
            raise LLMProviderError(f"OpenRouter request failed ({type(exc).__name__}).") from None

        if not response.choices:
            raise LLMProviderError("OpenRouter returned no completion choices.")

        choice = response.choices[0]
        content = choice.message.content

        if not isinstance(content, str) or not content.strip():
            raise LLMProviderError("OpenRouter returned an empty response.")

        usage = None

        if response.usage is not None:
            usage = LLMUsage(
                prompt_tokens=response.usage.prompt_tokens or 0,
                completion_tokens=response.usage.completion_tokens or 0,
                total_tokens=response.usage.total_tokens or 0,
            )

        return LLMResponse(
            content=content,
            model=response.model or request.model,
            provider=self.provider_name,
            finish_reason=choice.finish_reason,
            usage=usage,
        )

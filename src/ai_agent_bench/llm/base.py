"""Provider-independent interface for LLM integrations."""

from abc import ABC, abstractmethod

from ai_agent_bench.llm.models import LLMRequest, LLMResponse


class LLMProvider(ABC):
    """Abstract interface implemented by concrete LLM providers."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the provider's identifier."""
        raise NotImplementedError

    @abstractmethod
    def generate(self, request: LLMRequest) -> LLMResponse:
        """Send a request to the provider and return a normalized response."""
        raise NotImplementedError

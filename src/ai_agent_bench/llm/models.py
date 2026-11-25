"""Provider-independent models for LLM requests and responses."""

from dataclasses import dataclass
from typing import Literal

MessageRole = Literal["system", "user", "assistant", "tool"]


@dataclass(frozen=True)
class LLMMessage:
    """A single message in an LLM conversation."""

    role: MessageRole
    content: str

    def __post_init__(self) -> None:
        if not self.content.strip():
            raise ValueError("Message content must not be empty.")


@dataclass(frozen=True)
class LLMRequest:
    """A normalized request to an LLM provider."""

    messages: tuple[LLMMessage, ...]
    model: str
    temperature: float = 0.2
    max_tokens: int | None = None

    def __post_init__(self) -> None:
        if not self.messages:
            raise ValueError("LLM request must contain at least one message.")

        if not self.model.strip():
            raise ValueError("Model name must not be empty.")

        if not 0.0 <= self.temperature <= 2.0:
            raise ValueError("Temperature must be between 0 and 2.")

        if self.max_tokens is not None and self.max_tokens <= 0:
            raise ValueError("max_tokens must be greater than zero.")


@dataclass(frozen=True)
class LLMUsage:
    """Token usage reported by the provider."""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


@dataclass(frozen=True)
class LLMResponse:
    """A normalized response returned by an LLM provider."""

    content: str
    model: str
    provider: str
    finish_reason: str | None = None
    usage: LLMUsage | None = None

    def __post_init__(self) -> None:
        if not self.content.strip():
            raise ValueError("LLM response content must not be empty.")

"""Configuration management for AI Agent Bench."""

import os
from dataclasses import dataclass, field

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class LLMConfig:
    """Configuration for the LLM provider and agent."""

    provider: str
    model: str
    api_key: str = field(repr=False)
    max_steps: int = 20
    temperature: float = 0.2
    timeout_seconds: int = 120

    @classmethod
    def from_env(cls) -> "LLMConfig":
        """Load and validate LLM configuration from environment variables."""

        provider = os.getenv("LLM_PROVIDER", "openrouter").strip().lower()
        model = os.getenv("LLM_MODEL", "").strip()
        api_key = os.getenv("OPENROUTER_API_KEY", "").strip()

        max_steps_raw = os.getenv("AGENT_MAX_STEPS", "20")
        temperature_raw = os.getenv("AGENT_TEMPERATURE", "0.2")
        timeout_raw = os.getenv("LLM_TIMEOUT_SECONDS", "120")

        if provider != "openrouter":
            raise ValueError(
                f"Unsupported LLM provider: {provider}. Currently supported provider: openrouter."
            )

        if not model:
            raise ValueError("LLM_MODEL must not be empty.")

        if not api_key:
            raise ValueError("OPENROUTER_API_KEY is missing. Set it in your local .env file.")

        try:
            max_steps = int(max_steps_raw)
        except ValueError as exc:
            raise ValueError("AGENT_MAX_STEPS must be an integer.") from exc

        try:
            temperature = float(temperature_raw)
        except ValueError as exc:
            raise ValueError("AGENT_TEMPERATURE must be a number.") from exc

        try:
            timeout_seconds = int(timeout_raw)
        except ValueError as exc:
            raise ValueError("LLM_TIMEOUT_SECONDS must be an integer.") from exc

        if max_steps <= 0:
            raise ValueError("AGENT_MAX_STEPS must be greater than zero.")

        if not 0.0 <= temperature <= 2.0:
            raise ValueError("AGENT_TEMPERATURE must be between 0 and 2.")

        if timeout_seconds <= 0:
            raise ValueError("LLM_TIMEOUT_SECONDS must be greater than zero.")

        return cls(
            provider=provider,
            model=model,
            api_key=api_key,
            max_steps=max_steps,
            temperature=temperature,
            timeout_seconds=timeout_seconds,
        )

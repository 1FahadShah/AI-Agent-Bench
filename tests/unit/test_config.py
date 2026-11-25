from dataclasses import FrozenInstanceError

import pytest

from ai_agent_bench.config import LLMConfig


def set_valid_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "openrouter")
    monkeypatch.setenv("LLM_MODEL", "particle-ai/particle-1:free")
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-api-key")
    monkeypatch.setenv("AGENT_MAX_STEPS", "20")
    monkeypatch.setenv("AGENT_TEMPERATURE", "0.2")
    monkeypatch.setenv("LLM_TIMEOUT_SECONDS", "120")


def test_config_loads_valid_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    set_valid_environment(monkeypatch)

    config = LLMConfig.from_env()

    assert config.provider == "openrouter"
    assert config.model == "particle-ai/particle-1:free"
    assert config.api_key == "test-api-key"
    assert config.max_steps == 20
    assert config.temperature == 0.2
    assert config.timeout_seconds == 120


def test_api_key_is_hidden_from_config_representation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    set_valid_environment(monkeypatch)

    config = LLMConfig.from_env()

    assert "test-api-key" not in repr(config)


def test_config_is_immutable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    set_valid_environment(monkeypatch)

    config = LLMConfig.from_env()

    with pytest.raises(FrozenInstanceError):
        config.model = "another-model"  # type: ignore[misc]


def test_missing_api_key_raises_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    set_valid_environment(monkeypatch)
    monkeypatch.setenv("OPENROUTER_API_KEY", "")

    with pytest.raises(ValueError, match="OPENROUTER_API_KEY is missing"):
        LLMConfig.from_env()


def test_unsupported_provider_raises_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    set_valid_environment(monkeypatch)
    monkeypatch.setenv("LLM_PROVIDER", "unsupported-provider")

    with pytest.raises(ValueError, match="Unsupported LLM provider"):
        LLMConfig.from_env()


def test_missing_model_raises_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    set_valid_environment(monkeypatch)
    monkeypatch.setenv("LLM_MODEL", "")

    with pytest.raises(ValueError, match="LLM_MODEL must not be empty"):
        LLMConfig.from_env()


def test_invalid_max_steps_raises_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    set_valid_environment(monkeypatch)
    monkeypatch.setenv("AGENT_MAX_STEPS", "invalid")

    with pytest.raises(ValueError, match="AGENT_MAX_STEPS must be an integer"):
        LLMConfig.from_env()


def test_zero_max_steps_raises_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    set_valid_environment(monkeypatch)
    monkeypatch.setenv("AGENT_MAX_STEPS", "0")

    with pytest.raises(ValueError, match="greater than zero"):
        LLMConfig.from_env()


def test_invalid_temperature_raises_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    set_valid_environment(monkeypatch)
    monkeypatch.setenv("AGENT_TEMPERATURE", "invalid")

    with pytest.raises(ValueError, match="AGENT_TEMPERATURE must be a number"):
        LLMConfig.from_env()


def test_temperature_out_of_range_raises_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    set_valid_environment(monkeypatch)
    monkeypatch.setenv("AGENT_TEMPERATURE", "2.5")

    with pytest.raises(ValueError, match="between 0 and 2"):
        LLMConfig.from_env()


def test_invalid_timeout_raises_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    set_valid_environment(monkeypatch)
    monkeypatch.setenv("LLM_TIMEOUT_SECONDS", "invalid")

    with pytest.raises(ValueError, match="LLM_TIMEOUT_SECONDS must be an integer"):
        LLMConfig.from_env()


def test_zero_timeout_raises_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    set_valid_environment(monkeypatch)
    monkeypatch.setenv("LLM_TIMEOUT_SECONDS", "0")

    with pytest.raises(ValueError, match="greater than zero"):
        LLMConfig.from_env()

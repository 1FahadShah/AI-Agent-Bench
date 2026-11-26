from pathlib import Path

import pytest

from ai_agent_bench.config import LLMConfig
from ai_agent_bench.llm.base import LLMProvider
from ai_agent_bench.llm.models import LLMRequest, LLMResponse
from ai_agent_bench.orchestration.service import BenchmarkOrchestrator


class CustomProvider(LLMProvider):
    """Minimal custom provider used to test execution policy."""

    @property
    def provider_name(self) -> str:
        return "custom"

    def generate(self, request: LLMRequest) -> LLMResponse:
        return LLMResponse(
            content="Test response",
            model=request.model,
            provider=self.provider_name,
        )


def create_orchestrator(
    tmp_path: Path,
    provider: LLMProvider | None = None,
    allow_unsafe_local_execution: bool = False,
) -> BenchmarkOrchestrator:
    tasks = tmp_path / "tasks"
    tasks.mkdir(exist_ok=True)

    return BenchmarkOrchestrator(
        tasks_directory=tasks,
        workspace_root=tmp_path / "workspaces",
        results_directory=tmp_path / "results",
        config=LLMConfig(
            provider="openrouter",
            model="test-model",
            api_key="test-key",
        ),
        provider=provider,
        allow_unsafe_local_execution=allow_unsafe_local_execution,
    )


def test_real_provider_execution_is_blocked_by_default(
    tmp_path: Path,
) -> None:
    orchestrator = create_orchestrator(tmp_path)

    with pytest.raises(RuntimeError, match="not OS-isolated"):
        orchestrator.run("MISSING-TASK")


def test_custom_provider_execution_is_blocked_by_default(
    tmp_path: Path,
) -> None:
    orchestrator = create_orchestrator(
        tmp_path,
        provider=CustomProvider(),
    )

    with pytest.raises(RuntimeError, match="not OS-isolated"):
        orchestrator.run("MISSING-TASK")


def test_explicit_opt_in_bypasses_execution_guard(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    orchestrator = create_orchestrator(
        tmp_path,
        provider=CustomProvider(),
        allow_unsafe_local_execution=True,
    )

    def stop_before_execution(task_id: str) -> None:
        raise LookupError("Execution guard passed")

    monkeypatch.setattr(
        orchestrator.loader,
        "load_task",
        stop_before_execution,
    )

    with pytest.raises(LookupError, match="Execution guard passed"):
        orchestrator.run("MISSING-TASK")

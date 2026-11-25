import json
from pathlib import Path

import pytest

from ai_agent_bench.config import LLMConfig
from ai_agent_bench.llm.base import LLMProvider
from ai_agent_bench.llm.models import LLMRequest, LLMResponse
from ai_agent_bench.orchestration.service import BenchmarkOrchestrator

BUGGY_IMPLEMENTATION = """
def paginate(items, page, page_size):
    if page < 1 or page_size < 1:
        raise ValueError("Invalid pagination parameters")

    total_items = len(items)
    total_pages = total_items // page_size

    start = (page - 1) * page_size
    end = start + page_size

    return {
        "items": items[start:end],
        "page": page,
        "page_size": page_size,
        "total_items": total_items,
        "total_pages": total_pages,
        "has_previous": page > 1,
        "has_next": page < total_pages,
    }
"""

FIXED_IMPLEMENTATION = """
import math


def paginate(items, page, page_size):
    if page < 1 or page_size < 1:
        raise ValueError("Invalid pagination parameters")

    total_items = len(items)
    total_pages = math.ceil(total_items / page_size) if total_items else 0

    start = (page - 1) * page_size
    end = start + page_size

    return {
        "items": items[start:end],
        "page": page,
        "page_size": page_size,
        "total_items": total_items,
        "total_pages": total_pages,
        "has_previous": page > 1,
        "has_next": page < total_pages,
    }
"""

PARTIALLY_FIXED_IMPLEMENTATION = """
def paginate(items, page, page_size):
    if page < 1 or page_size < 1:
        raise ValueError("Invalid pagination parameters")

    total_items = len(items)

    # Deliberately overfits the visible test case.
    total_pages = (
        3 if total_items == 23 else total_items // page_size
    )

    start = (page - 1) * page_size
    end = start + page_size

    return {
        "items": items[start:end],
        "page": page,
        "page_size": page_size,
        "total_items": total_items,
        "total_pages": total_pages,
        "has_previous": page > 1,
        "has_next": page < total_pages,
    }
"""


class MockLLMProvider(LLMProvider):
    """Deterministic LLM provider for orchestration tests."""

    def __init__(self, responses: list[str]) -> None:
        self.responses = list(responses)
        self.generate_calls = 0

    @property
    def provider_name(self) -> str:
        return "mock"

    def generate(self, request: LLMRequest) -> LLMResponse:
        self.generate_calls += 1

        if not self.responses:
            raise RuntimeError("Mock provider has no remaining responses")

        return LLMResponse(
            content=self.responses.pop(0),
            model=request.model,
            provider=self.provider_name,
        )


def tool_action(tool_name: str, arguments: dict) -> str:
    return json.dumps(
        {
            "action_type": "tool",
            "tool_name": tool_name,
            "arguments": arguments,
        }
    )


def final_action(message: str = "Task completed.") -> str:
    return json.dumps(
        {
            "action_type": "final",
            "final_message": message,
        }
    )


@pytest.fixture
def benchmark_directories(tmp_path: Path) -> dict[str, Path]:
    tasks_directory = tmp_path / "tasks"
    task_directory = tasks_directory / "PB-SWE-001"

    starter_directory = task_directory / "starter"
    visible_tests_directory = task_directory / "visible_tests"
    hidden_tests_directory = task_directory / "hidden_tests"
    reference_directory = task_directory / "reference"

    for directory in (
        starter_directory,
        visible_tests_directory,
        hidden_tests_directory,
        reference_directory,
    ):
        directory.mkdir(parents=True)

    (starter_directory / "pagination.py").write_text(
        BUGGY_IMPLEMENTATION,
        encoding="utf-8",
    )

    (visible_tests_directory / "test_pagination.py").write_text(
        "from pagination import paginate\n\n"
        "def test_partial_page_rounds_up():\n"
        "    result = paginate(list(range(23)), page=1, page_size=10)\n"
        "    assert result['total_pages'] == 3\n"
        "    assert result['has_next'] is True\n",
        encoding="utf-8",
    )

    (hidden_tests_directory / "test_hidden.py").write_text(
        "def test_placeholder():\n    assert True\n",
        encoding="utf-8",
    )

    (reference_directory / "pagination.py").write_text(
        FIXED_IMPLEMENTATION,
        encoding="utf-8",
    )

    task_yaml = task_directory / "task.yaml"

    task_yaml.write_text(
        """
id: PB-SWE-001
name: Fix Pagination Boundary Bug
description: Fix the pagination boundary calculation.
category: software_engineering
difficulty: medium
instructions: |
  Fix the pagination implementation.
  Run the visible tests.
environment:
  python_version: "3.13"
  timeout_seconds: 30
  max_agent_steps: 10
evaluation:
  evaluation_type: tests
  visible_tests_path: visible_tests
  hidden_tests_path: hidden_tests
  reference_solution_path: reference
tags:
  - pagination
""",
        encoding="utf-8",
    )

    return {
        "tasks": tasks_directory,
        "task": task_directory,
        "workspaces": tmp_path / "workspaces",
        "results": tmp_path / "runs",
    }


@pytest.fixture
def llm_config() -> LLMConfig:
    return LLMConfig(
        provider="openrouter",
        model="mock-model",
        api_key="test-key-not-used",
        max_steps=10,
        temperature=0.0,
        timeout_seconds=30,
    )


def create_orchestrator(
    directories: dict[str, Path],
    config: LLMConfig,
    provider: LLMProvider,
) -> BenchmarkOrchestrator:
    return BenchmarkOrchestrator(
        tasks_directory=directories["tasks"],
        workspace_root=directories["workspaces"],
        results_directory=directories["results"],
        config=config,
        provider=provider,
    )


def test_orchestrator_completes_and_passes_benchmark(
    benchmark_directories: dict[str, Path],
    llm_config: LLMConfig,
) -> None:
    provider = MockLLMProvider(
        [
            tool_action("list_files", {"directory": "starter"}),
            tool_action("read_file", {"file_path": "starter/pagination.py"}),
            tool_action(
                "write_file",
                {
                    "file_path": "starter/pagination.py",
                    "content": FIXED_IMPLEMENTATION,
                },
            ),
            tool_action(
                "run_command",
                {
                    "command": [
                        "python",
                        "-m",
                        "pytest",
                        "../visible_tests",
                        "-q",
                    ],
                    "working_directory": "starter",
                },
            ),
            final_action("Fixed the pagination boundary bug."),
        ]
    )

    orchestrator = create_orchestrator(
        benchmark_directories,
        llm_config,
        provider,
    )

    result = orchestrator.run("PB-SWE-001")

    assert result.task_id == "PB-SWE-001"
    assert result.agent_result.completed is True
    assert result.agent_result.steps_used == 5
    assert result.evaluation_result.passed is True
    assert result.passed is True
    assert result.result_path.is_file()

    saved_result = json.loads(result.result_path.read_text(encoding="utf-8"))

    assert saved_result["visible_tests_passed"] is True
    assert saved_result["hidden_tests_passed"] is True
    assert saved_result["benchmark_passed"] is True
    assert saved_result["task"]["task_id"] == "PB-SWE-001"
    assert saved_result["agent"]["provider"] == "mock"
    assert saved_result["agent"]["model"] == "mock-model"
    assert saved_result["evaluation"]["passed"] is True
    assert "api_key" not in saved_result["agent"]

    assert provider.generate_calls == 5


def test_orchestrator_records_evaluation_failure(
    benchmark_directories: dict[str, Path],
    llm_config: LLMConfig,
) -> None:
    provider = MockLLMProvider([final_action("Finished without making changes.")])

    orchestrator = create_orchestrator(
        benchmark_directories,
        llm_config,
        provider,
    )

    result = orchestrator.run("PB-SWE-001")

    assert result.agent_result.completed is True
    assert result.evaluation_result.passed is False
    assert result.passed is False
    assert result.result_path.is_file()

    saved_result = json.loads(result.result_path.read_text(encoding="utf-8"))

    assert saved_result["visible_tests_passed"] is False
    assert saved_result["evaluation"]["exit_code"] != 0


def test_orchestrator_evaluates_and_saves_after_agent_error(
    benchmark_directories: dict[str, Path],
    llm_config: LLMConfig,
) -> None:
    provider = MockLLMProvider(["This is not valid JSON"])

    orchestrator = create_orchestrator(
        benchmark_directories,
        llm_config,
        provider,
    )

    result = orchestrator.run("PB-SWE-001")

    assert result.agent_result.completed is False
    assert result.agent_result.error is not None
    assert result.evaluation_result.passed is False
    assert result.result_path.is_file()

    saved_result = json.loads(result.result_path.read_text(encoding="utf-8"))

    assert saved_result["agent"]["completed"] is False
    assert saved_result["evaluation"]["passed"] is False


def test_orchestrator_rejects_unsupported_evaluation_type(
    benchmark_directories: dict[str, Path],
    llm_config: LLMConfig,
) -> None:
    task_file = benchmark_directories["task"] / "task.yaml"

    task_yaml = task_file.read_text(encoding="utf-8")
    task_yaml = task_yaml.replace(
        "evaluation_type: tests",
        "evaluation_type: state_checks",
    )
    task_file.write_text(task_yaml, encoding="utf-8")

    provider = MockLLMProvider([])

    orchestrator = create_orchestrator(
        benchmark_directories,
        llm_config,
        provider,
    )

    with pytest.raises(NotImplementedError, match="Only tests-based evaluation"):
        orchestrator.run("PB-SWE-001")

    assert provider.generate_calls == 0


def test_hidden_failure_overrides_visible_test_success(
    benchmark_directories: dict[str, Path],
    llm_config: LLMConfig,
) -> None:
    hidden_test = benchmark_directories["task"] / "hidden_tests" / "test_hidden.py"
    hidden_test.write_text(
        "from pagination import paginate\n\n"
        "def test_non_multiple_page_count():\n"
        "    result = paginate(list(range(21)), page=1, page_size=10)\n"
        "    assert result['total_pages'] == 3\n",
        encoding="utf-8",
    )

    provider = MockLLMProvider(
        [
            tool_action(
                "write_file",
                {
                    "file_path": "starter/pagination.py",
                    "content": PARTIALLY_FIXED_IMPLEMENTATION,
                },
            ),
            final_action("Fixed the visible pagination example."),
        ]
    )

    orchestrator = create_orchestrator(
        benchmark_directories,
        llm_config,
        provider,
    )

    result = orchestrator.run("PB-SWE-001")

    assert result.agent_result.completed is True

    # The implementation passes the visible test.
    assert result.evaluation_result.passed is True
    assert result.hidden_evaluation_result.passed is False

    # Hidden-test failure must prevent overall benchmark success.
    assert result.passed is False

    saved_result = json.loads(result.result_path.read_text(encoding="utf-8"))

    assert saved_result["visible_tests_passed"] is True
    assert saved_result["hidden_tests_passed"] is False
    assert saved_result["benchmark_passed"] is False

    assert saved_result["evaluation"]["visible"]["passed"] is True
    assert saved_result["evaluation"]["hidden"]["passed"] is False

    assert result.report_path.is_file()

    report = result.report_path.read_text(encoding="utf-8")

    assert "FAILED" in report
    assert "hidden_tests_test_failure" in report

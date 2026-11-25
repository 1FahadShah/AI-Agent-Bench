from pathlib import Path
from unittest.mock import patch

import pytest

from ai_agent_bench.evaluation.evaluator import VisibleTestEvaluator
from ai_agent_bench.execution.runner import CommandRunner, ExecutionResult


@pytest.fixture
def workspace(tmp_path: Path) -> Path:
    workspace = tmp_path / "workspace"
    starter_directory = workspace / "starter"
    agent_tests_directory = workspace / "visible_tests"

    starter_directory.mkdir(parents=True)
    agent_tests_directory.mkdir()

    (starter_directory / "pagination.py").write_text(
        "def add(a, b):\n    return a + b\n",
        encoding="utf-8",
    )

    (agent_tests_directory / "test_pagination.py").write_text(
        "from pagination import add\n\ndef test_add():\n    assert add(2, 3) == 5\n",
        encoding="utf-8",
    )

    return workspace


@pytest.fixture
def trusted_tests_directory(tmp_path: Path) -> Path:
    tests_directory = tmp_path / "trusted_benchmark_tests"
    tests_directory.mkdir()

    (tests_directory / "test_pagination.py").write_text(
        "from pagination import add\n\ndef test_add():\n    assert add(2, 3) == 5\n",
        encoding="utf-8",
    )

    return tests_directory


def test_evaluator_passes_when_trusted_visible_tests_pass(
    workspace: Path,
    trusted_tests_directory: Path,
) -> None:
    evaluator = VisibleTestEvaluator(timeout_seconds=30)

    result = evaluator.evaluate(workspace, trusted_tests_directory)

    assert result.evaluation_type == "visible_tests"
    assert result.passed is True
    assert result.exit_code == 0
    assert result.timed_out is False
    assert result.error is None
    assert result.execution_error is False
    assert "1 passed" in result.stdout


def test_evaluator_fails_when_trusted_visible_tests_fail(
    workspace: Path,
    trusted_tests_directory: Path,
) -> None:
    test_file = trusted_tests_directory / "test_pagination.py"

    test_file.write_text(
        "from pagination import add\n\ndef test_add():\n    assert add(2, 3) == 10\n",
        encoding="utf-8",
    )

    evaluator = VisibleTestEvaluator(timeout_seconds=30)

    result = evaluator.evaluate(workspace, trusted_tests_directory)

    assert result.passed is False
    assert result.exit_code != 0
    assert result.error == "Visible tests failed."
    assert result.execution_error is False


def test_evaluator_ignores_agent_modified_test_copies(
    workspace: Path,
    trusted_tests_directory: Path,
) -> None:
    agent_test_file = workspace / "visible_tests" / "test_pagination.py"

    agent_test_file.write_text(
        "def test_fake_success():\n    assert True\n",
        encoding="utf-8",
    )

    evaluator = VisibleTestEvaluator(timeout_seconds=30)

    result = evaluator.evaluate(workspace, trusted_tests_directory)

    assert result.passed is True
    assert result.exit_code == 0
    assert "1 passed" in result.stdout
    assert "test_fake_success" not in result.stdout


def test_evaluator_rejects_missing_workspace(
    tmp_path: Path,
    trusted_tests_directory: Path,
) -> None:
    evaluator = VisibleTestEvaluator()

    with pytest.raises(ValueError, match="Workspace"):
        evaluator.evaluate(tmp_path / "missing", trusted_tests_directory)


def test_evaluator_rejects_missing_trusted_tests_directory(
    workspace: Path,
    tmp_path: Path,
) -> None:
    evaluator = VisibleTestEvaluator()

    with pytest.raises(FileNotFoundError, match="Trusted visible tests"):
        evaluator.evaluate(workspace, tmp_path / "missing_tests")


def test_evaluator_rejects_tests_inside_agent_workspace(
    workspace: Path,
) -> None:
    evaluator = VisibleTestEvaluator()

    with pytest.raises(ValueError, match="outside the agent workspace"):
        evaluator.evaluate(workspace, workspace / "visible_tests")


def test_evaluator_rejects_missing_starter_directory(
    tmp_path: Path,
    trusted_tests_directory: Path,
) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    evaluator = VisibleTestEvaluator()

    with pytest.raises(FileNotFoundError, match="Starter directory"):
        evaluator.evaluate(workspace, trusted_tests_directory)


def test_evaluator_rejects_zero_timeout() -> None:
    with pytest.raises(ValueError, match="greater than zero"):
        VisibleTestEvaluator(timeout_seconds=0)


def test_evaluator_reports_execution_error(
    workspace: Path,
    trusted_tests_directory: Path,
) -> None:
    evaluator = VisibleTestEvaluator(timeout_seconds=30)

    with patch.object(
        CommandRunner,
        "run",
        side_effect=FileNotFoundError("Python executable not found"),
    ):
        result = evaluator.evaluate(workspace, trusted_tests_directory)

    assert result.passed is False
    assert result.execution_error is True
    assert result.exit_code is None
    assert "FileNotFoundError" in result.error


def test_evaluator_reports_timeout(
    workspace: Path,
    trusted_tests_directory: Path,
) -> None:
    evaluator = VisibleTestEvaluator(timeout_seconds=1)

    timeout_result = ExecutionResult(
        command=["python", "-m", "pytest"],
        exit_code=None,
        stdout="",
        stderr="",
        duration_seconds=1.0,
        timed_out=True,
        output_truncated=False,
    )

    with patch.object(
        CommandRunner,
        "run",
        return_value=timeout_result,
    ):
        result = evaluator.evaluate(workspace, trusted_tests_directory)

    assert result.passed is False
    assert result.timed_out is True
    assert result.execution_error is False
    assert result.exit_code is None
    assert result.error == "Visible tests timed out."

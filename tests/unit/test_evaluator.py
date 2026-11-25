from pathlib import Path
from unittest.mock import patch

import pytest

from ai_agent_bench.evaluation.evaluator import VisibleTestEvaluator
from ai_agent_bench.execution.runner import CommandRunner, ExecutionResult


@pytest.fixture
def workspace(tmp_path: Path) -> Path:
    workspace = tmp_path / "workspace"
    tests_directory = workspace / "visible_tests"

    tests_directory.mkdir(parents=True)

    (workspace / "pagination.py").write_text(
        "def add(a, b):\n    return a + b\n",
        encoding="utf-8",
    )

    (tests_directory / "test_pagination.py").write_text(
        "from pagination import add\n\ndef test_add():\n    assert add(2, 3) == 5\n",
        encoding="utf-8",
    )

    return workspace


def test_evaluator_passes_when_visible_tests_pass(workspace: Path) -> None:
    evaluator = VisibleTestEvaluator(timeout_seconds=30)

    result = evaluator.evaluate(workspace, "visible_tests")

    assert result.evaluation_type == "visible_tests"
    assert result.passed is True
    assert result.exit_code == 0
    assert result.timed_out is False
    assert result.error is None
    assert result.execution_error is False
    assert "1 passed" in result.stdout


def test_evaluator_fails_when_visible_tests_fail(workspace: Path) -> None:
    test_file = workspace / "visible_tests" / "test_pagination.py"

    test_file.write_text(
        "from pagination import add\n\ndef test_add():\n    assert add(2, 3) == 10\n",
        encoding="utf-8",
    )

    evaluator = VisibleTestEvaluator(timeout_seconds=30)

    result = evaluator.evaluate(workspace, "visible_tests")

    assert result.passed is False
    assert result.exit_code != 0
    assert result.error == "Visible tests failed."
    assert result.execution_error is False


def test_evaluator_rejects_missing_workspace(tmp_path: Path) -> None:
    evaluator = VisibleTestEvaluator()

    with pytest.raises(ValueError, match="Workspace"):
        evaluator.evaluate(tmp_path / "missing", "visible_tests")


def test_evaluator_rejects_missing_tests_directory(workspace: Path) -> None:
    evaluator = VisibleTestEvaluator()

    with pytest.raises(FileNotFoundError):
        evaluator.evaluate(workspace, "missing_tests")


def test_evaluator_rejects_path_outside_workspace(workspace: Path) -> None:
    evaluator = VisibleTestEvaluator()

    with pytest.raises(ValueError, match="inside the workspace"):
        evaluator.evaluate(workspace, "../outside")


def test_evaluator_rejects_zero_timeout() -> None:
    with pytest.raises(ValueError, match="greater than zero"):
        VisibleTestEvaluator(timeout_seconds=0)


def test_evaluator_reports_execution_error(workspace: Path) -> None:
    evaluator = VisibleTestEvaluator(timeout_seconds=30)

    with patch.object(
        CommandRunner,
        "run",
        side_effect=FileNotFoundError("Python executable not found"),
    ):
        result = evaluator.evaluate(workspace, "visible_tests")

    assert result.passed is False
    assert result.execution_error is True
    assert result.exit_code is None
    assert "FileNotFoundError" in result.error


def test_evaluator_reports_timeout(workspace: Path) -> None:
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
        result = evaluator.evaluate(workspace, "visible_tests")

    assert result.passed is False
    assert result.timed_out is True
    assert result.execution_error is False
    assert result.exit_code is None
    assert result.error == "Visible tests timed out."

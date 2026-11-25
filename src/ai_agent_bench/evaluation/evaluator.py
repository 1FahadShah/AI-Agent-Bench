"""Independent evaluation of benchmark task workspaces."""

import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path

from ai_agent_bench.execution.runner import CommandRunner


@dataclass
class EvaluationResult:
    """Structured outcome of a benchmark evaluation."""

    evaluation_type: str
    passed: bool
    exit_code: int | None
    stdout: str
    stderr: str
    duration_seconds: float
    timed_out: bool
    output_truncated: bool
    error: str | None = None
    execution_error: bool = False
    passed_tests: int = 0
    failed_tests: int = 0
    error_tests: int = 0
    skipped_tests: int = 0

    @property
    def total_tests(self) -> int:
        return self.passed_tests + self.failed_tests + self.error_tests

    @property
    def pass_rate(self) -> float | None:
        if self.total_tests == 0:
            return None
        return self.passed_tests / self.total_tests


class TestEvaluator:
    """Execute trusted tests against an agent's modified workspace."""

    def __init__(
        self,
        evaluation_type: str,
        timeout_seconds: int = 300,
    ) -> None:
        if evaluation_type not in {"visible_tests", "hidden_tests"}:
            raise ValueError("Unsupported evaluation type.")
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be greater than zero")

        self.evaluation_type = evaluation_type
        self.timeout_seconds = timeout_seconds

    @property
    def display_name(self) -> str:
        return "Visible tests" if self.evaluation_type == "visible_tests" else "Hidden tests"

    def evaluate(
        self,
        workspace: Path,
        trusted_tests_directory: Path,
    ) -> EvaluationResult:
        workspace = workspace.resolve()
        tests_directory = trusted_tests_directory.resolve()
        starter_directory = (workspace / "starter").resolve()

        if not workspace.is_dir():
            raise ValueError("Workspace must be an existing directory")
        if tests_directory.is_relative_to(workspace):
            raise ValueError("Trusted tests must be outside the agent workspace")
        if not tests_directory.is_dir():
            raise FileNotFoundError(
                f"Trusted {self.display_name.lower()} directory does not exist: {tests_directory}"
            )
        if not starter_directory.is_relative_to(workspace):
            raise ValueError("Starter directory must remain inside the workspace")
        if not starter_directory.is_dir():
            raise FileNotFoundError("Starter directory does not exist in the workspace")

        runner = CommandRunner(
            workspace=workspace,
            timeout_seconds=self.timeout_seconds,
        )

        command = [
            sys.executable,
            "-m",
            "pytest",
            str(tests_directory),
            "-q",
            "--tb=short",
        ]

        environment = os.environ.copy()
        existing_pythonpath = environment.get("PYTHONPATH", "")
        python_paths = [str(starter_directory)]
        if existing_pythonpath:
            python_paths.append(existing_pythonpath)
        environment["PYTHONPATH"] = os.pathsep.join(python_paths)

        try:
            execution = runner.run(command=command, env=environment)
        except Exception as exc:
            return EvaluationResult(
                evaluation_type=self.evaluation_type,
                passed=False,
                exit_code=None,
                stdout="",
                stderr="",
                duration_seconds=0.0,
                timed_out=False,
                output_truncated=False,
                error=f"Test execution failed ({type(exc).__name__}).",
                execution_error=True,
            )

        summary = self._parse_summary(execution.stdout + "\n" + execution.stderr)

        if execution.timed_out:
            error = f"{self.display_name} timed out."
        elif execution.exit_code != 0:
            error = f"{self.display_name} failed."
        else:
            error = None

        return EvaluationResult(
            evaluation_type=self.evaluation_type,
            passed=execution.exit_code == 0 and not execution.timed_out,
            exit_code=execution.exit_code,
            stdout=execution.stdout,
            stderr=execution.stderr,
            duration_seconds=execution.duration_seconds,
            timed_out=execution.timed_out,
            output_truncated=execution.output_truncated,
            error=error,
            passed_tests=summary["passed"],
            failed_tests=summary["failed"],
            error_tests=summary["errors"],
            skipped_tests=summary["skipped"],
        )

    @staticmethod
    def _parse_summary(output: str) -> dict[str, int]:
        counts = {"passed": 0, "failed": 0, "errors": 0, "skipped": 0}
        patterns = {
            "passed": r"(\d+)\s+passed\b",
            "failed": r"(\d+)\s+failed\b",
            "errors": r"(\d+)\s+error\b",
            "skipped": r"(\d+)\s+skipped\b",
        }

        for key, pattern in patterns.items():
            matches = re.findall(pattern, output)
            if matches:
                counts[key] = int(matches[-1])

        return counts


class VisibleTestEvaluator(TestEvaluator):
    """Evaluate trusted visible tests."""

    def __init__(self, timeout_seconds: int = 300) -> None:
        super().__init__("visible_tests", timeout_seconds)


class HiddenTestEvaluator(TestEvaluator):
    """Evaluate trusted hidden tests without exposing their results to the agent."""

    def __init__(self, timeout_seconds: int = 300) -> None:
        super().__init__("hidden_tests", timeout_seconds)

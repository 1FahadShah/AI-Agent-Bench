"""Independent evaluation of benchmark task workspaces."""

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


class VisibleTestEvaluator:
    """Run visible benchmark tests independently of the agent."""

    def __init__(self, timeout_seconds: int = 300) -> None:
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be greater than zero")

        self.timeout_seconds = timeout_seconds

    def evaluate(
        self,
        workspace: Path,
        visible_tests_path: str,
    ) -> EvaluationResult:
        """Execute visible tests against the agent's modified workspace."""

        workspace = workspace.resolve()
        tests_directory = (workspace / visible_tests_path).resolve()

        if not workspace.is_dir():
            raise ValueError("Workspace must be an existing directory")

        if not tests_directory.is_relative_to(workspace):
            raise ValueError("Visible tests path must remain inside the workspace")

        if not tests_directory.is_dir():
            raise FileNotFoundError(f"Visible tests directory does not exist: {visible_tests_path}")

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
        ]

        try:
            execution = runner.run(command=command)

        except Exception as exc:
            return EvaluationResult(
                evaluation_type="visible_tests",
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

        return EvaluationResult(
            evaluation_type="visible_tests",
            passed=(execution.exit_code == 0 and not execution.timed_out),
            exit_code=execution.exit_code,
            stdout=execution.stdout,
            stderr=execution.stderr,
            duration_seconds=execution.duration_seconds,
            timed_out=execution.timed_out,
            output_truncated=execution.output_truncated,
            error=(
                "Visible tests timed out."
                if execution.timed_out
                else ("Visible tests failed." if execution.exit_code != 0 else None)
            ),
        )

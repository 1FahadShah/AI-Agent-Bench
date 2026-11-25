"""Independent evaluation of benchmark task workspaces."""

import os
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
    """Run trusted benchmark tests against an agent's modified workspace."""

    def __init__(self, timeout_seconds: int = 300) -> None:
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be greater than zero")

        self.timeout_seconds = timeout_seconds

    def evaluate(
        self,
        workspace: Path,
        trusted_visible_tests_directory: Path,
    ) -> EvaluationResult:
        """Execute trusted tests against the agent's modified solution."""

        workspace = workspace.resolve()
        tests_directory = trusted_visible_tests_directory.resolve()
        starter_directory = (workspace / "starter").resolve()

        if not workspace.is_dir():
            raise ValueError("Workspace must be an existing directory")

        if tests_directory.is_relative_to(workspace):
            raise ValueError("Trusted visible tests must be outside the agent workspace")

        if not tests_directory.is_dir():
            raise FileNotFoundError(
                f"Trusted visible tests directory does not exist: {tests_directory}"
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
        ]

        environment = os.environ.copy()
        existing_pythonpath = environment.get("PYTHONPATH", "")

        python_paths = [str(starter_directory)]

        if existing_pythonpath:
            python_paths.append(existing_pythonpath)

        environment["PYTHONPATH"] = os.pathsep.join(python_paths)

        try:
            execution = runner.run(
                command=command,
                env=environment,
            )

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

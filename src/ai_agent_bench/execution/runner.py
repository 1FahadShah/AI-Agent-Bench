"""Controlled command execution within benchmark workspaces."""

import os
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ExecutionResult:
    command: list[str]
    exit_code: int | None
    stdout: str
    stderr: str
    duration_seconds: float
    timed_out: bool
    output_truncated: bool


class CommandRunner:
    """Execute allowlisted commands within a benchmark workspace."""

    ALLOWED_COMMANDS = {
        "python",
        "python.exe",
        "pytest",
        "pytest.exe",
    }

    SAFE_ENVIRONMENT_KEYS = {
        "PATH",
        "SYSTEMROOT",
        "SYSTEMDRIVE",
        "WINDIR",
        "TEMP",
        "TMP",
        "PATHEXT",
        "PYTHONPATH",
        "PYTEST_DISABLE_PLUGIN_AUTOLOAD",
    }

    @classmethod
    def _build_environment(cls, env: dict[str, str] | None) -> dict[str, str]:
        """Pass only explicitly permitted environment variables to child processes."""
        source = os.environ if env is None else env
        return {
            key: value for key, value in source.items() if key.upper() in cls.SAFE_ENVIRONMENT_KEYS
        }

    def __init__(
        self,
        workspace: Path,
        timeout_seconds: int = 30,
        max_output_chars: int = 20_000,
    ) -> None:
        self.workspace = workspace.resolve()
        self.timeout_seconds = timeout_seconds
        self.max_output_chars = max_output_chars

        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be greater than zero")

        if max_output_chars <= 0:
            raise ValueError("max_output_chars must be greater than zero")

        if not self.workspace.exists() or not self.workspace.is_dir():
            raise ValueError("Workspace must be an existing directory")

    def _validate_working_directory(self, working_directory: Path) -> Path:
        resolved_directory = working_directory.resolve()

        if not resolved_directory.exists():
            raise FileNotFoundError(f"Working directory does not exist: {resolved_directory}")

        if not resolved_directory.is_dir():
            raise ValueError("Working directory must be a directory")

        if not resolved_directory.is_relative_to(self.workspace):
            raise ValueError("Working directory must remain inside the benchmark workspace")

        return resolved_directory

    def _validate_command(self, command: list[str]) -> None:
        if not command:
            raise ValueError("Command cannot be empty")

        if not all(isinstance(argument, str) for argument in command):
            raise ValueError("All command arguments must be strings")

        executable_name = Path(command[0]).name.lower()

        if executable_name not in self.ALLOWED_COMMANDS:
            raise ValueError(f"Command is not allowed: {executable_name}")

    def _truncate_output(self, output: str) -> tuple[str, bool]:
        if len(output) <= self.max_output_chars:
            return output, False

        truncated_output = output[: self.max_output_chars]
        truncated_output += "\n\n[OUTPUT TRUNCATED: maximum output size reached]"

        return truncated_output, True

    def run(
        self,
        command: list[str],
        working_directory: Path | None = None,
        env: dict[str, str] | None = None,
    ) -> ExecutionResult:
        """Execute an allowlisted command without invoking a shell.

        An optional environment dictionary can override the subprocess
        environment. When omitted, the subprocess inherits the parent
        process environment.
        """

        self._validate_command(command)

        if working_directory is None:
            working_directory = self.workspace

        resolved_working_directory = self._validate_working_directory(working_directory)

        start_time = time.perf_counter()

        try:
            completed_process = subprocess.run(
                command,
                cwd=resolved_working_directory,
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
                shell=False,
                check=False,
                env=self._build_environment(env),
            )

            duration_seconds = time.perf_counter() - start_time

            stdout, stdout_truncated = self._truncate_output(completed_process.stdout)
            stderr, stderr_truncated = self._truncate_output(completed_process.stderr)

            return ExecutionResult(
                command=command,
                exit_code=completed_process.returncode,
                stdout=stdout,
                stderr=stderr,
                duration_seconds=duration_seconds,
                timed_out=False,
                output_truncated=(stdout_truncated or stderr_truncated),
            )

        except subprocess.TimeoutExpired as exc:
            duration_seconds = time.perf_counter() - start_time

            stdout = exc.stdout or ""
            stderr = exc.stderr or ""

            if isinstance(stdout, bytes):
                stdout = stdout.decode(errors="replace")

            if isinstance(stderr, bytes):
                stderr = stderr.decode(errors="replace")

            stdout, stdout_truncated = self._truncate_output(stdout)
            stderr, stderr_truncated = self._truncate_output(stderr)

            return ExecutionResult(
                command=command,
                exit_code=None,
                stdout=stdout,
                stderr=stderr,
                duration_seconds=duration_seconds,
                timed_out=True,
                output_truncated=(stdout_truncated or stderr_truncated),
            )

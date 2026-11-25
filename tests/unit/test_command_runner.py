import sys
from pathlib import Path

import pytest

from ai_agent_bench.execution.runner import CommandRunner


@pytest.fixture
def workspace(tmp_path: Path) -> Path:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    return workspace


def test_runner_executes_python_command(workspace: Path) -> None:
    runner = CommandRunner(workspace)

    result = runner.run(
        [sys.executable, "-c", "print('hello benchmark')"]
    )

    assert result.exit_code == 0
    assert "hello benchmark" in result.stdout
    assert result.timed_out is False


def test_runner_rejects_disallowed_command(workspace: Path) -> None:
    runner = CommandRunner(workspace)

    with pytest.raises(ValueError, match="Command is not allowed"):
        runner.run(["cmd.exe", "/c", "echo hello"])


def test_runner_rejects_working_directory_outside_workspace(
    workspace: Path,
    tmp_path: Path,
) -> None:
    runner = CommandRunner(workspace)
    outside_directory = tmp_path / "outside"
    outside_directory.mkdir()

    with pytest.raises(
        ValueError,
        match="inside the benchmark workspace",
    ):
        runner.run(
            [sys.executable, "-c", "print('hello')"],
            working_directory=outside_directory,
        )


def test_runner_enforces_timeout(workspace: Path) -> None:
    runner = CommandRunner(
        workspace,
        timeout_seconds=1,
    )

    result = runner.run(
        [
            sys.executable,
            "-c",
            "import time; time.sleep(5)",
        ]
    )

    assert result.timed_out is True
    assert result.exit_code is None
    assert result.duration_seconds < 5


def test_runner_truncates_large_output(workspace: Path) -> None:
    runner = CommandRunner(
        workspace,
        max_output_chars=100,
    )

    result = runner.run(
        [
            sys.executable,
            "-c",
            "print('A' * 500)",
        ]
    )

    assert result.exit_code == 0
    assert result.output_truncated is True
    assert len(result.stdout) > 100
    assert "OUTPUT TRUNCATED" in result.stdout


def test_runner_rejects_empty_command(workspace: Path) -> None:
    runner = CommandRunner(workspace)

    with pytest.raises(ValueError, match="Command cannot be empty"):
        runner.run([])


def test_runner_rejects_invalid_timeout(workspace: Path) -> None:
    with pytest.raises(ValueError, match="greater than zero"):
        CommandRunner(
            workspace,
            timeout_seconds=0,
        )


def test_runner_rejects_invalid_output_limit(workspace: Path) -> None:
    with pytest.raises(ValueError, match="greater than zero"):
        CommandRunner(
            workspace,
            max_output_chars=0,
        )
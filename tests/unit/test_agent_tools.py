import sys
from pathlib import Path

import pytest

from ai_agent_bench.agent.tools import ToolRegistry


@pytest.fixture
def workspace(tmp_path: Path) -> Path:
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    (workspace / "example.py").write_text(
        "print('hello')",
        encoding="utf-8",
    )

    return workspace


@pytest.fixture
def registry(workspace: Path) -> ToolRegistry:
    return ToolRegistry(workspace)


def test_registry_exposes_expected_tools(
    registry: ToolRegistry,
) -> None:
    tools = registry.get_available_tools()

    assert "list_files" in tools
    assert "read_file" in tools
    assert "write_file" in tools
    assert "run_command" in tools


def test_list_files_lists_workspace_contents(
    registry: ToolRegistry,
) -> None:
    result = registry.execute(
        "list_files",
        {"directory": "."},
    )

    assert result.success is True
    assert "example.py" in result.output


def test_read_file_reads_file(
    registry: ToolRegistry,
) -> None:
    result = registry.execute(
        "read_file",
        {"file_path": "example.py"},
    )

    assert result.success is True
    assert "print('hello')" in result.output


def test_write_file_creates_file(
    workspace: Path,
    registry: ToolRegistry,
) -> None:
    result = registry.execute(
        "write_file",
        {
            "file_path": "output/result.txt",
            "content": "benchmark output",
        },
    )

    assert result.success is True

    created_file = workspace / "output" / "result.txt"

    assert created_file.exists()
    assert created_file.read_text(encoding="utf-8") == ("benchmark output")


def test_read_file_rejects_path_traversal(
    registry: ToolRegistry,
) -> None:
    result = registry.execute(
        "read_file",
        {"file_path": "../outside.txt"},
    )

    assert result.success is False
    assert "inside the workspace" in result.error


def test_write_file_rejects_path_traversal(
    registry: ToolRegistry,
) -> None:
    result = registry.execute(
        "write_file",
        {
            "file_path": "../outside.txt",
            "content": "should not be written",
        },
    )

    assert result.success is False
    assert "inside the workspace" in result.error


def test_run_command_executes_python(
    registry: ToolRegistry,
) -> None:
    result = registry.execute(
        "run_command",
        {
            "command": [
                sys.executable,
                "-c",
                "print('tool execution successful')",
            ],
        },
    )

    assert result.success is True
    assert "tool execution successful" in result.output


def test_run_command_rejects_disallowed_command(
    registry: ToolRegistry,
) -> None:
    result = registry.execute(
        "run_command",
        {
            "command": [
                "cmd.exe",
                "/c",
                "echo unsafe",
            ],
        },
    )

    assert result.success is False
    assert "not allowed" in result.error.lower()


def test_unknown_tool_is_rejected(
    registry: ToolRegistry,
) -> None:
    result = registry.execute(
        "delete_everything",
        {},
    )

    assert result.success is False
    assert "Unknown tool" in result.error


def test_invalid_tool_arguments_are_reported(
    registry: ToolRegistry,
) -> None:
    result = registry.execute(
        "read_file",
        {},
    )

    assert result.success is False
    assert "Invalid tool arguments" in result.error

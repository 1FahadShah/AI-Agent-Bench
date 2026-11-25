from pathlib import Path

from typer.testing import CliRunner

from ai_agent_bench.cli import app

runner = CliRunner()


def create_valid_task(tasks_directory: Path, task_id: str = "TEST-001") -> None:
    task_directory = tasks_directory / task_id

    for directory in ("starter", "visible_tests", "hidden_tests", "reference"):
        (task_directory / directory).mkdir(parents=True, exist_ok=True)

    (task_directory / "starter" / "example.py").write_text(
        "def add(a, b):\n    return a + b\n",
        encoding="utf-8",
    )

    task_yaml = f"""
id: {task_id}
name: CLI Test Task
description: A task for testing the CLI.
category: software_engineering
difficulty: easy
instructions: Fix the example implementation.
environment:
  timeout_seconds: 30
  max_agent_steps: 5
evaluation:
  evaluation_type: tests
  visible_tests_path: visible_tests
  hidden_tests_path: hidden_tests
  reference_solution_path: reference
tags:
  - cli
"""

    (task_directory / "task.yaml").write_text(task_yaml, encoding="utf-8")


def test_cli_displays_help() -> None:
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "list-tasks" in result.output
    assert "validate" in result.output
    assert "run" in result.output


def test_cli_lists_available_tasks(tmp_path: Path) -> None:
    tasks_directory = tmp_path / "tasks"
    create_valid_task(tasks_directory)

    result = runner.invoke(
        app,
        ["list-tasks", "--tasks-dir", str(tasks_directory)],
    )

    assert result.exit_code == 0
    assert "TEST-001" in result.output
    assert "CLI Test Task" in result.output


def test_cli_reports_when_no_tasks_exist(tmp_path: Path) -> None:
    tasks_directory = tmp_path / "empty_tasks"
    tasks_directory.mkdir()

    result = runner.invoke(
        app,
        ["list-tasks", "--tasks-dir", str(tasks_directory)],
    )

    assert result.exit_code == 1
    assert "No benchmark tasks found" in result.output


def test_cli_validates_one_task(tmp_path: Path) -> None:
    tasks_directory = tmp_path / "tasks"
    create_valid_task(tasks_directory)

    result = runner.invoke(
        app,
        ["validate", "TEST-001", "--tasks-dir", str(tasks_directory)],
    )

    assert result.exit_code == 0
    assert "PASSED: TEST-001" in result.output
    assert "1 task(s) passed" in result.output


def test_cli_validates_all_tasks(tmp_path: Path) -> None:
    tasks_directory = tmp_path / "tasks"
    create_valid_task(tasks_directory, "TEST-001")
    create_valid_task(tasks_directory, "TEST-002")

    result = runner.invoke(
        app,
        ["validate", "--tasks-dir", str(tasks_directory)],
    )

    assert result.exit_code == 0
    assert "PASSED: TEST-001" in result.output
    assert "PASSED: TEST-002" in result.output
    assert "2 task(s) passed" in result.output


def test_cli_reports_invalid_task(tmp_path: Path) -> None:
    tasks_directory = tmp_path / "tasks"
    tasks_directory.mkdir()

    result = runner.invoke(
        app,
        ["validate", "MISSING-001", "--tasks-dir", str(tasks_directory)],
    )

    assert result.exit_code == 1
    assert "FAILED: MISSING-001" in result.output

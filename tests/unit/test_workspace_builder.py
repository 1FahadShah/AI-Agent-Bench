from pathlib import Path

import pytest
import yaml

from ai_agent_bench.execution.workspace import WorkspaceBuilder


@pytest.fixture
def task_directory(tmp_path: Path) -> Path:
    task_directory = tmp_path / "tasks" / "PB-SWE-001"

    (task_directory / "starter").mkdir(parents=True)
    (task_directory / "visible_tests").mkdir()
    (task_directory / "hidden_tests").mkdir()
    (task_directory / "reference").mkdir()

    (task_directory / "starter" / "pagination.py").write_text(
        "def paginate(items):\n    return items\n",
        encoding="utf-8",
    )

    (task_directory / "visible_tests" / "test_pagination.py").write_text(
        "def test_example():\n    assert True\n",
        encoding="utf-8",
    )

    (task_directory / "hidden_tests" / "secret_test.py").write_text(
        "SECRET HIDDEN TEST",
        encoding="utf-8",
    )

    (task_directory / "reference" / "pagination.py").write_text(
        "REFERENCE SOLUTION",
        encoding="utf-8",
    )

    task_data = {
        "id": "PB-SWE-001",
        "name": "Test Task",
        "description": "Workspace builder test",
        "category": "software_engineering",
        "difficulty": "medium",
        "instructions": "Fix the example.",
        "evaluation": {
            "evaluation_type": "tests",
            "visible_tests_path": "visible_tests",
            "hidden_tests_path": "hidden_tests",
            "reference_solution_path": "reference",
        },
    }

    (task_directory / "task.yaml").write_text(
        yaml.safe_dump(task_data, sort_keys=False),
        encoding="utf-8",
    )

    return task_directory


def test_workspace_contains_only_agent_visible_assets(
    task_directory: Path,
    tmp_path: Path,
) -> None:
    builder = WorkspaceBuilder(
        tasks_directory=task_directory.parent,
        workspace_root=tmp_path / "workspaces",
    )

    workspace = builder.build(
        task_id="PB-SWE-001",
        run_id="run-001",
    )

    assert (workspace / "task.yaml").exists()
    assert (workspace / "starter" / "pagination.py").exists()
    assert (workspace / "visible_tests" / "test_pagination.py").exists()

    assert not (workspace / "hidden_tests").exists()
    assert not (workspace / "reference").exists()


def test_workspace_task_metadata_is_sanitized(
    task_directory: Path,
    tmp_path: Path,
) -> None:
    builder = WorkspaceBuilder(
        tasks_directory=task_directory.parent,
        workspace_root=tmp_path / "workspaces",
    )

    workspace = builder.build(
        task_id="PB-SWE-001",
        run_id="run-002",
    )

    task_file = workspace / "task.yaml"

    with task_file.open("r", encoding="utf-8") as file:
        task_data = yaml.safe_load(file)

    evaluation = task_data["evaluation"]

    assert "visible_tests_path" in evaluation
    assert "hidden_tests_path" not in evaluation
    assert "reference_solution_path" not in evaluation


def test_workspace_creation_rejects_existing_workspace(
    task_directory: Path,
    tmp_path: Path,
) -> None:
    builder = WorkspaceBuilder(
        tasks_directory=task_directory.parent,
        workspace_root=tmp_path / "workspaces",
    )

    builder.build(
        task_id="PB-SWE-001",
        run_id="run-003",
    )

    with pytest.raises(FileExistsError):
        builder.build(
            task_id="PB-SWE-001",
            run_id="run-003",
        )


def test_workspace_creation_rejects_invalid_task_id(
    task_directory: Path,
    tmp_path: Path,
) -> None:
    builder = WorkspaceBuilder(
        tasks_directory=task_directory.parent,
        workspace_root=tmp_path / "workspaces",
    )

    with pytest.raises(ValueError):
        builder.build(
            task_id="../outside",
            run_id="run-004",
        )
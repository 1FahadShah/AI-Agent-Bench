from pathlib import Path

from ai_agent_bench.benchmark.models import BenchmarkTask
from ai_agent_bench.benchmark.validator import TaskValidator


def create_task_workspace(
    tasks_directory: Path,
    task_id: str = "TEST-001",
) -> Path:
    task_directory = tasks_directory / task_id

    for directory_name in (
        "starter",
        "visible_tests",
        "hidden_tests",
        "reference",
    ):
        (task_directory / directory_name).mkdir(parents=True, exist_ok=True)

    (task_directory / "starter" / "example.py").write_text(
        "# Starter file\n",
        encoding="utf-8",
    )

    return task_directory


def create_task(
    task_id: str = "TEST-001",
    visible_tests_path: str = "visible_tests",
    hidden_tests_path: str = "hidden_tests",
    reference_solution_path: str = "reference",
) -> BenchmarkTask:
    return BenchmarkTask(
        id=task_id,
        name="Validator Test Task",
        description="A task used to test the validator.",
        category="software_engineering",
        difficulty="medium",
        instructions="Test task instructions.",
        evaluation={
            "evaluation_type": "tests",
            "visible_tests_path": visible_tests_path,
            "hidden_tests_path": hidden_tests_path,
            "reference_solution_path": reference_solution_path,
        },
    )


def test_valid_task_has_no_errors(tmp_path):
    tasks_directory = tmp_path / "tasks"
    create_task_workspace(tasks_directory)

    validator = TaskValidator(tasks_directory)
    task = create_task()

    errors = validator.validate_task(task)

    assert errors == []


def test_missing_required_directory_is_detected(tmp_path):
    tasks_directory = tmp_path / "tasks"
    task_directory = create_task_workspace(tasks_directory)

    (task_directory / "hidden_tests").rmdir()

    validator = TaskValidator(tasks_directory)
    task = create_task()

    errors = validator.validate_task(task)

    assert any("hidden_tests" in error for error in errors)


def test_empty_starter_directory_is_detected(tmp_path):
    tasks_directory = tmp_path / "tasks"
    task_directory = create_task_workspace(tasks_directory)

    (task_directory / "starter" / "example.py").unlink()

    validator = TaskValidator(tasks_directory)
    task = create_task()

    errors = validator.validate_task(task)

    assert "Starter directory contains no files" in errors


def test_evaluation_path_escape_is_detected(tmp_path):
    tasks_directory = tmp_path / "tasks"
    create_task_workspace(tasks_directory)

    validator = TaskValidator(tasks_directory)
    task = create_task(visible_tests_path="../outside")

    errors = validator.validate_task(task)

    assert any("escapes task directory" in error for error in errors)


def test_missing_evaluation_path_is_detected(tmp_path):
    tasks_directory = tmp_path / "tasks"
    create_task_workspace(tasks_directory)

    validator = TaskValidator(tasks_directory)
    task = create_task(visible_tests_path="missing_tests")

    errors = validator.validate_task(task)

    assert any("does not exist" in error for error in errors)

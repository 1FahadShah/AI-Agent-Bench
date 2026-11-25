from pathlib import Path

from ai_agent_bench.benchmark.models import BenchmarkTask


class TaskValidator:
    REQUIRED_TASK_DIRECTORIES = (
        "starter",
        "visible_tests",
        "hidden_tests",
        "reference",
    )

    def __init__(self, tasks_directory: Path):
        self.tasks_directory = tasks_directory

    def validate_task(self, task: BenchmarkTask) -> list[str]:
        errors: list[str] = []

        task_directory = self.tasks_directory / task.id

        if not task_directory.exists():
            errors.append(f"Task directory does not exist: {task_directory}")
            return errors

        if not task_directory.is_dir():
            errors.append(f"Task path is not a directory: {task_directory}")
            return errors

        # Validate the task ID against the directory name.
        if task_directory.name != task.id:
            errors.append(
                f"Task ID '{task.id}' does not match directory "
                f"name '{task_directory.name}'"
            )

        # Validate required task directories.
        for directory_name in self.REQUIRED_TASK_DIRECTORIES:
            directory_path = task_directory / directory_name

            if not directory_path.exists():
                errors.append(
                    f"Required task directory is missing: {directory_name}"
                )
            elif not directory_path.is_dir():
                errors.append(
                    f"Expected directory but found another file type: "
                    f"{directory_name}"
                )

        # Validate evaluation paths.
        evaluation_paths = {
            "visible_tests_path": task.evaluation.visible_tests_path,
            "hidden_tests_path": task.evaluation.hidden_tests_path,
            "reference_solution_path": task.evaluation.reference_solution_path,
        }

        for field_name, relative_path in evaluation_paths.items():
            if relative_path is None:
                errors.append(f"Evaluation field is missing: {field_name}")
                continue

            path = Path(relative_path)

            if path.is_absolute():
                errors.append(
                    f"Evaluation path must be relative: {field_name}"
                )
                continue

            resolved_path = (task_directory / path).resolve()
            resolved_task_directory = task_directory.resolve()

            # Prevent evaluation paths from escaping the task directory.
            if not resolved_path.is_relative_to(resolved_task_directory):
                errors.append(
                    f"Evaluation path escapes task directory: {field_name}"
                )
                continue

            if not resolved_path.exists():
                errors.append(
                    f"Evaluation path does not exist: {field_name} "
                    f"-> {relative_path}"
                )

        # Validate that the starter directory contains files.
        starter_directory = task_directory / "starter"

        if starter_directory.exists() and starter_directory.is_dir():
            starter_files = [
                path for path in starter_directory.rglob("*") if path.is_file()
            ]

            if not starter_files:
                errors.append("Starter directory contains no files")

        return errors

    def validate_all(self, task_ids: list[str]) -> dict[str, list[str]]:
        results: dict[str, list[str]] = {}

        for task_id in task_ids:
            results[task_id] = []

            task_directory = self.tasks_directory / task_id

            if not task_directory.exists():
                results[task_id].append(
                    f"Task directory does not exist: {task_directory}"
                )
                continue

            task_file = task_directory / "task.yaml"

            if not task_file.exists():
                results[task_id].append("task.yaml is missing")
                continue

            results[task_id].append(
                "Task definition exists. Load it with TaskLoader "
                "to perform schema validation."
            )

        return results
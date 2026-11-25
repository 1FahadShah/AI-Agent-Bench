import re
import shutil
from pathlib import Path

import yaml


class WorkspaceBuilder:
    """Build an isolated workspace containing only agent-visible task assets."""

    ALLOWED_DIRECTORIES = (
        "starter",
        "visible_tests",
    )

    def __init__(
        self,
        tasks_directory: Path,
        workspace_root: Path,
    ) -> None:
        self.tasks_directory = tasks_directory.resolve()
        self.workspace_root = workspace_root.resolve()

    def build(self, task_id: str, run_id: str) -> Path:
        """Create a workspace for a benchmark run."""

        if not re.fullmatch(r"[A-Za-z0-9_-]+", task_id):
            raise ValueError(f"Invalid task ID: {task_id}")

        if not re.fullmatch(r"[A-Za-z0-9_-]+", run_id):
            raise ValueError(f"Invalid run ID: {run_id}")

        task_directory = self.tasks_directory / task_id

        if not task_directory.exists() or not task_directory.is_dir():
            raise FileNotFoundError(f"Task directory not found: {task_directory}")

        workspace_directory = self.workspace_root / task_id / run_id

        if workspace_directory.exists():
            raise FileExistsError(f"Workspace already exists: {workspace_directory}")

        task_file = task_directory / "task.yaml"

        if not task_file.is_file():
            raise FileNotFoundError(f"Task definition not found: {task_file}")

        with task_file.open("r", encoding="utf-8") as file:
            task_data = yaml.safe_load(file)

        if not isinstance(task_data, dict):
            raise ValueError(f"Invalid task definition: {task_file}")

        # Remove evaluator-only metadata from the task definition
        # presented to the agent.
        evaluation = task_data.get("evaluation", {})

        if isinstance(evaluation, dict):
            evaluation.pop("hidden_tests_path", None)
            evaluation.pop("reference_solution_path", None)

        workspace_directory.mkdir(parents=True, exist_ok=False)

        # Copy only explicitly permitted directories.
        for directory_name in self.ALLOWED_DIRECTORIES:
            source_directory = task_directory / directory_name

            if not source_directory.exists():
                raise FileNotFoundError(f"Required task directory not found: {source_directory}")

            if not source_directory.is_dir():
                raise ValueError(f"Expected a directory: {source_directory}")

            destination_directory = workspace_directory / directory_name

            shutil.copytree(
                source_directory,
                destination_directory,
                ignore=shutil.ignore_patterns(
                    "__pycache__",
                    "*.pyc",
                    ".pytest_cache",
                ),
            )

        # Write the sanitized task definition into the agent workspace.
        workspace_task_file = workspace_directory / "task.yaml"

        with workspace_task_file.open("w", encoding="utf-8") as file:
            yaml.safe_dump(
                task_data,
                file,
                sort_keys=False,
                allow_unicode=True,
            )

        return workspace_directory

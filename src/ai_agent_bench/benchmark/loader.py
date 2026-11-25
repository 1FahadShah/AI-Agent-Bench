from pathlib import Path

import yaml

from ai_agent_bench.benchmark.models import BenchmarkTask


class TaskLoader:
    def __init__(self, tasks_directory: Path):
        self.tasks_directory = tasks_directory

    def load_task(self, task_id: str) -> BenchmarkTask:
        task_directory = self.tasks_directory / task_id
        task_file = task_directory / "task.yaml"

        if not task_file.exists():
            raise FileNotFoundError(f"Task definition not found: {task_file}")

        with task_file.open("r", encoding="utf-8") as file:
            task_data = yaml.safe_load(file)

        if not isinstance(task_data, dict):
            raise ValueError(f"Invalid task definition: {task_file}")

        task = BenchmarkTask.model_validate(task_data)

        if task.id != task_id:
            raise ValueError(
                f"Task ID mismatch: directory contains '{task_id}', "
                f"but definition declares '{task.id}'"
            )

        return task

    def list_tasks(self) -> list[str]:
        if not self.tasks_directory.exists():
            return []

        return sorted(
            directory.name
            for directory in self.tasks_directory.iterdir()
            if directory.is_dir() and (directory / "task.yaml").exists()
        )

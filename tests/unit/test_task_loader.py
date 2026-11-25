from pathlib import Path

from ai_agent_bench.benchmark.loader import TaskLoader
from ai_agent_bench.benchmark.models import TaskCategory, TaskDifficulty


PROJECT_ROOT = Path(__file__).resolve().parents[2]
TASKS_DIRECTORY = PROJECT_ROOT / "benchmark" / "tasks"


def test_load_pb_swe_001():
    loader = TaskLoader(TASKS_DIRECTORY)

    task = loader.load_task("PB-SWE-001")

    assert task.id == "PB-SWE-001"
    assert task.name == "Fix Pagination Boundary Bug"
    assert task.category == TaskCategory.SOFTWARE_ENGINEERING
    assert task.difficulty == TaskDifficulty.MEDIUM


def test_task_environment_configuration():
    loader = TaskLoader(TASKS_DIRECTORY)

    task = loader.load_task("PB-SWE-001")

    assert task.environment.timeout_seconds == 300
    assert task.environment.max_agent_steps == 30


def test_list_tasks():
    loader = TaskLoader(TASKS_DIRECTORY)

    task_ids = loader.list_tasks()

    assert "PB-SWE-001" in task_ids


def test_task_slug():
    loader = TaskLoader(TASKS_DIRECTORY)

    task = loader.load_task("PB-SWE-001")

    assert task.task_slug == "pb_swe_001"

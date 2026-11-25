from enum import Enum

from pydantic import BaseModel, Field


class TaskCategory(str, Enum):
    SOFTWARE_ENGINEERING = "software_engineering"
    TERMINAL = "terminal"


class TaskDifficulty(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class EvaluationType(str, Enum):
    TESTS = "tests"
    STATE_CHECKS = "state_checks"
    HYBRID = "hybrid"


class TaskEnvironment(BaseModel):
    python_version: str = "3.11+"
    timeout_seconds: int = Field(default=300, gt=0)
    max_agent_steps: int = Field(default=30, gt=0)


class TaskEvaluation(BaseModel):
    evaluation_type: EvaluationType
    visible_tests_path: str | None = None
    hidden_tests_path: str | None = None
    reference_solution_path: str | None = None


class BenchmarkTask(BaseModel):
    id: str
    name: str
    description: str
    category: TaskCategory
    difficulty: TaskDifficulty
    instructions: str

    environment: TaskEnvironment = Field(default_factory=TaskEnvironment)
    evaluation: TaskEvaluation

    tags: list[str] = Field(default_factory=list)

    @property
    def task_slug(self) -> str:
        return self.id.lower().replace("-", "_")

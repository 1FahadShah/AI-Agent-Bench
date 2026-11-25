"""End-to-end orchestration for benchmark task execution."""

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from ai_agent_bench.agent.interface import AgentRequest, AgentResult
from ai_agent_bench.agent.llm_agent import LLMAgent
from ai_agent_bench.agent.runtime import AgentRuntime
from ai_agent_bench.agent.tools import ToolRegistry
from ai_agent_bench.benchmark.loader import TaskLoader
from ai_agent_bench.benchmark.models import BenchmarkTask, EvaluationType
from ai_agent_bench.benchmark.validator import TaskValidator
from ai_agent_bench.config import LLMConfig
from ai_agent_bench.evaluation.evaluator import (
    EvaluationResult,
    VisibleTestEvaluator,
)
from ai_agent_bench.execution.workspace import WorkspaceBuilder
from ai_agent_bench.llm.base import LLMProvider
from ai_agent_bench.llm.openrouter import OpenRouterProvider
from ai_agent_bench.results.storage import ResultStorage


@dataclass
class BenchmarkRun:
    """Complete outcome of one benchmark execution."""

    run_id: str
    task_id: str
    workspace: Path
    agent_result: AgentResult
    evaluation_result: EvaluationResult
    result_path: Path

    @property
    def passed(self) -> bool:
        """Return whether the visible-test evaluation passed.

        This does not represent full benchmark certification because
        hidden-test evaluation is not implemented yet.
        """
        return self.evaluation_result.passed


class BenchmarkOrchestrator:
    """Coordinate task loading, agent execution, evaluation, and persistence."""

    def __init__(
        self,
        tasks_directory: Path,
        workspace_root: Path,
        results_directory: Path,
        config: LLMConfig,
        provider: LLMProvider | None = None,
    ) -> None:
        self.tasks_directory = tasks_directory.resolve()
        self.workspace_root = workspace_root.resolve()
        self.config = config

        self.loader = TaskLoader(self.tasks_directory)
        self.validator = TaskValidator(self.tasks_directory)

        self.workspace_builder = WorkspaceBuilder(
            tasks_directory=self.tasks_directory,
            workspace_root=self.workspace_root,
        )

        self.result_storage = ResultStorage(results_directory)
        self.provider = provider or OpenRouterProvider(config)

    def run(self, task_id: str) -> BenchmarkRun:
        """Execute one benchmark task from loading through result persistence."""

        task = self.loader.load_task(task_id)
        self._validate_task(task)

        run_id = self._generate_run_id()

        task_directory = (self.tasks_directory / task.id).resolve()
        trusted_tests_directory = self._get_trusted_tests_directory(
            task,
            task_directory,
        )

        workspace = self.workspace_builder.build(
            task_id=task.id,
            run_id=run_id,
        )

        tool_registry = ToolRegistry(
            workspace=workspace,
            timeout_seconds=task.environment.timeout_seconds,
        )

        max_steps = min(
            self.config.max_steps,
            task.environment.max_agent_steps,
        )

        request = self._build_agent_request(
            task=task,
            workspace=workspace,
            available_tools=tool_registry.get_available_tools(),
            max_steps=max_steps,
        )

        agent = LLMAgent(
            provider=self.provider,
            model=self.config.model,
            temperature=self.config.temperature,
        )

        agent_result = AgentRuntime(tool_registry).run(
            agent=agent,
            request=request,
        )

        evaluator = VisibleTestEvaluator(
            timeout_seconds=task.environment.timeout_seconds,
        )

        evaluation_result = evaluator.evaluate(
            workspace=workspace,
            trusted_visible_tests_directory=trusted_tests_directory,
        )

        result_path = self.result_storage.save_run(
            run_id=run_id,
            result=self._build_result_record(
                task=task,
                workspace=workspace,
                agent_result=agent_result,
                evaluation_result=evaluation_result,
            ),
        )

        return BenchmarkRun(
            run_id=run_id,
            task_id=task.id,
            workspace=workspace,
            agent_result=agent_result,
            evaluation_result=evaluation_result,
            result_path=result_path,
        )

    def _validate_task(self, task: BenchmarkTask) -> None:
        """Validate task assets and supported evaluation requirements."""

        errors = self.validator.validate_task(task)

        if errors:
            details = "\n".join(f"- {error}" for error in errors)
            raise ValueError(f"Benchmark task validation failed:\n{details}")

        if task.evaluation.evaluation_type != EvaluationType.TESTS:
            raise NotImplementedError(
                "Only tests-based evaluation is currently supported. "
                f"Received: {task.evaluation.evaluation_type.value}"
            )

        if not task.evaluation.visible_tests_path:
            raise ValueError("Tests-based evaluation requires visible_tests_path.")

    def _get_trusted_tests_directory(
        self,
        task: BenchmarkTask,
        task_directory: Path,
    ) -> Path:
        """Resolve original visible tests without allowing path traversal."""

        tests_path = Path(task.evaluation.visible_tests_path)

        if tests_path.is_absolute():
            raise ValueError("Visible tests path must be relative.")

        trusted_directory = (task_directory / tests_path).resolve()

        if not trusted_directory.is_relative_to(task_directory):
            raise ValueError("Trusted visible tests path must remain inside the task directory.")

        if not trusted_directory.is_dir():
            raise FileNotFoundError(
                f"Trusted visible tests directory does not exist: {trusted_directory}"
            )

        return trusted_directory

    @staticmethod
    def _generate_run_id() -> str:
        """Generate a timestamped, collision-resistant run identifier."""

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        unique_suffix = uuid4().hex[:8]

        return f"{timestamp}_{unique_suffix}"

    @staticmethod
    def _build_agent_request(
        task: BenchmarkTask,
        workspace: Path,
        available_tools: list[str],
        max_steps: int,
    ) -> AgentRequest:
        """Construct the standardized agent request."""

        task_description = f"{task.description}\n\nTask instructions:\n{task.instructions}"

        return AgentRequest(
            task_id=task.id,
            task_description=task_description,
            workspace=workspace,
            available_tools=available_tools,
            max_steps=max_steps,
        )

    def _build_result_record(
        self,
        task: BenchmarkTask,
        workspace: Path,
        agent_result: AgentResult,
        evaluation_result: EvaluationResult,
    ) -> dict:
        """Build a JSON-serializable benchmark result record."""

        return {
            "task": {
                "task_id": task.id,
                "task_name": task.name,
                "category": task.category.value,
                "difficulty": task.difficulty.value,
                "evaluation_type": task.evaluation.evaluation_type.value,
            },
            "agent": {
                "provider": self.provider.provider_name,
                "model": self.config.model,
                "completed": agent_result.completed,
                "final_message": agent_result.final_message,
                "steps_used": agent_result.steps_used,
                "error": agent_result.error,
                "metadata": agent_result.metadata,
            },
            "evaluation": asdict(evaluation_result),
            "workspace": str(workspace),
            "visible_tests_passed": evaluation_result.passed,
        }

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
    HiddenTestEvaluator,
    VisibleTestEvaluator,
)
from ai_agent_bench.evaluation.failure_analysis import (
    FailureAnalysis,
    FailureAnalyzer,
)
from ai_agent_bench.evaluation.scoring import EvaluationScore, ScoringEngine
from ai_agent_bench.execution.workspace import WorkspaceBuilder
from ai_agent_bench.llm.base import LLMProvider
from ai_agent_bench.llm.openrouter import OpenRouterProvider
from ai_agent_bench.results.reporting import BenchmarkReporter
from ai_agent_bench.results.storage import ResultStorage


@dataclass
class BenchmarkRun:
    """Complete outcome of one benchmark execution."""

    run_id: str
    task_id: str
    workspace: Path
    agent_result: AgentResult
    evaluation_result: EvaluationResult
    hidden_evaluation_result: EvaluationResult
    score: EvaluationScore
    failure_analysis: FailureAnalysis
    result_path: Path
    report_path: Path

    @property
    def passed(self) -> bool:
        """Return whether the complete benchmark passed."""
        return self.score.benchmark_passed


class BenchmarkOrchestrator:
    """Coordinate task execution, independent evaluation, and reporting."""

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
        self.results_directory = results_directory.resolve()
        self.config = config

        self.loader = TaskLoader(self.tasks_directory)
        self.validator = TaskValidator(self.tasks_directory)

        self.workspace_builder = WorkspaceBuilder(
            tasks_directory=self.tasks_directory,
            workspace_root=self.workspace_root,
        )

        self.result_storage = ResultStorage(self.results_directory)
        self.provider = provider or OpenRouterProvider(config)

    def run(self, task_id: str) -> BenchmarkRun:
        """Execute one benchmark task from loading through reporting."""
        task = self.loader.load_task(task_id)
        self._validate_task(task)

        run_id = self._generate_run_id()
        task_directory = (self.tasks_directory / task.id).resolve()

        visible_tests_directory = self._get_trusted_tests_directory(
            task_directory,
            task.evaluation.visible_tests_path,
            "visible tests",
        )
        hidden_tests_directory = self._get_trusted_tests_directory(
            task_directory,
            task.evaluation.hidden_tests_path,
            "hidden tests",
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

        # Evaluation happens only after the agent has stopped.
        # Evaluator outputs are never added to agent history or prompts.
        visible_result = VisibleTestEvaluator(
            timeout_seconds=task.environment.timeout_seconds,
        ).evaluate(
            workspace=workspace,
            trusted_tests_directory=visible_tests_directory,
        )

        hidden_result = HiddenTestEvaluator(
            timeout_seconds=task.environment.timeout_seconds,
        ).evaluate(
            workspace=workspace,
            trusted_tests_directory=hidden_tests_directory,
        )

        score = ScoringEngine.score(
            visible=visible_result,
            hidden=hidden_result,
            agent_completed=agent_result.completed,
        )

        failure_analysis = FailureAnalyzer.analyze(
            agent_result=agent_result,
            visible=visible_result,
            hidden=hidden_result,
        )

        report = BenchmarkReporter.generate(
            task_id=task.id,
            run_id=run_id,
            score=score,
            failure_analysis=failure_analysis,
        )

        result_path = self.result_storage.save_run(
            run_id=run_id,
            result=self._build_result_record(
                task=task,
                workspace=workspace,
                agent_result=agent_result,
                visible_result=visible_result,
                hidden_result=hidden_result,
                score=score,
                failure_analysis=failure_analysis,
                report=report,
            ),
        )

        report_path = result_path.with_suffix(".md")
        report_path.write_text(report, encoding="utf-8")

        return BenchmarkRun(
            run_id=run_id,
            task_id=task.id,
            workspace=workspace,
            agent_result=agent_result,
            evaluation_result=visible_result,
            hidden_evaluation_result=hidden_result,
            score=score,
            failure_analysis=failure_analysis,
            result_path=result_path,
            report_path=report_path,
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

        if not task.evaluation.hidden_tests_path:
            raise ValueError("Tests-based evaluation requires hidden_tests_path.")

    @staticmethod
    def _get_trusted_tests_directory(
        task_directory: Path,
        relative_path: str | None,
        description: str,
    ) -> Path:
        """Resolve a trusted test directory without allowing path traversal."""
        if not relative_path:
            raise ValueError(f"Tests-based evaluation requires {description} path.")

        tests_path = Path(relative_path)

        if tests_path.is_absolute():
            raise ValueError(f"{description.capitalize()} path must be relative.")

        trusted_directory = (task_directory / tests_path).resolve()

        if not trusted_directory.is_relative_to(task_directory):
            raise ValueError(f"Trusted {description} path must remain inside the task directory.")

        if not trusted_directory.is_dir():
            raise FileNotFoundError(
                f"Trusted {description} directory does not exist: {trusted_directory}"
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
        visible_result: EvaluationResult,
        hidden_result: EvaluationResult,
        score: EvaluationScore,
        failure_analysis: FailureAnalysis,
        report: str,
    ) -> dict:
        """Build a JSON-serializable benchmark result record."""
        # Preserve the original flat evaluation fields for compatibility.
        evaluation_record = {
            **asdict(visible_result),
            "visible": asdict(visible_result),
            "hidden": asdict(hidden_result),
            "score": asdict(score),
            "failure_analysis": asdict(failure_analysis),
            "benchmark_passed": score.benchmark_passed,
        }

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
            "evaluation": evaluation_record,
            "workspace": str(workspace),
            "visible_tests_passed": visible_result.passed,
            "hidden_tests_passed": hidden_result.passed,
            "agent_completed": agent_result.completed,
            "benchmark_passed": score.benchmark_passed,
            "report": report,
        }

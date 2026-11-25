"""Command-line interface for AI Agent Bench."""

from pathlib import Path

import typer

from ai_agent_bench.benchmark.loader import TaskLoader
from ai_agent_bench.benchmark.validator import TaskValidator
from ai_agent_bench.config import LLMConfig
from ai_agent_bench.orchestration.service import BenchmarkOrchestrator

app = typer.Typer(
    name="ai-agent-bench",
    help="Run and evaluate AI agent benchmark tasks.",
    no_args_is_help=True,
)


@app.command("list-tasks")
def list_tasks(
    tasks_dir: Path = typer.Option(
        Path("benchmark/tasks"),
        "--tasks-dir",
        help="Directory containing benchmark task definitions.",
    ),
) -> None:
    """List available benchmark tasks."""
    loader = TaskLoader(tasks_dir.resolve())
    task_ids = loader.list_tasks()

    if not task_ids:
        typer.echo(f"No benchmark tasks found in: {tasks_dir.resolve()}")
        raise typer.Exit(code=1)

    typer.echo(f"Available benchmark tasks ({len(task_ids)}):\n")

    for task_id in task_ids:
        try:
            task = loader.load_task(task_id)
            typer.echo(f"{task.id} | {task.name} | {task.category.value} | {task.difficulty.value}")
        except Exception as exc:
            typer.echo(f"{task_id} | ERROR loading task: {exc}")


@app.command("validate")
def validate_tasks(
    task_id: str | None = typer.Argument(
        None,
        help="Optional task ID. Omit to validate every available task.",
    ),
    tasks_dir: Path = typer.Option(
        Path("benchmark/tasks"),
        "--tasks-dir",
        help="Directory containing benchmark task definitions.",
    ),
) -> None:
    """Validate one benchmark task or all available tasks."""
    tasks_directory = tasks_dir.resolve()
    loader = TaskLoader(tasks_directory)
    validator = TaskValidator(tasks_directory)

    task_ids = [task_id] if task_id else loader.list_tasks()

    if not task_ids:
        typer.echo(f"No benchmark tasks found in: {tasks_directory}")
        raise typer.Exit(code=1)

    total_errors = 0

    for current_task_id in task_ids:
        typer.echo(f"\nValidating {current_task_id}...")

        try:
            task = loader.load_task(current_task_id)
            errors = validator.validate_task(task)
        except Exception as exc:
            errors = [str(exc)]

        if errors:
            total_errors += len(errors)
            typer.echo(f"FAILED: {current_task_id}", err=True)

            for error in errors:
                typer.echo(f"  - {error}", err=True)
        else:
            typer.echo(f"PASSED: {current_task_id}")

    if total_errors:
        typer.echo(f"\nValidation failed with {total_errors} error(s).", err=True)
        raise typer.Exit(code=1)

    typer.echo(f"\nValidation successful: {len(task_ids)} task(s) passed.")


@app.command("run")
def run_benchmark(
    task_id: str = typer.Argument(
        ...,
        help="ID of the benchmark task to execute.",
    ),
    tasks_dir: Path = typer.Option(
        Path("benchmark/tasks"),
        "--tasks-dir",
        help="Directory containing benchmark task definitions.",
    ),
    workspace_dir: Path = typer.Option(
        Path("results/workspaces"),
        "--workspace-dir",
        help="Root directory for agent task workspaces.",
    ),
    results_dir: Path = typer.Option(
        Path("results/runs"),
        "--results-dir",
        help="Directory where benchmark results are stored.",
    ),
) -> None:
    """Execute a benchmark task using the configured LLM agent."""
    typer.echo(f"Starting benchmark: {task_id}")

    try:
        config = LLMConfig.from_env()

        typer.echo(f"Provider: {config.provider}")
        typer.echo(f"Model: {config.model}")
        typer.echo("Initializing benchmark orchestrator...")

        orchestrator = BenchmarkOrchestrator(
            tasks_directory=tasks_dir,
            workspace_root=workspace_dir,
            results_directory=results_dir,
            config=config,
        )

        result = orchestrator.run(task_id)

    except Exception as exc:
        typer.echo(f"\nBenchmark execution failed: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    status = "PASSED" if result.passed else "FAILED"

    typer.echo("\n=== BENCHMARK RESULT ===")
    typer.echo(f"Task: {result.task_id}")
    typer.echo(f"Run ID: {result.run_id}")
    typer.echo(f"Status: {status}")
    typer.echo(f"Test score: {result.score.score:.2f}/100")
    typer.echo(f"Tests passed: {result.score.passed_tests}/{result.score.total_tests}")
    typer.echo(f"Agent completed: {result.agent_result.completed}")
    typer.echo(f"Steps used: {result.agent_result.steps_used}")
    typer.echo(f"JSON result: {result.result_path}")
    typer.echo(f"Markdown report: {result.report_path}")
    typer.echo(f"Workspace: {result.workspace}")

    if not result.passed:
        raise typer.Exit(code=1)


def main() -> None:
    """Run the command-line application."""
    app()


if __name__ == "__main__":
    main()

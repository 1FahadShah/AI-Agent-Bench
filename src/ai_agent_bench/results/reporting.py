"""Human-readable reports for benchmark runs."""

from ai_agent_bench.evaluation.failure_analysis import FailureAnalysis
from ai_agent_bench.evaluation.scoring import EvaluationScore


class BenchmarkReporter:
    """Format aggregate benchmark outcomes for human review."""

    @staticmethod
    def generate(
        task_id: str,
        run_id: str,
        score: EvaluationScore,
        failure_analysis: FailureAnalysis,
    ) -> str:
        status = "PASSED" if score.benchmark_passed else "FAILED"
        agent_status = "Completed" if score.agent_completed else "Incomplete"

        lines = [
            f"# Benchmark Report: {task_id}",
            "",
            f"- Run ID: {run_id}",
            f"- Overall status: {status}",
            f"- Agent execution: {agent_status}",
            f"- Test score: {score.score:.2f}/100",
            "",
            "## Test Summary",
            "",
            f"- Total tests: {score.total_tests}",
            f"- Passed: {score.passed_tests}",
            f"- Failed: {score.failed_tests}",
            f"- Errors: {score.error_tests}",
            f"- Skipped: {score.skipped_tests}",
            "",
            "## Evaluation Pass Rates",
            "",
            f"- Visible: {BenchmarkReporter._format_rate(score.visible_pass_rate)}",
            f"- Hidden: {BenchmarkReporter._format_rate(score.hidden_pass_rate)}",
            "",
            "## Failure Analysis",
            "",
            failure_analysis.summary,
        ]

        if failure_analysis.categories:
            lines.extend(
                [
                    "",
                    "Categories:",
                    *[f"- {category}" for category in failure_analysis.categories],
                ]
            )

        return "\n".join(lines) + "\n"

    @staticmethod
    def _format_rate(rate: float | None) -> str:
        if rate is None:
            return "Unavailable"
        return f"{rate * 100:.2f}%"

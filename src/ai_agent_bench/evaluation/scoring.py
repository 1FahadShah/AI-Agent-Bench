"""Transparent scoring for benchmark evaluation results."""

from dataclasses import dataclass

from ai_agent_bench.evaluation.evaluator import EvaluationResult


@dataclass(frozen=True)
class EvaluationScore:
    """Aggregate score derived from test execution outcomes."""

    score: float
    passed_tests: int
    failed_tests: int
    error_tests: int
    skipped_tests: int
    total_tests: int
    agent_completed: bool
    benchmark_passed: bool
    visible_pass_rate: float | None
    hidden_pass_rate: float | None


class ScoringEngine:
    """Calculate reproducible benchmark scores from evaluation results."""

    @staticmethod
    def score(
        visible: EvaluationResult,
        hidden: EvaluationResult,
        agent_completed: bool = True,
    ) -> EvaluationScore:
        passed = visible.passed_tests + hidden.passed_tests
        failed = visible.failed_tests + hidden.failed_tests
        errors = visible.error_tests + hidden.error_tests
        skipped = visible.skipped_tests + hidden.skipped_tests
        total = passed + failed + errors

        score = round((passed / total) * 100, 2) if total else 0.0

        benchmark_passed = agent_completed and visible.passed and hidden.passed and total > 0

        return EvaluationScore(
            score=score,
            passed_tests=passed,
            failed_tests=failed,
            error_tests=errors,
            skipped_tests=skipped,
            total_tests=total,
            agent_completed=agent_completed,
            benchmark_passed=benchmark_passed,
            visible_pass_rate=visible.pass_rate,
            hidden_pass_rate=hidden.pass_rate,
        )

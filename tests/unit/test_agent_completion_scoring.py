from ai_agent_bench.evaluation.evaluator import EvaluationResult
from ai_agent_bench.evaluation.scoring import ScoringEngine


def make_result(evaluation_type: str) -> EvaluationResult:
    return EvaluationResult(
        evaluation_type=evaluation_type,
        passed=True,
        exit_code=0,
        stdout="",
        stderr="",
        duration_seconds=0.1,
        timed_out=False,
        output_truncated=False,
        passed_tests=5,
    )


def test_incomplete_agent_cannot_pass_benchmark_when_all_tests_pass() -> None:
    visible = make_result("visible_tests")
    hidden = make_result("hidden_tests")

    score = ScoringEngine.score(
        visible=visible,
        hidden=hidden,
        agent_completed=False,
    )

    assert score.score == 100.0
    assert score.visible_pass_rate == 1.0
    assert score.hidden_pass_rate == 1.0
    assert score.agent_completed is False
    assert score.benchmark_passed is False


def test_completed_agent_passes_when_both_evaluations_pass() -> None:
    visible = make_result("visible_tests")
    hidden = make_result("hidden_tests")

    score = ScoringEngine.score(
        visible=visible,
        hidden=hidden,
        agent_completed=True,
    )

    assert score.agent_completed is True
    assert score.benchmark_passed is True

from pathlib import Path

from ai_agent_bench.agent.interface import AgentResult
from ai_agent_bench.evaluation.evaluator import (
    EvaluationResult,
    HiddenTestEvaluator,
)
from ai_agent_bench.evaluation.failure_analysis import FailureAnalyzer
from ai_agent_bench.evaluation.scoring import ScoringEngine
from ai_agent_bench.results.reporting import BenchmarkReporter


def make_result(
    evaluation_type: str,
    passed: bool,
    passed_tests: int,
    failed_tests: int = 0,
    error_tests: int = 0,
) -> EvaluationResult:
    return EvaluationResult(
        evaluation_type=evaluation_type,
        passed=passed,
        exit_code=0 if passed else 1,
        stdout="",
        stderr="",
        duration_seconds=0.1,
        timed_out=False,
        output_truncated=False,
        passed_tests=passed_tests,
        failed_tests=failed_tests,
        error_tests=error_tests,
    )


def test_hidden_evaluator_runs_trusted_tests(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    starter = workspace / "starter"
    trusted_tests = tmp_path / "trusted_hidden_tests"

    starter.mkdir(parents=True)
    trusted_tests.mkdir()

    (starter / "solution.py").write_text(
        "def add(a, b):\n    return a + b\n",
        encoding="utf-8",
    )
    (trusted_tests / "test_solution.py").write_text(
        "from solution import add\n\ndef test_add():\n    assert add(2, 3) == 5\n",
        encoding="utf-8",
    )

    result = HiddenTestEvaluator(timeout_seconds=30).evaluate(
        workspace,
        trusted_tests,
    )

    assert result.evaluation_type == "hidden_tests"
    assert result.passed is True
    assert result.passed_tests == 1
    assert result.total_tests == 1
    assert result.pass_rate == 1.0


def test_hidden_evaluator_rejects_tests_inside_workspace(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "workspace"
    (workspace / "starter").mkdir(parents=True)
    hidden_tests = workspace / "hidden_tests"
    hidden_tests.mkdir()

    evaluator = HiddenTestEvaluator()

    try:
        evaluator.evaluate(workspace, hidden_tests)
    except ValueError as exc:
        assert "outside the agent workspace" in str(exc)
    else:
        raise AssertionError("Expected evaluator to reject workspace-local tests")


def test_scoring_combines_visible_and_hidden_results() -> None:
    visible = make_result("visible_tests", True, passed_tests=8)
    hidden = make_result(
        "hidden_tests",
        False,
        passed_tests=7,
        failed_tests=3,
    )

    score = ScoringEngine.score(visible, hidden)

    assert score.passed_tests == 15
    assert score.failed_tests == 3
    assert score.total_tests == 18
    assert score.score == 83.33
    assert score.visible_pass_rate == 1.0
    assert score.hidden_pass_rate == 0.7
    assert score.benchmark_passed is False


def test_scoring_passes_only_when_both_evaluations_pass() -> None:
    visible = make_result("visible_tests", True, passed_tests=5)
    hidden = make_result("hidden_tests", True, passed_tests=5)

    score = ScoringEngine.score(visible, hidden)

    assert score.score == 100.0
    assert score.benchmark_passed is True


def test_scoring_does_not_pass_when_no_tests_were_collected() -> None:
    visible = make_result("visible_tests", False, passed_tests=0)
    hidden = make_result("hidden_tests", False, passed_tests=0)

    score = ScoringEngine.score(visible, hidden)

    assert score.total_tests == 0
    assert score.score == 0.0
    assert score.benchmark_passed is False


def test_failure_analyzer_classifies_hidden_test_failure() -> None:
    agent = AgentResult(
        completed=True,
        final_message="Completed the task.",
        steps_used=4,
    )
    visible = make_result("visible_tests", True, passed_tests=5)
    hidden = make_result(
        "hidden_tests",
        False,
        passed_tests=3,
        failed_tests=2,
    )

    analysis = FailureAnalyzer.analyze(agent, visible, hidden)

    assert analysis.failed is True
    assert "hidden_tests_test_failure" in analysis.categories


def test_failure_analyzer_identifies_agent_execution_error() -> None:
    agent = AgentResult(
        completed=False,
        final_message="",
        steps_used=1,
        error="Provider failure",
    )
    visible = make_result("visible_tests", False, passed_tests=0)
    hidden = make_result("hidden_tests", False, passed_tests=0)

    analysis = FailureAnalyzer.analyze(agent, visible, hidden)

    assert "agent_execution_error" in analysis.categories


def test_reporter_generates_aggregate_report() -> None:
    visible = make_result("visible_tests", True, passed_tests=5)
    hidden = make_result("hidden_tests", False, passed_tests=3, failed_tests=2)
    score = ScoringEngine.score(visible, hidden)

    agent = AgentResult(
        completed=True,
        final_message="Completed.",
        steps_used=4,
    )
    analysis = FailureAnalyzer.analyze(agent, visible, hidden)

    report = BenchmarkReporter.generate(
        task_id="PB-SWE-001",
        run_id="test-run",
        score=score,
        failure_analysis=analysis,
    )

    assert "# Benchmark Report: PB-SWE-001" in report
    assert "Test score: 80.00/100" in report
    assert "Hidden: 60.00%" in report
    assert "FAILED" in report
    assert "hidden_tests_test_failure" in report

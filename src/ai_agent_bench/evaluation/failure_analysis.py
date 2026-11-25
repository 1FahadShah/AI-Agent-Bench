"""Evidence-based classification of benchmark execution failures."""

from dataclasses import dataclass

from ai_agent_bench.agent.interface import AgentResult
from ai_agent_bench.evaluation.evaluator import EvaluationResult


@dataclass(frozen=True)
class FailureAnalysis:
    """Failure classifications supported by execution evidence."""

    categories: list[str]
    summary: str
    failed: bool


class FailureAnalyzer:
    """Classify observable agent and evaluator outcomes."""

    @staticmethod
    def analyze(
        agent_result: AgentResult,
        visible: EvaluationResult,
        hidden: EvaluationResult,
    ) -> FailureAnalysis:
        categories: list[str] = []

        if not agent_result.completed:
            if agent_result.error:
                categories.append("agent_execution_error")
            else:
                categories.append("agent_incomplete")

        for result in (visible, hidden):
            if result.timed_out:
                categories.append(f"{result.evaluation_type}_timeout")
            elif result.execution_error:
                categories.append(f"{result.evaluation_type}_execution_error")
            elif not result.passed:
                categories.append(f"{result.evaluation_type}_test_failure")

        if not categories:
            return FailureAnalysis(
                categories=[],
                summary="Agent completed and all evaluated tests passed.",
                failed=False,
            )

        descriptions = {
            "agent_execution_error": "The agent encountered an execution error.",
            "agent_incomplete": "The agent did not return a completed result.",
            "visible_tests_timeout": "Visible test execution exceeded its timeout.",
            "hidden_tests_timeout": "Hidden test execution exceeded its timeout.",
            "visible_tests_execution_error": (
                "Visible test execution encountered an infrastructure error."
            ),
            "hidden_tests_execution_error": (
                "Hidden test execution encountered an infrastructure error."
            ),
            "visible_tests_test_failure": "One or more visible tests failed.",
            "hidden_tests_test_failure": "One or more hidden tests failed.",
        }

        summary = " ".join(descriptions[category] for category in categories)

        return FailureAnalysis(
            categories=categories,
            summary=summary,
            failed=True,
        )

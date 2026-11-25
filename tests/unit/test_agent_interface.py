from pathlib import Path

import pytest

from ai_agent_bench.agent.interface import (
    Agent,
    AgentAction,
    AgentRequest,
    AgentResult,
)


class DummyAgent(Agent):
    """Minimal test implementation of the step-based Agent interface."""

    def decide(
        self,
        request: AgentRequest,
        history: list[dict],
    ) -> AgentAction:
        return AgentAction(
            action_type="final",
            final_message=f"Completed task {request.task_id}",
        )


def test_agent_request_stores_task_information(
    tmp_path: Path,
) -> None:
    request = AgentRequest(
        task_id="PB-SWE-001",
        task_description="Fix the pagination bug.",
        workspace=tmp_path,
        available_tools=[
            "list_files",
            "read_file",
            "write_file",
            "run_command",
        ],
    )

    assert request.task_id == "PB-SWE-001"
    assert request.task_description == "Fix the pagination bug."
    assert request.workspace == tmp_path
    assert request.max_steps == 20


def test_agent_request_custom_step_limit(
    tmp_path: Path,
) -> None:
    request = AgentRequest(
        task_id="PB-SWE-001",
        task_description="Fix pagination.",
        workspace=tmp_path,
        available_tools=[],
        max_steps=5,
    )

    assert request.max_steps == 5


def test_agent_action_tool_call() -> None:
    action = AgentAction(
        action_type="tool",
        tool_name="read_file",
        arguments={"file_path": "pagination.py"},
    )

    assert action.action_type == "tool"
    assert action.tool_name == "read_file"
    assert action.arguments["file_path"] == "pagination.py"


def test_agent_action_final() -> None:
    action = AgentAction(
        action_type="final",
        final_message="I fixed the pagination bug.",
    )

    assert action.action_type == "final"
    assert action.final_message == "I fixed the pagination bug."


def test_agent_result_defaults() -> None:
    result = AgentResult(
        completed=True,
        final_message="Task completed.",
        steps_used=3,
    )

    assert result.completed is True
    assert result.final_message == "Task completed."
    assert result.steps_used == 3
    assert result.error is None
    assert result.metadata == {}


def test_agent_result_can_contain_error() -> None:
    result = AgentResult(
        completed=False,
        final_message="Task failed.",
        steps_used=2,
        error="Agent reached its step limit.",
    )

    assert result.completed is False
    assert result.error == "Agent reached its step limit."


def test_agent_interface_is_abstract() -> None:
    with pytest.raises(TypeError):
        Agent()


def test_concrete_agent_implements_interface(
    tmp_path: Path,
) -> None:
    request = AgentRequest(
        task_id="PB-SWE-001",
        task_description="Fix pagination.",
        workspace=tmp_path,
        available_tools=[],
    )

    agent = DummyAgent()

    action = agent.decide(request, history=[])

    assert action.action_type == "final"
    assert "PB-SWE-001" in action.final_message
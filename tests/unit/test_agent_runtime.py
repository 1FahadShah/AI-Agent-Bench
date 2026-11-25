import pytest

from ai_agent_bench.agent.interface import Agent, AgentAction, AgentRequest
from ai_agent_bench.agent.runtime import AgentRuntime
from ai_agent_bench.agent.tools import ToolRegistry


class ScriptedAgent(Agent):
    def __init__(self, actions):
        self.actions = actions
        self.calls = 0

    def decide(self, request, history):
        action = self.actions[self.calls]
        self.calls += 1
        return action


class FailingAgent(Agent):
    def decide(self, request, history):
        raise RuntimeError("Simulated agent failure")


class InvalidAgent:
    def decide(self, request, history):
        return "not an AgentAction"


@pytest.fixture
def workspace(tmp_path):
    workspace_path = tmp_path / "workspace"
    workspace_path.mkdir()
    (workspace_path / "example.txt").write_text(
        "Hello benchmark",
        encoding="utf-8",
    )
    return workspace_path


@pytest.fixture
def runtime(workspace):
    registry = ToolRegistry(workspace)
    return AgentRuntime(registry)


@pytest.fixture
def request_data(workspace):
    return AgentRequest(
        task_id="TEST-001",
        task_description="Test task",
        workspace=workspace,
        available_tools=[
            "list_files",
            "read_file",
            "write_file",
            "run_command",
        ],
        max_steps=5,
    )


def test_final_action_completes_task(runtime, request_data):
    agent = ScriptedAgent(
        [
            AgentAction(
                action_type="final",
                final_message="Task completed successfully.",
            )
        ]
    )

    result = runtime.run(agent, request_data)

    assert result.completed is True
    assert result.final_message == "Task completed successfully."
    assert result.steps_used == 1
    assert result.error is None


def test_tool_call_is_executed_and_recorded(runtime, request_data):
    agent = ScriptedAgent(
        [
            AgentAction(
                action_type="tool",
                tool_name="list_files",
                arguments={"directory": "."},
            ),
            AgentAction(
                action_type="final",
                final_message="I inspected the workspace.",
            ),
        ]
    )

    result = runtime.run(agent, request_data)

    assert result.completed is True
    assert result.steps_used == 2

    history = result.metadata["history"]

    assert len(history) == 2
    assert history[0]["action_type"] == "tool"
    assert history[0]["tool_name"] == "list_files"
    assert history[0]["tool_success"] is True
    assert "example.txt" in history[0]["tool_output"]
    assert history[1]["action_type"] == "final"


def test_tool_failure_is_recorded_and_agent_can_continue(
    runtime,
    request_data,
):
    agent = ScriptedAgent(
        [
            AgentAction(
                action_type="tool",
                tool_name="read_file",
                arguments={"file_path": "missing_file.txt"},
            ),
            AgentAction(
                action_type="final",
                final_message="Recovered from tool failure.",
            ),
        ]
    )

    result = runtime.run(agent, request_data)

    assert result.completed is True
    assert result.steps_used == 2

    first_step = result.metadata["history"][0]

    assert first_step["tool_success"] is False
    assert first_step["tool_error"] is not None


def test_disallowed_tool_is_blocked(runtime, request_data):
    request_data.available_tools = ["list_files"]

    agent = ScriptedAgent(
        [
            AgentAction(
                action_type="tool",
                tool_name="write_file",
                arguments={
                    "file_path": "new.txt",
                    "content": "Should not be written",
                },
            )
        ]
    )

    result = runtime.run(agent, request_data)

    assert result.completed is False
    assert "Tool not allowed" in result.error

    assert not (request_data.workspace / "new.txt").exists()


def test_max_steps_is_enforced(runtime, request_data):
    request_data.max_steps = 2

    agent = ScriptedAgent(
        [
            AgentAction(
                action_type="tool",
                tool_name="list_files",
                arguments={"directory": "."},
            ),
            AgentAction(
                action_type="tool",
                tool_name="list_files",
                arguments={"directory": "."},
            ),
            AgentAction(
                action_type="final",
                final_message="Should never be reached.",
            ),
        ]
    )

    result = runtime.run(agent, request_data)

    assert result.completed is False
    assert result.steps_used == 2
    assert result.error == "Maximum steps exceeded."
    assert len(result.metadata["history"]) == 2


def test_agent_exception_is_handled(runtime, request_data):
    result = runtime.run(FailingAgent(), request_data)

    assert result.completed is False
    assert result.steps_used == 1
    assert "Simulated agent failure" in result.error


def test_invalid_agent_response_is_handled(runtime, request_data):
    result = runtime.run(InvalidAgent(), request_data)

    assert result.completed is False
    assert result.steps_used == 1
    assert "Agent decision must return an AgentAction" in result.error


def test_invalid_action_type_is_rejected(runtime, request_data):
    agent = ScriptedAgent(
        [
            AgentAction(
                action_type="invalid_action",
            )
        ]
    )

    result = runtime.run(agent, request_data)

    assert result.completed is False
    assert "Unsupported action type" in result.error


def test_tool_action_without_tool_name_is_rejected(runtime, request_data):
    agent = ScriptedAgent(
        [
            AgentAction(
                action_type="tool",
                tool_name=None,
            )
        ]
    )

    result = runtime.run(agent, request_data)

    assert result.completed is False
    assert "requires a tool_name" in result.error

from pathlib import Path

from ai_agent_bench.agent.interface import AgentRequest
from ai_agent_bench.agent.llm_agent import LLMAgent
from ai_agent_bench.agent.runtime import AgentRuntime
from ai_agent_bench.agent.tools import ToolRegistry
from ai_agent_bench.llm.models import LLMResponse


class MockLLMProvider:
    """Mock provider that returns predefined LLM responses."""

    provider_name = "mock"

    def __init__(self, responses: list[str]) -> None:
        self.responses = responses
        self.requests = []

    def generate(self, request):
        self.requests.append(request)

        response_content = self.responses.pop(0)

        return LLMResponse(
            content=response_content,
            model="mock-model",
            provider="mock",
        )


def test_llm_agent_executes_tool_and_completes_task(tmp_path: Path):
    # Arrange: create a benchmark workspace.
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    (workspace / "example.txt").write_text(
        "Hello benchmark",
        encoding="utf-8",
    )

    request = AgentRequest(
        task_id="TEST-LLM-001",
        task_description="Inspect the workspace and report its files.",
        workspace=workspace,
        available_tools=["list_files", "read_file"],
        max_steps=5,
    )

    provider = MockLLMProvider(
        responses=[
            ('{"action_type":"tool","tool_name":"list_files","arguments":{"directory":"."}}'),
            ('{"action_type":"final","final_message":"The workspace contains example.txt."}'),
        ]
    )

    agent = LLMAgent(
        provider=provider,
        model="mock-model",
    )

    runtime = AgentRuntime(
        ToolRegistry(workspace),
    )

    # Act: execute the real agent through the real runtime.
    result = runtime.run(agent, request)

    # Assert: task completed successfully.
    assert result.completed is True
    assert result.final_message == ("The workspace contains example.txt.")
    assert result.steps_used == 2

    # Assert: the tool was actually executed.
    history = result.metadata["history"]

    assert len(history) == 2
    assert history[0]["action_type"] == "tool"
    assert history[0]["tool_name"] == "list_files"
    assert history[0]["tool_success"] is True
    assert "example.txt" in history[0]["tool_output"]

    # Assert: the second LLM request received execution history.
    assert len(provider.requests) == 2

    second_request = provider.requests[1]

    assert len(second_request.messages) == 2

    user_message = second_request.messages[1].content

    assert "example.txt" in user_message
    assert "list_files" in user_message
    assert "tool_success" in user_message

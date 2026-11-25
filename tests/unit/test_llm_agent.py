import pytest

from ai_agent_bench.agent.interface import AgentAction, AgentRequest
from ai_agent_bench.agent.llm_agent import LLMAgent
from ai_agent_bench.llm.models import LLMResponse


class MockLLMProvider:
    """Mock provider that returns predefined LLM responses."""

    provider_name = "mock"

    def __init__(self, responses: list[str]) -> None:
        self.responses = responses
        self.requests = []
        self.call_count = 0

    def generate(self, request):
        self.requests.append(request)

        content = self.responses[self.call_count]
        self.call_count += 1

        return LLMResponse(
            content=content,
            model=request.model,
            provider=self.provider_name,
        )


@pytest.fixture
def agent_request(tmp_path):
    return AgentRequest(
        task_id="PB-SWE-001",
        task_description="Fix the pagination bug.",
        workspace=tmp_path,
        available_tools=[
            "list_files",
            "read_file",
            "write_file",
            "run_command",
        ],
        max_steps=5,
    )


def test_llm_agent_implements_agent_interface() -> None:
    from ai_agent_bench.agent.interface import Agent

    provider = MockLLMProvider(['{"action_type": "final", "final_message": "Done."}'])

    agent = LLMAgent(
        provider=provider,
        model="test-model",
    )

    assert isinstance(agent, Agent)


def test_llm_agent_parses_tool_action(agent_request) -> None:
    provider = MockLLMProvider(
        [
            (
                '{"action_type": "tool", '
                '"tool_name": "read_file", '
                '"arguments": {"file_path": "pagination.py"}}'
            )
        ]
    )

    agent = LLMAgent(provider=provider, model="test-model")

    action = agent.decide(agent_request, history=[])

    assert isinstance(action, AgentAction)
    assert action.action_type == "tool"
    assert action.tool_name == "read_file"
    assert action.arguments == {"file_path": "pagination.py"}


def test_llm_agent_parses_final_action(agent_request) -> None:
    provider = MockLLMProvider(['{"action_type": "final", "final_message": "Task completed."}'])

    agent = LLMAgent(provider=provider, model="test-model")

    action = agent.decide(agent_request, history=[])

    assert action.action_type == "final"
    assert action.final_message == "Task completed."


def test_llm_agent_builds_valid_llm_request(agent_request) -> None:
    provider = MockLLMProvider(['{"action_type": "final", "final_message": "Done."}'])

    agent = LLMAgent(
        provider=provider,
        model="test-model",
        temperature=0.5,
    )

    agent.decide(agent_request, history=[])

    llm_request = provider.requests[0]

    assert llm_request.model == "test-model"
    assert llm_request.temperature == 0.5
    assert llm_request.messages[0].role == "system"
    assert llm_request.messages[1].role == "user"

    prompt = llm_request.messages[0].content

    assert "PB-SWE-001" in prompt
    assert "list_files" in prompt
    assert "read_file" in prompt
    assert "write_file" in prompt
    assert "run_command" in prompt


def test_llm_agent_includes_execution_history(agent_request) -> None:
    provider = MockLLMProvider(['{"action_type": "final", "final_message": "Done."}'])

    agent = LLMAgent(provider=provider, model="test-model")

    history = [
        {
            "step": 1,
            "action_type": "tool",
            "tool_name": "list_files",
            "arguments": {"directory": "."},
            "tool_success": True,
            "tool_output": "pagination.py",
            "tool_error": None,
        }
    ]

    agent.decide(agent_request, history)

    user_message = provider.requests[0].messages[1].content

    assert "pagination.py" in user_message
    assert "list_files" in user_message
    assert "tool_success" in user_message


def test_llm_agent_uses_history_on_subsequent_decisions(
    agent_request,
) -> None:
    provider = MockLLMProvider(
        [
            ('{"action_type": "tool", "tool_name": "list_files", "arguments": {"directory": "."}}'),
            '{"action_type": "final", "final_message": "Done."}',
        ]
    )

    agent = LLMAgent(provider=provider, model="test-model")

    first_action = agent.decide(agent_request, history=[])

    history = [
        {
            "step": 1,
            "action_type": "tool",
            "tool_name": first_action.tool_name,
            "arguments": first_action.arguments,
            "tool_success": True,
            "tool_output": "pagination.py",
            "tool_error": None,
        }
    ]

    second_action = agent.decide(agent_request, history)

    assert second_action.action_type == "final"
    assert len(provider.requests) == 2
    assert "pagination.py" in provider.requests[1].messages[1].content


def test_llm_agent_rejects_malformed_provider_response(
    agent_request,
) -> None:
    provider = MockLLMProvider(["not valid JSON"])

    agent = LLMAgent(provider=provider, model="test-model")

    with pytest.raises(ValueError):
        agent.decide(agent_request, history=[])


def test_llm_agent_rejects_empty_available_tools(agent_request) -> None:
    agent_request.available_tools = []

    provider = MockLLMProvider(['{"action_type": "final", "final_message": "Done."}'])

    agent = LLMAgent(provider=provider, model="test-model")

    agent.decide(agent_request, history=[])

    prompt = provider.requests[0].messages[0].content

    assert "No tools are available" in prompt

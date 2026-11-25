import pytest

from ai_agent_bench.agent.action_parser import ActionParser
from ai_agent_bench.agent.interface import AgentAction


@pytest.fixture
def parser() -> ActionParser:
    return ActionParser()


def test_parse_valid_tool_action(parser: ActionParser) -> None:
    raw_response = """
    {
        "action_type": "tool",
        "tool_name": "read_file",
        "arguments": {
            "file_path": "pagination.py"
        }
    }
    """

    action = parser.parse(raw_response)

    assert isinstance(action, AgentAction)
    assert action.action_type == "tool"
    assert action.tool_name == "read_file"
    assert action.arguments == {"file_path": "pagination.py"}
    assert action.final_message is None


def test_parse_valid_final_action(parser: ActionParser) -> None:
    raw_response = """
    {
        "action_type": "final",
        "final_message": "The pagination bug is fixed."
    }
    """

    action = parser.parse(raw_response)

    assert isinstance(action, AgentAction)
    assert action.action_type == "final"
    assert action.final_message == "The pagination bug is fixed."


@pytest.mark.parametrize(
    "raw_response",
    [
        "",
        "not valid json",
        '{"action_type": "tool",',
        "[]",
        '"hello"',
        "null",
    ],
)
def test_reject_invalid_json_or_non_object(
    parser: ActionParser,
    raw_response: str,
) -> None:
    with pytest.raises(ValueError):
        parser.parse(raw_response)


@pytest.mark.parametrize(
    "raw_response",
    [
        '{"action_type": "unknown"}',
        '{"action_type": "tool_call"}',
        '{"tool_name": "read_file"}',
        '{"action_type": 123}',
    ],
)
def test_reject_unsupported_or_missing_action_type(
    parser: ActionParser,
    raw_response: str,
) -> None:
    with pytest.raises(ValueError):
        parser.parse(raw_response)


@pytest.mark.parametrize(
    "raw_response",
    [
        '{"action_type": "tool"}',
        '{"action_type": "tool", "tool_name": ""}',
        '{"action_type": "tool", "tool_name": 123}',
        '{"action_type": "tool", "tool_name": "read_file", "arguments": []}',
        '{"action_type": "tool", "tool_name": "read_file", "arguments": "invalid"}',
    ],
)
def test_reject_invalid_tool_actions(
    parser: ActionParser,
    raw_response: str,
) -> None:
    with pytest.raises(ValueError):
        parser.parse(raw_response)


@pytest.mark.parametrize(
    "raw_response",
    [
        '{"action_type": "final"}',
        '{"action_type": "final", "final_message": ""}',
        '{"action_type": "final", "final_message": 123}',
    ],
)
def test_reject_invalid_final_actions(
    parser: ActionParser,
    raw_response: str,
) -> None:
    with pytest.raises(ValueError):
        parser.parse(raw_response)


@pytest.mark.parametrize(
    "raw_response",
    [
        ('{"action_type": "tool", "tool_name": "read_file", "arguments": {}, "unexpected": true}'),
        ('{"action_type": "final", "final_message": "Done", "tool_name": "read_file"}'),
    ],
)
def test_reject_unexpected_fields(
    parser: ActionParser,
    raw_response: str,
) -> None:
    with pytest.raises(ValueError):
        parser.parse(raw_response)


def test_reject_duplicate_json_keys(parser: ActionParser) -> None:
    raw_response = """
    {
        "action_type": "tool",
        "action_type": "final",
        "final_message": "Done"
    }
    """

    with pytest.raises(ValueError, match="Duplicate JSON key"):
        parser.parse(raw_response)

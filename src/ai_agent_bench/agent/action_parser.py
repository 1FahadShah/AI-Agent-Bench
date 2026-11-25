import json
from typing import Any

from ai_agent_bench.agent.interface import AgentAction


def _reject_duplicate_keys(
    pairs: list[tuple[str, Any]],
) -> dict[str, Any]:
    """Reject duplicate keys while decoding a JSON object."""

    result = {}

    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON key: {key}")

        result[key] = value

    return result


class ActionParser:
    """Parse and validate structured LLM responses into agent actions."""

    def parse(self, raw_response: str) -> AgentAction:
        """Convert a JSON response into a validated AgentAction."""

        try:
            payload = json.loads(
                raw_response,
                object_pairs_hook=_reject_duplicate_keys,
            )
        except (json.JSONDecodeError, TypeError) as exc:
            raise ValueError("LLM response must contain valid JSON.") from exc

        if not isinstance(payload, dict):
            raise ValueError("LLM response must be a JSON object.")

        action_type = payload.get("action_type")

        if action_type == "tool":
            return self._parse_tool_action(payload)

        if action_type == "final":
            return self._parse_final_action(payload)

        raise ValueError("Unsupported or missing action_type.")

    def _parse_tool_action(self, payload: dict[str, Any]) -> AgentAction:
        expected_fields = {"action_type", "tool_name", "arguments"}

        if set(payload) != expected_fields:
            raise ValueError("Tool action contains missing or unexpected fields.")

        tool_name = payload["tool_name"]
        arguments = payload["arguments"]

        if not isinstance(tool_name, str) or not tool_name.strip():
            raise ValueError("Tool action requires a non-empty tool_name.")

        if not isinstance(arguments, dict):
            raise ValueError("Tool action arguments must be a JSON object.")

        return AgentAction(
            action_type="tool",
            tool_name=tool_name,
            arguments=arguments,
        )

    def _parse_final_action(self, payload: dict[str, Any]) -> AgentAction:
        expected_fields = {"action_type", "final_message"}

        if set(payload) != expected_fields:
            raise ValueError("Final action contains missing or unexpected fields.")

        final_message = payload["final_message"]

        if not isinstance(final_message, str) or not final_message.strip():
            raise ValueError("Final action requires a non-empty final_message.")

        return AgentAction(
            action_type="final",
            final_message=final_message,
        )

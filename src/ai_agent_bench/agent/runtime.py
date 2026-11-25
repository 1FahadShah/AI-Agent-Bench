from ai_agent_bench.agent.interface import Agent, AgentAction, AgentRequest, AgentResult
from ai_agent_bench.agent.tools import ToolRegistry


class AgentRuntime:
    """Orchestrates an agent's decisions and tool execution."""

    def __init__(self, tool_registry: ToolRegistry):
        self.tool_registry = tool_registry

    def run(self, agent: Agent, request: AgentRequest) -> AgentResult:
        history: list[dict] = []

        for step in range(1, request.max_steps + 1):
            try:
                action = agent.decide(request, history)
            except Exception as exc:
                return AgentResult(
                    completed=False,
                    final_message="Agent execution failed.",
                    steps_used=step,
                    error=f"Agent decision error: {exc}",
                    metadata={"history": history},
                )

            if not isinstance(action, AgentAction):
                return AgentResult(
                    completed=False,
                    final_message="Agent returned an invalid action.",
                    steps_used=step,
                    error="Agent decision must return an AgentAction.",
                    metadata={"history": history},
                )

            if action.action_type == "final":
                history.append(
                    {
                        "step": step,
                        "action_type": "final",
                        "final_message": action.final_message,
                    }
                )

                return AgentResult(
                    completed=True,
                    final_message=action.final_message or "",
                    steps_used=step,
                    metadata={"history": history},
                )

            if action.action_type != "tool":
                history.append(
                    {
                        "step": step,
                        "action_type": action.action_type,
                        "error": "Invalid action type.",
                    }
                )

                return AgentResult(
                    completed=False,
                    final_message="Agent returned an invalid action.",
                    steps_used=step,
                    error=f"Unsupported action type: {action.action_type}",
                    metadata={"history": history},
                )

            if not action.tool_name:
                history.append(
                    {
                        "step": step,
                        "action_type": "tool",
                        "error": "Tool name was not provided.",
                    }
                )

                return AgentResult(
                    completed=False,
                    final_message="Agent attempted an invalid tool call.",
                    steps_used=step,
                    error="Tool action requires a tool_name.",
                    metadata={"history": history},
                )

            if action.tool_name not in request.available_tools:
                history.append(
                    {
                        "step": step,
                        "action_type": "tool",
                        "tool_name": action.tool_name,
                        "arguments": action.arguments,
                        "error": "Tool is not allowed for this task.",
                    }
                )

                return AgentResult(
                    completed=False,
                    final_message="Agent attempted to use an unavailable tool.",
                    steps_used=step,
                    error=f"Tool not allowed: {action.tool_name}",
                    metadata={"history": history},
                )

            tool_result = self.tool_registry.execute(
                action.tool_name,
                action.arguments,
            )

            history.append(
                {
                    "step": step,
                    "action_type": "tool",
                    "tool_name": action.tool_name,
                    "arguments": action.arguments,
                    "tool_success": tool_result.success,
                    "tool_output": tool_result.output,
                    "tool_error": tool_result.error,
                }
            )

        return AgentResult(
            completed=False,
            final_message="Agent reached the maximum step limit.",
            steps_used=request.max_steps,
            error="Maximum steps exceeded.",
            metadata={"history": history},
        )

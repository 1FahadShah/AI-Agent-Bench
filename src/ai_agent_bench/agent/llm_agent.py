import json

from ai_agent_bench.agent.action_parser import ActionParser
from ai_agent_bench.agent.interface import Agent, AgentAction, AgentRequest
from ai_agent_bench.llm.base import LLMProvider
from ai_agent_bench.llm.models import LLMMessage, LLMRequest


class LLMAgent(Agent):
    """Agent that uses an LLM to select benchmark actions."""

    def __init__(
        self,
        provider: LLMProvider,
        model: str,
        temperature: float = 0.2,
        action_parser: ActionParser | None = None,
    ) -> None:
        self.provider = provider
        self.model = model
        self.temperature = temperature
        self.action_parser = action_parser or ActionParser()

    def decide(
        self,
        request: AgentRequest,
        history: list[dict],
    ) -> AgentAction:
        """Generate and parse the next action for a benchmark task."""

        messages = (
            LLMMessage(
                role="system",
                content=self._build_system_prompt(request),
            ),
            LLMMessage(
                role="user",
                content=self._build_user_message(request, history),
            ),
        )

        llm_request = LLMRequest(
            messages=messages,
            model=self.model,
            temperature=self.temperature,
        )

        response = self.provider.generate(llm_request)

        return self.action_parser.parse(response.content)

    def _build_system_prompt(self, request: AgentRequest) -> str:
        """Describe the task environment and required response format."""

        if request.available_tools:
            tools_description = "\n".join(f"- {tool}" for tool in request.available_tools)
        else:
            tools_description = "No tools are available."

        return f"""
You are an AI agent solving software engineering benchmark tasks.

Your task:
- Task ID: {request.task_id}
- Description: {request.task_description}

Workspace:
- You are working inside a dedicated benchmark task workspace.
- Use the provided tools to inspect and modify files.
- Do not assume files exist without inspecting them.
- Verify changes using available tools when appropriate.
- Only use the provided tools for workspace operations.

Available tools:
{tools_description}

You must return exactly one JSON object per response.

For a tool action, use:
{{
  "action_type": "tool",
  "tool_name": "read_file",
  "arguments": {{
    "file_path": "example.py"
  }}
}}

For a final action, use:
{{
  "action_type": "final",
  "final_message": "Describe what you completed."
}}

Rules:
- Use only the available tool names.
- Tool arguments must be a JSON object.
- Do not include Markdown code fences.
- Do not include explanations outside the JSON object.
- Return a final action only when you are ready to stop.
""".strip()

    def _build_user_message(
        self,
        request: AgentRequest,
        history: list[dict],
    ) -> str:
        """Build the current task context and execution history."""

        return json.dumps(
            {
                "task_id": request.task_id,
                "task_description": request.task_description,
                "execution_history": history,
                "instruction": ("Review the execution history and choose your next action."),
            },
            indent=2,
            ensure_ascii=False,
        )

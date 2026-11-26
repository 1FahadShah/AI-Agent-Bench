
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
        """Describe the task environment and exact tool contracts."""

        available_tools = set(request.available_tools)

        tool_contracts = {
            "list_files": """
Tool: list_files

Purpose:
List files and directories inside the benchmark workspace.

Arguments:
{
    "directory": "."
}

Rules:
- Use "directory", NOT "path".
- The directory argument is optional.
- The default directory is ".".
""",
            "read_file": """
Tool: read_file

Purpose:
Read a text file inside the benchmark workspace.

Arguments:
{
    "file_path": "starter/app/session.py"
}

Rules:
- file_path is required.
- Use a workspace-relative path.
""",
            "write_file": """
Tool: write_file

Purpose:
Create or replace a text file inside the benchmark workspace.

Arguments:
{
    "file_path": "starter/app/session.py",
    "content": "complete file contents"
}

Rules:
- Both file_path and content are required.
- Provide the complete intended file contents.
- Do not use this tool to modify files outside the workspace.
""",
            "run_command": """
Tool: run_command

Purpose:
Execute an allowlisted command inside the benchmark workspace.

Arguments:
{
    "command": ["python", "-m", "pytest", "visible_tests"],
    "working_directory": "."
}

Rules:
- command is REQUIRED.
- command MUST be a JSON array of strings.
- NEVER provide command as a single string.
- The first array element is the executable.
- Each subsequent element is a separate argument.
- working_directory is optional and defaults to ".".
- Only use commands supported by the execution environment.
- Do not use shell operators, pipes, command chaining, or shell syntax.
- Do not assume a command is allowed without checking its result.
""",
        }

        if request.available_tools:
            descriptions = [
                tool_contracts[tool_name]
                for tool_name in request.available_tools
                if tool_name in tool_contracts
            ]

            tools_description = (
                "\n".join(descriptions)
                if descriptions
                else "No documented tools are available."
            )
        else:
            tools_description = "No tools are available."

        return f"""
You are an AI agent solving software engineering benchmark tasks.

TASK:
- Task ID: {request.task_id}
- Description: {request.task_description}

WORKSPACE:
- You are operating inside a dedicated benchmark task workspace.
- Inspect the repository before making changes.
- Do not assume files exist without inspecting them.
- Understand relevant modules and their dependencies.
- Identify root causes rather than applying superficial fixes.
- Preserve existing public interfaces unless the task explicitly requires changes.
- Make focused changes and avoid unrelated modifications.
- Verify your implementation using available tests.
- Only use the provided tools for workspace operations.

AVAILABLE TOOL CONTRACTS:

{tools_description}

RESPONSE FORMAT:

Return exactly one valid JSON object per response.

For a tool action:

{{
    "action_type": "tool",
    "tool_name": "read_file",
    "arguments": {{
        "file_path": "starter/app/session.py"
    }}
}}

For a final action:

{{
    "action_type": "final",
    "final_message": "Describe the changes and verification results."
}}

RULES:

1. Use only tool names listed in the available tool contracts.
2. Follow tool argument names and types exactly.
3. Never invent tool arguments.
4. Never pass a shell command string to run_command.
5. Never use Markdown code fences around your JSON response.
6. Do not include explanations outside the JSON object.
7. Inspect relevant files before editing them.
8. Read the results of tool calls before deciding your next action.
9. If a tool call fails, understand the error and correct your next action.
10. Do not claim tests passed unless you actually ran them.
11. Do not stop before making a reasonable attempt to complete the task.
12. Return a final action only when you have finished your implementation and verification attempt.
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
                "instruction": (
                    "Review the task and execution history. "
                    "Choose the next appropriate action. "
                    "Follow the exact available tool contracts."
                ),
            },
            indent=2,
            ensure_ascii=False,
        )

from dataclasses import dataclass
from pathlib import Path

from ai_agent_bench.execution.runner import CommandRunner, ExecutionResult


@dataclass
class ToolResult:
    tool_name: str
    success: bool
    output: str
    error: str | None = None


class ToolRegistry:
    """Provides controlled tools for an agent operating in a task workspace."""

    def __init__(
        self,
        workspace: Path,
        timeout_seconds: int = 30,
        max_output_chars: int = 20_000,
    ) -> None:
        self.workspace = workspace.resolve()

        if not self.workspace.exists() or not self.workspace.is_dir():
            raise ValueError("Workspace must be an existing directory")

        self.command_runner = CommandRunner(
            workspace=self.workspace,
            timeout_seconds=timeout_seconds,
            max_output_chars=max_output_chars,
        )

        self.tools = {
            "list_files": self.list_files,
            "read_file": self.read_file,
            "write_file": self.write_file,
            "run_command": self.run_command,
        }

    def _resolve_path(self, relative_path: str) -> Path:
        """Resolve a path and ensure it remains inside the workspace."""

        if not relative_path:
            raise ValueError("Path cannot be empty")

        resolved_path = (self.workspace / relative_path).resolve()

        if not resolved_path.is_relative_to(self.workspace):
            raise ValueError("Path must remain inside the workspace")

        return resolved_path

    def list_files(
        self,
        directory: str = ".",
    ) -> ToolResult:
        """List files and directories inside the workspace."""

        try:
            target_directory = self._resolve_path(directory)

            if not target_directory.exists():
                raise FileNotFoundError(
                    f"Directory does not exist: {directory}"
                )

            if not target_directory.is_dir():
                raise ValueError(
                    f"Path is not a directory: {directory}"
                )

            entries = sorted(
                target_directory.iterdir(),
                key=lambda path: (not path.is_dir(), path.name.lower()),
            )

            output_lines = []

            for entry in entries:
                entry_type = "DIR" if entry.is_dir() else "FILE"

                relative_entry = entry.relative_to(self.workspace)

                output_lines.append(
                    f"{entry_type}: {relative_entry}"
                )

            output = (
                "\n".join(output_lines)
                if output_lines
                else "Directory is empty."
            )

            return ToolResult(
                tool_name="list_files",
                success=True,
                output=output,
            )

        except Exception as exc:
            return ToolResult(
                tool_name="list_files",
                success=False,
                output="",
                error=str(exc),
            )

    def read_file(
        self,
        file_path: str,
    ) -> ToolResult:
        """Read a text file inside the workspace."""

        try:
            target_file = self._resolve_path(file_path)

            if not target_file.exists():
                raise FileNotFoundError(
                    f"File does not exist: {file_path}"
                )

            if not target_file.is_file():
                raise ValueError(
                    f"Path is not a file: {file_path}"
                )

            content = target_file.read_text(
                encoding="utf-8",
            )

            return ToolResult(
                tool_name="read_file",
                success=True,
                output=content,
            )

        except Exception as exc:
            return ToolResult(
                tool_name="read_file",
                success=False,
                output="",
                error=str(exc),
            )

    def write_file(
        self,
        file_path: str,
        content: str,
    ) -> ToolResult:
        """Write a text file inside the workspace."""

        try:
            target_file = self._resolve_path(file_path)

            target_file.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            target_file.write_text(
                content,
                encoding="utf-8",
            )

            return ToolResult(
                tool_name="write_file",
                success=True,
                output=f"File written successfully: {file_path}",
            )

        except Exception as exc:
            return ToolResult(
                tool_name="write_file",
                success=False,
                output="",
                error=str(exc),
            )

    def run_command(
        self,
        command: list[str],
        working_directory: str = ".",
    ) -> ToolResult:
        """Execute an allowlisted command inside the workspace."""

        try:
            target_directory = self._resolve_path(
                working_directory,
            )

            if not target_directory.exists():
                raise FileNotFoundError(
                    f"Working directory does not exist: "
                    f"{working_directory}"
                )

            if not target_directory.is_dir():
                raise ValueError(
                    "Working directory must be a directory"
                )

            result: ExecutionResult = self.command_runner.run(
                command=command,
                working_directory=target_directory,
            )

            output_parts = [
                f"Exit code: {result.exit_code}",
                f"Timed out: {result.timed_out}",
                f"Duration: {result.duration_seconds:.2f} seconds",
            ]

            if result.stdout:
                output_parts.append(
                    f"\nSTDOUT:\n{result.stdout}"
                )

            if result.stderr:
                output_parts.append(
                    f"\nSTDERR:\n{result.stderr}"
                )

            return ToolResult(
                tool_name="run_command",
                success=(
                    result.exit_code == 0
                    and not result.timed_out
                ),
                output="\n".join(output_parts),
                error=(
                    "Command failed or timed out."
                    if result.exit_code != 0 or result.timed_out
                    else None
                ),
            )

        except Exception as exc:
            return ToolResult(
                tool_name="run_command",
                success=False,
                output="",
                error=str(exc),
            )

    def execute(
        self,
        tool_name: str,
        arguments: dict,
    ) -> ToolResult:
        """Execute a tool by name."""

        if tool_name not in self.tools:
            return ToolResult(
                tool_name=tool_name,
                success=False,
                output="",
                error=f"Unknown tool: {tool_name}",
            )

        try:
            tool_function = self.tools[tool_name]

            return tool_function(**arguments)

        except TypeError as exc:
            return ToolResult(
                tool_name=tool_name,
                success=False,
                output="",
                error=f"Invalid tool arguments: {exc}",
            )

    def get_available_tools(self) -> list[str]:
        """Return names of tools available to the agent."""

        return list(self.tools.keys())
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path

from ai_agent_bench.agent.tools import ToolRegistry


@dataclass
class AgentRequest:
    """Input provided to an agent for one benchmark task."""

    task_id: str
    task_description: str
    workspace: Path
    available_tools: list[str]
    max_steps: int = 20


@dataclass
class AgentResult:
    """Standardized result returned by an agent."""

    completed: bool
    final_message: str
    steps_used: int
    error: str | None = None
    metadata: dict = field(default_factory=dict)


class Agent(ABC):
    """Base interface that all benchmark agents must implement."""

    @abstractmethod
    def run(
        self,
        request: AgentRequest,
        tools: ToolRegistry,
    ) -> AgentResult:
        """Execute a benchmark task using the provided tools."""
        raise NotImplementedError
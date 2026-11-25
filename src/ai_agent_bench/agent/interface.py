from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class AgentRequest:
    """Input provided to an agent for one benchmark task."""

    task_id: str
    task_description: str
    workspace: Path
    available_tools: list[str]
    max_steps: int = 20


@dataclass
class AgentAction:
    """One action selected by an agent."""

    action_type: str
    tool_name: str | None = None
    arguments: dict = field(default_factory=dict)
    final_message: str | None = None


@dataclass
class AgentResult:
    """Standardized result returned after runtime execution."""

    completed: bool
    final_message: str
    steps_used: int
    error: str | None = None
    metadata: dict = field(default_factory=dict)


class Agent(ABC):
    """Base interface for agents that make one decision per step."""

    @abstractmethod
    def decide(
        self,
        request: AgentRequest,
        history: list[dict],
    ) -> AgentAction:
        """Choose the next action based on the task and history."""
        raise NotImplementedError

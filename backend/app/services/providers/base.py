from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional
from uuid import UUID
from datetime import datetime


@dataclass
class AIProviderRequest:
    """Input to an AI provider call."""

    scenario: str  # learning_diagnosis, lesson_plan, rubric_generation, resource_recommendation, teaching_reflection
    input_data: dict[str, Any]  # Structured input per scenario
    user_id: str | UUID
    school_id: str | UUID
    project_id: Optional[str | UUID] = None
    agent_config: dict[str, Any] = field(default_factory=dict)


@dataclass
class AIProviderResult:
    """Output from an AI provider call."""

    success: bool
    content: Any  # The actual output (dict, str, etc.)
    provider: str  # gjt_api, gjt_link, manual_import, mock
    scenario: str
    metadata: dict[str, Any] = field(default_factory=dict)
    diagnostic_metadata: dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    requires_review: bool = True  # All AI output must be reviewed
    finished_at: Optional[datetime] = None


class BaseAIProvider(ABC):
    """Abstract base for all AI providers."""

    provider_name: str = "base"

    @abstractmethod
    async def run(self, request: AIProviderRequest) -> AIProviderResult:
        """Execute the AI call and return a result."""
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the provider is available."""
        ...

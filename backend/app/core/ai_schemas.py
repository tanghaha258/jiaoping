"""
Pydantic schemas for AI agent and AI call requests/responses.

All schemas follow the unified API response format:
    {"code": 0, "message": "success", "data": {}, "trace_id": "..."}
"""

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field


# ─── Shared Types ─────────────────────────────────────────────────────────────

class AgentConfig(BaseModel):
    """Configuration for an AI agent."""
    provider: str = "mock"  # gjt_api, gjt_link, manual_import, mock
    model: Optional[str] = None
    endpoint: Optional[str] = None
    auth_type: Optional[str] = None
    timeout_seconds: int = 30
    max_retries: int = 1
    extra: dict[str, Any] = Field(default_factory=dict)


LESSON_PLAN_THINKING_STEPS: list[dict[str, Any]] = [
    {
        "code": "understanding",
        "title": "Understand teaching request",
        "description": "Parse theme, grade, class, subject, lesson count and teacher constraints.",
        "percent": 15,
    },
    {
        "code": "retrieving_context",
        "title": "Retrieve school context",
        "description": "Load subjects, classes, agent configuration and reusable teaching context.",
        "percent": 35,
    },
    {
        "code": "drafting",
        "title": "Draft teaching plan",
        "description": "Ask the configured provider to create the first structured draft.",
        "percent": 65,
    },
    {
        "code": "normalizing",
        "title": "Normalize business objects",
        "description": "Convert provider output into project, tasks, rubric, resources and notes.",
        "percent": 90,
    },
    {
        "code": "awaiting_review",
        "title": "Await teacher review",
        "description": "Persist the draft and wait for teacher edits before adoption.",
        "percent": 100,
    },
]


AI_AGENT_CONTRACTS: list[dict[str, Any]] = [
    {
        "scenario": "lesson_plan",
        "name": "AI lesson-plan workflow",
        "version": "2026-05-v1",
        "provider_modes": ["mock", "gjt_api"],
        "input_contract": {
            "type": "object",
            "required": [
                "theme",
                "grade",
                "subject_ids",
                "class_ids",
                "lesson_count",
            ],
            "properties": {
                "theme": {"type": "string"},
                "grade": {"type": "string"},
                "subject_ids": {"type": "array", "items": {"type": "string"}},
                "class_ids": {"type": "array", "items": {"type": "string"}},
                "lesson_count": {"type": "integer", "minimum": 1, "maximum": 20},
                "core_competencies": {"type": "array", "items": {"type": "string"}},
                "interdisciplinary_requirements": {"type": "string"},
                "assessment_preferences": {"type": "string"},
                "resource_preferences": {"type": "string"},
                "extra_requirements": {"type": "string"},
            },
        },
        "output_contract": {
            "type": "object",
            "required": ["project", "tasks", "rubric", "resources", "teacher_notes"],
            "properties": {
                "project": {
                    "type": "object",
                    "required": [
                        "name",
                        "grade",
                        "subject_ids",
                        "class_ids",
                        "driving_question",
                        "lesson_count",
                        "objectives",
                    ],
                },
                "tasks": {"type": "array"},
                "rubric": {"type": "object"},
                "resources": {"type": "array"},
                "teacher_notes": {"type": "array"},
            },
        },
        "thinking_steps": LESSON_PLAN_THINKING_STEPS,
        "adoption_rule": "Teacher adoption creates an active project, draft tasks, a personal rubric and suggested resources.",
    },
    {
        "scenario": "learning_diagnosis",
        "name": "Learning diagnosis",
        "version": "2026-05-v1",
        "provider_modes": ["mock", "gjt_api"],
        "input_contract": {
            "type": "object",
            "required": ["project_id", "class_id", "evidence"],
        },
        "output_contract": {
            "type": "object",
            "required": ["class_profile", "tiered_suggestions"],
        },
        "thinking_steps": [
            {"code": "collecting_evidence", "title": "Collect evidence", "percent": 25},
            {"code": "analyzing_patterns", "title": "Analyze learning patterns", "percent": 70},
            {"code": "awaiting_review", "title": "Await teacher review", "percent": 100},
        ],
        "adoption_rule": "Reserved for diagnosis records; no direct student-facing publication.",
    },
    {
        "scenario": "rubric_generation",
        "name": "Rubric generation",
        "version": "2026-05-v1",
        "provider_modes": ["mock", "gjt_api"],
        "input_contract": {
            "type": "object",
            "required": ["project_id", "assessment_goal"],
        },
        "output_contract": {
            "type": "object",
            "required": ["name", "items"],
        },
        "thinking_steps": [
            {"code": "understanding_goal", "title": "Understand goal", "percent": 30},
            {"code": "building_dimensions", "title": "Build dimensions", "percent": 80},
            {"code": "awaiting_review", "title": "Await teacher review", "percent": 100},
        ],
        "adoption_rule": "Teacher adoption creates or updates a rubric only.",
    },
    {
        "scenario": "resource_recommendation",
        "name": "Resource recommendation",
        "version": "2026-05-v1",
        "provider_modes": ["mock", "gjt_api"],
        "input_contract": {
            "type": "object",
            "required": ["project_id", "resource_preferences"],
        },
        "output_contract": {
            "type": "object",
            "required": ["resources"],
        },
        "thinking_steps": [
            {"code": "matching_need", "title": "Match resource need", "percent": 35},
            {"code": "ranking_resources", "title": "Rank resources", "percent": 80},
            {"code": "awaiting_review", "title": "Await teacher review", "percent": 100},
        ],
        "adoption_rule": "Teacher adoption adds resource metadata or a recommendation list.",
    },
    {
        "scenario": "teaching_reflection",
        "name": "Teaching reflection",
        "version": "2026-05-v1",
        "provider_modes": ["mock", "gjt_api"],
        "input_contract": {
            "type": "object",
            "required": ["project_id", "implementation_notes"],
        },
        "output_contract": {
            "type": "object",
            "required": ["strengths", "improvements"],
        },
        "thinking_steps": [
            {"code": "summarizing_evidence", "title": "Summarize evidence", "percent": 40},
            {"code": "suggesting_improvements", "title": "Suggest improvements", "percent": 85},
            {"code": "awaiting_review", "title": "Await teacher review", "percent": 100},
        ],
        "adoption_rule": "Teacher adoption stores reflection suggestions for later reuse.",
    },
]


# ─── AI Agent Schemas ─────────────────────────────────────────────────────────

class AIAgentCreate(BaseModel):
    """Request body for creating an AI agent configuration."""
    name: str = Field(..., min_length=1, max_length=128, description="智能体名称")
    provider: str = Field(..., pattern=r"^(gjt_api|gjt_link|manual_import|mock)$", description="Provider类型")
    scenario: str = Field(..., pattern=r"^(learning_diagnosis|lesson_plan|rubric_generation|resource_recommendation|teaching_reflection)$", description="应用场景")
    config: AgentConfig = Field(default_factory=AgentConfig, description="智能体配置")
    input_schema: Optional[dict[str, Any]] = Field(None, description="输入字段定义")
    output_schema: Optional[dict[str, Any]] = Field(None, description="输出字段定义")
    enabled: bool = Field(True, description="是否启用")


class AIAgentUpdate(BaseModel):
    """Request body for updating an AI agent configuration."""
    name: Optional[str] = Field(None, min_length=1, max_length=128)
    provider: Optional[str] = Field(None, pattern=r"^(gjt_api|gjt_link|manual_import|mock)$")
    scenario: Optional[str] = Field(None, pattern=r"^(learning_diagnosis|lesson_plan|rubric_generation|resource_recommendation|teaching_reflection)$")
    config: Optional[AgentConfig] = None
    input_schema: Optional[dict[str, Any]] = None
    output_schema: Optional[dict[str, Any]] = None
    enabled: Optional[bool] = None


class AIAgentResponse(BaseModel):
    """Response body for AI agent detail/list."""
    id: UUID
    name: str
    provider: str
    scenario: str
    config: dict[str, Any]
    input_schema: Optional[dict[str, Any]] = None
    output_schema: Optional[dict[str, Any]] = None
    enabled: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ─── AI Call Schemas ──────────────────────────────────────────────────────────

class AICallRequest(BaseModel):
    """Request body for initiating an AI call."""
    agent_id: UUID = Field(..., description="智能体ID")
    scenario: str = Field(..., description="调用场景")
    project_id: Optional[UUID] = Field(None, description="关联项目ID")
    input: dict[str, Any] = Field(..., description="结构化输入数据")


class AICallResponse(BaseModel):
    """Response body for an AI call record."""
    id: UUID
    agent_id: UUID
    agent_name: Optional[str] = None
    scenario: str
    provider: str
    status: str
    input_summary: Optional[str] = None
    output_summary: Optional[str] = None
    review_status: str
    error_message: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AIImportRequest(BaseModel):
    """Request body for manually importing AI output."""
    output_content: dict[str, Any] = Field(..., description="AI输出内容")
    attachments: Optional[list[str]] = Field(None, description="附件URL列表")
    adopted: bool = Field(False, description="是否立即采纳")
    gjt_agent_name: Optional[str] = Field(None, description="桂教通智能体名称")
    gjt_usage_time: Optional[datetime] = Field(None, description="桂教通使用时间")
    notes: Optional[str] = Field(None, description="备注说明")


class AIReviewRequest(BaseModel):
    """Request body for reviewing AI output."""
    review_status: str = Field(..., pattern=r"^(approved|rejected)$", description="审核状态")
    comments: Optional[str] = Field(None, description="审核意见")
    modifications: Optional[dict[str, Any]] = Field(None, description="教师修改内容")


class AIAdoptRequest(BaseModel):
    """Request body for adopting AI output into a business object."""
    target_type: str = Field(..., description="目标业务类型: project_lesson, task, rubric, evaluation, resource")
    target_id: Optional[str] = Field(None, description="目标业务对象ID，若为None则创建新对象")


class LessonPlanDraftRequest(BaseModel):
    """Request body for the one-click AI lesson-plan workflow."""

    agent_id: Optional[str] = Field(None, description="AI agent id. If empty, use the first enabled lesson_plan agent.")
    theme: str = Field(..., min_length=1, max_length=200)
    grade: str = Field(..., min_length=1, max_length=50)
    subject_ids: list[str] = Field(..., min_length=1)
    class_ids: list[str] = Field(..., min_length=1)
    lesson_count: int = Field(..., ge=1, le=20)
    core_competencies: list[str] = Field(default_factory=list)
    interdisciplinary_requirements: str = Field(default="", max_length=1000)
    assessment_preferences: str = Field(default="", max_length=1000)
    resource_preferences: str = Field(default="", max_length=1000)
    extra_requirements: str = Field(default="", max_length=1500)


class LessonPlanAdoptRequest(BaseModel):
    """Teacher-reviewed draft payload for adoption."""

    draft: Optional[dict[str, Any]] = Field(None, description="Teacher-edited normalized draft.")


# ─── Utility / Query Schemas ──────────────────────────────────────────────────

class AICallListFilter(BaseModel):
    """Filter parameters for listing AI calls."""
    agent_id: Optional[UUID] = None
    scenario: Optional[str] = None
    provider: Optional[str] = None
    status: Optional[str] = None
    review_status: Optional[str] = None
    project_id: Optional[UUID] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None


class AIAgentListFilter(BaseModel):
    """Filter parameters for listing AI agents."""
    scenario: Optional[str] = None
    provider: Optional[str] = None
    enabled: Optional[bool] = None

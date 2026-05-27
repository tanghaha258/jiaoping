"""
AI Service — business logic layer for AI operations.

Layered architecture:
    API Router (ai.py) -> AI Service (this file) -> AI Gateway -> Provider

Responsibilities:
    - Agent CRUD with validation
    - AI call initiation with permission checks
    - Manual import handling
    - AI output review and adoption
    - Audit logging for all write operations

Uses SQLAlchemy ORM models from app.models and integrates with
Agent A's dependency injection (get_db, get_current_user, require_roles).
"""

import json
import logging
import uuid as _uuid
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.ai_schemas import AI_AGENT_CONTRACTS, AI_PROVIDER_MODES
from app.core.exceptions import (
    AIProviderUnavailableException,
    InvalidStateTransitionException,
    PermissionDeniedException,
    ResourceNotFoundException,
)
from app.models.ai_agent import AIAgent
from app.models.ai_agent_call import AIAgentCall
from app.models.ai_call_step import AICallStep
from app.models.audit_log import AuditLog
from app.models.user import User
from app.services.ai_gateway import AIGateway
from app.services.providers.base import AIProviderRequest

logger = logging.getLogger(__name__)

# ─── Constants ────────────────────────────────────────────────────────────────

VALID_SCENARIOS = {
    "learning_diagnosis",
    "lesson_plan",
    "rubric_generation",
    "resource_recommendation",
    "teaching_reflection",
}

VALID_PROVIDERS = set(AI_PROVIDER_MODES)

ADOPTABLE_TARGET_TYPES = {"project_lesson", "task", "rubric", "evaluation", "resource"}


# ─── Model Serialization ──────────────────────────────────────────────────────

def _agent_to_dict(agent: AIAgent) -> dict:
    """Serialize an AIAgent ORM object to a dict."""
    return {
        "id": agent.id,
        "name": agent.name,
        "provider": agent.provider,
        "scenario": agent.scenario,
        "config": agent.config or {},
        "input_schema": agent.input_schema or {},
        "output_schema": agent.output_schema or {},
        "enabled": agent.enabled,
        "created_at": agent.created_at.isoformat() if agent.created_at else None,
        "updated_at": agent.updated_at.isoformat() if agent.updated_at else None,
    }


def _call_to_dict(call: AIAgentCall) -> dict:
    """Serialize an AIAgentCall ORM object to a dict."""
    agent_name = None
    if hasattr(call, 'agent') and call.agent:
        agent_name = call.agent.name

    return {
        "id": call.id,
        "agent_id": call.agent_id,
        "agent_name": agent_name,
        "user_id": call.user_id,
        "school_id": call.school_id,
        "project_id": call.project_id,
        "scenario": call.scenario,
        "provider": call.provider,
        "status": call.status,
        "input_summary": call.input_summary,
        "output_summary": call.output_summary,
        "request_payload": call.request_payload or {},
        "response_payload": call.response_payload or {},
        "review_status": call.review_status,
        "error_message": call.error_message,
        "created_at": call.created_at.isoformat() if call.created_at else None,
        "updated_at": call.updated_at.isoformat() if call.updated_at else None,
    }


# ─── AI Service ───────────────────────────────────────────────────────────────

class AIService:
    """
    Business logic layer for AI operations.

    Handles permission checks, state transitions, audit logging,
    and coordinates with the AI Gateway for actual provider calls.
    """

    def __init__(self, ai_gateway: AIGateway):
        self.gateway = ai_gateway

    async def get_contracts(self) -> dict:
        """Return local AI agent contracts used by provider adapters."""
        return {"items": json.loads(json.dumps(AI_AGENT_CONTRACTS))}

    # ─── Agent Management ──────────────────────────────────────────────────

    async def list_agents(
        self,
        db: AsyncSession,
        scenario: Optional[str] = None,
        provider: Optional[str] = None,
        enabled: Optional[bool] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        """List AI agents with optional filters and pagination."""
        query = select(AIAgent).where(AIAgent.deleted_at.is_(None))

        if scenario:
            query = query.where(AIAgent.scenario == scenario)
        if provider:
            query = query.where(AIAgent.provider == provider)
        if enabled is not None:
            query = query.where(AIAgent.enabled == enabled)

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        # Fetch page
        offset = (page - 1) * page_size
        query = query.order_by(AIAgent.created_at.desc()).offset(offset).limit(page_size)
        result = await db.execute(query)
        agents = result.scalars().all()

        return {
            "items": [_agent_to_dict(a) for a in agents],
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    async def create_agent(self, db: AsyncSession, data, user: User) -> dict:
        """Create a new AI agent configuration."""
        agent = AIAgent(
            name=data.name,
            provider=data.provider,
            scenario=data.scenario,
            config=data.config.model_dump() if hasattr(data, 'model_dump') else (data.config or {}),
            input_schema=data.input_schema or {},
            output_schema=data.output_schema or {},
            enabled=data.enabled if hasattr(data, 'enabled') else True,
        )

        db.add(agent)
        await db.flush()
        await db.refresh(agent)

        # Audit log
        await self._audit(db, user, "ai_agent.create", "ai_agent", agent.id, {
            "name": agent.name,
            "scenario": agent.scenario,
            "provider": agent.provider,
        })

        return _agent_to_dict(agent)

    async def get_agent(self, db: AsyncSession, agent_id: UUID) -> dict:
        """Get a single AI agent by ID."""
        result = await db.execute(
            select(AIAgent).where(
                AIAgent.id == str(agent_id),
                AIAgent.deleted_at.is_(None),
            )
        )
        agent = result.scalar_one_or_none()
        if agent is None:
            raise ResourceNotFoundException(f"AI智能体不存在: {agent_id}")
        return _agent_to_dict(agent)

    async def update_agent(
        self, db: AsyncSession, agent_id: UUID, data: dict, user: User
    ) -> dict:
        """Update an AI agent configuration (partial update)."""
        result = await db.execute(
            select(AIAgent).where(
                AIAgent.id == str(agent_id),
                AIAgent.deleted_at.is_(None),
            )
        )
        agent = result.scalar_one_or_none()
        if agent is None:
            raise ResourceNotFoundException(f"AI智能体不存在: {agent_id}")

        updatable = {"name", "provider", "scenario", "config", "input_schema", "output_schema", "enabled"}
        for field in updatable:
            if field in data and data[field] is not None:
                setattr(agent, field, data[field])

        await db.flush()
        await db.refresh(agent)

        # Audit log
        await self._audit(db, user, "ai_agent.update", "ai_agent", agent.id, {
            "updated_fields": list(data.keys()),
        })

        return _agent_to_dict(agent)

    async def delete_agent(self, db: AsyncSession, agent_id: UUID, user: User) -> dict:
        """Soft-delete an AI agent configuration."""
        result = await db.execute(
            select(AIAgent).where(
                AIAgent.id == str(agent_id),
                AIAgent.deleted_at.is_(None),
            )
        )
        agent = result.scalar_one_or_none()
        if agent is None:
            raise ResourceNotFoundException(f"AI智能体不存在: {agent_id}")

        agent.enabled = False
        agent.deleted_at = datetime.now(timezone.utc)
        await db.flush()

        await self._audit(db, user, "ai_agent.delete", "ai_agent", agent.id, {
            "name": agent.name,
            "scenario": agent.scenario,
            "provider": agent.provider,
        })

        return {"id": agent.id, "deleted": True}

    # ─── AI Call Management ────────────────────────────────────────────────

    async def initiate_call(
        self,
        db: AsyncSession,
        agent_id: UUID,
        scenario: str,
        input_data: dict[str, Any],
        user: User,
        project_id: Optional[UUID] = None,
    ) -> dict:
        """
        Initiate an AI call.

        Flow:
            1. Look up agent configuration
            2. Validate scenario compatibility
            3. Build AIProviderRequest
            4. Execute via AI Gateway
            5. Create and return call record
        """
        # Get agent
        result = await db.execute(
            select(AIAgent).where(
                AIAgent.id == str(agent_id),
                AIAgent.deleted_at.is_(None),
            )
        )
        agent = result.scalar_one_or_none()
        if agent is None:
            raise ResourceNotFoundException(f"AI智能体不存在: {agent_id}")

        if not agent.enabled:
            raise AIProviderUnavailableException(f"AI智能体 '{agent.name}' 已被禁用")

        # Build the provider request
        provider_request = AIProviderRequest(
            scenario=scenario,
            input_data=input_data,
            user_id=UUID(user.id) if isinstance(user.id, str) else user.id,
            school_id=UUID(user.school_id) if isinstance(user.school_id, str) else user.school_id,
            project_id=project_id,
            agent_config=agent.config or {},
        )

        # Create call record (status=created)
        call = AIAgentCall(
            agent_id=str(agent_id),
            user_id=user.id,
            school_id=user.school_id,
            project_id=str(project_id) if project_id else None,
            scenario=scenario,
            provider=agent.provider or "mock",
            input_summary=self._summarize(input_data),
            request_payload=input_data,
            status="created",
            review_status="pending",
        )
        db.add(call)
        await db.flush()

        # Update status to running
        call.status = "running"
        await db.flush()

        # Execute via gateway
        try:
            provider_result = await self.gateway.execute(
                provider_request,
                {"id": agent.id, "name": agent.name, "provider": agent.provider, "config": agent.config or {}},
            )

            # Update call record with result
            call.status = "succeeded" if provider_result.success else "failed"
            call.response_payload = provider_result.content if provider_result.success else None
            call.output_summary = self._summarize(provider_result.content) if provider_result.success else None
            call.error_message = provider_result.error_message
        except Exception as e:
            logger.exception(f"AI provider execution failed")
            call.status = "failed"
            call.error_message = f"AI调用异常: {str(e)}"

        await db.flush()
        await db.refresh(call)

        # Audit log
        await self._audit(db, user, "ai_call.initiate", "ai_agent_call", call.id, {
            "agent_id": str(agent_id),
            "scenario": scenario,
            "status": call.status,
        })

        result_dict = _call_to_dict(call)
        # Attach metadata from provider result if available
        if 'provider_result' in locals() and provider_result.metadata:
            result_dict["metadata"] = provider_result.metadata
        return result_dict

    async def import_result(
        self,
        db: AsyncSession,
        call_id: UUID,
        output_content: dict[str, Any],
        user: User,
        adopted: bool = False,
        gjt_agent_name: Optional[str] = None,
        gjt_usage_time: Optional[datetime] = None,
        notes: Optional[str] = None,
        attachments: Optional[list[str]] = None,
    ) -> dict:
        """Manually import AI output into a call record (for gjt_link and manual_import providers)."""
        result = await db.execute(
            select(AIAgentCall).where(AIAgentCall.id == str(call_id))
        )
        call = result.scalar_one_or_none()
        if call is None:
            raise ResourceNotFoundException(f"AI调用记录不存在: {call_id}")

        # Validate state transition
        valid_current_states = {"created", "running", "failed"}
        if call.status not in valid_current_states:
            raise InvalidStateTransitionException(
                f"当前状态 '{call.status}' 不允许导入操作"
            )

        call.status = "imported"
        call.output_summary = self._summarize(output_content)
        call.response_payload = output_content

        if adopted:
            call.review_status = "approved"
            call.status = "adopted"

        await db.flush()
        await db.refresh(call)

        # Audit log
        await self._audit(db, user, "ai_call.import", "ai_agent_call", call.id, {
            "gjt_agent_name": gjt_agent_name,
            "adopted": adopted,
        })

        return _call_to_dict(call)

    async def review_output(
        self,
        db: AsyncSession,
        call_id: UUID,
        review_status: str,
        user: User,
        comments: Optional[str] = None,
        modifications: Optional[dict[str, Any]] = None,
    ) -> dict:
        """Review (approve or reject) AI output."""
        if review_status not in ("approved", "rejected"):
            raise InvalidStateTransitionException(f"无效的审核状态: {review_status}")

        result = await db.execute(
            select(AIAgentCall).where(AIAgentCall.id == str(call_id))
        )
        call = result.scalar_one_or_none()
        if call is None:
            raise ResourceNotFoundException(f"AI调用记录不存在: {call_id}")

        # Can only review calls that have content
        valid_statuses = {"succeeded", "imported", "reviewed"}
        if call.status not in valid_statuses:
            raise InvalidStateTransitionException(
                f"当前状态 '{call.status}' 不允许审核操作"
            )

        # If modifications were made, update the response payload
        if modifications:
            call.response_payload = modifications

        call.review_status = review_status
        call.status = "reviewed"

        await db.flush()
        await db.refresh(call)

        # Audit log
        await self._audit(db, user, "ai_call.review", "ai_agent_call", call.id, {
            "review_status": review_status,
            "has_comments": bool(comments),
            "has_modifications": bool(modifications),
        })

        return _call_to_dict(call)

    async def adopt_output(
        self,
        db: AsyncSession,
        call_id: UUID,
        target_type: str,
        target_id: Optional[str],
        user: User,
    ) -> dict:
        """Adopt AI output into a business object (project_lesson, task, rubric, etc.)."""
        if target_type not in ADOPTABLE_TARGET_TYPES:
            raise InvalidStateTransitionException(f"不支持的目标类型: {target_type}")

        result = await db.execute(
            select(AIAgentCall).where(AIAgentCall.id == str(call_id))
        )
        call = result.scalar_one_or_none()
        if call is None:
            raise ResourceNotFoundException(f"AI调用记录不存在: {call_id}")

        # Must be reviewed/approved before adoption
        if call.review_status != "approved":
            raise InvalidStateTransitionException(
                f"AI输出必须先通过审核才能采纳。当前审核状态: {call.review_status}"
            )

        call.status = "adopted"
        await db.flush()
        await db.refresh(call)

        # Audit log
        await self._audit(db, user, f"ai_call.adopt.{target_type}", target_type, target_id or str(call_id), {
            "call_id": str(call_id),
            "scenario": call.scenario,
            "target_type": target_type,
            "target_id": target_id,
        })

        return _call_to_dict(call)

    async def list_calls(
        self,
        db: AsyncSession,
        user: User,
        filters: Optional[dict] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        """List AI call records with pagination, filtering, and school isolation."""
        query = select(AIAgentCall)

        # School-level data isolation
        if user.school_id:
            query = query.where(AIAgentCall.school_id == user.school_id)

        if filters:
            for key in ("agent_id", "scenario", "provider", "status", "review_status", "project_id"):
                if filters.get(key):
                    query = query.where(getattr(AIAgentCall, key) == filters[key])

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        # Fetch page
        offset = (page - 1) * page_size
        query = query.order_by(AIAgentCall.created_at.desc()).offset(offset).limit(page_size)
        result = await db.execute(query)
        calls = result.scalars().all()

        return {
            "items": [_call_to_dict(c) for c in calls],
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    async def get_call(self, db: AsyncSession, call_id: UUID, user: User) -> dict:
        """Get a single AI call record with school isolation check."""
        result = await db.execute(
            select(AIAgentCall).where(AIAgentCall.id == str(call_id))
        )
        call = result.scalar_one_or_none()
        if call is None:
            raise ResourceNotFoundException(f"AI调用记录不存在: {call_id}")

        # School isolation check
        if user.school_id and call.school_id != user.school_id:
            raise PermissionDeniedException("无权查看其他学校的AI调用记录")

        return _call_to_dict(call)

    # ─── Internal Helpers ──────────────────────────────────────────────────

    async def get_call_progress(self, db: AsyncSession, call_id: UUID, user: User) -> dict:
        """Return observable thinking/progress steps for one AI call."""
        result = await db.execute(
            select(AIAgentCall).where(AIAgentCall.id == str(call_id))
        )
        call = result.scalar_one_or_none()
        if call is None:
            raise ResourceNotFoundException(f"AI call not found: {call_id}")
        if user.school_id and call.school_id != user.school_id:
            raise PermissionDeniedException("Cannot view another school's AI call")

        steps_result = await db.execute(
            select(AICallStep)
            .where(AICallStep.call_id == str(call_id), AICallStep.deleted_at.is_(None))
            .order_by(AICallStep.sort_order)
        )
        steps = steps_result.scalars().all()
        percent = max((step.percent for step in steps if step.status == "completed"), default=0)
        if call.status == "failed":
            percent = max(percent, max((step.percent for step in steps), default=0))

        return {
            "call_id": call.id,
            "scenario": call.scenario,
            "status": call.status,
            "percent": percent,
            "steps": [self._step_to_dict(step) for step in steps],
        }

    async def _audit(
        self,
        db: AsyncSession,
        user: User,
        action: str,
        target_type: str,
        target_id: str,
        detail: dict,
    ) -> None:
        """Create an audit log entry (best-effort, non-blocking)."""
        try:
            audit = AuditLog(
                user_id=user.id,
                action=action,
                target_type=target_type,
                target_id=target_id,
                detail=detail,
            )
            db.add(audit)
            await db.flush()
        except Exception as e:
            logger.error(f"Audit log write failed (non-blocking): {e}", exc_info=True)

    def _summarize(self, content: Any, max_length: int = 200) -> str:
        """Create a brief text summary of content for display."""
        if content is None:
            return "无内容"
        if isinstance(content, str):
            return content[:max_length] + ("..." if len(content) > max_length else "")
        if isinstance(content, dict):
            for key in ("class_profile", "theme", "name", "overall", "title"):
                if key in content:
                    val = content[key]
                    if isinstance(val, str):
                        return val[:max_length] + ("..." if len(val) > max_length else "")
            keys = list(content.keys())[:5]
            return f"包含字段: {', '.join(keys)}"
        if isinstance(content, list):
            return f"列表，共 {len(content)} 项"
        return str(content)[:max_length]

    def _step_to_dict(self, step: AICallStep) -> dict:
        """Serialize an AI progress step."""
        return {
            "id": step.id,
            "call_id": step.call_id,
            "code": step.code,
            "title": step.title,
            "description": step.description,
            "status": step.status,
            "percent": step.percent,
            "sort_order": step.sort_order,
            "started_at": step.started_at.isoformat() if step.started_at else None,
            "completed_at": step.completed_at.isoformat() if step.completed_at else None,
            "metadata": step.metadata_ or {},
        }

"""
AI API Routes — HTTP layer for AI operations.

Layered architecture:
    HTTP (this file) -> AI Service -> AI Gateway -> Provider

All routes return the unified API response format:
    {"code": 0, "message": "success", "data": {}, "trace_id": "..."}

Integrates with Agent A's dependency injection (get_db, get_current_user, require_roles)
and response helpers (success_response, error_response).
"""

import logging
from typing import Any, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db, require_roles
from app.core.exceptions import (
    AIProviderUnavailableException,
    InvalidStateTransitionException,
    PermissionDeniedException,
    ResourceNotFoundException,
)
from app.core.response import success_response, error_response
from app.models.user import User
from app.core.ai_schemas import (
    AIAgentCreate,
    AIAgentUpdate,
    AIAdoptRequest,
    AICallRequest,
    AIImportRequest,
    AIReviewRequest,
    LessonPlanAdoptRequest,
    LessonPlanDraftRequest,
)
from app.services.ai_gateway import AIGateway
from app.services.ai_service import AIService
from app.services.lesson_plan_workflow import LessonPlanWorkflowService

logger = logging.getLogger(__name__)

# ─── Router Setup ──────────────────────────────────────────────────────────────

router = APIRouter(prefix="/ai", tags=["AI 智能体"])

# ─── Gateway / Service singletons ──────────────────────────────────────────────

_gateway: Optional[AIGateway] = None
_service: Optional[AIService] = None
_lesson_plan_service: Optional[LessonPlanWorkflowService] = None


def get_gateway() -> AIGateway:
    global _gateway
    if _gateway is None:
        _gateway = AIGateway()
    return _gateway


def get_service() -> AIService:
    global _service
    if _service is None:
        _service = AIService(get_gateway())
    return _service


def get_lesson_plan_service() -> LessonPlanWorkflowService:
    global _lesson_plan_service
    if _lesson_plan_service is None:
        _lesson_plan_service = LessonPlanWorkflowService(get_gateway())
    return _lesson_plan_service


@router.get("/contracts")
async def list_ai_contracts(
    current_user: User = Depends(get_current_user),
):
    """Return local AI-agent contracts for frontend and provider adapters."""
    service = get_service()
    return success_response(await service.get_contracts())


@router.get("/workflows/lesson-plan/options")
async def get_lesson_plan_options(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("teacher")),
):
    """Return form options for the AI lesson-plan workflow."""
    service = get_lesson_plan_service()
    try:
        return success_response(await service.get_options(db, current_user))
    except Exception as e:
        logger.exception("Failed to load lesson-plan workflow options")
        return error_response(50000, f"加载AI备课选项失败: {str(e)}", 500)


@router.post("/workflows/lesson-plan/draft")
async def create_lesson_plan_draft(
    body: LessonPlanDraftRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("teacher")),
):
    """Generate a normalized AI lesson-plan draft."""
    service = get_lesson_plan_service()
    try:
        return success_response(
            await service.create_draft(db, body, current_user),
            message="AI教学方案草案已生成",
        )
    except (ResourceNotFoundException, AIProviderUnavailableException) as e:
        return error_response(e.code, e.message, e.status_code)
    except InvalidStateTransitionException as e:
        return error_response(e.code, e.message, e.status_code)


@router.post("/workflows/lesson-plan/{call_id}/adopt")
async def adopt_lesson_plan_draft(
    call_id: UUID,
    body: LessonPlanAdoptRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("teacher")),
):
    """Adopt a reviewed AI lesson-plan draft into real teaching objects."""
    service = get_lesson_plan_service()
    try:
        result = await service.adopt_draft(db, call_id, body.draft, current_user)
        return success_response(result, message="AI教学方案已落地为项目")
    except ResourceNotFoundException as e:
        return error_response(e.code, e.message, e.status_code)
    except InvalidStateTransitionException as e:
        return error_response(e.code, e.message, e.status_code)
    except PermissionDeniedException as e:
        return error_response(e.code, e.message, e.status_code)


# ─── Agent Routes ──────────────────────────────────────────────────────────────

@router.get("/agents")
async def list_agents(
    scenario: Optional[str] = Query(None, description="场景过滤"),
    provider: Optional[str] = Query(None, description="Provider过滤"),
    enabled: Optional[bool] = Query(None, description="启用状态过滤"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    获取AI智能体列表。

    支持按场景、Provider和启用状态进行过滤，返回分页结果。
    """
    service = get_service()
    try:
        result = await service.list_agents(
            db,
            scenario=scenario,
            provider=provider,
            enabled=enabled,
            page=page,
            page_size=page_size,
        )
        return success_response(result)
    except Exception as e:
        logger.exception("Failed to list agents")
        return error_response(50000, f"获取智能体列表失败: {str(e)}", 500)


@router.post("/agents")
async def create_agent(
    body: AIAgentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "school_admin", "super_admin")),
):
    """
    创建AI智能体配置（管理员操作）。

    配置新的AI智能体，指定Provider类型和应用场景。
    """
    service = get_service()
    try:
        agent = await service.create_agent(db, body, current_user)
        return success_response(agent, message="智能体创建成功")
    except Exception as e:
        logger.exception("Failed to create agent")
        return error_response(50000, f"创建智能体失败: {str(e)}", 500)


@router.get("/agents/{agent_id}")
async def get_agent(
    agent_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    获取AI智能体详情。
    """
    service = get_service()
    try:
        agent = await service.get_agent(db, agent_id)
        return success_response(agent)
    except ResourceNotFoundException as e:
        return error_response(e.code, e.message, e.status_code)


@router.patch("/agents/{agent_id}")
async def update_agent(
    agent_id: UUID,
    body: AIAgentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "school_admin", "super_admin")),
):
    """
    更新AI智能体配置（管理员操作）。

    支持部分更新，只更新传入的字段。
    """
    service = get_service()
    update_data = {k: v for k, v in body.model_dump().items() if v is not None}
    if not update_data:
        return error_response(40000, "没有提供需要更新的字段", 400)

    try:
        agent = await service.update_agent(db, agent_id, update_data, current_user)
        return success_response(agent, message="智能体更新成功")
    except ResourceNotFoundException as e:
        return error_response(e.code, e.message, e.status_code)


# ─── AI Call Routes ────────────────────────────────────────────────────────────

@router.delete("/agents/{agent_id}")
async def delete_agent(
    agent_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "school_admin", "super_admin")),
):
    """Soft-delete an AI agent configuration."""
    service = get_service()
    try:
        result = await service.delete_agent(db, agent_id, current_user)
        return success_response(result, message="AI智能体已删除")
    except ResourceNotFoundException as e:
        return error_response(e.code, e.message, e.status_code)


@router.post("/calls")
async def initiate_call(
    body: AICallRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    发起AI调用。

    提交结构化输入数据，AI网关根据智能体配置选择合适的Provider
    进行处理，返回处理结果或创建待处理任务。
    """
    service = get_service()
    try:
        call_record = await service.initiate_call(
            db,
            agent_id=body.agent_id,
            scenario=body.scenario,
            input_data=body.input,
            user=current_user,
            project_id=body.project_id,
        )
        return success_response(call_record, message="AI调用已发起")
    except ResourceNotFoundException as e:
        return error_response(e.code, e.message, e.status_code)
    except AIProviderUnavailableException as e:
        return error_response(e.code, e.message, e.status_code)


@router.get("/calls")
async def list_calls(
    agent_id: Optional[UUID] = Query(None, description="智能体过滤"),
    scenario: Optional[str] = Query(None, description="场景过滤"),
    provider: Optional[str] = Query(None, description="Provider过滤"),
    status: Optional[str] = Query(None, description="状态过滤"),
    review_status: Optional[str] = Query(None, description="审核状态过滤"),
    project_id: Optional[UUID] = Query(None, description="项目过滤"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    获取AI调用记录列表。

    支持多维度过滤和分页。数据按学校隔离，用户只能查看本校记录。
    """
    service = get_service()
    filters = {}
    if agent_id:
        filters["agent_id"] = str(agent_id)
    if scenario:
        filters["scenario"] = scenario
    if provider:
        filters["provider"] = provider
    if status:
        filters["status"] = status
    if review_status:
        filters["review_status"] = review_status
    if project_id:
        filters["project_id"] = str(project_id)

    try:
        result = await service.list_calls(
            db, current_user, filters=filters or None, page=page, page_size=page_size
        )
        return success_response(result)
    except Exception as e:
        logger.exception("Failed to list calls")
        return error_response(50000, f"获取调用记录失败: {str(e)}", 500)


@router.get("/calls/{call_id}")
async def get_call(
    call_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    获取AI调用详情。

    包含输入摘要、输出内容、审核状态等完整信息。
    """
    service = get_service()
    try:
        call_record = await service.get_call(db, call_id, current_user)
        return success_response(call_record)
    except ResourceNotFoundException as e:
        return error_response(e.code, e.message, e.status_code)
    except PermissionDeniedException as e:
        return error_response(e.code, e.message, e.status_code)


@router.get("/calls/{call_id}/progress")
async def get_call_progress(
    call_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return AI thinking/progress steps for one call."""
    service = get_service()
    try:
        progress = await service.get_call_progress(db, call_id, current_user)
        return success_response(progress)
    except ResourceNotFoundException as e:
        return error_response(e.code, e.message, e.status_code)
    except PermissionDeniedException as e:
        return error_response(e.code, e.message, e.status_code)


@router.post("/calls/{call_id}/import")
async def import_call_result(
    call_id: UUID,
    body: AIImportRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    人工回填AI调用结果。

    用于桂教通链接模式或人工导入模式：教师在桂教通平台完成操作后，
    将结果复制回平台。支持上传截图和附件。
    """
    service = get_service()
    try:
        call_record = await service.import_result(
            db,
            call_id=call_id,
            output_content=body.output_content,
            user=current_user,
            adopted=body.adopted,
            gjt_agent_name=body.gjt_agent_name,
            gjt_usage_time=body.gjt_usage_time,
            notes=body.notes,
            attachments=body.attachments,
        )
        return success_response(call_record, message="结果导入成功")
    except ResourceNotFoundException as e:
        return error_response(e.code, e.message, e.status_code)
    except InvalidStateTransitionException as e:
        return error_response(e.code, e.message, e.status_code)


@router.post("/calls/{call_id}/review")
async def review_call_output(
    call_id: UUID,
    body: AIReviewRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    审核AI输出。

    教师对AI生成的内容进行审核：批准(approved)或拒绝(rejected)。
    审核通过后，可以通过 /adopt 接口将内容应用到业务对象。
    教师也可以在审核时直接修改AI输出内容。
    """
    service = get_service()
    try:
        call_record = await service.review_output(
            db,
            call_id=call_id,
            review_status=body.review_status,
            user=current_user,
            comments=body.comments,
            modifications=body.modifications,
        )
        action = "通过" if body.review_status == "approved" else "驳回"
        return success_response(call_record, message=f"AI输出已{action}审核")
    except ResourceNotFoundException as e:
        return error_response(e.code, e.message, e.status_code)
    except InvalidStateTransitionException as e:
        return error_response(e.code, e.message, e.status_code)


@router.post("/calls/{call_id}/adopt")
async def adopt_call_output(
    call_id: UUID,
    body: AIAdoptRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    采纳AI输出到业务对象。

    将已审核通过的AI输出应用到指定的业务对象类型：
    - project_lesson: 项目课时
    - task: 任务
    - rubric: 评价量规
    - evaluation: 评价
    - resource: 资源

    如果target_id为None，系统将根据target_type创建新的业务对象。
    """
    service = get_service()
    try:
        call_record = await service.adopt_output(
            db,
            call_id=call_id,
            target_type=body.target_type,
            target_id=body.target_id,
            user=current_user,
        )
        return success_response(call_record, message="AI输出已采纳")
    except ResourceNotFoundException as e:
        return error_response(e.code, e.message, e.status_code)
    except InvalidStateTransitionException as e:
        return error_response(e.code, e.message, e.status_code)
    except PermissionDeniedException as e:
        return error_response(e.code, e.message, e.status_code)

"""Dashboard service: aggregate statistics for the admin/teacher dashboard."""

import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.ai_agent import AIAgent
from app.models.user import User
from app.models.school import School
from app.models.class_ import Class
from app.models.subject import Subject
from app.models.project import Project
from app.models.task import Task
from app.models.resource import Resource
from app.models.ai_agent_call import AIAgentCall

logger = logging.getLogger(__name__)


class DashboardService:
    """Service for dashboard aggregate statistics."""

    @staticmethod
    async def get_overview(
        db: AsyncSession,
        school_id: Optional[str] = None,
        owner_id: Optional[str] = None,
    ) -> dict:
        """Return aggregate counts for the dashboard overview.

        Args:
            db: Database session.
            school_id: If provided, scope all queries to this school.
            owner_id: If provided (teacher scope), scope project/task stats to this owner's projects.

        Returns:
            dict with counts for schools, teachers, students, projects, tasks, resources, ai_calls.
        """
        # --- Schools count (always global, not scoped) ---
        school_count_query = select(func.count()).select_from(School)
        school_count = (await db.execute(school_count_query)).scalar()

        # --- Teachers count ---
        teacher_count_query = select(func.count()).select_from(User).where(User.role == "teacher")
        if school_id:
            teacher_count_query = teacher_count_query.where(User.school_id == school_id)
        teacher_count = (await db.execute(teacher_count_query)).scalar()

        # --- Students count ---
        student_count_query = select(func.count()).select_from(User).where(User.role == "student")
        if school_id:
            student_count_query = student_count_query.where(User.school_id == school_id)
        student_count = (await db.execute(student_count_query)).scalar()

        # --- Projects count ---
        project_count_query = select(func.count()).select_from(Project)
        if school_id:
            project_count_query = project_count_query.where(Project.school_id == school_id)
        if owner_id:
            project_count_query = project_count_query.where(Project.owner_id == owner_id)
        project_count = (await db.execute(project_count_query)).scalar()

        # --- Tasks count ---
        task_count_query = select(func.count()).select_from(Task)
        if school_id or owner_id:
            task_count_query = task_count_query.join(Project, Task.project_id == Project.id)
        if school_id:
            task_count_query = task_count_query.where(Project.school_id == school_id)
        if owner_id:
            task_count_query = task_count_query.where(Project.owner_id == owner_id)
        task_count = (await db.execute(task_count_query)).scalar()

        # --- Resources count ---
        resource_count_query = select(func.count()).select_from(Resource)
        if school_id:
            resource_count_query = resource_count_query.where(Resource.school_id == school_id)
        resource_count = (await db.execute(resource_count_query)).scalar()

        # --- AI calls count ---
        ai_call_count_query = select(func.count()).select_from(AIAgentCall)
        if school_id:
            ai_call_count_query = ai_call_count_query.where(AIAgentCall.school_id == school_id)
        if owner_id:
            ai_call_count_query = ai_call_count_query.where(AIAgentCall.user_id == owner_id)
        ai_call_count = (await db.execute(ai_call_count_query)).scalar()

        return {
            "schools": school_count,
            "teachers": teacher_count,
            "students": student_count,
            "projects": project_count,
            "tasks": task_count,
            "resources": resource_count,
            "ai_calls": ai_call_count,
        }

    @staticmethod
    async def get_ai_usage(
        db: AsyncSession,
        school_id: Optional[str] = None,
        owner_id: Optional[str] = None,
    ) -> dict:
        """Return AI usage breakdown: call counts by scenario and by provider.

        Args:
            db: Database session.
            school_id: If provided, scope to this school.
            owner_id: If provided (teacher scope), scope to this user's AI calls.

        Returns:
            dict with by_scenario list, by_provider list, total_calls.
        """
        # --- By scenario ---
        by_scenario_query = (
            select(AIAgentCall.scenario, func.count().label("count"))
            .select_from(AIAgentCall)
            .group_by(AIAgentCall.scenario)
            .order_by(func.count().desc())
        )
        if school_id:
            by_scenario_query = by_scenario_query.where(AIAgentCall.school_id == school_id)
        if owner_id:
            by_scenario_query = by_scenario_query.where(AIAgentCall.user_id == owner_id)
        by_scenario_result = await db.execute(by_scenario_query)
        by_scenario = [
            {"scenario": row.scenario, "count": row.count}
            for row in by_scenario_result
        ]

        # --- By provider ---
        by_provider_query = (
            select(AIAgentCall.provider, func.count().label("count"))
            .select_from(AIAgentCall)
            .group_by(AIAgentCall.provider)
            .order_by(func.count().desc())
        )
        if school_id:
            by_provider_query = by_provider_query.where(AIAgentCall.school_id == school_id)
        if owner_id:
            by_provider_query = by_provider_query.where(AIAgentCall.user_id == owner_id)
        by_provider_result = await db.execute(by_provider_query)
        by_provider = [
            {"provider": row.provider, "count": row.count}
            for row in by_provider_result
        ]

        # --- Total ---
        total_query = select(func.count()).select_from(AIAgentCall)
        if school_id:
            total_query = total_query.where(AIAgentCall.school_id == school_id)
        if owner_id:
            total_query = total_query.where(AIAgentCall.user_id == owner_id)
        total_calls = (await db.execute(total_query)).scalar()

        return {
            "by_scenario": by_scenario,
            "by_provider": by_provider,
            "total_calls": total_calls,
        }

    @staticmethod
    async def get_project_trends(
        db: AsyncSession,
        school_id: Optional[str] = None,
        owner_id: Optional[str] = None,
    ) -> dict:
        """Return project trends: counts by month and by status.

        Args:
            db: Database session.
            school_id: If provided, scope to this school.
            owner_id: If provided (teacher scope), scope to this owner's projects.

        Returns:
            dict with by_month list and by_status list.
        """
        # --- By status ---
        by_status_query = (
            select(Project.status, func.count().label("count"))
            .select_from(Project)
            .group_by(Project.status)
        )
        if school_id:
            by_status_query = by_status_query.where(Project.school_id == school_id)
        if owner_id:
            by_status_query = by_status_query.where(Project.owner_id == owner_id)
        by_status_result = await db.execute(by_status_query)
        by_status = [
            {"status": row.status, "count": row.count}
            for row in by_status_result
        ]

        # --- By month ---
        # Group by year and month from created_at
        by_month_query = (
            select(
                func.strftime("%Y-%m", Project.created_at).label("month"),
                func.count().label("count"),
            )
            .select_from(Project)
            .group_by(func.strftime("%Y-%m", Project.created_at))
            .order_by("month")
        )
        if school_id:
            by_month_query = by_month_query.where(Project.school_id == school_id)
        if owner_id:
            by_month_query = by_month_query.where(Project.owner_id == owner_id)
        by_month_result = await db.execute(by_month_query)
        by_month = [
            {"month": row.month, "count": row.count}
            for row in by_month_result
        ]

        return {
            "by_month": by_month,
            "by_status": by_status,
        }

    @staticmethod
    async def get_trial_readiness(db: AsyncSession) -> dict:
        """Return the admin-facing checklist for trial operation."""
        counts = {
            "active_schools": await DashboardService._count(
                db,
                School,
                School.status == "active",
                School.deleted_at.is_(None),
            ),
            "classes": await DashboardService._count(db, Class, Class.deleted_at.is_(None)),
            "subjects": await DashboardService._count(db, Subject, Subject.deleted_at.is_(None)),
            "teachers": await DashboardService._count(
                db,
                User,
                User.role == "teacher",
                User.status == "active",
                User.deleted_at.is_(None),
            ),
            "students": await DashboardService._count(
                db,
                User,
                User.role == "student",
                User.status == "active",
                User.deleted_at.is_(None),
            ),
            "lesson_plan_agents": await DashboardService._count(
                db,
                AIAgent,
                AIAgent.scenario == "lesson_plan",
                AIAgent.enabled.is_(True),
                AIAgent.deleted_at.is_(None),
            ),
            "workflow_projects": await DashboardService._count(
                db,
                Project,
                Project.status.in_(["active", "completed"]),
                Project.deleted_at.is_(None),
            ),
            "student_tasks": await DashboardService._count(
                db,
                Task,
                Task.status.in_(["published", "closed"]),
                Task.deleted_at.is_(None),
            ),
            "resources": await DashboardService._count(
                db,
                Resource,
                Resource.status.in_(["active", "published"]),
                Resource.deleted_at.is_(None),
            ),
        }

        items = [
            DashboardService._service_readiness_item(),
            DashboardService._organization_data_item(counts),
            DashboardService._user_accounts_item(counts),
            await DashboardService._ai_contract_item(db, counts),
            DashboardService._teaching_workflow_item(counts),
            DashboardService._student_task_item(counts),
            DashboardService._resources_item(counts),
            DashboardService._backup_path_item(),
        ]
        summary = {
            "ok": sum(1 for item in items if item["status"] == "ok"),
            "warning": sum(1 for item in items if item["status"] == "warning"),
            "error": sum(1 for item in items if item["status"] == "error"),
        }

        return {
            "status": "action_required" if summary["error"] else "ready",
            "checked_at": datetime.now(timezone.utc).isoformat(),
            "summary": summary,
            "items": items,
        }

    @staticmethod
    async def get_trial_operations_runbook(db: AsyncSession) -> dict:
        """Return ordered trial rehearsal stages derived from readiness evidence."""
        readiness = await DashboardService.get_trial_readiness(db)
        items = {item["key"]: item for item in readiness["items"]}
        stages = [
            DashboardService._runbook_stage(
                key="service_readiness",
                title="服务与数据可用",
                owner="平台管理员",
                items=[items.get("service_readiness")],
                route="/admin",
                primary_action="查看 readiness",
                next_step="确认本地服务、数据库和上传目录可用后，进入基础数据检查。",
            ),
            DashboardService._runbook_stage(
                key="base_data",
                title="基础数据演练",
                owner="区县/学校管理员",
                items=[items.get("organization_data")],
                route="/admin/schools",
                primary_action="核对学校班级学科",
                next_step="学校、班级和学科齐备后，继续核对试点账号。",
            ),
            DashboardService._runbook_stage(
                key="account_access",
                title="账号登录演练",
                owner="学校管理员",
                items=[items.get("user_accounts")],
                route="/admin/users",
                primary_action="核对教师学生账号",
                next_step="确认教师和学生账号可以登录，并准备初始密码发放清单。",
            ),
            DashboardService._ai_provider_runbook_stage(items.get("ai_contract")),
            DashboardService._runbook_stage(
                key="teaching_workflow",
                title="教学闭环演练",
                owner="试点教师",
                items=[items.get("teaching_workflow"), items.get("student_task_availability")],
                route="/teacher/projects",
                primary_action="演练项目到任务闭环",
                next_step="确认教师可创建或采纳项目，学生端可看到已发布任务。",
            ),
            DashboardService._resource_backup_runbook_stage(
                items.get("resources"),
                items.get("backup_path"),
            ),
        ]
        summary = {
            "ok": sum(1 for stage in stages if stage["status"] == "ok"),
            "warning": sum(1 for stage in stages if stage["status"] == "warning"),
            "error": sum(1 for stage in stages if stage["status"] == "error"),
        }
        return {
            "status": "action_required" if summary["error"] else "ready",
            "checked_at": readiness["checked_at"],
            "summary": summary,
            "stages": stages,
        }

    @staticmethod
    async def _count(db: AsyncSession, model, *conditions) -> int:
        stmt = select(func.count()).select_from(model)
        for condition in conditions:
            stmt = stmt.where(condition)
        return int((await db.execute(stmt)).scalar() or 0)

    @staticmethod
    def _item(
        key: str,
        label: str,
        status: str,
        description: str,
        metric: str,
        action: str,
        route: str,
    ) -> dict:
        return {
            "key": key,
            "label": label,
            "status": status,
            "description": description,
            "metric": metric,
            "action": action,
            "route": route,
        }

    @staticmethod
    def _runbook_stage(
        key: str,
        title: str,
        owner: str,
        items: list[Optional[dict]],
        route: str,
        primary_action: str,
        next_step: str,
    ) -> dict:
        present_items = [item for item in items if item]
        return {
            "key": key,
            "title": title,
            "status": DashboardService._worst_status(present_items),
            "owner": owner,
            "route": route,
            "primary_action": primary_action,
            "evidence": DashboardService._stage_evidence(present_items),
            "next_step": next_step,
        }

    @staticmethod
    def _worst_status(items: list[dict]) -> str:
        order = {"ok": 0, "warning": 1, "error": 2}
        if not items:
            return "warning"
        return max((item["status"] for item in items), key=lambda status: order.get(status, 1))

    @staticmethod
    def _stage_evidence(items: list[dict]) -> list[str]:
        if not items:
            return ["暂无 readiness 证据"]
        return [
            f"{item['label']}：{item['metric']}（{DashboardService._status_label(item['status'])}）"
            for item in items
        ]

    @staticmethod
    def _status_label(status: str) -> str:
        if status == "ok":
            return "正常"
        if status == "warning":
            return "提醒"
        return "阻断"

    @staticmethod
    def _ai_provider_runbook_stage(ai_item: Optional[dict]) -> dict:
        route = "/admin/ai-agents"
        action = "执行 Provider 配置自检"
        next_step = "保持 mock/manual 可演练；真实 Provider 接入前先完成配置自检，再查看失败诊断。"
        if ai_item and ai_item.get("route") == "/admin/ai-calls":
            route = "/admin/ai-calls"
            action = "查看 AI 调用诊断"
            next_step = "先处理近期真实 Provider 调用失败，再继续教师侧生成演练。"
        return DashboardService._runbook_stage(
            key="ai_provider_rehearsal",
            title="AI Provider演练",
            owner="平台管理员",
            items=[ai_item],
            route=route,
            primary_action=action,
            next_step=next_step,
        )

    @staticmethod
    def _resource_backup_runbook_stage(resource_item: Optional[dict], backup_item: Optional[dict]) -> dict:
        route = "/teacher/resources" if resource_item and resource_item.get("status") != "ok" else "/admin"
        action = "补齐资源或执行备份"
        if backup_item and backup_item.get("status") != "ok":
            route = "/admin"
            action = "核对备份路径"
        return DashboardService._runbook_stage(
            key="resource_and_backup",
            title="资源与备份演练",
            owner="平台管理员",
            items=[resource_item, backup_item],
            route=route,
            primary_action=action,
            next_step="确认演示资源可用，并在正式试运行前完成一次 SQLite 备份演练。",
        )

    @staticmethod
    def _service_readiness_item() -> dict:
        provider_mode = "gjt_api" if all([
            settings.GJT_API_BASE_URL,
            settings.GJT_API_KEY,
            settings.GJT_AGENT_ID,
        ]) else "mock"
        try:
            upload_dir = Path(settings.UPLOAD_DIR).resolve()
            upload_dir.mkdir(parents=True, exist_ok=True)
            status = "ok"
            description = "API、数据库会话和上传目录可用，AI Provider 当前按配置运行。"
        except Exception as exc:  # pragma: no cover - only exercised by broken deployments
            upload_dir = Path(settings.UPLOAD_DIR)
            status = "error"
            description = f"上传目录不可用：{exc}"

        return DashboardService._item(
            key="service_readiness",
            label="服务运行状态",
            status=status,
            description=description,
            metric=f"AI Provider: {provider_mode} / 上传目录: {upload_dir}",
            action="查看健康检查接口",
            route="/admin/settings",
        )

    @staticmethod
    def _organization_data_item(counts: dict) -> dict:
        ready = counts["active_schools"] > 0 and counts["classes"] > 0 and counts["subjects"] > 0
        return DashboardService._item(
            key="organization_data",
            label="基础组织数据",
            status="ok" if ready else "error",
            description="学校、班级和学科是项目、账号和教学任务运转的基础。",
            metric=f"学校 {counts['active_schools']} / 班级 {counts['classes']} / 学科 {counts['subjects']}",
            action="导入或维护学校、班级、学科",
            route="/admin/schools",
        )

    @staticmethod
    def _user_accounts_item(counts: dict) -> dict:
        ready = counts["teachers"] > 0 and counts["students"] > 0
        return DashboardService._item(
            key="user_accounts",
            label="教师与学生账号",
            status="ok" if ready else "error",
            description="试运行至少需要可登录的教师账号和学生账号。",
            metric=f"教师 {counts['teachers']} / 学生 {counts['students']}",
            action="导入或创建试运行账号",
            route="/admin/users",
        )

    @staticmethod
    def _ai_contract_item(counts: dict) -> dict:
        ready = counts["lesson_plan_agents"] > 0
        return DashboardService._item(
            key="ai_contract",
            label="AI 智能体契约",
            status="ok" if ready else "error",
            description="教学方案生成需要启用的 lesson_plan 智能体配置。",
            metric=f"可用教学方案智能体 {counts['lesson_plan_agents']}",
            action="检查 AI 智能体配置",
            route="/admin/ai-agents",
        )

    @staticmethod
    def _teaching_workflow_item(counts: dict) -> dict:
        ready = counts["workflow_projects"] > 0
        return DashboardService._item(
            key="teaching_workflow",
            label="教学项目闭环",
            status="ok" if ready else "warning",
            description="已有激活或完成项目时，可以直接演示教学评主流程。",
            metric=f"激活/完成项目 {counts['workflow_projects']}",
            action="让教师创建或采纳一个教学项目",
            route="/teacher/projects",
        )

    @staticmethod
    async def _ai_contract_item(db: AsyncSession, counts: dict) -> dict:
        agents_result = await db.execute(
            select(AIAgent).where(
                AIAgent.scenario == "lesson_plan",
                AIAgent.enabled.is_(True),
                AIAgent.deleted_at.is_(None),
            )
        )
        agents = agents_result.scalars().all()
        real_agents = [agent for agent in agents if DashboardService._is_real_provider(agent.provider)]

        if not agents:
            return DashboardService._item(
                key="ai_contract",
                label="AI 智能体契约",
                status="error",
                description="教学方案生成需要启用 lesson_plan 智能体配置。",
                metric=f"可用教学方案智能体 {counts['lesson_plan_agents']}",
                action="检查 AI 智能体配置",
                route="/admin/ai-agents",
            )

        misconfigured = [
            agent for agent in real_agents
            if DashboardService._missing_provider_config(agent)
        ]
        if misconfigured:
            missing_names = "、".join(agent.name for agent in misconfigured[:3])
            return DashboardService._item(
                key="ai_contract",
                label="AI 智能体契约",
                status="error",
                description="真实 Provider 智能体还缺少必要配置，补齐前不建议试运行。",
                metric=f"待补齐配置 {len(misconfigured)} / 可用教学方案智能体 {len(agents)}",
                action=f"检查 {missing_names or 'AI 智能体'} 配置",
                route="/admin/ai-agents",
            )

        failure_count = await DashboardService._real_provider_failure_count(db)
        if failure_count:
            return DashboardService._item(
                key="ai_contract",
                label="AI 智能体契约",
                status="warning",
                description="真实 Provider 已出现调用失败，请联动调用记录排查。",
                metric=f"真实 Provider 失败调用 {failure_count}",
                action="查看 AI 调用诊断",
                route="/admin/ai-calls",
            )

        return DashboardService._item(
            key="ai_contract",
            label="AI 智能体契约",
            status="ok",
            description="教学方案生成智能体配置完整。",
            metric=f"可用教学方案智能体 {len(agents)} / 真实 Provider {len(real_agents)}",
            action="检查 AI 智能体配置",
            route="/admin/ai-agents",
        )

    @staticmethod
    def _is_real_provider(provider: Optional[str]) -> bool:
        return (provider or "mock") not in {"mock", "manual_import", "gjt_link"}

    @staticmethod
    def _missing_provider_config(agent: AIAgent) -> list[str]:
        provider = agent.provider or "mock"
        config = agent.config or {}
        missing: list[str] = []
        if not DashboardService._is_real_provider(provider):
            return missing
        if provider == "gjt_api":
            extra = config.get("extra") or {}
            if not (config.get("endpoint") or settings.GJT_API_BASE_URL):
                missing.append("endpoint")
            if not (config.get("agent_id") or extra.get("agent_id") or settings.GJT_AGENT_ID):
                missing.append("agent_id")
            return missing
        api_key_env = config.get("api_key_env")
        has_env_key = bool(api_key_env and os.getenv(api_key_env, ""))
        has_api_key = bool(config.get("api_key") or settings.OPENAI_COMPATIBLE_API_KEY)
        if not (config.get("endpoint") or settings.OPENAI_COMPATIBLE_API_BASE_URL):
            missing.append("endpoint")
        if not (config.get("model") or settings.OPENAI_COMPATIBLE_MODEL):
            missing.append("model")
        if not (has_env_key or has_api_key):
            missing.append("api_key")
        return missing

    @staticmethod
    async def _real_provider_failure_count(db: AsyncSession) -> int:
        query = select(func.count()).select_from(AIAgentCall).where(
            AIAgentCall.status == "failed",
            AIAgentCall.provider.notin_(["mock", "manual_import", "gjt_link"]),
        )
        return int((await db.execute(query)).scalar() or 0)

    @staticmethod
    def _student_task_item(counts: dict) -> dict:
        ready = counts["student_tasks"] > 0
        return DashboardService._item(
            key="student_task_availability",
            label="学生任务可见性",
            status="ok" if ready else "warning",
            description="发布任务后学生端才能看到任务并提交成果。",
            metric=f"已发布/已关闭任务 {counts['student_tasks']}",
            action="进入项目详情发布任务",
            route="/teacher/projects",
        )

    @staticmethod
    def _resources_item(counts: dict) -> dict:
        ready = counts["resources"] > 0
        return DashboardService._item(
            key="resources",
            label="资源中心",
            status="ok" if ready else "warning",
            description="资源中心有内容时，教学设计和任务支撑更完整。",
            metric=f"可用资源 {counts['resources']}",
            action="导入或维护校本资源",
            route="/teacher/resources",
        )

    @staticmethod
    def _backup_path_item() -> dict:
        db_path = DashboardService._sqlite_database_path()
        if db_path is None:
            return DashboardService._item(
                key="backup_path",
                label="数据备份路径",
                status="warning",
                description="当前不是 SQLite 数据库，请使用对应数据库的原生命令做备份。",
                metric="非 SQLite 数据库",
                action="查看部署文档中的备份建议",
                route="/admin/settings",
            )

        exists = db_path.exists()
        return DashboardService._item(
            key="backup_path",
            label="数据备份路径",
            status="ok" if exists else "warning",
            description="SQLite 试运行可使用脚本进行时间戳备份和安全恢复。",
            metric=str(db_path),
            action="执行 scripts/backup-sqlite.ps1",
            route="/admin/settings",
        )

    @staticmethod
    def _sqlite_database_path() -> Optional[Path]:
        database_url = settings.DATABASE_URL
        if not database_url.startswith("sqlite"):
            return None
        marker = ":///"
        if marker not in database_url:
            return None
        raw_path = database_url.split(marker, 1)[1]
        if raw_path in {":memory:", ""}:
            return None
        path = Path(raw_path)
        if not path.is_absolute():
            path = Path.cwd() / path
        return path.resolve()
